import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 操作日志查看：展示 ~/.cache/by-mgr/fedora-tweak-tool/logs/operations.log 尾部
Dialog {
    id: root
    anchors.centerIn: parent
    modal: true
    title: "操作日志"

    background: Rectangle {
        color: theme.popupBg
        border.color: theme.popupBorder
        radius: 12
    }
    header: Label {
        text: root.title
        font.pixelSize: 15
        font.bold: true
        renderType: Text.NativeRendering
        color: theme.textMain
        padding: 16
        bottomPadding: 4
    }
    contentItem: ColumnLayout {
        spacing: 8
        Rectangle {
            Layout.preferredWidth: 520
            Layout.preferredHeight: 300
            color: theme.boxDisabledBg
            radius: 8
            clip: true

            Flickable {
                id: logFlick
                anchors.fill: parent
                anchors.margins: 8
                anchors.rightMargin: 16
                clip: true
                contentWidth: width
                contentHeight: logText.implicitHeight
                boundsBehavior: Flickable.StopAtBounds
                flickableDirection: Flickable.VerticalFlick

                TextEdit {
                    id: logText
                    width: logFlick.width
                    readOnly: true
                    wrapMode: TextEdit.Wrap
                    text: repo.opLogText
                    font.family: "monospace"
                    font.pixelSize: 12
                    color: theme.textMain
                }
            }

            // 自绘纵向滚动条：Fluent 风格的原生 ScrollBar 在对话框内不渲染，故手绘
            Rectangle {
                id: track
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.margins: 6
                width: 6
                radius: 3
                color: "transparent"
                visible: logFlick.contentHeight > logFlick.height

                Rectangle {
                    id: thumb
                    width: parent.width
                    radius: 3
                    color: theme.textSub
                    opacity: dragArea.pressed ? 0.75 : 0.45
                    height: Math.max(24, track.height * logFlick.height / Math.max(logFlick.contentHeight, 1))
                    y: (track.height - height) * (logFlick.contentY / Math.max(logFlick.contentHeight - logFlick.height, 1))
                }
                MouseArea {
                    id: dragArea
                    anchors.fill: parent
                    onPositionChanged: {
                        if (!pressed || track.height <= thumb.height)
                            return
                        var maxY = track.height - thumb.height
                        var frac = Math.max(0, Math.min(1, (mouseY - thumb.height / 2) / maxY))
                        logFlick.contentY = frac * Math.max(logFlick.contentHeight - logFlick.height, 0)
                    }
                }
            }
        }
        Label {
            text: "日志文件：~/.cache/by-mgr/fedora-tweak-tool/logs/operations.log"
            opacity: 0.6
            font.pixelSize: 11
        }
    }
    footer: RowLayout {
        spacing: 8
        Button {
            text: "清空日志"
            flat: true
            onClicked: repo.clearOpLog()
        }
        Item { Layout.fillWidth: true }
        Button {
            text: "刷新"
            flat: true
            onClicked: repo.refreshOpLog()
        }
        Button {
            text: "关闭"
            highlighted: true
            Layout.preferredWidth: 100
            onClicked: root.close()
        }
    }
    onOpened: repo.refreshOpLog()
}
