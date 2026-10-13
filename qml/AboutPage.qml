import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 关于页：软件介绍 + 开源项目致谢（独立标签页）
ScrollView {
    id: root
    padding: 16
    ColumnLayout {
        width: root.availableWidth
        spacing: 12
        Label {
            text: "bytweak"
            font.pixelSize: 24
            font.bold: true
            color: theme.textMain
        }
        Label {
            text: "Fedora 系统调节工具，提供图形化的系统设置、软件包管理、硬件信息查看等功能。专为 Fedora 设计，基于 PySide6 构建。"
            wrapMode: Text.WordWrap
            color: theme.textMuted
            Layout.fillWidth: true
            font.pixelSize: 14
        }
        Label {
            text: "v0.1.0（开发版）"
            color: theme.textSub
            font.pixelSize: 12
        }
        Rectangle { Layout.fillWidth: true; height: 1; color: theme.cardBorder; Layout.topMargin: 8; Layout.bottomMargin: 8 }
        Label {
            text: "使用的开源项目"
            font.pixelSize: 16
            font.bold: true
            color: theme.textMain
        }
        Repeater {
            model: [
                ["PySide6", "Qt for Python，LGPL v3 — UI 框架"],
                ["FluentWinUI3", "第三方 QML 控件样式"],
                ["Python", "PSF 许可证 — 标准库 urllib、subprocess 等"],
                ["libdnf5", "GPL v2 — 软件包管理后端"],
                ["libva", "MIT — 硬件视频解码检测"],
                ["D-Bus", "GPL — 系统服务通信"],
                ["COPR API", "Fedora 构建系统公开接口"],
            ]
            delegate: ColumnLayout {
                spacing: 4
                Layout.fillWidth: true
                Layout.topMargin: 4
                Label {
                    text: "• " + modelData[0]
                    font.bold: true
                    color: theme.textMain
                    font.pixelSize: 14
                }
                Label {
                    text: "  " + modelData[1]
                    color: theme.textMuted
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
        Item { Layout.fillHeight: true }
    }
}
