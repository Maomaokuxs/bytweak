import QtQuick
import QtQuick.Controls

// 定制多选行：与 AccentCheckBox 同款指示器；文本锚定在指示器右侧，支持多行
CheckDelegate {
    id: control
    spacing: 10

    indicator: Rectangle {
        id: box
        implicitWidth: 20
        implicitHeight: 20
        x: control.leftPadding
        y: 10
        radius: 6
        SequentialAnimation {
            id: popAnim
            NumberAnimation { target: box; property: "scale"; from: 0.6; to: 1.0; duration: 160; easing.type: Easing.OutBack }
        }
        Connections { target: control; function onCheckedChanged() { popAnim.restart() } }
        color: !control.enabled ? theme.boxDisabledBg
               : control.checked ? (control.pressed ? theme.accentPressed : (control.hovered ? theme.accentHover : theme.accent))
               : "transparent"
        border.color: control.checked ? "transparent" : (control.hovered ? theme.accent : theme.boxBorder)
        border.width: control.checked ? 0 : 1.5

        Behavior on color { ColorAnimation { duration: 120 } }

        Canvas {
            anchors.fill: parent
            anchors.margins: 4
            visible: control.checked
            onVisibleChanged: requestPaint()
            onPaint: {
                var ctx = getContext("2d")
                ctx.strokeStyle = "#ffffff"
                ctx.lineWidth = 2.5
                ctx.lineCap = "round"
                ctx.lineJoin = "round"
                ctx.beginPath()
                ctx.moveTo(width * 0.22, height * 0.52)
                ctx.lineTo(width * 0.43, height * 0.72)
                ctx.lineTo(width * 0.78, height * 0.28)
                ctx.stroke()
            }
        }
    }

    contentItem: Text {
        text: control.text
        color: control.enabled ? theme.textMain : theme.textSub
        font: control.font
        wrapMode: Text.WordWrap
        verticalAlignment: Text.AlignTop
        anchors.left: control.indicator.right
        anchors.leftMargin: control.spacing
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.topMargin: 8
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 8
    }
}
