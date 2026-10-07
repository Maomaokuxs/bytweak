"""主机名纯逻辑层：hostnamectl 查询/校验，无 Qt 依赖。"""
import re
import subprocess

HOSTNAME_PATTERN = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def current_hostname() -> str:
    try:
        r = subprocess.run(["hostnamectl", "--static"], capture_output=True,
                           text=True, timeout=5)
    except FileNotFoundError:
        raise RuntimeError("未找到 hostnamectl")
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "读取主机名失败")
    return r.stdout.strip()


def build_set_hostname_cmd(name: str) -> list[str]:
    """构造 hostnamectl set-hostname 命令；非法输入抛 ValueError。"""
    name = (name or "").strip()
    if not HOSTNAME_PATTERN.match(name):
        raise ValueError("主机名只能包含字母、数字和连字符，不能以连字符开头或结尾，最长 64 字符")
    return ["hostnamectl", "set-hostname", name]
