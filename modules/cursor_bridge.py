"""光标 QML 桥接：cursor_core 主题管理 + 预览图经 ImageProvider 供给 QML。"""
from PySide6.QtCore import QObject, Signal, Property, Slot, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from . import cursor_core
from .utils import logger


class CursorPreviewProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        # 预置 1x1 透明图，避免首帧空图触发 QML image provider 警告
        self.image = QImage(8, 8, QImage.Format_ARGB32)
        self.image.fill(0)

    def requestImage(self, _id, size, _requested):
        size.setWidth(self.image.width())
        size.setHeight(self.image.height())
        return self.image


class CursorBridge(QObject):
    themesChanged = Signal()
    filePathChanged = Signal()
    previewChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, provider: CursorPreviewProvider, parent=None):
        super().__init__(parent)
        self._provider = provider
        self._themes: list[str] = []
        self._current_index = -1
        self._file_path = ""
        self._tick = 0
        self._preview_info = ""

    def getThemes(self):
        return self._themes

    themeList = Property(list, getThemes, notify=themesChanged)

    def getCurrentIndex(self):
        return self._current_index

    def _setCurrentIndex(self, v):
        if self._current_index != v:
            self._current_index = v
            self.themesChanged.emit()

    currentThemeIndex = Property(int, getCurrentIndex, notify=themesChanged)

    def getFilePath(self):
        return self._file_path

    def _setFilePath(self, v):
        if self._file_path != v:
            self._file_path = v
            self.filePathChanged.emit()

    filePath = Property(str, getFilePath, notify=filePathChanged)

    def getTick(self):
        return self._tick

    previewTick = Property(int, getTick, notify=previewChanged)

    def getPreviewInfo(self):
        return self._preview_info

    previewInfo = Property(str, getPreviewInfo, notify=previewChanged)

    @Slot()
    def refresh(self):
        try:
            self._themes = cursor_core.list_themes()
            true_theme = cursor_core.read_current_theme()
            idx = -1
            if true_theme:
                if true_theme in self._themes:
                    idx = self._themes.index(true_theme)
                else:
                    for i, name in enumerate(self._themes):
                        if name.lower() == true_theme.lower():
                            idx = i
                            break
            if idx == -1 and self._themes:
                idx = 0  # 与 Widgets 下拉框默认选中首项的行为一致
            self._current_index = idx
            self.themesChanged.emit()
            self._render_preview()
            logger.debug(f"cursor bridge themes: {len(self._themes)}")
        except Exception as e:
            logger.warning(f"bridge cursor refresh failed: {e}")

    @Slot(int)
    def setTheme(self, index: int):
        if 0 <= index < len(self._themes):
            self._setCurrentIndex(index)
            self._render_preview()

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
        if self._file_path:
            try:
                name = cursor_core.import_archive(self._file_path)
                cursor_core.apply_theme(name)
                self._setFilePath("")
                self.refresh()
                self.message.emit("成功", f"外部鼠标主题 【{name}】 导入并应用成功！", False)
            except Exception as e:
                self.message.emit("导入失败", str(e), True)
            return
        if not (0 <= self._current_index < len(self._themes)):
            self.message.emit("提示", "请选择本地鼠标主题，或导入外部压缩包！", True)
            return
        target = self._themes[self._current_index]
        try:
            cursor_core.apply_theme(target)
            self._render_preview()
            self.message.emit("切换成功", f"鼠标主题已成功切换为 【{target}】！", False)
        except Exception as e:
            self.message.emit("失败", str(e), True)

    def _render_preview(self, cols: int = 8):
        try:
            if 0 <= self._current_index < len(self._themes):
                img, drawn, total = cursor_core.render_preview(self._themes[self._current_index], cols)
                name = self._themes[self._current_index]
            else:
                img, drawn, total, name = QImage(), 0, 0, ""
            self._provider.image = img
            self._preview_info = f"{name} — 已预览 {drawn}/{total} 种样式" if drawn else "无标准素材"
            self._tick += 1
            self.previewChanged.emit()
        except Exception as e:
            logger.warning(f"cursor preview failed: {e}")
