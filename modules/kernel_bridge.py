"""内核管理 QML 桥接：kernel_core 查询 + dnf/grubby 提权执行，后台复用 Worker。"""
from PySide6.QtCore import QObject, Signal, Property, Slot

from . import kernel_core
from .utils import logger, run_pkexec
from .workers import Worker


class KernelBridge(QObject):
    kernelsChanged = Signal()
    busyChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._kernels: list[dict] = []
        self._busy = False
        self._workers: list[Worker] = []

    def getKernels(self):
        return self._kernels

    kernels = Property(list, getKernels, notify=kernelsChanged)

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
            self._kernels = kernel_core.list_kernels()
            self.kernelsChanged.emit()
            logger.debug(f"kernel bridge scan: {len(self._kernels)} kernels")
        except Exception as e:
            logger.warning(f"bridge kernel refresh failed: {e}")
            self.message.emit("刷新失败", str(e), True)

    @Slot(str)
    def removeKernel(self, full: str):
        try:
            cmd = kernel_core.build_remove_cmd(full, self._kernels or None)
        except ValueError as e:
            self.message.emit("错误", str(e), True)
            return
        self._run_privileged(cmd, f"内核/删除 {full}", f"已删除内核 {full}")

    @Slot(str)
    def setDefault(self, full: str):
        try:
            cmd = kernel_core.build_set_default_cmd(full)
        except ValueError as e:
            self.message.emit("错误", str(e), True)
            return
        self._run_privileged(cmd, f"内核/设为默认 {full}",
                             f"已将 {full} 设为默认启动内核")

    def _run_privileged(self, cmd: list[str], label: str, ok_msg: str):
        if self._busy:
            return

        def _task():
            result = run_pkexec(cmd, timeout=300)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip()
                                   or "pkexec 执行失败")
            return result

        self._setBusy(True)
        worker = Worker(_task, label=label, timeout=330)
        self._workers.append(worker)

        def on_ok(_):
            self._setBusy(False)
            self.message.emit("提示", ok_msg, False)
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
