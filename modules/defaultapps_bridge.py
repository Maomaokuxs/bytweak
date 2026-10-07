"""默认应用设置 QML 桥接：defaultapps_core 查询/设置（用户级，无需提权）。"""
import subprocess

from PySide6.QtCore import QObject, Signal, Property, Slot

from . import defaultapps_core
from .utils import logger


class DefaultAppsBridge(QObject):
    defaultsChanged = Signal()
    busyChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._defaults: list[dict] = []
        self._busy = False

    def getDefaults(self):
        return self._defaults

    defaults = Property(list, getDefaults, notify=defaultsChanged)

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
        self._setBusy(True)
        try:
            self._defaults = defaultapps_core.get_defaults()
            self.defaultsChanged.emit()
            logger.debug(f"defaultapps bridge scan: {len(self._defaults)} targets")
        except Exception as e:
            logger.warning(f"bridge defaultapps refresh failed: {e}")
            self.message.emit("刷新失败", str(e), True)
        finally:
            self._setBusy(False)

    @Slot(str, str)
    def setDefault(self, key: str, desktop_id: str):
        if self._busy:
            return
        try:
            cmd = defaultapps_core.build_set_default_cmd(desktop_id, key)
        except ValueError as e:
            self.message.emit("输入有误", str(e), True)
            return
        self._setBusy(True)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip() or "设置失败")
            self.message.emit("提示", "默认应用已更新", False)
        except Exception as e:
            logger.warning(f"bridge defaultapps set failed: {e}")
            self.message.emit("操作失败", str(e)[:500], True)
        finally:
            self._setBusy(False)
            self.refresh()
