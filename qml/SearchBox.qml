import QtQuick
import QtQuick.Controls

// 导航搜索框：独立组件
// 长椭圆（胶囊）形 + 外框线；聚焦时主题色高亮只分布在底部外沿，贴合底部弧度
// （FluentWinUI3 默认输入框底在当前主题下不可见，故自定义）
TextField {
    id: field
    placeholderTextColor: theme.textSub
    color: theme.textMain
    leftPadding: 16
    rightPadding: 16
    background: Item {
        // 高亮层（下）：accent 胶囊，底部撑出 3px，仅底部弧线露在白底之外
        // 3px（而非 2px）：低 PPI 显示器上 2px 弧线锯齿明显，3px 抗锯齿更平滑
        Rectangle {
            visible: field.activeFocus
            anchors.fill: parent
            anchors.bottomMargin: -3
            radius: height / 2
            color: "transparent"
            border.color: theme.accent
            border.width: 3
            antialiasing: true
        }
        // 主体（上）：白胶囊 + 浅灰边框，盖住高亮层的上/左/右
        Rectangle {
            anchors.fill: parent
            radius: height / 2
            color: theme.cardBg
            border.color: theme.cardBorder
            border.width: 1
        }
    }
}
