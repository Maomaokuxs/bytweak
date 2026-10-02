"""Flatpak 纯逻辑层：CLI 查询解析 + 命令构造，无 Qt 依赖。"""
import re
import shutil
import subprocess

APP_ID_PATTERN = re.compile(r'^[A-Za-z0-9_.-]+(\.[A-Za-z0-9_.-]+)+$')
REMOTE_PATTERN = re.compile(r'^[A-Za-z0-9_.-]+$')


def flatpak_available() -> bool:
    return shutil.which("flatpak") is not None


def _run(*args: str, timeout: int = 60) -> str:
    cmd = subprocess.run(["flatpak", *args], capture_output=True,
                         text=True, timeout=timeout)
    if cmd.returncode != 0:
        raise RuntimeError((cmd.stderr or cmd.stdout).strip() or "flatpak 执行失败")
    return cmd.stdout


def list_apps() -> list[dict]:
    """已安装应用 [{id, name, version, branch, origin, scope}]。须后台线程调用。"""
    out = _run("list", "--app", "--columns=application,name,version,branch,origin,installation")
    apps = []
    for line in out.split("\n"):
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) < 6 or not parts[0]:
            continue
        apps.append({"id": parts[0], "name": parts[1] or parts[0], "version": parts[2],
                     "branch": parts[3], "origin": parts[4], "scope": parts[5]})
    apps.sort(key=lambda a: a["id"].lower())
    return apps


def list_remotes() -> list[dict]:
    """远程源 [{name, scope}]。须后台线程调用。"""
    out = _run("remotes")
    remotes = []
    for line in out.split("\n"):
        parts = line.split()
        if not parts:
            continue
        opts = parts[1] if len(parts) > 1 else ""
        remotes.append({"name": parts[0],
                        "scope": "system" if "system" in opts else "user"})
    return remotes


def _check_app(app_id: str) -> str:
    app_id = (app_id or "").strip()
    if not APP_ID_PATTERN.match(app_id):
        raise ValueError(f"非法应用 ID: {app_id}")
    return app_id


def _check_scope(scope: str) -> str:
    if scope not in ("user", "system"):
        raise ValueError(f"非法安装位置: {scope}")
    return scope


def build_install_cmd(app_id: str, remote: str = "flathub", scope: str = "user") -> list[str]:
    """安装命令；user 域无需提权，system 域由调用方 pkexec。"""
    app_id = _check_app(app_id)
    remote = (remote or "").strip()
    if not REMOTE_PATTERN.match(remote):
        raise ValueError(f"非法远程源: {remote}")
    return ["flatpak", "install", "-y", f"--{scope}", remote, app_id]


def build_uninstall_cmd(app_id: str, scope: str = "user") -> list[str]:
    return ["flatpak", "uninstall", "-y", f"--{_check_scope(scope)}", _check_app(app_id)]


def build_update_cmd() -> list[str]:
    return ["flatpak", "update", "-y"]
