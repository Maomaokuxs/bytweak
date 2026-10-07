import QtQuick
import QtQuick.Controls

// 统一样式下拉框：白底 + 浅灰描边，与卡片/AppTextField 风格一致
// （FluentWinUI3 默认下拉框底在当前主题下不可见，故自定义；弹窗底各页已自绘）
ComboBox {
    background: Rectangle {
        radius: 8
        color: theme.cardBg
        border.color: theme.cardBorder
        border.width: 1
    }
}
