import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 软件源页：双列表开关 + 刷新（内容滚动，底栏固定）
ColumnLayout {
    spacing: 0

    AppDialog {
        id: msgDlg
    }
    Connections {
        target: repo
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    ScrollView {
        id: repoScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        Item {
            width: repoScroll.availableWidth
            height: innerCol.implicitHeight + 32
            ColumnLayout {
                id: innerCol
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                Label { text: "软件源管理"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }

                GroupBox {
                    title: "当前系统已部署的仓库"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 300
                    ColumnLayout {
                        anchors.fill: parent
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            model: repo.repoList
                            enabled: !repo.busy
                            delegate: AccentCheckDelegate {
                                width: parent.width
                                text: modelData.name + "\n[" + modelData.id + "]"
                                checked: modelData.enabled
                                onToggled: repo.toggleRepo(modelData.id, checked)
                            }
                            ScrollBar.vertical: ScrollBar {}
                        }
                        Label {
                            text: "暂无仓库数据，点击右下刷新重试"
                            opacity: 0.6
                            horizontalAlignment: Text.AlignHCenter
                            Layout.fillWidth: true
                            visible: repo.repoList.length === 0 && !repo.busy
                        }
                    }
                }

                GroupBox {
                    title: "推荐仓库"
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        Repeater {
                            model: repo.recommendedList
                            delegate: AccentCheckDelegate {
                                Layout.fillWidth: true
                                text: modelData.label
                                checked: modelData.installed
                                enabled: !repo.busy
                                onToggled: repo.toggleRecommended(modelData.id, checked)
                            }
                        }
                        Label {
                            text: "推荐源暂不可用，点击右下刷新重试"
                            opacity: 0.6
                            horizontalAlignment: Text.AlignHCenter
                            Layout.fillWidth: true
                            visible: repo.recommendedList.length === 0 && !repo.busy
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
        BusyIndicator { visible: repo.busy; running: repo.busy }
        Button {
            text: "刷新"
            flat: true
            enabled: !repo.busy
            onClicked: repo.refresh()
        }
    }

    Component.onCompleted: repo.refresh()
}
