import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 输入设备选项卡：Fcitx 输入法 / 鼠标指针样式
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
        TabButton { text: "Fcitx 输入法" }
        TabButton { text: "鼠标指针样式" }
    }

    StackLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        currentIndex: bar.currentIndex
        FcitxPage {}
        CursorPage {}
    }
}
