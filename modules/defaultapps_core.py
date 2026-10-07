"""默认应用设置纯逻辑层：xdg-mime 查询/设置 + .desktop 候选扫描，无 Qt 依赖。"""
import re
import subprocess
from pathlib import Path

# (key, 显示名, mimetype)
TARGETS = [
    ("browser", "网页浏览器", "text/html"),
    ("filemanager", "文件管理器", "inode/directory"),
    ("image", "图片查看器", "image/png"),
    ("video", "视频播放器", "video/mp4"),
    ("text", "文本编辑器", "text/plain"),
    ("pdf", "PDF 阅读器", "application/pdf"),
]

DESKTOP_ID_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]*\.desktop$")
MIME_BY_KEY = {k: m for k, _, m in TARGETS}


def _desktop_dirs() -> list[Path]:
    dirs = []
    home = Path.home() / ".local" / "share" / "applications"
    if home.is_dir():
        dirs.append(home)
    sys_dir = Path("/usr/share/applications")
    if sys_dir.is_dir():
        dirs.append(sys_dir)
    return dirs


def _run_xdg(*args: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(["xdg-mime", *args], capture_output=True,
                           text=True, timeout=timeout)
    except FileNotFoundError:
        raise RuntimeError("未找到 xdg-mime，请先安装 xdg-utils")
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "xdg-mime 执行失败")
    return r.stdout.strip()


def _parse_desktop(path: Path) -> dict | None:
    """解析 .desktop，返回 {id, name, mimes}；NoDisplay 或无 Name 的跳过。"""
    name = ""
    mimes: set[str] = set()
    nodisplay = False
    in_entry = False
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if line == "[Desktop Entry]":
                    in_entry = True
                    continue
                if line.startswith("[") and line.endswith("]"):
                    in_entry = False
                    continue
                if not in_entry or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                if k == "Name" and not name:
                    name = v.strip()
                elif k == "MimeType":
                    mimes = {m.strip().rstrip(";") for m in v.split(";") if m.strip()}
                elif k == "NoDisplay" and v.strip().lower() == "true":
                    nodisplay = True
    except OSError:
        return None
    if nodisplay or not name:
        return None
    return {"id": path.name, "name": name, "mimes": mimes}


def scan_candidates(mime: str) -> list[dict]:
    """返回支持该 mimetype 的 [{id, name}]，按名称排序。须在后台线程调用。"""
    seen: dict[str, dict] = {}
    for d in _desktop_dirs():
        for path in sorted(d.glob("*.desktop")):
            info = _parse_desktop(path)
            if not info or info["id"] in seen:
                continue
            if mime in info["mimes"]:
                seen[info["id"]] = {"id": info["id"], "name": info["name"]}
    return sorted(seen.values(), key=lambda c: c["name"].lower())


def query_default(mime: str) -> str:
    """返回该 mimetype 的默认 .desktop id（无则返回空串）。"""
    try:
        return _run_xdg("query", "default", mime)
    except RuntimeError:
        return ""


def get_defaults() -> list[dict]:
    """返回 [{key, label, mime, current, current_name, candidates}]。"""
    out = []
    for key, label, mime in TARGETS:
        current = query_default(mime)
        candidates = scan_candidates(mime)
        names = {c["id"]: c["name"] for c in candidates}
        out.append({
            "key": key,
            "label": label,
            "mime": mime,
            "current": current,
            "current_name": names.get(current, current or "未设置"),
            "candidates": candidates,
        })
    return out


def build_set_default_cmd(desktop_id: str, key: str) -> list[str]:
    """构造 xdg-mime default 命令（用户级，无需提权）；非法输入抛 ValueError。"""
    desktop_id = (desktop_id or "").strip()
    if not DESKTOP_ID_PATTERN.match(desktop_id):
        raise ValueError(f"非法桌面文件 ID: {desktop_id}")
    mime = MIME_BY_KEY.get((key or "").strip())
    if not mime:
        raise ValueError(f"未知设置项: {key}")
    valid = {c["id"] for c in scan_candidates(mime)}
    if desktop_id not in valid:
        raise ValueError(f"{desktop_id} 不支持 {mime}")
    return ["xdg-mime", "default", desktop_id, mime]
