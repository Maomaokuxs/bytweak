import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 仪表盘主页：系统硬件整行卡 + 小方块状态卡（流式排），可自定义显示
ColumnLayout {
    spacing: 0

    component SquareCard: ItemDelegate {
        property string cardId: ""
        property string cardTitle: ""
        property string cardValue: ""
        implicitHeight: 104
        // 可跳转标识（GNOME HIG：链到其他视图的行尾加右向箭头）
        Label {
            text: "›"
            anchors.right: parent.right
            anchors.rightMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            font.pixelSize: 22
            opacity: 0.35
        }
        background: Rectangle {
            color: theme.cardBg
            border.color: hovered ? theme.accent : theme.cardBorder
            radius: 14
        }
        contentItem: ColumnLayout {
            spacing: 6
            Label { text: cardTitle; font.pixelSize: 12; opacity: 0.6 }
            Label {
                text: cardValue
                font.pixelSize: 14
                font.bold: true
                renderType: Text.NativeRendering
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                elide: Text.ElideRight
                rightPadding: 20
                Layout.fillWidth: true
                Layout.fillHeight: true
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    function dashTitle(id) {
        for (var i = 0; i < dash.allCards.length; i++)
            if (dash.allCards[i].id === id) return dash.allCards[i].title
        return id
    }

    function dashValue(id) {
        if (id === "timezone") return tz.statusText.replace("当前系统时区：", "")
        if (id === "grub")
            return (grub.themeList.length > 0 && grub.currentThemeIndex >= 0) ? grub.themeList[grub.currentThemeIndex] : "—"
        if (id === "gpu") return gpu.statusText
        if (id === "cursor")
            return (cursor.themeList.length > 0 && cursor.currentThemeIndex >= 0) ? cursor.themeList[cursor.currentThemeIndex] : "—"
        if (id === "repo") {
            if (repo.upgradesChecked && repo.upgradablePkgs.length > 0)
                return repo.upgradablePkgs.length + " 个可更新"
            var on = repo.repoList.filter(function (r) { return r.enabled }).length
            return on + " / " + repo.repoList.length + " 已启用"
        }
        if (id === "fcitx") {
            var light = "", dark = ""
            if (fcitx.themeList.length > 0) {
                if (fcitx.lightThemeIndex >= 0) light = fcitx.themeList[fcitx.lightThemeIndex]
                if (fcitx.darkThemeIndex >= 0) dark = fcitx.themeList[fcitx.darkThemeIndex]
            }
            return (light || dark) ? light + (dark && dark !== light ? " / " + dark : "") : "—"
        }
        if (id === "desktop") return desk.statusText
        if (id === "service") {
            var n = svc.serviceList.filter(function (s) { return s.active }).length
            return svc.serviceList.length > 0 ? n + " 运行中" : "—"
        }
        if (id === "flatpak")
            return flat.available ? flat.appList.length + " 个应用" : "未安装"
        if (id === "dnf") return dnf.supported ? "传统 DNF 可用" : "未检测到 DNF"
        return ""
    }


    ScrollView {
        id: dashScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: dashScroll.availableWidth
            spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Label { text: "总览"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }
                    Item { Layout.fillWidth: true }
                    AppButton {
                        id: customBtn
                        text: "自定义卡片"
                        flat: true
                        onClicked: customPopup.opened ? customPopup.close() : customPopup.open()
                        // 下拉复选框：从按钮下方弹出，点击外部/按 Esc 关闭
                        Popup {
                            id: customPopup
                            x: customBtn.width - width
                            y: customBtn.height + 6
                            width: 300
                            padding: 12
                            modal: false
                            dim: false
                            closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
                            background: Rectangle {
                                color: theme.popupBg
                                border.color: theme.popupBorder
                                radius: 12
                            }
                            contentItem: ColumnLayout {
                                spacing: 4
                                Label {
                                    text: "自定义卡片"
                                    font.pixelSize: 14
                                    font.bold: true
                                    renderType: Text.NativeRendering
                                    color: theme.textMain
                                    bottomPadding: 4
                                }
                                Repeater {
                                    model: dash.allCards
                                    delegate: AccentCheckBox {
                                        Layout.fillWidth: true
                                        text: modelData.title
                                        checked: dash.visibleCards.indexOf(modelData.id) !== -1
                                        onToggled: dash.setCardVisible(modelData.id, checked)
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    color: theme.cardBg
                    border.color: theme.cardBorder
                    radius: 14
                    implicitHeight: hwCol.implicitHeight + 28
                    ColumnLayout {
                        id: hwCol
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 6
                        Label { text: "系统硬件概览"; font.pixelSize: 12; opacity: 0.6 }
                        GridLayout {
                            id: hwGrid
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 16
                            rowSpacing: 6
                            Repeater {
                                model: dash.hardwareInfo
                                delegate: RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Layout.columnSpan: (modelData.label === "CPU" || modelData.label === "系统" || modelData.label === "硬盘 /") ? 2 : 1
                                    Label { text: modelData.label; opacity: 0.6; Layout.preferredWidth: 52 }
                                    Label {
                                        text: modelData.value
                                        font.bold: true
                                        renderType: Text.NativeRendering
                                        wrapMode: Text.WordWrap
                                        maximumLineCount: 2
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }
                                }
                            }
                        }
                    }
                }

                GridLayout {
                    id: cardGrid
                    Layout.fillWidth: true
                    columns: Math.max(1, dash.visibleCards.length <= 2 ? dash.visibleCards.length : 3)
                    columnSpacing: 12
                    rowSpacing: 12
                    property int remainder: dash.visibleCards.length % columns
                    Repeater {
                        model: dash.visibleCards
                        delegate: SquareCard {
                            required property string modelData
                            required property int index
                            Layout.fillWidth: true
                            Layout.columnSpan: (index === dash.visibleCards.length - 1 && cardGrid.remainder === 1) ? cardGrid.columns : 1
                            cardTitle: dashTitle(modelData)
                            cardValue: dashValue(modelData)
                            onClicked: dash.goPage(modelData)
                        }
                    }
                }

                Label {
                    text: "已隐藏全部卡片，可通过右上自定义恢复"
                    opacity: 0.6
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                    visible: dash.visibleCards.length === 0
                }
        }
    }

    Component.onCompleted: {
        tz.refresh()
        grub.refreshThemes()
        gpu.refresh()
        cursor.refresh()
        repo.refresh()
        repo.refreshUpgrades()
        fcitx.refresh()
        desk.refresh()
        svc.refresh()
        flat.refresh()
        dnf.refresh()
    }
}
