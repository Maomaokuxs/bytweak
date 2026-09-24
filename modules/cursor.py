import os
from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMessageBox, QFileDialog

from . import cursor_core
from .utils import logger


class CursorManager(QObject):
    """Widgets 薄层：下拉/预览/弹窗，逻辑全部走 cursor_core。"""

    def __init__(self, app_ctx):
        super().__init__(app_ctx.window if hasattr(app_ctx, "window") else None)
        self.ctx = app_ctx
        from PySide6.QtCore import QTimer
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self.update_cursor_preview)
        try:
            if self.ctx.cursor_preview_lbl:
                self.ctx.cursor_preview_lbl.installEventFilter(self)
            if self.ctx.window:
                self.ctx.window.installEventFilter(self)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            if obj in (self.ctx.cursor_preview_lbl, self.ctx.window):
                try:
                    self._debounce_timer.stop()
                    self._debounce_timer.start(80)
                except Exception:
                    self.update_cursor_preview()
        return False

    def refresh_cursor_themes_combo(self):
        if not self.ctx.cursor_theme_combo:
            return
        valid_themes = cursor_core.list_themes()
        self.ctx.cursor_theme_combo.clear()
        self.ctx.cursor_theme_combo.addItems(valid_themes)
        logger.debug(f"cursor themes loaded: {len(valid_themes)}")
        true_theme = cursor_core.read_current_theme()
        if true_theme:
            logger.debug(f"KDE cursorTheme: {true_theme}")
            index = self.ctx.cursor_theme_combo.findText(true_theme)
            if index == -1:
                for i in range(self.ctx.cursor_theme_combo.count()):
                    if self.ctx.cursor_theme_combo.itemText(i).lower() == true_theme.lower():
                        index = i
                        break
            if index != -1:
                self.ctx.cursor_theme_combo.setCurrentIndex(index)

    def smart_browse_cursor(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.ctx.window, "选择鼠标主题压缩包", os.path.expanduser("~/Downloads"), "鼠标包 (*.tar.gz *.tar.xz *.zip *.tgz)"
        )
        if file_path:
            self.ctx.cursor_path_edit.setText(file_path)

    def dispatch_cursor_apply(self):
        user_input_path = self.ctx.cursor_path_edit.text().strip() if self.ctx.cursor_path_edit else ""
        if user_input_path:
            try:
                theme_dir_name = cursor_core.import_archive(user_input_path)
                cursor_core.apply_theme(theme_dir_name)
                self.refresh_cursor_themes_combo()
                if self.ctx.cursor_theme_combo:
                    idx = self.ctx.cursor_theme_combo.findText(theme_dir_name)
                    if idx != -1:
                        self.ctx.cursor_theme_combo.setCurrentIndex(idx)
                if self.ctx.cursor_path_edit:
                    self.ctx.cursor_path_edit.clear()
                self.update_cursor_preview()
                QMessageBox.information(self.ctx.window, "成功", f"外部鼠标主题 【{theme_dir_name}】 导入并应用成功！")
            except Exception as e:
                QMessageBox.critical(self.ctx.window, "导入失败", str(e))
        else:
            if not self.ctx.cursor_theme_combo or self.ctx.cursor_theme_combo.currentIndex() == -1:
                QMessageBox.warning(self.ctx.window, "提示", "请选择本地鼠标主题，或导入外部压缩包！")
                return
            target_theme = self.ctx.cursor_theme_combo.currentText()
            try:
                cursor_core.apply_theme(target_theme)
                self.update_cursor_preview()
                QMessageBox.information(self.ctx.window, "切换成功", f"鼠标主题已成功切换为 【{target_theme}】！")
            except Exception as e:
                QMessageBox.critical(self.ctx.window, "失败", str(e))

    def update_cursor_preview(self):
        if not self.ctx.cursor_theme_combo or not self.ctx.cursor_preview_lbl:
            return
        selected_theme = self.ctx.cursor_theme_combo.currentText()
        if not selected_theme:
            self.ctx.cursor_preview_lbl.setText("暂无预览")
            return
        lbl = self.ctx.cursor_preview_lbl
        avail_w = lbl.width() if lbl.width() > 40 else 320
        avail_w = max(160, avail_w - 16)
        if avail_w < 360:
            cols = 4
        elif avail_w < 560:
            cols = 6
        else:
            cols = 8
        cols = min(cols, len(cursor_core.CURSOR_SLOTS))
        canvas_img, drawn, total = cursor_core.render_preview(selected_theme, cols)
        canvas = QPixmap.fromImage(canvas_img)
        if drawn > 0:
            self.ctx.cursor_preview_lbl.setStyleSheet("QLabel { border: 1px solid palette(mid); border-radius: 8px; }")
            self.ctx.cursor_preview_lbl.setPixmap(canvas)
            self.ctx.cursor_preview_lbl.setToolTip(f"{selected_theme} — 已预览 {drawn}/{total} 种样式")
        else:
            self.ctx.cursor_preview_lbl.setStyleSheet("QLabel { border: 1px dashed palette(mid); border-radius: 8px; color: palette(mid); font-weight: bold; font-size: 13px; }")
            self.ctx.cursor_preview_lbl.setText(f"{selected_theme}\n[无标准素材]")
