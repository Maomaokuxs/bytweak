import os
import shlex
import subprocess
import logging

logger = logging.getLogger("fedora-tweak-tool")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    # 默认简洁：启动/提权/警告/错误；FTT_DEBUG=1 打开全量调试
    logger.setLevel(logging.DEBUG if os.environ.get("FTT_DEBUG") == "1" else logging.INFO)


def get_releasever(fallback: str = "43") -> str:
    """动态获取 Fedora releasever，失败回退"""
    try:
        r = subprocess.run(["rpm", "-E", "%fedora"], capture_output=True, text=True, timeout=3)
        if r.returncode == 0 and r.stdout.strip().isdigit():
            return r.stdout.strip()
    except Exception as e:
        logger.warning(f"get_releasever failed: {e}")
    return fallback


def get_basearch(fallback: str = "x86_64") -> str:
    try:
        r = subprocess.run(["rpm", "-E", "%_arch"], capture_output=True, text=True, timeout=3)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception as e:
        logger.warning(f"get_basearch failed: {e}")
    return fallback


def run_pkexec(cmd: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
    """安全提权执行：列表形式，无 shell 注入"""
    full = ["pkexec"] + cmd
    logger.info(f"pkexec: {shlex.join(full)}")
    return subprocess.run(full, capture_output=True, text=True, timeout=timeout)


def run_pkexec_shell(script: str, timeout: int | None = None) -> subprocess.CompletedProcess:
    """多命令 shell 提权：script 由内部可信拼接，调用方需自行 shlex.quote 变量插值"""
    logger.info(f"pkexec sh -c: {script[:300]}")
    return subprocess.run(["pkexec", "sh", "-c", script], capture_output=True, text=True, timeout=timeout)


def rpmfusion_urls() -> tuple[str, str]:
    ver = get_releasever()
    free = f"https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-{ver}.noarch.rpm"
    nonfree = f"https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-{ver}.noarch.rpm"
    return free, nonfree
