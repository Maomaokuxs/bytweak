"""鼠标光标纯逻辑层：主题扫描/应用/导入 + Xcursor 预览渲染，无 Qt Widgets 依赖。"""
import os
import re
import shutil
import struct
import subprocess
import tarfile
import zipfile

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QPainter

SEARCH_PATHS = [
    os.path.expanduser("~/.icons"),
    os.path.expanduser("~/.local/share/icons"),
    "/usr/share/icons",
]
USER_ICONS_ROOT = os.path.expanduser("~/.local/share/icons")
SANDBOX_DIR = "/tmp/cursor_theme_sandbox"

# 预览槽位（优先级从高到低）
CURSOR_SLOTS = [
    ["left_ptr", "default", "arrow"],
    ["pointer", "pointing_hand", "hand2", "hand1"],
    ["xterm", "ibeam", "text"],
    ["wait", "watch", "progress", "half-busy"],
    ["crosshair", "cross"],
    ["fleur", "move", "size_all", "all-scroll"],
    ["hand1", "grab"],
    ["hand2", "grabbing"],
]

CELL = 64
ICON = 36


def list_themes(search_paths: list[str] | None = None) -> list[str]:
    paths = search_paths or SEARCH_PATHS
    valid: list[str] = []
    for path in paths:
        if not os.path.exists(path):
            continue
        try:
            for name in os.listdir(path):
                if name == "default":
                    continue
                full_path = os.path.join(path, name)
                if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "cursors")):
                    if name not in valid:
                        valid.append(name)
        except Exception:
            pass
    valid.sort()
    return valid


def read_current_theme() -> str:
    """读取当前光标主题：先 KDE（kreadconfig6），再 GNOME（gsettings）；都失败返回空串。"""
    try:
        r = subprocess.run(
            ["kreadconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme"],
            capture_output=True, text=True, check=True, timeout=3,
        )
        if r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "cursor-theme"],
            capture_output=True, text=True, check=True, timeout=3,
        )
        return r.stdout.strip().strip("'\"")
    except Exception:
        return ""


def resolve_theme_dir(theme_name: str, search_paths: list[str] | None = None) -> str | None:
    for root in search_paths or SEARCH_PATHS:
        test_path = os.path.join(root, theme_name)
        if os.path.exists(test_path):
            return test_path
    return None


def _load_xcur_pixmap(cursor_file: str) -> QPixmap | None:
    """解析 Xcursor 文件，取最大尺寸图像块转为 QPixmap；失败返回 None。"""
    try:
        real_path = os.path.realpath(cursor_file)
        if not os.path.exists(real_path) or os.path.isdir(real_path):
            return None
        with open(real_path, "rb") as f:
            data = f.read()
        if data[:4] != b"Xcur":
            return None
        ntoc = struct.unpack("<I", data[8:12])[0]
        img_offset = None
        pos = 16
        max_size_found = 0
        for _ in range(ntoc):
            if pos + 12 > len(data):
                break
            ctype, csub, cpos = struct.unpack("<III", data[pos:pos + 12])
            if ctype == 0xfffd0002 and 16 <= csub <= 128 and csub > max_size_found:
                max_size_found = csub
                img_offset = cpos
            pos += 12
        if not img_offset or img_offset + 36 > len(data):
            return None
        w, h = struct.unpack("<II", data[img_offset + 16:img_offset + 24])
        if not (16 <= w <= 128 and 16 <= h <= 128):
            return None
        pixel_start = img_offset + 36
        pixel_len = w * h * 4
        if pixel_start + pixel_len > len(data):
            return None
        qimg = QImage(data[pixel_start:pixel_start + pixel_len], w, h, QImage.Format_ARGB32)
        return QPixmap.fromImage(qimg)
    except Exception:
        return None


