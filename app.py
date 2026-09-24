#!/usr/bin/python3
import sys
import os

# 系统级打包路径与本地开发路径注入 sys.path，防止模块 ImportError
sys.path.insert(0, "/usr/share/fedora-tweak-tool")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QPushButton, QLabel, 
                               QListWidget, QStackedWidget, QLineEdit, QMainWindow, QCheckBox, QWidget, QFrame)

try:
    from modules.utils import logger
except Exception:
    import logging
    logger = logging.getLogger("fedora-tweak-tool")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)

# 挂载所有的模块化引擎
from modules.timezone import TimezoneManager
from modules.gpu import GpuManager
from modules.grub import GrubManager
from modules.cursor import CursorManager
from modules.repo import RepoManager
from modules.fcitx import FcitxManager
from modules.desktop import DesktopManager

class FedoraTweakApp:
    def __init__(self):
        # =====================================================================
        # 1. 自适应路径加载 UI 文件（本地开发版优先）
        # =====================================================================
        loader = QUiLoader()
        ui_possible_paths = [
            # 第一优先级：当前代码所在目录下的 main.ui（开发修改立刻生效）
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.ui"), 
            # 第二优先级：当前终端工作目录下的 main.ui
            "main.ui",
            # 第三优先级（兜底）：系统级打包安装后的只读路径
            "/usr/share/fedora-tweak-tool/main.ui"  
        ]
        
        ui_path = next((path for path in ui_possible_paths if os.path.exists(path)), None)
        if not ui_path:
            logger.critical("无法找到 main.ui 核心资源文件！")
            sys.exit(-1)
        logger.debug(f"UI 资源命中: {ui_path}")

        ui_file = QFile(ui_path)
        if not ui_file.open(QFile.ReadOnly):
            logger.critical(f"无法打开 UI 文件: {ui_path}")
            sys.exit(-1)
        self.window = loader.load(ui_file)
        ui_file.close()
        if self.window is None:
            logger.critical("QUiLoader 加载失败，UI 为空")
            sys.exit(-1)

        # 全局状态防死锁锁定位
        self._is_loading_repos = False

        # =====================================================================
        # 2. 获取 UI 组件（带类型与缺失告警）
        # =====================================================================
        def _find(cls, name, required=False):
            obj = self.window.findChild(cls, name)
            if not obj and required:
                logger.warning(f"UI 组件缺失: {cls.__name__}#{name}")
            return obj

        # --- 中央路由组件 ---
        self.nav_list = _find(QListWidget, "nav_list", required=True)
        self.content_stack = _find(QStackedWidget, "content_stack", required=True)
        logger.debug(f"nav_list: {'OK' if self.nav_list else 'MISSING'} | content_stack pages: {self.content_stack.count() if self.content_stack else 0}")

        # --- 时区组件 ---
        self.combo = _find(QComboBox, "timezone_combo")
        self.btn = _find(QPushButton, "apply_btn")
        self.current_lbl = _find(QLabel, "current_zone_lbl")

        # --- GRUB 引导组件（下拉框即当前状态，无独立状态标签） ---
        self.current_grub_lbl = None
        self.grub_path_edit = _find(QLineEdit, "grub_path_edit")
        self.grub_browse_btn = _find(QPushButton, "grub_browse_btn")
        self.grub_apply_btn = _find(QPushButton, "grub_apply_btn")
        self.grub_theme_combo = _find(QComboBox, "grub_theme_combo")
        self.grub_refresh_btn = _find(QPushButton, "grub_refresh_btn")

        # --- GPU 硬件组件 ---
        self.gpu_info_lbl = _find(QLabel, "gpu_info_lbl")
        self.driver_status_lbl = _find(QLabel, "driver_status_lbl")
        self.gpu_driver_version_lbl = _find(QLabel, "gpu_driver_version_lbl")
        self.gpu_action_btn = _find(QPushButton, "gpu_action_btn")
        self.gpu_refresh_btn = _find(QPushButton, "gpu_refresh_btn")
        # 显卡设备列表由 gpu_info_lbl 统一渲染（富文本行），不再使用代码拼装卡片
        self.gpu_cards_container = None
        self.gpu_cards_layout = None
        self.codec_h264_lbl = _find(QLabel, "codec_h264_lbl")
        self.codec_h265_lbl = _find(QLabel, "codec_h265_lbl")
        self.codec_av1_lbl = _find(QLabel, "codec_av1_lbl")
        self.codec_vp9_lbl = _find(QLabel, "codec_vp9_lbl")
        self.codec_nvenc_lbl = _find(QLabel, "codec_nvenc_lbl")
        self.codec_vaapi_lbl = _find(QLabel, "codec_vaapi_lbl")

        # --- 鼠标与输入法组件 ---
        self.cursor_theme_combo = _find(QComboBox, "cursor_theme_combo")
        self.cursor_path_edit = _find(QLineEdit, "cursor_path_edit")
        self.cursor_browse_btn = _find(QPushButton, "btn_browse_cursor")
        if not self.cursor_browse_btn:
            self.cursor_browse_btn = _find(QPushButton, "cursor_browse_btn")
        self.cursor_apply_btn = _find(QPushButton, "btn_apply_cursor")
        if not self.cursor_apply_btn:
            self.cursor_apply_btn = _find(QPushButton, "cursor_apply_btn")
        self.cursor_preview_lbl = _find(QLabel, "cursor_preview_lbl")
        if self.cursor_preview_lbl:
            canvas = QPixmap(128, 128)
            canvas.fill(Qt.transparent)
            self.cursor_preview_lbl.setPixmap(canvas)

        # --- 软件源大管家组件 ---
        self.repo_list_widget = _find(QListWidget, "repo_list_widget")
        self.recommended_repo_list = _find(QListWidget, "recommended_repo_list")
        self.repo_refresh_btn = _find(QPushButton, "repo_refresh_btn")

        # --- Fcitx 输入法主题组件 ---
        self.fcitx_current_theme_lbl = _find(QLabel, "fcitx_current_theme_lbl")
        self.fcitx_theme_combo = _find(QComboBox, "fcitx_theme_combo")
        self.fcitx_dark_theme_combo = _find(QComboBox, "fcitx_dark_theme_combo")
        self.fcitx_auto_switch_check = _find(QCheckBox, "fcitx_auto_switch_check")
        self.fcitx_path_edit = _find(QLineEdit, "fcitx_path_edit")
        self.fcitx_browse_btn = _find(QPushButton, "fcitx_browse_btn")
        self.fcitx_apply_btn = _find(QPushButton, "fcitx_apply_btn")
        self.fcitx_refresh_btn = _find(QPushButton, "fcitx_refresh_btn")
        # 输入法页无预览控件（主题配置即时生效，无需占位）
        self.fcitx_preview_lbl = None

        # --- 现代抛光：导航图标 + 柔和阴影（无新依赖，缺图标主题时自动退化为纯文本） ---
        self._page_anim = None
        self._fade_anim = None
        try:
            from PySide6.QtGui import QIcon
            from PySide6.QtCore import QSize
            _icon_names = [
                ("preferences-system-time", "clock"),
                ("drive-harddisk", "system-boot"),
                ("video-display", "video-card"),
                ("input-mouse", "preferences-desktop-peripherals"),
                ("system-software-install", "software-update-available"),
                ("input-keyboard", "preferences-desktop-locale"),
                ("preferences-desktop", "applications-system"),
            ]
            if self.nav_list:
                self.nav_list.setIconSize(QSize(20, 20))
                for _i in range(self.nav_list.count()):
                    _names = _icon_names[_i] if _i < len(_icon_names) else ()
                    _icon = QIcon()
                    for _n in _names:
                        _icon = QIcon.fromTheme(_n)
                        if not _icon.isNull():
                            break
                    if not _icon.isNull():
                        _item = self.nav_list.item(_i)
                        if _item:
                            _item.setIcon(_icon)
        except Exception as _e:
            logger.warning(f"nav icons failed: {_e}")
        try:
            from PySide6.QtWidgets import QGraphicsDropShadowEffect
            from PySide6.QtGui import QColor
            for _w in (
                self.window.findChild(QWidget, "header_bar"),
                self.nav_list,
                self.content_stack,
            ):
                if _w is None:
                    continue
                _shadow = QGraphicsDropShadowEffect(_w)
                _shadow.setBlurRadius(18)
                _shadow.setOffset(0, 2)
                _shadow.setColor(QColor(17, 24, 39, 28))
                _w.setGraphicsEffect(_shadow)
        except Exception as _e:
            logger.warning(f"shadows failed: {_e}")


        # =====================================================================
        # 3. 实例化子模块
        # =====================================================================
        self.tz_mgr = TimezoneManager(self)
        self.gpu_mgr = GpuManager(self)
        self.grub_mgr = GrubManager(self)
        self.cursor_mgr = CursorManager(self)
        self.repo_mgr = RepoManager(self)
        self.fcitx_mgr = FcitxManager(self)
        self.desktop_mgr = DesktopManager(self)
        # 桌面组件页纯代码拼装，追加到导航末尾（不动 main.ui）
        try:
            desktop_page = self.desktop_mgr.build_page()
            if self.nav_list and self.content_stack and desktop_page:
                self.nav_list.addItem("桌面组件")
                try:
                    from PySide6.QtGui import QIcon as _QIcon2
                    _dicon = _QIcon2.fromTheme("preferences-desktop")
                    if not _dicon.isNull():
                        _ditem = self.nav_list.item(self.nav_list.count() - 1)
                        if _ditem:
                            _ditem.setIcon(_dicon)
                except Exception:
                    pass
                self.content_stack.addWidget(desktop_page)
                logger.debug("desktop page appended")
        except Exception as e:
            logger.warning(f"desktop page append failed: {e}")

        # =====================================================================
        # 4. 连接中央路由与信号
        # =====================================================================
        if self.nav_list and self.content_stack:
            def _fade_to(row_index):
                """现代切换：新页 160ms 淡入（OutCubic），阴影挂在 stack 上、
                透明度挂在子页上，互不冲突，连点可打断。"""
                try:
                    from PySide6.QtCore import QPropertyAnimation, QEasingCurve
                    from PySide6.QtWidgets import QGraphicsOpacityEffect
                    stack = self.content_stack
                    # 清理上一页残留的透明度特效，避免叠加耗性能
                    try:
                        _old = stack.currentWidget()
                        if _old is not None and isinstance(_old.graphicsEffect(), QGraphicsOpacityEffect):
                            _old.setGraphicsEffect(None)
                    except Exception:
                        pass
                    if self._fade_anim:
                        try:
                            self._fade_anim.stop()
                        except Exception:
                            pass
                    stack.setCurrentIndex(row_index)
                    _page = stack.widget(row_index)
                    eff = QGraphicsOpacityEffect(_page)
                    eff.setOpacity(0.0)
                    _page.setGraphicsEffect(eff)
                    anim = QPropertyAnimation(eff, b"opacity", stack)
                    anim.setDuration(160)
                    anim.setStartValue(0.0)
                    anim.setEndValue(1.0)
                    anim.setEasingCurve(QEasingCurve.OutCubic)

                    def _done():
                        try:
                            if _page.graphicsEffect() is eff:
                                _page.setGraphicsEffect(None)
                        except Exception:
                            pass
                    anim.finished.connect(_done)
                    self._fade_anim = anim
                    anim.start()
                except Exception as _e:
                    logger.warning(f"page anim failed, direct switch: {_e}")
                    try:
                        self.content_stack.setCurrentIndex(row_index)
                    except Exception:
                        pass

            def safe_page_switcher(row_index):
                logger.debug(f"nav switch -> {row_index}")
                if row_index < 0:
                    return
                total_pages = self.content_stack.count()
                if row_index >= total_pages:
                    logger.warning(f"page switch out of range: {row_index} >= {total_pages}")
                    return
                if row_index == self.content_stack.currentIndex():
                    return
                _fade_to(row_index)
                if hasattr(self, 'repo_list_widget') and self.repo_list_widget and self.repo_list_widget.isVisible():
                    self.repo_mgr.scan_and_render_system_repos()
            self.nav_list.currentRowChanged.connect(safe_page_switcher)
            logger.debug("nav routing connected (animated)")
        else:
            logger.error("nav_list or content_stack missing, routing not connected")

        # --- 绑定业务模块动作 ---
        if self.btn: self.btn.clicked.connect(self.tz_mgr.apply_timezone)
        
        if self.grub_browse_btn: self.grub_browse_btn.clicked.connect(self.grub_mgr.smart_browse_grub)
        if self.grub_refresh_btn: self.grub_refresh_btn.clicked.connect(self.grub_mgr.refresh_local_themes_combo)
        if self.grub_apply_btn: self.grub_apply_btn.clicked.connect(self.grub_mgr.dispatch_grub_apply)
        
        if self.gpu_action_btn: self.gpu_action_btn.clicked.connect(self.gpu_mgr.apply_gpu_codec_fix)
        if self.gpu_refresh_btn: self.gpu_refresh_btn.clicked.connect(self.gpu_mgr.detect_gpu_and_drivers)
        
        if self.cursor_browse_btn: self.cursor_browse_btn.clicked.connect(self.cursor_mgr.smart_browse_cursor)
        if self.cursor_apply_btn: self.cursor_apply_btn.clicked.connect(self.cursor_mgr.dispatch_cursor_apply)
        if self.cursor_theme_combo: self.cursor_theme_combo.currentIndexChanged.connect(self.cursor_mgr.update_cursor_preview)

        if self.fcitx_browse_btn: self.fcitx_browse_btn.clicked.connect(self.fcitx_mgr.smart_browse_theme)
        if self.fcitx_apply_btn: self.fcitx_apply_btn.clicked.connect(self.fcitx_mgr.dispatch_apply)
        if self.fcitx_refresh_btn: self.fcitx_refresh_btn.clicked.connect(self.fcitx_mgr.refresh_theme_combos)
        
        if self.repo_list_widget: self.repo_list_widget.itemClicked.connect(self.repo_mgr.dispatch_repo_toggle_on_click)
        if self.recommended_repo_list: self.recommended_repo_list.itemClicked.connect(self.repo_mgr.dispatch_recommended_toggle_on_click)
        if self.repo_refresh_btn: self.repo_refresh_btn.clicked.connect(self.repo_mgr.scan_and_render_system_repos)

        # =====================================================================
        # 5. 冷启动初始化渲染
        # =====================================================================
        self.tz_mgr.init_timezone_list()
        self.tz_mgr.refresh_current_timezone()
        self.grub_mgr.refresh_local_themes_combo()
        self.gpu_mgr.detect_gpu_and_drivers()
        self.cursor_mgr.refresh_cursor_themes_combo()
        self.fcitx_mgr.refresh_current_theme()
        self.fcitx_mgr.refresh_theme_combos()

        if self.nav_list: self.nav_list.setCurrentRow(0)
        self.cursor_mgr.update_cursor_preview()
        # 启动即跟随壁纸点缀色
        try:
            self.desktop_mgr.refresh_theme(False)
        except Exception as e:
            logger.warning(f"theme accent follow failed: {e}")

