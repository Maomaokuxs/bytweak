"""仪表盘桥接：卡片可见性配置（JSON 持久化）+ 跨页导航信号 + 系统硬件概览。"""
import json
import os
import platform
import shutil
import socket

from PySide6.QtCore import QObject, Signal, Property, Slot

from .utils import logger, get_os_info, is_fedora, is_atomic

CONFIG_DIR = os.path.expanduser("~/.config/fedora-tweak-tool")
CONFIG_PATH = os.path.join(CONFIG_DIR, "dashboard.json")

ALL_CARDS = [
    {"id": "timezone", "title": "时区"},
    {"id": "grub", "title": "GRUB"},
    {"id": "gpu", "title": "显卡"},
    {"id": "cursor", "title": "鼠标"},
    {"id": "repo", "title": "软件包"},
    {"id": "fcitx", "title": "输入法"},
    {"id": "desktop", "title": "桌面"},
    {"id": "service", "title": "服务"},
    {"id": "flatpak", "title": "Flatpak"},
    {"id": "dnf", "title": "DNF"},
]

CARD_PAGES = {"timezone": 1, "grub": 2, "gpu": 3, "cursor": 4,
              "repo": 5, "fcitx": 6, "desktop": 7,
              "service": 9, "flatpak": 10, "dnf": 11}


def _read_cpu_model() -> str:
    try:
        with open("/proc/cpuinfo", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return ""


def _read_mem() -> tuple[float, float]:
    """返回 (已用GB, 总量GB)；失败返回 (0, 0)。"""
    try:
        info = {}
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[0].rstrip(":") in ("MemTotal", "MemAvailable"):
                    info[parts[0].rstrip(":")] = int(parts[1])  # kB
        total = info.get("MemTotal", 0) / 1024 / 1024
        avail = info.get("MemAvailable", 0) / 1024 / 1024
        if total <= 0:
            return 0.0, 0.0
        return max(0.0, total - avail), total
    except Exception:
        return 0.0, 0.0


def _read_uptime() -> str:
    try:
        with open("/proc/uptime", encoding="utf-8") as f:
            secs = int(float(f.read().split()[0]))
        days, secs = divmod(secs, 86400)
        hours, secs = divmod(secs, 3600)
        minutes, _ = divmod(secs, 60)
        if days:
            return f"{days}天{hours}小时"
        if hours:
            return f"{hours}小时{minutes}分"
        return f"{minutes}分钟"
    except Exception:
        return ""


def _read_os_name() -> str:
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def hardware_overview() -> list[dict]:
    """返回 [{label, value}] 系统硬件概览行，失败项以 — 占位。"""
    rows = []
    try:
        rows.append({"label": "主机名", "value": socket.gethostname() or "—"})
    except Exception:
        rows.append({"label": "主机名", "value": "—"})
    rows.append({"label": "系统", "value": _read_os_name() or "—"})
    try:
        rows.append({"label": "内核", "value": platform.release() or "—"})
    except Exception:
        rows.append({"label": "内核", "value": "—"})
    rows.append({"label": "CPU", "value": _read_cpu_model() or "—"})
    used, total = _read_mem()
    if total > 0:
        rows.append({"label": "内存", "value": f"{used:.1f} / {total:.1f} GB（{used / total * 100:.0f}%）"})
    else:
        rows.append({"label": "内存", "value": "—"})
    try:
        du = shutil.disk_usage("/")
        rows.append({"label": "硬盘 /", "value": f"{du.used / 1024**3:.1f} / {du.total / 1024**3:.1f} GB（{du.used / du.total * 100:.0f}%）"})
    except Exception:
        rows.append({"label": "硬盘 /", "value": "—"})
    rows.append({"label": "运行时间", "value": _read_uptime() or "—"})
    return rows


def _load_visible() -> list[str]:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        saved = [c for c in data.get("cards", []) if c in CARD_PAGES]
        if saved:
            return saved
    except Exception:
        pass
    return [c["id"] for c in ALL_CARDS]


class DashboardBridge(QObject):
    cardsChanged = Signal()
    navigate = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        os_info = get_os_info()
        self._is_fedora = is_fedora(os_info)
        self._is_atomic = is_atomic(os_info)
        self._os_name = os_info.get("pretty", "") or "未知系统"
        self._visible: list[str] = _load_visible()
        if self._is_atomic and "dnf" in self._visible:
            self._visible.remove("dnf")

    def getOsName(self):
        return self._os_name

    osName = Property(str, getOsName, constant=True)

    def getIsFedora(self):
        return self._is_fedora

    isFedora = Property(bool, getIsFedora, constant=True)

    def getIsAtomic(self):
        return self._is_atomic

    isAtomic = Property(bool, getIsAtomic, constant=True)

    def getAllCards(self):
        if self._is_atomic:
            return [c for c in ALL_CARDS if c["id"] != "dnf"]
        return ALL_CARDS

    allCards = Property(list, getAllCards, constant=True)

    def getVisible(self):
        return list(self._visible)

    visibleCards = Property(list, getVisible, notify=cardsChanged)

    def getHardware(self):
        try:
            return hardware_overview()
        except Exception as e:
            logger.warning(f"hardware overview failed: {e}")
            return []

    hardwareInfo = Property(list, getHardware, notify=cardsChanged)

    @Slot(str, bool)
    def setCardVisible(self, card_id: str, on: bool):
        if card_id not in CARD_PAGES:
            return
        if on and card_id == "dnf" and self._is_atomic:
            return
        changed = False
        if on and card_id not in self._visible:
            order = [c["id"] for c in ALL_CARDS]
            self._visible.append(card_id)
            self._visible.sort(key=lambda c: order.index(c))
            changed = True
        elif not on and card_id in self._visible:
            self._visible.remove(card_id)
            changed = True
        if changed:
            self._save()
            self.cardsChanged.emit()

    @Slot(str)
    def goPage(self, card_id: str):
        if card_id == "dnf" and self._is_atomic:
            return
        if card_id in CARD_PAGES:
            self.navigate.emit(CARD_PAGES[card_id])

    def _save(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump({"cards": self._visible}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"dashboard config save failed: {e}")
