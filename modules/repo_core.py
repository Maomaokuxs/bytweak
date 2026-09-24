"""软件源纯逻辑层：扫描解析 + 脚本构造，无 Qt Widgets 依赖。"""
import os
import re
import shlex
import subprocess

from .utils import get_releasever, get_basearch, rpmfusion_urls

REPO_DIR = "/etc/yum.repos.d"
REPO_ID_PATTERN = re.compile(r'^[A-Za-z0-9._:-]+$')

# (展示名, 标识, 是否已部署的检测路径)
RECOMMEND_MANIFEST = [
    ("RPM Fusion 官方合集 (自由与非自由源)", "REC_RPM_FUSION", "/etc/yum.repos.d/rpmfusion-free.repo"),
    ("Google Chrome 官方源", "REC_GOOGLE_CHROME", "/etc/yum.repos.d/google-chrome.repo"),
    ("VSCode / Codium 微软官方源", "REC_VSCODE", "/etc/yum.repos.d/vscode.repo"),
]


def _expand_macros(text: str, releasever: str, basearch: str) -> str:
    return (text.replace("$releasever", releasever).replace("$basearch", basearch)
                .replace("${releasever}", releasever).replace("${basearch}", basearch))


def query_enabled_repos() -> set[str]:
    """向 DNF5 索要真实启用清单；失败返回空集合（调用方回退文件解析）。"""
    enabled: set[str] = set()
    cmd = subprocess.run(["dnf5", "repolist", "--enabled"], capture_output=True, text=True, timeout=10)
    for line in cmd.stdout.split("\n"):
        line = line.strip()
        if not line or line.lower().startswith("repo id") or "仓库 id" in line.lower() or line.startswith("="):
            continue
        parts = line.split()
        if parts:
            enabled.add(parts[0])
    return enabled


def scan_local_repos(repo_dir: str = REPO_DIR) -> list[dict]:
    """返回 [{id, name, enabled}]。"""
    releasever = get_releasever()
    basearch = get_basearch()
    try:
        true_enabled = query_enabled_repos()
    except Exception:
        true_enabled = set()
    repos: list[dict] = []
    if not os.path.exists(repo_dir):
        return repos
    for file_name in sorted(os.listdir(repo_dir)):
        if not file_name.endswith(".repo"):
            continue
        try:
            with open(os.path.join(repo_dir, file_name), "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue
        for section in re.split(r'^\[', content, flags=re.MULTILINE):
            if not section.strip():
                continue
            id_match = re.match(r'^([^\]\n]+)\]', section)
            if not id_match:
                continue
            repo_id = id_match.group(1).strip()
            name_match = re.search(r'^\s*name\s*=\s*(.+)$', section, re.MULTILINE)
            repo_name = name_match.group(1).strip() if name_match else repo_id
            repo_name = _expand_macros(repo_name, releasever, basearch)
            if true_enabled:
                is_enabled = repo_id in true_enabled
            else:
                matches = re.findall(r'^\s*enabled\s*=\s*(.+)$', section, re.MULTILINE)
                if matches:
                    is_enabled = matches[-1].strip() not in ("0", "false", "False")
                else:
                    is_enabled = True
            repos.append({"id": repo_id, "name": repo_name, "enabled": is_enabled})
    return repos


def scan_recommended() -> list[dict]:
    """返回 [{id, label, installed}]。"""
    return [{"id": rec_id, "label": label, "installed": os.path.exists(check_path)}
            for label, rec_id, check_path in RECOMMEND_MANIFEST]


def build_toggle_cmd(repo_id: str, enable: bool) -> list[str]:
    """本地源启闭命令（列表形式防注入）；非法 ID 抛 ValueError。"""
    if not REPO_ID_PATTERN.match(repo_id or ""):
        raise ValueError(f"非法 RepoID: {repo_id}")
    return ["dnf5", "config-manager", "enable" if enable else "disable", repo_id]


def build_recommended_script(rec_id: str, enable: bool) -> str:
    """推荐源部署/移除脚本；未知 ID 抛 ValueError。"""
    free_url, nonfree_url = rpmfusion_urls()
    if rec_id == "REC_RPM_FUSION":
        if enable:
            return f"dnf5 install -y {shlex.quote(free_url)} {shlex.quote(nonfree_url)} && dnf5 update -y --refresh"
        return "dnf5 remove -y rpmfusion-free-release rpmfusion-nonfree-release; rm -f /etc/yum.repos.d/rpmfusion-*.repo"
    if rec_id == "REC_GOOGLE_CHROME":
        if enable:
            return ("dnf5 config-manager enable google-chrome 2>/dev/null || "
                    "(printf '[google-chrome]\\nname=google-chrome\\nbaseurl=http://dl.google.com/linux/chrome/rpm/stable/x86_64\\n"
                    "enabled=1\\ngpgcheck=1\\ngpgkey=https://dl.google.com/linux/linux_signing_key.pub\\n' "
                    "> /etc/yum.repos.d/google-chrome.repo)")
        return "rm -f /etc/yum.repos.d/google-chrome.repo"
    if rec_id == "REC_VSCODE":
        if enable:
            return ("printf '[code]\\nname=Visual Studio Code\\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\\n"
                    "enabled=1\\ngpgcheck=1\\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc\\n' "
                    "> /etc/yum.repos.d/vscode.repo")
        return "rm -f /etc/yum.repos.d/vscode.repo"
    raise ValueError(f"未知推荐源: {rec_id}")
