import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtCore

// 光标页：导入卡 + 选择预览卡，预览图经 ImageProvider 供给（内容滚动，底栏固定）
ColumnLayout {
    spacing: 0

    FileDialog {
        id: fileDlg
        title: "选择鼠标主题压缩包"
        currentFolder: StandardPaths.writableLocation(StandardPaths.DownloadLocation)
        nameFilters: ["鼠标包 (*.tar.gz *.tar.xz *.zip *.tgz)"]
        onAccepted: cursor.setFilePath(selectedFile)
    }
    AppDialog {
        id: msgDlg
    }
    Connections {
        target: cursor
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    ScrollView {
        id: cursorScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: cursorScroll.availableWidth
            spacing: 12

                Label { text: "鼠标指针样式"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }
                Label {
                    text: "导入或切换鼠标指针主题，可实时预览效果"
                    opacity: 0.6
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                GroupBox {
                    title: "导入外部主题"
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12
                            Label { text: "主题文件"; Layout.preferredWidth: 80 }
                            AppTextField {
                                Layout.fillWidth: true
                                Layout.maximumWidth: 420
                                readOnly: true
                                        placeholderText: "*.tar.gz / *.zip"
                                text: cursor.filePath
                            }
                            Button { text: "浏览…"; onClicked: fileDlg.open() }
                        }
                    }
                }

                GroupBox {
                    title: "本地主题与预览"
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12
                            Label { text: "当前主题"; Layout.preferredWidth: 80 }
                            AppComboBox {
                                Layout.fillWidth: true
                                Layout.maximumWidth: 420
                                model: cursor.themeList
                                currentIndex: cursor.currentThemeIndex
                                onActivated: cursor.setTheme(index)
                                // 弹窗固定紧凑：最多 8 行
                                popup.height: Math.min(cursor.themeList.length, 8) * 40 + 16
                                popup.width: Math.min(width, 420)
                                // 自绘弹窗底：不依赖风格明暗素材（平台深色误判会导致黑底深字）
                                popup.background: Rectangle {
                                    color: theme.popupBg
                                    border.color: theme.popupBorder
                                    radius: 10
                                }
                            }
                        }
                        Image {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 88
                            Layout.maximumHeight: 150
                            fillMode: Image.PreserveAspectFit
                            source: "image://cursorimg/all?tick=" + cursor.previewTick
                        }
                        Label { text: cursor.previewInfo; opacity: 0.6 }
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
        Button {
            text: "应用"
            highlighted: true
            Layout.preferredWidth: 120
            onClicked: cursor.apply()
        }
    }

    Component.onCompleted: cursor.refresh()
}
