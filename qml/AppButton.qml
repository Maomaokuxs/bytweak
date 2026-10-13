import QtQuick
import QtQuick.Controls

// 自绘按钮：跟随 theme 桥昼夜切换（替代 Fluent 原生 Button，后者运行时不跟主题）
// 样式与 AppTextField 对齐：圆角 8，卡片底色 + 描边；highlighted 时用主题色实心
Button {
    id: btn
    background: Item {
        Rectangle {
            anchors.fill: parent
            radius: 8
            color: {
                if (!btn.enabled) return theme.boxDisabledBg
                if (btn.highlighted) {
                    if (btn.pressed) return theme.accentPressed
                    if (btn.hovered) return theme.accentHover
                    return theme.accent
                }
                if (btn.pressed) return theme.boxDisabledBg
                return theme.cardBg
            }
            border.color: {
                if (btn.highlighted) return "transparent"
                // hover 时描边用 accent 色，其余用 cardBorder
                if (btn.hovered && btn.enabled) return theme.accent
                return theme.cardBorder
            }
            border.width: btn.highlighted ? 0 : 1
            opacity: btn.flat ? (btn.hovered ? 0.12 : 0) : 1
        }
    }
    contentItem: Label {
        text: btn.text
        font: btn.font
        color: {
            if (!btn.enabled) return theme.textSub
            if (btn.highlighted) return "#ffffff"
            return theme.textMain
        }
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
