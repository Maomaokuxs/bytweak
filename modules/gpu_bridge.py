"""显卡 QML 桥接：gpu_core 探测 + 一键修复，后台执行复用 Worker。"""
from PySide6.QtCore import QObject, Signal, Property, Slot

from . import gpu_core
from .utils import logger, run_pkexec_shell
from .workers import Worker

VENDOR_COLOR = {"NVIDIA": "#76b900", "AMD": "#ed1c24", "Intel": "#0071c5", "Unknown": "#6b7280"}


class GpuBridge(QObject):
    stateChanged = Signal()
    busyChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._level = "idle"
        self._gpus: list[dict] = []
        self._vendor = "Unknown"
        self._nvidia_installed = False
        self._perfect = False
        self._status = "正在侦测..."
        self._version = ""
        self._codec = {k: False for k in ("h264", "h265", "av1", "vp9", "nvenc", "vaapi")}
        self._action_text = "一键修复硬解"
        self._action_enabled = False
        self._busy = False
        self._workers: list[Worker] = []

    def _emit(self):
        self.stateChanged.emit()

    def getDeviceList(self):
        return [{"vendor": g["vendor"], "name": g["name"], "pci": g["pci"],
                 "color": VENDOR_COLOR.get(g["vendor"], "#6b7280")} for g in self._gpus]

    deviceList = Property(list, getDeviceList, notify=stateChanged)

    def getStatus(self):
        return self._status

    statusText = Property(str, getStatus, notify=stateChanged)

    def getVersion(self):
        return self._version

    versionText = Property(str, getVersion, notify=stateChanged)

    def getCodecList(self):
        items = [("h264", "H.264"), ("h265", "H.265"), ("av1", "AV1"),
                 ("vp9", "VP9"), ("vaapi", "VA-API")]
        if self._vendor == "NVIDIA":
            items.insert(4, ("nvenc", "NVENC"))
        else:
            items.insert(4, ("nvenc", "NVENC（仅 NVIDIA）"))
        return [{"name": name, "ok": bool(self._codec.get(key, False))} for key, name in items]

    codecList = Property(list, getCodecList, notify=stateChanged)

    def getActionText(self):
        return self._action_text

    actionText = Property(str, getActionText, notify=stateChanged)

    def getActionEnabled(self):
        return self._action_enabled and not self._busy

    actionEnabled = Property(bool, getActionEnabled, notify=stateChanged)

    def getLevel(self):
        # ok=状态完美 warn=需要处理 idle=未检出
        return self._level

    statusLevel = Property(str, getLevel, notify=stateChanged)

    def getBusy(self):
        return self._busy

    def _setBusy(self, v):
        if self._busy != v:
            self._busy = v
            self.busyChanged.emit()
            self.stateChanged.emit()

    busy = Property(bool, getBusy, notify=busyChanged)

    @Slot()
    def refresh(self):
        try:
            self._gpus = gpu_core.detect_gpus()
            self._vendor = gpu_core.primary_vendor(self._gpus)
            a = gpu_core.assess(self._vendor)
        except Exception as e:
            logger.warning(f"bridge gpu refresh failed: {e}")
            self._gpus = []
            self._vendor = "Unknown"
            a = {"nvidia_installed": False, "perfect": False, "status": f"检测失败: {e}",
                 "version": "", "codec": dict(self._codec)}
        self._nvidia_installed = a["nvidia_installed"]
        self._perfect = a["perfect"]
        self._level = "ok" if a["perfect"] else ("idle" if self._vendor == "Unknown" else "warn")
        self._status = a["status"]
        self._version = a["version"]
        self._codec = a["codec"]
        if self._perfect:
            self._action_text = "硬解状态完美，无需操作"
            self._action_enabled = False
        elif self._vendor == "NVIDIA":
            self._action_text = "一键安装闭源驱动 + 硬解" if not self._nvidia_installed else "一键打通 VA-API / NVENC"
            self._action_enabled = True
        elif self._vendor in ("AMD", "Intel"):
            self._action_text = f"一键激活 {self._vendor} 全格式硬解"
            self._action_enabled = True
        else:
            self._action_text = "一键检测"
            self._action_enabled = False
        self._emit()

    @Slot()
    def copyDiagnostics(self):
        """复制诊断摘要到剪贴板（设备 + 驱动 + 编解码矩阵纯文本）。"""
        try:
            from PySide6.QtWidgets import QApplication
            lines = ["Fedora Tweak Tool 显卡诊断"]
            for g in self._gpus:
                pci = f" [{g['pci']}]" if g["pci"] else ""
                lines.append(f"- {g['vendor']} · {g['name']}{pci}")
            lines.append(f"驱动：{self._status}")
            if self._version:
                lines.append(f"版本：{self._version}")
            states = []
            for key, name in [("h264", "H.264"), ("h265", "H.265"), ("av1", "AV1"),
                              ("vp9", "VP9"), ("nvenc", "NVENC"), ("vaapi", "VA-API")]:
                states.append(f"{name}={'OK' if self._codec.get(key) else '--'}")
            lines.append("硬解：" + " ".join(states))
            QApplication.clipboard().setText("\n".join(lines))
            self.message.emit("提示", "诊断信息已复制到剪贴板", False)
        except Exception as e:
            logger.warning(f"copy diagnostics failed: {e}")
            self.message.emit("失败", f"复制失败：{e}", True)

    @Slot()
    def apply(self):
        if self._busy or self._perfect or self._vendor == "Unknown":
            return
        try:
            script, success_msg = gpu_core.build_fix_script(self._vendor, self._nvidia_installed)
        except RuntimeError:
            return
        self.message.emit("准备整备环境", "工具即将拉起 Polkit 授权，请留意系统授权弹窗。授权后将在后台执行，界面不会卡死。", False)
        self._setBusy(True)

        def _task():
            result = run_pkexec_shell(script, timeout=1800)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "执行失败")
            return result

        worker = Worker(_task)
        self._workers.append(worker)

        def on_ok(_):
            self._setBusy(False)
            self.message.emit("部署成功", success_msg, False)
            self.refresh()
            self._cleanup(worker)

        def on_err(msg: str):
            self._setBusy(False)
            if "canceled" not in msg.lower() and "dismissed" not in msg.lower():
                self.message.emit("失败", f"部署失败:\n{msg}", True)
            self.refresh()
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
        worker.deleteLater()
