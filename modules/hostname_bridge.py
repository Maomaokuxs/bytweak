"""主机名 QML 桥接：hostname_core 查询 + hostnamectl 提权执行，后台复用 Worker。"""
from PySide6.QtCore import QObject, Signal, Property, Slot

from . import hostname_core
from .utils import logger, run_pkexec
from .workers import Worker


class HostnameBridge(QObject):
    hostnameChanged = Signal()
    busyChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hostname = ""
        self._busy = False
        self._workers: list[Worker] = []

    def getHostname(self):
        return self._hostname

    hostname = Property(str, getHostname, notify=hostnameChanged)

    def getBusy(self):
        return self._busy

    def _setBusy(self, v):
        if self._busy != v:
            self._busy = v
            self.busyChanged.emit()

    busy = Property(bool, getBusy, notify=busyChanged)

    @Slot()
    def refresh(self):
        if self._busy:
            return
        try:
            self._hostname = hostname_core.current_hostname()
            self.hostnameChanged.emit()
        except Exception as e:
            logger.warning(f"bridge hostname refresh failed: {e}")
            self.message.emit("刷新失败", str(e), True)

    @Slot(str)
    def setHostname(self, name: str):
        if self._busy:
            return
        try:
            cmd = hostname_core.build_set_hostname_cmd(name)
        except ValueError as e:
            self.message.emit("输入有误", str(e), True)
            return

        def _task():
            result = run_pkexec(cmd, timeout=60)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip()
                                   or "pkexec 执行失败")
            return result

        self._setBusy(True)
        worker = Worker(_task, label=f"主机名/修改为 {name}", timeout=90)
        self._workers.append(worker)

        def on_ok(_):
            self._setBusy(False)
            self.message.emit("提示", f"主机名已改为 {name}", False)
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
