import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 时区页：状态卡 + 选择卡 + 右下应用（内容滚动，底栏固定）
ColumnLayout {
    spacing: 0

    AppDialog {
        id: msgDlg
    }
    Connections {
        target: tz
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    ScrollView {
        id: tzScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: tzScroll.availableWidth
            spacing: 12

                Label { text: "时区设置"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }

                GroupBox {
                    title: "当前状态"
                    Layout.fillWidth: true
                    Label { text: tz.statusText; font.pixelSize: 15; font.bold: true; renderType: Text.NativeRendering; wrapMode: Text.WordWrap; anchors.fill: parent }
                }

                GroupBox {
                    title: "切换时区"
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12
                            Label { text: "选择时区"; Layout.preferredWidth: 80 }
                            ComboBox {
                                id: tzCombo
                                Layout.fillWidth: true
                                Layout.maximumWidth: 420
                                editable: true
                                model: tz.zoneList
                                currentIndex: tz.currentZoneIndex
                                onActivated: tz.setZone(index)
                                onAccepted: tz.setZoneByName(displayText)
                                // 弹窗固定紧凑：最多 8 行（约 304px），598 个时区也只显示 8 行
                                popup.height: Math.min(tz.zoneList.length, 8) * 36 + 16
                                popup.width: Math.min(width, 420)
                                // 自绘弹窗底：不依赖风格明暗素材（平台深色误判会导致黑底深字）
                                popup.background: Rectangle {
                                    color: theme.popupBg
                                    border.color: theme.popupBorder
                                    radius: 10
                                }
                            }
                        }
                    }
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
        BusyIndicator { visible: tz.busy; running: tz.busy }
        Button {
            text: tz.busy ? "执行中…" : "应用"
            highlighted: true
            enabled: !tz.busy
            Layout.preferredWidth: 120
            onClicked: {
                if (tzCombo.displayText && !tz.setZoneByName(tzCombo.displayText))
                    return
                tz.apply()
            }
        }
    }

    Component.onCompleted: tz.refresh()
}
