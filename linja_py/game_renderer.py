from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console, Group, group
from rich.layout import Layout
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich.theme import Theme

from .board import Board
from .utils import Move, Turn, ErrorMsg


class GameRenderer:
    """
    Clase encargada del aspecto visual del juego.
    """

    console: Console
    game_theme: Theme
    game_layout: Layout

    title_container: Align

    controls_text: Text

    def __init__(self):
        """
        Inicializa una interfaz del juego.
        """

        # Inicializar tema y terminal
        self.game_theme = Theme(
            {
                "bc": "bold cyan",
                "br": "bold red",
                "by": "bold yellow",
                "bm": "bold magenta",
                "bg": "bold bright_black",
                "y": "yellow",
            }
        )

        self.console = Console(color_system="auto", theme=self.game_theme)

        # Inicializar contenedores
        self.title_container = Align(
            Group(
                Rule("[by]Linja[/]", style="yellow"),
                Text.from_markup("[bg]Turno: 0[/]", end="", justify="center"),
                fit=False,
            ),
            align="center",
            vertical="middle",
        )

        self.controls_text = Text.from_markup(
            "\[[by]↑[/]/[by]↓[/]/[by]←[/]/[by]→[/]] o \[[by]W[/]/[by]S[/]/[by]A[/]/[by]D[/]] Mover cursor [bg]|[/]"
            " \[[by]Enter[/]] o \[[by]Space[/]] Seleccionar / Confirmar movimiento\n"
            "\[[by]U[/]] Deshacer [bg]|[/] \[[by]Y[/]] Rehacer [bg]|[/]"
            " \[[by]X[/]] Cancelar selección [bg]|[/] \[[br]Q[/]] Salir",
            justify="center",
            end="",
        )

        # Definir layout
        self.game_layout = Layout(name="main_layout")
        self.game_layout.split_column(
            Layout(" ", name="dummy", size=1),
            Layout(self.title_container, name="title", size=2),
            Layout(name="board_points", minimum_size=21),
            Layout(name="history", minimum_size=3),
            Layout(name="controls", minimum_size=2),
        )
        self.game_layout["board_points"].split_column(
            Layout(name="boards"),
            Layout(name="points_info", size=1),
        )
        self.game_layout["board_points"]["boards"].split_row(
            Layout(name="normal_board"), Layout(name="points_board")
        )
        self.game_layout["controls"].split_column(
            Layout(name="error_msg", visible=False, size=1),
            Layout(self.controls_text, name="controls_help", size=2),
        )

    @group(fit=False)
    def get_title_container(self, turn_count: int) -> Group:
        """
        Genera el contenedor del título y el turno actual.
        :return: Group con el título y el tiempo.
        """
        yield Rule("[by]Linja[/]", style="yellow")
        yield Text.from_markup(f"[bg]Turno: {turn_count}[/]", end="", justify="center")

    def get_boards(
        self,
        board: Board,
        turn: Turn,
        cursor_pos: tuple[int, int] | None = None,
        selected_pos: tuple[int, int] | None = None,
    ) -> Align:
        """
        Genera el objeto renderizable del tablero normal o el tablero de puntos
        de la partida. En función de si se pasan coordenadas de cursor o no se
        determina qué tablero crear.

        :param board: Tablero del cual obtener la representación gráfica.
        :param turn: Turno del jugador, necesario para el tablero de puntos.
        :param cursor_pos: Opcional; coordenadas del cursor en el tablero normal.
        :param selected_pos: Opcional; coordenadas de la celda seleccionada en el tablero normal.
        :return: Contenedor (Align) con el tablero respectivo dentro.
        """

        normal_board = True if cursor_pos else False

        # Tablero normal si se pasan posiciones, tablero de puntos si solo se pasa el turno
        return Align(
            Panel(
                Text.from_markup(
                    board.draw(cursor_pos, selected_pos)
                    if normal_board
                    else board.draw_with_points(turn),
                    end="",
                ),
                box=ROUNDED,
                title=f"[by]{'Tablero' if normal_board else 'Puntos'}[/]",
                title_align="left",
                border_style="yellow",
            ),
            align="center",
            vertical="middle",
        )

    def get_move_pairs(self, history: list[Move]) -> list[list[Move]]:
        """
        Obtiene una lista de movimientos agrupada por turnos.

        :param history: Historial con todas las jugadas
        :return: Lista de movimientos agrupada por turnos
        """
        move_pairs: list[list[Move]] = []
        temp: list[Move] = []
        last_turn: Turn

        if not history or len(history) == 0:
            return []

        # Agrupar movimientos por turnos
        last_turn = history[0].turn

        for move in history:
            if move.turn == last_turn:
                temp.append(move)
            else:
                last_turn = move.turn
                move_pairs.append(temp.copy())
                temp.clear()
                temp.append(move)

        move_pairs.append(temp.copy())

        return move_pairs

    def get_history(self, move_pairs: list[list[Move]] | None = None) -> Align:
        """
        Genera la representación gráfica del historial de la partida actual.

        :param move_pairs: Lista con los pares de movimientos de cada turno.
        :return: Contenedor (Align) con el historial de las jugadas pasadas.
        """
        # turno | R: (1, 2) -> (2, 3) ... | ()

        turn_counter = 0
        content: Text
        last_turn: Turn
        temp: list[str] = []

        # Si no hay historial mostrar un mensaje por defecto
        if len(move_pairs) == 0:
            content = Text("No hay jugadas en el historial.", end="")
        else:
            # Determinar cuantas líneas imprimir, mostrando primero las más recientes
            # -1: dummy | -2: title | -3: controles | -21: tablero | -2: bordes
            history_height = self.console.height - 1 - 2 - 3 - 21 - 2
            last_line = len(move_pairs)
            display_lines = min(len(move_pairs), history_height)

            turn_counter = last_line - display_lines

            # Iterar cada par de movimientos
            for i in range(last_line - display_lines, last_line):
                move_pair = move_pairs[i]
                last_turn = move_pair[0].turn

                # Estilo en función del color
                st = "br" if last_turn == Turn.RED else "bm"
                tr = "R" if last_turn == Turn.RED else "B"

                temp.append(f"[bg]{turn_counter}[/]|[{st}]{tr}[/]: ")

                # Iterar cada movimiento del par y añadirlo a la string temporal
                for move in move_pair:
                    temp.append(
                        f"[bold]{move.from_coords}[/] [bg]->[/] [bold]{move.to_coords}[/] [bg]|[/] "
                    )

                temp.append("\n")
                turn_counter += 1

            content = Text.from_markup("".join(temp), end="")

        return Align(
            Panel(
                content,
                box=ROUNDED,
                title="[by]Historial[/]",
                title_align="left",
                border_style="yellow",
                width=self.console.width,
            ),
            align="center",
            vertical="top",
        )

    def get_error_msg(self, err_msg: ErrorMsg) -> Text:
        """
        Genera un objeto renderizable para el mensaje de error del juego actual.

        :param err_msg: Mensaje de error a renderizar.
        :return: Text con el contenido del mensaje de error.
        """
        label_index = err_msg.find(":") + 1
        return Text.from_markup(
            f"[br]{err_msg[:label_index]}[/]{err_msg[label_index:]}",
            end="",
            justify="center",
        )

    def get_points_info(self, points: int, evaluation: int) -> Text:
        """
        Genera un objeto renderizable de los puntos y la evaluación del estado actual
        del tablero.

        :param points: Puntos del tablero actual.
        :param evaluation: Evaluacón del tablero actual.
        :return: Text con la puntuación y la evaluación actual del tablero.
        """
        return Text.from_markup(
            f"Número de puntos: [bold]{points}[/] [bg]|[/] Evaluación del tablero: [bold]{evaluation}[/]",
            justify="center",
            end="",
        )

    def render(
        self,
        board: Board,
        turn: Turn,
        cursor_pos: tuple[int, int] | None = None,
        selected_pos: tuple[int, int] | None = None,
        history: list[Move] | None = None,
        points: int = 0,
        evaluation: int = 0,
        err_msg: ErrorMsg | None = None,
    ):
        """
        Renderiza la interfaz del juego.

        :param board: Tablero actual.
        :param turn: Turno del jugador actual.
        :param cursor_pos: Coordenadas del cursor en el tablero-
        :param selected_pos: Coordenadas de la celda seleccionada en el tablero.
        :param history: Historial de jugadas.
        :param points: Puntos del jugador actual.
        :param evaluation: Evaluación del tablero actual.
        :param err_msg: Mensaje de error.
        """

        # Añadir mensaje de error u ocultarlo
        if err_msg:
            self.game_layout["controls"].size = 3
            self.game_layout["controls"]["error_msg"].update(
                self.get_error_msg(err_msg)
            )
            self.game_layout["controls"]["error_msg"].visible = True
        else:
            self.game_layout["controls"].size = 2
            self.game_layout["controls"]["error_msg"].visible = False

        # Actualizar puntos
        self.game_layout["board_points"]["points_info"].update(
            self.get_points_info(points, evaluation)
        )

        # Actualizar tableros
        self.game_layout["board_points"]["boards"]["normal_board"].update(
            self.get_boards(board, turn, cursor_pos, selected_pos)
        )

        self.game_layout["board_points"]["boards"]["points_board"].update(
            self.get_boards(board, turn)
        )

        # Actualizar historial
        move_pairs = self.get_move_pairs(history)
        turn_count = (
            len(move_pairs)
            if len(move_pairs) == 0 or turn != move_pairs[-1][0].turn
            else len(move_pairs) - 1
        )
        self.game_layout["history"].update(self.get_history(move_pairs))

        # Actualizar nº. turno
        self.game_layout["title"].update(self.get_title_container(turn_count))

        # Clear
        print("\033[2J\033[3J\033[H", end="")
        # Render
        self.console.print(self.game_layout)

    def render_end(self, winner: Turn, win_condition: str):
        color = "red" if winner == Turn.RED else "magenta"
        winner_color = "Rojo" if winner == Turn.RED else "Negro"
        reason = (
            "Ha obtenido más puntos que el rival."
            if win_condition == "score"
            else "El rival se ha quedado sin movimientos legales."
        )

        self.console.print(
            Align(
                Group(
                    "\n",
                    Panel(
                        Text.from_markup(
                            f"Ha ganado el color '{winner_color}'\nRazón: {reason}",
                            end="",
                            justify="center",
                        ),
                        border_style=f"bold {color} blink",
                        style=f"bold {color} blink",
                        expand=True,
                    ),
                    Text.from_markup(
                        f"[bold {color} blink]Gracias por jugar :D[/]",
                        end="",
                        justify="center",
                    ),
                ),
                align="center",
                vertical="middle",
            )
        )
