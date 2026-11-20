// Operacion — la operación elegida: qué hace, sobre qué, qué toca, la orden de F5 y la de Ctrl+Intro, lo que pide
// (el parámetro, el nombre del escenario); el plan (la última simulación) y el registro (la última aplicación).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

QQC2.ScrollView {
    id: pagina
    readonly property var o: studio.operaciones
    contentWidth: availableWidth
    QQC2.ScrollBar.horizontal.policy: QQC2.ScrollBar.AlwaysOff
    ColumnLayout {
        width: pagina.availableWidth - Kirigami.Units.largeSpacing * 2
        x: Kirigami.Units.largeSpacing
        y: Kirigami.Units.largeSpacing
        spacing: Kirigami.Units.largeSpacing
        // con las etiquetas a la izquierda y los textos largos con un ancho de lectura: antes caía al modo estrecho,
        // flotaba a la derecha y el texto se cortaba en el borde
        Kirigami.FormLayout {
            Layout.fillWidth: true
            wideMode: true
            Kirigami.Heading { Kirigami.FormData.label: "Operación:"; level: 4; text: pagina.o.titulo; wrapMode: Text.WordWrap; Layout.fillWidth: true; Layout.maximumWidth: Kirigami.Units.gridUnit * 34 }
            QQC2.Label { Kirigami.FormData.label: "Grupo:"; text: pagina.o.grupo }
            QQC2.Label { Kirigami.FormData.label: "Sobre:"; visible: pagina.o.sobreModelo; text: studio.modelos.hayActual ? studio.modelos.ref + " · escenario " + studio.modelos.escenario : "ningún modelo elegido"; color: studio.modelos.hayActual ? Kirigami.Theme.textColor : Kirigami.Theme.neutralTextColor; wrapMode: Text.WordWrap; Layout.fillWidth: true; Layout.maximumWidth: Kirigami.Units.gridUnit * 34 }
            QQC2.Label { Kirigami.FormData.label: "Sobre:"; visible: pagina.o.sobreDisciplina; text: pagina.o.disciplina || "ninguna disciplina elegida"; color: pagina.o.disciplina ? Kirigami.Theme.textColor : Kirigami.Theme.neutralTextColor }
            QQC2.Label { Kirigami.FormData.label: "Qué hace:"; text: pagina.o.descripcion; wrapMode: Text.WordWrap; Layout.fillWidth: true; Layout.maximumWidth: Kirigami.Units.gridUnit * 34 }
            QQC2.Label { Kirigami.FormData.label: "Toca:"; text: pagina.o.queToca; wrapMode: Text.WordWrap; Layout.fillWidth: true; Layout.maximumWidth: Kirigami.Units.gridUnit * 34; color: pagina.o.escribe ? Kirigami.Theme.neutralTextColor : Kirigami.Theme.positiveTextColor }
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "Lo que pide"; visible: pagina.o.entradaTipo !== "" }
            QQC2.ComboBox {
                id: campoParametro
                Kirigami.FormData.label: pagina.o.entradaEtiqueta + ":"
                visible: pagina.o.entradaTipo === "parametro"
                Layout.fillWidth: true
                model: pagina.o.nombresParametros
                currentIndex: Math.max(0, pagina.o.nombresParametros.indexOf(pagina.o.valor))
                onActivated: index => pagina.o.fijarValor(pagina.o.nombresParametros[index])
                Accessible.name: pagina.o.entradaEtiqueta
            }
            QQC2.TextField {
                id: campoTexto
                Kirigami.FormData.label: pagina.o.entradaEtiqueta + ":"
                visible: pagina.o.entradaTipo === "nombre"
                Layout.fillWidth: true
                text: pagina.o.valor
                placeholderText: "vacío: propio-<fecha>"
                onEditingFinished: pagina.o.fijarValor(text)
                Accessible.name: pagina.o.entradaEtiqueta
                Connections { target: pagina.o; function onCambiado() { if (!campoTexto.activeFocus) campoTexto.text = pagina.o.valor } }
            }
            Kirigami.Separator { Kirigami.FormData.isSection: true; Kirigami.FormData.label: "La orden" }
            QQC2.Label { Kirigami.FormData.label: pagina.o.verbo + " (F5):"; text: pagina.o.ordenSimular; font: Kirigami.Theme.fixedWidthFont; wrapMode: Text.WrapAnywhere; Layout.fillWidth: true; Layout.maximumWidth: Kirigami.Units.gridUnit * 34 }
            QQC2.Label { Kirigami.FormData.label: "Aplicar (Ctrl+Intro):"; visible: pagina.o.escribe; text: pagina.o.ordenAplicar; font: Kirigami.Theme.fixedWidthFont; wrapMode: Text.WrapAnywhere; Layout.fillWidth: true; Layout.maximumWidth: Kirigami.Units.gridUnit * 34 }
            QQC2.Label { Kirigami.FormData.label: "Ahora:"; visible: !pagina.o.puedeSimular; text: pagina.o.motivoNoSimular; wrapMode: Text.WordWrap; Layout.fillWidth: true; Layout.maximumWidth: Kirigami.Units.gridUnit * 34; color: Kirigami.Theme.neutralTextColor }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            Item { Layout.fillWidth: true }
            BotonAccion { accion: studio.acciones.accion("op.cancelar"); conTexto: false; visible: pagina.o.enCurso }
            BotonAccion { accion: studio.acciones.accion("op.simular") }
            BotonPrincipal {
                accion: studio.acciones.accion("op.aplicar")
                visible: pagina.o.escribe
                QQC2.ToolTip.text: accion.descripcion + " (" + accion.atajoTexto + ")"; QQC2.ToolTip.visible: hovered
            }
        }
        Kirigami.Separator { Layout.fillWidth: true; visible: pagina.o.plan !== "" || pagina.o.registro !== "" }
        Kirigami.Heading { visible: pagina.o.plan !== ""; level: 5; type: Kirigami.Heading.Type.Primary; text: pagina.o.escribe ? "Plan (la última simulación)" : "La última corrida" }
        QQC2.Label { visible: pagina.o.plan !== ""; Layout.fillWidth: true; text: pagina.o.plan; font: Kirigami.Theme.fixedWidthFont; wrapMode: Text.WrapAnywhere; textFormat: Text.PlainText }
        Kirigami.Heading { visible: pagina.o.registro !== ""; level: 5; type: Kirigami.Heading.Type.Primary; text: "Registro (la última aplicación)" }
        QQC2.Label { visible: pagina.o.registro !== ""; Layout.fillWidth: true; text: pagina.o.registro; font: Kirigami.Theme.fixedWidthFont; wrapMode: Text.WrapAnywhere; textFormat: Text.PlainText }
        Item { Layout.preferredHeight: Kirigami.Units.largeSpacing }
    }
}
