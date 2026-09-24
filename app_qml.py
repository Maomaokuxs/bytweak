#!/usr/bin/python3
"""Fedora Tweak Tool · QML 版主程序：FluentWinUI3 + 7 桥接，后端全部复用 *_core。
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
    app.setDesktopFileName("fedora-tweak-tool-qml.desktop")
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
    logger.info("QML 主程序启动：7 页桥接就绪")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
