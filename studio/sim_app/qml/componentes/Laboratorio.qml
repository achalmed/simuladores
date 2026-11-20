// Laboratorio — lo que no es el experimento en vivo: las operaciones del modelo, la disciplina y el laboratorio (la
// CLI, exportar, guardar un escenario, regenerar los contratos de los pubs) con su orden exacta, el registro de la
// última corrida y la salida del motor. Como la consola de RStudio: a mano, pero no protagonista.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

ColumnLayout {
    id: raiz
    readonly property var ops: studio.operaciones
    property int pestana: 0
    spacing: 0

    QQC2.ToolBar {
        Layout.fillWidth: true
        RowLayout {
            anchors.fill: parent
            spacing: Kirigami.Units.smallSpacing
            SelectorSegmentado {
                id: pestanas
                titulo: "Laboratorio"
                opciones: [{ clave: "0", texto: "Operación", icono: "system-run" },
                           { clave: "1", texto: "Registro de la corrida", icono: "view-history" },
                           { clave: "2", texto: "Salida del motor", icono: "utilities-terminal" }]
                actual: String(raiz.pestana)
                onElegida: clave => raiz.pestana = Number(clave)
            }
            Item { Layout.fillWidth: true }
            QQC2.Label { text: "Operación:"; visible: raiz.pestana === 0 }
            QQC2.ComboBox {
                id: selector
                visible: raiz.pestana === 0
                Layout.preferredWidth: Kirigami.Units.gridUnit * 15
                model: raiz.ops.lista
                textRole: "titulo"
                currentIndex: raiz.ops.indiceActual
                onActivated: index => raiz.ops.fijarPorIndice(index)
                Accessible.name: "Operación"
                Connections { target: raiz.ops; function onCambiado() { selector.currentIndex = raiz.ops.indiceActual } }
            }
        }
    }
    StackLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        currentIndex: raiz.pestana
        Operacion {}
        Registro {}
        PanelInferior { consola: studio.consola }
    }
}
