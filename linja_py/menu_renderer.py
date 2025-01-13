import sys
from dataclasses import dataclass
from os import system

import keyboard
from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console, Group
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich.theme import Theme

from .game_master import GameMaster
from .utils import flush_stdin


@dataclass
class Option:
    """
    Clase que representa una de las opciones del menú.
    """

    name: str
    text: Text
    description: Text


class MenuRenderer:
    """
    Clase que se encarga del aspecto gráfico del menú principal.
    """

    menu_theme: Theme
    menu_console: Console
    options_panel: Panel
    options: list[Option]
    play_sub_options: list[Option]
    options_description_panel: Panel
    menu_layout: Layout
    help_layout: Layout

    def __init__(self):
        """
        Inicializa un menú principal
        """
        self.menu_theme = Theme(
            {
                "basic": "white",
                "selected": "bold black on white",
                "exit_selected": "bold white on red",
            }
        )
        self.menu_console = Console(color_system="auto", theme=self.menu_theme)

        # Opciones del menú
        self.options = [
            Option(
                "jugar",
                Text("Jugar", style="selected", justify="center"),
                Text(
                    "Empieza una partida de Linja.\n"
                    "Podrás jugar tanto contra el ordenador como contra otra persona.",
                    style="basic",
                    justify="center",
                ),
            ),
            Option(
                "ayuda",
                Text("Ayuda", style="basic", justify="center"),
                Text(
                    "Aprende a jugar al Linja.\n"
                    "Podrás ver todas las reglas del juego junto con unos ejemplos.",
                    style="basic",
                    justify="center",
                ),
            ),
            Option(
                "salir",
                Text("Salir", style="exit_selected", justify="center"),
                Text("Salir del juego.", style="basic", justify="center"),
            ),
        ]

        # Opciones de jugar
        self.play_sub_options = [
            Option(
                "pvp",
                Text("Jugador vs Jugador", style="selected", justify="center"),
                Text(
                    "Empieza una partida de Linja para dos jugadores.",
                    style="basic",
                    justify="center",
                ),
            ),
            Option(
                "pve",
                Text("Jugador vs Ordenador", style="basic", justify="center"),
                Text(
                    "Empieza una partida de Linja para un solo jugador.",
                    style="basic",
                    justify="center",
                ),
            ),
        ]

        # Panel con las opciones y descripciones de estas
        self.options_panel = Panel(
            Group(*(op.text for op in self.options)),
            title="[b]Linja[/b]",
            title_align="center",
            box=ROUNDED,
            width=None,
            border_style="yellow",
            padding=1,
        )
        self.options_description_panel = Panel(
            "", title="[b]Descripción[/b]", box=ROUNDED, border_style="cyan", padding=1
        )

        # Layout principal del menú y configuración de este para incluir todos los elementos renderizables
        self.menu_layout = Layout(name="main_menu")
        self.menu_layout.split_column(
            Layout(" ", name="dummy", size=1),
            Layout(name="options", ratio=1),
            Layout(name="hint"),
        )
        self.menu_layout["options"].update(
            Align(self.options_panel, align="center", vertical="bottom")
        )
        self.menu_layout["hint"].update(
            Align(self.options_description_panel, align="center", vertical="top")
        )

        # Layout de la interfaz de ayuda
        self.help_layout = Layout(name="help")
        self.help_layout.split_column(
            Layout(" ", name="dummy", size=1),
            Layout(name="help_content"),
            Layout(name="help_controls", size=2),
        )
        self.help_layout["help_controls"].update(
            Group(
                Rule("", style="yellow"),
                Text.from_markup(
                    r"\[[bold yellow]↑[/]/[bold yellow]↓[/]] Desplazar ayuda | \[[bold yellow]Space[/]] "
                    r"Saltar a la siguiente página | \[[bold yellow]Q[/] / [bold yellow]Esc[/]] Salir",
                    end="",
                ),
            )
        )

    def render(self, option: str | None):
        """
        Imprime el menú por pantalla.

        :param option: Opcional; opción a destacar en caso de ser pasada.
        """
        # Clear
        print("\033[2J\033[3J\033[H", end="")

        if option is None:
            self.menu_console.print(self.menu_layout)
            return

        # Cambiar el estilo de la opción resaltada
        for op in self.options:
            if op.name == option:
                if op.name == "salir":
                    op.text.style = "exit_selected"
                else:
                    op.text.style = "selected"
                self.options_description_panel.renderable = op.description
            else:
                op.text.style = "basic"

        self.menu_console.print(self.menu_layout)

    def render_help(self):
        """
        Imprime una pequeña ayuda del programa. Esta ayuda se comporta como
        un 'pager', es scrolleable por teclado.
        """

        raw_markdown_str: str
        parsed_markdown_str: str
        str_list: list[str] = []
        n_lines: int = 0
        page: str

        old_console_height: int = 0
        top_line_index: int = 0
        bottom_line_index: int

        # Leer fichero de ayuda a una string
        with open("./markdown/help.md", encoding="utf-8") as fp:
            raw_markdown_str = fp.read()

        # Limpiar buffer de entrada
        flush_stdin()

        # Input loop
        while True:
            input_loop = True

            # Volver a partir la string en caso de redimensionar la terminal
            if old_console_height != self.menu_console.height - 2:
                # Parsear el fichero e imprimirlo a una string
                with self.menu_console.capture() as capture:
                    self.menu_console.print(Markdown(raw_markdown_str))
                parsed_markdown_str = capture.get()

                str_list = parsed_markdown_str.splitlines()
                n_lines = len(str_list)
                old_console_height = (
                    self.menu_console.height - self.help_layout["help_controls"].size
                )

            # Coger solo el nº de líneas que entran en la terminal
            bottom_line_index = (
                top_line_index
                + self.menu_console.height
                - self.help_layout["help_controls"].size
            )
            page = "\n".join(str_list[top_line_index:bottom_line_index])

            # Clear e impresión
            print("\033[2J\033[3J\033[H", end="")
            self.help_layout["help_content"].update(Text.from_ansi(page, end=""))
            self.menu_console.print(self.help_layout, end="")

            # Keyboard handler del 'pager' de ayuda
            while input_loop:
                event = keyboard.read_event()

                if event.event_type != keyboard.KEY_DOWN:
                    continue

                match [event.name, event.scan_code]:
                    case ["q" | "esc", _]:  # salir
                        flush_stdin()
                        return
                    case ["w", _] | [_, 72]:  # 1 linea up
                        top_line_index = max(0, top_line_index - 1)
                        if top_line_index > 0:
                            bottom_line_index -= 1
                    case ["s", _] | [_, 80]:  # 1 linea down
                        bottom_line_index = min(n_lines, bottom_line_index + 1)
                        if bottom_line_index <= n_lines:
                            top_line_index += 1
                    case ["space", _]:
                        bottom_line_index = min(
                            n_lines,
                            bottom_line_index
                            + self.menu_console.height
                            - self.help_layout["help_controls"].size,
                        )
                        if bottom_line_index <= n_lines:
                            top_line_index += (
                                self.menu_console.height
                                - self.help_layout["help_controls"].size
                            )
                    case _:
                        continue

                input_loop = False

    def process_selection(self, option: str):
        """
        Determinar qué se debe hacer en base a la opción seleccionada por el usuario.

        :param option: Opción que ha seleccionado el usuario.
        """
        match option:
            case "salir":
                print("Saliendo del programa...")
                keyboard.unhook_all()

                # IMPORTANTE: Limpiar buffer de entrada antes de salir para evitar que
                # todas las teclas pulsadas acaben en él y ejecuten comandos no deseados
                flush_stdin()

                system("cls")
                sys.exit(0)
            case "ayuda":
                # Iniciar ayuda
                self.render_help()
            case "jugar":
                # Mostrar / Ocultar opciones de juego
                for sub_op in self.play_sub_options:
                    if sub_op in self.options:
                        self.options.remove(sub_op)
                    else:
                        self.options.insert(1, sub_op)

                self.options_panel.renderable = Group(
                    *(opt.text for opt in self.options)
                )
            case "pvp":
                # Empezar partida jvj
                keyboard.unhook_all()
                flush_stdin()

                gm = GameMaster()
                gm.game_loop(pvp=True)
            case "pve":
                # Empezar partida jvm
                keyboard.unhook_all()
                flush_stdin()

                gm = GameMaster()
                gm.game_loop(pvp=False)
            case _:
                ...
