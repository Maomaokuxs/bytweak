import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 修改 niri 快捷键：勾选修饰键 + 选择/输入主键，实时预览组合。
// 保存后由后端把原键注释停用并写入新键。
Dialog {
    id: root
    anchors.centerIn: parent
    modal: true
    title: "修改快捷键"

    property string rawKeys: ""
    property string funcDesc: ""
    property string usedTitle: ""
    property var mods: ({ "Super": false, "Ctrl": false, "Alt": false, "Shift": false })
    property string keyName: ""

    property string rawDisplay: {
        var parts = (rawKeys || "").split("+")
        var out = []
        for (var i = 0; i < parts.length; i++) {
            var p = parts[i] === "Mod" ? "Super" : parts[i]
            out.push(labelFor(p))
        }
        return out.join("+")
    }

    // 键名 -> 符号（下拉里能查到就用符号，否则原样）
    function labelFor(name) {
        for (var i = 0; i < niri.keyChoices.length; i++)
            if (niri.keyChoices[i].value === name)
                return niri.keyChoices[i].label
        return name
    }
    // 用户可能输入的是符号，写回前还原成 XKB 名
    function resolveKey() {
        for (var i = 0; i < niri.keyChoices.length; i++)
            if (niri.keyChoices[i].label === keyName)
                return niri.keyChoices[i].value
        return keyName
    }

    property string composed: {
        var parts = []
        if (mods.Super) parts.push("Super")
        if (mods.Ctrl) parts.push("Ctrl")
        if (mods.Alt) parts.push("Alt")
        if (mods.Shift) parts.push("Shift")
        if (keyName !== "") parts.push(resolveKey())
        return parts.join("+")
    }
    property string composedDisplay: {
        var parts = []
        if (mods.Super) parts.push("Super")
        if (mods.Ctrl) parts.push("Ctrl")
        if (mods.Alt) parts.push("Alt")
        if (mods.Shift) parts.push("Shift")
        if (keyName !== "") parts.push(labelFor(resolveKey()))
        return parts.join("+")
    }

    function openFor(keys, desc, title) {
        rawKeys = keys
        funcDesc = desc
        usedTitle = title
        var parts = (keys || "").split("+")
        var st = { "Super": false, "Ctrl": false, "Alt": false, "Shift": false }
        var rest = []
        for (var i = 0; i < parts.length; i++) {
            var p = parts[i] === "Mod" ? "Super" : parts[i]
            if (p === "")
                continue
            if (st.hasOwnProperty(p))
                st[p] = true
            else
                rest.push(p)
        }
        mods = st
        keyName = rest.join("+")
        keyCombo.editText = labelFor(keyName)
        open()
    }

    background: Rectangle {
        color: theme.popupBg
        border.color: theme.popupBorder
        radius: 12
    }
    header: Label {
        text: root.title
        font.pixelSize: 15
        font.bold: true
        renderType: Text.NativeRendering
        color: theme.textMain
        padding: 16
        bottomPadding: 4
    }

    contentItem: ColumnLayout {
        spacing: 10

        Label {
            Layout.fillWidth: true
            Layout.preferredWidth: 420
            text: root.funcDesc
            font.bold: true
            wrapMode: Text.WordWrap
            color: theme.textMain
        }

        Label {
            Layout.fillWidth: true
            text: "原按键：" + root.rawDisplay + "（保存后注释保留）"
            opacity: 0.6
            font.pixelSize: 12
            color: theme.textMain
        }

        Label {
            text: "修饰键"
            font.bold: true
            opacity: 0.7
            color: theme.textMain
        }
        RowLayout {
            spacing: 14
            Repeater {
                model: ["Super", "Ctrl", "Alt", "Shift"]
                delegate: CheckBox {
                    text: modelData
                    checked: root.mods[modelData]
                    onToggled: {
                        var m = Object.assign({}, root.mods)
                        m[modelData] = checked
                        root.mods = m
                    }
                }
            }
        }

        Label {
            text: "主键（可从列表选，也可直接输入）"
            font.bold: true
            opacity: 0.7
            color: theme.textMain
        }
        AppComboBox {
            id: keyCombo
            Layout.fillWidth: true
            editable: true
            model: niri.keyChoices
            textRole: "label"
            valueRole: "value"
            onActivated: {
                root.keyName = currentValue
                editText = currentText
            }
            onEditTextChanged: {
                if (activeFocus)
                    root.keyName = editText
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: preview.implicitHeight + 16
            radius: 8
            color: theme.boxDisabledBg
            Label {
                id: preview
                anchors.centerIn: parent
                text: root.composed === "" ? "新按键：请选择修饰键和主键" : "新按键：" + root.composedDisplay
                font.family: "monospace"
                font.bold: true
                color: theme.textMain
            }
        }
    }

    footer: RowLayout {
        spacing: 8
        Item { Layout.fillWidth: true }
        AppButton {
            text: "取消"
            flat: true
            Layout.preferredWidth: 90
            onClicked: root.reject()
        }
        AppButton {
            text: "保存"
            highlighted: true
            Layout.preferredWidth: 100
            enabled: root.composed !== "" && root.composed !== root.rawDisplay
            onClicked: {
                niri.setKey(root.rawKeys, root.composed)
                root.accept()
            }
        }
    }
}
