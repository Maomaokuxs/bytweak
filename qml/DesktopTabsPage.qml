import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 桌面环境选项卡：桌面组件 / niri 快捷键 / 默认应用设置
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
        TabButton { text: "桌面组件" }
        TabButton { text: "niri 快捷键" }
        TabButton { text: "默认应用设置" }
    }

    StackLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        currentIndex: bar.currentIndex
        DesktopPage {}
        NiriKeysPage {}
        DefaultAppsPage {}
    }
}
