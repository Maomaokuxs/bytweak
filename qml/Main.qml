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

    // 极简导航：竖线条 + 文字 + 选中阴影衬底（附关键字供搜索过滤）
    // 同类功能已合并为选项卡：导航 8 项，组内顶部 TabBar 切换
    property var navFull: [
        { "name": "总览", "page": 0, "keys": "总览 首页 概览 状态 仪表盘 主机 内存 硬盘 home dashboard" },
        { "name": "系统设置", "page": 1, "keys": "系统设置 时区 时间 时钟 日期 timezone 主机名 hostname 电脑名" },
        { "name": "启动管理", "page": 2, "keys": "启动管理 grub 引导 开机 启动菜单 主题 boot 内核 kernel 旧内核 grubby" },
        { "name": "显卡与硬件加速", "page": 3, "keys": "显卡 gpu 驱动 硬解 编解码 nvidia amd intel 加速" },
        { "name": "输入设备", "page": 4, "keys": "输入设备 输入法 拼音 fcitx input 鼠标 指针 光标 mouse cursor" },
        { "name": "软件管理", "page": 5, "keys": "软件管理 软件包 安装 copr 软件源 仓库 rpm fusion repo dnf flatpak 沙盒 flathub 调优 镜像 缓存 并行" },
        { "name": "桌面环境", "page": 6, "keys": "桌面环境 桌面 通知 顶栏 waybar quickshell mako dunst 自启 niri 快捷键 热键 hotkey keybind 默认应用 打开方式 mime" },
        { "name": "服务管理", "page": 7, "keys": "服务 自启 开机 systemctl systemd service 启动 停止" }
    ]

    function filterNav(q) {
        q = q.trim().toLowerCase()
        var res = []
        for (var i = 0; i < navFull.length; i++) {
            var e = navFull[i]
            if (!q || e.name.toLowerCase().indexOf(q) !== -1 || e.keys.toLowerCase().indexOf(q) !== -1)
                res.push(e)
        }
        nav.model = res
        syncNavHighlight()
    }

    function syncNavHighlight() {
        for (var j = 0; j < nav.count; j++) {
            if (nav.model[j].page === stack.currentIndex) {
                nav.currentIndex = j
                return
            }
        }
        nav.currentIndex = -1
    }

    function gotoPage(page, sub) {
        if (searchField.displayText !== "")
            searchField.clear()
        searchField.focus = false
        stack.currentIndex = page
        syncNavHighlight()
        if (sub !== undefined && sub !== null) {
            const child = stack.children[page]
            if (child && typeof child.showTab === "function")
                child.showTab(sub)
        }
    }

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

        Shortcut {
            sequence: "Ctrl+K"
            context: Qt.ApplicationShortcut
            onActivated: searchField.forceActiveFocus()
        }

        ColumnLayout {
            Layout.preferredWidth: 200
            Layout.maximumWidth: 200
            Layout.fillHeight: true
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 6
                TextField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholderText: "搜索设置…"
                    placeholderTextColor: theme.textSub
                    color: theme.textMain
                    background: Rectangle {
                        radius: 8
                        color: theme.boxDisabledBg
                    }
                    onTextChanged: root.filterNav(text)
                    Keys.onEscapePressed: {
                        clear()
                        focus = false
                    }
                }
                ToolButton {
                    text: "✕"
                    flat: true
                    visible: searchField.displayText !== ""
                    onClicked: searchField.clear()
                }
            }

            Label {
                text: "无匹配设置"
                opacity: 0.6
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
                visible: nav.count === 0
            }

        ListView {
            id: nav
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.navFull
            currentIndex: 0
            spacing: 4
            delegate: ItemDelegate {
                id: navDelegate
                width: nav.width
                topPadding: 11
                bottomPadding: 11
                highlighted: ListView.isCurrentItem
                onClicked: root.gotoPage(modelData.page)
                background: Rectangle {
                    radius: 8
                    color: theme.accent
                    opacity: navDelegate.highlighted ? 0.12 : 0.0
                    layer.enabled: true
                    layer.effect: MultiEffect {
                        shadowEnabled: true
                        shadowColor: "#1a000000"
                        shadowOpacity: 0.4
                        shadowHorizontalOffset: 0
                        shadowVerticalOffset: 2
                        blurMax: 16
                    }
                    Behavior on opacity {
                        NumberAnimation { duration: 260; easing.type: Easing.InOutQuad }
                    }
                }
                contentItem: RowLayout {
                    spacing: 10
                    Rectangle {
                        width: 3
                        Layout.fillHeight: true
                        radius: 1.5
                        color: navDelegate.highlighted ? theme.accent : "transparent"
                        Behavior on color {
                            ColorAnimation { duration: 260; easing.type: Easing.InOutQuad }
                        }
                    }
                    Label {
                        text: modelData.name
                        color: navDelegate.highlighted ? theme.accent : theme.textMain
                        font.bold: navDelegate.highlighted
                        renderType: Text.NativeRendering
                        Layout.fillWidth: true
                        verticalAlignment: Text.AlignVCenter
                        Behavior on color {
                            ColorAnimation { duration: 260; easing.type: Easing.InOutQuad }
                        }
                    }
                }
            }
        }
        }

        Connections {
            target: dash
            function onNavigate(page, sub) { root.gotoPage(page, sub) }
        }

        AppDialog { id: sysWarnDlg }

        Component.onCompleted: {
            if (!dash.isFedora) {
                sysWarnDlg.title = "系统不受支持"
                sysWarnDlg.body = "检测到当前系统为“" + dash.osName + "”，本工具专为 Fedora 设计，部分功能可能不可用或执行失败。"
                sysWarnDlg.open()
            }
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
                currentIndex: 0

                DashboardPage {}
                SystemTabsPage {}
                BootTabsPage {}
                GpuPage {}
                InputTabsPage {}
                SoftwareTabsPage {}
                DesktopTabsPage {}
                ServicePage {}

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
