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
    _CONFIG = None  # 类级缓存配置文件路径

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


def _gsettings_color_scheme() -> int | None:
    """经 gsettings 读系统配色（与 theme-sync.sh 同源）。
    返回 1=prefer dark, 2=prefer light；失败返回 None。"""
    try:
        import subprocess
        out = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True, text=True, timeout=5)
        txt = (out.stdout or "").strip()
        if "prefer-dark" in txt:
            return 1
        if "prefer-light" in txt:
            return 2
    except Exception:
        pass
    return None


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
    """启动时一次性的主题判断：保存的手动选择 > gsettings > 默认浅色。
    运行时不再跟随系统（壁纸切换会触发 hellwal 全套变色，跟随会乱），
    只由用户经 UI 手动切换。"""
    # 1. FTT_THEME 环境变量（调试用）
    import os
    pref = os.environ.get("FTT_THEME", "auto").lower()
    if pref == "dark":
        return True
    if pref == "light":
        return False
    # 3. gsettings（仅启动时读一次）
    gs = _gsettings_color_scheme()
    if gs == 1:
        return True
    return False


class ThemeWatcher(QObject):
    """主动适配系统昼夜变化：
    每 3 秒读 gsettings（与 theme-sync.sh 同源），
    白天/黑夜变化时主动调用 theme.setDark() 硬套对应主题，
    保证显示正确，而不是依赖 Qt style 的自动跟随（不可靠）。
    用户经 UI 手动选择后，该次选择优先（持久化），不再被自动覆盖。
    """

    def __init__(self, theme_bridge: "ThemeBridge", parent=None):
        super().__init__(parent)
        self._theme = theme_bridge
        self._last = None
        try:
            from PySide6.QtCore import QTimer
            self._timer = QTimer(self)
            self._timer.setInterval(3000)
            self._timer.timeout.connect(self._poll)
            self._timer.start()
        except Exception:
            pass

    def _poll(self):
        try:
            v = _gsettings_color_scheme()
            if v is None or v == self._last:
                return
            self._last = v
            self._theme.setDark(v == 1)
        except Exception:
            pass
