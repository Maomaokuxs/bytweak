import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 软件包管理页：系统更新 + 统一搜索与安装（官方/COPR/第三方分组卡）+ 系统清理；
// 仓库启闭与推荐源收进右侧抽屉（软件源配置按钮打开）。
ColumnLayout {
    spacing: 0

    property string repoQuery: ""
    property int repoFilter: 0
    property bool repoCoprOnly: false
    property string coprExpanded: ""
    property bool hasSearched: false
    property var officialPkgList: repo.pkgResults.filter(function(p) { return p.source === "official" })
    property var thirdPkgList: repo.pkgResults.filter(function(p) { return p.source === "thirdparty" })
    property var coprPkgList: repo.pkgResults.filter(function(p) { return p.source === "copr" })
    property int resultFilter: 0
    property bool resultsExpanded: true
    property var filteredRepos: repo.repoList.filter(function (r) {
        if (repoCoprOnly && r.id.indexOf("copr:") !== 0)
            return false
        if (repoFilter === 1 && !r.enabled)
            return false
        if (repoFilter === 2 && r.enabled)
            return false
        var q = repoQuery.trim().toLowerCase()
        if (!q)
            return true
        return r.name.toLowerCase().indexOf(q) !== -1 || r.id.toLowerCase().indexOf(q) !== -1
    })
    property var filteredRecommended: repo.recommendedList.filter(function (r) {
        if (repoFilter === 1 && !r.installed)
            return false
        if (repoFilter === 2 && r.installed)
            return false
        var q = repoQuery.trim().toLowerCase()
        if (!q)
            return true
        return r.label.toLowerCase().indexOf(q) !== -1
    })

    AppDialog {
        id: msgDlg
    }
    OpLogDialog {
        id: logDlg
    }
    Connections {
        target: repo
        function onMessage(title, body, isError) {
            msgDlg.title = title
            msgDlg.body = body
            msgDlg.details = repo.lastOutput
            msgDlg.open()
        }
        function onSearchTimeout(label) {
            timeoutDlg.timeoutLabel = label
            timeoutDlg.open()
        }
    }

    // 搜索超时提示：30 秒未完成，让用户选择继续等待或终止
    Dialog {
        id: timeoutDlg
        anchors.centerIn: parent
        modal: true
        title: "搜索时间较长"
        property string timeoutLabel: "搜索"
        background: Rectangle {
            color: theme.popupBg
            border.color: theme.popupBorder
            radius: 12
        }
        header: Label {
            text: timeoutDlg.title
            font.pixelSize: 15
            font.bold: true
            color: theme.textMain
            padding: 16
            bottomPadding: 4
        }
        contentItem: ColumnLayout {
            spacing: 12
            Label {
                text: "“" + timeoutDlg.timeoutLabel + "”已执行 2 分钟仍未完成，是否继续等待？"
                color: theme.textMuted
                wrapMode: Text.WordWrap
                Layout.preferredWidth: 320
            }
            RowLayout {
                Layout.alignment: Qt.AlignRight
                spacing: 8
                AppButton {
                    text: "终止搜索"
                    onClicked: {
                        repo.cancelSearch()
                        timeoutDlg.close()
                    }
                }
                AppButton {
                    text: "继续等待"
                    highlighted: true
                    onClicked: timeoutDlg.close()
                }
            }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: 16
        Layout.rightMargin: 16
        Layout.topMargin: 12
        Layout.bottomMargin: 4
        spacing: 8
        Label { text: "软件包管理"; font.pixelSize: 22; font.bold: true; renderType: Text.NativeRendering }
        Label {
            text: "搜索安装软件包、管理软件源，检查系统更新"
            opacity: 0.6
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        Item { Layout.fillWidth: true }
        Label {
            visible: (repo.busy || repo.coprBusy) && repo.busyLabel !== ""
            text: repo.busyLabel
            opacity: 0.7
            font.pixelSize: 12
            color: theme.textMuted
        }
        BusyIndicator { visible: repo.busy; running: repo.busy }
        AppButton { text: "操作日志"; flat: true; onClicked: logDlg.open() }
        AppButton { text: "软件源配置"; onClicked: repoDrawer.open() }
    }

    ScrollView {
        id: repoScroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        padding: 16
        ColumnLayout {
            width: repoScroll.availableWidth
            spacing: 12

                GroupBox {
                    title: "搜索与安装"
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            SearchBox {
                                id: uniQuery
                                Layout.fillWidth: true
                                placeholderText: "搜索软件包或 COPR 项目，如 fastfetch…"
                                onAccepted: {
                                    hasSearched = true
                                    coprExpanded = ""
                                    resultsExpanded = true
                                    repo.unifiedSearch(text)
                                }
                                Keys.onEscapePressed: {
                                    clear()
                                    focus = false
                                }
                            }
                            AppButton {
                                text: "搜索"
                                enabled: !repo.coprBusy
                                onClicked: {
                                    hasSearched = true
                                    coprExpanded = ""
                                    resultsExpanded = true
                                    repo.unifiedSearch(uniQuery.text)
                                }
                            }
                            AppButton {
                                text: resultsExpanded ? "收起" : "展开"
                                flat: true
                                visible: officialPkgList.length + thirdPkgList.length + coprPkgList.length + repo.coprResults.length > 0
                                onClicked: resultsExpanded = !resultsExpanded
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            visible: hasSearched
                            AppComboBox {
                                Layout.preferredWidth: 140
                                model: ["全部来源", "仅官方", "仅 COPR", "仅第三方"]
                                onActivated: resultFilter = index
                            }
                            Label {
                                text: "官方 " + officialPkgList.length + " · COPR 项目 " + repo.coprResults.length + " · 第三方 " + thirdPkgList.length
                                opacity: 0.6
                                font.pixelSize: 12
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            visible: repo.coprError !== ""
                            Label {
                                text: "⚠ COPR 不可用：" + repo.coprError
                                color: theme.codecErr
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                                font.pixelSize: 12
                            }
                            AppButton {
                                text: "重试"
                                flat: true
                                enabled: !repo.coprBusy
                                onClicked: repo.unifiedSearch(uniQuery.text)
                            }
                        }
                        BusyIndicator {
                            visible: repo.coprBusy
                            running: repo.coprBusy
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Component {
                            id: pkgRowDelegate
                            ColumnLayout {
                                spacing: 2
                                property string pkgName: modelData.name
                                property bool isInstalled: repo.installedPkgs.indexOf(pkgName) !== -1
                                RowLayout {
                                    spacing: 8
                                    Label {
                                        text: pkgName
                                        font.bold: true
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }
                                    AppButton {
                                        text: isInstalled ? "卸载" : "安装"
                                        enabled: !repo.busy
                                        onClicked: isInstalled ? repo.removePackage(pkgName) : repo.installPackage(pkgName)
                                    }
                                }
                                Label {
                                    text: modelData.version + " · " + modelData.repo
                                    opacity: 0.6
                                    font.pixelSize: 12
                                }
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: officialBox.implicitHeight + 24
                            visible: officialPkgList.length > 0 && resultsExpanded && (resultFilter === 0 || resultFilter === 1)
                            radius: 8
                            color: Qt.darker(theme.cardBg, 1.07)
                            border.color: theme.cardBorder
                            border.width: 1
                            ColumnLayout {
                                id: officialBox
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 4
                            RowLayout {
                                spacing: 8
                                Label {
                                    text: "官方"
                                    color: "#ffffff"
                                    font.pixelSize: 12
                                    leftPadding: 8
                                    rightPadding: 8
                                    topPadding: 2
                                    bottomPadding: 2
                                    background: Rectangle { color: "#2b7cd3"; radius: 4 }
                                }
                                Label {
                                    text: "官方软件包 · " + officialPkgList.length + " 个"
                                    font.bold: true
                                }
                            }
                            Repeater {
                                model: officialPkgList
                                delegate: pkgRowDelegate
                            }
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: coprBox.implicitHeight + 24
                            visible: (repo.coprResults.length > 0 || coprPkgList.length > 0) && resultsExpanded && (resultFilter === 0 || resultFilter === 2)
                            radius: 8
                            color: Qt.darker(theme.cardBg, 1.07)
                            border.color: theme.cardBorder
                            border.width: 1
                            ColumnLayout {
                                id: coprBox
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 8
                        RowLayout {
                            spacing: 8
                            visible: repo.coprResults.length > 0
                            Label {
                                text: "COPR"
                                color: "#ffffff"
                                font.pixelSize: 12
                                leftPadding: 8
                                rightPadding: 8
                                topPadding: 2
                                bottomPadding: 2
                                background: Rectangle { color: "#7b5cc9"; radius: 4 }
                            }
                            Label {
                                text: "COPR 项目 · " + repo.coprResults.length + " 个"
                                font.bold: true
                            }
                        }
                        Repeater {
                            model: repo.coprResults
                            delegate: ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                property string projFull: modelData.full
                                property bool isEnabled: repo.repoList.some(function(r) { return r.enabled && r.id.indexOf("copr:") === 0 && r.id.endsWith(":" + modelData.owner + ":" + modelData.project) })
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Label {
                                        text: projFull
                                        font.bold: true
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }
                                    AppButton {
                                        text: coprExpanded === projFull ? "收起" : "软件包"
                                        flat: true
                                        enabled: !repo.coprBusy
                                        onClicked: {
                                            if (coprExpanded === projFull) {
                                                coprExpanded = ""
                                            } else {
                                                coprExpanded = projFull
                                                repo.listCoprPackages(modelData.owner, modelData.project)
                                            }
                                        }
                                    }
                                    AppButton {
                                        text: isEnabled ? "已启用" : "启用"
                                        enabled: !repo.busy && !isEnabled
                                        onClicked: repo.enableCopr(modelData.owner, modelData.project)
                                    }
                                }
                                Label {
                                    text: modelData.description
                                    opacity: 0.6
                                    font.pixelSize: 12
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                    visible: modelData.description !== ""
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.leftMargin: 16
                                    spacing: 4
                                    visible: coprExpanded === projFull
                                    Repeater {
                                        model: coprExpanded === projFull ? repo.coprPackages : []
                                        delegate: ColumnLayout {
                                            spacing: 2
                                            property string pkgName: modelData
                                            property bool isInstalled: repo.installedPkgs.indexOf(pkgName) !== -1
                                            RowLayout {
                                                spacing: 8
                                                Label {
                                                    text: pkgName
                                                    Layout.fillWidth: true
                                                    elide: Text.ElideRight
                                                }
                                                AppButton {
                                                    text: isInstalled ? "卸载" : "安装"
                                                    flat: true
                                                    enabled: !repo.busy
                                                    onClicked: isInstalled ? repo.removePackage(pkgName) : repo.installPackage(pkgName)
                                                }
                                            }
                                            Label {
                                                property var hint: repo.officialHints[pkgName]
                                                property bool hasHint: hint !== undefined && hint.source !== undefined && hint.source !== "none" && hint.source !== "copr"
                                                text: hasHint && hint.source === "official" ? "官方源也有提供 (" + hint.repo + ")，建议优先官方安装" : "第三方源也有提供 (" + (hasHint ? hint.repo : "") + ")"
                                                opacity: 0.6
                                                font.pixelSize: 12
                                                visible: hasHint
                                            }
                                        }
                                    }
                                    Label {
                                        text: repo.coprBusy ? "正在加载包列表…" : "该项目暂无可用包"
                                        opacity: 0.6
                                        font.pixelSize: 12
                                        visible: repo.coprPackages.length === 0
                                    }
                                }
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            visible: coprPkgList.length > 0
                            Label {
                                text: "可直接从 COPR 源安装的包："
                                opacity: 0.6
                                font.pixelSize: 12
                            }
                            Repeater {
                                model: coprPkgList
                                delegate: pkgRowDelegate
                            }
                        }
                            }
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: thirdBox.implicitHeight + 24
                            visible: thirdPkgList.length > 0 && resultsExpanded && (resultFilter === 0 || resultFilter === 3)
                            radius: 8
                            color: Qt.darker(theme.cardBg, 1.07)
                            border.color: theme.cardBorder
                            border.width: 1
                            ColumnLayout {
                                id: thirdBox
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 4
                            RowLayout {
                                spacing: 8
                                Label {
                                    text: "第三方"
                                    color: "#ffffff"
                                    font.pixelSize: 12
                                    leftPadding: 8
                                    rightPadding: 8
                                    topPadding: 2
                                    bottomPadding: 2
                                    background: Rectangle { color: "#b26a1b"; radius: 4 }
                                }
                                Label {
                                    text: "第三方软件包 · " + thirdPkgList.length + " 个"
                                    font.bold: true
                                }
                            }
                            Repeater {
                                model: thirdPkgList
                                delegate: pkgRowDelegate
                            }
                            }
                        }
                        Label {
                            text: !hasSearched ? "输入关键词，同时搜索官方源软件包与 COPR 项目"
                                  : (repo.coprError !== "" ? "官方源也未找到；COPR 当前不可用，稍后可重试" : "官方、COPR、第三方都没找到，换个关键词试试")
                            opacity: 0.6
                            horizontalAlignment: Text.AlignHCenter
                            Layout.fillWidth: true
                            visible: officialPkgList.length === 0 && thirdPkgList.length === 0 && coprPkgList.length === 0 && repo.coprResults.length === 0 && !repo.coprBusy
                        }
                    }
                }

                GroupBox {
                    title: "系统更新"
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Label {
                                text: !repo.upgradesChecked ? (repo.coprBusy ? "正在检查更新…" : "尚未检查更新") : (repo.upgradablePkgs.length === 0 ? "系统已是最新" : "有 " + repo.upgradablePkgs.length + " 个软件包可更新")
                                Layout.fillWidth: true
                            }
                            AppButton {
                                text: "检查更新"
                                flat: true
                                enabled: !repo.coprBusy
                                onClicked: repo.refreshUpgrades()
                            }
                            AppButton {
                                text: "一键升级"
                                highlighted: true
                                enabled: !repo.busy && repo.upgradesChecked && repo.upgradablePkgs.length > 0
                                onClicked: repo.upgradeAll()
                            }
                        }
                        Repeater {
                            model: repo.upgradablePkgs.slice(0, 15)
                            delegate: Label {
                                text: modelData.name + "  " + modelData.version
                                opacity: 0.6
                                font.pixelSize: 12
                            }
                        }
                        Label {
                            text: "…等共 " + repo.upgradablePkgs.length + " 个"
                            opacity: 0.6
                            font.pixelSize: 12
                            visible: repo.upgradablePkgs.length > 15
                        }
                    }
                }

                GroupBox {
                    title: "系统清理"
                    Layout.fillWidth: true
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Label {
                                text: "软件包缓存占用：" + repo.cacheSize
                                Layout.fillWidth: true
                            }
                            AppButton {
                                text: "清理缓存"
                                flat: true
                                enabled: !repo.busy
                                onClicked: repo.cleanCache()
                            }
                            AppButton {
                                text: "自动移除孤包"
                                enabled: !repo.busy
                                onClicked: repo.autoremove()
                            }
                        }
                        Label {
                            text: "清理缓存释放磁盘空间；自动移除不再被任何软件需要的依赖包"
                            opacity: 0.6
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }
                }
        }
    }

    Drawer {
        id: repoDrawer
        edge: Qt.RightEdge
        width: Math.min(420, parent.width * 0.92)
        height: parent.height
        modal: true
        dim: true
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 8
            Label { text: "软件源配置"; font.pixelSize: 18; font.bold: true; renderType: Text.NativeRendering }
            SearchBox {
                Layout.fillWidth: true
                placeholderText: "搜索仓库名称或 ID…"
                onTextChanged: repoQuery = text
                Keys.onEscapePressed: {
                    clear()
                    focus = false
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                AppComboBox {
                    Layout.fillWidth: true
                    model: ["全部", "已启用", "未启用"]
                    onActivated: repoFilter = index
                }
                CheckBox {
                    text: "仅 COPR"
                    checked: repoCoprOnly
                    enabled: !repo.busy
                    onToggled: repoCoprOnly = checked
                }
            }
            ScrollView {
                id: drawerScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                padding: 12
                ColumnLayout {
                    width: drawerScroll.availableWidth
                    spacing: 8
                    Label {
                        text: "共 " + repo.repoList.length + " 个 · 显示 " + filteredRepos.length + " 个"
                        opacity: 0.6
                        font.pixelSize: 12
                    }
                    Repeater {
                        model: filteredRepos
                        delegate: AccentCheckDelegate {
                            Layout.fillWidth: true
                            text: modelData.name + "\n[" + modelData.id + "]"
                            checked: modelData.enabled
                            enabled: !repo.busy
                            onToggled: repo.toggleRepo(modelData.id, checked)
                        }
                    }
                    Label {
                        text: repo.repoList.length === 0 ? "暂无仓库数据，点击下方刷新重试" : "无匹配仓库，换个关键词或筛选条件"
                        opacity: 0.6
                        horizontalAlignment: Text.AlignHCenter
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        visible: filteredRepos.length === 0 && !repo.busy
                    }
                }
            }
            GroupBox {
                title: "推荐仓库"
                Layout.fillWidth: true
                ColumnLayout {
                    anchors.fill: parent
                    Repeater {
                        model: filteredRecommended
                        delegate: AccentCheckDelegate {
                            Layout.fillWidth: true
                            text: modelData.label
                            checked: modelData.installed
                            enabled: !repo.busy
                            onToggled: repo.toggleRecommended(modelData.id, checked)
                        }
                    }
                    Label {
                        text: "无匹配的推荐仓库"
                        opacity: 0.6
                        horizontalAlignment: Text.AlignHCenter
                        Layout.fillWidth: true
                        visible: filteredRecommended.length === 0 && !repo.busy
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                AppButton {
                    text: "刷新"
                    flat: true
                    enabled: !repo.busy
                    onClicked: repo.refresh()
                }
                Item { Layout.fillWidth: true }
                BusyIndicator { visible: repo.busy; running: repo.busy }
                AppButton { text: "关闭"; highlighted: true; onClicked: repoDrawer.close() }
            }
        }
    }

    Component.onCompleted: {
        // 懒加载后首次进页不自动刷新，用户点"刷新检测"手动触发
        // 避免 180 秒的 refreshUpgrades 阻塞 UI
    }
}
