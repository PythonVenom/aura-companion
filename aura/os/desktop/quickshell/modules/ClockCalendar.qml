import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell

Item {
    id: clockModule
    property bool popupOpen: false
    property string currentTime: Qt.formatDateTime(new Date(), "hh:mm")

    Timer {
        interval: 1000; running: true; repeat: true
        onTriggered: clockModule.currentTime = Qt.formatDateTime(new Date(), "hh:mm")
    }

    Text {
        text: "🕒 " + currentTime
        color: "#cdd6f4"; font.pixelSize: 14
        MouseArea {
            anchors.fill: parent
            onClicked: clockModule.popupOpen = !clockModule.popupOpen
        }
    }

    PopupWindow {
        id: calendarPopup
        visible: clockModule.popupOpen
        anchor.item: clockModule
        anchor.rect.y: 40
        width: 300; height: 350
        color: "#1e1e2e"

        ColumnLayout {
            anchors.fill: parent; anchors.margins: 10
            Text { text: "Планер и Календарь"; color: "#cdd6f4"; font.bold: true; font.pixelSize: 16 }
            DayOfWeekRow { locale: Qt.locale("ru_RU") }
            MonthGrid {
                month: new Date().getMonth()
                year: new Date().getFullYear()
                locale: Qt.locale("ru_RU")
                Layout.fillWidth: true; Layout.fillHeight: true
            }
        }
    }
}
