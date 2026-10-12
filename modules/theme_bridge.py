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


def _portal_color_scheme() -> int | None:
    """经 XDG Desktop Portal 读系统配色偏好。
    返回 1=prefer dark, 2=prefer light, 0=no preference；失败返回 None。"""
    try:
        import subprocess
        out = subprocess.run(
            ["gdbus", "call", "--session",
             "--dest", "org.freedesktop.portal.Desktop",
             "--object-path", "/org/freedesktop/portal/desktop",
             "--method", "org.freedesktop.portal.Settings.Read",
             "org.freedesktop.appearance", "color-scheme"],
            capture_output=True, text=True, timeout=5)
        txt = out.stdout or ""
        if "uint32 1" in txt:
            return 1
        if "uint32 2" in txt:
            return 2
        if "uint32 0" in txt:
            return 0
    except Exception:
        pass
    return None


def detect_dark(app=None) -> bool:
    """FTT_THEME=dark 强制深色；=light 强制浅色；否则跟随系统（默认）。
    系统检测走 XDG Desktop Portal，不受 app.styleHints().setColorScheme() 锁定的影响。"""
    import os
    pref = os.environ.get("FTT_THEME", "auto").lower()
    if pref == "dark":
        return True
    if pref == "light":
        return False
    portal = _portal_color_scheme()
    if portal == 1:
        return True
    if portal == 2:
        return False
    # 回退：styleHints（注意 app 可能已锁定浅色，仅作最后手段）
    if app is not None:
        try:
            from PySide6.QtCore import Qt
            return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
        except Exception:
            pass
    return False


class ThemeWatcher(QObject):
    """监听系统昼夜切换（Portal SettingChanged 信号），自动更新 ThemeBridge。
    FTT_THEME 非 auto 时不跟随（用户手动指定优先）。"""

    def __init__(self, theme_bridge: "ThemeBridge", parent=None):
        super().__init__(parent)
        self._theme = theme_bridge
        import os
        self._follow = os.environ.get("FTT_THEME", "auto").lower() == "auto"
        self._setup_dbus()

    def _setup_dbus(self):
        if not self._follow:
            return
        try:
            from PySide6.QtDBus import QDBusConnection
            bus = QDBusConnection.sessionBus()
            if not bus.isConnected():
                return
            # 监听 org.freedesktop.portal.Settings 的 SettingChanged 信号
            bus.connect(
                "org.freedesktop.portal.Desktop",
                "/org/freedesktop/portal/desktop",
                "org.freedesktop.portal.Settings",
                "SettingChanged",
                self._on_setting_changed)
        except Exception:
            pass

    def _on_setting_changed(self, namespace: str, key: str, value):
        try:
            if namespace == "org.freedesktop.appearance" and key == "color-scheme":
                # value 是 QDBusVariant，取其值
                v = value.toUInt() if hasattr(value, "toUInt") else int(str(value))
                if v == 1:
                    self._theme.setDark(True)
                elif v == 2:
                    self._theme.setDark(False)
        except Exception:
            pass
