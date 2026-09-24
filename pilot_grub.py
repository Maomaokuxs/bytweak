#!/usr/bin/python3
"""GRUB QML 单页试点：FluentWinUI3 + GrubBridge（后端复用 grub_core）。
运行：python3 pilot_grub.py（看完直接关窗口；不影响主程序）"""
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
    try:
        from PySide6.QtCore import Qt as _Qt
        app.styleHints().setColorScheme(_Qt.ColorScheme.Light)
    except Exception:
        pass
    app.setStyle("Fusion")
    pal = QPalette()
    for role, hexv in [(QPalette.Window, "#f0f2f5"), (QPalette.WindowText, "#1f2937"),
                       (QPalette.Base, "#ffffff"), (QPalette.Text, "#111827"),
                       (QPalette.Button, "#ffffff"), (QPalette.ButtonText, "#111827"),
                       (QPalette.Highlight, "#1c71d8"), (QPalette.HighlightedText, "#ffffff"),
                       (QPalette.Accent, "#005fb8"),
                       (QPalette.AlternateBase, "#f7f8fa")]:
        pal.setColor(role, QColor(hexv))
    app.setPalette(pal)

    from modules.grub_bridge import GrubBridge
    from modules.theme_bridge import ThemeBridge
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("theme", ThemeBridge(dark=False))
    engine.rootContext().setContextProperty("bridge", GrubBridge())
    engine.load(QUrl.fromLocalFile(os.path.join(BASE, "qml", "GrubPilot.qml")))
    if not engine.rootObjects():
        print("QML 加载失败", file=sys.stderr)
        return 1
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
