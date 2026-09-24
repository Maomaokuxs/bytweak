import os
from PySide6.QtWidgets import QMessageBox, QFileDialog

from . import fcitx_core


class FcitxManager:
    """Widgets 薄层：控件读写 + 弹窗，逻辑全部走 fcitx_core。"""

    def __init__(self, app_ctx):
        self.ctx = app_ctx
        self.config_path = fcitx_core.CONFIG_PATH
        self.user_themes = fcitx_core.USER_THEMES
        self.sys_themes = fcitx_core.SYS_THEMES

    def refresh_current_theme(self):
        if not self.ctx.fcitx_current_theme_lbl:
            return
        self.ctx.fcitx_current_theme_lbl.setText(fcitx_core.theme_status_text())

    def refresh_theme_combos(self):
        themes = fcitx_core.scan_themes(self.user_themes, self.sys_themes)
        cfg = fcitx_core.read_config(self.config_path)
        for combo_name, key in [("fcitx_theme_combo", "Theme"),
                                ("fcitx_dark_theme_combo", "DarkTheme")]:
            combo = getattr(self.ctx, combo_name, None)
            if not combo:
                continue
            combo.clear()
            combo.addItems(themes)
            current = cfg.get(key)
            if current:
                idx = combo.findText(current)
                if idx != -1:
                    combo.setCurrentIndex(idx)
        check = self.ctx.fcitx_auto_switch_check
        if check:
            check.setChecked(cfg.get("UseDarkTheme", "False") == "True")

    def smart_browse_theme(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.ctx.window, "选择 Fcitx5 主题压缩包",
            os.path.expanduser("~/Downloads"),
            "主题包 (*.tar.gz *.tar.xz *.zip *.tgz)"
        )
        if file_path:
            self.ctx.fcitx_path_edit.setText(file_path)

    def dispatch_apply(self):
        user_path = self.ctx.fcitx_path_edit.text().strip() if self.ctx.fcitx_path_edit else ""
        if user_path:
            self._import_from_archive(user_path)
        else:
            light = self.ctx.fcitx_theme_combo.currentText() if self.ctx.fcitx_theme_combo else ""
            dark = self.ctx.fcitx_dark_theme_combo.currentText() if self.ctx.fcitx_dark_theme_combo else ""
            auto = self.ctx.fcitx_auto_switch_check.isChecked() if self.ctx.fcitx_auto_switch_check else False
            if not light and not dark:
                QMessageBox.warning(self.ctx.window, "提示", "请至少选择一个主题！")
                return
            self._apply_config(light, dark, auto)

    def _apply_config(self, light_theme, dark_theme, auto_switch):
        try:
            fcitx_core.write_config(light_theme, dark_theme, auto_switch, self.config_path)
            self.refresh_current_theme()
            self.refresh_theme_combos()
            QMessageBox.information(self.ctx.window, "成功", "输入法主题配置已应用")
        except Exception as e:
            QMessageBox.critical(self.ctx.window, "失败", f"应用配置失败：{e}")

    def _import_from_archive(self, archive_path):
        try:
            theme_name = fcitx_core.import_archive(archive_path, self.user_themes)
            self._apply_config(theme_name, theme_name, False)
        except Exception as e:
            QMessageBox.critical(self.ctx.window, "导入失败", str(e))
