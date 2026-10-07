import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 系统设置选项卡：时区设置 / 主机名
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
        TabButton { text: "时区设置" }
        TabButton { text: "主机名" }
    }

    StackLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        currentIndex: bar.currentIndex
        TimezonePage {}
        HostnamePage {}
    }
}
