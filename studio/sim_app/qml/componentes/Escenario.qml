// Escenario — el escenario del modelo actual: el selector (la base, los del modelo y los propios del studio), su
// lectura y su mecanismo, y el formulario generado desde los parámetros del modelo (un deslizador por Parametro,
// agrupados por su grupo). Mover un parámetro deja el escenario como «propio»; F5 lo corre.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

QQC2.ScrollView {
    id: pagina
    readonly property var m: studio.modelos
    readonly property var grupos: {
        const vistos = [], salida = []
        for (const p of m.parametros) { const g = p.grupo || ""; if (vistos.indexOf(g) < 0) { vistos.push(g); salida.push(g) } }
        return salida
    }
    function formato(v, unidad) {
        const a = Math.abs(v)
        const texto = (a >= 1000 || (a >= 10 && Number.isInteger(v))) ? Number(v).toLocaleString(Qt.locale(), "f", 0) : (a >= 10 ? Number(v).toLocaleString(Qt.locale(), "f", 1) : Number(v).toLocaleString(Qt.locale(), "f", 3).replace(/0+$/, "").replace(/[.,]$/, ""))
        return texto + (unidad ? " " + unidad : "")
    }
    contentWidth: availableWidth
    QQC2.ScrollBar.horizontal.policy: QQC2.ScrollBar.AlwaysOff
    ColumnLayout {
        id: columna
        width: pagina.availableWidth - Kirigami.Units.largeSpacing * 2
        x: Kirigami.Units.largeSpacing
        y: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing
        Kirigami.PlaceholderMessage {
            Layout.fillWidth: true
            visible: !pagina.m.cargado
            text: pagina.m.hayActual ? "El modelo no se pudo importar" : "Ningún modelo"
            explanation: pagina.m.hayActual ? pagina.m.motivoNoCargado : "Elige un modelo en la tabla."
            icon.name: pagina.m.hayActual ? "data-error" : "office-chart-line"
        }
        Kirigami.FormLayout {
            visible: pagina.m.cargado
            Layout.fillWidth: true
            QQC2.ComboBox {
                id: selector
                Kirigami.FormData.label: "Escenario:"
                Layout.fillWidth: true
                Layout.maximumWidth: columna.width - Kirigami.Units.gridUnit * 7      // un FormLayout no acorta un ComboBox con un texto largo
                model: pagina.m.escenarios
                textRole: "descripcion"
                currentIndex: pagina.m.indiceEscenario
                displayText: pagina.m.indiceEscenario < 0 ? pagina.m.textoEscenario : currentText
                onActivated: index => pagina.m.aplicarEscenarioPorIndice(index)
                Accessible.name: "Escenario"
                Connections { target: pagina.m; function onValoresCambiados() { selector.currentIndex = pagina.m.indiceEscenario } }
            }
            RowLayout {
                Kirigami.FormData.label: " "
                spacing: Kirigami.Units.smallSpacing
                BotonAccion { accion: studio.acciones.accion("modelo.correr") }
                BotonAccion { accion: studio.acciones.accion("modelo.restablecer") }
                BotonAccion { accion: studio.acciones.accion("op.guardar_escenario"); conTexto: true }
            }
        }
        QQC2.Label {                                                     // fuera del FormLayout: un Markdown largo no se ajusta dentro
            visible: pagina.m.cargado
            Layout.fillWidth: true
            text: pagina.m.lecturaEscenario
            textFormat: Text.MarkdownText
            wrapMode: Text.WordWrap
            Accessible.name: "Lectura del escenario"
        }
        Repeater {
            model: pagina.m.cargado ? pagina.grupos : []
            Kirigami.FormLayout {
                id: forma
                required property string modelData
                Layout.fillWidth: true
                Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: forma.modelData ? forma.modelData.charAt(0).toUpperCase() + forma.modelData.slice(1) : "Parámetros" }
                Repeater {
                    model: pagina.m.parametros.filter(p => (p.grupo || "") === forma.modelData)
                    ColumnLayout {
                        id: campo
                        required property var modelData
                        readonly property real valor: pagina.m.valores[modelData.nombre] !== undefined ? pagina.m.valores[modelData.nombre] : modelData.valor
                        Kirigami.FormData.label: modelData.etiqueta + ":"
                        Kirigami.FormData.labelAlignment: Qt.AlignTop
                        Layout.fillWidth: true
                        spacing: 0
                        RowLayout {
                            Layout.fillWidth: true
                            QQC2.Slider {
                                id: barra
                                Layout.fillWidth: true
                                from: campo.modelData.minimo
                                to: campo.modelData.maximo
                                stepSize: campo.modelData.paso
                                value: campo.valor
                                onMoved: pagina.m.fijarValor(campo.modelData.nombre, value)
                                Accessible.name: campo.modelData.etiqueta
                                QQC2.ToolTip.text: campo.modelData.definicion
                                QQC2.ToolTip.visible: hovered && campo.modelData.definicion !== ""
                            }
                            QQC2.Label {
                                Layout.preferredWidth: Kirigami.Units.gridUnit * 5
                                horizontalAlignment: Text.AlignRight
                                text: pagina.formato(campo.valor, campo.modelData.unidad)
                                font.bold: Math.abs(campo.valor - campo.modelData.valor) > 1e-9
                            }
                        }
                        QQC2.Label {
                            visible: campo.modelData.definicion !== ""
                            Layout.fillWidth: true
                            text: campo.modelData.definicion
                            wrapMode: Text.WordWrap
                            font: Kirigami.Theme.smallFont
                            color: Kirigami.Theme.disabledTextColor
                        }
                    }
                }
            }
        }
        Item { Layout.preferredHeight: Kirigami.Units.largeSpacing }
    }
}
