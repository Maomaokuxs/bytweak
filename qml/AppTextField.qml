import QtQuick
import QtQuick.Controls

// 统一样式输入框：灰底 + 1px 边框线 + 主题文字色
// （FluentWinUI3 默认输入框底在当前主题下不可见，故自定义）
TextField {
    placeholderTextColor: theme.textSub
    color: theme.textMain
    background: Rectangle {
        radius: 8
        color: theme.boxDisabledBg
        border.color: theme.boxBorder
        border.width: 1
    }
}
