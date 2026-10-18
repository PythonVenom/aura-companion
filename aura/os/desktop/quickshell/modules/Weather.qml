import QtQuick
import QtQuick.Layouts
import Quickshell.Io

Item {
    property string weatherText: "Загрузка..."
    Process {
        id: weatherProc
        command: ["bash", "/home/pythonvenom/.config/quickshell/scripts/weather.sh"]
        running: false
        stdout: StdioCollector {
            onStreamFinished: weatherText = text.trim()
        }
    }
    Timer {
        interval: 900000 // Каждые 15 минут
        running: true; repeat: true
        triggeredOnStart: true
        onTriggered: weatherProc.running = true
    }
    Text { text: "🌤 " + weatherText; color: "#a6adc8"; font.pixelSize: 14 }
}
