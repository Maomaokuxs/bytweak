import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 服务管理页：system 服务启停 + 自启开关（内容滚动，底栏固定）
ColumnLayout {
    spacing: 0

    property string svcQuery: ""
    property int svcFilter: 0
    property var filteredServices: svc.serviceList.filter(function (s) {
        if (svcFilter === 1 && !s.active)
            return false
        if (svcFilter === 2 && s.active)
            return false
        var q = svcQuery.trim().toLowerCase()
        if (!q)
            return true
        return s.id.toLowerCase().indexOf(q) !== -1 || s.desc.toLowerCase().indexOf(q) !== -1
    })

    AppDialog { id: msgDlg }
    Connections {
        target: svc
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    ScrollView {
        id: svcScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: svcScroll.availableWidth
            spacing: 12

            Label { text: "服务管理"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                TextField {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 420
                    placeholderText: "搜索服务名或描述…"
                    onTextChanged: svcQuery = text
                    Keys.onEscapePressed: {
                        clear()
                        focus = false
                    }
                }
                ComboBox {
                    Layout.preferredWidth: 110
                    model: ["全部", "运行中", "已停止"]
                    onActivated: svcFilter = index
                }
            }

            Label {
                text: "共 " + svc.serviceList.length + " 个 · 显示 " + filteredServices.length + " 个"
                opacity: 0.6
                font.pixelSize: 12
            }

            GroupBox {
                Layout.fillWidth: true
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 2
                    Repeater {
                        model: filteredServices
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                Layout.alignment: Qt.AlignVCenter
                                color: modelData.active ? theme.codecOk : theme.textSub
                                opacity: modelData.active ? 1.0 : 0.5
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    text: modelData.id
                                    font.family: "monospace"
                                    font.pixelSize: 13
                                    font.bold: true
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: modelData.desc + (modelData.enabledState !== "enabled" && modelData.enabledState !== "disabled" ? " · " + modelData.enabledState : "")
                                    opacity: 0.6
                                    font.pixelSize: 12
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }
                            AccentCheckDelegate {
                                text: "自启"
                                checked: modelData.enabled
                                enabled: !svc.busy && modelData.enabledState !== "static" && modelData.enabledState !== "masked"
                                onToggled: svc.setEnabled(modelData.id, checked)
                            }
                            Button {
                                text: modelData.active ? "停止" : "启动"
                                flat: !modelData.active
                                enabled: !svc.busy
                                Layout.preferredWidth: 76
                                onClicked: svc.setActive(modelData.id, !modelData.active)
                            }
                        }
                    }
                    Label {
                        text: svc.serviceList.length === 0 ? "暂无服务数据，点击右下刷新重试" : "无匹配服务，换个关键词或筛选条件"
                        opacity: 0.6
                        horizontalAlignment: Text.AlignHCenter
                        Layout.fillWidth: true
                        visible: filteredServices.length === 0 && !svc.busy
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
        BusyIndicator { visible: svc.busy; running: svc.busy }
        Button {
            text: "刷新"
            flat: true
            enabled: !svc.busy
            onClicked: svc.refresh()
        }
    }

    Component.onCompleted: svc.refresh()
}
