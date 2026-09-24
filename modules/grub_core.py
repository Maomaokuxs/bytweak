"""GRUB 纯逻辑层：无任何 Qt Widgets 依赖，可被 Widgets 版与 QML 版共用。"""
import os
import re
import shlex
import shutil
import tarfile
import zipfile

SYSTEM_THEMES_ROOT = "/usr/share/grub/themes"
GRUB_DEFAULTS = "/etc/default/grub"
SANDBOX_DIR = "/tmp/grub_theme_sandbox"

VALID_NAME = re.compile(r'^[A-Za-z0-9._-]+$')


def get_current_theme() -> tuple[str | None, str]:
    """返回 (主题名或 None, 状态文案)。"""
    if not os.path.exists(GRUB_DEFAULTS):
        return None, "未找到 /etc/default/grub"
    with open(GRUB_DEFAULTS, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'^\s*GRUB_THEME=["\' ]?([^"\'\n]+)["\' ]?', content, re.MULTILINE)
    if match:
        raw_path = match.group(1).strip()
        theme_name = os.path.basename(os.path.dirname(raw_path))
        return theme_name, f"当前正在使用的主题：【 {theme_name} 】"
    return None, "当前正在使用的主题：系统默认文字菜单 (未启用主题)"


def list_local_themes(root: str = SYSTEM_THEMES_ROOT) -> list[str]:
    """列出已安装且含 theme.txt 的主题名（排序后）。"""
    if not os.path.exists(root):
        return []
    valid = []
    for name in os.listdir(root):
        full_path = os.path.join(root, name)
        if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "theme.txt")):
            valid.append(name)
    valid.sort()
    return valid


def build_switch_script(selected_name: str, root: str = SYSTEM_THEMES_ROOT) -> str:
    """本地主题一键切换脚本；主题名非法时抛 ValueError。"""
    if not VALID_NAME.match(selected_name or ""):
        raise ValueError(f"非法主题名: {selected_name}")
    target_theme_txt = os.path.join(root, selected_name, "theme.txt")
    return (
        "sed -i '/^GRUB_THEME=/d' /etc/default/grub"
        f" && echo 'GRUB_THEME={shlex.quote(target_theme_txt)}' >> /etc/default/grub"
        " && grub2-mkconfig -o /boot/grub2/grub.cfg"
    )


def extract_archive(user_input_path: str, sandbox_dir: str = SANDBOX_DIR) -> str:
    """解压主题包到沙盒并返回沙盒路径；失败抛异常。"""
    if not os.path.exists(user_input_path):
        raise FileNotFoundError("指定的主题文件不存在！")
    if os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir)
    os.makedirs(sandbox_dir, exist_ok=True)
    try:
        if user_input_path.endswith('.zip'):
            with zipfile.ZipFile(user_input_path, 'r') as z:
                z.extractall(sandbox_dir)
        else:
            with tarfile.open(user_input_path, 'r:*') as t:
                t.extractall(sandbox_dir)
    except Exception:
        shutil.rmtree(sandbox_dir, ignore_errors=True)
        raise
    return sandbox_dir


def find_theme_dirs(sandbox_dir: str) -> dict[str, str]:
    """扫描沙盒，返回 {展示名: 主题目录}；无有效主题抛 ValueError。"""
    detected: dict[str, str] = {}
    for root, _dirs, files in os.walk(sandbox_dir):
        if "theme.txt" in files:
            current_dir = os.path.dirname(os.path.join(root, "theme.txt"))
            key = f"{os.path.basename(os.path.dirname(current_dir))} - {os.path.basename(current_dir)}"
            detected[key] = current_dir
    if not detected:
        raise ValueError("压缩包内未找到 theme.txt，配置丢失！")
    return detected


def build_install_script(source_dir: str, root: str = SYSTEM_THEMES_ROOT) -> tuple[str, str]:
    """外部主题安装脚本；返回 (脚本, 主题目录名)。目录名非法抛 ValueError。"""
    theme_name = os.path.basename(source_dir.rstrip("/"))
    if not VALID_NAME.match(theme_name):
        raise ValueError(f"主题目录名非法: {theme_name}")
    target_system_path = os.path.join(root, theme_name)
    theme_txt = os.path.join(target_system_path, "theme.txt")
    script = (
        f"mkdir -p {shlex.quote(root)}"
        f" && cp -r {shlex.quote(source_dir)} {shlex.quote(target_system_path)}"
        " && sed -i '/^GRUB_THEME=/d' /etc/default/grub"
        f" && echo 'GRUB_THEME={shlex.quote(theme_txt)}' >> /etc/default/grub"
        " && grub2-mkconfig -o /boot/grub2/grub.cfg"
    )
    return script, theme_name


def cleanup_sandbox(sandbox_dir: str = SANDBOX_DIR):
    if sandbox_dir and os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir, ignore_errors=True)
