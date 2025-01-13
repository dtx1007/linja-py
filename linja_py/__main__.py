import keyboard
from .menu_renderer import MenuRenderer


def main():
    """
    Función principal del programa.
    Inicializa el menu principal del juego.
    """

    # Setup
    menu = MenuRenderer()
    op = menu.options[0].name
    op_index = 0
    op_len = len(menu.options)

    # Input loop
    while True:
        menu.render(op)

        input_loop = True

        # El doble bucle ayuda a ignorar las entradas no deseadas y
        # ahorrar re-renders debido a pulsar teclas que no hacen nada.
        while input_loop:
            event = keyboard.read_event()

            # Ignorar el 'release' de la tecla
            if event.event_type != keyboard.KEY_DOWN:
                continue

            match [event.name, event.scan_code]:
                case ["enter", _]:  # Seleccionar
                    menu.process_selection(op)
                    op_len = len(menu.options)
                case ["w", _] | [_, 72]:  # Arr
                    op_index = (op_index - 1) % op_len
                    op = menu.options[op_index].name
                case ["s", _] | [_, 80]:  # Abj
                    op_index = (op_index + 1) % op_len
                    op = menu.options[op_index].name
                case _:
                    continue

            input_loop = False


if __name__ == "__main__":
    main()
