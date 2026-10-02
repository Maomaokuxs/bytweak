"""服务管理 QML 桥接：service_core 查询 + systemctl 分发，后台执行复用 Worker。"""
from PySide6.QtCore import QObject, Signal, Property, Slot

from . import service_core
from .utils import logger, run_pkexec
from .workers import Worker


class ServiceBridge(QObject):
    servicesChanged = Signal()
    busyChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._services: list[dict] = []
        self._busy = False
        self._loading = False
        self._workers: list[Worker] = []

    def getServices(self):
        return self._services

    serviceList = Property(list, getServices, notify=servicesChanged)

    def getBusy(self):
        return self._busy

    def _setBusy(self, v):
        if self._busy != v:
            self._busy = v
            self.busyChanged.emit()

    busy = Property(bool, getBusy, notify=busyChanged)

    @Slot()
    def refresh(self):
        if self._loading:
            return
        self._loading = True
        try:
            self._services = service_core.scan_services()
            self.servicesChanged.emit()
            logger.debug(f"service bridge scan: {len(self._services)} units")
        except Exception as e:
            logger.warning(f"bridge service refresh failed: {e}")
            self.message.emit("刷新失败", str(e), True)
        finally:
            self._loading = False

    @Slot(str, bool)
    def setEnabled(self, unit: str, enable: bool):
        self._act("enable" if enable else "disable", unit,
                  f"服务/自启 {'启用' if enable else '停用'} {unit}")

    @Slot(str, bool)
    def setActive(self, unit: str, start: bool):
        self._act("start" if start else "stop", unit,
                  f"服务/{'启动' if start else '停止'} {unit}")

    def _act(self, action: str, unit: str, label: str):
        if self._busy or self._loading:
            return
        try:
            cmd = service_core.build_systemctl_cmd(action, unit)
        except ValueError as e:
            self.message.emit("错误", str(e), True)
            return

        def _task():
            result = run_pkexec(cmd, timeout=120)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
            return result

        self._setBusy(True)
        worker = Worker(_task, label=label, timeout=180)
        self._workers.append(worker)

        def on_ok(_):
            self._setBusy(False)
            self.message.emit("提示", "操作成功", False)
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
