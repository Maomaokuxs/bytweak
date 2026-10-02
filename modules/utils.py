import os
import shlex
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger("fedora-tweak-tool")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    # 默认简洁：启动/提权/警告/错误；FTT_DEBUG=1 打开全量调试
    logger.setLevel(logging.DEBUG if os.environ.get("FTT_DEBUG") == "1" else logging.INFO)

# 操作日志：每次执行的功能留痕（by-mgr 命名空间，XDG 缓存目录）
APP_ID = "fedora-tweak-tool"
LOG_DIR = os.path.join(os.path.expanduser("~"), ".cache/by-mgr", APP_ID, "logs")
OPERATIONS_LOG = os.path.join(LOG_DIR, "operations.log")
LOG_ROTATE_SIZE = 512 * 1024


def operations_log_path() -> str:
    return OPERATIONS_LOG


def log_operation(action: str, ok: bool, seconds: float = 0.0, detail: str = ""):
    """追加一条操作记录：时间 | 结果 | 耗时 | 功能 | 详情（失败时为错误尾）。"""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        if os.path.exists(OPERATIONS_LOG) and os.path.getsize(OPERATIONS_LOG) > LOG_ROTATE_SIZE:
            try:
                os.replace(OPERATIONS_LOG, OPERATIONS_LOG + ".1")
            except Exception:
                pass
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "OK" if ok else "FAIL"
        line = f"{stamp} | {status} {seconds:.1f}s | {action}"
        if detail:
            line += f" | {detail[:300].replace(chr(10), ' ⏎ ')}"
        with open(OPERATIONS_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        logger.warning(f"write operations log failed: {e}")


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


def get_os_info(path: str = "/etc/os-release") -> dict:
    """解析 os-release，返回 {id, id_like, name, pretty, variant}；失败返回 {}。"""
    info: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                info[k.strip().lower()] = v.strip().strip('"').strip("'")
    except Exception as e:
        logger.warning(f"get_os_info failed: {e}")
        return {}
    return {"id": info.get("id", ""),
            "id_like": info.get("id_like", ""),
            "name": info.get("name", ""),
            "pretty": info.get("pretty_name", info.get("name", "")),
            "variant": info.get("variant", info.get("variant_id", ""))}


def is_fedora(os_info: dict | None = None) -> bool:
    """是否为 Fedora 系（ID=fedora 或 ID_LIKE 含 fedora）。"""
    info = os_info if os_info is not None else get_os_info()
    if (info.get("id") or "").lower() == "fedora":
        return True
    return "fedora" in (info.get("id_like") or "").lower().split()


def is_atomic(os_info: dict | None = None) -> bool:
    """是否为原子化系统（ostree/bootc 启动，或变体名为原子版本）。"""
    if os.path.exists("/run/ostree-booted"):
        return True
    info = os_info if os_info is not None else get_os_info()
    variant = f"{info.get('variant', '')}".lower()
    return any(k in variant for k in ("silverblue", "kinoite", "sericea", "onyx",
                                      "iot", "atomic", "bootc"))
