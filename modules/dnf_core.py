"""DNF 调优纯逻辑层：/etc/dnf/dnf.conf [main] 读写 + 校验，无 Qt 依赖。"""
import configparser
import os
import shutil

DNF_CONF = "/etc/dnf/dnf.conf"

INT_KEYS = {"max_parallel_downloads": (1, 20), "installonly_limit": (2, 10)}
BOOL_KEYS = ("fastestmirror", "keepcache", "clean_requirements_on_remove", "best")
ALL_KEYS = tuple(INT_KEYS) + BOOL_KEYS
DEFAULTS = {"max_parallel_downloads": "10", "installonly_limit": "3",
            "fastestmirror": "true", "keepcache": "false",
            "clean_requirements_on_remove": "true", "best": "true"}


def _has_dnf() -> bool:
    return shutil.which("dnf5") is not None or shutil.which("dnf") is not None


def dnf_supported() -> bool:
    return os.path.exists(DNF_CONF) or _has_dnf()


def read_settings(path: str = DNF_CONF) -> dict:
    """读 [main] 配置并叠加默认值；文件缺失返回默认值。"""
    cfg = dict(DEFAULTS)
    if os.path.exists(path):
        try:
            cp = configparser.ConfigParser()
            cp.optionxform = str
            with open(path, encoding="utf-8", errors="ignore") as f:
                cp.read_file(f)
            if cp.has_section("main"):
                for k in ALL_KEYS:
                    if cp.has_option("main", k):
                        cfg[k] = cp.get("main", k).strip()
        except Exception:
            pass
    return cfg


def validate_settings(raw: dict) -> dict:
    """校验并归一化；非法抛 ValueError。返回 {key: 字符串值}。"""
    out: dict[str, str] = {}
    for k, (lo, hi) in INT_KEYS.items():
        try:
            v = int(str(raw.get(k, DEFAULTS[k])).strip())
        except (ValueError, TypeError):
            raise ValueError(f"非法数值 {k}: {raw.get(k)}")
        if not lo <= v <= hi:
            raise ValueError(f"{k} 取值范围 {lo}~{hi}")
        out[k] = str(v)
    for k in BOOL_KEYS:
        v = str(raw.get(k, DEFAULTS[k])).strip().lower()
        if v in ("1", "true", "yes", "on"):
            out[k] = "true"
        elif v in ("0", "false", "no", "off"):
            out[k] = "false"
        else:
            raise ValueError(f"非法布尔值 {k}: {raw.get(k)}")
    return out
