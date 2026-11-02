// Main.qml — Simuladores Studio (reingeniería del 2026-11-02, docs/reingenieria.md): un laboratorio de simulación sobre
// GuiComun.VentanaBase, al modo de MATLAB, RStudio y JupyterLab. Arriba, el modelo con su estado de validez, las
// acciones del experimento y las vistas. A la izquierda, el catálogo de modelos por disciplina (F9). En el centro, el
// espacio de simulación: Simulación (o Evolución temporal), Comparación, Sensibilidad, Ficha, Verificaciones y
// Laboratorio. A la derecha, los parámetros con sus deslizadores. Abajo, la barra de estado. Ninguna llamada al motor
// ni al disco aquí: todo lo hacen los controladores de Python (studio.*).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import QtCore
import GuiComun
import "componentes"

VentanaBase {
    id: ventana

    readonly property var espacio: studio.espacio
    readonly property var registro: studio.acciones
    readonly property var modelos: studio.modelos
    readonly property var ops: studio.operaciones
    readonly property var validez: modelos.validez
    property int vista: 0
    property bool mostrarCatalogo: true
    readonly property var vistas: [modelos.temporal ? "Evolución temporal" : "Simulación", "Comparación", "Sensibilidad", "Ficha", "Verificaciones", "Laboratorio"]

    title: (modelos.hayActual ? modelos.id + " · " + modelos.titulo : "Laboratorio") + " — Simuladores Studio"
    acciones: registro
    tareas: studio.tareas
    consola: studio.consola
    descripcion: descripcionStudio
    autor: "Edison Achalma (@achalmed)"
    claveAjustes: "ventana-3"
    width: 1400
    height: 880

    function accion(nombre) { return registro.accion(nombre) }
    function irAVista(i) { ventana.vista = Math.max(0, Math.min(ventana.vistas.length - 1, i)) }

    Settings {
        category: "espacio"
        property alias vista: ventana.vista
        property alias catalogo: ventana.mostrarCatalogo
    }

    Connections {
        target: studio.interfaz
        function onPedir(nombre, datos) {
            switch (nombre) {
            case "buscar": ventana.mostrarCatalogo = true; catalogo.enfocar(); break
            case "catalogo": ventana.mostrarCatalogo = !ventana.mostrarCatalogo; break
            case "aplicar": dialogoAplicar.abrir(); break
            case "venv": dialogoVenv.open(); break
            case "vista": irAVista(datos.indice); break
            case "salida": irAVista(5); laboratorio.pestana = 2; break
            case "paleta": ventana.paleta.abrir(datos.texto || ""); break
            case "aviso": ventana.mensajes.mostrar(datos.texto, datos.tipo || "informacion"); break
            }
        }
    }
    Connections { target: espacio; function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) } }
    Connections {
        target: modelos
        function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) }
        function onActualCambiado() { modelos.fijarColorTexto(Kirigami.Theme.textColor.toString()) }
    }
    Connections {
        target: ops
        function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) }
        function onTerminada(id, aplicar, codigo) {
            if (id === "correr") irAVista(0)
            else if (id === "verificar") irAVista(4)
            else if (!(aplicar && (id === "datos" || id === "guardar_escenario"))) { irAVista(5); laboratorio.pestana = 0 }
        }
    }
    Component.onCompleted: modelos.fijarColorTexto(Kirigami.Theme.textColor.toString())

    // ------------------------------------------------------------------ la cabecera: el modelo, su validez y las vistas
    header: QQC2.ToolBar {
        position: QQC2.ToolBar.Header
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.smallSpacing
            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing
                BotonAccion { accion: ventana.accion("ver.catalogo"); conTexto: false }
                Kirigami.Icon {
                    source: modelos.hayActual ? "office-chart-line" : "applications-science"
                    implicitWidth: Kirigami.Units.iconSizes.medium
                    implicitHeight: implicitWidth
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Kirigami.Heading {
                        Layout.fillWidth: true
                        level: 3
                        text: modelos.hayActual ? modelos.id + " · " + modelos.titulo : "Laboratorio de simulación"
                        elide: Text.ElideRight
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        text: modelos.hayActual ? modelos.textoDisciplina + (modelos.seccion ? " · " + modelos.seccion : "") + (modelos.pregunta ? " · " + modelos.pregunta : "")
                                                : "Elige un modelo del catálogo: su simulación, su ficha y sus verificaciones"
                        color: Kirigami.Theme.disabledTextColor
                        elide: Text.ElideRight
                    }
                }
                // el estado de validez (L8)
                QQC2.Control {
                    id: chip
                    visible: modelos.hayActual && modelos.cargado
                    readonly property string nivel: validez.valido === true ? "positivo" : (validez.nivel || "neutro")
                    padding: Kirigami.Units.smallSpacing
                    leftPadding: Kirigami.Units.largeSpacing
                    rightPadding: Kirigami.Units.largeSpacing
                    background: Rectangle {
                        radius: height / 2
                        color: chip.nivel === "positivo" ? Kirigami.Theme.positiveBackgroundColor
                               : (chip.nivel === "negativo" ? Kirigami.Theme.negativeBackgroundColor : Kirigami.Theme.neutralBackgroundColor)
                    }
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.smallSpacing
                        Kirigami.Icon {
                            source: chip.nivel === "positivo" ? "data-success" : (chip.nivel === "negativo" ? "data-error" : "data-warning")
                            implicitWidth: Kirigami.Units.iconSizes.small
                            implicitHeight: implicitWidth
                        }
                        QQC2.Label {
                            text: validez.valido === true ? "VÁLIDO · " + modelos.textoEstado.toLowerCase() : (validez.titulo || modelos.textoEstado || "sin corrida")
                            font.weight: Font.DemiBold
                        }
                    }
                    QQC2.ToolTip.text: (validez.texto || "") + (modelos.hayActual ? "\n" + modelos.resumenVerificacion : "")
                    QQC2.ToolTip.visible: zonaChip.hovered
                    HoverHandler { id: zonaChip }
                    Accessible.name: "Validez: " + (validez.titulo || (validez.valido ? "válido" : "")) + ". " + (validez.texto || "")
                }
                Kirigami.Separator { Layout.fillHeight: true; Layout.margins: Kirigami.Units.smallSpacing }
                BotonAccion { accion: ventana.accion("modelo.correr") }
                BotonAccion { accion: ventana.accion("modelo.verificar") }
                BotonAccion { accion: ventana.accion("ver.figura"); conTexto: false }
                BotonAccion { accion: ventana.accion("archivo.abrir"); conTexto: false }
                BotonAccion { accion: ventana.accion("ventana.paleta"); conTexto: false }
            }
            QQC2.TabBar {
                id: pestanas
                Layout.fillWidth: true
                currentIndex: ventana.vista
                onCurrentIndexChanged: ventana.vista = currentIndex
                Repeater {                  // las seis vistas son fijas: el modelo del Repeater es una lista constante de índices
                    model: 6
                    delegate: QQC2.TabButton {
                        required property int index
                        text: ventana.vistas[index] + (index === 4 && modelos.nFallos > 0 ? " (" + modelos.nFallos + " ✘)" : "")
                        icon.name: ["office-chart-line", "view-split-left-right", "office-chart-line-stacked", "text-x-generic", "checkmark", "utilities-terminal"][index]
                        width: implicitWidth
                        QQC2.ToolTip.text: "Ctrl+" + (index + 1)
                        QQC2.ToolTip.visible: hovered
                    }
                }
            }
        }
    }

    // ------------------------------------------------------------------ catálogo · espacio de simulación · parámetros
    RowLayout {
        anchors.fill: parent
        spacing: 0
        CatalogoModelos {
            id: catalogo
            visible: ventana.mostrarCatalogo
            Layout.preferredWidth: Kirigami.Units.gridUnit * 17
            Layout.fillHeight: true
        }
        Kirigami.Separator { Layout.fillHeight: true; visible: catalogo.visible }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            StackLayout {
                anchors.fill: parent
                visible: modelos.hayActual || ventana.vista === 5
                currentIndex: ventana.vista
                EspacioSimulacion {}
                Comparacion {}
                Sensibilidad {}
                Ficha {}
                Verificaciones {}
                Laboratorio { id: laboratorio }
            }
            Kirigami.PlaceholderMessage {
                anchors.centerIn: parent
                width: parent.width - Kirigami.Units.gridUnit * 6
                visible: !modelos.hayActual && ventana.vista !== 5
                icon.name: "office-chart-line"
                text: "Elige un modelo del catálogo"
                explanation: modelos.resumen + "\n\nSu simulación se redibuja al mover los parámetros; un resultado solo se da por válido si sus verificaciones pasan."
            }
        }
        Kirigami.Separator { Layout.fillHeight: true; visible: parametros.visible }
        PanelParametros {
            id: parametros
            visible: modelos.cargado && ventana.vista <= 2
            Layout.preferredWidth: Kirigami.Units.gridUnit * 18
            Layout.fillHeight: true
        }
    }

    footer: BarraEstado {
        resumen: espacio.resumen
        contexto: espacio.contexto
        tareas: studio.tareas
        onProgresoPulsado: { irAVista(5); laboratorio.pestana = 2 }
    }

    // ------------------------------------------------------------------ diálogos
    Kirigami.PromptDialog {
        id: dialogoAplicar
        title: "Aplicar: " + ops.titulo + (modelos.hayActual && ops.sobreModelo ? " · " + modelos.id : "")
        subtitle: ops.textoConfirmacion
        standardButtons: Kirigami.Dialog.Cancel
        customFooterActions: [Kirigami.Action { text: "Aplicar"; icon.name: "dialog-ok-apply"; enabled: ops.puedeAplicar; onTriggered: { ops.aplicar(); dialogoAplicar.close() } }]
        function abrir() {
            if (!ops.puedeAplicar) { ventana.mensajes.mostrar(ops.motivoNoAplicar, "aviso"); irAVista(5); laboratorio.pestana = 0; return }
            open()
        }
    }
    Kirigami.PromptDialog {
        id: dialogoVenv
        title: "El entorno del studio"
        subtitle: (studio.ajustes.hayVenv ? "Las CLI del laboratorio, la figura académica y las fórmulas corren con " + studio.ajustes.interprete + " (el .venv del repo: matplotlib)."
                                           : "No existe el .venv del repo: sin matplotlib no hay figura académica, fórmulas dibujadas, reportes ni CLI del laboratorio (correr y verificar un modelo sí funcionan).")
                  + "\n\nPara crearlo (sin sudo ni apt):\n" + studio.ajustes.ordenVenv
        standardButtons: Kirigami.Dialog.Close
        customFooterActions: [Kirigami.Action { text: "Copiar la orden"; icon.name: "edit-copy"; onTriggered: { espacio.copiar(studio.ajustes.ordenVenv); dialogoVenv.close() } }]
    }
    dialogoAjustes: DialogoAjustesStudio {}
}
