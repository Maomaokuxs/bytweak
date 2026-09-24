"""软件源 QML 桥接：repo_core 扫描 + 开关分发，后台执行复用 Worker。"""
from PySide6.QtCore import QObject, Signal, Property, Slot

from . import repo_core
from .utils import logger, run_pkexec, run_pkexec_shell
from .workers import Worker


class RepoBridge(QObject):
    reposChanged = Signal()
    recommendedChanged = Signal()
    busyChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._repos: list[dict] = []
        self._recommended: list[dict] = []
        self._busy = False
        self._loading = False
        self._workers: list[Worker] = []

    def getRepos(self):
        return self._repos

    repoList = Property(list, getRepos, notify=reposChanged)

    def getRecommended(self):
        return self._recommended

    recommendedList = Property(list, getRecommended, notify=recommendedChanged)

    def getBusy(self):
        return self._busy

    def _setBusy(self, v):
        if self._busy != v:
            self._busy = v
            self.busyChanged.emit()

    busy = Property(bool, getBusy, notify=busyChanged)

    @Slot()
    def refresh(self):
        if self._loading:
            return
        self._loading = True
        try:
            self._repos = repo_core.scan_local_repos()
            self.reposChanged.emit()
            self._recommended = repo_core.scan_recommended()
            self.recommendedChanged.emit()
            logger.debug(f"repo bridge scan: {len(self._repos)} local")
        except Exception as e:
            logger.warning(f"bridge repo refresh failed: {e}")
        finally:
            self._loading = False

    @Slot(str, bool)
    def toggleRepo(self, repo_id: str, enable: bool):
        if self._busy or self._loading:
            return
        try:
            cmd = repo_core.build_toggle_cmd(repo_id, enable)
        except ValueError as e:
            self.message.emit("错误", str(e), True)
            self.refresh()
            return

        def _task():
            result = run_pkexec(cmd, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
            return result

        self._run_async(_task, "配置成功")

    @Slot(str, bool)
    def toggleRecommended(self, rec_id: str, enable: bool):
        if self._busy or self._loading:
            return
        try:
            script = repo_core.build_recommended_script(rec_id, enable)
        except ValueError as e:
            self.message.emit("错误", str(e), True)
            return

        def _task():
            result = run_pkexec_shell(script, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
            return result

        self._run_async(_task, "配置成功")

    def _run_async(self, task_fn, success_msg: str):
        self._setBusy(True)
        worker = Worker(task_fn)
        self._workers.append(worker)

        def on_ok(_):
            self._setBusy(False)
            self.message.emit("提示", success_msg, False)
            self._cleanup(worker)
            self.refresh()

        def on_err(msg: str):
            self._setBusy(False)
            if "canceled" not in msg.lower() and "dismissed" not in msg.lower():
                self.message.emit("改写失败", f"操作失败:\n{msg}", True)
            self._cleanup(worker)
            self.refresh()

        worker.finished_ok.connect(on_ok)
        worker.finished_err.connect(on_err)
        worker.start()

    def _cleanup(self, worker: Worker):
        try:
            worker.finished_ok.disconnect()
            worker.finished_err.disconnect()
        except Exception:
            pass
        if worker in self._workers:
            self._workers.remove(worker)
        worker.deleteLater()
