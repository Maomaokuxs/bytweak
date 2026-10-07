import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 软件管理选项卡：软件包管理 / Flatpak 管理 / DNF 调优（原子系统隐藏 DNF）
ColumnLayout {
    id: root
    spacing: 0

    function showTab(i) {
        if (i >= 0 && i < bar.count)
            bar.setCurrentIndex(i)
    }

    TabBar {
        id: bar
        Layout.fillWidth: true
        Layout.leftMargin: 16
        Layout.rightMargin: 16
        Layout.topMargin: 12
        TabButton { text: "软件包管理" }
        TabButton { text: "Flatpak 管理" }
        TabButton { text: "DNF 调优"; visible: !dash.isAtomic }
    }

    StackLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        currentIndex: bar.currentIndex
        RepoPage {}
        FlatpakPage {}
        DnfPage {}
    }
}
