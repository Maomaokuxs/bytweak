import os
from PySide6.QtWidgets import QMessageBox, QFileDialog, QInputDialog

from . import grub_core
from .utils import logger, run_pkexec_shell
from .workers import Worker


class GrubManager:
    """Widgets 薄层：控件读写 + 弹窗，逻辑全部走 grub_core。"""

    def __init__(self, app_ctx):
        self.ctx = app_ctx
        self.system_themes_root = grub_core.SYSTEM_THEMES_ROOT
        self._workers: list[Worker] = []

    def refresh_local_themes_combo(self):
        """下拉框即当前状态：选中项默认定位到正在使用的主题。"""
        if not self.ctx.grub_theme_combo:
            return
        try:
            valid_themes = grub_core.list_local_themes()
            current, _ = grub_core.get_current_theme()
            self.ctx.grub_theme_combo.clear()
            self.ctx.grub_theme_combo.addItems(valid_themes)
            if current in valid_themes:
                self.ctx.grub_theme_combo.setCurrentIndex(valid_themes.index(current))
            logger.debug(f"grub combo synced to '{current}'")
        except Exception as e:
            logger.warning(f"refresh_local_themes_combo failed: {e}")

    def dispatch_grub_apply(self):
        user_input_path = self.ctx.grub_path_edit.text().strip()
        if user_input_path:
            self.apply_grub_theme_archive(user_input_path)
        else:
            self.apply_local_grub_theme_switch()

    def apply_local_grub_theme_switch(self):
        if not self.ctx.grub_theme_combo or self.ctx.grub_theme_combo.currentIndex() == -1:
            return
        selected_name = self.ctx.grub_theme_combo.currentText()
        try:
            script = grub_core.build_switch_script(selected_name, self.system_themes_root)
        except ValueError as e:
            QMessageBox.critical(self.ctx.window, "错误", str(e))
            return
        self._run_async(script, f"成功切换本地已有主题：【{selected_name}】")

    def smart_browse_grub(self):
        file_path, _ = QFileDialog.getOpenFileName(self.ctx.window, "选择 GRUB 主题", os.path.expanduser("~/Downloads"), "所有文件 (*)")
        if file_path:
            self.ctx.grub_path_edit.setText(file_path)

    def apply_grub_theme_archive(self, user_input_path):
        try:
            sandbox_dir = grub_core.extract_archive(user_input_path)
            detected_themes = grub_core.find_theme_dirs(sandbox_dir)
        except Exception as e:
            QMessageBox.critical(self.ctx.window, "解析失败", str(e))
            return

        if len(detected_themes) == 1:
            final_source_dir = list(detected_themes.values())[0]
        else:
            chosen, ok = QInputDialog.getItem(self.ctx.window, "选择版本", "分辨率款式选择：", sorted(list(detected_themes.keys())), current=0, editable=False)
            if not ok:
                grub_core.cleanup_sandbox(sandbox_dir)
                return
            final_source_dir = detected_themes[chosen]

        try:
            script, _ = grub_core.build_install_script(final_source_dir, self.system_themes_root)
        except ValueError as e:
            QMessageBox.critical(self.ctx.window, "解析失败", str(e))
            grub_core.cleanup_sandbox(sandbox_dir)
            return

        def on_success():
            self.refresh_local_themes_combo()
            if self.ctx.grub_path_edit:
                self.ctx.grub_path_edit.clear()
            QMessageBox.information(self.ctx.window, "成功", "外部主题安装应用成功！")

        self._run_async(script, None, on_success_cb=on_success, sandbox=sandbox_dir)

    def _run_async(self, script: str, success_msg: str | None, on_success_cb=None, sandbox: str | None = None):
        if self.ctx.grub_apply_btn:
            self.ctx.grub_apply_btn.setEnabled(False)
            self.ctx.grub_apply_btn.setText("执行中，请稍候...")

        def _task():
            result = run_pkexec_shell(script, timeout=300)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "执行失败")
            return result

        worker = Worker(_task)
        self._workers.append(worker)

        def on_ok(_):
            grub_core.cleanup_sandbox(sandbox) if sandbox else None
            if on_success_cb:
                on_success_cb()
            elif success_msg:
                QMessageBox.information(self.ctx.window, "成功", success_msg)
                self.refresh_local_themes_combo()
            self._restore_button(worker)

        def on_err(msg: str):
            grub_core.cleanup_sandbox(sandbox) if sandbox else None
            if "canceled" in msg.lower() or "dismissed" in msg.lower():
                logger.debug("grub pkexec canceled")
            else:
                QMessageBox.critical(self.ctx.window, "失败", f"GRUB 操作失败:\n{msg}")
            self._restore_button(worker)

        worker.finished_ok.connect(on_ok)
        worker.finished_err.connect(on_err)
        worker.start()

    def _restore_button(self, worker: Worker):
        if self.ctx.grub_apply_btn:
            self.ctx.grub_apply_btn.setEnabled(True)
            self.ctx.grub_apply_btn.setText("写入并更新 GRUB")
        try:
            worker.finished_ok.disconnect()
            worker.finished_err.disconnect()
        except Exception:
            pass
        if worker in self._workers:
            self._workers.remove(worker)
        worker.deleteLater()
