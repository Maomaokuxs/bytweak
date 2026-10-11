import QtQuick
import QtQuick.Controls

// 统一样式输入框
// 默认盒式：白底 + 浅灰描边，与卡片风格一致（用于内容区）
// underline=true：透明底 + 底部下划线，Fluent 风格（用于导航栏等灰底区域）
// 聚焦时底部显示主题色高亮线（模仿 Windows 输入框）；盒式下高亮线贴合底部圆角
// （FluentWinUI3 默认输入框底在当前主题下不可见，故自定义）
TextField {
    id: field
    property bool underline: false
    placeholderTextColor: theme.textSub
    color: theme.textMain
    background: Rectangle {
        radius: 8
        color: field.underline ? "transparent"
              : field.activeFocus ? theme.accent : theme.cardBg
        border.color: field.underline ? "transparent"
                      : field.activeFocus ? theme.accent : theme.cardBorder
        border.width: field.underline ? 0 : 1

        // 盒式聚焦：内衬四周留 1px、底部留 2px 主题色，形成贴合圆角的底部高亮线
        Rectangle {
            visible: !field.underline
            anchors.fill: parent
            anchors.margins: 1
            anchors.bottomMargin: field.activeFocus ? 2 : 1
            radius: 7
            color: theme.cardBg
        }

        // 下划线式：底部横线，聚焦时变主题色加粗
        Rectangle {
            visible: field.underline
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: field.activeFocus ? 2 : 1
            color: field.activeFocus ? theme.accent : theme.boxBorder
        }
    }
}
