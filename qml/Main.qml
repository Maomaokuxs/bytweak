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
    property var navFull: [
        { "name": "总览", "page": 0, "keys": "总览 首页 概览 状态 仪表盘 主机 内存 硬盘 home dashboard" },
        { "name": "时区设置", "page": 1, "keys": "时区 时间 时钟 日期 timezone" },
        { "name": "GRUB 配置", "page": 2, "keys": "grub 引导 开机 启动菜单 主题 boot" },
        { "name": "显卡与硬件加速", "page": 3, "keys": "显卡 gpu 驱动 硬解 编解码 nvidia amd intel 加速" },
        { "name": "鼠标指针样式", "page": 4, "keys": "鼠标 指针 光标 主题 mouse cursor" },
        { "name": "软件包管理", "page": 5, "keys": "软件包 安装 copr 软件源 仓库 rpm fusion repo dnf" },
        { "name": "Fcitx 输入法", "page": 6, "keys": "输入法 拼音 主题 fcitx input" },
        { "name": "桌面组件", "page": 7, "keys": "桌面 通知 顶栏 waybar quickshell mako dunst 自启 niri" },
        { "name": "niri 快捷键", "page": 8, "keys": "niri 快捷键 键位 热键 按键 hotkey keybind 快捷键位" },
        { "name": "服务管理", "page": 9, "keys": "服务 自启 开机 systemctl systemd service 启动 停止" },
        { "name": "Flatpak 管理", "page": 10, "keys": "flatpak 应用 沙盒 flathub 安装 卸载 更新" },
        { "name": "DNF 调优", "page": 11, "keys": "dnf 调优 下载 镜像 缓存 并行 fastestmirror" },
        { "name": "默认应用设置", "page": 12, "keys": "默认应用 浏览器 文件管理器 默认程序 打开方式 mime" },
        { "name": "内核管理", "page": 13, "keys": "内核 kernel 删除 旧内核 默认启动 grubby boot" },
        { "name": "主机名", "page": 14, "keys": "主机名 hostname 电脑名 改名" }
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

    function gotoPage(page) {
        if (searchField.displayText !== "")
            searchField.clear()
        searchField.focus = false
        stack.currentIndex = page
        syncNavHighlight()
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
            function onNavigate(index) { root.gotoPage(index) }
        }

        AppDialog { id: sysWarnDlg }

        Component.onCompleted: {
            if (dash.isAtomic) {
                root.navFull = root.navFull.filter(function (e) { return e.page !== 11 && e.page !== 13 })
                nav.model = root.navFull
                syncNavHighlight()
            }
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
                TimezonePage {}
                GrubPage {}
                GpuPage {}
                CursorPage {}
                RepoPage {}
                FcitxPage {}
                DesktopPage {}
                NiriKeysPage {}
                ServicePage {}
                FlatpakPage {}
                DnfPage {}
                DefaultAppsPage {}
                KernelPage {}
                HostnamePage {}

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
