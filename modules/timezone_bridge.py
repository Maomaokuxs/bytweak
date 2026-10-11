"""时区 QML 桥接：timedatectl 读写，pkexec 提权走后台线程。"""
import subprocess
from PySide6.QtCore import QObject, Signal, Property, Slot

from .utils import logger
from .workers import Worker


def list_timezones() -> list[str]:
    try:
        r = subprocess.run(["timedatectl", "list-timezones"], capture_output=True, text=True, check=True, timeout=5)
        return [z.strip() for z in r.stdout.split("\n") if z.strip()]
    except Exception as e:
        logger.warning(f"list-timezones failed: {e}")
        return ["Asia/Shanghai", "UTC"]


def current_timezone() -> str:
    r = subprocess.run(["timedatectl", "show", "--property=Timezone", "--value"],
                       capture_output=True, text=True, check=True, timeout=3)
    return r.stdout.strip()


class TimezoneBridge(QObject):
    statusChanged = Signal()
    zonesChanged = Signal()
    busyChanged = Signal()
    message = Signal(str, str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._zones: list[str] = []
        # 实际系统时区：只由 refresh() 从 timedatectl 读取更新
        self._current_index = -1
        # 下拉框里的用户选择：setZone/setZoneByName 更新，apply() 应用它
        self._selected_index = -1
        self._busy = False
        self._workers: list[Worker] = []

    def getStatus(self):
        # 只显示真实系统时区，不受下拉框选择影响
        if 0 <= self._current_index < len(self._zones):
            return f"当前系统时区：{self._zones[self._current_index]}"
        return "当前系统时区：正在获取..."

    statusText = Property(str, getStatus, notify=zonesChanged)

    def getZones(self):
        return self._zones

    zoneList = Property(list, getZones, notify=zonesChanged)

    def getCurrentIndex(self):
        # 供下拉框 currentIndex 绑定：显示的是用户选择
        return self._selected_index

    def _setSelectedIndex(self, v):
        if self._selected_index != v:
            self._selected_index = v
            self.zonesChanged.emit()

    currentZoneIndex = Property(int, getCurrentIndex, notify=zonesChanged)

    def getBusy(self):
        return self._busy

    def _setBusy(self, v):
        if self._busy != v:
            self._busy = v
            self.busyChanged.emit()

    busy = Property(bool, getBusy, notify=busyChanged)

    @Slot()
    def refresh(self):
        try:
            zones = list_timezones()
            try:
                current = current_timezone()
            except Exception:
                current = ""
            self._zones = zones
            self._current_index = zones.index(current) if current in zones else (0 if zones else -1)
            # 刷新时选中项同步为真实时区
            self._selected_index = self._current_index
            self.zonesChanged.emit()
            logger.debug(f"timezone synced to '{current}'")
        except Exception as e:
            logger.warning(f"bridge timezone refresh failed: {e}")

    @Slot(int)
    def setZone(self, index: int):
        # 只改用户选择，不碰实际时区显示
        if 0 <= index < len(self._zones):
            self._setSelectedIndex(index)

    @Slot(str, result=bool)
    def setZoneByName(self, name: str) -> bool:
        """可搜索下拉框确认：精确匹配优先，忽略大小写兜底。
        返回是否匹配成功；失败弹提示。供回车与“应用”按钮共用，避免
        打字后直接点应用导致新旧选项错位。"""
        text = (name or "").strip()
        if text in self._zones:
            self._setSelectedIndex(self._zones.index(text))
            return True
        lowered = text.lower()
        for i, z in enumerate(self._zones):
            if z.lower() == lowered:
                self._setSelectedIndex(i)
                return True
        self.message.emit("提示", f"未找到时区：{text}", True)
        return False

    @Slot()
    def apply(self):
        if self._busy:
            return
        if not (0 <= self._selected_index < len(self._zones)):
            self.message.emit("提示", "请选择合法时区", True)
            return
        target = self._zones[self._selected_index]
        if "/" not in target:
            self.message.emit("提示", "请选择合法时区", True)
            return
        if self._selected_index == self._current_index:
            self.message.emit("提示", "已经是当前时区，无需修改", False)
            return
        logger.debug(f"apply timezone -> {target}")
        self._setBusy(True)

        def _task():
            result = subprocess.run(["pkexec", "timedatectl", "set-timezone", target],
                                    capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "授权失败或执行错误")
            return result

        worker = Worker(_task, label=f"时区/切换 {target}", timeout=60)
        self._workers.append(worker)

        def on_ok(_):
            self._setBusy(False)
            self.message.emit("提示", "配置成功", False)
            self.refresh()
            self._cleanup(worker)

        def on_err(msg: str):
            self._setBusy(False)
            if "canceled" not in msg.lower() and "dismissed" not in msg.lower():
                self.message.emit("失败", msg, True)
            self._cleanup(worker)

        worker.finished_ok.connect(on_ok)
        worker.finished_err.connect(on_err)
        worker.start()

    def _cleanup(self, worker: Worker):
        try:
            worker.finished_ok.disconnect()
            worker.finished_err.disconnect()
        except Exception:
            pass
        if worker in self._workers:
            self._workers.remove(worker)
        # 超时线程任其自生自灭：不再触碰，避免销毁仍在运行的线程导致崩溃
        if not getattr(worker, "timed_out", False):
            worker.deleteLater()
