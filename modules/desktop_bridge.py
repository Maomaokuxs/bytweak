"""桌面组件 QML 桥接：desktop_core 探测切换（用户态进程操作，无需提权）。"""
from PySide6.QtCore import QObject, Signal, Property, Slot

from . import desktop_core
from .utils import logger


def _options_with_index(options, current):
    items = [{"key": k, "title": t, "desc": d} for k, t, d in options]
    try:
        index = [k for k, _, _ in options].index(current)
    except ValueError:
        index = -1
    return items, index


class DesktopBridge(QObject):
    stateChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._notif_items: list[dict] = []
        self._notif_index = -1
        self._bar_items: list[dict] = []
        self._bar_index = -1
        self._persist = True
        self._status = "就绪"

    def getNotifItems(self):
        return self._notif_items

    notifItems = Property(list, getNotifItems, notify=stateChanged)

    def getNotifIndex(self):
        return self._notif_index

    def _setNotifIndex(self, v):
        if self._notif_index != v:
            self._notif_index = v
            self.stateChanged.emit()

    notifIndex = Property(int, getNotifIndex, notify=stateChanged)

    def getBarItems(self):
        return self._bar_items

    barItems = Property(list, getBarItems, notify=stateChanged)

    def getBarIndex(self):
        return self._bar_index

    def _setBarIndex(self, v):
        if self._bar_index != v:
            self._bar_index = v
            self.stateChanged.emit()

    barIndex = Property(int, getBarIndex, notify=stateChanged)

    def getPersist(self):
        return self._persist

    def _setPersist(self, v):
        if self._persist != v:
            self._persist = v
            self.stateChanged.emit()

    persistEnabled = Property(bool, getPersist, notify=stateChanged)

    def getStatus(self):
        return self._status

    def _say(self, msg):
        logger.debug(msg)
        if self._status != msg:
            self._status = msg
            self.stateChanged.emit()

    statusText = Property(str, getStatus, notify=stateChanged)

    @Slot()
    def refresh(self):
        try:
            nm = desktop_core.detect_notif_manager()
            bar = desktop_core.detect_bar()
            self._notif_items, self._notif_index = _options_with_index(desktop_core.NOTIF_OPTIONS, nm)
            self._bar_items, self._bar_index = _options_with_index(desktop_core.BAR_OPTIONS, bar)
            self._say(f"当前：通知[{nm}] 顶栏[{bar}]")
            self.stateChanged.emit()
        except Exception as e:
            logger.warning(f"bridge desktop refresh failed: {e}")

    @Slot(int)
    def setNotif(self, index: int):
        if 0 <= index < len(self._notif_items):
            self._setNotifIndex(index)

    @Slot(int)
    def setBar(self, index: int):
        if 0 <= index < len(self._bar_items):
            self._setBarIndex(index)

    @Slot(bool)
    def setPersist(self, on: bool):
        self._setPersist(bool(on))

    @Slot()
    def applyAll(self):
        if not (0 <= self._notif_index < len(self._notif_items)):
            self._say("先选一个通知管理器")
            return
        if not (0 <= self._bar_index < len(self._bar_items)):
            self._say("先选一个顶栏")
            return
        notif_key = self._notif_items[self._notif_index]["key"]
        bar_key = self._bar_items[self._bar_index]["key"]
        msg = desktop_core.switch_notif(notif_key)
        msg2 = desktop_core.switch_bar(bar_key)
        extra = ""
        if self._persist:
            extra = "；" + desktop_core.sync_niri_autostart(bar_key)
        self.refresh()
        self._say(f"{msg}；{msg2}{extra}")
