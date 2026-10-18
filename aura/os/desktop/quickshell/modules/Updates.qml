import QtQuick
import QtQuick.Layouts
import Quickshell.Io

Item {
    property string updateText: "Проверка..."
    Process {
        id: updateProc
        command: ["bash", "/home/pythonvenom/.config/quickshell/scripts/updates.sh"]
        running: false
        stdout: StdioCollector {
            onStreamFinished: updateText = text.trim()
        }
    }
    Timer {
        interval: 3600000 // Каждый час
        running: true; repeat: true
        triggeredOnStart: true
        onTriggered: updateProc.running = true
    }
    Text { text: updateText; color: "#f9e2af"; font.pixelSize: 14 }
}
