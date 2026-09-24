import subprocess
from PySide6.QtCore import QObject, QEvent, QPoint
from PySide6.QtWidgets import QApplication, QMessageBox
from .utils import logger


class TimezoneManager(QObject):
    """时区管理：下拉弹窗通过事件过滤限宽高（DPR 自适应），不做猴子补丁。"""

    def __init__(self, app_ctx):
        super().__init__(app_ctx.window if hasattr(app_ctx, "window") else None)
        self.ctx = app_ctx
        logger.debug("TimezoneManager mounted")

    def init_timezone_list(self):
        if not self.ctx.combo:
            return
        try:
            self.ctx.combo.setMaxVisibleItems(12)
            self.ctx.combo.installEventFilter(self)
        except Exception:
            pass
        try:
            logger.debug("fetching timezones via timedatectl")
            result = subprocess.run(["timedatectl", "list-timezones"], capture_output=True, text=True, check=True, timeout=5)
            all_zones = [zone.strip() for zone in result.stdout.split("\n") if zone.strip()]
            self.ctx.combo.clear()
            self.ctx.combo.addItems(all_zones)
            logger.debug(f"timezones loaded: {len(all_zones)}")
        except Exception as e:
            logger.warning(f"list-timezones failed, fallback: {e}")
            self.ctx.combo.addItems(["Asia/Shanghai", "UTC"])

    def eventFilter(self, obj, event):
        # 下拉前（鼠标/键盘触发）先把 view 尺寸钳住；QComboBox 弹窗是独立顶层，不受父布局裁剪
        if obj is self.ctx.combo and event.type() in (QEvent.MouseButtonPress, QEvent.KeyPress):
            try:
                self._clamp_popup()
            except Exception as e:
                logger.debug(f"clamp popup failed: {e}")
        return False

    def _clamp_popup(self):
        combo = self.ctx.combo
        v = combo.view()
        try:
            scr = QApplication.screenAt(combo.mapToGlobal(QPoint(0, 0))) or QApplication.primaryScreen()
            dpr = float(scr.devicePixelRatio() if scr else 1.0)
        except Exception:
            dpr = 1.0
        max_w = int(420 * dpr)
        if getattr(self.ctx, "content_stack", None) and self.ctx.content_stack.width() > 100:
            max_w = int(self.ctx.content_stack.width() * 0.88 - 16)
            max_w = max(int(280 * dpr), min(int(520 * dpr), max_w))
        try:
            screen = QApplication.screenAt(combo.mapToGlobal(QPoint(0, 0))) or QApplication.primaryScreen()
            geo = screen.availableGeometry() if screen else None
            if geo:
                combo_global = combo.mapToGlobal(QPoint(0, 0))
                avail_right = geo.right() - combo_global.x() - 8
                avail_left = combo_global.x() - geo.left() + combo.width() - 8
                max_w = min(max_w, max(int(200 * dpr), avail_right),
                            max(int(200 * dpr), avail_left + combo.width()))
                max_w = min(max_w, int(geo.width() * 0.42))
                below = geo.bottom() - (combo_global.y() + combo.height()) - 12
                above = combo_global.y() - geo.top() - 12
                avail_h = max(below, above, int(160 * dpr))
                cap_h = min(int(self.ctx.window.height() * 0.58), int(geo.height() * 0.48), int(380 * dpr))
                avail_h = max(int(160 * dpr), min(avail_h, cap_h))
                v.setMaximumHeight(avail_h)
        except Exception:
            pass
        v.setMinimumWidth(min(combo.width(), max_w))
        v.setMaximumWidth(max_w)

    def refresh_current_timezone(self):
        try:
            result = subprocess.run(["timedatectl", "show", "--property=Timezone", "--value"], capture_output=True, text=True, check=True, timeout=3)
            current_zone = result.stdout.strip()
            logger.debug(f"current timezone: {current_zone}")
            if self.ctx.current_lbl:
                self.ctx.current_lbl.setText(current_zone)
            if self.ctx.combo:
                index = self.ctx.combo.findText(current_zone)
                if index != -1:
                    self.ctx.combo.setCurrentIndex(index)
                    logger.debug(f"combo synced to index {index} ({current_zone})")
                else:
                    logger.warning(f"combo missing current zone '{current_zone}'")
        except Exception as e:
            logger.warning(f"refresh_current_timezone failed: {e}")

    def apply_timezone(self):
        if not self.ctx.combo:
            return
        target_zone = self.ctx.combo.currentText().strip()
        if not target_zone or "/" not in target_zone:
            QMessageBox.warning(self.ctx.window, "提示", "请选择合法时区")
            return
        logger.debug(f"apply timezone -> {target_zone}")
        cmd = ["pkexec", "timedatectl", "set-timezone", target_zone]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                QMessageBox.information(self.ctx.window, "提示", "配置成功")
                self.refresh_current_timezone()
            else:
                if "canceled" in (result.stderr or "").lower():
                    logger.debug("pkexec canceled by user")
                else:
                    QMessageBox.critical(self.ctx.window, "失败", result.stderr.strip() or "授权失败或执行错误")
        except Exception as e:
            logger.error(f"apply_timezone failed: {e}")
            QMessageBox.critical(self.ctx.window, "失败", str(e))
