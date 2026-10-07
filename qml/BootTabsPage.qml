import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 启动管理选项卡：GRUB 配置 / 内核管理（原子系统隐藏内核管理）
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
        TabButton { text: "GRUB 配置" }
        TabButton { text: "内核管理"; visible: !dash.isAtomic }
    }

    StackLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        currentIndex: bar.currentIndex
        GrubPage {}
        KernelPage {}
    }
}
