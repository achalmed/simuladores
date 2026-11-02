// CatalogoModelos — la entrada del laboratorio (reingeniería L1): los modelos por disciplina, buscables (Ctrl+F) y
// filtrables por disciplina y estado de verificación, agrupados por disciplina y sección. Cada modelo dice su estado
// con un icono; el actual queda resaltado. Elegir uno lo abre en el espacio de simulación.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

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
            Flow {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing
                QQC2.Button {
                    text: "Todas"
                    checkable: true
                    checked: raiz.e.disciplina === ""
                    flat: !checked
                    onClicked: raiz.e.fijarDisciplina("")
                }
                Repeater {
                    model: raiz.m.disciplinas
                    delegate: QQC2.Button {
                        required property var modelData
                        text: modelData.texto
                        icon.name: modelData.icono
                        checkable: true
                        checked: raiz.e.disciplina === modelData.nombre
                        flat: !checked
                        onClicked: raiz.e.fijarDisciplina(checked ? modelData.nombre : "")
                    }
                }
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
                    highlighted: actual
                    onClicked: { lista.currentIndex = index; raiz.m.irA(ref) }
                    Keys.onReturnPressed: raiz.m.irA(ref)
                    Accessible.name: model.id + " " + model.titulo + ", " + model.estado
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.smallSpacing
                        Kirigami.Icon {
                            source: fila.clave === "verificado" ? "data-success" : (fila.clave === "diferencias" ? "data-error" : "data-information")
                            color: fila.clave === "verificado" ? Kirigami.Theme.positiveTextColor
                                   : (fila.clave === "diferencias" ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.neutralTextColor)
                            implicitWidth: Kirigami.Units.iconSizes.small
                            implicitHeight: implicitWidth
                            Layout.alignment: Qt.AlignTop
                            Layout.topMargin: 2
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            QQC2.Label {
                                Layout.fillWidth: true
                                text: "<b>" + fila.model.id + "</b> · " + fila.model.titulo
                                textFormat: Text.StyledText
                                elide: Text.ElideRight
                                color: fila.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
                            }
                            QQC2.Label {
                                Layout.fillWidth: true
                                text: (fila.model.seccion ? fila.model.seccion + " · " : "") + "nivel " + fila.model.nivelCurricular + " · " + fila.model.estado
                                font: Kirigami.Theme.smallFont
                                elide: Text.ElideRight
                                color: fila.highlighted ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.disabledTextColor
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
