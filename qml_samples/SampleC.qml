import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

// 样例 C：Material 深色内置风格（展示深色 + 零自定义）
ApplicationWindow {
    id: root
    visible: true
    width: 520
    height: 640
    title: "QML 样例 C · Material 深色"
    Material.theme: Material.Dark
    Material.accent: Material.Teal

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
                    spacing: 12
                    Label { text: "GRUB 配置"; font.pixelSize: 22; font.bold: true }

                    GroupBox {
                        title: "当前状态"
                        Layout.fillWidth: true
                        Label { text: bridge.statusText; wrapMode: Text.WordWrap; anchors.fill: parent }
                    }
                    GroupBox {
                        title: "安装外部主题包"
                        Layout.fillWidth: true
                        RowLayout {
                            anchors.fill: parent
                            Label { text: "主题文件" }
                            TextField { Layout.fillWidth: true; placeholderText: "未选择，可直接切换本地主题"; text: bridge.filePath }
                            Button { text: "浏览…"; flat: true; onClicked: bridge.browse() }
                        }
                    }
                    GroupBox {
                        title: "本地已安装主题"
                        Layout.fillWidth: true
                        ColumnLayout {
                            anchors.fill: parent
                            ComboBox { Layout.fillWidth: true; model: bridge.themeList; currentIndex: bridge.currentTheme }
                            Switch { text: "安装后自动更新 GRUB 配置"; checked: true }
                        }
                    }
                    Item { Layout.fillHeight: true }
                    RowLayout {
                        Layout.alignment: Qt.AlignRight
                        Button { text: "刷新"; flat: true; onClicked: bridge.refresh() }
                        Button { text: "写入并更新 GRUB"; highlighted: true; onClicked: bridge.applyTheme() }
                    }
                }
            }
            Label { text: "（其他设置页）"; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        }
    }
}
