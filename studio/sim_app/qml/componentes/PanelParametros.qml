// PanelParametros — los controles del experimento (reingeniería L4–L5): el escenario (la base, los del modelo y los
// propios), el modo en vivo, y un deslizador por parámetro con el rango, el paso y la unidad que el modelo declara,
// agrupados por su grupo. El valor se escribe también a mano; el que se aparta de la base va resaltado con la base al
// lado. Mover un deslizador recalcula en vivo cuando el modelo lo permite; si no, F5.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

QQC2.Control {
    id: raiz
    readonly property var m: studio.modelos

    function texto(v, paso) {
        const decimales = paso >= 1 ? 0 : Math.min(4, Math.max(1, Math.ceil(-Math.log10(paso))))
        return Number(v).toLocaleString(Qt.locale(), "f", decimales)
    }

    padding: 0
    Accessible.name: "Parámetros"

    contentItem: ColumnLayout {
        spacing: 0
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.largeSpacing
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Heading { level: 4; text: "Escenario" }
            QQC2.ComboBox {
                id: selector
                Layout.fillWidth: true
                model: raiz.m.escenarios
                textRole: "nombre"
                currentIndex: raiz.m.indiceEscenario
                displayText: raiz.m.escenario === "propio" ? "propio (los valores de abajo)" : currentText
                onActivated: index => raiz.m.aplicarEscenarioPorIndice(index)
                Accessible.name: "Escenario"
                QQC2.ToolTip.text: raiz.m.textoEscenario
                QQC2.ToolTip.visible: hovered && raiz.m.textoEscenario !== ""
            }
            QQC2.Label {
                Layout.fillWidth: true
                text: raiz.m.textoEscenario
                wrapMode: Text.WordWrap
                font: Kirigami.Theme.smallFont
                color: Kirigami.Theme.disabledTextColor
                visible: text !== "" && raiz.m.escenario !== "propio"
            }
            RowLayout {
                Layout.fillWidth: true
                QQC2.Switch {
                    id: vivo
                    text: "En vivo"
                    checked: raiz.m.vivo
                    onToggled: raiz.m.vivo = checked
                    QQC2.ToolTip.text: "Recalcular al mover un parámetro; se apaga solo si el modelo tarda más de 400 ms (entonces, F5)"
                    QQC2.ToolTip.visible: hovered
                }
                Item { Layout.fillWidth: true }
                QQC2.Label {
                    visible: raiz.m.hayCorrida
                    text: raiz.m.msCorrida.toLocaleString(Qt.locale(), "f", 0) + " ms"
                    font: Kirigami.Theme.smallFont
                    color: Kirigami.Theme.disabledTextColor
                    Accessible.name: "Tiempo de la última corrida"
                }
            }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        QQC2.ScrollView {
            id: desplazable
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: availableWidth
            QQC2.ScrollBar.horizontal.policy: QQC2.ScrollBar.AlwaysOff
            ColumnLayout {
                width: desplazable.availableWidth
                spacing: 0
                Repeater {
                    model: raiz.m.parametros
                    delegate: ColumnLayout {
                        id: parametro
                        required property var modelData
                        required property int index
                        readonly property real valor: raiz.m.valores[modelData.nombre] !== undefined ? raiz.m.valores[modelData.nombre] : modelData.valor
                        readonly property bool cambiado: Math.abs(valor - modelData.valor) > Math.max(1e-12, modelData.paso * 1e-6)
                        readonly property bool nuevoGrupo: index === 0 || raiz.m.parametros[index - 1].grupo !== modelData.grupo
                        Layout.fillWidth: true
                        Layout.leftMargin: Kirigami.Units.largeSpacing
                        Layout.rightMargin: Kirigami.Units.largeSpacing
                        spacing: 0
                        Kirigami.ListSectionHeader {
                            Layout.fillWidth: true
                            Layout.leftMargin: -Kirigami.Units.largeSpacing
                            Layout.rightMargin: -Kirigami.Units.largeSpacing
                            visible: parametro.nuevoGrupo && parametro.modelData.grupo !== ""
                            text: parametro.modelData.grupo
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            Layout.topMargin: Kirigami.Units.smallSpacing
                            QQC2.Label {
                                Layout.fillWidth: true
                                text: parametro.modelData.etiqueta + (parametro.modelData.unidad ? " (" + parametro.modelData.unidad + ")" : "")
                                elide: Text.ElideRight
                                font.weight: parametro.cambiado ? Font.DemiBold : Font.Normal
                                QQC2.ToolTip.text: parametro.modelData.nombre + (parametro.modelData.definicion ? ": " + parametro.modelData.definicion : "")
                                QQC2.ToolTip.visible: zona.hovered
                                HoverHandler { id: zona }
                            }
                            QQC2.TextField {
                                id: campo
                                Layout.preferredWidth: Kirigami.Units.gridUnit * 4.5
                                horizontalAlignment: Text.AlignRight
                                font.family: Kirigami.Theme.fixedWidthFont.family
                                font.weight: parametro.cambiado ? Font.Bold : Font.Normal
                                text: raiz.texto(parametro.valor, parametro.modelData.paso)
                                validator: DoubleValidator { bottom: parametro.modelData.minimo; top: parametro.modelData.maximo; locale: Qt.locale().name }
                                onEditingFinished: {
                                    const v = Number.fromLocaleString(Qt.locale(), text)
                                    if (!isNaN(v)) raiz.m.fijarValor(parametro.modelData.nombre, v)
                                    text = Qt.binding(() => raiz.texto(parametro.valor, parametro.modelData.paso))
                                }
                                Accessible.name: parametro.modelData.etiqueta
                            }
                        }
                        QQC2.Slider {
                            id: deslizador
                            Layout.fillWidth: true
                            from: parametro.modelData.minimo
                            to: parametro.modelData.maximo
                            stepSize: parametro.modelData.paso
                            snapMode: QQC2.Slider.SnapAlways
                            value: parametro.valor
                            onMoved: raiz.m.fijarValor(parametro.modelData.nombre, value)
                            Accessible.name: parametro.modelData.etiqueta
                            // la marca de la base
                            Rectangle {
                                visible: parametro.cambiado
                                width: 2
                                height: Kirigami.Units.gridUnit * 0.7
                                radius: 1
                                color: Kirigami.Theme.disabledTextColor
                                y: deslizador.topPadding + deslizador.availableHeight / 2 - height / 2
                                x: deslizador.leftPadding + (parametro.modelData.valor - deslizador.from) / Math.max(1e-12, deslizador.to - deslizador.from) * deslizador.availableWidth - 1
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            QQC2.Label { text: raiz.texto(parametro.modelData.minimo, parametro.modelData.paso); font: Kirigami.Theme.smallFont; color: Kirigami.Theme.disabledTextColor }
                            Item { Layout.fillWidth: true }
                            QQC2.Label {
                                visible: parametro.cambiado
                                text: "base " + raiz.texto(parametro.modelData.valor, parametro.modelData.paso)
                                font: Kirigami.Theme.smallFont
                                color: Kirigami.Theme.disabledTextColor
                            }
                            Item { Layout.fillWidth: true }
                            QQC2.Label { text: raiz.texto(parametro.modelData.maximo, parametro.modelData.paso); font: Kirigami.Theme.smallFont; color: Kirigami.Theme.disabledTextColor }
                        }
                    }
                }
                Kirigami.PlaceholderMessage {
                    Layout.fillWidth: true
                    Layout.margins: Kirigami.Units.largeSpacing
                    visible: raiz.m.parametros.length === 0
                    text: raiz.m.hayActual ? "Este modelo no declara parámetros" : "Ningún modelo"
                }
                Item { Layout.preferredHeight: Kirigami.Units.largeSpacing }
            }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing
            BotonAccion { accion: studio.acciones.accion("modelo.restablecer") }
            Item { Layout.fillWidth: true }
            BotonAccion { accion: studio.acciones.accion("modelo.correr"); conTexto: !raiz.m.vivo }
        }
    }
}
