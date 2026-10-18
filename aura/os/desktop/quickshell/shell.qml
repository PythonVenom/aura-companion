import Quickshell
import Quickshell.Io
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

ShellRoot {
    // --- ТЕЛЕМЕТРИЯ ---
    property string auraStatus: "..."
    property string cpuLoad: "..."
    property string gpuInfo: "..."
    Process {
        id: telemetryProc
        command: ["bash", "/home/pythonvenom/.config/quickshell/telemetry.sh"]
        running: false
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    let data = JSON.parse(text);
                    auraStatus = data.aura.toUpperCase();
                    cpuLoad = data.cpu;
                    gpuInfo = `GPU: ${data.gpu_load} ${data.gpu_temp}`;
                } catch(e) {}
            }
        }
    }
    Timer { interval: 1000; running: true; repeat: true; onTriggered: telemetryProc.running = true }

    // --- СПИСОК ОКОН (ДЛЯ ТАСКБАРА) ---
    property var openWindows: []
    Process {
        id: windowProc
        command: ["bash", "/home/pythonvenom/.config/quickshell/scripts/list-windows.sh"]
        running: false
        stdout: StdioCollector {
            onStreamFinished: {
                try { openWindows = JSON.parse(text) } catch(e) { openWindows = [] }
            }
        }
    }
    Timer { interval: 1000; running: true; repeat: true; onTriggered: windowProc.running = true }

    // --- ПОГОДА ---
    property string weatherText: "🌤 ..."
    Process {
        id: weatherProc
        command: ["bash", "/home/pythonvenom/.config/quickshell/scripts/weather.sh"]
        running: false
        stdout: StdioCollector { onStreamFinished: weatherText = text.trim() }
    }
    Timer { interval: 900000; running: true; repeat: true; triggeredOnStart: true; onTriggered: weatherProc.running = true }

    // --- ОБНОВЛЕНИЯ ---
    property string updateText: "📦 ..."
    Process {
        id: updateProc
        command: ["bash", "/home/pythonvenom/.config/quickshell/scripts/updates.sh"]
        running: false
        stdout: StdioCollector { onStreamFinished: updateText = text.trim() }
    }
    Timer { interval: 3600000; running: true; repeat: true; triggeredOnStart: true; onTriggered: updateProc.running = true }

    // --- ЧАСЫ ---
    property string currentTime: Qt.formatDateTime(new Date(), "hh:mm")
    Timer { interval: 1000; running: true; repeat: true; onTriggered: currentTime = Qt.formatDateTime(new Date(), "hh:mm") }

    property bool settingsOpen: false
    property bool calendarOpen: false

    // ВЕРХНЯЯ ПАНЕЛЬ
    PanelWindow {
        anchors { top: true; left: true; right: true }
        implicitHeight: 36
        color: "#1e1e2e"
        
        RowLayout {
            anchors.fill: parent; anchors.margins: 8; spacing: 10
            
            Rectangle {
                implicitWidth: 32; implicitHeight: 28; color: settingsOpen ? "#45475a" : "transparent"; radius: 6
                Text { anchors.centerIn: parent; text: "⚙️"; color: "#cdd6f4"; font.pixelSize: 16 }
                MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: { settingsOpen = !settingsOpen; calendarOpen = false; } }
            }

            Rectangle {
                implicitWidth: 32; implicitHeight: 28; color: "transparent"; radius: 6
                Text { anchors.centerIn: parent; text: "🗔"; color: "#a6e3a1"; font.pixelSize: 16 }
                MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: Quickshell.execDetached(["bash", "/home/pythonvenom/.config/quickshell/scripts/aura-wm.sh", "overview"]) }
            }

            Text { text: updateText; color: "#f9e2af"; font.pixelSize: 14 }
            Text { text: weatherText; color: "#a6adc8"; font.pixelSize: 14 }
            
            Item { Layout.fillWidth: true }
            
            Rectangle {
                color: "transparent"; implicitWidth: auraText.implicitWidth; implicitHeight: auraText.implicitHeight
                Text { id: auraText; text: `🛸 AURA: ${auraStatus} | CPU: ${cpuLoad} | ${gpuInfo}`; color: "#89b4fa"; font.bold: true; font.pixelSize: 14 }
                MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: Quickshell.execDetached(["qterminal", "-e", "python3 aura_main.py"]) }
            }
            
            Item { Layout.fillWidth: true }
            
            Rectangle {
                implicitWidth: 70; implicitHeight: 28; color: calendarOpen ? "#45475a" : "transparent"; radius: 6
                Text { anchors.centerIn: parent; text: currentTime; color: "#cdd6f4"; font.pixelSize: 14; font.bold: true }
                MouseArea { anchors.fill: parent; onClicked: { calendarOpen = !calendarOpen; settingsOpen = false; } }
            }
            
            Rectangle {
                implicitWidth: 32; implicitHeight: 28; color: "transparent"; radius: 6
                Text { anchors.centerIn: parent; text: "⏻"; color: "#f38ba8"; font.pixelSize: 16 }
                MouseArea { anchors.fill: parent; hoverEnabled: true; onClicked: Quickshell.execDetached(["lxqt-leave"]) }
            }
        }
    }

    // ШТОРКА НАСТРОЕК
    PanelWindow {
        visible: settingsOpen
        anchors { top: true; left: true }
        margins.top: 42; margins.left: 8
        implicitWidth: 320; implicitHeight: 280
        color: "#1e1e2e"
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 15; spacing: 10
            Text { text: "Быстрые настройки"; color: "#cdd6f4"; font.bold: true; font.pixelSize: 16 }
            GridLayout {
                columns: 2; rowSpacing: 10; columnSpacing: 10; Layout.fillWidth: true
                Button { text: "📶 Wi-Fi"; Layout.fillWidth: true; onClicked: Quickshell.execDetached(["nm-connection-editor"]) }
                Button { text: "📡 Bluetooth"; Layout.fillWidth: true; onClicked: Quickshell.execDetached(["blueman-manager"]) }
                Button { text: "🔊 Звук"; Layout.fillWidth: true; onClicked: Quickshell.execDetached(["pavucontrol"]) }
                Button { text: "🎤 Микрофон"; Layout.fillWidth: true; onClicked: Quickshell.execDetached(["pavucontrol"]) }
                Button { text: "📷 Камера"; Layout.fillWidth: true; onClicked: Quickshell.execDetached(["cheese"]) }
                Button { text: "⚙️ Система"; Layout.fillWidth: true; onClicked: Quickshell.execDetached(["lxqt-config"]) }
            }
        }
    }

    // КАЛЕНДАРЬ
    PanelWindow {
        visible: calendarOpen
        anchors { top: true; right: true }
        margins.top: 42; margins.right: 8
        implicitWidth: 320; implicitHeight: 380
        color: "#1e1e2e"
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 15
            Text { text: "Планер и Календарь"; color: "#cdd6f4"; font.bold: true; font.pixelSize: 16; Layout.alignment: Qt.AlignHCenter }
            DayOfWeekRow { locale: Qt.locale("ru_RU"); Layout.fillWidth: true }
            MonthGrid { month: new Date().getMonth(); year: new Date().getFullYear(); locale: Qt.locale("ru_RU"); Layout.fillWidth: true; Layout.fillHeight: true }
        }
    }

    // НИЖНЯЯ ПАНЕЛЬ (Настоящий таскбар)
    PanelWindow {
        anchors { bottom: true; left: true; right: true }
        implicitHeight: 48
        color: "#181825"
        
        RowLayout {
            anchors.fill: parent; anchors.margins: 4; spacing: 10
            
            // Кнопка Меню (Rofi)
            Rectangle {
                implicitWidth: 36; implicitHeight: 36; radius: 6
                color: rofiMouse.containsMouse ? "#45475a" : "#313244"
                Text { anchors.centerIn: parent; text: "📱"; font.pixelSize: 16 }
                MouseArea { id: rofiMouse; anchors.fill: parent; hoverEnabled: true; onClicked: Quickshell.execDetached(["rofi", "-show", "drun"]) }
            }

            // Закрепленные приложения (Умный запуск)
            Rectangle {
                implicitWidth: 36; implicitHeight: 36; radius: 6
                color: termMouse.containsMouse ? "#45475a" : "#313244"
                Text { anchors.centerIn: parent; text: ">_"; color: "#a6e3a1"; font.pixelSize: 16; font.bold: true; font.family: "monospace" }
                MouseArea { id: termMouse; anchors.fill: parent; hoverEnabled: true; onClicked: Quickshell.execDetached(["bash", "/home/pythonvenom/.config/quickshell/scripts/smart-launch.sh", "QTerminal", "qterminal"]) }
            }
            Rectangle {
                implicitWidth: 36; implicitHeight: 36; radius: 6
                color: browserMouse.containsMouse ? "#45475a" : "#313244"
                Text { anchors.centerIn: parent; text: "🌐"; color: "#fab387"; font.pixelSize: 16 }
                MouseArea { id: browserMouse; anchors.fill: parent; hoverEnabled: true; onClicked: Quickshell.execDetached(["bash", "/home/pythonvenom/.config/quickshell/scripts/smart-launch.sh", "Firefox", "firefox"]) }
            }

            // Разделитель
            Rectangle { implicitWidth: 1; implicitHeight: 24; color: "#45475a" }

            // ДИНАМИЧЕСКИЙ СПИСОК ОКОН (Таскбар)
            RowLayout {
                Layout.fillWidth: true
                spacing: 5
                Repeater {
                    model: openWindows
                    delegate: Rectangle {
                        implicitWidth: 150; implicitHeight: 32; radius: 4
                        color: winMouse.containsMouse ? "#313244" : "transparent"
                        
                        Text {
                            anchors.fill: parent; anchors.leftMargin: 8; anchors.rightMargin: 8
                            verticalAlignment: Text.AlignVCenter
                            text: modelData.title
                            color: "#cdd6f4"; font.pixelSize: 12
                            elide: Text.ElideRight
                        }
                        
                        MouseArea {
                            id: winMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            // При клике активируем это окно
                            onClicked: Quickshell.execDetached(["wmctrl", "-i", "-a", modelData.id])
                        }
                    }
                }
            }
            
            // Кнопка Микрофона Aura
            Rectangle {
                implicitWidth: 36; implicitHeight: 36; radius: 6
                color: micMouse.containsMouse ? "#f38ba8" : "#313244"
                Text { anchors.centerIn: parent; text: "🎤"; color: "#f38ba8"; font.pixelSize: 16 }
                MouseArea { id: micMouse; anchors.fill: parent; hoverEnabled: true; onClicked: Quickshell.execDetached(["bash", "/home/pythonvenom/.config/quickshell/scripts/aura-listen.sh"]) }
            }
        }
    }
}
