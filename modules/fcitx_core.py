"""Fcitx5 主题纯逻辑层：配置读写 + 主题扫描 + 压缩包导入，无 Qt Widgets 依赖。"""
import os
import re
import shutil
import subprocess
import tarfile
import zipfile

CONFIG_PATH = os.path.expanduser("~/.config/fcitx5/conf/classicui.conf")
USER_THEMES = os.path.expanduser("~/.local/share/fcitx5/themes")
SYS_THEMES = "/usr/share/fcitx5/themes"
SANDBOX_DIR = "/tmp/fcitx_theme_sandbox"

THEME_KEYS = ("Theme", "DarkTheme", "UseDarkTheme")


def read_config(config_path: str = CONFIG_PATH) -> dict:
    cfg: dict = {}
    if not os.path.exists(config_path):
        return cfg
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^\s*(Theme|DarkTheme|UseDarkTheme)\s*=\s*(.+)\s*$', line)
                if m:
                    cfg[m.group(1)] = m.group(2).strip()
    except Exception:
        pass
    return cfg


def theme_status_text(cfg: dict | None = None) -> str:
    cfg = cfg if cfg is not None else read_config()
    light = cfg.get("Theme", "默认")
    dark = cfg.get("DarkTheme", "默认")
    status = f"浅色主题：【{light}】  深色主题：【{dark}】"
    if cfg.get("UseDarkTheme", "False") == "True":
        status += "  (自动切换已开启)"
    return status


def write_config(light_theme: str, dark_theme: str, auto_switch: bool,
                 config_path: str = CONFIG_PATH):
    """合并写入三键，保留文件其余内容；成功后通知 fcitx5 重载。"""
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    lines: list[str] = []
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    new_lines: list[str] = []
    keys_written: set[str] = set()
    for line in lines:
        m = re.match(r'^\s*(Theme|DarkTheme|UseDarkTheme)\s*=', line.strip())
        if m:
            key = m.group(1)
            if key not in keys_written:
                if key == "Theme" and light_theme:
                    new_lines.append(f"Theme={light_theme}\n")
                elif key == "DarkTheme" and dark_theme:
                    new_lines.append(f"DarkTheme={dark_theme}\n")
                elif key == "UseDarkTheme":
                    new_lines.append(f"UseDarkTheme={'True' if auto_switch else 'False'}\n")
                else:
                    new_lines.append(line)
                keys_written.add(key)
            continue
        new_lines.append(line)
    if "Theme" not in keys_written and light_theme:
        new_lines.append(f"Theme={light_theme}\n")
    if "DarkTheme" not in keys_written and dark_theme:
        new_lines.append(f"DarkTheme={dark_theme}\n")
    if "UseDarkTheme" not in keys_written:
        new_lines.append(f"UseDarkTheme={'True' if auto_switch else 'False'}\n")
    with open(config_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    subprocess.run(["fcitx5-remote", "-r"], capture_output=True)


def scan_themes(user_themes: str = USER_THEMES, sys_themes: str = SYS_THEMES) -> list[str]:
    themes: list[str] = []
    for root in [user_themes, sys_themes]:
        if not os.path.exists(root):
            continue
        try:
            for name in os.listdir(root):
                theme_dir = os.path.join(root, name)
                if os.path.isdir(theme_dir) and os.path.exists(os.path.join(theme_dir, "theme.conf")):
                    if name not in themes:
                        themes.append(name)
        except Exception:
            pass
    themes.sort(key=str.lower)
    return themes


def import_archive(archive_path: str, user_themes: str = USER_THEMES,
                   sandbox: str = SANDBOX_DIR) -> str:
    """解包导入主题，返回主题名；失败抛异常。"""
    if not os.path.exists(archive_path):
        raise FileNotFoundError("指定的压缩包路径不存在！")
    if os.path.exists(sandbox):
        shutil.rmtree(sandbox)
    os.makedirs(sandbox, exist_ok=True)
    try:
        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as z:
                z.extractall(sandbox)
        elif archive_path.endswith((".tar.xz", ".xz")):
            with tarfile.open(archive_path, "r:xz") as t:
                t.extractall(sandbox)
        else:
            with tarfile.open(archive_path, "r:gz") as t:
                t.extractall(sandbox)
        theme_dir = None
        for root, _dirs, files in os.walk(sandbox):
            if "theme.conf" in files:
                theme_dir = root
                break
        if not theme_dir:
            raise ValueError("压缩包内未找到包含 theme.conf 的有效 Fcitx5 主题！")
        theme_name = os.path.basename(theme_dir)
        target = os.path.join(user_themes, theme_name)
        os.makedirs(user_themes, exist_ok=True)
        if os.path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(theme_dir, target)
        return theme_name
    finally:
        if os.path.exists(sandbox):
            shutil.rmtree(sandbox)
