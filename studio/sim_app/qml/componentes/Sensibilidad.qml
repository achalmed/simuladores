// Sensibilidad — el barrido de un parámetro sobre su rango declarado (reingeniería L6): la magnitud elegida frente al
// parámetro alrededor del escenario en edición (los demás parámetros, en sus valores; sin cambios es `base.sensibilidad`
// del motor, la base), con su valor marcado y la derivada ∂magnitud/∂parámetro en él; los puntos del rango donde el
// modelo no calcula se dicen y quedan fuera de la curva. Con el recálculo en vivo, mover un parámetro vuelve a barrer.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

ColumnLayout {
    id: raiz
    readonly property var m: studio.modelos
    readonly property var s: m.sensibilidad
    readonly property var nombres: m.parametros.map(p => p.nombre)
    readonly property var v: m.validez
    function barrer() {
        if (m.cargado && nombres.length) m.calcularSensibilidad(nombres[Math.max(0, parametro.currentIndex)], magnitud.currentIndex >= 0 ? magnitud.currentText : "")
    }
    function numero(x) { return x === null || x === undefined ? "—" : Number(x).toLocaleString(Qt.locale(), "g", 4) }
    spacing: 0
    onVisibleChanged: if (visible && (s.x === undefined || s.parametro !== m.parametroSensibilidad)) barrer()
    Connections { target: raiz.m; function onActualCambiado() { if (raiz.visible) Qt.callLater(raiz.barrer) } }
    // un parámetro movido: el barrido sigue al escenario si el modelo es rápido (en vivo); si no, «Barrer»
    Connections { target: raiz.m; function onValoresCambiados() { if (raiz.visible && raiz.m.vivo) rebarrer.restart() } }
    Timer { id: rebarrer; interval: 250; onTriggered: raiz.barrer() }

    RowLayout {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing
        QQC2.Label { text: "Parámetro:" }
        QQC2.ComboBox {
            id: parametro
            Layout.preferredWidth: Kirigami.Units.gridUnit * 12
            model: raiz.m.parametros
            textRole: "etiqueta"
            currentIndex: Math.max(0, raiz.nombres.indexOf(raiz.m.parametroSensibilidad))
            onActivated: raiz.barrer()
            Accessible.name: "Parámetro que se barre"
        }
        QQC2.Label { text: "Magnitud:" }
        QQC2.ComboBox {
            id: magnitud
            Layout.preferredWidth: Kirigami.Units.gridUnit * 12
            model: raiz.m.magnitudes
            currentIndex: raiz.m.magnitudes.indexOf(raiz.m.magnitudSensibilidad)
            onActivated: raiz.barrer()
            Accessible.name: "Magnitud que se observa"
        }
        QQC2.ToolButton {
            icon.name: "view-refresh"
            text: "Barrer"
            enabled: raiz.m.cargado
            onClicked: raiz.barrer()
        }
        Item { Layout.fillWidth: true }
    }
    GraficoXY {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.margins: Kirigami.Units.smallSpacing
        datos: raiz.s.grafico || ({})
        marcaX: raiz.s.valorActual !== undefined ? raiz.s.valorActual : NaN
        invalido: raiz.m.hayCorrida && raiz.v.valido !== true ? (raiz.v.titulo || "") : ""
        nivelInvalido: raiz.v.nivel || "negativo"
        motivoInvalido: raiz.v.texto || ""
        mensajeVacio: !raiz.m.hayActual ? "Elige un modelo del catálogo" : (raiz.nombres.length ? "Elige un parámetro y una magnitud" : "Este modelo no declara parámetros")
        nombreAccesible: "Sensibilidad de " + (raiz.s.magnitud || "") + " a " + (raiz.s.etiqueta || "")
    }
    Kirigami.Separator { Layout.fillWidth: true }
    Kirigami.FormLayout {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        visible: raiz.s.x !== undefined
        QQC2.Label {
            Kirigami.FormData.label: raiz.s.escenario ? "Derivada en el escenario:" : "Derivada en la base:"
            text: "∂" + (raiz.s.magnitud || "") + " / ∂" + (raiz.s.parametro || "") + " = " + raiz.numero(raiz.s.derivada)
            font: Kirigami.Theme.fixedWidthFont
        }
        QQC2.Label {
            Kirigami.FormData.label: raiz.s.escenario ? "Valor del escenario:" : "Valor base:"
            text: (raiz.s.parametro || "") + " = " + raiz.numero(raiz.s.valorActual) + (raiz.s.unidad ? " " + raiz.s.unidad : "") + "  →  " + (raiz.s.magnitud || "") + " = " + raiz.numero(raiz.s.actual)
        }
        QQC2.Label {
            Kirigami.FormData.label: "Fijos del escenario:"
            visible: !!raiz.s.escenario && raiz.s.fijos !== undefined && Object.keys(raiz.s.fijos).length > 0
            text: raiz.s.fijos ? Object.keys(raiz.s.fijos).map(k => k + " = " + raiz.numero(raiz.s.fijos[k])).join(", ") : ""
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        QQC2.Label {
            Kirigami.FormData.label: "Rango barrido:"
            text: raiz.s.x && raiz.s.x.length ? raiz.numero(raiz.s.x[0]) + " … " + raiz.numero(raiz.s.x[raiz.s.x.length - 1]) + " (" + raiz.s.x.length + " puntos)" : "—"
        }
        QQC2.Label {
            Kirigami.FormData.label: "Fuera de dominio:"
            visible: !!raiz.s.fallidos && raiz.s.fallidos.length > 0
            text: raiz.s.fallidos ? raiz.s.fallidos.length + " punto(s) donde el modelo no calcula: " + raiz.s.fallidos.map(x => raiz.numero(x)).join(", ") : ""
            color: Kirigami.Theme.neutralTextColor
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }
}
