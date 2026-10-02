"""niri 快捷键 QML 桥接：读取配置键位并翻译作用，支持就地改键（原键注释保留）。"""
from PySide6.QtCore import QObject, Signal, Property, Slot

from . import niri_core
from .utils import logger, log_operation


class NiriBridge(QObject):
    keybindsChanged = Signal()
    groupsChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._keybinds: list[dict] = []
        self._groups: list[dict] = []

    def getKeybinds(self):
        return self._keybinds

    keybinds = Property(list, getKeybinds, notify=keybindsChanged)

    def getGroups(self):
        return self._groups

    groups = Property(list, getGroups, notify=groupsChanged)

    def getKeyChoices(self):
        return niri_core.key_choices()

    keyChoices = Property(list, getKeyChoices, constant=True)

    @Slot()
    def refresh(self):
        try:
            raw = niri_core.load_keybinds()
        except Exception as e:
            logger.warning(f"niri keybinds load failed: {e}")
            raw = []
        items = [{
            "keys": niri_core.format_keys(k["keys"]),
            "rawKeys": k["keys"],
            "title": k["title"],
            "desc": k["desc"],
            "category": k.get("category", "其他"),
            "disabled": k["disabled"],
        } for k in raw]
        self._keybinds = items
        self.keybindsChanged.emit()

        buckets: dict[str, list] = {}
        for it in items:
            buckets.setdefault(it["category"], []).append(it)
        order = [c for c in niri_core.CATEGORY_ORDER if c in buckets]
        order += [c for c in buckets if c not in order]
        self._groups = [{"name": c, "items": buckets[c]} for c in order]
        self.groupsChanged.emit()
        logger.info(f"niri 快捷键：载入 {len(items)} 条 / {len(self._groups)} 类")

    @Slot(str, str)
    def setKey(self, rawKeys: str, newCombo: str):
        """就地改键：原键注释停用、写入新键。"""
        try:
            backup = niri_core.update_binding(rawKeys, newCombo)
        except ValueError as e:
            self.message.emit("无法修改", str(e), True)
            return
        except Exception as e:
            logger.warning(f"niri setKey failed: {e}")
            self.message.emit("修改失败", str(e), True)
            return
        log_operation(f"niri快捷键/改键 {rawKeys} → {newCombo}", True)
        self.refresh()
        tail = f"\n原键已注释保留，备份：{backup.split('/')[-1]}" if backup else ""
        self.message.emit("已修改", f"{rawKeys} → {newCombo}{tail}\nniri 会自动重载，无需重启。", False)
