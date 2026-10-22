import Quickshell
import Quickshell.Io
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

FloatingWindow {
    id: chatWindow
    title: "Aura Chat"
    width: 400
    height: 500
    color: "#1e1e2e"
    
    property string historyText: "Загрузка истории..."
    
    Process {
        id: readerProc
        command: ["bash", "/home/pythonvenom/.config/quickshell/scripts/aura-chat.sh", "read"]
        running: false
        stdout: StdioCollector {
            onStreamFinished: historyText = text.trim()
        }
    }
    
    Timer {
        interval: 2000; running: true; repeat: true
        onTriggered: readerProc.running = true
    }

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
                text: chatWindow.historyText
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
