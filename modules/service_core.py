"""服务管理纯逻辑层：systemctl 查询 + 命令构造，无 Qt 依赖。"""
import re
import subprocess

UNIT_PATTERN = re.compile(r'^[A-Za-z0-9@_.-]+\.service$')
ACTIONS = ("start", "stop", "restart", "enable", "disable")


def _run(*args: str, timeout: int = 15) -> str:
    cmd = subprocess.run(["systemctl", *args], capture_output=True,
                         text=True, timeout=timeout)
    return cmd.stdout


def scan_services() -> list[dict]:
    """返回 [{id, desc, active, sub, enabled, enabledState}]（system 级服务全量）。
    enabledState 保留原始状态串（enabled/disabled/static/masked…）。
    任一查询失败抛异常，由调用方提示。须在后台线程调用。"""
    try:
        files_out = _run("list-unit-files", "--type=service", "--no-pager", "--no-legend")
    except Exception as e:
        raise RuntimeError(f"读取服务清单失败: {e}")
    try:
        units_out = _run("list-units", "--type=service", "--all", "--no-pager", "--no-legend")
    except Exception:
        units_out = ""
    file_state: dict[str, str] = {}
    for line in files_out.split("\n"):
        parts = line.split()
        if len(parts) >= 2 and parts[0].endswith(".service"):
            file_state[parts[0]] = parts[1]
    active_map: dict[str, dict] = {}
    for line in units_out.split("\n"):
        parts = line.split(None, 4)
        if len(parts) >= 4 and parts[0].endswith(".service"):
            active_map[parts[0]] = {"active": parts[2], "sub": parts[3],
                                    "desc": parts[4] if len(parts) > 4 else ""}
    out = []
    for unit in sorted(set(file_state) | set(active_map)):
        state = file_state.get(unit, "unknown")
        info = active_map.get(unit, {"active": "inactive", "sub": "dead", "desc": ""})
        out.append({"id": unit, "desc": info["desc"] or unit,
                    "active": info["active"] == "active", "sub": info["sub"],
                    "enabled": state.startswith("enabled"),
                    "enabledState": state})
    return out


def build_systemctl_cmd(action: str, unit: str) -> list[str]:
    """启停/自启命令（列表形式防注入）；非法输入抛 ValueError。"""
    if action not in ACTIONS:
        raise ValueError(f"未知操作: {action}")
    unit = (unit or "").strip()
    if not UNIT_PATTERN.match(unit):
        raise ValueError(f"非法服务名: {unit}")
    return ["systemctl", action, unit]
