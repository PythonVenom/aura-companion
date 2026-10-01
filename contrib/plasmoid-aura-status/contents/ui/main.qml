import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    readonly property int popupW: plasmoid.configuration.popupWidth
    readonly property int popupH: plasmoid.configuration.popupHeight
    readonly property int btnH: plasmoid.configuration.buttonHeight
    readonly property real fscale: plasmoid.configuration.fontScale
    readonly property int pollMs: plasmoid.configuration.pollInterval

    property string auraState: "unknown"
    property string auraText: ""
    property var chatMessages: []

    readonly property var stateColors: ({
        "idle": "#5a7a9a", "listening": "#f5c542", "thinking": "#f58742",
        "speaking": "#42c55a", "paused": "#666666", "error": "#c54242",
        "unknown": "#888888"
    })
    readonly property var stateLabels: ({
        "idle": "Ждёт", "listening": "Слушает", "thinking": "Думает",
        "speaking": "Говорит", "paused": "На паузе", "error": "Ошибка",
        "unknown": "Нет данных"
    })

    Plasma5Support.DataSource {
        id: execSource
        engine: "executable"
        connectedSources: []
        onNewData: (sourceName, data) => {
            var stdout = (data["stdout"] || "").trim();
            if (stdout.length > 0) {
                try {
                    var p = JSON.parse(stdout);
                    root.auraState = p.state || "unknown";
                    root.auraText = p.text || "";
                } catch (e) {}
            }
            execSource.disconnectSource(sourceName);
        }
        function fetch() {
            connectSource("cat \"$HOME/.cache/aura/aura_status.json\" 2>/dev/null");
        }
    }

    Plasma5Support.DataSource {
        id: chatSource
        engine: "executable"
        connectedSources: []
        onNewData: (sourceName, data) => {
            var stdout = (data["stdout"] || "").trim();
            if (stdout.length > 0) {
                var lines = stdout.split("\n");
                var msgs = [];
                for (var i = 0; i < lines.length; i++) {
                    var line = lines[i].trim();
                    if (line.length === 0) continue;
                    try { msgs.push(JSON.parse(line)); } catch (e) {}
                }
                root.chatMessages = msgs;
            }
            chatSource.disconnectSource(sourceName);
        }
        function fetch() {
            connectSource("tail -n 50 \"$HOME/.cache/aura/chat_history.jsonl\" 2>/dev/null");
        }
    }

    Plasma5Support.DataSource {
        id: ctlSource
        engine: "executable"
        connectedSources: []
        onNewData: (sourceName, data) => {
            ctlSource.disconnectSource(sourceName);
        }
        function call(cmd) {
            connectSource("python3 $HOME/aura_project/scripts/aura_ctl.py " + cmd);
        }
        function sendChat(text) {
            var escaped = text.replace(/"/g, '\\"').replace(/\\/g, '\\\\');
            connectSource("python3 -c \"import json,sys;open('$HOME/.cache/aura/chat_inbox.jsonl','a').write(json.dumps({'user':sys.argv[1],'ts':0},ensure_ascii=False)+chr(10))\" \"" + escaped + "\"");
        }
    }

    Timer {
        interval: root.pollMs
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            execSource.fetch();
            chatSource.fetch();
        }
    }

    compactRepresentation: Item {
        Layout.minimumWidth: Kirigami.Units.iconSizes.small
        Layout.minimumHeight: Kirigami.Units.iconSizes.small
        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width, parent.height) * 0.75
            height: width
            radius: width / 2
            color: root.stateColors[root.auraState] || "#888888"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: root.expanded = !root.expanded
        }
    }

    fullRepresentation: Item {
        implicitWidth: root.popupW
        implicitHeight: root.popupH
        Layout.preferredWidth: root.popupW
        Layout.preferredHeight: root.popupH

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 6

            // === СТАТУС-СТРОКА ===
            RowLayout {
                Layout.fillWidth: true
                Rectangle {
                    width: 20; height: 20; radius: 10
                    color: root.stateColors[root.auraState] || "#888888"
                }
                Text {
                    text: root.stateLabels[root.auraState] || "?"
                    font.bold: true
                    font.pixelSize: Kirigami.Units.gridUnit * 1.0 * root.fscale
                    color: Kirigami.Theme.textColor
                }
                Item { Layout.fillWidth: true }
            }

            // === КНОПКИ УПРАВЛЕНИЯ ===
            GridLayout {
                Layout.fillWidth: true
                columns: 4
                columnSpacing: 4
                PlasmaComponents3.Button {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    text: (root.auraState === "paused") ? "▶" : "⏸"
                    onClicked: ctlSource.call((root.auraState === "paused") ? "resume" : "pause")
                }
                PlasmaComponents3.Button {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    text: "⟳"
                    onClicked: ctlSource.call("restart")
                }
                PlasmaComponents3.Button {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    text: "⏹"
                    onClicked: ctlSource.call("stop")
                }
                PlasmaComponents3.Button {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    text: "✕"
                    onClicked: ctlSource.call("kill")
                }
            }

            // === ЧАТ ===
            Text {
                text: "Чат с Aura"
                font.bold: true
                font.pixelSize: Kirigami.Units.gridUnit * 0.9 * root.fscale
                color: Kirigami.Theme.textColor
                Layout.topMargin: 4
            }

            QQC2.ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true

                ListView {
                    id: chatView
                    model: root.chatMessages
                    spacing: 4
                    delegate: ColumnLayout {
                        width: chatView.width - 12
                        spacing: 2

                        Text {
                            text: modelData.user || ""
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                            font.pixelSize: Kirigami.Units.gridUnit * 0.85 * root.fscale
                            color: Kirigami.Theme.highlightColor
                            font.bold: true
                        }
                        Text {
                            text: modelData.aura || ""
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                            font.pixelSize: Kirigami.Units.gridUnit * 0.85 * root.fscale
                            color: Kirigami.Theme.textColor
                            bottomPadding: 4
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                QQC2.TextField {
                    id: chatInput
                    Layout.fillWidth: true
                    placeholderText: "Написать Aura..."
                    font.pixelSize: Kirigami.Units.gridUnit * 0.9 * root.fscale
                    onAccepted: {
                        if (text.trim().length > 0) {
                            ctlSource.sendChat(text.trim());
                            text = "";
                        }
                    }
                }
                PlasmaComponents3.Button {
                    text: "➤"
                    onClicked: {
                        if (chatInput.text.trim().length > 0) {
                            ctlSource.sendChat(chatInput.text.trim());
                            chatInput.text = "";
                        }
                    }
                }
            }
        }
    }

    toolTipMainText: "Аура"
    toolTipSubText: root.stateLabels[root.auraState] || "?"
}
