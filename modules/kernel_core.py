"""内核管理纯逻辑层：rpm 查询 + grubby/dnf 命令构造，无 Qt 依赖。"""
import os
import re
import subprocess

FULL_PATTERN = re.compile(r"^[0-9][A-Za-z0-9_+.~:-]*$")
KERNEL_PKGS = ("kernel", "kernel-core", "kernel-modules",
               "kernel-modules-core", "kernel-modules-extra")


def _run(*args: str, timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), capture_output=True, text=True,
                          timeout=timeout)


def current_kernel() -> str:
    r = _run("uname", "-r")
    if r.returncode != 0:
        raise RuntimeError("读取当前内核失败")
    return r.stdout.strip()


def default_kernel() -> str:
    """grubby 默认启动内核版本（vmlinuz 文件名后缀）；失败返回空串。"""
    try:
        r = _run("grubby", "--default-kernel")
    except FileNotFoundError:
        return ""
    if r.returncode != 0:
        return ""
    p = r.stdout.strip()
    return p[len("/boot/vmlinuz-"):] if p.startswith("/boot/vmlinuz-") else ""


def list_kernels() -> list[dict]:
    """返回 [{full, current, is_default, pkgs}]，按安装时间倒序。"""
    r = _run("rpm", "-q", "kernel", "--queryformat",
             "%{VERSION}-%{RELEASE}.%{ARCH} %{INSTALLTIME}\n")
    if r.returncode != 0:
        raise RuntimeError("未找到已安装的 kernel 包")
    try:
        cur = current_kernel()
    except Exception:
        cur = ""
    dft = default_kernel()
    items = []
    for line in r.stdout.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        full, ts = parts
        if not FULL_PATTERN.match(full):
            continue
        pkgs = []
        for pkg in KERNEL_PKGS:
            q = _run("rpm", "-q", f"{pkg}-{full}")
            if q.returncode == 0 and "is not installed" not in q.stdout:
                pkgs.append(f"{pkg}-{full}")
        items.append({"full": full, "current": full == cur,
                      "is_default": full == dft, "pkgs": pkgs,
                      "_ts": int(ts) if ts.isdigit() else 0})
    items.sort(key=lambda k: k["_ts"], reverse=True)
    for k in items:
        del k["_ts"]
    return items


def build_remove_cmd(full: str, kernels: list[dict] | None = None) -> list[str]:
    """构造 dnf 移除内核命令；删当前/默认/最后一个抛 ValueError。"""
    full = (full or "").strip()
    if not FULL_PATTERN.match(full):
        raise ValueError(f"非法内核版本: {full}")
    ks = kernels if kernels is not None else list_kernels()
    target = next((k for k in ks if k["full"] == full), None)
    if not target:
        raise ValueError(f"未安装该内核: {full}")
    if target["current"]:
        raise ValueError("不能删除正在运行的内核")
    if target["is_default"]:
        raise ValueError("不能删除默认启动内核，请先切换默认项")
    if len(ks) <= 1:
        raise ValueError("只剩一个内核，不能删除")
    if not target["pkgs"]:
        raise ValueError(f"未找到 {full} 的软件包")
    return ["dnf", "-y", "remove", *target["pkgs"]]


def build_set_default_cmd(full: str) -> list[str]:
    """构造 grubby 设默认内核命令；非法输入或 vmlinuz 不存在抛 ValueError。"""
    full = (full or "").strip()
    if not FULL_PATTERN.match(full):
        raise ValueError(f"非法内核版本: {full}")
    vmlinuz = f"/boot/vmlinuz-{full}"
    if not os.path.isfile(vmlinuz):
        raise ValueError(f"找不到 {vmlinuz}")
    return ["grubby", "--set-default", vmlinuz]
