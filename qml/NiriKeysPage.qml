import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// niri 快捷键页：读取 niri 配置键位、翻译成中文作用，按功能分类展示（内容滚动）
ColumnLayout {
    id: root
    spacing: 0

    property string keyQuery: ""

    // 按分类过滤后的分组（搜索命中键位/作用/英文名）
    property var filteredGroups: {
        var q = keyQuery.trim().toLowerCase()
        var out = []
        for (var i = 0; i < niri.groups.length; i++) {
            var g = niri.groups[i]
            var list = g.items
            if (q) {
                list = list.filter(function (k) {
                    return k.keys.toLowerCase().indexOf(q) !== -1
                        || k.desc.toLowerCase().indexOf(q) !== -1
                        || k.title.toLowerCase().indexOf(q) !== -1
                })
            }
            if (list.length > 0)
                out.push({ "name": g.name, "items": list })
        }
        return out
    }
    property int shownCount: {
        var n = 0
        for (var i = 0; i < filteredGroups.length; i++)
            n += filteredGroups[i].items.length
        return n
    }

    AppDialog { id: msgDlg }
    NiriKeyEditDialog { id: editDlg }
    Connections {
        target: niri
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    Item {
        id: viewport
        Layout.fillWidth: true
        Layout.fillHeight: true

        Flickable {
            id: keyFlick
            anchors.fill: parent
            anchors.rightMargin: 16
            clip: true
            contentWidth: width
            contentHeight: contentCol.implicitHeight + 32
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.VerticalFlick

            ColumnLayout {
                id: contentCol
                x: 16
                y: 16
                width: keyFlick.width - 32
                spacing: 14

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ColumnLayout {
                    spacing: 2
                    Label {
                        text: "niri 快捷键"
                        font.pixelSize: 22
                        font.bold: true
                        color: theme.textMain
                        renderType: Text.NativeRendering
                    }
                    Label {
                        text: "以下键位读自你的 niri 配置，Mod 显示为 Super"
                        opacity: 0.55
                        font.pixelSize: 12
                        color: theme.textMain
                    }
                }
                Item { Layout.fillWidth: true }
                Label {
                    text: "共 " + niri.keybinds.length + " 条 · 显示 " + shownCount + " 条"
                    opacity: 0.55
                    font.pixelSize: 12
                    color: theme.textMain
                    Layout.alignment: Qt.AlignTop
                }
            }

            AppTextField {
                objectName: "keySearch"
                Layout.fillWidth: true
                Layout.maximumWidth: 420
                placeholderText: "搜索键位或功能，如 工作区、截图、Super+T…"
                color: theme.textMain
                leftPadding: 10
                rightPadding: 10
                onTextChanged: keyQuery = text
                Keys.onEscapePressed: {
                    clear()
                    focus = false
                }
            }

            Repeater {
                model: root.filteredGroups
                delegate: ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Rectangle {
                            Layout.preferredWidth: 3
                            Layout.preferredHeight: 14
                            radius: 1.5
                            color: theme.accent
                        }
                        Label {
                            text: modelData.name
                            font.bold: true
                            font.pixelSize: 14
                            color: theme.textMain
                            renderType: Text.NativeRendering
                        }
                        Label {
                            text: modelData.items.length + " 条"
                            opacity: 0.5
                            font.pixelSize: 12
                            color: theme.textMain
                        }
                        Item { Layout.fillWidth: true }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: groupCol.implicitHeight + 16
                        radius: 10
                        color: Qt.darker(theme.cardBg, 1.04)
                        border.color: theme.cardBorder
                        border.width: 1

                        ColumnLayout {
                            id: groupCol
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 2

                            Repeater {
                                model: modelData.items
                                delegate: Rectangle {
                                    id: row
                                    Layout.fillWidth: true
                                    implicitHeight: rowLayout.implicitHeight + 12
                                    radius: 6
                                    color: hover.hovered && !modelData.disabled
                                           ? Qt.darker(theme.cardBg, 1.11) : "transparent"
                                    opacity: modelData.disabled ? 0.55 : 1.0
                                    Behavior on color {
                                        ColorAnimation { duration: 260; easing.type: Easing.InOutQuad }
                                    }

                                    HoverHandler { id: hover }

                                    RowLayout {
                                        id: rowLayout
                                        anchors.fill: parent
                                        anchors.leftMargin: 8
                                        anchors.rightMargin: 8
                                        spacing: 12

                                        Rectangle {
                                            Layout.preferredWidth: 196
                                            Layout.alignment: Qt.AlignVCenter
                                            implicitHeight: keyText.implicitHeight + 10
                                            radius: 6
                                            color: theme.boxDisabledBg
                                            border.color: theme.cardBorder
                                            border.width: 1
                                            Label {
                                                id: keyText
                                                anchors.centerIn: parent
                                                width: parent.width - 12
                                                text: modelData.keys
                                                font.family: "monospace"
                                                font.bold: true
                                                font.pixelSize: 12
                                                horizontalAlignment: Text.AlignHCenter
                                                wrapMode: Text.Wrap
                                                color: theme.textMain
                                                renderType: Text.NativeRendering
                                            }
                                        }

                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 1
                                            Label {
                                                Layout.fillWidth: true
                                                text: modelData.disabled ? modelData.desc + "（已停用·原键保留）" : modelData.desc
                                                wrapMode: Text.WordWrap
                                                color: theme.textMain
                                                renderType: Text.NativeRendering
                                            }
                                            Label {
                                                Layout.fillWidth: true
                                                text: modelData.title
                                                wrapMode: Text.WordWrap
                                                opacity: 0.5
                                                font.pixelSize: 11
                                                visible: modelData.title !== "" && modelData.title !== modelData.desc
                                            }
                                        }

                                        Button {
                                            text: "编辑"
                                            flat: true
                                            visible: !modelData.disabled
                                            Layout.alignment: Qt.AlignVCenter
                                            onClicked: editDlg.openFor(modelData.rawKeys, modelData.desc, modelData.title)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Label {
                text: niri.keybinds.length === 0
                      ? "未找到 niri 快捷键，请确认 ~/.config/niri/config.kdl 存在"
                      : "没有匹配的键位，换个关键词试试"
                opacity: 0.6
                color: theme.textMain
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
                Layout.topMargin: 24
                visible: root.filteredGroups.length === 0
            }
            }
        }

        // 自绘纵向滚动条：Fluent 风格原生 ScrollBar 不渲染，故手绘
        Rectangle {
            id: track
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            anchors.margins: 6
            width: 6
            radius: 3
            color: "transparent"
            visible: keyFlick.contentHeight > keyFlick.height

            Rectangle {
                id: thumb
                width: parent.width
                radius: 3
                color: theme.textMuted
                opacity: dragArea.pressed ? 0.75 : 0.4
                height: Math.max(28, track.height * keyFlick.height / Math.max(keyFlick.contentHeight, 1))
                y: (track.height - height) * (keyFlick.contentY / Math.max(keyFlick.contentHeight - keyFlick.height, 1))
            }
            MouseArea {
                id: dragArea
                anchors.fill: parent
                onPositionChanged: {
                    if (!pressed || track.height <= thumb.height)
                        return
                    var maxY = track.height - thumb.height
                    var frac = Math.max(0, Math.min(1, (mouseY - thumb.height / 2) / maxY))
                    keyFlick.contentY = frac * Math.max(keyFlick.contentHeight - keyFlick.height, 0)
                }
            }
        }
    }

    // 底栏固定
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: 1
        color: theme.cardBorder
    }
    RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 16
        Layout.rightMargin: 16
        Layout.topMargin: 8
        Layout.bottomMargin: 12
        spacing: 8
        Label {
            text: "来源 ~/.config/niri/config.kdl"
            opacity: 0.5
            font.pixelSize: 11
            color: theme.textMain
        }
        Item { Layout.fillWidth: true }
        Button { text: "刷新"; flat: true; onClicked: niri.refresh() }
    }

    Component.onCompleted: niri.refresh()
}
