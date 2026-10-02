"""GRUB QML 桥接：把 grub_core 纯逻辑暴露为 QML 属性/槽位，后台执行复用 Worker。"""
from PySide6.QtCore import QObject, Signal, Property, Slot, QUrl

from . import grub_core
from .utils import logger, run_pkexec_shell
from .workers import Worker


class GrubBridge(QObject):
    themesChanged = Signal()
    filePathChanged = Signal()
    busyChanged = Signal()
    # title, body, isError
    message = Signal(str, str, bool)
    # 多版本主题包待用户二选一时触发，QML 用 choiceList 弹窗展示
    choiceRequested = Signal()
    choiceChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._themes: list[str] = []
        self._current_index = -1
        self._file_path = ""
        self._busy = False
        self._choice_list: list[str] = []
        self._pending_source: dict[str, str] = {}
        self._pending_sandbox = ""
        self._workers: list[Worker] = []

    # ---------- 属性 ----------

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

    def getBusy(self):
        return self._busy

    def _setBusy(self, v):
        if self._busy != v:
            self._busy = v
            self.busyChanged.emit()

    busy = Property(bool, getBusy, notify=busyChanged)

    def getChoiceList(self):
        return self._choice_list

    choiceList = Property(list, getChoiceList, notify=choiceChanged)

    # ---------- 刷新 ----------

    @Slot()
    def refreshThemes(self):
        try:
            themes = grub_core.list_local_themes()
            current, _ = grub_core.get_current_theme()
            self._themes = themes
            self._current_index = themes.index(current) if current in themes else (-1 if not themes else 0)
            self.themesChanged.emit()
        except Exception as e:
            logger.warning(f"bridge refreshThemes failed: {e}")

    @Slot(str)
    def setFilePath(self, url_or_path: str):
        """QML FileDialog 传来 file:// URL 或纯路径，统一转本地路径。"""
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

    # ---------- 应用 ----------

    @Slot()
    def apply(self):
        if self._busy:
            return
        if self._file_path:
            self._apply_archive(self._file_path)
        else:
            self._apply_local()

    @Slot(int)
    def applyLocalTheme(self, index: int):
        """下拉选中即只记录索引，真正写入走 apply()；QML 也可直接按索引应用。"""
        if 0 <= index < len(self._themes):
            self._setCurrentIndex(index)

    def _apply_local(self):
        if not (0 <= self._current_index < len(self._themes)):
            self.message.emit("提示", "请先选择一个本地主题", True)
            return
        name = self._themes[self._current_index]
        try:
            script = grub_core.build_switch_script(name)
        except ValueError as e:
            self.message.emit("错误", str(e), True)
            return
        self._run_privileged(script, f"成功切换本地已有主题：【{name}】", label=f"GRUB/切换本地主题 {name}")

    def _apply_archive(self, path: str):
        try:
            sandbox = grub_core.extract_archive(path)
            detected = grub_core.find_theme_dirs(sandbox)
        except Exception as e:
            self.message.emit("解析失败", str(e), True)
            return
        if len(detected) == 1:
            self._install_source(next(iter(detected.values())), sandbox)
            return
        # 多版本：记下候选，通知 QML 弹窗让用户选
        self._pending_source = detected
        self._pending_sandbox = sandbox
        self._choice_list = sorted(detected.keys())
        self.choiceChanged.emit()
        self.choiceRequested.emit()

    @Slot(int)
    def chooseVariant(self, index: int):
        """用户在多版本弹窗中做出选择后继续安装；取消传 -1。"""
        if index < 0 or index >= len(self._choice_list):
            grub_core.cleanup_sandbox(self._pending_sandbox)
            self._reset_pending()
            return
        key = self._choice_list[index]
        source = self._pending_source.get(key)
        sandbox = self._pending_sandbox
        self._reset_pending()
        if source:
            self._install_source(source, sandbox)
        else:
            grub_core.cleanup_sandbox(sandbox)

    def _reset_pending(self):
        self._pending_source = {}
        self._pending_sandbox = ""
        if self._choice_list:
            self._choice_list = []
            self.choiceChanged.emit()

    def _install_source(self, source_dir: str, sandbox: str):
        try:
            script, _ = grub_core.build_install_script(source_dir)
        except ValueError as e:
            grub_core.cleanup_sandbox(sandbox)
            self.message.emit("解析失败", str(e), True)
            return

        def on_success():
            self.refreshThemes()
            self._setFilePath("")

        self._run_privileged(
            script, "外部主题安装应用成功！", on_success_cb=on_success, sandbox=sandbox,
            label=f"GRUB/安装外部主题 {source_dir.split('/')[-1]}"
        )

    # ---------- 后台执行 ----------

    def _run_privileged(self, script: str, success_msg: str, on_success_cb=None, sandbox: str = "", label: str = ""):
        self._setBusy(True)

        def _task():
            result = run_pkexec_shell(script, timeout=300)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "执行失败")
            return result

        worker = Worker(_task, label=label or "GRUB/提权执行", timeout=420)
        self._workers.append(worker)

        def on_ok(_):
            grub_core.cleanup_sandbox(sandbox)
            self._setBusy(False)
            if on_success_cb:
                on_success_cb()
            self.message.emit("成功", success_msg, False)
            self._cleanup(worker)

        def on_err(msg: str):
            grub_core.cleanup_sandbox(sandbox)
            self._setBusy(False)
            if "canceled" not in msg.lower() and "dismissed" not in msg.lower():
                self.message.emit("失败", f"GRUB 操作失败:\n{msg}", True)
            logger.debug("grub bridge pkexec finished/canceled")
            self._cleanup(worker)

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
        # 超时线程任其自生自灭：不再触碰，避免销毁仍在运行的线程导致崩溃
        if not getattr(worker, "timed_out", False):
            worker.deleteLater()
