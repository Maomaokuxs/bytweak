"""Flatpak QML 桥接：flatpak_core 查询 + 安装卸载，后台执行复用 Worker。

user 域操作无需提权；system 域走 pkexec。"""
import subprocess

from PySide6.QtCore import QObject, Signal, Property, Slot

from . import flatpak_core
from .utils import logger, run_pkexec
from .workers import Worker


class FlatpakBridge(QObject):
    appsChanged = Signal()
    remotesChanged = Signal()
    busyChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._apps: list[dict] = []
        self._remotes: list[dict] = []
        self._available = flatpak_core.flatpak_available()
        self._busy = False
        self._loading = False
        self._workers: list[Worker] = []

    def getApps(self):
        return self._apps

    appList = Property(list, getApps, notify=appsChanged)

    def getRemotes(self):
        return self._remotes

    remoteList = Property(list, getRemotes, notify=remotesChanged)

    def getAvailable(self):
        return self._available

    available = Property(bool, getAvailable, constant=True)

    def getBusy(self):
        return self._busy

    def _setBusy(self, v):
        if self._busy != v:
            self._busy = v
            self.busyChanged.emit()

    busy = Property(bool, getBusy, notify=busyChanged)

    @Slot()
    def refresh(self):
        if self._loading or not self._available:
            return
        self._loading = True
        try:
            self._apps = flatpak_core.list_apps()
            self.appsChanged.emit()
            self._remotes = flatpak_core.list_remotes()
            self.remotesChanged.emit()
            logger.debug(f"flatpak bridge scan: {len(self._apps)} apps")
        except Exception as e:
            logger.warning(f"bridge flatpak refresh failed: {e}")
            self.message.emit("刷新失败", str(e), True)
        finally:
            self._loading = False

    @Slot(str, str)
    def installApp(self, app_id: str, remote: str = "flathub"):
        if self._busy or self._loading:
            return
        try:
            cmd = flatpak_core.build_install_cmd(app_id, remote or "flathub", "user")
        except ValueError as e:
            self.message.emit("错误", str(e), True)
            return
        self._run(cmd, f"Flatpak/安装 {app_id.strip()}", "安装成功", timeout=900)

    @Slot(str, str)
    def uninstallApp(self, app_id: str, scope: str = "user"):
        if self._busy or self._loading:
            return
        try:
            cmd = flatpak_core.build_uninstall_cmd(app_id, scope)
        except ValueError as e:
            self.message.emit("错误", str(e), True)
            return
        use_pkexec = (scope == "system")
        self._run(cmd, f"Flatpak/卸载 {app_id.strip()}", "卸载成功",
                  timeout=600, use_pkexec=use_pkexec)

    @Slot()
    def updateAll(self):
        if self._busy or self._loading:
            return
        self._run(flatpak_core.build_update_cmd(), "Flatpak/全部更新", "更新完成", timeout=1800)

    def _run(self, cmd: list[str], label: str, success_msg: str,
             timeout: float = 600, use_pkexec: bool = False):
        if use_pkexec:
            def _task():
                result = run_pkexec(cmd, timeout=int(timeout))
                if result.returncode != 0:
                    raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
                return result
        else:
            def _task():
                logger.info(f"flatpak: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                if result.returncode != 0:
                    raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "执行失败")
                return result

        self._setBusy(True)
        worker = Worker(_task, label=label, timeout=timeout + 120)
        self._workers.append(worker)

        def on_ok(_):
            self._setBusy(False)
            self.message.emit("提示", success_msg, False)
            self._cleanup(worker)
            self.refresh()

        def on_err(msg: str):
            self._setBusy(False)
            if "canceled" not in msg.lower() and "dismissed" not in msg.lower():
                self.message.emit("操作失败", f"操作失败:\n{msg[:500]}", True)
            self._cleanup(worker)
            self.refresh()

        worker.finished_ok.connect(on_ok)
        worker.finished_err.connect(on_err)
        worker.start()

    def _cleanup(self, worker: Worker):
        try:
            worker.finished_ok.disconnect()
            worker.finished_err.disconnect()
        except Exception:
            pass
        if worker in self._workers:
            self._workers.remove(worker)
        if not getattr(worker, "timed_out", False):
            worker.deleteLater()
