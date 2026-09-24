"""显卡纯逻辑层：lspci 探测 + 驱动/硬解判定 + 修复脚本构造，无 Qt Widgets 依赖。"""
import os
import re
import shlex
import subprocess

from .utils import rpmfusion_urls


def _rpm_installed(pkg: str) -> bool:
    try:
        r = subprocess.run(["rpm", "-q", pkg], capture_output=True, text=True, timeout=3)
        return r.returncode == 0
    except Exception:
        return False


def detect_gpus(lspci_text: str | None = None) -> list[dict]:
    """返回 [{vendor, name, pci, raw}]；vendor ∈ NVIDIA/AMD/Intel/Unknown。"""
    if lspci_text is None:
        result = subprocess.run(["lspci", "-nn"], capture_output=True, text=True, check=True, timeout=5)
        lspci_text = result.stdout
    gpus: list[dict] = []
    for line in lspci_text.splitlines():
        if "VGA compatible" not in line and "3D controller" not in line and "Display controller" not in line:
            continue
        pci_match = re.search(r"\[([0-9a-fA-F]{4}:[0-9a-fA-F]{4})\]", line)
        pci_id = pci_match.group(1) if pci_match else ""
        name_match = re.search(r"\[([^\]]+)\]", line)
        name = name_match.group(1) if name_match else line.split(":", 2)[-1].strip()[:40]
        vendor = "Unknown"
        if "NVIDIA" in line:
            vendor = "NVIDIA"
        elif "Advanced Micro Devices" in line or "AMD" in line or "[1002:" in line:
            vendor = "AMD"
        elif "Intel" in line or "[8086:" in line:
            vendor = "Intel"
        gpus.append({"vendor": vendor, "name": name, "pci": pci_id, "raw": line})
    return gpus


def primary_vendor(gpus: list[dict]) -> str:
    vendors = [g["vendor"] for g in gpus]
    if "NVIDIA" in vendors:
        return "NVIDIA"
    if "AMD" in vendors:
        return "AMD"
    if "Intel" in vendors:
        return "Intel"
    return "Unknown"


def nvidia_driver_loaded() -> bool:
    return os.path.exists("/proc/driver/nvidia/version")


def nvidia_driver_version() -> str:
    try:
        with open("/proc/driver/nvidia/version", encoding="utf-8", errors="ignore") as f:
            return f.read().splitlines()[0][:80]
    except Exception:
        return "NVIDIA 驱动已加载"


def assess(vendor: str) -> dict:
    """返回 {nvidia_installed, perfect, status, version, codec{...}}。"""
    codec = {"h264": False, "h265": False, "av1": False, "vp9": False, "nvenc": False, "vaapi": False}
    if vendor == "NVIDIA":
        if nvidia_driver_loaded():
            # 注意：elFarto 项目在仓库中的包名就是 libva-nvidia-driver
            # （提供 /usr/lib64/dri/nvidia_drv_video.so），并无独立的
            # nvidia-vaapi-driver 包，切勿再引入该包名
            vaapi = _rpm_installed("libva-nvidia-driver")
            codec.update(vaapi=vaapi, nvenc=True, h264=vaapi, h265=vaapi, av1=vaapi, vp9=vaapi)
            if vaapi:
                return {"nvidia_installed": True, "perfect": True,
                        "status": "NVIDIA 闭源驱动已加载，全格式硬解就绪",
                        "version": nvidia_driver_version(), "codec": codec}
            return {"nvidia_installed": True, "perfect": False,
                    "status": "已加载闭源驱动，但缺少 libva-nvidia-driver，录屏与浏览器硬解受限",
                    "version": nvidia_driver_version(), "codec": codec}
        return {"nvidia_installed": False, "perfect": False,
                "status": "检测到 NVIDIA 显卡，当前为 Nouveau 开源驱动（性能与硬解受限）",
                "version": "Nouveau，建议安装 akmod-nvidia", "codec": codec}
    if vendor in ("AMD", "Intel"):
        freeworld = _rpm_installed("mesa-va-drivers-freeworld")
        codec.update(h264=freeworld, h265=freeworld, vp9=freeworld, av1=freeworld, vaapi=freeworld)
        version = "mesa-va-drivers-freeworld 已安装" if freeworld else "mesa-va-drivers-freeworld 未安装"
        if not _rpm_installed("gstreamer1-plugins-bad-freeworld"):
            version += "，gstreamer 插件缺失"
        if freeworld:
            return {"nvidia_installed": False, "perfect": True,
                    "status": f"{vendor} 原生驱动正常，专利编解码已激活",
                    "version": version, "codec": codec}
        return {"nvidia_installed": False, "perfect": False,
                "status": f"{vendor} 驱动正常，Fedora 默认屏蔽 H264/H265 专利硬解",
                "version": version, "codec": codec}
    return {"nvidia_installed": False, "perfect": False,
            "status": "未侦测到主流显卡，基础渲染", "version": "", "codec": codec}


def build_fix_script(vendor: str, nvidia_installed: bool) -> tuple[str, str]:
    """返回 (提权脚本, 成功文案)；无需操作时抛 RuntimeError。"""
    free_url, nonfree_url = rpmfusion_urls()
    if vendor == "NVIDIA":
        if not nvidia_installed:
            script = f"""
            dnf5 config-manager --set-enabled fedora-cisco-openh264 || true
            dnf5 install -y {shlex.quote(free_url)} || true
            dnf5 install -y {shlex.quote(nonfree_url)} || true
            dnf5 update -y --refresh
            dnf5 install -y akmod-nvidia xorg-x11-drv-nvidia-cuda libva-nvidia-driver gstreamer1-vaapi
            """
            return script, "NVIDIA 闭源驱动与全格式硬解部署成功，请务必重新启动电脑。"
        return ("dnf5 install -y libva-nvidia-driver gstreamer1-vaapi",
                "NVIDIA VA-API 高速硬解通道打通成功。")
    if vendor in ("AMD", "Intel"):
        script = f"""
        dnf5 install -y {shlex.quote(free_url)} || true
        dnf5 update -y --refresh
        dnf5 swap -y mesa-va-drivers mesa-va-drivers-freeworld
        dnf5 swap -y mesa-vdr-drivers mesa-vdr-drivers-freeworld 2>/dev/null || true
        dnf5 install -y gstreamer1-plugins-bad-freeworld gstreamer1-plugins-ugly-freeworld ffmpeg-free 2>/dev/null || dnf5 install -y gstreamer1-plugins-bad-freeworld gstreamer1-plugins-ugly-freeworld ffmpeg-free-devel
        """
        return script, f"{vendor} 开源全格式多媒体硬解加速已激活。"
    raise RuntimeError("当前无需修复")
