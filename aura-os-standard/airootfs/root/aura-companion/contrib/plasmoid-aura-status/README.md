# Aura Status Plasmoid

KDE Plasma 6 виджет — кружок в трее, показывающий статус Ауры.

## Установка

    mkdir -p ~/.local/share/plasma/plasmoids/org.aura.status/contents/ui
    cp metadata.json ~/.local/share/plasma/plasmoids/org.aura.status/
    cp contents/ui/main.qml ~/.local/share/plasma/plasmoids/org.aura.status/contents/ui/
    kquitapp6 plasmashell && sleep 2 && kstart plasmashell &

Затем: правый клик на панели -> Add Widgets -> Aura.

## Как работает

Каждые 500 мс виджет выполняет `cat /tmp/aura_status.json` через
Plasma5Support.DataSource (engine: executable). XMLHttpRequest
с file:// в Plasma 6 блокируется — поэтому именно exec.

aura/status.py пишет файл атомарно (tmp + os.replace) при каждой
смене состояния: idle / listening / thinking / speaking / error.

## Цвета

- idle      — синий, ждёт Аура
- listening — жёлтый, слушает
- thinking  — оранжевый, думает
- speaking  — зелёный, говорит
- error     — красный, ошибка
- unknown   — серый, нет данных