def render_preview(theme_name: str, cols: int = 8) -> tuple[QImage, int, int]:
    """渲染主题预览横条；返回 (QImage, 已绘制数, 计划数)。无素材返回空图与 0。"""
    slots = CURSOR_SLOTS[: max(1, cols)]
    theme_path = resolve_theme_dir(theme_name)
    pixmaps: list[QPixmap | None] = [None] * len(slots)
    if theme_path:
        cursors_dir = os.path.join(theme_path, "cursors")
        if os.path.isdir(cursors_dir):
            for i, fallbacks in enumerate(slots):
                for name in fallbacks:
                    b_path = os.path.join(cursors_dir, name)
                    if os.path.lexists(b_path):
                        pixmaps[i] = _load_xcur_pixmap(b_path)
                        break
    drawn = sum(1 for p in pixmaps if p is not None)
    canvas = QPixmap(cols * CELL, CELL)
    canvas.fill(Qt.transparent)
    if drawn:
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        for i, pix in enumerate(pixmaps):
            if pix is None:
                continue
            scaled = pix.scaled(ICON, ICON, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = i * CELL + (CELL - scaled.width()) // 2
            y = (CELL - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        painter.end()
    return canvas.toImage(), drawn, len(slots)


def apply_theme(theme_name: str):
    """三端写入：Xcursor 默认继承 + GTK3/4 + gsettings + KDE 热刷新。"""
    default_dir = os.path.join(USER_ICONS_ROOT, "default")
    os.makedirs(default_dir, exist_ok=True)
    with open(os.path.join(default_dir, "index.theme"), "w", encoding="utf-8") as f:
        f.write(f"[Icon Theme]\nName=Default\nComment=Default Cursor Theme\nInherits={theme_name}\n")
    for gtk_ver in ["gtk-3.0", "gtk-4.0"]:
        gtk_dir = os.path.expanduser(f"~/.config/{gtk_ver}")
        os.makedirs(gtk_dir, exist_ok=True)
        ini_path = os.path.join(gtk_dir, "settings.ini")
        content = ""
        if os.path.exists(ini_path):
            with open(ini_path, "r", encoding="utf-8") as f:
                content = f.read()
        if "gtk-cursor-theme-name=" in content:
            content = re.sub(r"gtk-cursor-theme-name=.*$", f"gtk-cursor-theme-name={theme_name}",
                             content, flags=re.MULTILINE)
        else:
            if "[Settings]" not in content:
                content = "[Settings]\n" + content
            content = content.replace("[Settings]\n", f"[Settings]\ngtk-cursor-theme-name={theme_name}\n")
        with open(ini_path, "w", encoding="utf-8") as f:
            f.write(content)
    subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", theme_name],
                   capture_output=True)
    if shutil.which("plasma-apply-cursortheme"):
        subprocess.run(["plasma-apply-cursortheme", theme_name], capture_output=True)


def import_archive(user_input_path: str, user_icons_root: str = USER_ICONS_ROOT,
                   sandbox_dir: str = SANDBOX_DIR) -> str:
    """解包导入外部主题，返回主题名；失败抛异常。"""
    if not os.path.exists(user_input_path):
        raise FileNotFoundError("指定的压缩包路径不存在！")
    if os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir)
    os.makedirs(sandbox_dir, exist_ok=True)
    try:
        if user_input_path.endswith('.zip'):
            with zipfile.ZipFile(user_input_path, 'r') as z:
                z.extractall(sandbox_dir)
        elif user_input_path.endswith(('.tar.xz', '.xz')):
            with tarfile.open(user_input_path, 'r:xz') as t:
                t.extractall(sandbox_dir)
        else:
            with tarfile.open(user_input_path, 'r:gz') as t:
                t.extractall(sandbox_dir)
        target_source_dir = None
        for root, dirs, _files in os.walk(sandbox_dir):
            if "cursors" in dirs:
                target_source_dir = root
                break
        if not target_source_dir:
            raise ValueError("未在包内找到包含 'cursors' 的合规鼠标主题文件夹！")
        theme_name = os.path.basename(target_source_dir)
        target_deploy_path = os.path.join(user_icons_root, theme_name)
        os.makedirs(user_icons_root, exist_ok=True)
        if os.path.exists(target_deploy_path):
            shutil.rmtree(target_deploy_path)
        shutil.copytree(target_source_dir, target_deploy_path)
        return theme_name
    finally:
        if os.path.exists(sandbox_dir):
            shutil.rmtree(sandbox_dir)
