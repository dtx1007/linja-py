# Ayuda Linja

Guía de ayuda para el juego del Linja.

## 📋 Índice

- ♟ [Tablero](#-tablero)
- 🎯 [Objetivo](#-objetivo)
- 📙 [Reglas](#-reglas)

## ♟ Tablero

Diagrama del tablero del Linja.

```txt
        0   1   2   3   4   5
      |---|---|---|---|---|---|
    0 | o | o | o | o | o | o |
      |---|---|---|---|---|---|
    1 | o |   |   |   |   | x |
      |---|---|---|---|---|---|
    2 | o |   |   |   |   | x |
      |---|---|---|---|---|---|
    3 | o |   |   |   |   | x |
      |---|---|---|---|---|---|
    4 | o |   |   |   |   | x |
      |---|---|---|---|---|---|
    5 | o |   |   |   |   | x |
      |---|---|---|---|---|---|
    6 | o |   |   |   |   | x |
      |---|---|---|---|---|---|
    7 | x | x | x | x | x | x |
      |---|---|---|---|---|---|
```

El juego consta de dos colores:

- 'o' Rojas
- 'x' Negras

## 🎯 Objetivo

El Linja es un juego de dos jugadores que consta en obtener una mayor puntuación que tu adversario realizando movimientos legales de las piezas.

Cada color **solo obtiene puntos para aquellas piezas pasadas la mitad del tablero**. Por ello, el objetivo principal del juego es llegar con las piezas del jugador lo más cerca posible del borde opuesto a donde empiezan las piezas de dicho jugador.

La partida acaba cuando las piezas de ambos jugadores quedan completamente **separadas**.

> ❗**Importante:** Por **separadas** se entiende que, la fichas más cercana de cada jugador a su borde de partida no tiene ninguna ficha del color opuesto por delante de ella.

Ejemplo de tablero finalizado:

```txt
 Fin de partida                            Puntos
                |---|---|---|---|---|---|        
           *    | x | x | x | x | x | x |    +5  *
   Piezas  *    |---|---|---|---|---|---|        *
   negras  *    | x |   | x | x | x |   |    +3  * Puntos
           *    |---|---|---|---|---|---|        *  para
           *    | x |   |   | x |   |   |    +2  * negras
         > ---- |---|---|---|---|---|---|        *
           #    | o |   |   |   |   |   |    +1  *
           #    |---|---|---|---|---|---| -------- <
           #    |   |   |   |   |   |   |    +1  #
   Piezas  #    |---|---|---|---|---|---|        #
    rojas  #    | o |   |   |   |   | o |    +2  # Puntos
           #    |---|---|---|---|---|---|        #  para
           #    |   | o |   |   | o | o |    +3  #  rojas 
           #    |---|---|---|---|---|---|        #
           #    | o | o | o | o | o | o |    +5  #
                |---|---|---|---|---|---|
```

Como se puede apreciar, la partida está acabada, las piezas están perfectamente separadas y forman dos grupos homogéneos. En este punto se contarían las piezas de cada uno de los colores y se averiguaría quién es el ganador en función de quién tiene un número mayor de puntos.

> ❗**Importante:** La pieza roja 'o' de la 3a fila, 1a columna **no** contaría para los puntos de las rojas, dado que no ha pasado el centro del tablero.

## 📙 Reglas

El juego se compone principalmente de las siguientes reglas.

Cada movimiento es en sí, es un par de movimientos. El primero consta en mover una pieza una fila hacia arriba. El segundo, dependerá del primero, en función del número de piezas que hubiera en la fila a la que se ha movido la pieza del primer movimiento, ese será el número de filas a mover en el segundo movimiento.

> ❗**Importante:** Los movimientos siempre **han de ser completos**, si se pide mover '4' filas, se ha de mover esa cantidad con una sola ficha, no se puede repartir el movimiento entre varias piezas. Aclarar que, se pueden hacer movimientos con fichas distintas pero, **siempre** la cantidad exacta.

Ejemplo de un par de movimientos:

```txt
            |---------------------- Primer movimiento (1 fila siempre)
            |
            v 
      |---|---|---|---|---|---|
    0 |   | o |   | o |   |   |
      |---| v |---|---|---|---|
    1 |   | o |   |   | o | x | < En el primer movimiento, la ficha ha
      |---|---|---|---|---|---|   acabado en un fila en la que había 2
    2 |   |   |   |   |   |   |   fichas, el siguiente movimiento será
      |---|---|---|---|---|---|   de 2 filas.
      
                    |-------------- Segundo movimiento (longitud variable)
                    |
                    v
      |---|---|---|---|---|---|
    0 |   |   |   | o |   |   | < Se pueden mover piezas distintas en
      |---|---|---| v |---|---|   cada movimiento pero, siempre se debe
    1 |   | o |   |   | o | x |   mover la cantidad exacta del movimiento,
      |---|---|---| v |---|---|   en este caso, 2 filas.
    2 |   |   |   | o |   |   |
      |---|---|---|---|---|---|
```

Hay dos excepciones a los movimientos:

- Si en su primer movimiento, un jugador mueve a una fila sin fichas, este **pierde su segundo movimiento** (sería un movimiento de 0 filas).

```txt
            |---------------------- Primer movimiento (1 fila siempre)
            |
            v 
      |---|---|---|---|---|---|
    0 |   | o |   | o |   |   |
      |---| v |---|---|---|---|
    1 |   | o |   |   |   |   | < En esta fila no hay piezas, por ende
      |---|---|---|---|---|---|   el segundo movimiento del jugador será
    2 |   |   |   |   |   |   |   de 0 filas, es decir, pierde este
      |---|---|---|---|---|---|   movimiento.
```

- Si en su segundo movimiento un jugador mueve a una fila sin fichas, este **gana un turno adicional** completo, es decir, vuelve a hacer su primer y segundo movimiento una vez más. Esto solo puede ocurrir una vez.

```txt
            |---------------------- Primer movimiento (1 fila siempre)
            |
            v 
      |---|---|---|---|---|---|
    0 |   | o |   | o |   |   |
      |---| v |---|---|---|---|
    1 |   | o |   |   |   | x | < En el primer movimiento, la ficha ha
      |---|---|---|---|---|---|   acabado en un fila en la que había 2
    2 |   |   |   |   |   |   |   fichas, el siguiente movimiento será
      |---|---|---|---|---|---|   de 2 filas.
      
                    |-------------- Segundo movimiento (longitud variable)
                    |
                    v
      |---|---|---|---|---|---|
    0 |   |   |   | o |   |   |
      |---|---|---| v |---|---|
    1 |   | o |   |   | o | x |
      |---|---|---| v |---|---|
    2 |   |   |   | o |   |   | < En esta fila no hay piezas, pero,
      |---|---|---|---|---|---|   como es el segundo movimiento esto
                                  nos otorga otro turno completo.

            |---------------------- Tercer movimiento (igual que 1er; 1 fila)
            |
            v       
      |---|---|---|---|---|---|
    0 |   |   |   |   |   |   |
      |---|---|---|---|---|---|
    1 |   | o |   |   | o | x |
      |---| v |---|---|---|---|
    2 |   | o |   | o |   |   | < Hay 1 pieza en la fila, por lo cual,
      |---|---|---|---|---|---|   el siguiente movimiento será de 1
                                  fila.

            |---------------------- Cuarto movimiento (igual que 2do; variable)
            |
            v       
      |---|---|---|---|---|---|
    0 |   |   |   |   |   |   |
      |---|---|---|---|---|---|
    1 |   |   |   |   | o | x |
      |---|---|---|---|---|---|
    2 |   | o |   | o |   |   | 
      |---| v |---|---|---|---|
    3 |   | o |   |   |   |   | < Se mueve a una fila vacía, normalmente,
      |---|---|---|---|---|---|   esto nos otorgaría otro movimiento pero,
                                  al haber obtenido ya nuestro turno extra
                                  anteriormente, se pasa al turno del oponente.

```

El máximo número de fichas en una fila intermedia es de 6, mientras que, en los extremos este es ilimitado. No es posible mover a una fila ocupada, a menos que sean las de los extremos, el jugador debe saltar esa fila para seguir moviendo.

```txt
      |---|---|---|---|---|---|
   0  | x | x | x | x | x | x | [x] x 7 < Al ser un extremo del tablero
      |---|---|---|---|---|---|           puede haber un número ilimitado
      |   |   |   |   |   |   |           de piezas.
      |---|---|---|---|---|---|
   2  | o | o | o | o | o | o | < Al no ser un extremo del tablero solo
      |---|---|---|---|---|---|   puede haber un máximo de 6 piezas.
      
      |---|---|---|---|---|---|
      |   |   | x |   |   |   | < Una pieza no puede moverse a una fila
      |---|---| v |---|---|---|   completa.
      | o | o | o | o | o | o |
      |---|---|---|---|---|---|
      
      |---|---|---|---|---|---|
      |   |   | x |   |   |   | < Alternativamente, si que se puede
      |---|---| v |---|---|---|   saltar por encima de una fila compelta.
      | o | o | o | o | o | o |   Para ello se necesita mover al menos 2
      |---|---| v |---|---|---|   filas.
      |   |   | x |   |   |   |
      |---|---|---|---|---|---| 
```

La partida termina cuando los dos tipos de piezas (rojas y negras) quedan completamente separadas una de otra, es decir, cada una forma un grupo homogéneo en las filas en las que está ([ejemplo](#-objetivo)).

---

La ayuda está disponible también en formato Markdown dentro de los ficheros del programa `./markdown/help.md`.
