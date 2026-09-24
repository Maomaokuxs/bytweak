#!/usr/bin/python3
"""样式样例预览器：同一设置页 x 4 种设计语言，顶部下拉实时切换。
A 现行现代版 / B GNOME Adwaita / C Win11 Fluent / D KDE Breeze
运行：python3 preview_styles.py（看完直接关窗口；不影响主程序）"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QListWidget, QListWidgetItem,
                               QStackedWidget, QGroupBox, QFrame, QLabel,
                               QLineEdit, QComboBox, QPushButton, QCheckBox)
from PySide6.QtGui import QIcon

# ---------------------------------------------------------------- A：现行现代版
QSS_A = """
QMainWindow { background: #eef0f4; font-size: 13px; }
QWidget#centralwidget { background: #eef0f4; }
QWidget#header_bar { background: #ffffff; border: 1px solid #e3e6eb; border-radius: 14px; }
QLabel#app_title_lbl { font-size: 15px; font-weight: 700; color: #111827; }
QLabel#app_sub_lbl { font-size: 11px; color: #6b7280; }
QListWidget#nav_list { background: #ffffff; border: 1px solid #e3e6eb; border-radius: 14px; padding: 8px; outline: 0; }
QListWidget#nav_list::item { padding: 12px 14px; margin: 2px 0px; border-radius: 10px; color: #374151; }
QListWidget#nav_list::item:selected { background: #3584e4; color: #ffffff; font-weight: 600; }
QStackedWidget#content_stack { background: #ffffff; border: 1px solid #e3e6eb; border-radius: 14px; }
QLabel#page_title_lbl { font-size: 20px; font-weight: 800; color: #111827; }
QGroupBox { background: #ffffff; border: 1px solid #e7eaef; border-radius: 14px; margin-top: 10px; padding-top: 14px; font-weight: 600; color: #111827; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 14px; padding: 0 6px; color: #4b5563; }
QFrame[frameShape="5"] { background: #ffffff; border: 1px solid #e7eaef; border-radius: 14px; }
QPushButton { background: #3584e4; color: #ffffff; border: none; border-radius: 9px; padding: 8px 20px; font-weight: 600; }
QPushButton#refresh_btn { background: #f3f5f8; color: #374151; border: 1px solid #dfe3e9; font-weight: 500; }
QLineEdit, QComboBox { background: #f7f8fa; border: 1px solid #dfe3e9; border-radius: 9px; padding: 8px 12px; }
QListWidget#sample_list { background: #f7f8fa; border: 1px solid #e3e6eb; border-radius: 10px; padding: 4px; outline: 0; }
QListWidget#sample_list::item { padding: 9px 10px; border-radius: 7px; margin: 1px 0; }
"""

# ---------------------------------------------------------------- B：GNOME Adwaita
QSS_B = """
QMainWindow { background: #f6f5f4; font-size: 13px; font-family: "Cantarell", sans-serif; }
QWidget#centralwidget { background: #f6f5f4; }
QWidget#header_bar { background: #ffffff; border: 1px solid #e4e2e0; border-radius: 12px; }
QLabel#app_title_lbl { font-size: 15px; font-weight: 700; color: #2e3436; }
QLabel#app_sub_lbl { font-size: 11px; color: #9a9996; }
QListWidget#nav_list { background: #ffffff; border: 1px solid #e4e2e0; border-radius: 12px; padding: 6px; outline: 0; }
QListWidget#nav_list::item { padding: 10px 12px; margin: 1px 0px; border-radius: 8px; color: #3d3846; }
QListWidget#nav_list::item:selected { background: #1c71d8; color: #ffffff; font-weight: 700; }
QStackedWidget#content_stack { background: #ffffff; border: 1px solid #e4e2e0; border-radius: 12px; }
QLabel#page_title_lbl { font-size: 22px; font-weight: 800; color: #2e3436; }
QGroupBox { background: transparent; border: none; margin-top: 14px; font-weight: 700; font-size: 14px; color: #2e3436; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 2px; padding: 0 0px; }
QFrame[frameShape="5"] { background: #ffffff; border: 1px solid #e4e2e0; border-radius: 12px; }
QPushButton { background: #1c71d8; color: #ffffff; border: none; border-radius: 17px; padding: 8px 24px; font-weight: 700; }
QPushButton:hover { background: #2a7cd8; }
QPushButton#refresh_btn { background: #e9e7e4; color: #2e3436; border: none; font-weight: 600; }
QPushButton#refresh_btn:hover { background: #dedbd7; }
QLineEdit, QComboBox { background: #ffffff; border: 1px solid #c9c6c2; border-radius: 8px; padding: 8px 12px; }
QLineEdit:focus, QComboBox:focus { border: 2px solid #1c71d8; }
QListWidget#sample_list { background: #ffffff; border: 1px solid #e4e2e0; border-radius: 12px; padding: 2px; outline: 0; }
QListWidget#sample_list::item { padding: 12px 12px; border-radius: 0px; margin: 0px; border-bottom: 1px solid #f0efee; }
"""

# ---------------------------------------------------------------- C：Win11 Fluent
QSS_C = """
QMainWindow { background: #f3f3f3; font-size: 13px; font-family: "Segoe UI Variable", "Cantarell", sans-serif; }
QWidget#centralwidget { background: #f3f3f3; }
QWidget#header_bar { background: #ffffff; border: 1px solid #e5e5e5; border-bottom-width: 1px; border-radius: 8px; }
QLabel#app_title_lbl { font-size: 14px; font-weight: 600; color: #1b1a19; }
QLabel#app_sub_lbl { font-size: 11px; color: #605e5c; }
QListWidget#nav_list { background: transparent; border: none; padding: 4px; outline: 0; }
QListWidget#nav_list::item { padding: 9px 12px; margin: 1px 0px; border-radius: 6px; color: #323130; border: 1px solid transparent; }
QListWidget#nav_list::item:hover { background: #ffffff; border: 1px solid #e5e5e5; }
QListWidget#nav_list::item:selected { background: #ffffff; border: 1px solid #e5e5e5; border-left: 3px solid #005fb8; font-weight: 600; color: #1b1a19; }
QStackedWidget#content_stack { background: #ffffff; border: 1px solid #e5e5e5; border-radius: 8px; }
QLabel#page_title_lbl { font-size: 20px; font-weight: 600; color: #1b1a19; }
QGroupBox { background: #fafafa; border: 1px solid #e5e5e5; border-radius: 6px; margin-top: 8px; padding-top: 12px; font-weight: 600; color: #1b1a19; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 12px; padding: 0 4px; color: #323130; }
QFrame[frameShape="5"] { background: #fafafa; border: 1px solid #e5e5e5; border-radius: 6px; }
QPushButton { background: #005fb8; color: #ffffff; border: 1px solid #005fb8; border-radius: 6px; padding: 7px 18px; font-weight: 600; }
QPushButton:hover { background: #1a6fc0; }
QPushButton#refresh_btn { background: #ffffff; color: #1b1a19; border: 1px solid #c7c7c7; font-weight: 400; }
QPushButton#refresh_btn:hover { background: #f5f5f5; }
QLineEdit, QComboBox { background: #ffffff; border: 1px solid #8a8886; border-bottom: 2px solid #8a8886; border-radius: 6px 6px 0px 0px; padding: 7px 12px; }
QLineEdit:focus, QComboBox:focus { border-bottom: 2px solid #005fb8; }
QListWidget#sample_list { background: #ffffff; border: 1px solid #e5e5e5; border-radius: 6px; padding: 2px; outline: 0; }
QListWidget#sample_list::item { padding: 8px 10px; border-radius: 4px; margin: 0px; }
QListWidget#sample_list::item:hover { background: #f5f5f5; }
"""

# ---------------------------------------------------------------- D：KDE Breeze
QSS_D = """
QMainWindow { background: #eff0f1; font-size: 13px; }
QWidget#centralwidget { background: #eff0f1; }
QWidget#header_bar { background: #ffffff; border: 1px solid #bdc3c7; border-radius: 6px; }
QLabel#app_title_lbl { font-size: 14px; font-weight: 700; color: #232629; }
QLabel#app_sub_lbl { font-size: 11px; color: #7f8c8d; }
QListWidget#nav_list { background: #ffffff; border: 1px solid #bdc3c7; border-radius: 6px; padding: 4px; outline: 0; }
QListWidget#nav_list::item { padding: 8px 10px; margin: 1px 0px; border-radius: 4px; color: #232629; }
QListWidget#nav_list::item:hover { background: #e3e9ed; }
QListWidget#nav_list::item:selected { background: #3daee9; color: #ffffff; font-weight: 600; }
QStackedWidget#content_stack { background: #ffffff; border: 1px solid #bdc3c7; border-radius: 6px; }
QLabel#page_title_lbl { font-size: 18px; font-weight: 700; color: #232629; }
QGroupBox { background: #ffffff; border: 1px solid #bdc3c7; border-radius: 6px; margin-top: 8px; padding-top: 12px; font-weight: 600; color: #232629; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 0 4px; }
QFrame[frameShape="5"] { background: #ffffff; border: 1px solid #bdc3c7; border-radius: 6px; }
QPushButton { background: #3daee9; color: #ffffff; border: 1px solid #2a9ed8; border-radius: 4px; padding: 7px 18px; font-weight: 600; }
QPushButton:hover { background: #51b8ec; }
QPushButton#refresh_btn { background: #fcfcfc; color: #232629; border: 1px solid #bdc3c7; font-weight: 400; }
QPushButton#refresh_btn:hover { background: #e3e9ed; }
QLineEdit, QComboBox { background: #ffffff; border: 1px solid #bdc3c7; border-radius: 4px; padding: 7px 10px; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #3daee9; }
QListWidget#sample_list { background: #ffffff; border: 1px solid #bdc3c7; border-radius: 4px; padding: 2px; outline: 0; alternate-background-color: #f5f6f7; }
QListWidget#sample_list::item { padding: 7px 8px; border-radius: 3px; margin: 0px; }
"""

STYLES = [
    ("A 现行现代版（圆角卡片 + 蓝）", QSS_A),
    ("B GNOME Adwaita（胶囊按钮 + 无框分组）", QSS_B),
    ("C Win11 Fluent（小圆角 + 左侧指示条）", QSS_C),
    ("D KDE Breeze（紧凑 + 天空蓝）", QSS_D),
]


def build_sample_page():
    """与主程序同构的代表页：标题 + 状态卡 + 表单卡 + 列表卡 + 底栏。"""
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(12, 12, 12, 12)
    lay.setSpacing(12)

    title = QLabel("GRUB 配置")
    title.setObjectName("page_title_lbl")
    lay.addWidget(title)

    status = QFrame()
    status.setFrameShape(QFrame.StyledPanel)
    status.setFrameShadow(QFrame.Raised)
    sl = QHBoxLayout(status)
    sl.addWidget(QLabel("当前正在使用的主题：Graphite"))
    lay.addWidget(status)

    form = QGroupBox("安装外部主题包")
    fl = QHBoxLayout(form)
    fl.setSpacing(12)
    lab = QLabel("主题文件")
    lab.setMinimumWidth(70)
    fl.addWidget(lab)
    le = QLineEdit()
    le.setPlaceholderText("未选择，可直接切换本地主题")
    fl.addWidget(le, 1)
    fl.addWidget(QPushButton("浏览…"))
    lay.addWidget(form)

    lst_box = QGroupBox("本地已安装主题")
    ll = QVBoxLayout(lst_box)
    lst = QListWidget()
    lst.setObjectName("sample_list")
    lst.setAlternatingRowColors(True)
    for name, rid, on in [("Graphite Dark\n[graphite]", "graphite", True), ("Vimix White\n[vimix]", "vimix", False),
                          ("Tela Ochre\n[tela]", "tela", True), ("Stylish Black\n[stylish]", "stylish", False)]:
        it = QListWidgetItem(name)
        it.setData(Qt.UserRole, rid)
        it.setCheckState(Qt.Checked if on else Qt.Unchecked)
        lst.addItem(it)
    ll.addWidget(lst)
    lay.addWidget(lst_box, 1)

    bottom = QWidget()
    bl = QHBoxLayout(bottom)
    bl.setContentsMargins(0, 0, 0, 0)
    bl.setSpacing(8)
    bl.addStretch(1)
    rb = QPushButton("刷新")
    rb.setObjectName("refresh_btn")
    rb.setMinimumHeight(34)
    bl.addWidget(rb)
    ab = QPushButton("写入并更新 GRUB")
    ab.setMinimumSize(150, 34)
    bl.addWidget(ab)
    lay.addWidget(bottom)
    return page


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    from PySide6.QtGui import QPalette, QColor
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor("#f0f2f5"))
    pal.setColor(QPalette.WindowText, QColor("#1f2937"))
    pal.setColor(QPalette.Base, QColor("#ffffff"))
    pal.setColor(QPalette.Text, QColor("#111827"))
    pal.setColor(QPalette.Button, QColor("#ffffff"))
    pal.setColor(QPalette.ButtonText, QColor("#111827"))
    pal.setColor(QPalette.Highlight, QColor("#3584e4"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.AlternateBase, QColor("#f7f8fa"))
    app.setPalette(pal)
    win = QMainWindow()
    win.setWindowTitle("样式样例预览（挑选后关闭即可）")
    win.resize(980, 680)
    central = QWidget()
    central.setObjectName("centralwidget")
    win.setCentralWidget(central)
    root = QVBoxLayout(central)
    root.setContentsMargins(12, 12, 12, 12)
    root.setSpacing(12)

    # 切换条
    switch_row = QHBoxLayout()
    switch_row.addWidget(QLabel("样式方案："))
    combo = QComboBox()
    for name, _ in STYLES:
        combo.addItem(name)
    combo.setMinimumWidth(340)
    switch_row.addWidget(combo)
    switch_row.addStretch(1)
    hint = QLabel("同一页面 · 顶部下拉实时切换对比")
    hint.setEnabled(False)
    switch_row.addWidget(hint)
    root.addLayout(switch_row)

    # 顶栏
    header = QWidget()
    header.setObjectName("header_bar")
    header.setMaximumHeight(52)
    hl = QHBoxLayout(header)
    icon = QLabel("●")
    icon.setObjectName("app_icon_lbl")
    icon.setMinimumWidth(28)
    hl.addWidget(icon)
    tbox = QVBoxLayout()
    tbox.setSpacing(0)
    t1 = QLabel("Fedora Tweak Tool")
    t1.setObjectName("app_title_lbl")
    t2 = QLabel("系统微调 · 简洁现代")
    t2.setObjectName("app_sub_lbl")
    tbox.addWidget(t1)
    tbox.addWidget(t2)
    hl.addLayout(tbox)
    hl.addStretch(1)
    hl.addWidget(QLabel("v1.1.5"))
    root.addWidget(header)

    # 导航 + 内容
    mid = QHBoxLayout()
    mid.setSpacing(12)
    nav = QListWidget()
    nav.setObjectName("nav_list")
    nav.setMinimumWidth(180)
    nav.setMaximumWidth(260)
    nav.setIconSize(QSize(20, 20))
    for t, ic in [("时区设置", "preferences-system-time"), ("GRUB 配置", "drive-harddisk"),
                  ("显卡与硬件加速", "video-display"), ("鼠标指针样式", "input-mouse"),
                  ("软件源管理", "system-software-install"), ("Fcitx 输入法", "input-keyboard"),
                  ("桌面组件", "preferences-desktop")]:
        it = QListWidgetItem(t)
        icon = QIcon.fromTheme(ic)
        if not icon.isNull():
            it.setIcon(icon)
        nav.addItem(it)
    nav.setCurrentRow(1)
    stack = QStackedWidget()
    stack.setObjectName("content_stack")
    stack.addWidget(build_sample_page())
    mid.addWidget(nav, 1)
    mid.addWidget(stack, 4)
    root.addLayout(mid, 1)

    def apply_style(i):
        app.setStyleSheet(STYLES[i][1])
        win.setWindowTitle(f"样式样例预览 - {STYLES[i][0]}")

    combo.currentIndexChanged.connect(apply_style)
    apply_style(0)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
