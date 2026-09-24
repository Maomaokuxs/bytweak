import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 显卡页：设备卡 + 驱动硬解卡 + 编解码矩阵（内容滚动，底栏固定）
ColumnLayout {
    spacing: 0

    AppDialog {
        id: msgDlg
    }
    Connections {
        target: gpu
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    ScrollView {
        id: gpuScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        Item {
            width: gpuScroll.availableWidth
            height: innerCol.implicitHeight + 32
            ColumnLayout {
                id: innerCol
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                Label { text: "显卡与硬件加速"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }

                GroupBox {
                    title: "检测到的显卡"
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10
                        Repeater {
                            model: gpu.deviceList
                            delegate: RowLayout {
                                Layout.fillWidth: true
                                spacing: 10
                                GlyphIcon { kind: "chip"; color: modelData.color; iconSize: 24 }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 1
                                    Label { text: modelData.vendor; font.bold: true; font.pixelSize: 14; renderType: Text.NativeRendering; color: theme.textMain }
                                    Label { text: modelData.name + (modelData.pci ? "  [" + modelData.pci + "]" : ""); color: theme.textSub; font.pixelSize: 12 }
                                }
                            }
                        }
                        Label {
                            text: "未侦测到主流显卡"
                            color: theme.textSub
                            font.italic: true
                            visible: gpu.deviceList.length === 0
                        }
                    }
                }

                GroupBox {
                    title: "驱动与硬解状态"
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Rectangle {
                                id: statusDot
                                width: 10
                                height: 10
                                radius: 5
                                Layout.alignment: Qt.AlignTop
                                Layout.topMargin: 5
                                color: gpu.busy ? theme.textSub : (gpu.statusLevel === "ok" ? theme.codecOk : (gpu.statusLevel === "warn" ? theme.codecErr : theme.textSub))
                                SequentialAnimation {
                                    loops: Animation.Infinite
                                    running: gpu.busy
                                    NumberAnimation { target: statusDot; property: "opacity"; from: 1.0; to: 0.35; duration: 600; easing.type: Easing.InOutQuad }
                                    NumberAnimation { target: statusDot; property: "opacity"; from: 0.35; to: 1.0; duration: 600; easing.type: Easing.InOutQuad }
                                    onStopped: statusDot.opacity = 1.0
                                }
                            }
                            Label { text: gpu.statusText; font.pixelSize: 15; font.bold: true; renderType: Text.NativeRendering; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                        }
                        TextEdit { text: gpu.versionText; opacity: 0.6; wrapMode: TextEdit.WordWrap; Layout.fillWidth: true; readOnly: true; selectByMouse: true; renderType: TextEdit.NativeRendering; color: theme.textSub; font.pixelSize: 12; font.family: "monospace" }
                        Label { text: "硬解能力"; font.bold: true; font.pixelSize: 12; renderType: Text.NativeRendering; opacity: 0.6 }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 16
                            rowSpacing: 10
                            Repeater {
                                model: gpu.codecList
                            delegate: RowLayout {
                                spacing: 8
                                GlyphIcon {
                                    kind: modelData.ok ? "check" : "x"
                                    color: modelData.ok ? theme.codecOk : theme.codecErr
                                    iconSize: 16
                                }
                                Label { text: modelData.name; color: theme.textMain; font.pixelSize: 14 }
                            }
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
        spacing: 8
        Button {
            text: "刷新检测"
            flat: true
            enabled: !gpu.busy
            onClicked: gpu.refresh()
        }
        Button {
            text: "复制诊断信息"
            flat: true
            enabled: !gpu.busy
            onClicked: gpu.copyDiagnostics()
        }
        Item { Layout.fillWidth: true }
        BusyIndicator { visible: gpu.busy; running: gpu.busy }
        Button {
            text: gpu.busy ? "正在后台执行，请稍候…" : gpu.actionText
            highlighted: true
            enabled: gpu.actionEnabled
            Layout.preferredWidth: 220
            onClicked: gpu.apply()
        }
    }

    Component.onCompleted: gpu.refresh()
}
