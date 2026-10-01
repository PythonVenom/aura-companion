// Aura Status Plasmoid — читает "$HOME/.cache/aura/aura_status.json" через executable datasource.
// XMLHttpRequest с file:// в Plasma 6 блокируется — используем Plasma5Support.

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    property string auraState: "unknown"
    property string auraText: ""
    property string lastUser: ""
    property string lastAura: ""
    property bool fetching: false

    readonly property var stateColors: ({
        "idle":      "#5a7a9a",
        "listening": "#f5c542",
        "thinking":  "#f58742",
        "speaking":  "#42c55a",
        "paused":    "#666666",
        "error":     "#c54242",
        "unknown":   "#888888"
    })

    readonly property var stateLabels: ({
        "idle":      "Ждёт",
        "listening": "Слушает",
        "thinking":  "Думает",
        "speaking":  "Говорит",
        "paused":    "На паузе",
        "error":     "Ошибка",
        "unknown":   "Нет данных"
    })

    Plasma5Support.DataSource {
        id: execSource
        engine: "executable"
        connectedSources: []

        onNewData: (sourceName, data) => {
            var stdout = (data["stdout"] || "").trim();
            if (stdout.length > 0) {
                try {
                    var parsed = JSON.parse(stdout);
                    var ns = parsed.state || "unknown";
                    var nt = parsed.text || "";
                    if (ns !== root.auraState) root.auraState = ns;
                    if (nt !== root.auraText) root.auraText = nt;
                } catch (e) {
                    console.log("[Aura Widget] parse error:", e, "raw:", stdout);
                }
            }
            execSource.disconnectSource(sourceName);
            root.fetching = false;
        }

        function fetch() {
            connectSource("cat \"$HOME/.cache/aura/aura_status.json\" 2>/dev/null");
        }
    }

    Plasma5Support.DataSource {
        id: dialogSource
        engine: "executable"
        connectedSources: []

        onNewData: (sourceName, data) => {
            var stdout = (data["stdout"] || "").trim();
            if (stdout.length > 0) {
                try {
                    var parsed = JSON.parse(stdout);
                    var u = parsed.user || "";
                    var a = parsed.aura || "";
                    if (u !== root.lastUser) root.lastUser = u;
                    if (a !== root.lastAura) root.lastAura = a;
                } catch (e) {
                    console.log("[Aura Widget] dialog parse error:", e);
                }
            }
            dialogSource.disconnectSource(sourceName);
        }

        function fetch() {
            connectSource("cat \"$HOME/.cache/aura/aura_last_dialog.json\" 2>/dev/null");
        }
    }

    Timer {
        interval: 500
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            if (root.fetching) return;
            root.fetching = true;
            execSource.fetch();
            dialogSource.fetch();
        }
    }

    // --- Компактный вид (в панели) ---
    compactRepresentation: Item {
        Layout.minimumWidth: Kirigami.Units.iconSizes.small
        Layout.minimumHeight: Kirigami.Units.iconSizes.small

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(parent.width, parent.height) * 0.75
            height: width
            radius: width / 2
            color: root.stateColors[root.auraState] || "#888888"
            border.color: Qt.rgba(0, 0, 0, 0.3)
            border.width: 1

            Behavior on color {
                ColorAnimation { duration: 200 }
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton
            onClicked: root.expanded = !root.expanded
        }
    }

    // --- Развёрнутый вид ---
    fullRepresentation: Item {
        Layout.preferredWidth: 240
        Layout.preferredHeight: 200

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8

            RowLayout {
                spacing: 8

                Rectangle {
                    width: 18
                    height: 18
                    radius: 9
                    color: root.stateColors[root.auraState] || "#888888"
                    border.color: Qt.rgba(0, 0, 0, 0.3)
                    border.width: 1

                    Behavior on color {
                        ColorAnimation { duration: 200 }
                    }
                }

                Text {
                    text: root.stateLabels[root.auraState] || "?"
                    font.bold: true
                    font.pixelSize: Kirigami.Units.gridUnit * 0.9
                    color: Kirigami.Theme.textColor
                }

                Item { Layout.fillWidth: true }
            }

            Text {
                text: root.auraText || "—"
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                font.pixelSize: Kirigami.Units.gridUnit * 0.8
                color: Kirigami.Theme.textColor
                opacity: 0.85
                elide: Text.ElideRight
                maximumLineCount: 2
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: Kirigami.Theme.textColor
                opacity: 0.2
            }

            Text {
                text: "Ты: " + (root.lastUser || "—")
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                font.pixelSize: Kirigami.Units.gridUnit * 0.75
                color: Kirigami.Theme.textColor
                opacity: 0.9
                elide: Text.ElideRight
                maximumLineCount: 2
            }

            Text {
                text: "Аура: " + (root.lastAura || "—")
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
                Layout.fillHeight: true
                font.pixelSize: Kirigami.Units.gridUnit * 0.75
                color: Kirigami.Theme.textColor
                opacity: 0.9
                elide: Text.ElideRight
                maximumLineCount: 4
            }
        }
    }

    toolTipMainText: "Аура"
    toolTipSubText: {
        var label = root.stateLabels[root.auraState] || "?";
        return root.auraText ? label + "\n" + root.auraText : label;
    }
}
