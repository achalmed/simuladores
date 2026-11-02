// EspacioSimulacion — la vista principal (reingeniería L2, L7, L8): el gráfico grande del escenario (sólido) sobre la
// base (punteada), que se redibuja al mover los parámetros; «Evolución temporal» cuando el eje x es el tiempo; debajo,
// los resultados numéricos frente a la base. Si la corrida no puede presentarse como válida (verificaciones fallidas,
// sin verificar, números no finitos), el gráfico lleva la marca, la tabla se atenúa y el motivo va arriba.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

ColumnLayout {
    id: raiz
    readonly property var m: studio.modelos
    readonly property var v: m.validez
    readonly property bool valido: v.valido === true
    readonly property bool figura: studio.ajustes.figuraAcademica && m.figura !== ""
    spacing: 0

    Kirigami.InlineMessage {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        visible: raiz.m.hayCorrida && !raiz.valido && (raiz.v.titulo || "") !== ""
        type: raiz.v.nivel === "negativo" ? Kirigami.MessageType.Error : Kirigami.MessageType.Warning
        text: "<b>" + (raiz.v.titulo || "") + "</b> — " + (raiz.v.texto || "")
    }
    QQC2.SplitView {
        Layout.fillWidth: true
        Layout.fillHeight: true
        orientation: Qt.Vertical

        ColumnLayout {
            QQC2.SplitView.fillHeight: true
            QQC2.SplitView.minimumHeight: Kirigami.Units.gridUnit * 12
            spacing: 0
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.largeSpacing
                Layout.rightMargin: Kirigami.Units.largeSpacing
                Layout.topMargin: Kirigami.Units.smallSpacing
                Kirigami.Heading {
                    level: 4
                    text: raiz.m.temporal ? "Evolución temporal" : "Simulación"
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    text: raiz.m.hayCorrida ? "escenario «" + raiz.m.escenario + "»" + (raiz.m.escenario !== "base" ? " sobre la base (punteada)" : "")
                                              + (raiz.figura ? " · figura académica (matplotlib)" : "") : ""
                    color: Kirigami.Theme.disabledTextColor
                    elide: Text.ElideRight
                }
            }
            GraficoCientifico {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: Kirigami.Units.smallSpacing
                visible: !raiz.figura
                datos: raiz.m.grafico
                base: raiz.m.escenario !== "base" && raiz.m.hayCorrida ? raiz.m.graficoBase : null
                limites: raiz.m.escenario !== "base" ? raiz.m.limitesComunes : null
                invalido: raiz.m.hayCorrida && !raiz.valido ? (raiz.v.titulo || "") : ""
                nivelInvalido: raiz.v.nivel || "negativo"
                motivoInvalido: raiz.v.texto || ""
                mensajeVacio: !raiz.m.hayActual ? "Elige un modelo del catálogo"
                              : (!raiz.m.cargado ? "No se pudo importar el modelo: " + raiz.m.motivoNoCargado : "Sin corrida: córrelo (F5)")
                nombreAccesible: "Gráfico de " + (raiz.m.id || "ningún modelo")
            }
            Image {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: Kirigami.Units.smallSpacing
                visible: raiz.figura
                source: raiz.figura ? raiz.m.figura : ""
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                Accessible.name: "Figura académica de " + raiz.m.id
            }
        }
        ColumnLayout {
            QQC2.SplitView.preferredHeight: Kirigami.Units.gridUnit * 10
            QQC2.SplitView.minimumHeight: Kirigami.Units.gridUnit * 5
            spacing: 0
            Kirigami.Separator { Layout.fillWidth: true }
            RowLayout {
                Layout.fillWidth: true
                Layout.margins: Kirigami.Units.smallSpacing
                Kirigami.Icon {
                    source: raiz.valido ? "data-success" : (raiz.v.nivel === "negativo" ? "data-error" : "data-warning")
                    color: raiz.valido ? Kirigami.Theme.positiveTextColor : (raiz.v.nivel === "negativo" ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.neutralTextColor)
                    implicitWidth: Kirigami.Units.iconSizes.small
                    implicitHeight: implicitWidth
                    visible: raiz.m.hayCorrida
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    text: !raiz.m.hayCorrida ? "Resultados" : (raiz.valido ? "Resultados frente a la base · verificados"
                                                                          : "Resultados " + (raiz.v.titulo || "").toLowerCase() + ": no se dan por buenos")
                    font.bold: true
                    elide: Text.ElideRight
                }
                QQC2.Label {
                    text: raiz.m.fechaCorrida
                    font: Kirigami.Theme.smallFont
                    color: Kirigami.Theme.disabledTextColor
                }
            }
            TablaDatos {
                Layout.fillWidth: true
                Layout.fillHeight: true
                opacity: raiz.m.hayCorrida && !raiz.valido ? 0.5 : 1
                modelo: raiz.m.resultadosModelo
                claveAjustes: "resultados"
                umbralEstrecho: 0
                mensajeVacio: raiz.m.hayCorrida ? "Este modelo no declara resultados" : "Sin corrida"
                iconoVacio: "view-list-details"
                columnas: [{ ancho: 0, minimo: 8 }, { ancho: 6, alinear: "derecha", mono: true }, { ancho: 6, alinear: "derecha", mono: true },
                           { ancho: 6, alinear: "derecha", mono: true, semantica: true }, { ancho: 5, alinear: "derecha", secundaria: true }]
            }
        }
    }
}
