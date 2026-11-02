// DialogoAjustesStudio — «Configurar Simuladores Studio…»: la figura académica por omisión, la terminal y el
// intérprete de las CLI del laboratorio.
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.kirigamiaddons.formcard as FormCard
import GuiComun

DialogoAjustes {
    id: dialogo
    title: "Configurar Simuladores Studio"
    readonly property var a: studio.ajustes
    modulos: [{ titulo: "General", icono: "configure", pagina: paginaGeneral }]
    onGuardado: { dialogo.a.guardar(); ventana.mensajes.mostrar("Preferencias guardadas.", "positivo") }

    Component {
        id: paginaGeneral
        ColumnLayout {
            function guardar() { dialogo.a.figuraAcademica = figura.checked; dialogo.a.terminal = terminal.text }
            FormCard.FormHeader { title: "Resultados" }
            FormCard.FormCard {
                FormCard.FormCheckDelegate { id: figura; text: "Mostrar la figura académica (matplotlib) en vez del gráfico en vivo"; checked: dialogo.a.figuraAcademica; enabled: studio.modelos.hayMatplotlib; description: studio.modelos.hayMatplotlib ? "La figura de graficos.figura: fondo blanco, la paleta del laboratorio, las etiquetas anti-solape; la misma que se exporta." : "Necesita matplotlib: el .venv del repo." }
            }
            FormCard.FormHeader { title: "El laboratorio" }
            FormCard.FormCard {
                FormCard.FormTextDelegate { text: "Raíz: " + dialogo.a.raiz }
                FormCard.FormTextDelegate { text: "Las CLI corren con " + dialogo.a.interprete + (dialogo.a.hayVenv ? " (el .venv del repo)." : ". No existe el .venv del repo: Herramientas › El entorno del studio… dice cómo crearlo.") }
            }
            FormCard.FormHeader { title: "Sistema" }
            FormCard.FormCard {
                FormCard.FormTextFieldDelegate { id: terminal; label: "Terminal para «Abrir terminal»"; text: dialogo.a.terminal; placeholderText: "konsole" }
            }
        }
    }
}
