"""niri 快捷键解析：读取 niri 配置的 binds{} 块，翻译成中文作用说明。
纯标准库实现（无 kdl 依赖），按 niri 配置的书写习惯做行级状态机解析。"""
import os
import re
import shlex

NIRI_CONFIG = os.path.expanduser("~/.config/niri/config.kdl")
NIRI_KEYBINDS = os.path.expanduser("~/.config/niri/keybinds.kdl")

# 动作名 -> 中文说明（方向类另按参数补全）
ACTION_DESC = {
    "show-hotkey-overlay": "显示快捷键帮助",
    "spawn": "启动程序",
    "spawn-sh": "运行命令",
    "focus-column-left": "聚焦左列",
    "focus-column-right": "聚焦右列",
    "focus-window-up": "聚焦上窗口",
    "focus-window-down": "聚焦下窗口",
    "focus-monitor-left": "聚焦左显示器",
    "focus-monitor-right": "聚焦右显示器",
    "focus-monitor-up": "聚焦上显示器",
    "focus-monitor-down": "聚焦下显示器",
    "focus-column-first": "聚焦最左列",
    "focus-column-last": "聚焦最右列",
    "focus-workspace": "切换工作区",
    "focus-workspace-down": "切换到下一个工作区",
    "focus-workspace-up": "切换到上一个工作区",
    "focus-workspace-previous": "切回上一个工作区",
    "move-column-left": "当前列左移",
    "move-column-right": "当前列右移",
    "move-window-up": "当前窗口上移",
    "move-window-down": "当前窗口下移",
    "move-column-to-monitor-left": "当前列移到左显示器",
    "move-column-to-monitor-right": "当前列移到右显示器",
    "move-column-to-monitor-up": "当前列移到上显示器",
    "move-column-to-monitor-down": "当前列移到下显示器",
    "move-column-to-workspace": "当前列移到工作区",
    "move-column-to-workspace-down": "当前列移到下一个工作区",
    "move-column-to-workspace-up": "当前列移到上一个工作区",
    "move-window-to-workspace": "当前窗口移到工作区",
    "move-column-to-first": "当前列移到最左",
    "move-column-to-last": "当前列移到最右",
    "move-workspace-down": "工作区下移",
    "move-workspace-up": "工作区上移",
    "close-window": "关闭窗口",
    "fullscreen-window": "窗口全屏",
    "maximize-column": "最大化当前列",
    "maximize-window-to-edges": "最大化到屏幕边缘",
    "expand-column-to-available-width": "扩展到可用宽度",
    "center-column": "当前列居中",
    "center-visible-columns": "可见列全部居中",
    "set-column-width": "调整列宽",
    "set-window-height": "调整窗口高度",
    "switch-preset-column-width": "切换列宽预设",
    "switch-preset-column-width-back": "反向切换列宽预设",
    "switch-preset-window-height": "切换窗口高度预设",
    "reset-window-height": "重置窗口高度",
    "toggle-window-floating": "切换浮动/平铺",
    "switch-focus-between-floating-and-tiling": "在浮动与平铺间切换焦点",
    "toggle-column-tabbed-display": "切换列标签页显示",
    "consume-or-expel-window-left": "并入/移出左侧列",
    "consume-or-expel-window-right": "并入/移出右侧列",
    "consume-window-into-column": "并入下方窗口到当前列",
    "expel-window-from-column": "移出当前列底部窗口",
    "toggle-overview": "打开/关闭概览",
    "toggle-keyboard-shortcuts-inhibit": "切换快捷键抑制",
    "screenshot": "区域截图",
    "screenshot-screen": "整屏截图",
    "screenshot-window": "当前窗口截图",
    "power-off-monitors": "关闭显示器",
    "quit": "退出 niri",
    "switch-layout": "切换键盘布局",
}

_WORKSPACE_ACTIONS = {"focus-workspace", "move-column-to-workspace", "move-window-to-workspace"}
_SIZE_ACTIONS = {"set-column-width", "set-window-height"}

# 分类展示顺序与归属
CATEGORY_ORDER = ["窗口操作", "窗口与列移动", "工作区", "布局与尺寸",
                  "程序与脚本", "媒体与硬件", "系统与视图"]
