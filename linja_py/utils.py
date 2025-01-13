import os
import sys
from dataclasses import dataclass
from enum import Enum

if os.name == "nt":
    import msvcrt

# Type aliases
ErrorMsg = str


class Turn(Enum):
    """
    Clase que representa los posibles turnos en el juego del Linja.

    La clase en un enumerado y contiene solo los colores ROJO y NEGRO, además
    de una función para obtener el color opuesto.
    """

    RED = 1
    BLACK = 2

    def get_oposite(self):
        """
        Devuelve el color opuesto al que invoca esta función.

        :return: Color opuesto: RED -> BLACK | BLACK -> RED
        """
        if self == self.RED:
            return self.BLACK
        else:
            return self.RED


@dataclass(frozen=True)
class Move:
    """
    Clase que representa un movimiento del juego.
    """
    from_coords: tuple[int, int]
    to_coords: tuple[int, int]
    movement: int
    turn: Turn


# Funciones de ayuda generales
def check_coords(coords: tuple[int, int]) -> bool:
    if len(coords) != 2:
        raise ValueError("Coordinates should be of length 2.\n"
                         f"Expected: (row, col) | Got: 'coords' = {coords}")
    elif type(coords[0]) != int or type(coords[1]) != int:
        raise TypeError("Coordinates should be integers.\n"
                        f"Expected: (int, int) | Got: 'coords' = {coords}")
    else:
        return True


def side_by_side_str(strings: list[str], space: int = 4) -> str:
    out = []

    while any(strings):
        line = []

        for i, string in enumerate(strings):
            to_nl = string.find("\n")

            line.append(string[:to_nl])
            strings[i] = string[to_nl + 1:]

        out.append((" " * space).join(line))

    return "\n".join(out)


def flush_stdin():
    """
    Función vital al programa, permite limpiar el buffer de caracteres que guarda
    'stdin'.
    \n
    Es necesario debido al loop de entrada que se usa. Todos los
    caracteres pulsados durante una ejecución se acumulan en el buffer de entrada
    y acaban suponiendo un problema tras salir de este, daod que todos estos
    caracteres se vuelven a reproducir en la terminal, llevando a comportamientos
    no deseados.
    """
    sys.stdin.flush()

    #  En caso de usar windows aprovechar el método que ofrece el so
    if os.name == "nt":
        while msvcrt.kbhit():
            msvcrt.getch()
