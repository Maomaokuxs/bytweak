import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 统一样式消息弹窗：白卡 + 标题 + 正文 + 右下实心确定钮
// details 非空时左下出现“查看输出”，展开显示等宽详情文本（如命令完整输出）
Dialog {
    id: root
    anchors.centerIn: parent
    modal: true
    property alias body: bodyLabel.text
    property string details: ""
    property bool showDetails: false
    onOpened: showDetails = false

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
        // 正文用只读 TextEdit：支持鼠标选中复制（报错信息需要能复制）
        TextEdit {
            id: bodyLabel
            readOnly: true
            selectByMouse: true
            wrapMode: Text.WordWrap
            color: theme.textMuted
            Layout.preferredWidth: 320
            // 去掉 TextEdit 默认的焦点框样式，保持 Label 外观
            activeFocusOnTab: false
        }
        TextArea {
            visible: root.showDetails && root.details !== ""
            readOnly: true
            wrapMode: Text.Wrap
            text: root.details
            font.family: "monospace"
            font.pixelSize: 12
            color: theme.textMain
            Layout.preferredWidth: 440
            Layout.preferredHeight: 200
            background: Rectangle {
                color: theme.boxDisabledBg
                radius: 8
            }
        }
    }
    footer: RowLayout {
        spacing: 8
        Button {
            text: root.showDetails ? "隐藏输出" : "查看输出"
            flat: true
            visible: root.details !== ""
            onClicked: root.showDetails = !root.showDetails
        }
        Item { Layout.fillWidth: true }
        Button {
            text: "确定"
            highlighted: true
            Layout.preferredWidth: 100
            onClicked: root.accept()
        }
    }
}