_CAT_FOCUS = {
    "focus-column-left", "focus-column-right", "focus-window-up", "focus-window-down",
    "focus-monitor-left", "focus-monitor-right", "focus-monitor-up", "focus-monitor-down",
    "focus-column-first", "focus-column-last", "close-window",
}
_CAT_MOVE = {
    "move-column-left", "move-column-right", "move-window-up", "move-window-down",
    "move-column-to-monitor-left", "move-column-to-monitor-right",
    "move-column-to-monitor-up", "move-column-to-monitor-down",
    "move-column-to-first", "move-column-to-last",
    "consume-or-expel-window-left", "consume-or-expel-window-right",
    "consume-window-into-column", "expel-window-from-column",
}
_CAT_WORKSPACE = {
    "focus-workspace", "focus-workspace-down", "focus-workspace-up", "focus-workspace-previous",
    "move-column-to-workspace", "move-column-to-workspace-down", "move-column-to-workspace-up",
    "move-window-to-workspace", "move-workspace-down", "move-workspace-up",
}
_CAT_LAYOUT = {
    "maximize-column", "maximize-window-to-edges", "fullscreen-window",
    "center-column", "center-visible-columns",
    "set-column-width", "set-window-height",
    "switch-preset-column-width", "switch-preset-column-width-back",
    "switch-preset-window-height", "reset-window-height",
    "expand-column-to-available-width",
    "toggle-window-floating", "switch-focus-between-floating-and-tiling",
    "toggle-column-tabbed-display",
}
_CAT_SYSTEM = {
    "toggle-overview", "toggle-keyboard-shortcuts-inhibit",
    "screenshot", "screenshot-screen", "screenshot-window",
    "power-off-monitors", "quit", "show-hotkey-overlay", "switch-layout",
}


def categorize(keys: str, action: str) -> str:
    """把一条绑定归入中文分类。"""
    tokens = action.strip().split(None, 1)
    name = tokens[0].rstrip(";") if tokens else ""
    if keys.startswith("XF86"):
        return "媒体与硬件"
    if name in ("spawn", "spawn-sh"):
        return "程序与脚本"
    if name in _CAT_FOCUS:
        return "窗口操作"
    if name in _CAT_MOVE:
        return "窗口与列移动"
    if name in _CAT_WORKSPACE:
        return "工作区"
    if name in _CAT_LAYOUT:
        return "布局与尺寸"
    if name in _CAT_SYSTEM:
        return "系统与视图"
    return "其他"


def _unquote(s: str) -> str:
    s = s.strip().rstrip(";").strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


def _describe(action: str) -> str:
    """把一条 niri 动作翻译成中文说明。"""
    action = action.strip().rstrip(";").strip()
    if not action:
        return ""
    parts = action.split(None, 1)
    name = parts[0]
    arg = parts[1].strip() if len(parts) > 1 else ""
    base = ACTION_DESC.get(name)
    if name in ("spawn", "spawn-sh"):
        try:
            cmd = " ".join(shlex.split(arg))
        except ValueError:
            cmd = _unquote(arg)
        for prefix in ("sh -c ", "bash -c "):
            if cmd.startswith(prefix):
                cmd = cmd[len(prefix):].strip().strip('"')
        return f"{base}：{cmd[:80]}"
    if name in _WORKSPACE_ACTIONS:
        return f"{base} {_unquote(arg)}" if arg else base
    if name in _SIZE_ACTIONS:
        return f"{base} {_unquote(arg)}" if arg else base
    if base:
        return f"{base} {arg}".rstrip() if arg else base
    return f"{name} {arg}".rstrip()


def _parse_binds_block(text: str) -> list[list[str]]:
    """取出 binds{} 内每个绑定节点的原始行列表。"""
    match = re.search(r'(?m)^\s*binds\s*\{', text)
    if not match:
        return []
    depth = 1
    block_lines: list[str] = []
    for line in text[match.end():].splitlines():
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            head = line.split("}", 1)[0]
            if head.strip():
                block_lines.append(head)
            break
        block_lines.append(line)

    nodes: list[list[str]] = []
    cur: list[str] = []
    ndepth = 0
    for line in block_lines:
        if not cur:
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            cur = [line]
            ndepth = line.count("{") - line.count("}")
            if ndepth <= 0:
                nodes.append(cur)
                cur = []
            continue
        cur.append(line)
        ndepth += line.count("{") - line.count("}")
        if ndepth <= 0:
            nodes.append(cur)
            cur = []
    if cur:
        nodes.append(cur)
    return nodes


