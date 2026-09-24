from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem, QMessageBox

from . import repo_core
from .utils import logger, run_pkexec, run_pkexec_shell
from .workers import Worker


class RepoManager:
    """Widgets 薄层：列表渲染 + 开关分发，逻辑全部走 repo_core。"""

    def __init__(self, app_ctx):
        self.ctx = app_ctx
        self._workers: list[Worker] = []
        logger.debug("RepoManager mounted")

    def scan_and_render_system_repos(self):
        if not self.ctx.repo_list_widget:
            return
        self.ctx._is_loading_repos = True
        logger.debug("SYSTEM REPOS SCAN START")
        try:
            repos = repo_core.scan_local_repos()
        except Exception as e:
            logger.warning(f"scan failed: {e}")
            repos = []
        self.ctx.repo_list_widget.clear()
        for r in repos:
            item = QListWidgetItem(f"{r['name']}\n[{r['id']}]")
            item.setData(Qt.UserRole, r["id"])
            item.setCheckState(Qt.Checked if r["enabled"] else Qt.Unchecked)
            self.ctx.repo_list_widget.addItem(item)
        logger.debug(f"local repos: {len(repos)}")

        if self.ctx.recommended_repo_list:
            self.ctx.recommended_repo_list.clear()
            for r in repo_core.scan_recommended():
                rec_item = QListWidgetItem(r["label"])
                rec_item.setData(Qt.UserRole, r["id"])
                rec_item.setCheckState(Qt.Checked if r["installed"] else Qt.Unchecked)
                self.ctx.recommended_repo_list.addItem(rec_item)

        self.ctx._is_loading_repos = False
        logger.debug("SYSTEM REPOS SCAN END")

    def _run_privileged_shell(self, script: str):
        result = run_pkexec_shell(script, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
        return result

    def _run_privileged_cmd(self, cmd: list[str]):
        result = run_pkexec(cmd, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
        return result

    def dispatch_recommended_toggle_on_click(self, item):
        if getattr(self.ctx, "_is_loading_repos", False):
            return
        rec_id = item.data(Qt.UserRole)
        is_now_checked = item.checkState() == Qt.Checked
        logger.debug(f"RECOMMENDED {rec_id} -> {'enable' if is_now_checked else 'disable'}")
        try:
            shell_script = repo_core.build_recommended_script(rec_id, is_now_checked)
        except ValueError as e:
            logger.warning(str(e))
            return

        def _task():
            return self._run_privileged_shell(shell_script)

        self._run_async_task(_task, item, is_now_checked, which="recommended")

    def dispatch_repo_toggle_on_click(self, item):
        if getattr(self.ctx, "_is_loading_repos", False):
            return
        repo_id = item.data(Qt.UserRole)
        is_now_checked = item.checkState() == Qt.Checked
        logger.debug(f"LOCAL REPO {repo_id} -> {'enable' if is_now_checked else 'disable'}")
        try:
            cmd = repo_core.build_toggle_cmd(repo_id, is_now_checked)
        except ValueError as e:
            QMessageBox.critical(self.ctx.window, "错误", str(e))
            item.setCheckState(Qt.Unchecked if is_now_checked else Qt.Checked)
            return

        def _task():
            return self._run_privileged_cmd(cmd)

        self._run_async_task(_task, item, is_now_checked, which="local")

    def _run_async_task(self, task_fn, item, is_now_checked: bool, which="local"):
        target = self.ctx.recommended_repo_list if which == "recommended" else self.ctx.repo_list_widget
        if target:
            target.setEnabled(False)

        worker = Worker(task_fn)
        self._workers.append(worker)

        def on_ok(_):
            QMessageBox.information(self.ctx.window, "提示", "配置成功")
            self._cleanup_worker(worker)
            self._reenable_and_refresh()

        def on_err(msg: str):
            try:
                item.setCheckState(Qt.Unchecked if is_now_checked else Qt.Checked)
            except Exception:
                pass
            if "canceled" in msg.lower() or "dismissed" in msg.lower():
                logger.debug("pkexec canceled by user")
            else:
                QMessageBox.critical(self.ctx.window, "改写失败", f"操作失败:\n{msg}")
            self._cleanup_worker(worker)
            self._reenable_and_refresh()

        worker.finished_ok.connect(on_ok)
        worker.finished_err.connect(on_err)
        worker.start()

    def _reenable_and_refresh(self):
        try:
            if self.ctx.repo_list_widget:
                self.ctx.repo_list_widget.setEnabled(True)
            if self.ctx.recommended_repo_list:
                self.ctx.recommended_repo_list.setEnabled(True)
        except Exception:
            pass
        self.scan_and_render_system_repos()

    def _cleanup_worker(self, worker: Worker):
        try:
            worker.finished_ok.disconnect()
            worker.finished_err.disconnect()
        except Exception:
            pass
        if worker in self._workers:
            self._workers.remove(worker)
        worker.deleteLater()
