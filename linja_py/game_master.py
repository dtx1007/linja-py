import sys
import time
from dataclasses import dataclass
from math import inf

import keyboard

from .board import Board
from .game_renderer import GameRenderer
from .undo import Undo
from .utils import Move, Turn, ErrorMsg, side_by_side_str, flush_stdin


@dataclass(frozen=True)
class MinimaxResult:
    best_move_set: list[Move]
    best_value: float


class GameMaster:
    _undo: Undo[Board]
    _current_board: Board

    _move_history: list[Move]
    _move_history_redo: list[Move]
    _move_count: int
    _movement: int

    _turn: Turn
    _winner: Turn | None
    _win_condition: str | None
    _extra_turn_expended: bool
    _cursor: tuple[int, int]

    _minimax_calls: int
    _renderer: GameRenderer

    def __init__(self):
        self._movement = 1
        self._move_history = []
        self._move_history_redo = []

        self._turn = Turn.RED
        self._winner = None
        self._extra_turn_expended = False
        self._cursor = (0, 0)

        self._current_board = Board()
        self._undo = Undo()

        self._minimax_calls = 0
        self._renderer = GameRenderer()

    def move_cursor(self, move_amount: tuple[int, int]):
        new_cursor_x = (
            self._cursor[0] + move_amount[0]
        ) % self._current_board._BOARD_ROWS
        new_cursor_y = (
            self._cursor[1] + move_amount[1]
        ) % self._current_board._BOARD_COLS
        new_cursor_pos = (new_cursor_x, new_cursor_y)

        if self._current_board.validate_coords(new_cursor_pos, strict=False):
            self._cursor = new_cursor_pos

    def calculate_points(self, turn: Turn) -> int:
        points: int = 0
        points_per_row = [5, 3, 2, 1, 0, 0, 0, 0]

        if turn == turn.BLACK:
            points_per_row.reverse()

        # Iterar filas y calcular puntuación en base a las piezas del color respectivo
        for i, row in enumerate(self._current_board.get_board_array()):
            points += (
                self._current_board.get_piece_count_on_row(i, turn)
                * points_per_row.pop()
            )

        if turn == turn.BLACK:
            points *= -1

        return points

    def evaluate_board(self):
        points_b = self.calculate_points(Turn.BLACK)
        points_r = self.calculate_points(Turn.RED)

        # Ajustar para el ganador
        if self.is_over():
            if self._turn == Turn.BLACK:
                points_b = -999
            else:
                points_r = 999
        # Tener en cuenta la posibilidad de quedarse bloqueado como un estado no deseado
        elif self.is_stuck():
            if self._turn == Turn.BLACK:
                points_r = 999
            else:
                points_b = -999

        return points_r + points_b

    def calculate_max_move_amount(self) -> int:
        last_turn = None
        last_move_to_row = None

        # Obtener fila y turno del último mov y calcular máximo movimiento en esta jugada
        if len(self._move_history) > 0:
            last_turn = self._move_history[-1].turn
            last_move_to_row = (
                self._move_history[-1].to_coords[0]
                if len(self._move_history) != 0
                else None
            )

        # Existe la excepción de que la jugada 1 fuese a una esquina, lo que significa que el jugador solo puede
        # mover 1 este turno, si no se calcula de forma normal
        if last_move_to_row is not None:
            if last_turn != self._turn:
                return 1
            if (
                self._current_board.is_edge_row(last_move_to_row)
                or self._move_history[-1].movement == 2
            ):
                return 1
            else:
                return self._current_board.get_piece_count_on_row(last_move_to_row) - 1

        # Para que no haya movimientos anteriores tenemos que estar en el primer movimiento de la partida
        # Máx. en primer movimiento es 1
        return 1

    def check_if_legal(
        self, move: int, from_coords: tuple[int, int], to_coords: tuple[int, int]
    ) -> ErrorMsg | None:
        from_row, from_col = from_coords
        to_row, to_col = to_coords

        if not self._current_board.is_edge_row(
            to_row
        ) and not self._current_board.is_empty(to_coords):
            return ErrorMsg(
                "MOVIMIENTO ILEGAL: No puedes moverte a una celda que ya está ocupada."
            )
        elif (self._turn == Turn.RED and to_row < from_row) or (
            self._turn == Turn.BLACK and to_row > from_row
        ):
            return ErrorMsg("MOVIMIENTO ILEGAL: No puedes moverte hacia atrás.")

        # Obtener fila del último mov y calcular máximo movimiento en esta jugada
        last_move_to_row = (
            self._move_history[-1].to_coords[0]
            if len(self._move_history) != 0
            else None
        )

        # Calcular máximo movimiento permitido
        allowed_move_amount = self.calculate_max_move_amount()

        move_amount = abs(to_row - from_row)

        if move_amount == 0:
            return ErrorMsg(
                "MOVIMIENTO ILEGAL: No puedes moverte a la misma fila en la que ya estás."
            )
        elif move == 1 and move_amount != 1:
            return ErrorMsg(
                "MOVIMIENTO ILEGAL: En tu primer movimiento solo puedes moverte una fila hacia delante."
            )
        elif (
            move == 2
            and self._current_board.is_edge_row(last_move_to_row)
            and move_amount != allowed_move_amount
        ):
            return ErrorMsg(
                "MOVIMIENTO ILEGAL: En tu primer movimiento llegaste a uno de los bordes del tablero, "
                "esto significa que no puedes mover más de 1 en tu siguiente movimiento."
            )
        elif move == 2 and move_amount != allowed_move_amount:
            return ErrorMsg(
                "MOVIMIENTO ILEGAL: En tu segundo movimiento has de moverte el equivalente en filas al"
                "número de fichas que había en la posición final de tu movimiento anterior.\n"
                f"Has intentado moverte '{move_amount}' filas pero debes moverte '{allowed_move_amount}'."
            )
        elif (
            not self._current_board.is_edge_row(to_row)
            and self._current_board.get_piece_count_on_row(to_row) == 6
        ):
            return ErrorMsg(
                "MOVIMIENTO ILEGAL: Las filas intermedias del tablero solo pueden tener un máximo de "
                "6 fichas. Mueve otra pieza."
            )

        return None

    def check_if_selectable(self, coords: tuple[int, int]) -> ErrorMsg | None:
        if not self._current_board.is_piece(coords):
            return ErrorMsg(
                "ERROR DE SELECCIÓN: No puedes seleccionar una celda que no contiene ninguna pieza."
            )
        elif self._current_board.get_cell_type(coords).name != self._turn.name:
            return ErrorMsg(
                "ERROR DE SELECCIÓN: No puedes mover las piezas del contrincante.\n"
                f"Eres el color {'rojo (o)' if self._turn.name == 'RED' else 'negro (x)'}."
            )

        return None

    def make_move(
        self, move: int, from_coords: tuple[int, int], to_coords: tuple[int, int]
    ) -> ErrorMsg | None:
        # Comprobar si el movimiento es legal
        err = self.check_if_legal(move, from_coords, to_coords)

        if err:
            return err

        temp_last_board = self._current_board.clone()

        self._current_board.move_piece(from_coords, to_coords)
        self._undo.add_item(temp_last_board, self._current_board.clone())
        self._move_history.append(Move(from_coords, to_coords, move, self._turn))
        self._move_history_redo.clear()

        # Determinar siguiente turno
        temp_next_turn = self.next_turn()

        if temp_next_turn != self._turn:
            self._movement = 1
        else:
            self._movement = 2 if move == 1 else 1

        # Comprobar si hay ganador, en caso contrario decidir para quien es el siguiente turno
        if self.is_over():
            self._winner = self._turn
            self._win_condition = "score"
        elif self.is_stuck():
            self._winner = self._turn.get_oposite()
            self._win_condition = "stuck"
        else:
            self._turn = temp_next_turn
            self._winner = None
            self._win_condition = None

    def next_turn(self) -> Turn:
        last_move = self._move_history[-1] if len(self._move_history) != 0 else None
        turn_count = 0

        if last_move:
            last_to_row = last_move.to_coords[0]
            last_movement = last_move.movement
            last_turn = last_move.turn

            # Turno extra para el jugador si había movido a una fila sin fichas
            if (
                last_movement == 2
                and self._current_board.get_piece_count_on_row(last_to_row) - 1 == 0
            ):
                # Calcular para los 4 últimos movimientos (contando este) si los 4 eran consecutivos
                # en cuyo caso quitar la posibilidad de volver a ganar un turno extra en este movimiento
                if len(self._move_history) > 3:
                    for move in self._move_history[-4:]:
                        if move.turn == self._turn:
                            turn_count += 1
                        else:
                            break

                        if turn_count == 4:
                            return last_turn.get_oposite()

                return last_turn

            # Perder el turno por haber movido a una fila sin fichas
            elif (
                last_movement == 1
                and self._current_board.get_piece_count_on_row(last_to_row) - 1 == 0
            ):
                return last_turn.get_oposite()

            # Si era el primer movimiento del jugador, devolverle el turno
            elif last_movement == 1:
                return last_turn

            # Si no era el primer movimiento del jugador ni cumplía lo anterior, pasar turno
            else:
                return last_turn.get_oposite()

        return self._turn

    def is_over(self) -> bool:
        # - El juego termina cuando las piezas de ambos jugadores quedan separadas
        # - El juego también puede terminar porque uno de los jugadores haya introducido todas sus piezas
        # en el extremo opuesto
        # - Existe la posibilidad de quedarse sin movimientos legales, esto resulta en victoria
        # para el jugador que no se queda bloqueado -> is_stuck()

        # Comprobar si uno de los colores ha metido todas sus piezas en el extremo opuesto
        red_points = self.calculate_points(Turn.RED)
        black_points = self.calculate_points(Turn.BLACK)

        if abs(red_points) == 60 or abs(black_points) == 60:
            return True

        # Obtener las filas en las que hay piezas rojas (usar sets para quitar duplicados)
        red_cells_rows = {
            row for row, _ in self._current_board.get_cells_coords(Turn.RED)
        }
        black_cells_rows = {
            row for row, _ in self._current_board.get_cells_coords(Turn.BLACK)
        }

        # Obtener las últimas filas en las que hay piezas de cada color
        last_red_cell_row = min(red_cells_rows)
        last_black_cell_row = max(black_cells_rows)

        return last_red_cell_row > last_black_cell_row

    def is_stuck(self) -> bool:
        # Segunda condición de fin; uno de los jugadores se queda bloqueado.

        move_amount = self.calculate_max_move_amount()
        current_turn_cells = self._current_board.get_cells_coords(self._turn)
        last_cell_x = -1

        # - En el caso de perder el turno este check es necesario
        # Si no, perder el turno resultaría en siempre estar considerado como una posición sin movimientos legales
        # - También hay que tener en cuenta que este check es necesaria si la partida ya ha terminado,
        # puesto que, sino, hay fines de partida que pueden no tener más movimientos legales (porque ya se ha ganado)
        if move_amount == 0 or self._winner is not None:
            return False

        for cell_x, cell_y in current_turn_cells:
            # Si la pieza ya está en uno de los extremos no evaluarla
            if self._current_board.is_edge_row_for_turn(cell_x, self._turn):
                continue

            # No comprobar movimientos de fichas en la misma fila
            if last_cell_x == cell_x:
                continue

            # Obtener dirección hacia la que mover en función del turno
            to_x = (
                cell_x + move_amount
                if self._turn == Turn.RED
                else (cell_x - move_amount)
            )

            # Si la ficha tuviera que moverse fuera del tablero no sería un mov legal
            if not self._current_board.validate_coords((to_x, 0), strict=False):
                continue

            # Obtener columna a mover
            if self._current_board.is_empty(
                (to_x, cell_y)
            ) or self._current_board.is_edge_row(to_x):
                to_y = cell_y
            else:
                for i in range(len(self._current_board.get_board_array()[to_x])):
                    if self._current_board.is_empty((to_x, i)):
                        to_y = i
                        break
                else:
                    # Si no se puede coger la columna significa que no hay hueco para colocar esta
                    # pieza en la fila de destino, lo cual significa que este movimiento no es legal
                    continue

            if (
                self.check_if_legal(self._movement, (cell_x, cell_y), (to_x, to_y))
                is None
            ):
                return False

            last_cell_x = cell_x

        return True

    def undo_move(self) -> ErrorMsg | None:
        if len(self._undo) == 0:
            return ErrorMsg("ERROR DE DESHACER: No quedan jugadas para deshacer.")

        # No haría falta comprobar que existe porque si se puede hacer undo ya había un movimiento anterior
        last_move = self._move_history.pop()
        self._move_history_redo.append(last_move)

        # Devolver estado al tablero y actualizar undo
        self._current_board = self._undo.undo()
        self._turn = last_move.turn
        self._movement = last_move.movement

    def redo_move(self) -> ErrorMsg | None:
        if self._undo.redo_length() == 0:
            return ErrorMsg("ERROR DE REHACER: No quedan jugadas para rehacer.")

        next_move = self._move_history_redo.pop()
        self._move_history.append(next_move)

        # Recuperar estado inmediatamente más nuevo del tablero
        self._current_board = self._undo.redo()
        self._turn = self.next_turn()
        self._movement = 2 if next_move.movement == 1 else 1

    def minimax(
        self,
        max_depth: int,
        is_maximizing: bool,
        depth: int = 0,
        alpha: float = -inf,
        beta: float = inf,
    ) -> MinimaxResult:
        # Implementación Minimax con poda Alfa-Beta
        # 1. Empezar en el estado actual
        # 2. Generar todos los posibles movimientos para el jugador actual
        #      - Generar todos los movimientos parciales en el mismo nodo
        # 3. Ir al primer nodo y recurrir hasta llegar a un nodo hoja (estado final) o frontera de exploración
        #      - A la hora de recurrir, debemos maximizar la función heurística en los nodos en los que juega
        #        el ordenador. A su vez, minimizar los nodos en los que juega el jugador.
        #      - En los nodos de maximización debemos asignar el valor a Alfa, y a Beta en los de minimización.
        #          - Alfa empieza en -inf y Beta en +inf (para preferir los valores obtenidos)
        #      - En la recursión, comprobar que el valor de Alfa es menor que Beta, en caso contrario, podar
        #        dicha rama y dejar de explorar por ahí. (Poda Alfa-Beta)
        # 4. Devolver el mayor valor de Alfa en los nodos Max y el menor de Beta en los nodos Min
        # 4. Una vez explorados todos los estados posibles devolver el nodo con mejor valor máximo

        best_move: list[Move]
        temp_move: list[Move]
        best_value: float
        value: float
        inital_turn: Turn = Turn(self._turn)

        self._minimax_calls += 1

        if max_depth <= 0:
            raise ValueError(
                f"Can not perform minimax up to a depth of '{max_depth}', depth should be bigger than 0."
            )

        # Si llegamos a la frontera de exploración o al final del juego devolver puntos
        # No devolvemos movimiento dado que este se incluye en el retorno de los niveles
        # superiores, en los nodos finales solo nos interesa obtener el valor de la función
        # heurística.
        if depth == max_depth or self.is_over() or self.is_stuck():
            return MinimaxResult([], self.evaluate_board())

        if is_maximizing:
            # Rama de max
            best_value = -inf

            # Iterar por los movimientos posibles
            for move in self._next_move_generator():
                value = self.minimax(
                    max_depth, False, depth + 1, alpha, beta
                ).best_value

                if value > best_value:
                    best_value = value
                    best_move = move

                alpha = max(best_value, alpha)

                # Corte Beta
                if not alpha < beta:
                    # Dado que terminamos la ejecución el generador no tiene
                    # posibilidad de dejar el turno en su estado inicial dado
                    # que no ha podido explorar todos los movimientos posibles

                    # Reiniciar tablero al turno anterior
                    for _ in range(len(move)):
                        self.undo_move()
                    break

            return MinimaxResult(best_move, best_value)
        else:
            # Rama de min
            best_value = inf

            for move in self._next_move_generator():
                value = self.minimax(max_depth, True, depth + 1, alpha, beta).best_value

                if value < best_value:
                    best_value = value
                    best_move = move

                beta = min(best_value, beta)

                # Corte Alfa
                if not alpha < beta:
                    for _ in range(len(move)):
                        self.undo_move()
                    break

            return MinimaxResult(best_move, best_value)

    def print_possible_moves(self):
        gen = self._next_move_generator()
        initial_board = self._current_board.clone()
        second_move_board: Board

        hit_count: int = 0

        for i, move in enumerate(self._next_move_generator()):
            # if i == 5:
            #     break

            second_move_board = self._current_board.clone()

            print(f"Possible move n.º {i}")

            for pmove in move:
                print(pmove)

            print(
                side_by_side_str(
                    [
                        initial_board.draw(),
                        self._current_board.draw(),
                        self._current_board.draw_with_points(self._turn.get_oposite()),
                    ]
                )
            )
            print(
                f"Your score: {self.calculate_points(self._turn.get_oposite())}\n"
                f"Opponents score: {self.calculate_points(self._turn)}\n"
                f"Move eval: {self.evaluate_board()}\n"
            )

            for j, move_2 in enumerate(self._next_move_generator()):
                print(f"Possible move n.º {i}.{j}")

                for pmove in move_2:
                    print(pmove)

                print(
                    side_by_side_str(
                        [
                            second_move_board.draw(),
                            self._current_board.draw(),
                            self._current_board.draw_with_points(
                                self._turn.get_oposite()
                            ),
                        ]
                    )
                )
                print(
                    f"Your score: {self.calculate_points(self._turn.get_oposite())}\n"
                    f"Opponents score: {self.calculate_points(self._turn)}\n"
                    f"Move eval: {self.evaluate_board()}\n"
                )

                hit_count += 1

            hit_count += 1

        print(f"Total possible moves: {hit_count}")

    def _next_move_generator(self):
        turn = self._turn
        movement = self._movement

        allowed_movement_amount: int
        to_x: int
        to_y: int
        last_cell_x: int = -1

        # Obtener piezas pertenecientes a este turno y cantidad a mover
        turn_cells_coords: list[tuple[int, int]] = self._current_board.get_cells_coords(
            turn
        )
        allowed_movement_amount: int = self.calculate_max_move_amount()

        # Iterar cada pieza
        for cell_x, cell_y in turn_cells_coords:
            # Si la pieza ya está en uno de los extremos no evaluarla
            if self._current_board.is_edge_row_for_turn(cell_x, turn):
                continue

            # No comprobar movimientos de fichas en la misma fila
            if last_cell_x == cell_x:
                continue

            # Obtener dirección hacia la que mover en función del turno
            to_x = (
                cell_x + allowed_movement_amount
                if turn == Turn.RED
                else (cell_x - allowed_movement_amount)
            )

            # Comprobar que la fila a la que nos movemos está en el tablero
            if not self._current_board.validate_coords((to_x, 0), strict=False):
                continue

            # Calcular columna (priorizar misma columna)
            if self._current_board.is_empty(
                (to_x, cell_y)
            ) or self._current_board.is_edge_row(to_x):
                to_y = cell_y
            else:
                # Motivos estéticos, preferir movimiento más a la izquierda para rojas y der, para negras
                if turn == Turn.RED:
                    temp_range = range(len(self._current_board.get_board_array()[to_x]))
                else:
                    temp_range = range(
                        len(self._current_board.get_board_array()[to_x]) - 1, -1, -1
                    )

                # Si no se puede en la misma columna buscar primera columna libre en la fila a mover
                for i in temp_range:
                    if self._current_board.is_empty((to_x, i)):
                        to_y = i
                        break
                else:
                    # Si no hay ninguna columna vacía significa que esa pieza no tiene un movimiento legal
                    continue

            self.make_move(movement, (cell_x, cell_y), (to_x, to_y))
            if self.is_stuck():
                self._winner = None
                self._win_condition = None
            elif self._turn == turn and not self.is_over():
                # Guardar movimiento actual
                parent_move = [Move((cell_x, cell_y), (to_x, to_y), movement, turn)]

                # Recurrir en esta misma función para ir generando los posibles movimientos secundarios
                # del movimiento realizado
                for move in self._next_move_generator():
                    yield parent_move + move
            else:
                # Si el turno ya no es nuestro devolver el movimiento hecho (usando un generador)
                yield [Move((cell_x, cell_y), (to_x, to_y), movement, turn)]

            # Revertir el movimiento para conservar el estado inicial y permitir el cálculo
            # recursivo de posibles movimientos
            self.undo_move()

            last_cell_x = cell_x

    def game_loop(self, pvp: bool = True, player: Turn = Turn.RED):
        # Variables de impresión y control
        selected_coords: tuple[int, int] | None = None
        input_loop: bool

        # Variable con el mensaje de error de los movimientos
        err_msg: ErrorMsg | None = None

        # Variables del pve
        computer_moves: list[Move]
        minimax_max_depth: int = 2

        while True:
            if self._winner is not None:
                self._renderer.render_end(self._winner, self._win_condition)
                keyboard.unhook_all()
                flush_stdin()
                exit(0)

            # Turno del ordenador (en caso de jugar contra él)
            if not pvp and self._turn == player.get_oposite():
                # Obtener mejor conjunto de movimientos
                computer_moves = self.minimax(minimax_max_depth, False).best_move_set

                # Mover
                for move in computer_moves:
                    # Mostrar selección de pieza de la IA
                    self._renderer.render(
                        self._current_board,
                        self._turn,
                        move.from_coords,
                        None,
                        self._move_history,
                        self.calculate_points(self._turn),
                        self.evaluate_board(),
                        err_msg,
                    )
                    # Delay artificial para mejorar la visibilidad
                    time.sleep(0.5)
                    self.make_move(move.movement, move.from_coords, move.to_coords)

                    # Mostrar tablero resultante del movimiento
                    self._renderer.render(
                        self._current_board,
                        self._turn,
                        move.to_coords,
                        None,
                        self._move_history,
                        self.calculate_points(self._turn),
                        self.evaluate_board(),
                        err_msg,
                    )
                    time.sleep(0.5)

                if self._winner is not None:
                    self._renderer.render_end(self._winner, self._win_condition)
                    keyboard.unhook_all()
                    flush_stdin()
                    exit(0)

            # Mostrar tablero y loop de entrada
            if pvp or self._turn == player:
                self._renderer.render(
                    self._current_board,
                    self._turn,
                    self._cursor,
                    selected_coords,
                    self._move_history,
                    self.calculate_points(self._turn),
                    self.evaluate_board(),
                    err_msg,
                )

            input_loop = True

            while input_loop:
                event = keyboard.read_event()

                # El loop de entrada existe para ahorrar re-renders innecesarios debido a pulsar teclas que no
                # forman parte de las reconocidas y, principalmente, para quitar 1 re-render innecesario debido
                # a que todos los eventos de teclado están duplicados en 'pulsar' y 'soltar' la tecla.
                if event.event_type != keyboard.KEY_DOWN:
                    continue

                match [event.name, event.scan_code]:
                    case ["q", _]:
                        print("Saliendo del programa...")
                        keyboard.unhook_all()

                        # IMPORTANTE: Limpiar buffer de entrada antes de salir para evitar que
                        # todas las teclas pulsadas acaben en él y ejecuten comandos no deseados
                        flush_stdin()

                        sys.exit(0)
                    case ["enter" | "space", _]:  # Seleccionar / confirmar
                        if selected_coords is None:
                            # Comprobar si la pieza es seleccionable y asignar
                            err_msg = self.check_if_selectable(self._cursor)
                            selected_coords = self._cursor if not err_msg else None
                        else:
                            # Intentar mover
                            err_msg = self.make_move(
                                self._movement, selected_coords, self._cursor
                            )
                            if err_msg:
                                break

                            selected_coords = None
                    case ["u", _]:  # Deshacer
                        selected_coords = None
                        err_msg = self.undo_move()

                        # Deshacer jugada completa de la IA en cada de jugar contra ella.
                        if not pvp and err_msg is None:
                            temp_turn = self._turn.get_oposite()
                            while self._turn != temp_turn:
                                err_msg = self.undo_move()

                                if err_msg:
                                    err_msg = None
                                    break

                    case ["y", _]:  # Rehacer
                        selected_coords = None
                        err_msg = self.redo_move()

                    case ["x", _]:  # De-seleccionar
                        selected_coords = None
                    case ["w", _] | [_, 72]:  # Arr
                        self.move_cursor((-1, 0))
                    case ["a", _] | [_, 75]:  # Izq
                        self.move_cursor((0, -1))
                    case ["d", _] | [_, 77]:  # Der
                        self.move_cursor((0, 1))
                    case ["s", _] | [_, 80]:  # Abj
                        self.move_cursor((1, 0))
                    case _:
                        continue

                input_loop = False
