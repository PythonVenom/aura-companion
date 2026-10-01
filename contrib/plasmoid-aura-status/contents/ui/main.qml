import QtQuick
import QtQuick.Layouts
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
    readonly property bool showText: plasmoid.configuration.showText
    readonly property bool showDialog: plasmoid.configuration.showDialog

    property string auraState: "unknown"
    property string auraText: ""
    property string lastUser: ""
    property string lastAura: ""
    property bool fetching: false

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
                    var parsed = JSON.parse(stdout);
                    root.auraState = parsed.state || "unknown";
                    root.auraText = parsed.text || "";
                } catch (e) { console.log("[Aura] parse:", e); }
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
                    root.lastUser = parsed.user || "";
                    root.lastAura = parsed.aura || "";
                } catch (e) {}
            }
            dialogSource.disconnectSource(sourceName);
        }
        function fetch() {
            connectSource("cat \"$HOME/.cache/aura/aura_last_dialog.json\" 2>/dev/null");
        }
    }

    Plasma5Support.DataSource {
        id: ctlSource
        engine: "executable"
        connectedSources: []
        onNewData: (sourceName, data) => {
            console.log("[Aura] ctl:", sourceName);
            ctlSource.disconnectSource(sourceName);
        }
        function call(cmd) {
            connectSource("python3 $HOME/aura_project/scripts/aura_ctl.py " + cmd);
        }
    }

    Timer {
        interval: root.pollMs
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            if (root.fetching) return;
            root.fetching = true;
            execSource.fetch();
            if (root.showDialog) dialogSource.fetch();
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
            border.color: Qt.rgba(0, 0, 0, 0.3)
            border.width: 1
            Behavior on color { ColorAnimation { duration: 200 } }
        }
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton
            onClicked: root.expanded = !root.expanded
        }
    }

    fullRepresentation: Item {
        implicitWidth: root.popupW
        implicitHeight: root.popupH
        Layout.preferredWidth: root.popupW
        Layout.preferredHeight: root.popupH
        Layout.minimumWidth: root.popupW
        Layout.minimumHeight: root.popupH

        Rectangle {
            anchors.fill: parent
            color: Kirigami.Theme.backgroundColor

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Rectangle {
                        width: 28 * root.fscale
                        height: 28 * root.fscale
                        radius: width / 2
                        color: root.stateColors[root.auraState] || "#888888"
                        border.color: Qt.rgba(0, 0, 0, 0.3)
                        border.width: 1
                        Behavior on color { ColorAnimation { duration: 200 } }
                    }
                    Text {
                        text: root.stateLabels[root.auraState] || "?"
                        font.bold: true
                        font.pixelSize: Kirigami.Units.gridUnit * 1.2 * root.fscale
                        color: Kirigami.Theme.textColor
                    }
                    Item { Layout.fillWidth: true }
                }

                Text {
                    visible: root.showText
                    text: root.auraText || "—"
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                    font.pixelSize: Kirigami.Units.gridUnit * 1.0 * root.fscale
                    color: Kirigami.Theme.textColor
                    opacity: 0.85
                    elide: Text.ElideRight
                    maximumLineCount: 3
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: Kirigami.Theme.textColor
                    opacity: 0.2
                }

                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 8
                    rowSpacing: 8

                    PlasmaComponents3.Button {
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.btnH
                        text: (root.auraState === "paused") ? "▶ Resume" : "⏸ Pause"
                        icon.name: (root.auraState === "paused") ? "media-playback-start" : "media-playback-pause"
                        font.pixelSize: Kirigami.Units.gridUnit * 0.95 * root.fscale
                        onClicked: ctlSource.call((root.auraState === "paused") ? "resume" : "pause")
                    }
                    PlasmaComponents3.Button {
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.btnH
                        text: "⟳ Restart"
                        icon.name: "view-refresh"
                        font.pixelSize: Kirigami.Units.gridUnit * 0.95 * root.fscale
                        onClicked: ctlSource.call("restart")
                    }
                    PlasmaComponents3.Button {
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.btnH
                        text: "⏹ Stop"
                        icon.name: "process-stop"
                        font.pixelSize: Kirigami.Units.gridUnit * 0.95 * root.fscale
                        onClicked: ctlSource.call("stop")
                    }
                    PlasmaComponents3.Button {
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.btnH
                        text: "✕ Kill"
                        icon.name: "window-close"
                        font.pixelSize: Kirigami.Units.gridUnit * 0.95 * root.fscale
                        onClicked: ctlSource.call("kill")
                    }
                }

                Rectangle {
                    visible: root.showDialog
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: Kirigami.Theme.textColor
                    opacity: 0.2
                }

                Text {
                    visible: root.showDialog
                    text: "Ты: " + (root.lastUser || "—")
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                    font.pixelSize: Kirigami.Units.gridUnit * 0.9 * root.fscale
                    color: Kirigami.Theme.textColor
                    opacity: 0.9
                    elide: Text.ElideRight
                    maximumLineCount: 2
                }

                Text {
                    visible: root.showDialog
                    text: "Аура: " + (root.lastAura || "—")
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    font.pixelSize: Kirigami.Units.gridUnit * 0.9 * root.fscale
                    color: Kirigami.Theme.textColor
                    opacity: 0.9
                    elide: Text.ElideRight
                    maximumLineCount: 6
                }
            }
        }
    }

    toolTipMainText: "Аура"
    toolTipSubText: {
        var label = root.stateLabels[root.auraState] || "?";
        return root.auraText ? label + "\n" + root.auraText : label;
    }
}
