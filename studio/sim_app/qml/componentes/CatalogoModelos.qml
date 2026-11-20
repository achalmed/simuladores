// CatalogoModelos — la entrada del laboratorio (reingeniería L1): los modelos por disciplina, buscables (Ctrl+F) y
// filtrables por disciplina y estado de verificación, agrupados por disciplina y sección. Cada modelo dice su estado
// con un icono; el actual queda resaltado. Elegir uno lo abre en el espacio de simulación.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

QQC2.Control {
    id: raiz
    readonly property var m: studio.modelos
    readonly property var e: studio.espacio
    function enfocar() { campo.forceActiveFocus(); campo.selectAll() }

    padding: 0
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    background: Rectangle { color: Kirigami.Theme.backgroundColor }
    Accessible.name: "Catálogo de modelos"

    contentItem: ColumnLayout {
        spacing: 0
        ColumnLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing
            Kirigami.SearchField {
                id: campo
                Layout.fillWidth: true
                placeholderText: "Buscar un modelo (Ctrl+F)"
                onTextChanged: raiz.m.buscar(text)
                Keys.onEscapePressed: text = ""
                Keys.onDownPressed: lista.forceActiveFocus()
                Accessible.name: "Buscar un modelo"
            }
            // las disciplinas: un selector segmentado (gui-comun 4.2), «Todas» primero; el acento sale del tema
            SelectorSegmentado {
                id: disciplinas
                Layout.maximumWidth: parent.width
                titulo: "Disciplina"
                compacto: raiz.m.disciplinas.length > 2
                opciones: [{ clave: "", texto: "Todas", descripcion: "Los modelos de todas las disciplinas" }].concat(
                              raiz.m.disciplinas.map(d => ({ clave: d.nombre, texto: d.texto, descripcion: "Solo " + d.texto })))
                actual: raiz.e.disciplina
                onElegida: clave => raiz.e.fijarDisciplina(clave)
            }
            QQC2.ComboBox {
                id: estados
                Layout.fillWidth: true
                readonly property var claves: ["", "verificado", "diferencias", "sin_verificar"]
                model: ["Todos los estados (" + raiz.m.total + ")",
                        "Verificados (" + (raiz.m.contadores.verificado || 0) + ")",
                        "Con diferencias (" + (raiz.m.contadores.diferencias || 0) + ")",
                        "Sin verificar (" + (raiz.m.contadores.sin_verificar || 0) + ")"]
                currentIndex: Math.max(0, claves.indexOf(raiz.e.estado))
                onActivated: index => raiz.e.fijarEstado(claves[index])
                Accessible.name: "Estado de verificación"
            }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        QQC2.ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            ListView {
                id: lista
                clip: true
                model: raiz.m.catalogo
                keyNavigationEnabled: true
                activeFocusOnTab: true
                currentIndex: -1
                section.property: "textoDisciplina"
                section.criteria: ViewSection.FullString
                section.delegate: Kirigami.ListSectionHeader {
                    required property string section
                    width: ListView.view.width
                    text: section
                }
                delegate: QQC2.ItemDelegate {
                    id: fila
                    required property int index
                    required property var model
                    readonly property string ref: model.ref
                    readonly property string clave: model.clave
                    readonly property bool actual: ref === raiz.m.ref
                    width: ListView.view.width
                    leftPadding: Kirigami.Units.largeSpacing
                    // la elegida teñida con su marca (FondoFila), no el bloque lleno del acento: en Lliphi Oscuro el
                    // acento es el rojo de los errores y el modelo elegido parecía uno con fallos
                    background: FondoFila { control: fila; elegida: fila.actual }
                    onClicked: { lista.currentIndex = index; raiz.m.irA(ref) }
                    Keys.onReturnPressed: raiz.m.irA(ref)
                    Accessible.name: model.id + " " + model.titulo + ", " + model.estado + (actual ? ", elegido" : "")
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.smallSpacing + Kirigami.Units.smallSpacing / 2
                        // el estado: una palomita verde, un aspa roja o, sin verificar, un círculo hueco neutro (no la «i»
                        // del tema, que en oscuro sale del color del acento y se confunde con un error)
                        Item {
                            Layout.alignment: Qt.AlignTop
                            Layout.topMargin: Kirigami.Units.smallSpacing / 2
                            implicitWidth: Kirigami.Units.iconSizes.small
                            implicitHeight: implicitWidth
                            Kirigami.Icon {
                                anchors.fill: parent
                                visible: fila.clave !== "sin_verificar"
                                source: fila.clave === "verificado" ? "checkmark" : "data-error"
                                color: fila.clave === "verificado" ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.negativeTextColor
                            }
                            QQC2.Label {
                                visible: fila.clave === "sin_verificar"
                                anchors.centerIn: parent
                                text: "○"
                                color: Kirigami.Theme.disabledTextColor
                                Accessible.ignored: true
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            QQC2.Label {
                                Layout.fillWidth: true
                                text: "<b>" + fila.model.id + "</b> · " + fila.model.titulo
                                textFormat: Text.StyledText
                                elide: Text.ElideRight
                            }
                            QQC2.Label {
                                Layout.fillWidth: true
                                text: (fila.model.seccion ? fila.model.seccion + " · " : "") + "nivel " + fila.model.nivelCurricular + " · " + fila.model.estado
                                font: Kirigami.Theme.smallFont
                                elide: Text.ElideRight
                                color: Kirigami.Theme.disabledTextColor
                            }
                        }
                    }
                }
                Kirigami.PlaceholderMessage {
                    anchors.centerIn: parent
                    width: parent.width - Kirigami.Units.gridUnit * 2
                    visible: lista.count === 0
                    icon.name: "office-chart-line"
                    text: raiz.m.total === 0 ? "Ningún modelo" : "Ningún modelo cumple la búsqueda"
                    explanation: raiz.m.total === 0 ? "Falta catalogo.json en la raíz del laboratorio (python3 main.py catalogo --aplicar)" : ""
                }
            }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        QQC2.Label {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            text: raiz.m.visibles + " de " + raiz.m.total + " modelos"
            font: Kirigami.Theme.smallFont
            color: Kirigami.Theme.disabledTextColor
        }
    }
}