def _parse_node(lines: list[str]) -> dict | None:
    text = "\n".join(lines).strip()
    if not text or text.startswith("//"):
        return None
    disabled = False
    if text.lstrip().startswith("/-"):
        disabled = True
        text = text.lstrip()[2:].lstrip()
    header = text.split("{", 1)[0].strip()
    if not header:
        return None
    keys = header.split()[0]
    title_match = re.search(r'hotkey-overlay-title="([^"]*)"', header)
    title = title_match.group(1) if title_match else ""
    body = text.split("{", 1)[1] if "{" in text else ""
    body = body.rsplit("}", 1)[0].strip()
    return {"keys": keys, "title": title, "action": body,
            "desc": _describe(body), "disabled": disabled,
            "category": categorize(keys, body)}


def load_keybinds(path: str = "") -> list[dict]:
    """读取 niri 配置的快捷键清单（含被注释禁用的，标记 disabled）。
    按配置文件出现顺序返回 [{keys, title, desc, disabled}]。"""
    paths = [path] if path else [NIRI_CONFIG, NIRI_KEYBINDS]
    out: list[dict] = []
    seen: set[str] = set()
    for p in paths:
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue
        for node_lines in _parse_binds_block(content):
            item = _parse_node(node_lines)
            if not item or item["keys"] in seen:
                continue
            seen.add(item["keys"])
            out.append(item)
    return out


