// Verificaciones — las verificaciones numéricas del modelo actual tal como el motor las devuelve (la coherencia
// estructural, sus identidades y teoremas, las citas de la ficha): cada una con su detalle (valor, esperado,
// diferencia) y su fuente; arriba, el resumen y la fecha del estado.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import GuiComun

ColumnLayout {
    id: pagina
    readonly property var m: studio.modelos
    spacing: 0
    RowLayout {
        Layout.fillWidth: true
        Layout.margins: Kirigami.Units.smallSpacing
        spacing: Kirigami.Units.smallSpacing
        Kirigami.Icon {
            source: pagina.m.estado === "verificado" ? "data-success" : (pagina.m.estado === "diferencias" ? "data-error" : "data-information")
            color: pagina.m.estado === "verificado" ? Kirigami.Theme.positiveTextColor : (pagina.m.estado === "diferencias" ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.neutralTextColor)
            implicitWidth: Kirigami.Units.iconSizes.smallMedium
            implicitHeight: implicitWidth
            visible: pagina.m.hayActual
        }
        QQC2.Label {
            Layout.fillWidth: true
            text: pagina.m.hayActual ? pagina.m.textoEstado + " · " + pagina.m.resumenVerificacion : ""
            wrapMode: Text.WordWrap
        }
        BotonAccion { accion: studio.acciones.accion("modelo.verificar") }
    }
    Kirigami.Separator { Layout.fillWidth: true }
    ListaDiagnosticos {
        Layout.fillWidth: true
        Layout.fillHeight: true
        modelo: pagina.m.verificacionesModelo
        mensajeVacio: !pagina.m.hayActual ? "Ningún modelo" : "Sin verificar en este studio: Verificar el modelo (F5) corre sus identidades y teoremas"
        iconoVacio: "checkmark"
        nombreAccesible: "Verificaciones de " + (pagina.m.id || "ningún modelo")
        onActivada: fila => studio.acciones.accion("archivo.abrir").disparar()
    }
}
