import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// DNF 调优页：/etc/dnf/dnf.conf [main] 常用开关（内容滚动，底栏固定）
// 无传统 DNF 时仅展示说明（原子系统下本页入口自动隐藏）。
ColumnLayout {
    spacing: 0

    property string parallelText: dnf.settings["max_parallel_downloads"] || "10"
    property string installonlyText: dnf.settings["installonly_limit"] || "3"
    property bool fastestmirrorOn: dnf.settings["fastestmirror"] !== "false"
    property bool keepcacheOn: dnf.settings["keepcache"] === "true"
    property bool cleanReqOn: dnf.settings["clean_requirements_on_remove"] !== "false"
    property bool bestOn: dnf.settings["best"] !== "false"

    AppDialog { id: msgDlg }
    Connections {
        target: dnf
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.open()
        }
    }

    ScrollView {
        id: dnfScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: dnfScroll.availableWidth
            spacing: 12

            Label { text: "DNF 调优"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }

            Label {
                text: "未检测到传统 DNF（/etc/dnf/dnf.conf 不存在），暂无可调项。"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                opacity: 0.7
                visible: !dnf.supported
            }

            GroupBox {
                title: "下载"
                Layout.fillWidth: true
                visible: dnf.supported
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Label { text: "并行下载数"; Layout.preferredWidth: 80 }
                        AppTextField {
                            Layout.maximumWidth: 120
                            text: parallelText
                            validator: IntValidator { bottom: 1; top: 20 }
                            inputMethodHints: Qt.ImhDigitsOnly
                            onTextChanged: parallelText = text
                        }
                        Label { text: "1~20，默认 10"; opacity: 0.6; font.pixelSize: 12 }
                    }
                    AccentCheckDelegate {
                        Layout.fillWidth: true
                        text: "自动选择最快镜像（fastestmirror）"
                        checked: fastestmirrorOn
                        enabled: !dnf.busy
                        onToggled: fastestmirrorOn = checked
                    }
                }
            }

            GroupBox {
                title: "缓存与事务"
                Layout.fillWidth: true
                visible: dnf.supported
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8
                    AccentCheckDelegate {
                        Layout.fillWidth: true
                        text: "保留下载缓存（keepcache）"
                        checked: keepcacheOn
                        enabled: !dnf.busy
                        onToggled: keepcacheOn = checked
                    }
                    AccentCheckDelegate {
                        Layout.fillWidth: true
                        text: "卸载时清理无用依赖（clean_requirements_on_remove）"
                        checked: cleanReqOn
                        enabled: !dnf.busy
                        onToggled: cleanReqOn = checked
                    }
                    AccentCheckDelegate {
                        Layout.fillWidth: true
                        text: "优先最新版本（best）"
                        checked: bestOn
                        enabled: !dnf.busy
                        onToggled: bestOn = checked
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12
                        Label { text: "旧内核保留"; Layout.preferredWidth: 80 }
                        AppTextField {
                            Layout.maximumWidth: 120
                            text: installonlyText
                            validator: IntValidator { bottom: 2; top: 10 }
                            inputMethodHints: Qt.ImhDigitsOnly
                            onTextChanged: installonlyText = text
                        }
                        Label { text: "2~10，默认 3"; opacity: 0.6; font.pixelSize: 12 }
                    }
                }
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 16
        Layout.rightMargin: 16
        Layout.topMargin: 8
        Layout.bottomMargin: 12
        Layout.alignment: Qt.AlignRight
        spacing: 8
        BusyIndicator { visible: dnf.busy; running: dnf.busy }
        Button {
            text: "刷新"
            flat: true
            enabled: !dnf.busy && dnf.supported
            onClicked: dnf.refresh()
        }
        Button {
            text: "应用"
            highlighted: true
            Layout.preferredWidth: 120
            enabled: !dnf.busy && dnf.supported
            onClicked: dnf.apply({
                "max_parallel_downloads": parallelText,
                "installonly_limit": installonlyText,
                "fastestmirror": fastestmirrorOn ? "true" : "false",
                "keepcache": keepcacheOn ? "true" : "false",
                "clean_requirements_on_remove": cleanReqOn ? "true" : "false",
                "best": bestOn ? "true" : "false"
            })
        }
    }

    Component.onCompleted: dnf.refresh()
}