# 符号键：显示用符号，写回仍用 XKB 名（+ 号键不映射，避免 Super++ 歧义）
KEY_SYMBOLS = {
    "Minus": "-", "Equal": "=", "BracketLeft": "[", "BracketRight": "]",
    "Backslash": "\\", "Comma": ",", "Period": ".", "Slash": "/",
    "Semicolon": ";", "Apostrophe": "'", "Grave": "`",
    "Left": "←", "Right": "→", "Up": "↑", "Down": "↓",
}
SYMBOL_TO_KEY = {v: k for k, v in KEY_SYMBOLS.items()}
KEY_CHOICES = (
    [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    + [str(d) for d in range(10)]
    + ["Left", "Right", "Up", "Down", "Home", "End", "Page_Up", "Page_Down",
       "Tab", "Space", "Return", "Escape", "BackSpace", "Delete", "Insert",
       "Minus", "Equal", "BracketLeft", "BracketRight", "Comma", "Period",
       "Slash", "Backslash", "Semicolon", "Apostrophe", "Grave",
       "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
       "Print", "XF86AudioMute", "XF86AudioPlay"]
)


def key_label(name: str) -> str:
    """键名 -> 展示符号（无映射则原样）。"""
    return KEY_SYMBOLS.get(name, name)


def key_choices() -> list[dict]:
    """编辑器下拉选项：[{label: 符号/名, value: XKB 名}]。"""
    return [{"label": key_label(k), "value": k} for k in KEY_CHOICES]


def format_keys(keys: str) -> str:
    """展示用：Mod 显示为 Super，符号键显示为符号本身。"""
    if not keys:
        return keys
    out = []
    for p in keys.split("+"):
        q = "Super" if p == "Mod" else p
        out.append(key_label(q))
    return "+".join(out)


# ---------- 修改绑定（写回配置）----------

KEY_COMBO_RE = re.compile(r'^[A-Za-z0-9_+]+$')
MODIFIERS = ("Super", "Ctrl", "Alt", "Shift")


def validate_combo(combo: str) -> str:
    combo = (combo or "").strip()
    if not combo or not KEY_COMBO_RE.match(combo):
        raise ValueError(f"非法按键组合：{combo}")
    if combo[0] == "+" or combo[-1] == "+" or "++" in combo:
        raise ValueError(f"非法按键组合：{combo}")
    return combo


def split_combo(combo: str) -> dict:
    """把组合键拆成 {mods:[...], key:'...'} 供编辑框回填。Mod 视为 Super。"""
    parts = [p for p in (combo or "").split("+") if p]
    mods, rest = [], []
    for p in parts:
        q = "Super" if p == "Mod" else p
        if q in MODIFIERS:
            mods.append(q)
        else:
            rest.append(q)
    return {"mods": mods, "key": "+".join(rest)}


def _iter_binds_block(lines: list[str]):
    """在行数组中定位 binds{} 块，产出 (行号, 缩进, 内容) 供改写。"""
    depth = 0
    inside = False
    for idx, line in enumerate(lines):
        if not inside:
            if re.match(r'^\s*binds\s*\{', line):
                inside = True
                depth = line.count("{") - line.count("}")
            continue
        yield idx, line
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            return


def _locate_bind(lines: list[str], raw_keys: str):
    """返回匹配 raw_keys 的绑定节点行区间 (start, end)，找不到返回 None。"""
    depth = 0
    inside = False
    for idx, line in enumerate(lines):
        if not inside:
            if re.match(r'^\s*binds\s*\{', line):
                inside = True
                depth = line.count("{") - line.count("}")
            continue
        if depth == 1:
            stripped = line.strip()
            if stripped and not stripped.startswith("//"):
                core = stripped[2:].lstrip() if stripped.startswith("/-") else stripped
                head = core.split("{", 1)[0].split()
                if head and head[0].split("{")[0] == raw_keys:
                    d = 0
                    j = idx
                    while j < len(lines):
                        d += lines[j].count("{") - lines[j].count("}")
                        if d == 0:
                            break
                        j += 1
                    return idx, j
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            return None
    return None


def _enabled_keys(lines: list[str]) -> set[str]:
    """当前处于启用状态的键位集合（Mod 归一为 Super，用于冲突检测）。"""
    out: set[str] = set()
    depth = 0
    inside = False
    for line in lines:
        if not inside:
            if re.match(r'^\s*binds\s*\{', line):
                inside = True
                depth = line.count("{") - line.count("}")
            continue
        if depth == 1:
            stripped = line.strip()
            if stripped and not stripped.startswith("//") and not stripped.startswith("/-"):
                head = stripped.split("{", 1)[0].split()
                if head:
                    out.add(_norm_combo(head[0]))
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            break
    return out


def _backup(path: str) -> str:
    import time as _t
    stamp = _t.strftime("%Y%m%d_%H%M%S")
    dst = f"{path}.bak.{stamp}"
    try:
        with open(path, encoding="utf-8") as f:
            data = f.read()
        with open(dst, "w", encoding="utf-8") as f:
            f.write(data)
    except Exception:
        return ""
    return dst


def _norm_combo(combo: str) -> str:
    return "+".join("Super" if p == "Mod" else p for p in (combo or "").split("+"))


def update_binding(raw_keys: str, new_combo: str, path: str = "") -> str:
    """把 raw_keys 对应的绑定注释停用，再紧跟写入使用 new_combo 的同功能绑定。
    返回备份文件路径（失败抛 ValueError/RuntimeError）。"""
    path = path or NIRI_CONFIG
    new_combo = validate_combo(new_combo)
    if _norm_combo(new_combo) == _norm_combo(raw_keys):
        raise ValueError("按键组合未发生变化")
    if not path or not os.path.exists(path):
        raise ValueError("未找到 niri 配置文件")
    with open(path, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    lines = text.split("\n")
    span = _locate_bind(lines, raw_keys)
    if not span:
        raise ValueError(f"未找到快捷键：{format_keys(raw_keys)}")
    start, end = span
    first = lines[start]
    if first.lstrip().startswith("/-"):
        raise ValueError("该快捷键已处于停用状态")
    if _norm_combo(new_combo) in _enabled_keys(lines) and _norm_combo(new_combo) != _norm_combo(raw_keys):
        raise ValueError(f"按键组合 {new_combo} 已被其它功能占用")

    indent = first[:len(first) - len(first.lstrip())]
    stripped = first.lstrip()
    # 原行注释保留（niri 用 /- 停用节点）
    lines[start] = f"{indent}/- {stripped}"
    # 保留原节点除键位外的头部（hotkey-overlay-title 等）
    rest = stripped.split(None, 1)[1] if len(stripped.split(None, 1)) > 1 else ""
    new_first = indent + new_combo + ((" " + rest) if rest else "")
    lines[end + 1:end + 1] = [new_first]

    backup = _backup(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return backup

