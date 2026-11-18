// EspacioSimulacion — la vista principal (reingeniería L2, L7, L8; forma del laboratorio, 2026-11-18): las curvas del
// escenario (sólidas) sobre las de la base (punteadas), que se mueven al arrastrar los parámetros; el equilibrio, marcado
// en el gráfico y dicho con sus cifras arriba, frente al de la base; «Evolución temporal» cuando el eje x es el tiempo;
// debajo, los resultados numéricos frente a la base. Si la corrida no puede presentarse como válida (verificaciones
// fallidas, sin verificar, números no finitos), el gráfico lleva la marca, la tabla se atenúa y el motivo va arriba, en
// una línea con el color de estado del tema (es un estado, no un aviso: no va a Mensajes).
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
    readonly property var eq: m.hayCorrida && m.grafico ? (m.grafico.equilibrio || null) : null
    readonly property var eqBase: m.escenario !== "base" && m.graficoBase ? (m.graficoBase.equilibrio || null) : null
    readonly property color colorNivel: v.nivel === "negativo" ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.neutralTextColor
    spacing: 0

    // una cifra del equilibrio, con los decimales que su tamaño pide
    function cifra(x) {
        const a = Math.abs(x)
        return Number(x).toLocaleString(Qt.locale(), "f", a >= 1000 ? 0 : (a >= 10 ? 1 : (a >= 1 ? 2 : 3)))
    }

    RowLayout {
        Layout.fillWidth: true
        Layout.leftMargin: Kirigami.Units.largeSpacing
        Layout.rightMargin: Kirigami.Units.largeSpacing
        Layout.topMargin: Kirigami.Units.smallSpacing
        visible: raiz.m.hayCorrida && !raiz.valido && (raiz.v.titulo || "") !== ""
        spacing: Kirigami.Units.smallSpacing
        Kirigami.Icon {
            source: raiz.v.nivel === "negativo" ? "data-error" : "data-warning"
            color: raiz.colorNivel
            implicitWidth: Kirigami.Units.iconSizes.small
            implicitHeight: implicitWidth
            Layout.alignment: Qt.AlignTop
        }
        QQC2.Label {
            Layout.fillWidth: true
            text: "<b>" + (raiz.v.titulo || "") + "</b> · " + (raiz.v.texto || "")
            textFormat: Text.StyledText
            color: raiz.colorNivel
            wrapMode: Text.WordWrap
        }
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
            // el equilibrio con sus cifras: el mismo punto que marca el gráfico (el acento del tema), y el de la base
            RowLayout {
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.largeSpacing
                Layout.rightMargin: Kirigami.Units.largeSpacing
                visible: raiz.eq !== null && !raiz.figura
                spacing: Kirigami.Units.smallSpacing
                QQC2.Label { text: "●"; color: Kirigami.Theme.highlightColor; Accessible.ignored: true }
                QQC2.Label {
                    text: raiz.eq ? "Equilibrio E: " + (raiz.m.grafico.etiquetaX || "x") + " = " + raiz.cifra(raiz.eq.x)
                                    + " · " + (raiz.m.grafico.etiquetaY || "y") + " = " + raiz.cifra(raiz.eq.y) : ""
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                    Layout.maximumWidth: raiz.width * 0.7
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    visible: raiz.eqBase !== null
                    text: raiz.eqBase ? "base: " + raiz.cifra(raiz.eqBase.x) + " · " + raiz.cifra(raiz.eqBase.y) : ""
                    color: Kirigami.Theme.disabledTextColor
                    elide: Text.ElideRight
                }
            }
            GraficoXY {
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
            QQC2.SplitView.preferredHeight: Kirigami.Units.gridUnit * 8
            QQC2.SplitView.minimumHeight: Kirigami.Units.gridUnit * 4
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
