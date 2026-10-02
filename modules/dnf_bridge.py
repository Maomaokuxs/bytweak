"""DNF 调优 QML 桥接：dnf.conf [main] 读写，经 pkexec 提权落盘。"""
import os
import tempfile

from PySide6.QtCore import QObject, Signal, Property, Slot

from . import dnf_core
from .utils import logger, run_pkexec
from .workers import Worker


class DnfBridge(QObject):
    settingsChanged = Signal()
    busyChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings: dict = dict(dnf_core.DEFAULTS)
        self._supported = dnf_core.dnf_supported()
        self._busy = False
        self._workers: list[Worker] = []

    def getSettings(self):
        return dict(self._settings)

    settings = Property('QVariant', getSettings, notify=settingsChanged)

    def getSupported(self):
        return self._supported

    supported = Property(bool, getSupported, constant=True)

    def getBusy(self):
        return self._busy

    def _setBusy(self, v):
        if self._busy != v:
            self._busy = v
            self.busyChanged.emit()

    busy = Property(bool, getBusy, notify=busyChanged)

    @Slot()
    def refresh(self):
        if not self._supported:
            return
        try:
            self._settings = dnf_core.read_settings()
            self.settingsChanged.emit()
        except Exception as e:
            logger.warning(f"bridge dnf refresh failed: {e}")

    @Slot('QVariant')
    def apply(self, raw):
        if self._busy or not self._supported:
            return
        try:
            cleaned = dnf_core.validate_settings(dict(raw or {}))
        except (ValueError, TypeError, AttributeError) as e:
            self.message.emit("错误", str(e), True)
            return

        def _task():
            fd, tmp = tempfile.mkstemp(prefix="dnf-conf-")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write("[main]\n")
                    for k in dnf_core.ALL_KEYS:
                        f.write(f"{k}={cleaned[k]}\n")
                r1 = run_pkexec(["cp", tmp, dnf_core.DNF_CONF], timeout=60)
                if r1.returncode != 0:
                    raise RuntimeError(r1.stderr.strip() or "写入配置失败")
                r2 = run_pkexec(["chmod", "644", dnf_core.DNF_CONF], timeout=60)
                if r2.returncode != 0:
                    raise RuntimeError(r2.stderr.strip() or "设置权限失败")
            finally:
                try:
                    os.unlink(tmp)
                except Exception:
                    pass
            return cleaned

        self._setBusy(True)
        worker = Worker(_task, label="DNF/调优写入", timeout=180)
        self._workers.append(worker)

        def on_ok(data):
            self._setBusy(False)
            self._settings = dict(data)
            self.settingsChanged.emit()
            self.message.emit("提示", "DNF 配置已生效", False)
            self._cleanup(worker)

        def on_err(msg: str):
            self._setBusy(False)
            if "canceled" not in msg.lower() and "dismissed" not in msg.lower():
                self.message.emit("操作失败", f"操作失败:\n{msg[:500]}", True)
            self._cleanup(worker)

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
