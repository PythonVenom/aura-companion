import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    Kirigami.FormLayout {
    id: page

    property alias cfg_popupWidth: wSpin.value
    property alias cfg_popupHeight: hSpin.value
    property alias cfg_buttonHeight: bSpin.value
    property alias cfg_fontScale: fSlider.value
    property alias cfg_pollInterval: pSpin.value
    property alias cfg_showDialog: dCheck.checked
    property alias cfg_showText: tCheck.checked

    QQC2.SpinBox {
        id: wSpin
        Kirigami.FormData.label: "Ширина попапа:"
        from: 240; to: 1200; stepSize: 20
    }

    QQC2.SpinBox {
        id: hSpin
        Kirigami.FormData.label: "Высота попапа:"
        from: 240; to: 1600; stepSize: 20
    }

    QQC2.SpinBox {
        id: bSpin
        Kirigami.FormData.label: "Высота кнопок:"
        from: 28; to: 120; stepSize: 4
    }

    RowLayout {
        Kirigami.FormData.label: "Масштаб шрифта:"
        QQC2.Slider {
            id: fSlider
            Layout.preferredWidth: 200
            from: 0.7; to: 2.0; stepSize: 0.1
        }
        QQC2.Label { text: fSlider.value.toFixed(1) }
    }

    QQC2.SpinBox {
        id: pSpin
        Kirigami.FormData.label: "Опрос статуса (мс):"
        from: 100; to: 5000; stepSize: 100
    }

    QQC2.CheckBox {
        id: dCheck
        text: "Показывать последний диалог"
    }

    QQC2.CheckBox {
        id: tCheck
        text: "Показывать текст статуса"
    }

    Item { Kirigami.FormData.isSection: true }

    QQC2.Label {
        text: "Песочница: меняй и смотри результат в реальном времени"
        opacity: 0.7
        wrapMode: Text.WordWrap
        Layout.preferredWidth: 260
    }
}
}
