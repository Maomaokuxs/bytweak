import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects

// 主壳：左侧导航 + 右侧 StackView（切换带滑动淡入过渡）
ApplicationWindow {
    id: root
    visible: true
    width: 980
    height: 680
    minimumWidth: 820
    minimumHeight: 560
    title: "Fedora Tweak Tool"

    // 极简导航：竖线条 + 文字 + 选中阴影衬底
    property var navModel: ["总览", "时区设置", "GRUB 配置", "显卡与硬件加速", "鼠标指针样式", "软件源管理", "Fcitx 输入法", "桌面组件"]

    // 切页过渡：新页淡入 + 微缩回弹（只作用于进入页；
    // StackLayout 自动隐藏旧页，结构上不可能重叠；scale 是渲染变换，不影响布局）
    NumberAnimation {
        id: fadeAnim
        target: null
        property: "opacity"
        from: 0.0
        to: 1.0
        duration: 180
        easing.type: Easing.OutCubic
    }
    NumberAnimation {
        id: zoomAnim
        target: null
        property: "scale"
        from: 0.985
        to: 1.0
        duration: 180
        easing.type: Easing.OutCubic
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        ListView {
            id: nav
            Layout.preferredWidth: 180
            Layout.maximumWidth: 260
            Layout.fillHeight: true
            model: root.navModel
            currentIndex: 0
            spacing: 4
            delegate: ItemDelegate {
                id: navDelegate
                width: nav.width
                topPadding: 11
                bottomPadding: 11
                highlighted: ListView.isCurrentItem
                onClicked: nav.currentIndex = index
                background: Rectangle {
                    radius: 8
                    color: navDelegate.highlighted ? theme.accent : "transparent"
                    opacity: navDelegate.highlighted ? 0.12 : 0.0
                    layer.enabled: navDelegate.highlighted
                    layer.effect: MultiEffect {
                        shadowEnabled: true
                        shadowColor: "#1a000000"
                        shadowOpacity: 0.4
                        shadowHorizontalOffset: 0
                        shadowVerticalOffset: 2
                        blurMax: 16
                    }
                    Behavior on opacity { NumberAnimation { duration: 140 } }
                }
                contentItem: RowLayout {
                    spacing: 10
                    Rectangle {
                        width: 3
                        Layout.fillHeight: true
                        radius: 1.5
                        color: navDelegate.highlighted ? theme.accent : "transparent"
                    }
                    Label {
                        text: modelData
                        color: navDelegate.highlighted ? theme.accent : theme.textMain
                        font.bold: navDelegate.highlighted
                        renderType: Text.NativeRendering
                        Layout.fillWidth: true
                        verticalAlignment: Text.AlignVCenter
                    }
                }
            }
        }

        Connections {
            target: dash
            function onNavigate(index) { nav.currentIndex = index }
        }

        // 内容阴影卡片底
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Rectangle {
                anchors.fill: parent
                color: theme.cardBg
                border.color: theme.cardBorder
                radius: 14
                layer.enabled: true
                layer.effect: MultiEffect {
                    shadowEnabled: true
                    shadowColor: "#1a000000"
                    shadowOpacity: 0.35
                    shadowHorizontalOffset: 0
                    shadowVerticalOffset: 6
                    blurMax: 32
                }
            }

            StackLayout {
                id: stack
                anchors.fill: parent
                currentIndex: nav.currentIndex

                DashboardPage {}
                TimezonePage {}
                GrubPage {}
                GpuPage {}
                CursorPage {}
                RepoPage {}
                FcitxPage {}
                DesktopPage {}

                onCurrentIndexChanged: {
                    const page = stack.children[stack.currentIndex]
                    if (!page)
                        return
                    fadeAnim.stop()
                    zoomAnim.stop()
                    fadeAnim.target = page
                    zoomAnim.target = page
                    page.opacity = 0.0
                    page.scale = 0.985
                    fadeAnim.start()
                    zoomAnim.start()
                }
            }
        }
    }
}
