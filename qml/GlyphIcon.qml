import QtQuick

// 手绘矢量图标：与复选框对号同笔触语言（圆头圆角），颜色任意指定，
// 不依赖 MultiEffect 染色（该方案在此 Qt 栈实测无效：软件渲染填色块，真机渲染不染色）
Item {
    id: root
    property string kind: "check"   // check | x | chip
    property color color: "#000000"
    property int iconSize: 20

    implicitWidth: iconSize
    implicitHeight: iconSize

    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.strokeStyle = root.color
            ctx.lineCap = "round"
            ctx.lineJoin = "round"
            if (root.kind === "check") {
                ctx.lineWidth = Math.max(2, width * 0.11)
                ctx.beginPath()
                ctx.moveTo(width * 0.22, height * 0.52)
                ctx.lineTo(width * 0.43, height * 0.72)
                ctx.lineTo(width * 0.78, height * 0.28)
                ctx.stroke()
            } else if (root.kind === "x") {
                ctx.lineWidth = Math.max(2, width * 0.11)
                ctx.beginPath()
                ctx.moveTo(width * 0.25, height * 0.25)
                ctx.lineTo(width * 0.75, height * 0.75)
                ctx.moveTo(width * 0.75, height * 0.25)
                ctx.lineTo(width * 0.25, height * 0.75)
                ctx.stroke()
            } else if (root.kind === "chip") {
                var u = width / 24
                ctx.lineWidth = Math.max(1.5, u * 1.8)
                ctx.strokeRect(4 * u, 4 * u, 16 * u, 16 * u)
                ctx.strokeRect(9 * u, 9 * u, 6 * u, 6 * u)
                ctx.beginPath()
                var pins = [[15, 2, 15, 0], [15, 22, 15, 24],
                            [2, 15, 0, 15], [2, 9, 0, 9],
                            [22, 15, 24, 15], [22, 9, 24, 9],
                            [9, 2, 9, 0], [9, 22, 9, 24]]
                for (var i = 0; i < pins.length; i++) {
                    var p = pins[i]
                    ctx.moveTo(p[0] * u, p[1] * u)
                    ctx.lineTo(p[2] * u, p[3] * u)
                }
                ctx.stroke()
            }
        }
    }
    Connections {
        target: root
        function onColorChanged() { canvas.requestPaint() }
    }
}
