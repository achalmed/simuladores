// Main.qml — Simuladores Studio: los modelos del laboratorio en un espacio de trabajo al estilo Dolphin/Kate sobre
// GuiComun.VentanaStudio. Navegación (Disciplinas · Verificación) · centro (la tabla de modelos) · detalles (el modelo:
// Ficha, Escenario, Resultados con el gráfico, Verificaciones, Registro, Operación) · panel inferior (la salida del
// motor) · barra de estado. Ninguna llamada al motor ni al disco aquí: todo lo hacen los controladores de Python (studio.*).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun
import "componentes"

VentanaStudio {
    id: ventana

    readonly property var espacio: studio.espacio
    readonly property var registro: studio.acciones
    readonly property var modelos: studio.modelos
    readonly property var ops: studio.operaciones

    title: (modelos.hayActual ? modelos.id + " · " + modelos.titulo : espacio.textoDisciplina) + " — Simuladores Studio"
    acciones: registro
    tareas: studio.tareas
    consola: studio.consola
    descripcion: descripcionStudio
    autor: "Edison Achalma (@achalmed)"
    resumen: espacio.resumen
    contexto: espacio.contexto
    claveAjustes: "ventana"

    function accion(nombre) { return registro.accion(nombre) }
    function irAPestana(i) { ventana.mostrarDetalles = true; detalles.pestanaActual = i }
    function religarNavegacion() { navegacion.actual = Qt.binding(() => espacio.nombreNavegacion) }

    Connections {
        target: studio.interfaz
        function onPedir(nombre, datos) {
            switch (nombre) {
            case "filtrar": filtro.forceActiveFocus(); filtro.selectAll(); break
            case "seleccionar_todo": tabla.seleccionarTodo(); break
            case "seleccionar_fila": if (datos.fila >= 0) tabla.seleccionarFila(datos.fila, true); break
            case "aplicar": dialogoAplicar.abrir(); break
            case "venv": dialogoVenv.open(); break
            case "pestana": irAPestana(datos.indice); break
            case "paleta": ventana.paleta.abrir(datos.texto || ""); break
            case "aviso": ventana.mensajes.mostrar(datos.texto, datos.tipo || "informacion"); break
            }
        }
    }
    Connections { target: espacio; function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) } function onFiltroCambiado() { religarNavegacion() } }
    Connections {
        target: modelos
        function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) }
        function onSeleccionar(fila) { if (fila >= 0) tabla.seleccionarFila(fila, true); irAPestana(0) }
        function onActualCambiado() { modelos.fijarColorTexto(Kirigami.Theme.textColor.toString()) }
    }
    Connections {
        target: ops
        function onAviso(texto, tipo) { ventana.mensajes.mostrar(texto, tipo) }
        function onTerminada(id, aplicar, codigo) {
            if (id === "correr") irAPestana(2)
            else if (id === "verificar") irAPestana(3)
            else if (!aplicar && (id === "datos" || id === "guardar_escenario")) irAPestana(5)
        }
    }
    Component.onCompleted: modelos.fijarColorTexto(Kirigami.Theme.textColor.toString())

    // ------------------------------------------------------------------ barra: la operación y el filtro
    herramientasExtra: [
        QQC2.ComboBox {
            id: selectorOperacion
            Layout.preferredWidth: Kirigami.Units.gridUnit * 15
            model: ops.lista
            textRole: "titulo"
            currentIndex: ops.indiceActual
            onActivated: index => ops.fijarPorIndice(index)
            Accessible.name: "Operación"
            QQC2.ToolTip.text: ops.descripcion
            QQC2.ToolTip.visible: hovered && ops.descripcion !== ""
            Connections { target: ops; function onCambiado() { selectorOperacion.currentIndex = ops.indiceActual } }
        },
        Kirigami.SearchField {
            id: filtro
            Layout.preferredWidth: Kirigami.Units.gridUnit * 11
            placeholderText: "Filtrar (Ctrl+F)"
            onTextChanged: modelos.modelo.filtrar(text)
            Keys.onEscapePressed: { text = ""; tabla.forceActiveFocus() }
            Accessible.name: "Filtrar"
        }
    ]

    // ------------------------------------------------------------------ navegación
    navegacion: PanelNavegacion {
        id: navegacion
        secciones: [
            { titulo: "Disciplinas", filas: modelos.filasDisciplinas },
            { titulo: "Verificación", filas: modelos.filasEstados }
        ]
        onElegida: nombre => {
            if (nombre.startsWith("estado.")) espacio.fijarEstado(nombre.substring(7))
            else { espacio.fijarEstado(""); espacio.fijarDisciplina(nombre.length > 10 ? nombre.substring(11) : "") }
            religarNavegacion()
        }
        Component.onCompleted: religarNavegacion()
    }

    // ------------------------------------------------------------------ centro
    centro: TablaDatos {
        id: tabla
        modelo: modelos.modelo
        claveAjustes: "modelos"
        umbralEstrecho: Kirigami.Units.gridUnit * 48
        mensajeVacio: modelos.total === 0 ? "Ningún modelo: falta catalogo.json en la raíz del laboratorio (python3 main.py catalogo --aplicar)"
                                          : "Ningún modelo cumple el filtro «" + espacio.textoFiltro + "»"
        iconoVacio: "office-chart-line"
        columnas: [
            { ancho: 4, mono: true },
            { ancho: 0, minimo: 14, conIcono: true },
            { ancho: 12, secundaria: true, estrecho: true },
            { ancho: 5, alinear: "derecha", secundaria: true, estrecho: true },
            { ancho: 5, alinear: "derecha", secundaria: true, estrecho: true },
            { ancho: 6, alinear: "derecha", secundaria: true, estrecho: true },
            { ancho: 8, semantica: true },
            { ancho: 9, secundaria: true, estrecho: true }
        ]
        onOrdenar: (columna, descendente) => modelos.modelo.ordenar(columna, descendente)
        onFilaActualCambiada: fila => modelos.fijarFila(fila)
        onActivada: fila => { modelos.fijarFila(fila); ventana.accion("archivo.abrir").disparar() }
        menuContextual: MenuAcciones {
            acciones: ventana.registro
            conAtajos: false
            elementos: [
                { tipo: "accion", nombre: "modelo.correr" }, { tipo: "accion", nombre: "modelo.verificar" }, { tipo: "accion", nombre: "modelo.restablecer" },
                { tipo: "separador" },
                { tipo: "accion", nombre: "op.simular" }, { tipo: "accion", nombre: "op.aplicar" },
                { tipo: "separador" },
                { tipo: "accion", nombre: "modelo.ficha" }, { tipo: "accion", nombre: "modelo.escenario" }, { tipo: "accion", nombre: "modelo.resultados" }, { tipo: "accion", nombre: "modelo.verificaciones" },
                { tipo: "separador" },
                { tipo: "accion", nombre: "archivo.abrir" }, { tipo: "accion", nombre: "archivo.carpeta" }, { tipo: "accion", nombre: "archivo.copiar" }
            ]
        }
    }

    // ------------------------------------------------------------------ detalles
    detalles: PanelDetalles {
        id: detalles
        anchoPreferido: Kirigami.Units.gridUnit * 30
        anchoMinimo: Kirigami.Units.gridUnit * 20
        titulo: modelos.hayActual ? modelos.id + " · " + modelos.titulo : ""
        subtitulo: modelos.hayActual ? modelos.textoDisciplina + (modelos.seccion ? " · " + modelos.seccion : "") + " · " + modelos.textoEstado : ""
        icono: modelos.hayActual ? "office-chart-line" : ""
        mensajeVacio: "Elige un modelo en la tabla: su ficha, su escenario, su corrida con el gráfico y sus verificaciones"
        iconoVacio: "office-chart-line"
        accionesCabecera: [ventana.accion("modelo.correr"), ventana.accion("modelo.verificar"), ventana.accion("archivo.abrir")]
        pestanas: [
            { titulo: "Ficha" },
            { titulo: "Escenario", contador: modelos.parametros.length },
            { titulo: "Resultados", contador: modelos.nResultados },
            { titulo: "Verificaciones", contador: modelos.nVerificaciones },
            { titulo: "Registro" },
            { titulo: "Operación" }
        ]
        Ficha {}
        Escenario {}
        Resultados {}
        Verificaciones {}
        Registro {}
        Operacion {}
    }

    inferior: PanelInferior { consola: studio.consola }

    // ------------------------------------------------------------------ diálogos
    Kirigami.PromptDialog {
        id: dialogoAplicar
        title: "Aplicar: " + ops.titulo + (modelos.hayActual && ops.sobreModelo ? " · " + modelos.id : "")
        subtitle: ops.textoConfirmacion
        standardButtons: Kirigami.Dialog.Cancel
        customFooterActions: [Kirigami.Action { text: "Aplicar"; icon.name: "dialog-ok-apply"; enabled: ops.puedeAplicar; onTriggered: { ops.aplicar(); dialogoAplicar.close() } }]
        function abrir() {
            if (!ops.puedeAplicar) { ventana.mensajes.mostrar(ops.motivoNoAplicar, "aviso"); irAPestana(5); return }
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
