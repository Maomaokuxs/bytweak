"""桌面组件纯逻辑层：通知/顶栏探测切换 + niri 自启同步，无 Qt Widgets 依赖。"""
import os
import re
import subprocess

HOME = os.path.expanduser("~")
NIRI_CONFIG = os.path.join(HOME, ".config/niri/config.kdl")
QUICKSHELL_DIR = os.path.join(HOME, "Documents/quickshell")

NOTIF_OPTIONS = [
    ("mako", "mako", "经典弹窗，轻量稳定"),
    ("dunst", "dunst", "历史记录 / 未读计数"),
    ("quickshell", "quickshell 中心", "顶栏铃铛 + 历史浮窗，需顶栏在跑"),
]
BAR_OPTIONS = [
    ("quickshell", "quickshell", "自研栏 + 悬浮坞 + 全套浮窗"),
    ("waybar", "waybar", "经典栏，配置即生效"),
]


def _run(cmd, timeout=10):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None


def _pgrep(name):
    r = _run(["pgrep", "-x", name])
    return bool(r and r.returncode == 0)


def detect_notif_manager() -> str:
    """mako | dunst | quickshell | none（看谁持有通知总线）"""
    r = _run(["busctl", "--user", "status", "org.freedesktop.Notifications"])
    if r and r.returncode == 0:
        for line in (r.stdout or "").splitlines():
            if line.startswith("CommandLine="):
                cmd = line.split("=", 1)[1]
                if "mako" in cmd:
                    return "mako"
                if "dunst" in cmd:
                    return "dunst"
                if "quickshell" in cmd:
                    return "quickshell"
    if _pgrep("mako"):
        return "mako"
    if _pgrep("dunst"):
        return "dunst"
    return "none"


def detect_bar() -> str:
    """quickshell | waybar | none"""
    r = _run(["pgrep", "-f", "quickshell.*Documents/quickshell"])
    if r and r.returncode == 0:
        return "quickshell"
    if _pgrep("quickshell"):
        return "quickshell"
    if _pgrep("waybar"):
        return "waybar"
    return "none"


def switch_notif(target: str) -> str:
    """切换通知管理器，返回状态文案；失败情况直接返回说明。"""
    current = detect_notif_manager()
    if target == current:
        return f"已经是 {target}，无需切换"
    if target == "mako":
        _run(["pkill", "-x", "dunst"])
        _run(["bash", "-c", "mako >/dev/null 2>&1 &"])
        return "已切到 mako（quickshell 中心自动退让）"
    if target == "dunst":
        _run(["pkill", "-x", "mako"])
        cfg = os.path.join(HOME, ".config/dunst/dunstrc")
        if not os.path.exists(cfg):
            return "没有 ~/.config/dunst/dunstrc，先装 dunst 配置"
        _run(["bash", "-c", f"dunst -config {cfg} >/dev/null 2>&1 &"])
        return "已切到 dunst（历史：dunstctl history）"
    if target == "quickshell":
        _run(["pkill", "-x", "mako"])
        _run(["pkill", "-x", "dunst"])
        return "已清场，quickshell 中心接管（需顶栏在跑；不在跑先去顶栏组启动）"
    return f"未知目标：{target}"


def switch_bar(target: str) -> str:
    current = detect_bar()
    if target == current:
        return f"已经是 {target}，无需切换"
    if target == "waybar":
        _run(["pkill", "-x", "quickshell"])
        _run(["bash", "-c", "waybar >/dev/null 2>&1 &"])
        return "已切到 waybar"
    if target == "quickshell":
        _run(["pkill", "-x", "waybar"])
        _run(["pkill", "-f", "[w]aybar/scripts/cava.sh"])
        _run(["pkill", "-x", "cava"])
        if not os.path.isdir(QUICKSHELL_DIR):
            return f"找不到 {QUICKSHELL_DIR}"
        _run(["bash", "-c", f"quickshell -p {QUICKSHELL_DIR} -d -n >/dev/null 2>&1 &"])
        return "已切到 quickshell"
    return f"未知目标：{target}"


def sync_niri_autostart(bar: str, config_path: str = NIRI_CONFIG,
                        quickshell_dir: str = QUICKSHELL_DIR) -> str:
    cfg = os.path.realpath(config_path)
    if not os.path.exists(cfg):
        return f"找不到 niri 配置 {cfg}，跳过自启同步"
    try:
        with open(cfg, encoding="utf-8") as f:
            text = f.read()
        qs_line = f'spawn-at-startup "quickshell" "-p" "{quickshell_dir}" "-d" "-n"'
        wb_line = 'spawn-at-startup "waybar"'
        lines = text.splitlines(keepends=True)
        out, has_qs, has_wb = [], False, False
        for line in lines:
            s = line.strip()
            if "quickshell" in s and "spawn-at-startup" in s:
                has_qs = True
                out.append((qs_line if bar == "quickshell" else "// " + qs_line) + "\n")
            elif s == wb_line or s == "// " + wb_line:
                has_wb = True
                out.append((wb_line if bar == "waybar" else "// " + wb_line) + "\n")
            else:
                out.append(line)
        if not has_qs:
            out.append((qs_line if bar == "quickshell" else "// " + qs_line) + "\n")
        if not has_wb:
            out.append((wb_line if bar == "waybar" else "// " + wb_line) + "\n")
        with open(cfg, "w", encoding="utf-8") as f:
            f.writelines(out)
        return f"niri 自启已同步[{bar}]（niri 会自动热重载）"
    except Exception as e:
        return f"自启同步失败：{e}"


def state_text() -> str:
    return f"当前：通知[{detect_notif_manager()}] 顶栏[{detect_bar()}]"


def read_hellwal_palette():
    """读中央调色板（仅 Widgets 版跟随壁纸用），失败回落默认浅色。"""
    pal = {"BG": "#f9f3f1", "FG": "#6a442f", "ACCENT": "#998c8c", "MUTED": "#b4aaa8"}
    env_path = os.path.join(HOME, ".cache/by-mgr/hellwal/global-palette.env")
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k in pal and re.match(r"^#[0-9a-fA-F]{6}$", v):
                        pal[k] = v
    except Exception:
        pass
    return pal
