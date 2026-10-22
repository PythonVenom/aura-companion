import Quickshell
import Quickshell.Io
import QtQuick
import QtQuick.Layouts

Item {
    id: root
    width: 300
    height: 50

    property color textColor: "#00ffcc"
    property string statusText: "Aura: Offline"

    FileView {
        id: statusFile
        path: Quickshell.env("HOME") + "/.cache/aura/mcp_status.json"
        watchChanges: true
        onFileChanged: {
            statusFile.reload()
            parseStatus()
        }
        onLoaded: parseStatus()

        function parseStatus() {
            try {
                let text = statusFile.text();
                if (!text) return;
                let data = JSON.parse(text);
                
                if (data.status === "idle") {
                    root.statusText = "Aura: Слушает...";
                    root.textColor = "#00ffcc";
                } else if (data.status === "thinking") {
                    root.statusText = "Aura: Думает...";
                    root.textColor = "#ffcc00";
                } else if (data.status === "running") {
                    root.statusText = "Aura: Выполняет " + data.tool + "...";
                    root.textColor = "#ff3366";
                }
            } catch (e) {}
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#1a1a1a"
        radius: 10
        border.color: root.textColor
        border.width: 1

        Text {
            anchors.centerIn: parent
            text: root.statusText
            color: root.textColor
            font.family: "Monospace"
            font.bold: true
            font.pixelSize: 14
        }
    }
}
