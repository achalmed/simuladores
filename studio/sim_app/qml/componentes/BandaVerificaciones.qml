// BandaVerificaciones — el pie del laboratorio (rediseño aprobado del 2026-11-18): las verificaciones del modelo contra
// la teoría, siempre a la vista bajo el gráfico y los parámetros. Arriba, el estado (cuántas pasan y cuándo), la fuente
// contra la que se verifica (la procedencia que declara el modelo o su disciplina) y Verificar (Ctrl+T); debajo, una
// fila por verificación con su resultado en el color de estado del tema, lo que el motor devolvió (valor, esperado,
// diferencia) y, en las citas, su propia fuente. La lista completa, con el detalle en varias líneas, es la vista
// Verificaciones (Ctrl+5): un doble clic en una fila lleva allí. Sin colores propios: Kirigami.Theme.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

QQC2.Control {
    id: raiz
    readonly property var m: studio.modelos
    readonly property string clave: m.estado
    signal verDetalle()

    function colorDe(ok, nivel) {
        if (nivel === "aviso") return Kirigami.Theme.neutralTextColor
        if (nivel === "otro") return Kirigami.Theme.disabledTextColor
        return ok ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.negativeTextColor
    }
    function iconoDe(ok, nivel) {
        if (nivel === "aviso") return "data-warning"
        if (nivel === "otro") return "data-information"
        return ok ? "data-success" : "data-error"
    }

    padding: 0
    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false
    background: Rectangle { color: Kirigami.Theme.backgroundColor }
    Accessible.name: "Verificaciones contra la teoría"

    contentItem: ColumnLayout {
        spacing: 0
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: Kirigami.Units.largeSpacing
            Layout.rightMargin: Kirigami.Units.smallSpacing
            Layout.topMargin: Kirigami.Units.smallSpacing
            Layout.bottomMargin: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon {
                source: raiz.clave === "verificado" ? "data-success" : (raiz.clave === "diferencias" ? "data-error" : "data-warning")
                color: raiz.clave === "verificado" ? Kirigami.Theme.positiveTextColor
                       : (raiz.clave === "diferencias" ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.neutralTextColor)
                implicitWidth: Kirigami.Units.iconSizes.small
                implicitHeight: implicitWidth
            }
            Kirigami.Heading {
                level: 5
                text: "Verificaciones contra la teoría"
            }
            QQC2.Label {
                text: raiz.m.resumenVerificacion
                color: raiz.clave === "verificado" ? Kirigami.Theme.positiveTextColor
                       : (raiz.clave === "diferencias" ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.neutralTextColor)
                elide: Text.ElideRight
                Layout.maximumWidth: raiz.width * 0.4
            }
            QQC2.Label {
                Layout.fillWidth: true
                text: raiz.m.fuenteVerificaciones ? "· fuente: " + raiz.m.fuenteVerificaciones : ""
                color: Kirigami.Theme.disabledTextColor
                elide: Text.ElideRight
                QQC2.ToolTip.text: raiz.m.fuenteVerificaciones
                QQC2.ToolTip.visible: zonaFuente.hovered && truncated
                HoverHandler { id: zonaFuente }
            }
            BotonAccion { accion: studio.acciones.accion("modelo.verificar") }
            QQC2.ToolButton {
                icon.name: "view-list-details"
                display: QQC2.AbstractButton.IconOnly
                text: "Todas las verificaciones (Ctrl+5)"
                onClicked: raiz.verDetalle()
                QQC2.ToolTip.text: text
                QQC2.ToolTip.visible: hovered
                Accessible.name: text
            }
        }
        Kirigami.Separator { Layout.fillWidth: true }
        ListView {
            id: lista
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: raiz.m.verificacionesModelo
            boundsBehavior: Flickable.StopAtBounds
            QQC2.ScrollBar.vertical: QQC2.ScrollBar {}
            delegate: QQC2.ItemDelegate {
                id: fila
                required property var model
                required property int index
                readonly property bool cita: String(model.mensaje).indexOf("cita ·") === 0
                width: ListView.view.width
                topPadding: Kirigami.Units.smallSpacing / 2
                bottomPadding: Kirigami.Units.smallSpacing / 2
                onDoubleClicked: raiz.verDetalle()
                Accessible.name: (model.ok ? "Pasa: " : "Falla: ") + model.mensaje + ". " + model.detalle
                QQC2.ToolTip.text: model.detalle + (fila.cita && model.fuente ? "\n" + model.fuente : "")
                QQC2.ToolTip.visible: hovered
                QQC2.ToolTip.delay: Kirigami.Units.toolTipDelay
                contentItem: RowLayout {
                    spacing: Kirigami.Units.smallSpacing
                    Kirigami.Icon {
                        source: raiz.iconoDe(fila.model.ok, fila.model.nivel)
                        color: raiz.colorDe(fila.model.ok, fila.model.nivel)
                        implicitWidth: Kirigami.Units.iconSizes.small
                        implicitHeight: implicitWidth
                    }
                    QQC2.Label {
                        text: fila.model.mensaje
                        font.weight: fila.model.ok ? Font.Normal : Font.DemiBold
                        color: fila.model.ok ? Kirigami.Theme.textColor : raiz.colorDe(false, fila.model.nivel)
                        elide: Text.ElideRight
                        Layout.maximumWidth: lista.width * 0.4
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        text: fila.model.detalle + (fila.cita && fila.model.fuente ? " · " + fila.model.fuente : "")
                        color: Kirigami.Theme.disabledTextColor
                        elide: Text.ElideRight
                    }
                }
            }
            QQC2.Label {
                anchors.centerIn: parent
                width: parent.width - Kirigami.Units.gridUnit * 4
                visible: lista.count === 0
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                color: Kirigami.Theme.disabledTextColor
                text: "Sin verificar en este studio: Verificar (Ctrl+T) corre sus identidades y teoremas; solo un modelo verificado da resultados válidos."
            }
        }
    }
}
