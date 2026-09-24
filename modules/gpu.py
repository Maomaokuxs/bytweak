from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt

from . import gpu_core
from .utils import logger, run_pkexec_shell
from .workers import Worker

VENDOR_ICON = {
    "NVIDIA": "󰢮",
    "AMD": "󰍛",
    "Intel": "",
    "Unknown": "󰍹",
}
VENDOR_COLOR = {
    "NVIDIA": "#76b900",
    "AMD": "#ed1c24",
    "Intel": "#0071c5",
    "Unknown": "#6b7280",
}
ICON_FONT = "'JetBrainsMono Nerd Font','JetBrainsMono NF','Symbols Nerd Font'"


def _set_codec(lbl, ok: bool, name: str):
    if not lbl:
        return
    mark = "✓" if ok else "✗"
    color = "#1a7f37" if ok else "#cf222e"
    lbl.setText(f'<span style="color:{color}; font-weight:700;">{mark}</span> {name}')
    lbl.setToolTip(f"{name}: {'已支持' if ok else '未支持'}")


class GpuManager:
    """Widgets 薄层：标签/按钮渲染 + 一键修复，探测逻辑全部走 gpu_core。"""

    def __init__(self, app_ctx):
        self.ctx = app_ctx
        self.detected_vendor = "Unknown"
        self.nvidia_driver_installed = False
        self.vaapi_perfect = False
        self._workers: list[Worker] = []
        self._gpus: list[dict] = []

    def detect_gpu_and_drivers(self):
        logger.debug("detect GPU/VAAPI")
        if getattr(self.ctx, "gpu_refresh_btn", None):
            self.ctx.gpu_refresh_btn.setEnabled(False)
            self.ctx.gpu_refresh_btn.setText("检测中...")
        try:
            self._gpus = gpu_core.detect_gpus()
            self.detected_vendor = gpu_core.primary_vendor(self._gpus)
            assessed = gpu_core.assess(self.detected_vendor)
        except Exception as e:
            logger.warning(f"detect_gpu failed: {e}")
            self._gpus = []
            self.detected_vendor = "Unknown"
            assessed = {"nvidia_installed": False, "perfect": False,
                        "status": f"检测失败: {e}", "version": "",
                        "codec": {k: False for k in ("h264", "h265", "av1", "vp9", "nvenc", "vaapi")}}

        self.nvidia_driver_installed = assessed["nvidia_installed"]
        self.vaapi_perfect = assessed["perfect"]
        codec = assessed["codec"]

        if self.ctx.gpu_action_btn:
            if self.vaapi_perfect:
                self.ctx.gpu_action_btn.setText("硬解状态完美，无需操作")
                self.ctx.gpu_action_btn.setEnabled(False)
                self.ctx.gpu_action_btn.setToolTip("所有硬解已打通，无需操作")
            else:
                self.ctx.gpu_action_btn.setEnabled(True)
                if self.detected_vendor == "NVIDIA":
                    if not self.nvidia_driver_installed:
                        self.ctx.gpu_action_btn.setText("一键安装闭源驱动 + 硬解")
                    else:
                        self.ctx.gpu_action_btn.setText("一键打通 VA-API / NVENC")
                elif self.detected_vendor in ["AMD", "Intel"]:
                    self.ctx.gpu_action_btn.setText(f"一键激活 {self.detected_vendor} 全格式硬解")
                else:
                    self.ctx.gpu_action_btn.setText("一键检测")
                    self.ctx.gpu_action_btn.setEnabled(False)

        self._render_device_list()
        if self.ctx.driver_status_lbl:
            self.ctx.driver_status_lbl.setText(assessed["status"])
        if getattr(self.ctx, "gpu_driver_version_lbl", None):
            self.ctx.gpu_driver_version_lbl.setText(assessed["version"])
        _set_codec(getattr(self.ctx, "codec_h264_lbl", None), codec["h264"], "H.264")
        _set_codec(getattr(self.ctx, "codec_h265_lbl", None), codec["h265"], "H.265")
        _set_codec(getattr(self.ctx, "codec_av1_lbl", None), codec["av1"], "AV1")
        _set_codec(getattr(self.ctx, "codec_vp9_lbl", None), codec["vp9"], "VP9")
        nvenc_name = "NVENC" if self.detected_vendor == "NVIDIA" else "NVENC（仅 NVIDIA）"
        _set_codec(getattr(self.ctx, "codec_nvenc_lbl", None), codec["nvenc"], nvenc_name)
        _set_codec(getattr(self.ctx, "codec_vaapi_lbl", None), codec["vaapi"], "VA-API")

        if getattr(self.ctx, "gpu_refresh_btn", None):
            self.ctx.gpu_refresh_btn.setEnabled(True)
            self.ctx.gpu_refresh_btn.setText("刷新检测")

    def _render_device_list(self):
        if not self.ctx.gpu_info_lbl:
            return
        if not self._gpus:
            self.ctx.gpu_info_lbl.setTextFormat(Qt.PlainText)
            self.ctx.gpu_info_lbl.setText("未侦测到主流显卡")
            self.ctx.gpu_info_lbl.setToolTip("")
            return
        self.ctx.gpu_info_lbl.setTextFormat(Qt.RichText)
        html_lines = []
        for g in self._gpus:
            icon = VENDOR_ICON.get(g["vendor"], VENDOR_ICON["Unknown"])
            color = VENDOR_COLOR.get(g["vendor"], "#6b7280")
            pci = f" <span style='font-size:12px;'>[{g['pci']}]</span>" if g["pci"] else ""
            html_lines.append(
                f"<span style=\"font-family:{ICON_FONT}; color:{color}; font-size:16px;\">{icon}</span>"
                f" <b style='font-size:15px;'>{g['vendor']}</b>"
                f" <span style='font-size:14px;'>· {g['name']}</span>{pci}"
            )
        self.ctx.gpu_info_lbl.setText("<br/>".join(html_lines))
        self.ctx.gpu_info_lbl.setToolTip("\n".join(g["raw"] for g in self._gpus))

    def apply_gpu_codec_fix(self):
        if self.vaapi_perfect or self.detected_vendor == "Unknown":
            return
        try:
            shell_script, success_msg = gpu_core.build_fix_script(
                self.detected_vendor, self.nvidia_driver_installed)
        except RuntimeError:
            return
        QMessageBox.information(self.ctx.window, "准备整备环境", "工具即将拉起 Polkit 授权，请留意系统授权弹窗。授权后将在后台执行，界面不会卡死。")
        if self.ctx.gpu_action_btn:
            self.ctx.gpu_action_btn.setEnabled(False)
            self.ctx.gpu_action_btn.setText("正在后台执行，请稍候...")
        def _task():
            result = run_pkexec_shell(shell_script, timeout=1800)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "执行失败")
            return result
        worker = Worker(_task)
        self._workers.append(worker)
        def on_ok(_):
            QMessageBox.information(self.ctx.window, "部署成功", success_msg)
            self.detect_gpu_and_drivers()
            self._cleanup(worker)
        def on_err(msg: str):
            if "canceled" in msg.lower() or "dismissed" in msg.lower():
                logger.debug("gpu pkexec canceled")
            else:
                QMessageBox.critical(self.ctx.window, "失败", f"部署失败:\n{msg}")
            self.detect_gpu_and_drivers()
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
