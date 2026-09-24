"""主题桥：浅色/深色两套显式配色，供 QML 自绘部件使用。
Fluent 内建控件跟随 styleHints；自绘部分（卡片/弹窗/复选框/编解码色）走这里，
避免平台误判明暗导致黑底深字。FTT_THEME=dark|light|auto（默认 auto 跟随系统）。"""
from PySide6.QtCore import QObject, Signal, Property, Slot

LIGHT = {
    "cardBg": "#ffffff",
    "cardBorder": "#e3e6eb",
    "textMain": "#111827",
    "textMuted": "#374151",
    "textSub": "#6b7280",
    "popupBg": "#ffffff",
    "popupBorder": "#e3e6eb",
    "accent": "#005fb8",
    "accentHover": "#106ebe",
    "accentPressed": "#004578",
    "boxBorder": "#8a8886",
    "boxDisabledBg": "#e5e7eb",
    "codecOk": "#1a7f37",
    "codecErr": "#cf222e",
}

DARK = {
    "cardBg": "#2b2b2b",
    "cardBorder": "#3a3a3a",
    "textMain": "#f3f3f3",
    "textMuted": "#d1d5db",
    "textSub": "#9ca3af",
    "popupBg": "#2b2b2b",
    "popupBorder": "#3a3a3a",
    "accent": "#60cdff",
    "accentHover": "#4fb3e8",
    "accentPressed": "#3a9fd4",
    "boxBorder": "#9ca3af",
    "boxDisabledBg": "#3a3a3a",
    "codecOk": "#3fb950",
    "codecErr": "#f85149",
}


class ThemeBridge(QObject):
    changed = Signal()

    def __init__(self, dark: bool = False, parent=None):
        super().__init__(parent)
        self._dark = bool(dark)

    def _get(self, key: str) -> str:
        return (DARK if self._dark else LIGHT)[key]

    def _is_dark(self) -> bool:
        return self._dark

    @Slot(bool)
    def setDark(self, v: bool):
        if self._dark != bool(v):
            self._dark = bool(v)
            self.changed.emit()

    dark = Property(bool, _is_dark, notify=changed)
    cardBg = Property(str, lambda s: s._get("cardBg"), notify=changed)
    cardBorder = Property(str, lambda s: s._get("cardBorder"), notify=changed)
    textMain = Property(str, lambda s: s._get("textMain"), notify=changed)
    textMuted = Property(str, lambda s: s._get("textMuted"), notify=changed)
    textSub = Property(str, lambda s: s._get("textSub"), notify=changed)
    popupBg = Property(str, lambda s: s._get("popupBg"), notify=changed)
    popupBorder = Property(str, lambda s: s._get("popupBorder"), notify=changed)
    accent = Property(str, lambda s: s._get("accent"), notify=changed)
    accentHover = Property(str, lambda s: s._get("accentHover"), notify=changed)
    accentPressed = Property(str, lambda s: s._get("accentPressed"), notify=changed)
    boxBorder = Property(str, lambda s: s._get("boxBorder"), notify=changed)
    boxDisabledBg = Property(str, lambda s: s._get("boxDisabledBg"), notify=changed)
    codecOk = Property(str, lambda s: s._get("codecOk"), notify=changed)
    codecErr = Property(str, lambda s: s._get("codecErr"), notify=changed)

    def codec_colors(self) -> tuple[str, str]:
        table = DARK if self._dark else LIGHT
        return table["codecOk"], table["codecErr"]

    def is_dark(self) -> bool:
        return self._dark


def detect_dark(app=None) -> bool:
    """FTT_THEME=dark 强制深色；=light 强制浅色；否则跟随系统（默认）。"""
    import os
    pref = os.environ.get("FTT_THEME", "auto").lower()
    if pref == "dark":
        return True
    if pref == "light":
        return False
    if app is not None:
        try:
            from PySide6.QtCore import Qt
            return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
        except Exception:
            pass
    return False
