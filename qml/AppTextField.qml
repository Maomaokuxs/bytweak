import QtQuick
import QtQuick.Controls

// 统一样式输入框：白底 + 浅灰描边，与卡片风格一致（用于内容区）
// focusHighlight=true（默认）时，聚焦底部显示主题色高亮线（模仿 Windows 输入框），高亮线贴合底部圆角
// 浏览框（readOnly 文件路径展示）设 focusHighlight: false，点击不出现高亮，与搜索框区分
// （FluentWinUI3 默认输入框底在当前主题下不可见，故自定义）
TextField {
    id: field
    property bool focusHighlight: true
    readonly property bool highlighted: field.activeFocus && field.focusHighlight
    placeholderTextColor: theme.textSub
    color: theme.textMain
    background: Rectangle {
        id: bg
        radius: 8
        color: field.highlighted ? theme.accent : theme.cardBg
        border.color: field.highlighted ? theme.accent : theme.cardBorder
        border.width: 1
        // 内衬：高亮时四周各留 1px、底部留 2px 主题色，形成贴合圆角的底部高亮线
        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            anchors.bottomMargin: field.highlighted ? 2 : 1
            radius: bg.radius - 1
            color: theme.cardBg
        }
    }
}
