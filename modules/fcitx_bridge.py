"""Fcitx5 QML 桥接：fcitx_core 配置读写 + 主题扫描导入（用户态，无需提权）。"""
import time

from PySide6.QtCore import QObject, Signal, Property, Slot, QUrl

from . import fcitx_core
from .utils import logger, log_operation


class FcitxBridge(QObject):
    statusChanged = Signal()
    themesChanged = Signal()
    filePathChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._themes: list[str] = []
        self._light_index = -1
        self._dark_index = -1
        self._auto = False
        self._file_path = ""

    def getStatus(self):
        return fcitx_core.theme_status_text()

    statusText = Property(str, getStatus, notify=statusChanged)

    def getThemes(self):
        return self._themes

    themeList = Property(list, getThemes, notify=themesChanged)

    def getLightIndex(self):
        return self._light_index

    def _setLightIndex(self, v):
        if self._light_index != v:
            self._light_index = v
            self.themesChanged.emit()

    lightThemeIndex = Property(int, getLightIndex, notify=themesChanged)

    def getDarkIndex(self):
        return self._dark_index

    def _setDarkIndex(self, v):
        if self._dark_index != v:
            self._dark_index = v
            self.themesChanged.emit()

    darkThemeIndex = Property(int, getDarkIndex, notify=themesChanged)

    def getAuto(self):
        return self._auto

    def _setAuto(self, v):
        if self._auto != v:
            self._auto = v
            self.themesChanged.emit()

    autoSwitch = Property(bool, getAuto, notify=themesChanged)

    def getFilePath(self):
        return self._file_path

    def _setFilePath(self, v):
        if self._file_path != v:
            self._file_path = v
            self.filePathChanged.emit()

    filePath = Property(str, getFilePath, notify=filePathChanged)

    @Slot()
    def refresh(self):
        try:
            self._themes = fcitx_core.scan_themes()
            cfg = fcitx_core.read_config()
            light = cfg.get("Theme", "")
            dark = cfg.get("DarkTheme", "")
            self._light_index = self._themes.index(light) if light in self._themes else -1
            self._dark_index = self._themes.index(dark) if dark in self._themes else -1
            self._auto = cfg.get("UseDarkTheme", "False") == "True"
            self.themesChanged.emit()
            self.statusChanged.emit()
        except Exception as e:
            logger.warning(f"bridge fcitx refresh failed: {e}")

    @Slot(int)
    def setLight(self, index: int):
        if 0 <= index < len(self._themes):
            self._setLightIndex(index)

    @Slot(int)
    def setDark(self, index: int):
        if 0 <= index < len(self._themes):
            self._setDarkIndex(index)

    @Slot(bool)
    def setAuto(self, on: bool):
        self._setAuto(bool(on))

    @Slot(str)
    def setFilePath(self, url_or_path: str):
        path = url_or_path.strip()
        if path.startswith("file://"):
            try:
                path = QUrl(path).toLocalFile() or path
            except Exception:
                pass
        self._setFilePath(path)

    @Slot()
    def clearFilePath(self):
        self._setFilePath("")

    @Slot()
    def apply(self):
        start = time.monotonic()
        if self._file_path:
            try:
                name = fcitx_core.import_archive(self._file_path)
                fcitx_core.write_config(name, name, False)
                self._setFilePath("")
                self.refresh()
                self.message.emit("成功", "输入法主题配置已应用", False)
                log_operation(f"输入法/导入主题 {name}", True, time.monotonic() - start)
            except Exception as e:
                self.message.emit("导入失败", str(e), True)
                log_operation("输入法/导入主题", False, time.monotonic() - start, str(e))
            return
        light = self._themes[self._light_index] if 0 <= self._light_index < len(self._themes) else ""
        dark = self._themes[self._dark_index] if 0 <= self._dark_index < len(self._themes) else ""
        if not light and not dark:
            self.message.emit("提示", "请至少选择一个主题！", True)
            return
        try:
            fcitx_core.write_config(light, dark, self._auto)
            self.refresh()
            self.message.emit("成功", "输入法主题配置已应用", False)
            log_operation(f"输入法/应用 {light}/{dark}", True, time.monotonic() - start)
        except Exception as e:
            self.message.emit("失败", f"应用配置失败：{e}", True)
            log_operation(f"输入法/应用 {light}/{dark}", False, time.monotonic() - start, str(e))
