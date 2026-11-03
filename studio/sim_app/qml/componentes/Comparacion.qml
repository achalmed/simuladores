// Comparacion — base y escenario lado a lado con la misma escala (reingeniería L5): dos gráficos con los límites
// comunes, la lectura del escenario (qué cambia y el mecanismo de transmisión que el modelo declara) y las diferencias
// numéricas. La validez se marca en los dos gráficos: el modelo es el mismo.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

ColumnLayout {
    id: raiz
    readonly property var m: studio.modelos
    readonly property var v: m.validez
    readonly property string marca: m.hayCorrida && v.valido !== true ? (v.titulo || "") : ""
    spacing: 0

    GridLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: Kirigami.Units.gridUnit * 12
        Layout.margins: Kirigami.Units.smallSpacing
        columns: raiz.width > Kirigami.Units.gridUnit * 40 ? 2 : 1
        columnSpacing: Kirigami.Units.largeSpacing
        rowSpacing: Kirigami.Units.smallSpacing
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Kirigami.Heading { level: 4; text: "Base"; Layout.leftMargin: Kirigami.Units.smallSpacing }
            GraficoXY {
                Layout.fillWidth: true
                Layout.fillHeight: true
                datos: raiz.m.graficoBase
                limites: raiz.m.limitesComunes
                invalido: raiz.marca
                nivelInvalido: raiz.v.nivel || "negativo"
                motivoInvalido: raiz.v.texto || ""
                mensajeVacio: raiz.m.hayActual ? "Sin corrida" : "Elige un modelo del catálogo"
                nombreAccesible: "Gráfico de la base"
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Kirigami.Heading { level: 4; text: "Escenario «" + raiz.m.escenario + "»"; Layout.leftMargin: Kirigami.Units.smallSpacing }
            GraficoXY {
                Layout.fillWidth: true
                Layout.fillHeight: true
                datos: raiz.m.grafico
                limites: raiz.m.limitesComunes
                invalido: raiz.marca
                nivelInvalido: raiz.v.nivel || "negativo"
                motivoInvalido: raiz.v.texto || ""
                mensajeVacio: raiz.m.hayActual ? "Sin corrida" : "Elige un modelo del catálogo"
                nombreAccesible: "Gráfico del escenario"
            }
        }
    }
    Kirigami.Separator { Layout.fillWidth: true }
    RowLayout {
        Layout.fillWidth: true
        Layout.preferredHeight: Kirigami.Units.gridUnit * 11
        spacing: 0
        VistaTexto {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: 2
            texto: raiz.m.lecturaEscenario
            markdown: true
            mensajeVacio: "La base no cambia nada: elige un escenario o mueve un parámetro"
            iconoVacio: "view-split-left-right"
            nombreAccesible: "Lectura del escenario"
        }
        Kirigami.Separator { Layout.fillHeight: true }
        TablaDatos {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredWidth: 3
            opacity: raiz.marca !== "" ? 0.5 : 1
            modelo: raiz.m.resultadosModelo
            claveAjustes: "comparacion"
            umbralEstrecho: 0
            mensajeVacio: raiz.m.hayCorrida ? "Este modelo no declara resultados" : "Sin corrida"
            iconoVacio: "view-list-details"
            columnas: [{ ancho: 0, minimo: 6 }, { ancho: 4, alinear: "derecha", mono: true }, { ancho: 4, alinear: "derecha", mono: true },
                       { ancho: 4, alinear: "derecha", mono: true, semantica: true }, { ancho: 4, alinear: "derecha", secundaria: true }]
        }
    }
}
