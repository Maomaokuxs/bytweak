import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtCore

// 输入法页：状态卡 + 导入卡 + 主题选择卡（内容滚动，底栏固定）
ColumnLayout {
    spacing: 0

    FileDialog {
        id: fileDlg
        title: "选择 Fcitx5 主题压缩包"
        currentFolder: StandardPaths.writableLocation(StandardPaths.DownloadLocation)
        nameFilters: ["主题包 (*.tar.gz *.tar.xz *.zip *.tgz)"]
        onAccepted: fcitx.setFilePath(selectedFile)
    }
    AppDialog {
        id: msgDlg
    }
    Connections {
        target: fcitx
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    ScrollView {
        id: fcitxScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: fcitxScroll.availableWidth
            spacing: 12

                Label { text: "Fcitx 输入法"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }
                Label {
                    text: "导入或切换 fcitx5 输入法主题（浅色/深色）"
                    opacity: 0.6
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                GroupBox {
                    title: "当前主题"
                    Layout.fillWidth: true
                    Label { text: fcitx.statusText; wrapMode: Text.WordWrap; anchors.fill: parent }
                }

                GroupBox {
                    title: "导入主题包"
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12
                            Label { text: "文件"; Layout.preferredWidth: 80 }
                            AppTextField {
                                Layout.fillWidth: true
                                Layout.maximumWidth: 420
                                readOnly: true
                                        placeholderText: "*.tar.gz / *.zip"
                                text: fcitx.filePath
                            }
                            AppButton { text: "浏览…"; onClicked: fileDlg.open() }
                        }
                    }
                }

                GroupBox {
                    title: "主题选择"
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12
                            Label { text: "浅色主题"; Layout.preferredWidth: 80 }
                            AppComboBox {
                                Layout.fillWidth: true
                                Layout.maximumWidth: 420
                                model: fcitx.themeList
                                currentIndex: fcitx.lightThemeIndex
                                onActivated: fcitx.setLight(index)
                                // 弹窗固定紧凑：最多 8 行
                                popup.height: Math.min(fcitx.themeList.length, 8) * 40 + 16
                                popup.width: Math.min(width, 420)
                                // 自绘弹窗底：不依赖风格明暗素材（平台深色误判会导致黑底深字）
                                popup.background: Rectangle {
                                    color: theme.popupBg
                                    border.color: theme.popupBorder
                                    radius: 10
                                }
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12
                            Label { text: "深色主题"; Layout.preferredWidth: 80 }
                            AppComboBox {
                                Layout.fillWidth: true
                                Layout.maximumWidth: 420
                                model: fcitx.themeList
                                currentIndex: fcitx.darkThemeIndex
                                onActivated: fcitx.setDark(index)
                                // 弹窗固定紧凑：最多 8 行
                                popup.height: Math.min(fcitx.themeList.length, 8) * 40 + 16
                                popup.width: Math.min(width, 420)
                                // 自绘弹窗底：不依赖风格明暗素材（平台深色误判会导致黑底深字）
                                popup.background: Rectangle {
                                    color: theme.popupBg
                                    border.color: theme.popupBorder
                                    radius: 10
                                }
                            }
                        }
                        AccentCheckBox {
                            text: "根据系统配色自动切换深色/浅色主题"
                            checked: fcitx.autoSwitch
                            onToggled: fcitx.setAuto(checked)
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
        AppButton { text: "刷新"; flat: true; onClicked: fcitx.refresh() }
        AppButton {
            text: "应用"
            highlighted: true
            Layout.preferredWidth: 120
            onClicked: fcitx.apply()
        }
    }

    Component.onCompleted: fcitx.refresh()
}
