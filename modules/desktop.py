#!/usr/bin/python3
# DesktopManager — Widgets 薄层：桌面组件页拼装 + 状态显示，逻辑全部走 desktop_core。
import os

try:
    from .utils import logger
except Exception:
    import logging
    logger = logging.getLogger("bytweak")

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFrame,
                               QRadioButton, QPushButton, QLabel, QCheckBox,
                               QButtonGroup, QMessageBox)

from . import desktop_core


def apply_hellwal_accent(app):
    """把 hellwal 点缀色追加入全局 QSS（导航选中/按钮/勾选），不动原文件。"""
    try:
        pal = desktop_core.read_hellwal_palette()
        extra = f"""
QListWidget::item:selected {{ background: {pal['ACCENT']}; color: {pal['BG']}; border-radius: 6px; }}
QPushButton {{ background: {pal['ACCENT']}; color: {pal['BG']}; border: none; border-radius: 8px; padding: 7px 14px; font-weight: bold; }}
QPushButton:hover {{ background: {pal['FG']}; }}
QPushButton:disabled {{ background: {pal['MUTED']}; color: {pal['BG']}; }}
QCheckBox::indicator:checked {{ background: {pal['ACCENT']}; border: 1px solid {pal['FG']}; }}
QRadioButton::indicator:checked {{ background: {pal['ACCENT']}; border: 2px solid {pal['FG']}; }}
QGroupBox {{ border: 1px solid {pal['MUTED']}; border-radius: 8px; margin-top: 12px; font-weight: bold; color: {pal['FG']}; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
"""
        app.setStyleSheet(app.styleSheet() + extra)
        try:
            from PySide6.QtGui import QColor, QPalette
            acc = QColor(pal['ACCENT'])
            lum = 0.299 * acc.red() + 0.587 * acc.green() + 0.114 * acc.blue()
            fg = QColor(pal['BG']) if lum < 150 else QColor("#111827")
            qpal = app.palette()
            qpal.setColor(QPalette.Highlight, acc)
            qpal.setColor(QPalette.HighlightedText, fg)
            app.setPalette(qpal)
        except Exception as e:
            logger.warning(f"highlight palette failed: {e}")
        logger.debug(f"hellwal accent applied: {pal['ACCENT']}")
        return pal
    except Exception as e:
        logger.warning(f"accent apply failed: {e}")
        return None


