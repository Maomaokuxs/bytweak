import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 主机名修改：查看与修改本机主机名（需管理员权限）
ColumnLayout {
    spacing: 0

    AppDialog { id: msgDlg }
    Connections {
        target: hostname
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    ScrollView {
        id: hnScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: hnScroll.availableWidth
            spacing: 12

            Label { text: "主机名"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }
            Label {
                text: "主机名是这台电脑在网络中的名字，修改后立即生效（部分应用可能需要重启）"
                opacity: 0.6
                font.pixelSize: 12
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            GroupBox {
                Layout.fillWidth: true
                title: "当前主机名"
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 10
                    Label {
                        text: hostname.hostname === "" ? "读取中…" : hostname.hostname
                        font.family: "monospace"
                        font.pixelSize: 16
                        font.bold: true
                    }
                    RowLayout {
                        spacing: 8
                        AppTextField {
                            id: nameField
                            Layout.fillWidth: true
                            Layout.maximumWidth: 320
                            placeholderText: "输入新主机名，如 my-fedora"
                            maximumLength: 64
                            Keys.onReturnPressed: applyBtn.clicked()
                        }
                        Button {
                            id: applyBtn
                            text: "应用"
                            enabled: !hostname.busy && nameField.text.trim() !== "" && nameField.text.trim() !== hostname.hostname
                            onClicked: {
                                hostname.setHostname(nameField.text)
                                nameField.clear()
                            }
                        }
                    }
                    Label {
                        text: "只能包含字母、数字和连字符，不能以连字符开头或结尾"
                        opacity: 0.55
                        font.pixelSize: 12
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
        BusyIndicator { visible: hostname.busy; running: hostname.busy }
        Button {
            text: "刷新"
            flat: true
            enabled: !hostname.busy
            onClicked: hostname.refresh()
        }
    }

    Component.onCompleted: hostname.refresh()
}
