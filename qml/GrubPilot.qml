import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import QtCore

// GRUB 单页试点：FluentWinUI3，逻辑全部走 GrubBridge（复用 grub_core）
ApplicationWindow {
    id: root
    visible: true
    width: 560
    height: 640
    title: "GRUB 配置 · QML 试点"

    FileDialog {
        id: fileDlg
        title: "选择 GRUB 主题"
        currentFolder: StandardPaths.writableLocation(StandardPaths.DownloadLocation)
        nameFilters: ["所有文件 (*)"]
        onAccepted: bridge.setFilePath(selectedFile)
    }

        AppDialog {
            id: msgDlg
        }

    Dialog {
        id: choiceDlg
        title: "选择版本"
        anchors.centerIn: parent
        modal: true
        property int selIdx: 0
        onOpened: selIdx = 0
        onAccepted: bridge.chooseVariant(selIdx)
        onRejected: bridge.chooseVariant(-1)

        background: Rectangle {
            color: "#ffffff"
            border.color: "#e3e6eb"
            radius: 12
        }
        header: Label {
            text: choiceDlg.title
            font.pixelSize: 15
            font.bold: true
            renderType: Text.NativeRendering
            color: "#111827"
            padding: 16
            bottomPadding: 4
        }
        contentItem: ColumnLayout {
            width: 340
            Label { text: "分辨率款式选择："; color: "#374151" }
            ListView {
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(220, choiceDlg.count * 36)
                property int count: bridge.choiceList.length
                model: bridge.choiceList
                clip: true
                delegate: ItemDelegate {
                    width: parent.width
                    text: modelData
                    highlighted: index === choiceDlg.selIdx
                    onClicked: choiceDlg.selIdx = index
                }
                ScrollBar.vertical: ScrollBar {}
            }
        }
        footer: RowLayout {
            spacing: 8
            Item { Layout.fillWidth: true }
            Button {
                text: "取消"
                Layout.preferredWidth: 100
                onClicked: choiceDlg.reject()
            }
            Button {
                text: "确定"
                highlighted: true
                Layout.preferredWidth: 100
                onClicked: choiceDlg.accept()
            }
        }
    }

    Connections {
        target: bridge
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
        function onChoiceRequested() { choiceDlg.open() }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label { text: "GRUB 配置"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }
        Label { text: "QML 试点页：交互经由 GrubBridge，后端与 Widgets 版共用 grub_core"; opacity: 0.6; wrapMode: Text.WordWrap; Layout.fillWidth: true }

        GroupBox {
            title: "安装外部主题包"
            Layout.fillWidth: true
            RowLayout {
                anchors.fill: parent
                spacing: 12
                Label { text: "主题文件"; Layout.preferredWidth: 80 }
                TextField {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 420
                    readOnly: true
                    placeholderText: "未选择，可直接切换本地主题"
                    text: bridge.filePath
                }
                Button { text: "浏览…"; onClicked: fileDlg.open() }
            }
        }

        GroupBox {
            title: "本地已安装主题"
            Layout.fillWidth: true
            ColumnLayout {
                anchors.fill: parent
                ComboBox {
                    id: themeCombo
                    objectName: "themeCombo"
                    Layout.fillWidth: true
                    Layout.maximumWidth: 420
                    model: bridge.themeList
                    currentIndex: bridge.currentThemeIndex
                    onActivated: bridge.applyLocalTheme(index)
                    // 弹窗限高：最多显示 8 行，且不超过窗口高度的 45%，全屏也不超
                    popup.height: Math.min(Math.min(bridge.themeList.length, 8) * 40 + 16, root.height * 0.45)
                    popup.width: width
                }
            }
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 8
            BusyIndicator { visible: bridge.busy; running: bridge.busy }
            Button {
                text: "刷新"
                flat: true
                enabled: !bridge.busy
                onClicked: bridge.refreshThemes()
            }
            Button {
                text: bridge.busy ? "执行中…" : "写入并更新 GRUB"
                highlighted: true
                enabled: !bridge.busy
                onClicked: bridge.apply()
            }
        }
    }

    Component.onCompleted: bridge.refreshThemes()
}
