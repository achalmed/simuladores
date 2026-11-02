// Resultados — la última corrida del modelo actual: el gráfico en vivo (GuiComun.Grafico sobre QuickCharts, con la
// figura académica de matplotlib como alternativa) y las magnitudes del escenario frente a la base (Δ y Δ %).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

ColumnLayout {
    id: pagina
    readonly property var m: studio.modelos
    readonly property var g: m.grafico
    readonly property bool figura: studio.ajustes.figuraAcademica && m.figura !== ""
    spacing: 0
    Grafico {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: Kirigami.Units.gridUnit * 12
        series: pagina.g.series || []
        etiquetasX: pagina.g.etiquetasX || []
        xMinimo: pagina.g.xMinimo !== undefined ? pagina.g.xMinimo : 0
        xMaximo: pagina.g.xMaximo !== undefined ? pagina.g.xMaximo : 1
        yMinimo: pagina.g.yMinimo !== undefined ? pagina.g.yMinimo : 0
        yMaximo: pagina.g.yMaximo !== undefined ? pagina.g.yMaximo : 1
        barras: pagina.g.barras || ({})
        puntos: pagina.g.puntos || []
        equilibrio: pagina.g.equilibrio !== undefined ? pagina.g.equilibrio : null
        marcas: pagina.g.marcas || []
        etiquetaX: pagina.g.etiquetaX || ""
        etiquetaY: pagina.g.etiquetaY || ""
        anotacion: pagina.g.anotacion || ""
        imagen: pagina.m.figura
        preferirImagen: pagina.figura
        mensajeVacio: !pagina.m.hayActual ? "Ningún modelo" : "Sin corrida: elige el escenario y córrelo (F5)"
        nombreAccesible: "Gráfico de " + (pagina.m.id || "ningún modelo")
    }
    Kirigami.Separator { Layout.fillWidth: true }
    QQC2.Label {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        visible: pagina.m.hayCorrida
        text: "Escenario «" + pagina.m.escenario + "» frente a la base · " + pagina.m.fechaCorrida + (pagina.figura ? " · figura académica (matplotlib)" : "")
        font: Kirigami.Theme.smallFont
        color: Kirigami.Theme.disabledTextColor
        elide: Text.ElideRight
    }
    TablaDatos {
        Layout.fillWidth: true
        Layout.preferredHeight: Kirigami.Units.gridUnit * 10
        modelo: pagina.m.resultadosModelo
        claveAjustes: "resultados"
        umbralEstrecho: 0
        mensajeVacio: pagina.m.hayCorrida ? "Este modelo no declara resultados" : ""
        iconoVacio: "view-list-details"
        columnas: [{ ancho: 0, minimo: 8 }, { ancho: 5, alinear: "derecha", mono: true }, { ancho: 5, alinear: "derecha", mono: true },
                   { ancho: 5, alinear: "derecha", mono: true, semantica: true }, { ancho: 4, alinear: "derecha", secundaria: true }]
    }
}
