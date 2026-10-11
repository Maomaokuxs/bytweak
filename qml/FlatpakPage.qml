import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Flatpak 管理页：远程源 + 应用安装/卸载/更新（内容滚动，底栏固定）
ColumnLayout {
    spacing: 0

    property string flatQuery: ""

    property var filteredApps: flat.appList.filter(function (a) {
        var q = flatQuery.trim().toLowerCase()
        if (!q)
            return true
        return a.id.toLowerCase().indexOf(q) !== -1 || a.name.toLowerCase().indexOf(q) !== -1
    })

    AppDialog { id: msgDlg }
    Connections {
        target: flat
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    ScrollView {
        id: flatScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: flatScroll.availableWidth
            spacing: 12

            Label { text: "Flatpak 管理"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }
            Label {
                text: "管理 Flatpak 远程源，安装与卸载应用"
                opacity: 0.6
                font.pixelSize: 12
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Label {
                text: "本机未安装 flatpak"
                opacity: 0.6
                visible: !flat.available
            }

            GroupBox {
                title: "远程源"
                Layout.fillWidth: true
                visible: flat.available
                ColumnLayout {
                    anchors.fill: parent
                    Repeater {
                        model: flat.remoteList
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Label {
                                text: modelData.name
                                font.bold: true
                                font.family: "monospace"
                            }
                            Label {
                                text: modelData.scope === "system" ? "系统" : "用户"
                                opacity: 0.6
                                font.pixelSize: 12
                            }
                        }
                    }
                }
            }

            GroupBox {
                title: "安装新应用"
                Layout.fillWidth: true
                visible: flat.available
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Label { text: "应用 ID"; Layout.preferredWidth: 80 }
                        AppTextField {
                            id: installField
                            Layout.fillWidth: true
                            Layout.maximumWidth: 420
                            placeholderText: "如 org.mozilla.firefox…"
                            Keys.onEscapePressed: {
                                clear()
                                focus = false
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Item { Layout.fillWidth: true }
                        Button {
                            text: "安装到用户"
                            highlighted: true
                            enabled: !flat.busy && installField.text.trim() !== ""
                            onClicked: flat.installApp(installField.text)
                        }
                    }
                }
            }

            GroupBox {
                title: "已安装应用"
                Layout.fillWidth: true
                visible: flat.available
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8
                    AppTextField {
                        Layout.fillWidth: true
                        Layout.maximumWidth: 420
                        placeholderText: "搜索应用名或 ID…"
                        onTextChanged: flatQuery = text
                        Keys.onEscapePressed: {
                            clear()
                            focus = false
                        }
                    }
                    Label {
                        text: "共 " + flat.appList.length + " 个 · 显示 " + filteredApps.length + " 个"
                        opacity: 0.6
                        font.pixelSize: 12
                    }
                    Repeater {
                        model: filteredApps
                        delegate: RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    text: modelData.name
                                    font.bold: true
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                                Label {
                                    text: modelData.id + " · " + modelData.version + " · " + modelData.origin + " · " + (modelData.scope === "system" ? "系统" : "用户")
                                    opacity: 0.6
                                    font.pixelSize: 12
                                    elide: Text.ElideRight
                                    Layout.fillWidth: true
                                }
                            }
                            Button {
                                text: "卸载"
                                flat: true
                                enabled: !flat.busy
                                onClicked: flat.uninstallApp(modelData.id, modelData.scope)
                            }
                        }
                    }
                    Label {
                        text: flat.appList.length === 0 ? "暂无应用数据，点击右下刷新重试" : "无匹配应用，换个关键词"
                        opacity: 0.6
                        horizontalAlignment: Text.AlignHCenter
                        Layout.fillWidth: true
                        visible: filteredApps.length === 0 && !flat.busy
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
        BusyIndicator { visible: flat.busy; running: flat.busy }
        Button {
            text: "刷新"
            flat: true
            enabled: !flat.busy && flat.available
            onClicked: flat.refresh()
        }
        Button {
            text: "全部更新"
            highlighted: true
            enabled: !flat.busy && flat.available
            onClicked: flat.updateAll()
        }
    }

    Component.onCompleted: flat.refresh()
}
