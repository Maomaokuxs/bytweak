import QtQuick
import QtQuick.Controls

// 统一样式输入框：白底 + 浅灰描边，与卡片风格一致（用于内容区）
// 输入框不需要聚焦高亮（与搜索框区分）
// 注意：background 必须用 Item 包一层，直接用 Rectangle 做 background 会导致圆角被裁成直角
// （FluentWinUI3 默认输入框底在当前主题下不可见，故自定义）
TextField {
    id: field
    placeholderTextColor: theme.textSub
    color: theme.textMain
    background: Item {
        Rectangle {
            anchors.fill: parent
            radius: 8
            color: theme.cardBg
            border.color: theme.cardBorder
            border.width: 1
        }
    }
}
