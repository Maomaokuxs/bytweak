import QtQuick
import QtQuick.Controls

// 导航搜索框：独立组件
// 长椭圆（胶囊）形 + 外框线；聚焦时底部主题色高亮线贴合底部弧度（模仿 Windows）
// （FluentWinUI3 默认输入框底在当前主题下不可见，故自定义）
TextField {
    id: field
    placeholderTextColor: theme.textSub
    color: theme.textMain
    background: Rectangle {
        id: bg
        radius: height / 2
        color: field.activeFocus ? theme.accent : theme.cardBg
        border.color: field.activeFocus ? theme.accent : theme.cardBorder
        border.width: 1
        // 内衬：聚焦时四周各留 1px、底部留 2px 主题色，形成贴合胶囊底部弧度的高亮线
        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            anchors.bottomMargin: field.activeFocus ? 2 : 1
            radius: bg.radius - 1
            color: theme.cardBg
        }
    }
}
