import QtQuick
import QtQuick.Controls

// 统一样式输入框：白底 + 浅灰描边，与卡片风格一致
// 聚焦时底部显示主题色高亮线（模仿 Windows 输入框）
// （FluentWinUI3 默认输入框底在当前主题下不可见，故自定义）
TextField {
    id: field
    placeholderTextColor: theme.textSub
    color: theme.textMain
    background: Rectangle {
        radius: 8
        color: theme.cardBg
        border.color: theme.cardBorder
        border.width: 1
        // Windows 风格：点击输入（聚焦）时底部高亮线
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            anchors.bottomMargin: 1
            height: 2
            radius: 1
            color: theme.accent
            visible: field.activeFocus
        }
    }
}
