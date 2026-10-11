import QtQuick
import QtQuick.Controls

// 统一样式输入框：白底 + 浅灰描边，与卡片风格一致（用于内容区）
// 聚焦时底部显示主题色高亮线（模仿 Windows 输入框），高亮线贴合底部圆角
// （FluentWinUI3 默认输入框底在当前主题下不可见，故自定义）
TextField {
    id: field
    placeholderTextColor: theme.textSub
    color: theme.textMain
    background: Rectangle {
        id: bg
        radius: 8
        color: field.activeFocus ? theme.accent : theme.cardBg
        border.color: field.activeFocus ? theme.accent : theme.cardBorder
        border.width: 1
        // 内衬：聚焦时四周各留 1px、底部留 2px 主题色，形成贴合圆角的底部高亮线
        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            anchors.bottomMargin: field.activeFocus ? 2 : 1
            radius: bg.radius - 1
            color: theme.cardBg
        }
    }
}
