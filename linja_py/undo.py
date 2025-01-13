from typing import TypeVar, Generic


T = TypeVar("T")


class Undo(Generic[T]):
    """
    Pila genérica que permite implementar un mecanismo para deshacer y rehacer elementos.
    Está pensada desde el punto de vista de que cada elemento de la pila sería un estado
    que interesa almacenar o recordar.

    La pila recuerda los elementos introducidos en ella, permitiendo recuperarlos de una
    forma cómoda (undo), además, se mantiene constancia de los elementos extraídos para
    poder volver a introducirlos (rehacer) en caso de que se necesiten.
    """

    _size: int
    _current_item: T
    _undo_stack: list[T]
    _redo_stack: list[T]

    def __init__(self):
        self._size = 0
        self._undo_stack = []
        self._redo_stack = []

    def __len__(self):
        return self._size

    def add_item(self, new_item: T, current_item: T):
        """
        Añade elementos 'viejos' a la pila. El concepto de 'viejos' se refiere
        a elementos que puede que sea de interés recuperar en un futuro.

        :param new_item: Elemento 'viejo' que se desea recordar.
        :param current_item: Elemento actual que sustituye al 'viejo'.
        """
        self._current_item = current_item
        self._undo_stack.append(new_item)
        self._clear_redo()
        self._size += 1

    def peek(self) -> T | None:
        """
        Devuelve el último elemento añadido a la pila, pero, no lo descarta de esta.

        :return: Último elemento añadido; None en caso de que no haya elementos en la pila.
        """
        if self._size == 0:
            return None

        return self._undo_stack[-1]

    def undo(self) -> T | None:
        """
        Recupera el último elemento introducido en la pila. No se descarta el elemento actual,
        sino que, se recuerda en caso de querer rehacer este.

        :return: Último elemento añadido; None en caso de que no haya elementos en la pila
        """
        if len(self._undo_stack) == 0:
            return None

        last_item = self._undo_stack.pop()

        self._redo_stack.append(self._current_item)
        self._current_item = last_item
        self._size -= 1

        return last_item

    def redo(self) -> T | None:
        """
        Recupera el elemento más reciente descartado debido a usar 'undo()'.

        :return: Elemento más recientemente descartado debido a usar 'undo()'.
                 En caso de que la última operación sobre la pila fuera añadir
                 un elemento, esta función devolverá None dado que, si se ha
                 insertado un nuevo elemento se entiende que los viejos ya no
                 serán válidos.
        """
        if len(self._redo_stack) == 0:
            return None

        last_item = self._redo_stack.pop()
        self._undo_stack.append(self._current_item)
        self._current_item = last_item
        self._size += 1

        return last_item

    def redo_length(self):
        """
        Devuelve la cantidad de elementos que contiene la pila de rehacer.
        Es decir, la cantidad de elementos que se han recordado debido a usar
        'undo()'.

        :return:
        """
        return len(self._redo_stack)

    def _clear_redo(self):
        self._redo_stack.clear()
