#!/usr/bin/python3
"""QML 样例预览：A FluentWinUI3 / B Adwaita自定义 / C Material深色。
用法：python3 preview_qml.py --all（三个窗口并排对比）
      python3 preview_qml.py --only A|B|C
看完直接关窗口；不影响主程序。"""
import os
import sys
import argparse

from PySide6.QtCore import QObject, Signal, Property, Slot

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

SAMPLES = {
    "A": ("qml_samples/SampleA.qml", "FluentWinUI3"),
    "B": ("qml_samples/SampleB.qml", "Basic"),
    "C": ("qml_samples/SampleC.qml", "Material"),
}

GEOMETRY = {"A": (20, 60), "B": (560, 60), "C": (1100, 60)}


def make_light_palette():
    from PySide6.QtGui import QPalette, QColor
    pal = QPalette()
    for role, hexv in [(QPalette.Window, "#f0f2f5"), (QPalette.WindowText, "#1f2937"),
                       (QPalette.Base, "#ffffff"), (QPalette.Text, "#111827"),
                       (QPalette.Button, "#ffffff"), (QPalette.ButtonText, "#111827"),
                       (QPalette.Highlight, "#1c71d8"), (QPalette.HighlightedText, "#ffffff"),
                       (QPalette.Accent, "#005fb8"),
                       (QPalette.AlternateBase, "#f7f8fa")]:
        pal.setColor(role, QColor(hexv))
    return pal


class SampleBridge(QObject):
    statusChanged = Signal()
    filePathChanged = Signal()

    def __init__(self):
        super().__init__()
        self._status = "当前正在使用的主题：Graphite"
        self._themes = ["Graphite Dark", "Vimix White", "Tela Ochre"]
        self._current = 0
        self._path = ""

    def getStatus(self):
        return self._status

    def setStatus(self, v):
        if self._status != v:
            self._status = v
            self.statusChanged.emit()

    statusText = Property(str, getStatus, setStatus, notify=statusChanged)

    def getThemes(self):
        return self._themes

    themeList = Property(list, getThemes, constant=True)

    def getCurrent(self):
        return self._current

    currentTheme = Property(int, getCurrent, constant=True)

    def getPath(self):
        return self._path

    def setPath(self, v):
        if self._path != v:
            self._path = v
            self.filePathChanged.emit()

    filePath = Property(str, getPath, setPath, notify=filePathChanged)

    @Slot()
    def refresh(self):
        self.setStatus(f"刷新完成：发现 {len(self._themes)} 个本地主题")

    @Slot()
    def applyTheme(self):
        self.setStatus(f"已应用主题：{self._themes[self._current]}（样例演示，未真实写入）")

    @Slot()
    def browse(self):
        self.setPath(os.path.expanduser("~/Downloads/graphite.tar.gz"))


def run_one(key):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtCore import QUrl

    qml_file, style = SAMPLES[key]
    QQuickStyle.setStyle(style)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(make_light_palette())

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", SampleBridge())
    engine.load(QUrl.fromLocalFile(os.path.join(BASE, qml_file)))
    if not engine.rootObjects():
        print(f"[{key}] QML 加载失败", file=sys.stderr)
        return 1
    win = engine.rootObjects()[0]
    try:
        x, y = GEOMETRY[key]
        win.setPosition(x, y)
    except Exception:
        pass
    return app.exec()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["A", "B", "C"], default=None)
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if args.only:
        sys.exit(run_one(args.only))
    # 默认与 --all：三个独立进程并排打开（QML 内置风格是进程全局的，必须分进程）
    import subprocess
    procs = []
    for k in ["A", "B", "C"]:
        procs.append(subprocess.Popen([sys.executable, __file__, "--only", k]))
    for p in procs:
        p.wait()


if __name__ == "__main__":
    main()
