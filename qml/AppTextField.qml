import QtQuick
import QtQuick.Controls

// 统一样式输入框：白底 + 浅灰描边，与卡片风格一致
// （FluentWinUI3 默认输入框底在当前主题下不可见，故自定义）
TextField {
    placeholderTextColor: theme.textSub
    color: theme.textMain
    background: Rectangle {
        radius: 8
        color: theme.cardBg
        border.color: theme.cardBorder
        border.width: 1
    }
}
