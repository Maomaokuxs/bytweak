import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 桌面组件页：通知三选一 + 顶栏二选一 + 右下应用（内容滚动，底栏固定）
ColumnLayout {
    spacing: 0

    ScrollView {
        id: deskScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: deskScroll.availableWidth
            spacing: 12

                Label { text: "桌面组件"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }

                Label { text: "通知管理器".toUpperCase(); font.bold: true; renderType: Text.NativeRendering; opacity: 0.6 }
                GroupBox {
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        Repeater {
                            model: desk.notifItems
                            delegate: RadioDelegate {
                                Layout.fillWidth: true
                                text: modelData.title + "\n" + modelData.desc
                                checked: index === desk.notifIndex
                                onToggled: desk.setNotif(index)
                            }
                        }
                    }
                }

                Label { text: "顶栏".toUpperCase(); font.bold: true; renderType: Text.NativeRendering; opacity: 0.6 }
                GroupBox {
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        Repeater {
                            model: desk.barItems
                            delegate: RadioDelegate {
                                Layout.fillWidth: true
                                text: modelData.title + "\n" + modelData.desc
                                checked: index === desk.barIndex
                                onToggled: desk.setBar(index)
                            }
                        }
                    }
                }

                Label { text: desk.statusText; wrapMode: Text.WordWrap; Layout.fillWidth: true; opacity: 0.7 }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    AccentCheckBox {
                        text: "同步写入 niri 自启"
                        checked: desk.persistEnabled
                        onToggled: desk.setPersist(checked)
                    }
                    Item { Layout.fillWidth: true }
                    AppButton { text: "刷新状态"; flat: true; onClicked: desk.refresh() }
                }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 16
        Layout.rightMargin: 16
        Layout.topMargin: 8
        Layout.bottomMargin: 12
        Layout.alignment: Qt.AlignRight
        spacing: 8
        AppButton {
            text: "应用切换"
            highlighted: true
            Layout.preferredWidth: 140
            onClicked: desk.applyAll()
        }
    }

    Component.onCompleted: desk.refresh()
}
