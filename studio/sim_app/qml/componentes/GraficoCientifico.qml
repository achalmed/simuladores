// GraficoCientifico — el gráfico del espacio de simulación (reingeniería L2), dibujado con Canvas: cada línea con su
// propio x (sin remuestrear), barras con el color de cada barra, puntos, el equilibrio con sus guías a los ejes, líneas
// verticales y horizontales con su nombre, ejes con marcas «redondas», leyenda y el valor bajo el cursor. La `base`
// (otro gráfico del mismo modelo) se dibuja punteada y atenuada debajo. Los colores son roles (azul, rojo, verde,
// dorado, morado, cian, gris, texto) pintados con Kirigami.Theme (ver `color`): ningún color propio. Si `invalido` trae un título
// («NO VÁLIDO», «SIN VERIFICAR»), el gráfico lo lleva marcado y no se presenta como un resultado bueno (L8).
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: raiz

    property var datos: ({})                 // sim.grafico(...)
    property var base: null                  // otro sim.grafico(...) para dibujar debajo, punteado
    property var limites: null               // {xMin, xMax, yMin, yMax}; si no, los de datos (y base)
    property string nombreDatos: "escenario"
    property string nombreBase: "base"
    property string invalido: ""             // «NO VÁLIDO» · «SIN VERIFICAR» · ""
    property string nivelInvalido: "negativo"
    property string motivoInvalido: ""
    property string mensajeVacio: "Sin corrida"
    property string nombreAccesible: "Gráfico"
    property real marcaX: NaN                // una línea vertical extra (el valor actual en la sensibilidad)
    readonly property bool hayDatos: !!datos && !!((datos.lineas && datos.lineas.length) || (datos.barras && datos.barras.valores && datos.barras.valores.length)
                                               || (datos.puntos && datos.puntos.length) || (datos.verticales && datos.verticales.length) || (datos.horizontales && datos.horizontales.length))
    spacing: Kirigami.Units.smallSpacing
    Accessible.name: nombreAccesible

    // Los roles semánticos (rojo, verde, dorado) son los del tema. Azul, morado y cian: los del tema si de verdad tienen
    // ese tono (Breeze: el enlace es azul); si no (un tema con acento rojo pone el enlace rojo), la saturación y la
    // luminosidad de los colores semánticos del tema con solo el tono fijado, para no confundir la demanda con la oferta.
    readonly property bool temaOscuro: Kirigami.Theme.backgroundColor.hslLightness < 0.5
    function tono(h) {
        const b = Kirigami.Theme.positiveTextColor
        const l = temaOscuro ? Math.max(b.hslLightness, 0.6) : Math.min(b.hslLightness, 0.42)
        return Qt.hsla(h, Math.max(b.hslSaturation, 0.55), l, 1)
    }
    function delTema(c, desde, hasta, h) {
        return c.hslSaturation > 0.3 && c.hslHue >= desde && c.hslHue <= hasta ? c : tono(h)
    }
    function color(rol) {
        switch (rol) {
        case "azul": return delTema(Kirigami.Theme.linkColor, 0.53, 0.70, 0.6)
        case "rojo": return Kirigami.Theme.negativeTextColor
        case "verde": return Kirigami.Theme.positiveTextColor
        case "dorado": return Kirigami.Theme.neutralTextColor
        case "morado": return delTema(Kirigami.Theme.visitedLinkColor, 0.72, 0.9, 0.78)
        case "cian": return delTema(Kirigami.Theme.activeTextColor, 0.45, 0.55, 0.5)
        case "gris": return Kirigami.Theme.disabledTextColor
        default: return Kirigami.Theme.textColor
        }
    }
    function lim() {
        if (limites && limites.xMax !== undefined) return limites
        const l = (datos && datos.limites) ? datos.limites : { xMin: 0, xMax: 1, yMin: 0, yMax: 1 }
        if (base && base.limites) return { xMin: Math.min(l.xMin, base.limites.xMin), xMax: Math.max(l.xMax, base.limites.xMax),
                                           yMin: Math.min(l.yMin, base.limites.yMin), yMax: Math.max(l.yMax, base.limites.yMax) }
        return l
    }
    function marcas(a, b, n) {
        const rango = b - a
        if (!(rango > 0)) return [a]
        const crudo = rango / n
        const pot = Math.pow(10, Math.floor(Math.log10(crudo)))
        const paso = [1, 2, 2.5, 5, 10].map(f => f * pot).find(p => rango / p <= n) || crudo
        const salida = []
        for (let v = Math.ceil(a / paso) * paso; v <= b + paso * 1e-9; v += paso) salida.push(Math.abs(v) < paso * 1e-9 ? 0 : v)
        return salida
    }
    function numero(v) {
        const a = Math.abs(v)
        if (a >= 10000) return v.toLocaleString(Qt.locale(), "f", 0)
        if (a >= 100) return v.toLocaleString(Qt.locale(), "f", 0)
        if (a >= 10) return v.toLocaleString(Qt.locale(), "f", 1)
        if (a >= 1) return v.toLocaleString(Qt.locale(), "f", 2)
        return v.toLocaleString(Qt.locale(), "g", 3)
    }
    onDatosChanged: lienzo.requestPaint()
    onBaseChanged: lienzo.requestPaint()
    onLimitesChanged: lienzo.requestPaint()
    onMarcaXChanged: lienzo.requestPaint()
    Connections { target: Kirigami.Theme; function onTextColorChanged() { lienzo.requestPaint() } }

    Item {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: Kirigami.Units.gridUnit * 10

        Canvas {
            id: lienzo
            anchors.fill: parent
            visible: raiz.hayDatos
            renderStrategy: Canvas.Cooperative
            readonly property real mIzq: Kirigami.Units.gridUnit * 3.6
            readonly property real mDer: Kirigami.Units.gridUnit
            readonly property real mSup: Kirigami.Units.gridUnit
            readonly property real mInf: Kirigami.Units.gridUnit * 2.6
            readonly property real anchoUtil: width - mIzq - mDer
            readonly property real altoUtil: height - mSup - mInf
            property var hover: null
            function px(x, l) { return mIzq + (x - l.xMin) / (l.xMax - l.xMin) * anchoUtil }
            function py(y, l) { return mSup + (1 - (y - l.yMin) / (l.yMax - l.yMin)) * altoUtil }
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()

            onPaint: {
                const ctx = getContext("2d")
                ctx.reset()
                if (!raiz.hayDatos || anchoUtil <= 10 || altoUtil <= 10) return
                const l = raiz.lim()
                const fuente = Kirigami.Theme.smallFont.pointSize * 1.33
                ctx.font = fuente + "px \"" + Kirigami.Theme.defaultFont.family + "\""
                const texto = Kirigami.Theme.textColor
                const tenue = Kirigami.Theme.disabledTextColor
                const barras = raiz.datos.barras && raiz.datos.barras.valores && raiz.datos.barras.valores.length
                // la rejilla y los ejes
                ctx.lineWidth = 1
                ctx.strokeStyle = tenue
                ctx.fillStyle = tenue
                ctx.globalAlpha = 0.25
                const ys = raiz.marcas(l.yMin, l.yMax, 6)
                for (const v of ys) { const y = py(v, l); ctx.beginPath(); ctx.moveTo(mIzq, y); ctx.lineTo(width - mDer, y); ctx.stroke() }
                const xs = barras ? [] : raiz.marcas(l.xMin, l.xMax, Math.max(3, Math.floor(anchoUtil / (Kirigami.Units.gridUnit * 5))))
                for (const v of xs) { const x = px(v, l); ctx.beginPath(); ctx.moveTo(x, mSup); ctx.lineTo(x, mSup + altoUtil); ctx.stroke() }
                ctx.globalAlpha = 1
                ctx.strokeStyle = texto
                ctx.beginPath(); ctx.moveTo(mIzq, mSup); ctx.lineTo(mIzq, mSup + altoUtil); ctx.lineTo(width - mDer, mSup + altoUtil); ctx.stroke()
                ctx.fillStyle = texto
                ctx.textAlign = "right"; ctx.textBaseline = "middle"
                for (const v of ys) ctx.fillText(raiz.numero(v), mIzq - 6, py(v, l))
                ctx.textAlign = "center"; ctx.textBaseline = "top"
                for (const v of xs) ctx.fillText(raiz.numero(v), px(v, l), mSup + altoUtil + 4)
                if (raiz.datos.etiquetaX) ctx.fillText(raiz.datos.etiquetaX, mIzq + anchoUtil / 2, mSup + altoUtil + fuente + 8)
                if (raiz.datos.etiquetaY) {
                    ctx.save(); ctx.translate(fuente * 0.9, mSup + altoUtil / 2); ctx.rotate(-Math.PI / 2)
                    ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(raiz.datos.etiquetaY, 0, 0); ctx.restore()
                }
                ctx.save()
                ctx.beginPath(); ctx.rect(mIzq, mSup, anchoUtil, altoUtil); ctx.clip()
                // la base (punteada, atenuada) y el escenario
                const capas = []
                if (raiz.base) capas.push({ g: raiz.base, base: true })
                capas.push({ g: raiz.datos, base: false })
                for (const capa of capas) {
                    const g = capa.g
                    ctx.globalAlpha = capa.base ? 0.5 : 1
                    ctx.setLineDash(capa.base ? [6, 4] : [])
                    for (const h of (g.horizontales || [])) {
                        ctx.strokeStyle = raiz.color(h.rol); ctx.lineWidth = 1.5
                        ctx.setLineDash(capa.base ? [2, 4] : [8, 4])
                        ctx.beginPath(); ctx.moveTo(mIzq, py(h.y, l)); ctx.lineTo(width - mDer, py(h.y, l)); ctx.stroke()
                    }
                    for (const v of (g.verticales || [])) {
                        ctx.strokeStyle = raiz.color(v.rol); ctx.lineWidth = 1.5
                        ctx.setLineDash(capa.base ? [2, 4] : [8, 4])
                        ctx.beginPath(); ctx.moveTo(px(v.x, l), mSup); ctx.lineTo(px(v.x, l), mSup + altoUtil); ctx.stroke()
                    }
                    ctx.setLineDash(capa.base ? [6, 4] : [])
                    for (const linea of (g.lineas || [])) {
                        ctx.strokeStyle = raiz.color(linea.rol)
                        ctx.lineWidth = capa.base ? 1.5 : 2.5
                        ctx.beginPath()
                        for (let i = 0; i < linea.x.length; i++) {
                            const x = px(linea.x[i], l), y = py(linea.y[i], l)
                            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
                        }
                        ctx.stroke()
                    }
                    if (g.barras && g.barras.valores && g.barras.valores.length) {
                        const n = g.barras.valores.length
                        const hueco = anchoUtil / n
                        const ancho = hueco * (raiz.base ? 0.32 : 0.55)
                        for (let i = 0; i < n; i++) {
                            const centro = mIzq + hueco * (i + 0.5) + (raiz.base ? (capa.base ? -ancho * 0.55 : ancho * 0.55) : 0)
                            const y0 = py(Math.max(0, l.yMin), l), y1 = py(g.barras.valores[i], l)
                            ctx.fillStyle = raiz.color(g.barras.roles ? g.barras.roles[i] : "azul")
                            ctx.globalAlpha = capa.base ? 0.35 : 0.85
                            ctx.fillRect(centro - ancho / 2, Math.min(y0, y1), ancho, Math.abs(y0 - y1))
                        }
                    }
                    ctx.setLineDash([])
                    ctx.globalAlpha = capa.base ? 0.5 : 1
                    for (const p of (g.puntos || [])) {
                        ctx.fillStyle = texto
                        ctx.beginPath(); ctx.arc(px(p.x, l), py(p.y, l), capa.base ? 3 : 4.5, 0, 2 * Math.PI); ctx.fill()
                        if (!capa.base && p.nombre) { ctx.textAlign = "left"; ctx.textBaseline = "bottom"; ctx.fillText(p.nombre, px(p.x, l) + 6, py(p.y, l) - 4) }
                    }
                    if (g.equilibrio) {
                        const ex = px(g.equilibrio.x, l), ey = py(g.equilibrio.y, l)
                        ctx.strokeStyle = texto; ctx.lineWidth = 1
                        ctx.setLineDash([3, 3])
                        ctx.beginPath(); ctx.moveTo(ex, ey); ctx.lineTo(ex, mSup + altoUtil); ctx.moveTo(ex, ey); ctx.lineTo(mIzq, ey); ctx.stroke()
                        ctx.setLineDash([])
                        ctx.fillStyle = capa.base ? tenue : Kirigami.Theme.highlightColor
                        ctx.beginPath(); ctx.arc(ex, ey, capa.base ? 4 : 6, 0, 2 * Math.PI); ctx.fill()
                        ctx.fillStyle = texto
                        if (!capa.base) { ctx.textAlign = "left"; ctx.textBaseline = "bottom"; ctx.fillText("E", ex + 8, ey - 4) }
                    }
                }
                ctx.globalAlpha = 1
                if (!isNaN(raiz.marcaX)) {
                    ctx.strokeStyle = Kirigami.Theme.highlightColor; ctx.lineWidth = 2; ctx.setLineDash([4, 3])
                    ctx.beginPath(); ctx.moveTo(px(raiz.marcaX, l), mSup); ctx.lineTo(px(raiz.marcaX, l), mSup + altoUtil); ctx.stroke(); ctx.setLineDash([])
                }
                if (hover) {
                    ctx.fillStyle = Kirigami.Theme.highlightColor
                    ctx.beginPath(); ctx.arc(hover.px, hover.py, 5, 0, 2 * Math.PI); ctx.fill()
                }
                ctx.restore()
                // las categorías de las barras
                if (barras) {
                    const n = raiz.datos.barras.categorias.length
                    ctx.fillStyle = texto; ctx.textAlign = "center"; ctx.textBaseline = "top"
                    for (let i = 0; i < n; i++) ctx.fillText(raiz.datos.barras.categorias[i], mIzq + anchoUtil / n * (i + 0.5), mSup + altoUtil + 4)
                }
            }

            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.NoButton
                onExited: { lienzo.hover = null; lienzo.requestPaint() }
                onPositionChanged: mouse => {
                    const l = raiz.lim()
                    let mejor = null
                    for (const linea of (raiz.datos.lineas || [])) {
                        for (let i = 0; i < linea.x.length; i++) {
                            const dx = lienzo.px(linea.x[i], l) - mouse.x, dy = lienzo.py(linea.y[i], l) - mouse.y
                            const d = dx * dx + dy * dy
                            if (!mejor || d < mejor.d) mejor = { d: d, px: lienzo.px(linea.x[i], l), py: lienzo.py(linea.y[i], l), x: linea.x[i], y: linea.y[i], nombre: linea.nombre }
                        }
                    }
                    lienzo.hover = mejor && mejor.d < 900 ? mejor : null
                    lienzo.requestPaint()
                }
            }
            QQC2.Label {
                visible: lienzo.hover !== null
                x: lienzo.hover ? Math.min(lienzo.hover.px + 10, lienzo.width - width - 4) : 0
                y: lienzo.hover ? Math.max(lienzo.hover.py - height - 8, 0) : 0
                text: lienzo.hover ? (lienzo.hover.nombre + ": (" + raiz.numero(lienzo.hover.x) + "; " + raiz.numero(lienzo.hover.y) + ")") : ""
                padding: Kirigami.Units.smallSpacing
                background: Rectangle { color: Kirigami.Theme.backgroundColor; border.color: Kirigami.Theme.disabledTextColor; radius: Kirigami.Units.cornerRadius }
            }
        }

        // la marca de un resultado que no puede presentarse como válido (L8)
        QQC2.Label {
            anchors.centerIn: parent
            visible: raiz.hayDatos && raiz.invalido !== ""
            text: raiz.invalido
            rotation: -18
            font.pointSize: Kirigami.Theme.defaultFont.pointSize * 4
            font.weight: Font.Black
            color: raiz.nivelInvalido === "negativo" ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.neutralTextColor
            opacity: 0.28
            Accessible.name: raiz.invalido + ": " + raiz.motivoInvalido
        }
        Kirigami.PlaceholderMessage {
            anchors.centerIn: parent
            width: parent.width - Kirigami.Units.gridUnit * 4
            visible: !raiz.hayDatos
            icon.name: "office-chart-line"
            text: raiz.mensajeVacio
        }
    }

    // la leyenda
    Flow {
        Layout.fillWidth: true
        Layout.leftMargin: lienzo.mIzq
        spacing: Kirigami.Units.largeSpacing
        visible: raiz.hayDatos
        Repeater {
            model: (raiz.datos.lineas || []).concat(raiz.datos.horizontales || []).concat(raiz.datos.verticales || [])
            delegate: RowLayout {
                required property var modelData
                spacing: Kirigami.Units.smallSpacing
                Rectangle { implicitWidth: Kirigami.Units.gridUnit; implicitHeight: 3; color: raiz.color(modelData.rol) }
                QQC2.Label { text: modelData.nombre; font: Kirigami.Theme.smallFont }
            }
        }
        RowLayout {
            visible: raiz.base !== null && raiz.base !== undefined
            spacing: Kirigami.Units.smallSpacing
            Rectangle { implicitWidth: Kirigami.Units.gridUnit; implicitHeight: 1; color: Kirigami.Theme.disabledTextColor }
            QQC2.Label { text: "punteado: " + raiz.nombreBase; font: Kirigami.Theme.smallFont; color: Kirigami.Theme.disabledTextColor }
        }
        QQC2.Label { visible: (raiz.datos.anotacion || "") !== ""; text: raiz.datos.anotacion || ""; font: Kirigami.Theme.smallFont; color: Kirigami.Theme.disabledTextColor }
    }
}
