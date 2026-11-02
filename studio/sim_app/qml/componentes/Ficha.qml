// Ficha — la ficha pedagógica del modelo actual en Markdown (lo que el modelo declara en base.Ficha: pregunta,
// contexto, autores, supuestos, variables, ecuaciones, derivación, intuición, limitaciones, evolución, procedencia).
import QtQuick
import GuiComun

VistaTexto {
    readonly property var m: studio.modelos
    texto: m.ficha
    markdown: true
    mensajeVacio: !m.hayActual ? "Ningún modelo" : (m.cargado ? "Este modelo no trae ficha" : "No se pudo importar el modelo: " + m.motivoNoCargado)
    iconoVacio: m.hayActual && !m.cargado ? "data-error" : "text-x-generic"
    nombreAccesible: "Ficha de " + (m.id || "ningún modelo")
}
