import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 统一样式消息弹窗：白卡 + 标题 + 正文 + 右下实心确定钮
Dialog {
    id: root
    anchors.centerIn: parent
    modal: true
    property alias body: bodyLabel.text

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
    contentItem: Label {
        id: bodyLabel
        wrapMode: Text.WordWrap
        color: theme.textMuted
        width: 320
    }
    footer: RowLayout {
        spacing: 8
        Item { Layout.fillWidth: true }
        Button {
            text: "确定"
            highlighted: true
            Layout.preferredWidth: 100
            onClicked: root.accept()
        }
    }
}
