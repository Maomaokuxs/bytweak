"""软件源纯逻辑层：扫描解析 + 脚本构造，无 Qt Widgets 依赖。"""
import os
import re
import shlex
import subprocess

from .utils import get_releasever, get_basearch, rpmfusion_urls

REPO_DIR = "/etc/yum.repos.d"
REPO_ID_PATTERN = re.compile(r'^[A-Za-z0-9._:-]+$')
COPR_ID_PATTERN = re.compile(r'^[A-Za-z0-9_.-]+$')
PKG_NAME_PATTERN = re.compile(r'^[A-Za-z0-9._:+-]+$')
COPR_HUB = "https://copr.fedorainfracloud.org"

# (展示名, 标识, 是否已部署的检测路径)
RECOMMEND_MANIFEST = [
    ("RPM Fusion 官方合集 (自由与非自由源)", "REC_RPM_FUSION", "/etc/yum.repos.d/rpmfusion-free.repo"),
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


def scan_local_repos_libdnf5() -> list[dict]:
    """经 libdnf5 原生读取 [{id, name, enabled}]：名称已展开宏，状态权威，
    带冒号 Copr ID 原生支持。失败抛异常，由调用方回退文件解析。"""
    import libdnf5
    base = libdnf5.base.Base()
    base.load_config()
    base.setup()
    sack = base.get_repo_sack()
    sack.create_repos_from_system_configuration()
    query = libdnf5.repo.RepoQuery(base)
    repos = []
    for r in query:
        repos.append({"id": r.get_id(), "name": r.get_name() or r.get_id(),
                      "enabled": bool(r.is_enabled())})
    repos.sort(key=lambda r: r["id"])
    return repos


def scan_local_repos(repo_dir: str = REPO_DIR) -> list[dict]:
    """返回 [{id, name, enabled}]。优先 libdnf5 原生读取，失败回退文件解析。"""
    if repo_dir == REPO_DIR:
        try:
            return scan_local_repos_libdnf5()
        except Exception:
            pass
    return _scan_local_repos_files(repo_dir)


def _scan_local_repos_files(repo_dir: str = REPO_DIR) -> list[dict]:
    """文件解析兜底（无 libdnf5 环境用，如纯 pip  venv）。"""
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


def _check_copr_part(value: str, what: str) -> str:
    value = (value or "").strip()
    if not COPR_ID_PATTERN.match(value):
        raise ValueError(f"非法 COPR {what}: {value}")
    return value


def _copr_api_get(path: str, params: dict | None = None) -> object:
    """直接调用 COPR 只读 API（不依赖 python3-copr 库）。
    返回解析后的 JSON（dict 或 list）；网络异常直接抛。"""
    import json
    import urllib.parse
    import urllib.request
    url = COPR_HUB.rstrip("/") + "/api_3" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "fedora-tweak-tool/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _copr_items(data: object) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        items = data.get("items", [])
        return items if isinstance(items, list) else []
    return []


def search_copr_projects(keyword: str, limit: int = 20) -> list[dict]:
    """匿名搜索 COPR 项目（只读公开 API，无需 token）。
    返回 [{owner, project, full, description}]。网络异常直接抛，由调用方提示。
    注意：须在后台线程调用。"""
    keyword = (keyword or "").strip()
    if len(keyword) < 2:
        raise ValueError("搜索关键词至少 2 个字符")
    resp = _copr_api_get("/project/search", {"query": keyword})
    items = _copr_items(resp)
    out = []
    for p in items:
        if len(out) >= limit:
            break
        owner, name = str(p.get("ownername") or ""), str(p.get("name") or "")
        if not owner or not name:
            continue
        out.append({"owner": owner, "project": name, "full": f"{owner}/{name}",
                    "description": (p.get("description") or "").strip()[:200]})
    return out


def list_copr_packages(owner: str, project: str) -> list[str]:
    """列出某 COPR 项目提供的包名（匿名只读）。须在后台线程调用。"""
    owner = _check_copr_part(owner, "作者")
    project = _check_copr_part(project, "项目")
    import urllib.parse
    resp = _copr_api_get(
        "/package/list/" + urllib.parse.quote(owner, safe="") + "/" + urllib.parse.quote(project, safe="")
    )
    pkgs = _copr_items(resp)
    return sorted({str(p.get("name") or "") for p in pkgs if isinstance(p, dict) and p.get("name")})


def build_copr_enable_cmd(owner: str, project: str) -> list[str]:
    """启用 COPR 源命令（dnf5 copr 插件）；非法输入抛 ValueError。"""
    owner = _check_copr_part(owner, "作者")
    project = _check_copr_part(project, "项目")
    return ["dnf5", "copr", "enable", "-y", f"{owner}/{project}"]


def build_install_cmd(pkg: str) -> list[str]:
    """按名装包命令；非法包名抛 ValueError。"""
    pkg = (pkg or "").strip()
    if not PKG_NAME_PATTERN.match(pkg):
        raise ValueError(f"非法包名: {pkg}")
    return ["dnf5", "install", "-y", pkg]


def build_remove_cmd(pkg: str) -> list[str]:
    """按名卸包命令；非法包名抛 ValueError。"""
    pkg = (pkg or "").strip()
    if not PKG_NAME_PATTERN.match(pkg):
        raise ValueError(f"非法包名: {pkg}")
    return ["dnf5", "remove", "-y", pkg]


def build_upgrade_cmd() -> list[str]:
    """一键升级全部命令。"""
    return ["dnf5", "upgrade", "-y"]


def build_autoremove_cmd() -> list[str]:
    """自动移除孤包命令。"""
    return ["dnf5", "autoremove", "-y"]


def build_clean_cmd() -> list[str]:
    """清理全部缓存命令。"""
    return ["dnf5", "clean", "all"]


def list_upgradable() -> list[dict]:
    """可更新包 [{name, version, repo}]（`dnf5 list upgrades`，多源优先官方）。
    失败返回空列表。须在后台线程调用。"""
    try:
        cmd = subprocess.run(["dnf5", "list", "upgrades"],
                             capture_output=True, text=True, timeout=180)
    except Exception:
        return []
    return [{"name": name, "version": e["version"], "repo": _prefer_repo(e["repos"])}
            for name, e in sorted(_parse_dnf_list(cmd.stdout).items())]


def get_cache_size() -> str:
    """dnf 缓存占用（人类可读）；失败返回 —。"""
    total = 0
    for d in ("/var/cache/libdnf5", "/var/cache/dnf"):
        try:
            out = subprocess.run(["du", "-sb", d], capture_output=True,
                                 text=True, timeout=30).stdout
            total += int(out.split()[0])
        except Exception:
            continue
    size = float(total)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return "—"


_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def _parse_dnf_list(stdout: str) -> dict[str, dict]:
    """解析 `dnf5 list` 输出为 {包名: {"version": 版本, "repos": [仓库ID...]}}（跳过源码包）。"""
    found: dict[str, dict] = {}
    for line in stdout.split("\n"):
        line = _ANSI_RE.sub("", line).strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3 or "." not in parts[0]:
            continue
        name, arch = parts[0].rsplit(".", 1)
        if arch == "src":
            continue
        version, repo = parts[1], parts[-1]
        entry = found.setdefault(name, {"version": version, "repos": []})
        if repo not in entry["repos"]:
            entry["repos"].append(repo)
    return found


def _prefer_repo(repos: list[str]) -> str:
    """多源时优先官方源，其次第三方，最后 COPR。"""
    rank = {"official": 0, "thirdparty": 1, "copr": 2}
    return min(repos, key=lambda r: rank[classify_repo(r)])


# Fedora 官方源 ID（另含 fedora-/updates- 前缀的 debuginfo/source/testing 变体）
OFFICIAL_REPO_IDS = {"fedora", "updates", "updates-testing", "rawhide",
                     "fedora-cisco-openh264"}


def classify_repo(repo_id: str) -> str:
    """仓库来源分类：official（Fedora 官方）/ thirdparty（第三方）/ copr。"""
    rid = (repo_id or "").strip().lower()
    if rid.startswith("copr:"):
        return "copr"
    if rid in OFFICIAL_REPO_IDS or rid.startswith(("fedora-", "updates-")):
        return "official"
    return "thirdparty"


def search_available_packages(keyword: str, limit: int = 30) -> list[dict]:
    """按关键词在已启用源中搜索软件包（`dnf5 list --available *关键词*`）。
    返回 [{name, version, repo, source}]（按包名排序，最多 limit 个；
    source 为 official/thirdparty/copr，多源时优先官方）。
    关键词不足 2 字符抛 ValueError；网络/解析失败返回空列表。后台线程调用。"""
    cleaned = re.sub(r'[*?\[\]\\]', "", (keyword or "").strip().lower())
    if len(cleaned) < 2:
        raise ValueError("搜索关键词至少 2 个字符")
    try:
        cmd = subprocess.run(["dnf5", "list", "--available", f"*{cleaned}*"],
                             capture_output=True, text=True, timeout=120)
    except Exception:
        return []
    out = []
    for name, e in sorted(_parse_dnf_list(cmd.stdout).items()):
        best = _prefer_repo(e["repos"])
        out.append({"name": name, "version": e["version"],
                    "repo": best, "source": classify_repo(best)})
    return out[:limit]


def check_installed(names: list[str]) -> list[str]:
    """查一批包名是否已安装（`rpm -q --queryformat` 批量，输出与系统语言无关）。
    返回已安装包名列表。失败返回空列表。后台线程调用。"""
    clean: list[str] = []
    for n in names or []:
        n = (n or "").strip()
        if n and PKG_NAME_PATTERN.match(n) and n not in clean:
            clean.append(n)
    if not clean:
        return []
    try:
        cmd = subprocess.run(["rpm", "-q", "--queryformat", "%{NAME}\n"] + clean,
                             capture_output=True, text=True, timeout=30)
    except Exception:
        return []
    got = {line.strip() for line in cmd.stdout.split("\n") if line.strip()}
    return [n for n in clean if n in got]


def check_official_available(names: list[str]) -> dict[str, str]:
    """查一批包名在已启用源中的提供情况（解析 `dnf5 list --available`）。
    返回 {包名: 仓库ID}（多源时优先官方源）；查不到的包不出现。
    网络/解析失败返回空字典。须在后台线程调用。"""
    clean: list[str] = []
    for n in names or []:
        n = (n or "").strip()
        if n and PKG_NAME_PATTERN.match(n) and n not in clean:
            clean.append(n)
    if not clean:
        return {}
    try:
        cmd = subprocess.run(["dnf5", "list", "--available"] + clean,
                             capture_output=True, text=True, timeout=120)
    except Exception:
        return {}
    parsed = _parse_dnf_list(cmd.stdout)
    return {n: _prefer_repo(parsed[n]["repos"]) for n in clean if n in parsed}


# 失败诊断规则：(正则, 中文定位提示)。按序匹配，命中即返回。
_FAILURE_RULES = [
    (r"公共密钥尚未安装|public key.*not installed|gpg.*(key|check)|signature.*(fail|invalid)|数字签名",
     "GPG 校验失败：缺少或不受信任的签名密钥，可先安装对应的 release 包导入密钥"),
    (r"no space left|disk full|磁盘空间不足",
     "磁盘空间不足：请先清理缓存或删除无用文件后重试"),
    (r"could not resolve host|connection (refused|timed out)|无法连接|网络不可达|timed out|connect to",
     "网络问题：无法连接仓库服务器，请检查网络或稍后重试"),
    (r"\b(404|403)\b|cannot download|failed to download|下载.*失败|no more mirrors",
     "仓库地址不可用：可能是源地址过期或镜像未同步，请刷新软件源或更换镜像"),
    (r"conflicts? with|file .* conflicts|与.*冲突",
     "软件包冲突：与已安装的包存在文件/依赖冲突，需先卸载冲突包或改用其它版本"),
    (r"nothing provides|requires .*but none|依赖.*无法满足|未找到.*提供",
     "依赖缺失：所需的依赖包在已启用源中找不到，可能需要额外启用第三方源"),
    (r"no match for argument|未找到与|unable to find a match",
     "找不到该软件包：请确认包名拼写，或先在软件源中启用提供它的仓库"),
    (r"already installed|nothing to do|无需任何处理",
     "无需操作：目标软件包已是期望状态"),
    (r"not authorized|permission denied|权限不足|authentication",
     "权限不足：未能获得授权，操作已取消（注意不要关闭授权弹窗）"),
    (r"unsupported|not available on|no compatible architecture|架构",
     "架构不支持：该包没有适用于当前系统架构的版本"),
    (r"transaction.*(test|check).*failed|test transaction",
     "事务校验失败：软件包管理器预演未通过，详情见输出"),
]


def diagnose_failure(text: str) -> str:
    """根据错误输出给出一句中文定位提示；无法识别返回空串。"""
    if not text:
        return ""
    for pattern, hint in _FAILURE_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            return hint
    return ""


def build_recommended_script(rec_id: str, enable: bool) -> str:
    """推荐源部署/移除脚本；未知 ID 抛 ValueError。"""
    free_url, nonfree_url = rpmfusion_urls()
    if rec_id == "REC_RPM_FUSION":
        if enable:
            return f"dnf5 install -y {shlex.quote(free_url)} {shlex.quote(nonfree_url)} && dnf5 update -y --refresh"
        return "dnf5 remove -y rpmfusion-free-release rpmfusion-nonfree-release; rm -f /etc/yum.repos.d/rpmfusion-*.repo"
    raise ValueError(f"未知推荐源: {rec_id}")