class DesktopManager:
    def __init__(self, app):
        self.app = app
        self.page = None
        self.notif_group = {}
        self.bar_group = {}
        self.status_lbl = None
        self.persist_check = None

    class _Row(QFrame):
        """整行可点面板：点任意处选中右侧 radio。"""
        def __init__(self, radio, parent=None):
            super().__init__(parent)
            self._radio = radio
            self.setFrameShape(QFrame.StyledPanel)
            self.setFrameShadow(QFrame.Raised)

        def mousePressEvent(self, event):
            self._radio.setChecked(True)
            super().mousePressEvent(event)

    @staticmethod
    def _section(page_layout, text):
        lbl = QLabel(text.upper())
        lbl.setObjectName("desktop_section_lbl")
        page_layout.addWidget(lbl)

    def _option_row(self, title, desc):
        """返回 (行容器, radio)：标题+描述在左，单选在右，整行可点。"""
        from PySide6.QtWidgets import QVBoxLayout
        rb = QRadioButton()
        rb.setStyleSheet(
            "QRadioButton::indicator { width: 18px; height: 18px; "
            "border-radius: 9px; border: 2px solid gray; background: transparent; }"
            "QRadioButton::indicator:checked { border: 2px solid palette(highlight); "
            "background: palette(highlight); }")
        row = self._Row(rb)
        lay = QHBoxLayout(row)
        lay.setContentsMargins(14, 10, 14, 10)
        txt = QVBoxLayout()
        txt.setSpacing(1)
        t = QLabel(title)
        t.setStyleSheet("font-size: 14px;")
        d = QLabel(desc)
        d.setStyleSheet("font-size: 12px; color: gray;")
        txt.addWidget(t)
        txt.addWidget(d)
        lay.addLayout(txt, 1)
        lay.addWidget(rb)
        return row, rb

    @staticmethod
    def _group_box(rows):
        from PySide6.QtWidgets import QFrame
        box = QFrame()
        box.setFrameShape(QFrame.StyledPanel)
        box.setFrameShadow(QFrame.Raised)
        lay = QVBoxLayout(box)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(0)
        for i, row in enumerate(rows):
            lay.addWidget(row)
            if i < len(rows) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setFrameShadow(QFrame.Sunken)
                lay.addWidget(sep)
        return box

    def build_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        _title = QLabel("桌面组件")
        _title.setObjectName("page_title_lbl")
        layout.addWidget(_title)

        self._section(layout, "通知管理器")
        self.notif_group = {}
        self._notif_btn_group = QButtonGroup(page)
        _nrows = []
        for key, title, desc in desktop_core.NOTIF_OPTIONS:
            row, btn = self._option_row(title, desc)
            self._notif_btn_group.addButton(btn)
            self.notif_group[key] = btn
            _nrows.append(row)
        layout.addWidget(self._group_box(_nrows))

        self._section(layout, "顶栏")
        self.bar_group = {}
        self._bar_btn_group = QButtonGroup(page)
        _brows = []
        for key, title, desc in desktop_core.BAR_OPTIONS:
            row, btn = self._option_row(title, desc)
            self._bar_btn_group.addButton(btn)
            self.bar_group[key] = btn
            _brows.append(row)
        layout.addWidget(self._group_box(_brows))

        self.status_lbl = QLabel("就绪")
        self.status_lbl.setObjectName("desktop_status_lbl")
        self.status_lbl.setWordWrap(True)
        layout.addWidget(self.status_lbl)
        opt_row = QHBoxLayout()
        opt_row.setSpacing(8)
        self.persist_check = QCheckBox("同步写入 niri 自启")
        self.persist_check.setChecked(True)
        opt_row.addWidget(self.persist_check)
        opt_row.addStretch(1)
        refresh_btn = QPushButton("刷新状态")
        refresh_btn.setObjectName("desktop_refresh_btn")
        refresh_btn.setMinimumHeight(32)
        refresh_btn.clicked.connect(self.refresh_state)
        opt_row.addWidget(refresh_btn)
        theme_btn = QPushButton("跟随壁纸配色")
        theme_btn.setObjectName("desktop_theme_btn")
        theme_btn.setMinimumHeight(32)
        theme_btn.clicked.connect(lambda: self.refresh_theme(True))
        opt_row.addWidget(theme_btn)
        layout.addLayout(opt_row)
        layout.addStretch(1)
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)
        bottom_row.addStretch(1)
        self.apply_all_btn = QPushButton("应用切换")
        self.apply_all_btn.setMinimumSize(120, 32)
        self.apply_all_btn.clicked.connect(self.dispatch_apply_all)
        bottom_row.addWidget(self.apply_all_btn)
        layout.addLayout(bottom_row)

        self.page = page
        self.refresh_state()
        return page

    def say(self, msg):
        logger.debug(msg)
        if self.status_lbl:
            self.status_lbl.setText(msg)

    def refresh_state(self):
        nm = desktop_core.detect_notif_manager()
        bar = desktop_core.detect_bar()
        for k, rb in self.notif_group.items():
            rb.setChecked(k == nm)
        for k, rb in self.bar_group.items():
            rb.setChecked(k == bar)
        self.say(f"当前：通知[{nm}] 顶栏[{bar}]")
        return nm, bar

    def refresh_theme(self, verbose=False):
        try:
            from PySide6.QtWidgets import QApplication
            pal = apply_hellwal_accent(QApplication.instance())
        except Exception as e:
            self.say(f"配色跟随失败：{e}")
            return
        if verbose and pal:
            self.say(f"已跟随壁纸配色：点缀 {pal['ACCENT']}")

    def dispatch_notif_switch(self):
        target = next((k for k, rb in self.notif_group.items() if rb.isChecked()), None)
        if not target:
            self.say("先选一个通知管理器")
            return
        self.say(desktop_core.switch_notif(target))
        self.refresh_state()

    def dispatch_bar_switch(self):
        target = next((k for k, rb in self.bar_group.items() if rb.isChecked()), None)
        if not target:
            self.say("先选一个顶栏")
            return
        self.say(desktop_core.switch_bar(target))
        if self.persist_check and self.persist_check.isChecked():
            self.say(self.status_lbl.text() + "；" + desktop_core.sync_niri_autostart(target))
        self.refresh_state()

    def dispatch_apply_all(self):
        """右下一键：先通知后顶栏，两组一起应用。"""
        self.dispatch_notif_switch()
        self.dispatch_bar_switch()