def _is_dark_mode(app: QApplication) -> bool:
    # 1. Qt6 styleHints
    try:
        hints = app.styleHints()
        if hasattr(hints, "colorScheme"):
            from PySide6.QtCore import Qt
            if hints.colorScheme() == Qt.ColorScheme.Dark:
                return True
    except Exception:
        pass
    # 2. GNOME gsettings
    try:
        import subprocess
        r = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"], capture_output=True, text=True, timeout=2)
        if "prefer-dark" in r.stdout:
            return True
        r2 = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"], capture_output=True, text=True, timeout=2)
        if "dark" in r2.stdout.lower():
            return True
    except Exception:
        pass
    # 3. KDE
    try:
        import subprocess
        r = subprocess.run(["kreadconfig6", "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme"], capture_output=True, text=True, timeout=2)
        if "dark" in r.stdout.lower():
            return True
    except Exception:
        pass
    # 4. palette lightness fallback
    try:
        from PySide6.QtGui import QPalette
        bg = app.palette().color(QPalette.Window)
        return bg.lightness() < 128
    except Exception:
        return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setDesktopFileName("fedora-tweak-tool.desktop")
    app.setStyle("Fusion")

    # 强制自管理调色板，避免系统浅色/深色调色板污染 QSS 导致字体不可见
    # FTT_THEME=light|dark|auto（默认 light，白底黑字；要跟系统走就设 auto）
    try:
        from PySide6.QtGui import QPalette, QColor
        _theme_pref = os.environ.get("FTT_THEME", "light").lower()
        if _theme_pref == "dark":
            is_dark = True
        elif _theme_pref == "auto":
            is_dark = _is_dark_mode(app)
        else:
            is_dark = False
        palette = QPalette()
        if is_dark:
            palette.setColor(QPalette.Window, QColor("#232326"))
            palette.setColor(QPalette.WindowText, QColor("#e5e7eb"))
            palette.setColor(QPalette.Base, QColor("#36363a"))
            palette.setColor(QPalette.Text, QColor("#f3f4f6"))
            palette.setColor(QPalette.Button, QColor("#3a3a3e"))
            palette.setColor(QPalette.ButtonText, QColor("#e5e7eb"))
        else:
            palette.setColor(QPalette.Window, QColor("#f0f2f5"))
            palette.setColor(QPalette.WindowText, QColor("#1f2937"))
            palette.setColor(QPalette.Base, QColor("#ffffff"))
            palette.setColor(QPalette.Text, QColor("#111827"))
            palette.setColor(QPalette.Button, QColor("#ffffff"))
            palette.setColor(QPalette.ButtonText, QColor("#111827"))
        app.setPalette(palette)
        logger.debug(f"palette forced to {'dark' if is_dark else 'light'} (is_dark={is_dark})")
    except Exception as _e:
        is_dark = False
        try:
            is_dark = _is_dark_mode(app)
        except Exception:
            pass
        logger.warning(f"palette setup failed: {_e}")

    # 根据深浅自动选择 QSS，兜底互备
    qss_candidates = ("style-dark.qss", "style.qss") if is_dark else ("style.qss", "style-dark.qss")
    for _qss_name in qss_candidates:
        for _base in (os.path.dirname(os.path.abspath(__file__)), "/usr/share/fedora-tweak-tool", os.getcwd()):
            _qss_path = os.path.join(_base, _qss_name)
            if os.path.exists(_qss_path):
                try:
                    with open(_qss_path, "r", encoding="utf-8") as _f:
                        app.setStyleSheet(_f.read())
                    logger.debug(f"QSS loaded: {_qss_path} (dark={is_dark})")
                except Exception as _e:
                    logger.warning(f"QSS load failed {_qss_path}: {_e}")
                break
        else:
            continue
        break
    tweak_app = FedoraTweakApp()
    tweak_app.window.show()
    sys.exit(app.exec())