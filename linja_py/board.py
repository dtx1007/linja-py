from enum import Enum
from copy import deepcopy
from .utils import check_coords, Turn


class CellType(Enum):
    """
    Enumerado con los tipos de celdas que puede haber en el tablero.
    """

    EMPTY = 0
    RED = 1
    BLACK = 2


def _cell_symbol(cell: CellType, markup: bool = True) -> str:
    """
    Devuelve una string con el formato correspondiente al tipa de celda pasado.

    :param cell: Tipo de celda.
    :param markup: Opcional; si se desea o no usar secuencias de marcado (False devuelve el texto plano)
    :return: String con el formato correspondiente a la celda pasada.
    """
    if not markup:
        if cell == CellType.EMPTY.value:
            return " "
        elif cell == CellType.RED.value:
            return "o"
        else:
            return "x"

    if cell == CellType.EMPTY.value:
        return " "
    elif cell == CellType.RED.value:
        return "[red]o[/]"
    else:
        return "[magenta]x[/]"


class Board:
    """
    Clase encargada del tablero del juego de Linja.
    """

    _BOARD_ROWS = 8
    _BOARD_COLS = 6

    _board: list[list[int]] = [[]]

    def __init__(self, initial_state: list[list[int]] = None):
        """
        Crea un tablero vacío o parte de uno.

        :param initial_state: Opcional, tablero a usar de base.
        """

        # Si se pasa un estado inicial, comprobar que es válido y usarlo
        if initial_state:
            if len(initial_state) != self._BOARD_ROWS:
                raise ValueError(
                    f"Initial state for Board should have '{self._BOARD_ROWS}' rows, "
                    f"got '{len(initial_state)}'."
                )

            for i, row in enumerate(initial_state):
                if self.is_edge_row(i):
                    continue

                if len(row) != 6:
                    raise ValueError(
                        f"Initial state rows for Board must be of length '{self._BOARD_COLS}', "
                        f"got '{len(row)}' for row '{i}'."
                    )

            self._board = deepcopy(initial_state)

        # Si no se pasa estado inicial, componer tablero
        else:
            ce = CellType.EMPTY.value
            cb = CellType.BLACK.value
            cr = CellType.RED.value

            self._board = [[cr, cr, cr, cr, cr, cr]]

            for i in range(self._BOARD_ROWS - 2):
                temp = []
                for j in range(self._BOARD_COLS):
                    if j == 0:
                        temp.append(cr)
                    elif j == 5:
                        temp.append(cb)
                    else:
                        temp.append(ce)

                self._board.append(temp)

            self._board.append([cb, cb, cb, cb, cb, cb])

    def __repr__(self):
        return self._board.__repr__()

    def __eq__(self, other):
        return self._board == other.get_board_array()

    def clone(self):
        return Board(self._board)

    def draw(
        self, cursor: tuple[int, int] = None, selected: tuple[int, int] = None
    ) -> str:
        """
        Construye una string con la representación del estado actual del tablero.

        :param cursor: Opcional, coordenadas donde mostrar un cursor dentro del tablero.
        :param selected: Opcional, coordenadas donde mostrar que una celda está seleccionada.
        :return: String del tablero.
        """

        padding = " " * 9
        add_padding: bool = False

        if (
            len(self._board[-1]) > self._BOARD_COLS
            or len(self._board[0]) > self._BOARD_COLS
        ):
            add_padding = True

        out = [
            f"   [bold]  0   1   2   3   4   5  [/]{padding if add_padding else ''}\n",
            f"   |---|---|---|---|---|---|{padding if add_padding else ''}\n",
        ]

        for i, row in enumerate(self._board):
            out.append(f" [bold]{i}[/] ")
            for j, cell in enumerate(row[:6]):
                if cursor is not None and cursor == (i, j):
                    if selected is not None and cursor == selected:
                        out.append(
                            f"|[bold]\[[/][bright_green]{_cell_symbol(cell, markup=False)}[/][bold]][/]"
                        )
                    else:
                        out.append(f"|[bold][[/]{_cell_symbol(cell)}[bold]][/]")
                elif selected is not None and selected == (i, j):
                    out.append(
                        f"| [bold bright_green]{_cell_symbol(cell, markup=False)}[/] "
                    )
                else:
                    out.append(f"| {_cell_symbol(cell)} ")

            if len(row) > self._BOARD_COLS and self.is_edge_row(i):
                out.append(f"|  [{_cell_symbol(row[-1])}] x{row.count(row[-1]):2}\n")
            else:
                out.append(f"|{padding if add_padding else ''}\n")
            out.append(
                f"   |---|---|---|---|---|---|{padding if add_padding else ''}\n"
            )

        return "".join(out)

    def draw_with_points(self, turn: Turn) -> str:
        """
        Construye una string con la representación del estado actual del tablero,
        muestra en el tablero información referente a los puntos del jugador pasado.

        :param turn: Turno del jugador sobre el cual construir el tablero.
        :return: String del tablero de puntos.
        """

        points = [5, 3, 2, 1, 0, 0, 0, 0]

        if turn == turn.BLACK:
            points.reverse()

        out = [
            "  [bold]   0   1   2   3   4   5    Puntos[/]    \n",
            "   |---|---|---|---|---|---|            \n",
        ]

        for i, row in enumerate(self._board):
            if (
                self.is_edge_row_for_turn(i, turn)
                and len(self._board[i]) > self._BOARD_COLS
            ):
                out.append(
                    f"   |        [bold black on red] {points[-1]} [/]"
                    f" x {self.get_piece_count_on_row(i, turn):<3}      "
                )
            else:
                out.append(f" [bold]{i}[/] ")

                for cell in row[:6]:
                    if cell == turn.value and turn == Turn.RED:
                        out.append(f"|[bold black on red] {points[-1]} [/]")
                    elif cell == turn.value and turn == Turn.BLACK:
                        out.append(f"|[bold white on magenta] {points[-1]} [/]")
                    else:
                        out.append(f"|   ")

            out.append(
                f"|  [bold]+{self.get_piece_count_on_row(i, turn) * points[-1]:-2d}[/] [bg]: {points.pop()}/pz\n[/]"
            )
            out.append("   |---|---|---|---|---|---|            \n")

        return "".join(out)

    def move_piece(self, from_coords: tuple[int, int], to_coords: tuple[int, int]):
        """
        Mueve una pieza en el tablero.

        :param from_coords: Coordenadas de la pieza a mover.
        :param to_coords: Coordenadas de destino donde se desea mover la pieza.
        """
        # Las coordenadas se comprueban externamente
        from_row, from_col = from_coords
        to_row, to_col = to_coords

        # Mover
        if self.is_edge_row(to_row):
            self._board[to_row].append(self._board[from_row][from_col])
        else:
            self._board[to_row][to_col] = self._board[from_row][from_col]

        self._board[from_row][from_col] = CellType.EMPTY.value

    def get_board_array(self) -> list[list[int]]:
        """
        Devuelve la representación en forma de lista del tablero actual.

        :return: Representación en forma de array del tablero.
        """
        return self._board

    def get_cell_type(self, coords: tuple[int, int]) -> CellType:
        """
        Devuelve el tipo respectivo de una celda del tablero.

        :param coords: Coordenadas de la pieza que se desea evaluar.
        :return: Tipo de la celda.
        """
        self.validate_coords(coords)

        return CellType(self.get_cell(coords))

    def get_cell(self, coords: tuple[int, int]) -> int:
        """
        Devuelve una celda del tablero. Se devuelve su representación
        en forma de número.

        :param coords: Coordenadas de la celda que se desea obtener.
        :return: Entero referente a la pieza seleccionada.
        """
        self.validate_coords(coords)

        row, col = coords

        return self._board[row][col]

    def get_cells_coords(self, turn: Turn) -> list[tuple[int, int]]:
        """
        Obtiene una lista de coordenadas referentes a las piezas de un color dado.

        :param turn: Color del cual se desean obtener sus piezas.
        :return: Lista con las coordenadas de las piezas de dicho color.
        """

        out: list = []

        for i, row in enumerate(self._board):
            for j, cell in enumerate(row):
                if CellType(cell).value == turn.value:
                    out.append((i, j))

        return out

    def get_piece_count_on_row(self, row: int, turn: Turn = None) -> int:
        """
        Obtiene cuál es el número de piezas que hay es una fila dada.

        :param row: Fila que se desea evaluar.
        :param turn: Opcional; turno de uno de los jugadores, filtra las piezas
               para solo contar las del turno respectivo.
        :return: Número de piezas que había en la fila pasada. -1 en caso de
                 no pasar una fila válida dentro del tablero.
        """
        if 0 <= row < self._BOARD_ROWS:
            if not turn:
                return self._board[row].count(CellType.RED.value) + self._board[
                    row
                ].count(CellType.BLACK.value)

            if turn == Turn.RED:
                return self._board[row].count(CellType.RED.value)
            else:
                return self._board[row].count(CellType.BLACK.value)

        return -1

    def is_edge_row(self, row: int) -> bool:
        """
        Comprueba si una fila se considera uno de los extremos del tablero.

        :param row: Fila que se desea evaluar.
        :return: Si la fila es o no uno de los extremos del tablero.
        """
        return row == 0 or row == self._BOARD_ROWS - 1

    def is_edge_row_for_turn(self, row: int, turn: Turn) -> bool:
        """
        Comprueba si una fila es considerada una esquina del tablero para
        un turno determinado.

        :param row: Fila que se desea evaluar.
        :param turn: Turno sobre el cual evaluar la fila.
        :return: Si la fila es ono uno de los extremos del tablero para el turno
                 pasado.
        """
        if turn == Turn.RED:
            return row == self._BOARD_ROWS - 1
        else:
            return row == 0

    def is_piece(self, coords: tuple[int, int]) -> bool:
        """
        Comprueba si unas coordenadas del tablero corresponden con una pieza.

        :param coords: Coordenadas del tablero a evaluar.
        :return: Si las coordenadas pasadas correspondían a una pieza o no.
        """
        self.validate_coords(coords)

        return self.get_cell_type(coords) in (CellType.RED, CellType.BLACK)

    def is_empty(self, coords: tuple[int, int]) -> bool:
        """
        Comprueba si una de las coordenadas del tablero corresponde a una celda
        vacía.

        :param coords: Coordenadas a evaluar.
        :return: Si las coordenadas pasadas  correspondían o no a una celda vacía.
        """
        self.validate_coords(coords)

        return self.get_cell_type(coords) == CellType.EMPTY

    def validate_coords(self, coords: tuple[int, int], strict: bool = True) -> bool:
        """
        Valida si unas coordenadas dadas pertenecen o no a este tablero.

        :param coords: Coordenadas a evaluar.
        :param strict: Si esta función debería devolver un valor o lanzar una excepción
                       en caso de que las coordenadas no sean válidas. Estricto significa
                       lanzar una excepción.
        :return: Si la coordenada pasada pertenece a los límites del tablero.
        """
        check_coords(coords)

        row, col = coords

        if not (0 <= row < self._BOARD_ROWS) or not (0 <= col < self._BOARD_COLS):
            if strict:
                raise ValueError(
                    "Coordinates should be contained within the board boundaries.\n"
                    f"Max board height (rows): {self._BOARD_ROWS} | Max board width (cols): {self._BOARD_COLS}\n"
                    f"Expected: (0 <= row < {self._BOARD_ROWS}, 0 <= col < {self._BOARD_COLS}) | Got: 'coords' = {coords}"
                )

            return False

        return True
