import Quickshell
import Quickshell.Io
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

ShellRoot {
    function logEvent(role, text) {
        Quickshell.execDetached(["bash", "/home/pythonvenom/.config/quickshell/scripts/aura-event.sh", role, text])
    }

    property bool chatOpen: false
    property bool settingsOpen: false
    property bool calendarOpen: false
    property bool powerMenuOpen: false

    // --- ЧАТ ---
    property string chatHistoryText: "История пуста (попробуй написать что-нибудь)"
    Process {
        id: chatReaderProc
        command: ["bash", "/home/pythonvenom/.config/quickshell/scripts/aura-chat.sh", "read"]
        running: false
        stdout: StdioCollector { onStreamFinished: chatHistoryText = text.trim() }
    }
    Timer { interval: 2000; running: chatOpen; repeat: true; onTriggered: chatReaderProc.running = true }

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

    // --- ПОГОДА И ОБНОВЛЕНИЯ ---
    property string weatherText: "🌤 ..."
    Process {
        id: weatherProc
        command: ["bash", "/home/pythonvenom/.config/quickshell/scripts/weather.sh"]
        running: false
        stdout: StdioCollector { onStreamFinished: weatherText = text.trim() }
    }
    Timer { interval: 900000; running: true; repeat: true; triggeredOnStart: true; onTriggered: weatherProc.running = true }

    property string updateText: "📦 ..."
    Process {
        id: updateProc
        command: ["bash", "/home/pythonvenom/.config/quickshell/scripts/updates.sh"]
        running: false
        stdout: StdioCollector { onStreamFinished: updateText = text.trim() }
    }
    Timer { interval: 3600000; running: true; repeat: true; triggeredOnStart: true; onTriggered: updateProc.running = true }

    // --- ЧАСЫ ---
    property string currentTime: Qt.formatDateTime(new Date(), "ddd, hh:mm")
    Timer { interval: 1000; running: true; repeat: true; onTriggered: currentTime = Qt.formatDateTime(new Date(), "ddd, hh:mm") }

    // ВЕРХНЯЯ ПАНЕЛЬ
    PanelWindow {
        anchors { top: true; left: true; right: true }
        implicitHeight: 32
        color: "#1e1e2e"
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 15
            
            Text {
                text: "📱 Меню"
                color: "#cdd6f4"
                font.pixelSize: 14
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        logEvent("system", "Открыто меню приложений")
                        Quickshell.execDetached(["rofi", "-show", "drun"])
                    }
                }
            }
            Text {
                text: "🗔 Обзор"
                color: "#a6e3a1"
                font.pixelSize: 14
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        logEvent("system", "Открыт обзор окон")
                        Quickshell.execDetached(["bash", "/home/pythonvenom/.config/quickshell/scripts/aura-wm.sh", "overview"])
                    }
                }
            }
            
            Item { Layout.fillWidth: true }
            
            Text {
                text: currentTime
                color: "#cdd6f4"
                font.bold: true
                font.pixelSize: 14
            }
            
            Item { Layout.fillWidth: true }
            
            Text {
                text: `🛸 ${auraStatus} | CPU: ${cpuLoad} | ${gpuInfo}`
                color: "#89b4fa"
                font.pixelSize: 12
            }
            Text { text: weatherText; color: "#a6adc8"; font.pixelSize: 14 }
            Text { text: updateText; color: "#f9e2af"; font.pixelSize: 14 }
            
            Text {
                text: "⚙️"
                font.pixelSize: 16
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        settingsOpen = !settingsOpen
                        calendarOpen = false
                        chatOpen = false
                        powerMenuOpen = false
                    }
                }
            }
            Text {
                text: "⏻"
                color: "#f38ba8"
                font.pixelSize: 16
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        powerMenuOpen = !powerMenuOpen
                        settingsOpen = false
                        calendarOpen = false
                        chatOpen = false
                    }
                }
            }
        }
    }

    // МЕНЮ ПИТАНИЯ
    PanelWindow {
        visible: powerMenuOpen
        anchors { top: true; right: true }
        margins.top: 38
        margins.right: 8
        implicitWidth: 180
        implicitHeight: 200
        color: "#1e1e2e"
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5
            
            Button {
                text: "Выключить"
                Layout.fillWidth: true
                onClicked: {
                    logEvent("system", "Пользователь выключил ПК")
                    Quickshell.execDetached(["systemctl", "poweroff"])
                }
            }
            Button {
                text: "Перезагрузить"
                Layout.fillWidth: true
                onClicked: {
                    logEvent("system", "Пользователь перезагрузил ПК")
                    Quickshell.execDetached(["systemctl", "reboot"])
                }
            }
            Button {
                text: "Сон"
                Layout.fillWidth: true
                onClicked: {
                    logEvent("system", "Пользователь отправил ПК в сон")
                    Quickshell.execDetached(["systemctl", "suspend"])
                }
            }
            Button {
                text: "Выйти"
                Layout.fillWidth: true
                onClicked: {
                    logEvent("system", "Пользователь вышел из сессии")
                    Quickshell.execDetached(["lxqt-leave", "--logout"])
                }
            }
        }
    }

    // НИЖНИЙ ДОК
    PanelWindow {
        anchors { bottom: true; left: true; right: true }
        implicitHeight: 60
        color: "#00000000"
        exclusiveZone: -1
        
        Rectangle {
            anchors.centerIn: parent
            width: 320
            height: 50
            radius: 12
            color: "#1e1e2e"
            border.color: "#313244"
            border.width: 1
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 15
                
                Rectangle {
                    implicitWidth: 36
                    implicitHeight: 36
                    radius: 8
                    color: termMouse.containsMouse ? "#45475a" : "#313244"
                    Text {
                        anchors.centerIn: parent
                        text: ">_"
                        color: "#a6e3a1"
                        font.pixelSize: 16
                        font.bold: true
                        font.family: "monospace"
                    }
                    MouseArea {
                        id: termMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            logEvent("system", "Открыт терминал")
                            Quickshell.execDetached(["bash", "/home/pythonvenom/.config/quickshell/scripts/smart-launch.sh", "QTerminal", "qterminal"])
                        }
                    }
                }
                
                Rectangle {
                    implicitWidth: 36
                    implicitHeight: 36
                    radius: 8
                    color: folderMouse.containsMouse ? "#45475a" : "#313244"
                    Text {
                        anchors.centerIn: parent
                        text: "📁"
                        color: "#89dceb"
                        font.pixelSize: 18
                    }
                    MouseArea {
                        id: folderMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            logEvent("system", "Открыт файловый менеджер")
                            Quickshell.execDetached(["pcmanfm-qt"])
                        }
                    }
                }
                
                Rectangle {
                    implicitWidth: 36
                    implicitHeight: 36
                    radius: 8
                    color: chatMouse.containsMouse ? "#45475a" : "#313244"
                    Text {
                        anchors.centerIn: parent
                        text: "💬"
                        color: "#89b4fa"
                        font.pixelSize: 18
                    }
                    MouseArea {
                        id: chatMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            chatOpen = !chatOpen
                            settingsOpen = false
                            calendarOpen = false
                            powerMenuOpen = false
                        }
                    }
                }
                
                Rectangle {
                    implicitWidth: 36
                    implicitHeight: 36
                    radius: 8
                    color: browserMouse.containsMouse ? "#45475a" : "#313244"
                    Text {
                        anchors.centerIn: parent
                        text: "🌐"
                        color: "#fab387"
                        font.pixelSize: 18
                    }
                    MouseArea {
                        id: browserMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            logEvent("system", "Открыт браузер")
                            Quickshell.execDetached(["bash", "/home/pythonvenom/.config/quickshell/scripts/smart-launch.sh", "Firefox", "firefox"])
                        }
                    }
                }
            }
        }
    }

    // ШТОРКА НАСТРОЕК
    PanelWindow {
        visible: settingsOpen
        anchors { top: true; left: true }
        margins.top: 38
        margins.left: 8
        implicitWidth: 320
        implicitHeight: 250
        color: "#1e1e2e"
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 10
            
            Text {
                text: "Быстрые настройки"
                color: "#cdd6f4"
                font.bold: true
                font.pixelSize: 16
            }
            GridLayout {
                columns: 2
                rowSpacing: 10
                columnSpacing: 10
                Layout.fillWidth: true
                
                Button { text: "📶 Wi-Fi"; Layout.fillWidth: true; onClicked: { logEvent("system", "Открыты настройки Wi-Fi"); Quickshell.execDetached(["nm-connection-editor"]) } }
                Button { text: "📡 Bluetooth"; Layout.fillWidth: true; onClicked: { logEvent("system", "Открыты настройки Bluetooth"); Quickshell.execDetached(["blueman-manager"]) } }
                Button { text: "🔊 Звук"; Layout.fillWidth: true; onClicked: { logEvent("system", "Открыты настройки звука"); Quickshell.execDetached(["pavucontrol"]) } }
                Button { text: "🎤 Микрофон"; Layout.fillWidth: true; onClicked: { logEvent("system", "Открыты настройки микрофона"); Quickshell.execDetached(["pavucontrol"]) } }
                Button { text: "📷 Камера"; Layout.fillWidth: true; onClicked: { logEvent("system", "Открыта камера"); Quickshell.execDetached(["guvcview"]) } }
                Button { text: "⚙️ Система"; Layout.fillWidth: true; onClicked: { logEvent("system", "Открыты системные настройки"); Quickshell.execDetached(["lxqt-config"]) } }
            }
        }
    }

    // КАЛЕНДАРЬ
    PanelWindow {
        visible: calendarOpen
        anchors { top: true; right: true }
        margins.top: 38
        margins.right: 8
        implicitWidth: 320
        implicitHeight: 380
        color: "#1e1e2e"
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 15
            
            Text {
                text: "Планер и Календарь"
                color: "#cdd6f4"
                font.bold: true
                font.pixelSize: 16
                Layout.alignment: Qt.AlignHCenter
            }
            DayOfWeekRow {
                locale: Qt.locale("ru_RU")
                Layout.fillWidth: true
            }
            MonthGrid {
                month: new Date().getMonth()
                year: new Date().getFullYear()
                locale: Qt.locale("ru_RU")
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }
    }

    // ОКНО ЧАТА
    PanelWindow {
        visible: chatOpen
        anchors { top: true; right: true }
        margins.top: 38
        margins.right: 8
        implicitWidth: 400
        implicitHeight: 500
        color: "#1e1e2e"
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10
            
            Text {
                text: "Диалог с Aura"
                color: "#89b4fa"
                font.bold: true
                font.pixelSize: 16
                Layout.alignment: Qt.AlignHCenter
            }
            
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                TextArea {
                    text: chatHistoryText
                    readOnly: true
                    wrapMode: TextArea.Wrap
                    color: "#cdd6f4"
                    background: Rectangle { color: "#181825"; radius: 5 }
                }
            }
            
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                
                TextField {
                    id: inputField
                    Layout.fillWidth: true
                    placeholderText: "Напиши Aura..."
                    color: "#cdd6f4"
                    background: Rectangle { color: "#313244"; radius: 5 }
                    onAccepted: {
                        if (text.trim() !== "") {
                            Quickshell.execDetached(["bash", "/home/pythonvenom/.config/quickshell/scripts/aura-chat.sh", "send", text])
                            text = ""
                        }
                    }
                }
                
                Button {
                    text: "➤"
                    onClicked: {
                        if (inputField.text.trim() !== "") {
                            Quickshell.execDetached(["bash", "/home/pythonvenom/.config/quickshell/scripts/aura-chat.sh", "send", inputField.text])
                            inputField.text = ""
                        }
                    }
                }
            }
        }
    }
}
