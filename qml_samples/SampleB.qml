import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 样例 B：自定义 Adwaita 风（Basic 基底 + 全手写：胶囊按钮 / 无框分组 / 分隔线列表）
ApplicationWindow {
    id: root
    visible: true
    width: 520
    height: 640
    title: "QML 样例 B · Adwaita 自定义"
    color: "#f6f5f4"

    property color accent: "#1c71d8"
    property color cardBorder: "#e4e2e0"

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        ListView {
            id: nav
            Layout.preferredWidth: 150
            Layout.fillHeight: true
            model: ["时区设置", "GRUB 配置", "显卡加速", "鼠标样式", "软件源管理", "Fcitx 输入法", "桌面组件"]
            currentIndex: 1
            delegate: ItemDelegate {
                width: nav.width
                text: modelData
                highlighted: ListView.isCurrentItem
                onClicked: nav.currentIndex = index
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: nav.currentIndex === 1 ? 0 : 1

            ScrollView {
                clip: true
                ColumnLayout {
                    width: parent.width
                    spacing: 6
                    Label { text: "GRUB 配置"; font.pixelSize: 24; font.bold: true; color: "#2e3436" }
                    Label { text: bridge.statusText; color: "#5e5c64"; wrapMode: Text.WordWrap; Layout.fillWidth: true }

                    // 无框分组：粗体标题 + 间距
                    Label { text: "安装外部主题包"; font.bold: true; font.pixelSize: 14; color: "#2e3436"; topPadding: 12 }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Label { text: "主题文件"; color: "#2e3436" }
                        TextField { Layout.fillWidth: true; placeholderText: "未选择，可直接切换本地主题"; text: bridge.filePath }
                        Button {
                            id: browseBtn
                            text: "浏览…"
                            leftPadding: 20; rightPadding: 20; topPadding: 8; bottomPadding: 8
                            onClicked: bridge.browse()
                            contentItem: Text { text: browseBtn.text; color: "#2e3436"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { radius: 17; color: browseBtn.pressed ? "#d5d2ce" : (browseBtn.hovered ? "#e2dfdb" : "#e9e7e4") }
                        }
                    }
                    Label { text: "本地已安装主题"; font.bold: true; font.pixelSize: 14; color: "#2e3436"; topPadding: 12 }
                    // 盒装列表：圆角外框 + 行分隔线
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: col.height + 4
                        color: "#ffffff"
                        border.color: root.cardBorder
                        radius: 12
                        ColumnLayout {
                            id: col
                            width: parent.width
                            spacing: 0
                            Repeater {
                                model: bridge.themeList
                                delegate: Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 44
                                    color: "transparent"
                                    Label { anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 12; text: modelData; color: "#2e3436" }
                                    Rectangle { anchors.bottom: parent.bottom; anchors.left: parent.left; anchors.right: parent.right; anchors.leftMargin: 12; height: 1; color: index === 2 ? "transparent" : "#f0efee"; visible: index !== 2 }
                                }
                            }
                        }
                    }
                    Item { Layout.fillHeight: true }
                    RowLayout {
                        Layout.alignment: Qt.AlignRight
                        spacing: 8
                        Button {
                            id: refreshBtn
                            text: "刷新"
                            leftPadding: 20; rightPadding: 20; topPadding: 8; bottomPadding: 8
                            onClicked: bridge.refresh()
                            contentItem: Text { text: refreshBtn.text; color: "#2e3436"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { radius: 17; color: refreshBtn.pressed ? "#d5d2ce" : (refreshBtn.hovered ? "#e2dfdb" : "#e9e7e4") }
                        }
                        Button {
                            id: applyBtn
                            text: "写入并更新 GRUB"
                            leftPadding: 24; rightPadding: 24; topPadding: 8; bottomPadding: 8
                            onClicked: bridge.applyTheme()
                            contentItem: Text { text: applyBtn.text; color: "#ffffff"; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { radius: 17; color: applyBtn.pressed ? "#155fa0" : (applyBtn.hovered ? "#2a7cd8" : "#1c71d8") }
                        }
                    }
                }
            }
            Label { text: "（其他设置页）"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        }
    }
}
