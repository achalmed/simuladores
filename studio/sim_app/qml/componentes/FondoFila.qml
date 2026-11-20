// FondoFila — el fondo de una fila de lista propia (el catálogo de modelos), con el lenguaje de la familia (gui-comun
// 4.2, como PanelNavegacion): la elegida teñida del acento al 0,22 con su marca a la izquierda (nunca el bloque lleno
// del acento, que en Lliphi Oscuro es el rojo de los errores), un tinte tenue al pasar y un borde con el foco del
// teclado. Colores y medidas de Kirigami.Theme, Kirigami.Units y Kirigami.ColorUtils; sin radios propios (regla del studio).
//     QQC2.ItemDelegate { id: fila; background: FondoFila { control: fila; elegida: fila.highlighted } }
import QtQuick
import org.kde.kirigami as Kirigami

Rectangle {
    id: raiz
    property Item control: null                     // el botón de la fila (un ItemDelegate)
    readonly property bool sobre: control !== null && (control.hovered || control.pressed)
    property bool elegida: false

    color: elegida ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.highlightColor, sobre ? 0.30 : 0.22)
         : control !== null && control.pressed ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.14)
         : control !== null && control.hovered ? Kirigami.ColorUtils.tintWithAlpha(Kirigami.Theme.backgroundColor, Kirigami.Theme.textColor, 0.07)
         : "transparent"
    border.width: control !== null && control.visualFocus ? 1 : 0
    border.color: Kirigami.Theme.focusColor
    Behavior on color { ColorAnimation { duration: Kirigami.Units.shortDuration } }
    Rectangle {          // la marca de la elegida
        visible: raiz.elegida
        anchors.left: parent.left
        anchors.leftMargin: Kirigami.Units.smallSpacing / 2
        anchors.verticalCenter: parent.verticalCenter
        width: Kirigami.Units.smallSpacing * 0.75
        height: parent.height - Kirigami.Units.smallSpacing * 2.5
        color: Kirigami.Theme.highlightColor
    }
}
