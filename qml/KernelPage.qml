import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 内核管理：查看已安装内核、删除旧内核、设置默认启动内核（需管理员权限）
ColumnLayout {
    spacing: 0

    property string confirmFull: ""

    AppDialog { id: msgDlg }
    Connections {
        target: kernel
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    ScrollView {
        id: kScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: kScroll.availableWidth
            spacing: 12

            Label { text: "内核管理"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }
            Label {
                text: "删除旧内核可释放 /boot 空间；正在运行、默认启动的内核以及最后一个内核不可删除"
                opacity: 0.6
                font.pixelSize: 12
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Repeater {
                model: kernel.kernels
                delegate: GroupBox {
                    Layout.fillWidth: true
                    RowLayout {
                        anchors.fill: parent
                        spacing: 8
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            RowLayout {
                                spacing: 6
                                Label {
                                    text: modelData.full
                                    font.family: "monospace"
                                    font.pixelSize: 13
                                    font.bold: true
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Rectangle {
                                    visible: modelData.current
                                    implicitWidth: curTxt.implicitWidth + 12
                                    implicitHeight: curTxt.implicitHeight + 6
                                    radius: 4
                                    color: theme.codecOk
                                    Label {
                                        id: curTxt
                                        anchors.centerIn: parent
                                        text: "当前"
                                        color: "white"
                                        font.pixelSize: 11
                                    }
                                }
                                Rectangle {
                                    visible: modelData.is_default
                                    implicitWidth: dftTxt.implicitWidth + 12
                                    implicitHeight: dftTxt.implicitHeight + 6
                                    radius: 4
                                    color: theme.accent
                                    Label {
                                        id: dftTxt
                                        anchors.centerIn: parent
                                        text: "默认启动"
                                        color: "white"
                                        font.pixelSize: 11
                                    }
                                }
                            }
                            Label {
                                text: modelData.pkgs.length + " 个软件包"
                                opacity: 0.6
                                font.pixelSize: 12
                            }
                        }
                        AppButton {
                            text: "设为默认"
                            flat: true
                            visible: !modelData.is_default
                            enabled: !kernel.busy
                            onClicked: kernel.setDefault(modelData.full)
                        }
                        AppButton {
                            text: confirmFull === modelData.full ? "确认删除？" : "删除"
                            enabled: !kernel.busy && !modelData.current && !modelData.is_default && kernel.kernels.length > 1
                            onClicked: {
                                if (confirmFull === modelData.full) {
                                    confirmFull = ""
                                    kernel.removeKernel(modelData.full)
                                } else {
                                    confirmFull = modelData.full
                                }
                            }
                        }
                    }
                }
            }

            Label {
                text: "未找到已安装的内核，点击右下刷新重试"
                opacity: 0.6
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
                visible: kernel.kernels.length === 0 && !kernel.busy
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
        BusyIndicator { visible: kernel.busy; running: kernel.busy }
        AppButton {
            text: "刷新"
            flat: true
            enabled: !kernel.busy
            onClicked: kernel.refresh()
        }
    }

    Component.onCompleted: kernel.refresh()
}
