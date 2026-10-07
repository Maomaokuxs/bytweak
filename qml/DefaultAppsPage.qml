import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 默认应用设置：浏览器 / 文件管理器 / 图片 / 视频 / 文本 / PDF 的默认打开应用
ColumnLayout {
    spacing: 0

    AppDialog { id: msgDlg }
    Connections {
        target: defapp
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    ScrollView {
        id: daScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: daScroll.availableWidth
            spacing: 12

            Label { text: "默认应用设置"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }
            Label {
                text: "修改即时生效，写入当前用户的 mimeapps.list，无需管理员权限"
                opacity: 0.6
                font.pixelSize: 12
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Repeater {
                model: defapp.defaults
                delegate: GroupBox {
                    Layout.fillWidth: true
                    title: modelData.label
                    RowLayout {
                        anchors.fill: parent
                        spacing: 8
                        Label {
                            text: "当前：" + modelData.current_name
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            opacity: 0.8
                        }
                        AppComboBox {
                            Layout.preferredWidth: 260
                            model: modelData.candidates.map(function (c) { return c.name })
                            currentIndex: Math.max(0, modelData.candidates.findIndex(function (c) { return c.id === modelData.current }))
                            onActivated: defapp.setDefault(modelData.key, modelData.candidates[index].id)
                            enabled: !defapp.busy && modelData.candidates.length > 0
                        }
                    }
                }
            }

            Label {
                text: "未扫描到可设置的应用"
                opacity: 0.6
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
                visible: defapp.defaults.length === 0 && !defapp.busy
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
        BusyIndicator { visible: defapp.busy; running: defapp.busy }
        Button {
            text: "刷新"
            flat: true
            enabled: !defapp.busy
            onClicked: defapp.refresh()
        }
    }

    Component.onCompleted: defapp.refresh()
}
