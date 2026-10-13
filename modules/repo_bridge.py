"""软件源 QML 桥接：repo_core 扫描 + 开关分发，后台执行复用 Worker。"""
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import time

from PySide6.QtCore import QObject, Signal, Property, Slot

from . import repo_core
from .utils import logger, run_pkexec, run_pkexec_shell
from .workers import Worker

# COPR API 在国内网络常被间歇性阻断：超时压短 + 失败后熔断冷却，
# 避免每次搜索都干等，也避免整个搜索因 COPR 失败而失败。
COPR_QUERY_TIMEOUT = 45
COPR_COOLDOWN = 90


class RepoBridge(QObject):
    reposChanged = Signal()
    recommendedChanged = Signal()
    busyChanged = Signal()
    busyLabelChanged = Signal()
    coprResultsChanged = Signal()
    # 搜索超时提示：30 秒未完成时触发，QML 弹框让用户选择继续等待或终止
    searchTimeout = Signal(str)
    coprPackagesChanged = Signal()
    coprBusyChanged = Signal()
    pkgResultsChanged = Signal()
    installedPkgsChanged = Signal()
    upgradableChanged = Signal()
    upgradesCheckedChanged = Signal()
    cacheSizeChanged = Signal()
    lastOutputChanged = Signal()
    opLogChanged = Signal()
    officialHintsChanged = Signal()
    coprErrorChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._repos: list[dict] = []
        self._recommended: list[dict] = []
        self._busy = False
        self._busyLabel = ""
        self._loading = False
        self._coprResults: list[dict] = []
        self._coprPackages: list[str] = []
        self._coprBusy = False
        self._coprError = ""
        self._coprDownUntil = 0.0
        self._pkgResults: list[dict] = []
        self._installedPkgs: list[str] = []
        self._upgradable: list[dict] = []
        self._upgradesChecked = False
        self._cacheSize = "—"
        self._lastOutput = ""
        self._opLogText = ""
        self._officialHints: dict = {}
        self._workers: list[Worker] = []
        self._currentWorker = None
        self._promptTimer = None

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

    def getBusyLabel(self):
        return self._busyLabel

    def _setBusyLabel(self, v: str):
        if self._busyLabel != v:
            self._busyLabel = v
            self.busyLabelChanged.emit()

    busyLabel = Property(str, getBusyLabel, notify=busyLabelChanged)

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
            self._cacheSize = repo_core.get_cache_size()
            self.cacheSizeChanged.emit()
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

        self._run_async(_task, "配置成功", label=f"软件源/开关 {repo_id} → {'启用' if enable else '禁用'}", timeout=720)

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

        self._run_async(_task, "配置成功", label=f"推荐源/开关 {rec_id} → {'安装' if enable else '移除'}", timeout=720)

    def _run_async(self, task_fn, success_msg: str, after=None, label: str = "", timeout: float = 0):
        self._setBusy(True)
        self._setBusyLabel(label or "正在执行…")
        worker = Worker(task_fn, label=label or "软件源/提权执行", timeout=timeout)
        self._workers.append(worker)

        def on_ok(result):
            self._setBusy(False)
            self._setBusyLabel("")
            try:
                out = (getattr(result, "stdout", "") or "")
                err = (getattr(result, "stderr", "") or "")
                body = out + ("\n" + err if err.strip() else "")
                self._setLastOutput(f"【{label or success_msg}】执行成功", body)
            except Exception:
                pass
            self.message.emit("提示", success_msg, False)
            self._cleanup(worker)
            self.refresh()
            if after is not None:
                after()

        def on_err(msg: str):
            self._setBusy(False)
            self._setBusyLabel("")
            self._setLastOutput(f"【{label or '操作'}】执行失败", msg)
            if "canceled" not in msg.lower() and "dismissed" not in msg.lower():
                hint = repo_core.diagnose_failure(msg)
                prefix = f"⚠ {hint}\n\n" if hint else ""
                self.message.emit("操作失败", f"{prefix}{msg[:500]}", True)
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
        # 超时线程任其自生自灭：不再触碰，避免销毁仍在运行的线程导致崩溃
        if not getattr(worker, "timed_out", False):
            worker.deleteLater()

    # ---------- COPR：搜索 / 包列表 / 启用 / 装包 ----------

    def getCoprError(self):
        return self._coprError

    coprError = Property(str, getCoprError, notify=coprErrorChanged)

    def _set_copr_error(self, msg: str):
        msg = (msg or "").strip()
        if self._coprError != msg:
            self._coprError = msg
            self.coprErrorChanged.emit()

    def _copr_guard(self, fn, *args):
        """COPR 调用统一入口：熔断冷却期内直接快速失败；失败则进入冷却。"""
        left = self._coprDownUntil - time.monotonic()
        if left > 0:
            raise RuntimeError(f"COPR 暂时不可用，{int(left) + 1} 秒后自动重试")
        try:
            result = self._query_guarded(fn, *args)
            if self._coprDownUntil > 0:
                logger.info("COPR 熔断恢复：API 调用成功")
            self._coprDownUntil = 0.0
            return result
        except Exception as e:
            self._coprDownUntil = time.monotonic() + COPR_COOLDOWN
            logger.exception(f"COPR 熔断触发（{COPR_COOLDOWN}s）")
            raise

    def getCoprResults(self):
        return self._coprResults

    coprResults = Property(list, getCoprResults, notify=coprResultsChanged)

    def getPkgResults(self):
        return self._pkgResults

    pkgResults = Property(list, getPkgResults, notify=pkgResultsChanged)

    def getUpgradable(self):
        return self._upgradable

    upgradablePkgs = Property(list, getUpgradable, notify=upgradableChanged)

    def getUpgradesChecked(self):
        return self._upgradesChecked

    upgradesChecked = Property(bool, getUpgradesChecked, notify=upgradesCheckedChanged)

    def getCacheSize(self):
        return self._cacheSize

    cacheSize = Property(str, getCacheSize, notify=cacheSizeChanged)

    def getLastOutput(self):
        return self._lastOutput

    lastOutput = Property(str, getLastOutput, notify=lastOutputChanged)

    def _setLastOutput(self, title: str, body: str):
        body = (body or "").strip()
        self._lastOutput = title + ("\n\n" + body[-3000:] if body else "")
        self.lastOutputChanged.emit()

    def getOpLog(self):
        return self._opLogText

    opLogText = Property(str, getOpLog, notify=opLogChanged)

    def getInstalledPkgs(self):
        return self._installedPkgs

    installedPkgs = Property(list, getInstalledPkgs, notify=installedPkgsChanged)

    def _merge_installed(self, names):
        merged = list(dict.fromkeys(list(self._installedPkgs) + list(names or [])))
        if merged != self._installedPkgs:
            self._installedPkgs = merged
            self.installedPkgsChanged.emit()

    def _prune_installed(self, names):
        doomed = set(names or [])
        pruned = [n for n in self._installedPkgs if n not in doomed]
        if pruned != self._installedPkgs:
            self._installedPkgs = pruned
            self.installedPkgsChanged.emit()

    def getCoprPackages(self):
        return self._coprPackages

    coprPackages = Property(list, getCoprPackages, notify=coprPackagesChanged)

    def getCoprBusy(self):
        return self._coprBusy

    def _setCoprBusy(self, v):
        if self._coprBusy != v:
            self._coprBusy = v
            self.coprBusyChanged.emit()

    coprBusy = Property(bool, getCoprBusy, notify=coprBusyChanged)

    @staticmethod
    def _query_guarded(fn, *args):
        """网络查询加超时保护（copr.v3 自身无超时参数）。
        线程池不等待回收：极端卡死时 worker 照常返回，界面不被拖住。"""
        ex = ThreadPoolExecutor(max_workers=1)
        try:
            fut = ex.submit(fn, *args)
            try:
                return fut.result(timeout=COPR_QUERY_TIMEOUT)
            except FuturesTimeoutError:
                raise RuntimeError("COPR 请求超时，请检查网络后重试")
        finally:
            ex.shutdown(wait=False, cancel_futures=True)

    def _run_lookup(self, task_fn, on_data, label: str = "", timeout: float = 300):
        if self._coprBusy:
            return
        self._setCoprBusy(True)
        self._setBusyLabel(label or "正在查询…")
        worker = Worker(task_fn, label=label or "软件源/查询", timeout=timeout)
        self._workers.append(worker)
        self._currentWorker = worker

        def on_ok(data):
            self._setCoprBusy(False)
            self._currentWorker = None
            if self._promptTimer:
                self._promptTimer.stop()
            on_data(data)
            self._cleanup(worker)

        def on_err(msg: str):
            self._setCoprBusy(False)
            self._currentWorker = None
            if self._promptTimer:
                self._promptTimer.stop()
            hint = repo_core.diagnose_failure(msg)
            prefix = f"⚠ {hint}\n\n" if hint else ""
            self.message.emit("查询失败", f"{prefix}{msg}", True)
            self._cleanup(worker)

        worker.finished_ok.connect(on_ok)
        worker.finished_err.connect(on_err)
        worker.start()
        # 30 秒未完成：提示用户是否继续等待
        from PySide6.QtCore import QTimer
        self._promptTimer = QTimer(self)
        self._promptTimer.setSingleShot(True)
        self._promptTimer.timeout.connect(lambda: self._on_search_slow(label))
        self._promptTimer.start(120000)  # 2 分钟后提示用户是否继续等待

    def _on_search_slow(self, label: str):
        # 30 秒还没完成（且 worker 还在跑）：弹框让用户选
        if self._currentWorker and self._currentWorker.isRunning():
            self.searchTimeout.emit(label or "搜索")

    @Slot()
    def cancelSearch(self):
        """用户选择终止搜索：放弃等待，后台线程结果会被丢弃。"""
        if self._promptTimer:
            self._promptTimer.stop()
        # 标记超时，后续结果不再上报（复用 Worker 的 timed_out 机制）
        if self._currentWorker:
            self._currentWorker.timed_out = True
        self._currentWorker = None
        self._setCoprBusy(False)
        self._set_copr_error("已取消搜索")

    def _merge_hints(self, hints: dict):
        merged = dict(self._officialHints)
        merged.update(hints or {})
        self._officialHints = merged
        self.officialHintsChanged.emit()

    def getOfficialHints(self):
        return self._officialHints

    officialHints = Property('QVariant', getOfficialHints, notify=officialHintsChanged)

    @Slot(str)
    def unifiedSearch(self, keyword: str):
        """统一搜索：官方源包名 + COPR 项目，一次返回。"""
        kw = (keyword or "").strip()
        if len(kw) < 2:
            self.message.emit("错误", "搜索关键词至少 2 个字符", True)
            return

        def _task():
            try:
                official = repo_core.search_available_packages(kw)
            except ValueError:
                official = []
            projects, copr_error = [], ""
            try:
                projects = self._copr_guard(repo_core.search_copr_projects, kw)
            except Exception as e:
                copr_error = str(e)
            try:
                installed = repo_core.check_installed([p["name"] for p in official])
            except Exception:
                installed = []
            return {"official": official, "projects": projects,
                    "installed": installed, "copr_error": copr_error}

        def _done(data):
            self._pkgResults = data.get("official", [])
            self.pkgResultsChanged.emit()
            self._coprResults = data.get("projects", [])
            self.coprResultsChanged.emit()
            self._merge_installed(data.get("installed", []))
            self._set_copr_error(data.get("copr_error", ""))

        self._run_lookup(_task, _done, label=f"搜索/统一 {kw}")

    @Slot(str)
    def searchCopr(self, keyword: str):
        def _task():
            return self._copr_guard(repo_core.search_copr_projects, keyword)

        def _done(data):
            self._coprResults = data
            self.coprResultsChanged.emit()
            self._set_copr_error("")

        self._run_lookup(_task, _done, label=f"搜索/COPR {keyword.strip()}")

    @Slot(str, str)
    def listCoprPackages(self, owner: str, project: str):
        def _task():
            pkgs, copr_error = [], ""
            try:
                pkgs = self._copr_guard(repo_core.list_copr_packages, owner, project)
            except Exception as e:
                copr_error = str(e)
            try:
                found = repo_core.check_official_available(pkgs)
            except Exception:
                found = {}
            hints = {k: {"repo": v, "source": repo_core.classify_repo(v)}
                     for k, v in found.items()}
            try:
                installed = repo_core.check_installed(pkgs)
            except Exception:
                installed = []
            return {"packages": pkgs, "hints": hints, "installed": installed,
                    "copr_error": copr_error}

        def _done(data):
            self._coprPackages = data.get("packages", [])
            self.coprPackagesChanged.emit()
            self._merge_hints(data.get("hints", {}))
            self._merge_installed(data.get("installed", []))
            self._set_copr_error(data.get("copr_error", ""))

        self._run_lookup(_task, _done, label=f"查询/COPR包 {owner}/{project}")

    @Slot()
    def refreshOpLog(self):
        """读操作日志尾部（最多 80 行）供 QML 展示。"""
        try:
            from .utils import operations_log_path
            with open(operations_log_path(), encoding="utf-8", errors="ignore") as f:
                lines = f.read().split("\n")
            self._opLogText = "\n".join([l for l in lines if l.strip()][-80:])
        except Exception:
            self._opLogText = "暂无操作日志"
        self.opLogChanged.emit()

    @Slot()
    def clearOpLog(self):
        try:
            from .utils import operations_log_path
            open(operations_log_path(), "w", encoding="utf-8").close()
        except Exception as e:
            self.message.emit("错误", f"清空日志失败：{e}", True)
            return
        self.refreshOpLog()
        self.message.emit("提示", "操作日志已清空", False)

    @Slot(str)
    def checkOfficial(self, pkg: str):
        """查单个包的提供情况，结果并入 officialHints（{包名: {repo, source}}；
        未提供则记 source 为 none）。"""
        name = (pkg or "").strip()
        if not repo_core.PKG_NAME_PATTERN.match(name):
            self.message.emit("错误", f"非法包名: {pkg}", True)
            return

        def _task():
            found = repo_core.check_official_available([name])
            if name in found:
                return {name: {"repo": found[name],
                               "source": repo_core.classify_repo(found[name])}}
            return {name: {"repo": "", "source": "none"}}

        self._run_lookup(_task, self._merge_hints, label=f"查询/包来源 {name}")

    @Slot(str, str)
    def enableCopr(self, owner: str, project: str):
        if self._busy or self._loading:
            return
        try:
            cmd = repo_core.build_copr_enable_cmd(owner, project)
        except ValueError as e:
            self.message.emit("错误", str(e), True)
            return

        def _task():
            result = run_pkexec(cmd, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
            return result

        self._run_async(_task, "COPR 源已启用", label=f"COPR/启用 {owner}/{project}", timeout=720)

    @Slot(str)
    def installPackage(self, pkg: str):
        if self._busy or self._loading:
            return
        try:
            cmd = repo_core.build_install_cmd(pkg)
        except ValueError as e:
            self.message.emit("错误", str(e), True)
            return
        name = (pkg or "").strip()

        def _task():
            result = run_pkexec(cmd, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
            return result

        self._run_async(_task, "软件包安装成功", after=lambda: self._merge_installed([name]), label=f"软件包/安装 {name}", timeout=720)

    @Slot(str)
    def removePackage(self, pkg: str):
        if self._busy or self._loading:
            return
        try:
            cmd = repo_core.build_remove_cmd(pkg)
        except ValueError as e:
            self.message.emit("错误", str(e), True)
            return
        name = (pkg or "").strip()

        def _task():
            result = run_pkexec(cmd, timeout=600)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
            return result

        def _after():
            self._prune_installed([name])
            self.refreshUpgrades()

        self._run_async(_task, "软件包已卸载", after=_after, label=f"软件包/卸载 {name}", timeout=720)

    @Slot()
    def refreshUpgrades(self):
        def _task():
            return repo_core.list_upgradable()

        def _done(data):
            self._upgradable = data
            self.upgradableChanged.emit()
            if not self._upgradesChecked:
                self._upgradesChecked = True
                self.upgradesCheckedChanged.emit()

        self._run_lookup(_task, _done, label="查询/可更新")

    @Slot()
    def upgradeAll(self):
        if self._busy or self._loading:
            return

        def _task():
            result = run_pkexec(repo_core.build_upgrade_cmd(), timeout=1800)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
            return result

        self._run_async(_task, "系统升级完成", after=self.refreshUpgrades, label="系统/一键升级", timeout=1920)

    @Slot()
    def autoremove(self):
        if self._busy or self._loading:
            return

        def _task():
            result = run_pkexec(repo_core.build_autoremove_cmd(), timeout=900)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
            return result

        self._run_async(_task, "孤包清理完成", after=self.refreshUpgrades, label="清理/自动移除孤包", timeout=1020)

    @Slot()
    def cleanCache(self):
        if self._busy or self._loading:
            return

        def _task():
            result = run_pkexec(repo_core.build_clean_cmd(), timeout=300)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pkexec 执行失败")
            return result

        self._run_async(_task, "缓存清理完成", label="清理/软件包缓存", timeout=420)
