#!/usr/bin/python3
"""Fedora Tweak Tool · QML 版主程序：FluentWinUI3 + 14 桥接，后端全部复用 *_core。
运行：python3 app_qml.py"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)


def main():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QPalette, QColor

    QQuickStyle.setStyle("FluentWinUI3")
    app = QApplication(sys.argv)
    # 点击输入框之外清除焦点：搜索框失焦、高亮消失、光标停止闪烁
    # （QML MouseArea 会被 ScrollView 的 Flickable 挡住，故用全局事件过滤器）
    from PySide6.QtCore import QObject as _QObject, QEvent as _QEvent, QPointF as _QPointF
    class _FocusClearFilter(_QObject):
        def eventFilter(self, watched, event):
            if event.type() == _QEvent.Type.MouseButtonPress:
                try:
                    win = app.activeWindow()
                    f = win.activeFocusItem() if win is not None else None
                    if f is not None:
                        cls = f.metaObject().className()
                        if "TextField" in cls or "SearchBox" in cls:
                            pos = event.position()
                            try:
                                top = f.mapToScene(_QPointF(0, 0))
                                inside = (top.x() <= pos.x() <= top.x() + f.width()
                                          and top.y() <= pos.y() <= top.y() + f.height())
                            except Exception:
                                inside = False
                            if not inside:
                                f.setFocus(False)
                except Exception:
                    pass
            return super().eventFilter(watched, event)
    _focus_filter = _FocusClearFilter(app)
    app.installEventFilter(_focus_filter)
    app.setDesktopFileName("fedora-tweak-tool-qml.desktop")
    # 强制中文 locale：经 SSH 等无 LANG 环境启动时，Qt 对话框（文件选择器）会显示英文；
    # 应用界面本身是中文写死的，这里保持一致
    try:
        from PySide6.QtCore import QLocale as _QLocale
        _QLocale.setDefault(_QLocale(_QLocale.Chinese, _QLocale.China))
    except Exception:
        pass
    # 锁定浅色方案：Fluent 素材按 styleHints 配色解析，平台主题（如深色 GTK）会误判为深色；
    # 与下方浅色调色板保持一致，否则出现深底深字
    try:
        from PySide6.QtCore import Qt as _Qt
        app.styleHints().setColorScheme(_Qt.ColorScheme.Light)
    except Exception:
        pass
    app.setStyle("Fusion")

    from modules.theme_bridge import ThemeBridge, detect_dark, LIGHT, DARK
    from modules.utils import logger
    theme = ThemeBridge(dark=detect_dark(app))
    table = DARK if theme.is_dark() else LIGHT
    base_bg = "#2b2b2b" if theme.is_dark() else "#ffffff"
    base_text = "#f3f3f3" if theme.is_dark() else "#111827"
    pal = QPalette()
    for role, hexv in [(QPalette.Window, "#1e1e21" if theme.is_dark() else "#f0f2f5"),
                       (QPalette.WindowText, base_text),
                       (QPalette.Base, base_bg),
                       (QPalette.Text, base_text),
                       (QPalette.Button, base_bg),
                       (QPalette.ButtonText, base_text),
                       (QPalette.Highlight, table["accent"]),
                       (QPalette.HighlightedText, "#ffffff"),
                       (QPalette.Accent, table["accent"]),
                       (QPalette.AlternateBase, "#333333" if theme.is_dark() else "#f7f8fa")]:
        pal.setColor(role, QColor(hexv))
    app.setPalette(pal)

    from modules.timezone_bridge import TimezoneBridge
    from modules.grub_bridge import GrubBridge
    from modules.gpu_bridge import GpuBridge
    from modules.cursor_bridge import CursorBridge, CursorPreviewProvider
    from modules.repo_bridge import RepoBridge
    from modules.fcitx_bridge import FcitxBridge
    from modules.desktop_bridge import DesktopBridge
    from modules.dashboard_bridge import DashboardBridge
    from modules.niri_bridge import NiriBridge
    from modules.service_bridge import ServiceBridge
    from modules.flatpak_bridge import FlatpakBridge
    from modules.dnf_bridge import DnfBridge
    from modules.defaultapps_bridge import DefaultAppsBridge
    from modules.kernel_bridge import KernelBridge
    from modules.hostname_bridge import HostnameBridge

    cursor_provider = CursorPreviewProvider()
    gpu_bridge = GpuBridge()
    bridges = {
        "theme": theme,
        "tz": TimezoneBridge(),
        "grub": GrubBridge(),
        "gpu": gpu_bridge,
        "cursor": CursorBridge(cursor_provider),
        "repo": RepoBridge(),
        "fcitx": FcitxBridge(),
        "desk": DesktopBridge(),
        "dash": DashboardBridge(),
        "niri": NiriBridge(),
        "svc": ServiceBridge(),
        "flat": FlatpakBridge(),
        "dnf": DnfBridge(),
        "defapp": DefaultAppsBridge(),
        "kernel": KernelBridge(),
        "hostname": HostnameBridge(),
    }

    engine = QQmlApplicationEngine()
    engine.addImageProvider("cursorimg", cursor_provider)
    for name, bridge in bridges.items():
        engine.rootContext().setContextProperty(name, bridge)
    engine.load(QUrl.fromLocalFile(os.path.join(BASE, "qml", "Main.qml")))
    if not engine.rootObjects():
        logger.error("Main.qml 加载失败")
        print("Main.qml 加载失败", file=sys.stderr)
        return 1
    logger.info("QML 主程序启动：14 页桥接就绪")
    try:
        from modules.utils import log_operation, operations_log_path
        log_operation("应用/启动", True)
        logger.info(f"操作日志：{operations_log_path()}")
    except Exception:
        pass
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
