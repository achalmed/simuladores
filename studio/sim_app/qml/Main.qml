// Main.qml — Simuladores Studio (reingeniería del 2026-11-02, docs/reingenieria.md; forma propia aprobada el 2026-11-18,
// docs/decisiones.md): el laboratorio, sobre GuiComun.VentanaBase. Arriba, el modelo con su estado de validez, las
// acciones del experimento y las vistas. A la izquierda, el catálogo de modelos por disciplina (F9). En el centro, el
// espacio de simulación: Simulación (o Evolución temporal) con las curvas que se mueven al arrastrar los parámetros y
// el equilibrio marcado, Comparación, Sensibilidad, Ficha, Verificaciones y Laboratorio. A la derecha, los parámetros.
// Al pie, las verificaciones contra la teoría con su fuente (Ctrl+Mayús+T). Abajo, la barra de estado, que recibe
// también las pistas efímeras; los avisos van a las notificaciones de KDE por Mensajes de la base. Sin colores propios:
// Kirigami.Theme. Ninguna llamada al motor ni al disco aquí: todo lo hacen los controladores de Python (studio.*).
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
    property bool mostrarVerificaciones: true
    property string pistaActual: ""            // lo efímero («elige primero un modelo»): a la barra de estado, unos segundos
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
    function pista(texto) { pistaActual = texto; relojPista.restart() }
    // un aviso de los controladores: la pista a la barra de estado; lo demás, a Mensajes (sin acciones: Plasma)
    function avisar(texto, tipo) {
        if (tipo === "pista") pista(texto)
        else ventana.mensajes.mostrar(texto, tipo || "informacion")
    }
    Timer { id: relojPista; interval: 6000; onTriggered: ventana.pistaActual = "" }

    Settings {
        category: "espacio"
        property alias vista: ventana.vista
        property alias catalogo: ventana.mostrarCatalogo
        property alias verificaciones: ventana.mostrarVerificaciones
    }

    Connections {
        target: studio.interfaz
        function onPedir(nombre, datos) {
            switch (nombre) {
            case "buscar": ventana.mostrarCatalogo = true; catalogo.enfocar(); break
            case "catalogo": ventana.mostrarCatalogo = !ventana.mostrarCatalogo; break
            case "verificaciones": ventana.mostrarVerificaciones = !ventana.mostrarVerificaciones; break
            case "aplicar": dialogoAplicar.abrir(); break
            case "venv": dialogoVenv.open(); break
            case "vista": irAVista(datos.indice); break
            case "salida": irAVista(5); laboratorio.pestana = 2; break
            case "paleta": ventana.paleta.abrir(datos.texto || ""); break
            case "aviso": avisar(datos.texto, datos.tipo); break
            }
        }
    }
    Connections { target: espacio; function onAviso(texto, tipo) { avisar(texto, tipo) } }
    Connections {
        target: modelos
        function onAviso(texto, tipo) { avisar(texto, tipo) }
        function onActualCambiado() { modelos.fijarColorTexto(Kirigami.Theme.textColor.toString()) }
    }
    Connections {
        target: ops
        function onAviso(texto, tipo) { avisar(texto, tipo) }
        function onTerminada(id, aplicar, codigo) {
            if (id === "correr") irAVista(0)
            else if (id === "verificar") irAVista(4)
            else if (!(aplicar && (id === "datos" || id === "guardar_escenario"))) { irAVista(5); laboratorio.pestana = 0 }
        }
    }
    Component.onCompleted: modelos.fijarColorTexto(Kirigami.Theme.textColor.toString())
    // el cambio de claro a oscuro con la ventana abierta: las fórmulas de la ficha se vuelven a dibujar con el texto nuevo
    Connections { target: Kirigami.Theme; function onTextColorChanged() { modelos.fijarColorTexto(Kirigami.Theme.textColor.toString()) } }

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
                // el estado de validez (L8): EtiquetaNivel de la base (sin radios ni colores propios)
                EtiquetaNivel {
                    id: chip
                    visible: modelos.hayActual && modelos.cargado
                    nivel: validez.valido === true ? "positivo" : (validez.nivel || "neutro")
                    icono: nivel === "positivo" ? "data-success" : (nivel === "negativo" ? "data-error" : "data-warning")
                    text: validez.valido === true ? "VÁLIDO · " + modelos.textoEstado.toLowerCase() : (validez.titulo || modelos.textoEstado || "sin corrida")
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

    // ------------------------------------------------------------------ el laboratorio: catálogo · curvas · parámetros / verificaciones
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
        QQC2.SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Vertical
            RowLayout {
                QQC2.SplitView.fillHeight: true
                QQC2.SplitView.minimumHeight: Kirigami.Units.gridUnit * 16
                spacing: 0
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
                        explanation: modelos.resumen + "\n\nSus curvas se mueven al arrastrar los parámetros; un resultado solo se da por válido si sus verificaciones contra la teoría pasan."
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
            // al pie, las verificaciones contra la teoría con su fuente (en las vistas del experimento)
            BandaVerificaciones {
                id: pie
                objectName: "bandaVerificaciones"
                visible: ventana.mostrarVerificaciones && modelos.cargado && ventana.vista <= 2
                QQC2.SplitView.preferredHeight: Kirigami.Units.gridUnit * 7
                QQC2.SplitView.minimumHeight: Kirigami.Units.gridUnit * 4
                onVerDetalle: irAVista(4)
            }
        }
    }

    footer: BarraEstado {
        resumen: espacio.resumen
        contexto: ventana.pistaActual || espacio.contexto
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
            if (!ops.puedeAplicar) { ventana.pista(ops.motivoNoAplicar); irAVista(5); laboratorio.pestana = 0; return }
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
