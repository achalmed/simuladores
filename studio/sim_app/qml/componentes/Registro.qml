// Registro — lo que dejó la última corrida del modelo actual (los valores, las curvas, las magnitudes frente a la base).
import QtQuick
import GuiComun

VistaTexto {
    readonly property var m: studio.modelos
    texto: m.registro
    mensajeVacio: !m.hayActual ? "Ningún modelo" : "Sin corrida todavía: lo que calcule el motor para " + m.id + " queda aquí"
    iconoVacio: "text-x-log"
    nombreAccesible: "Registro de " + (m.id || "ningún modelo")
}
