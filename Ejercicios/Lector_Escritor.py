import threading


def acumula5():
    global total
    contador = 0
    hilo_actual = threading.current_thread().getName()
    num_intentos = 0
    while contador < 20:
        lo_consegui = bloquea.acquire(blocking=False)
        try:
            if lo_consegui:
                contador = contador + 1
                total = total + 5
                print('Bloqueado por', hilo_actual, contador)
                print('Total ', total)
            else:
                num_intentos += 1
                print('Número de intentos de bloqueo',
                      num_intentos,
                      'hilo',
                      hilo_actual,
                      bloquea.locked())
                print('Hacer otro trabajo')

        finally:
            if lo_consegui:
                print('Liberado por', hilo_actual)
                bloquea.release()


total = 0
bloquea = threading.Lock()
hilo1 = threading.Thread(name='"Escritor"', target=acumula5)
hilo2 = threading.Thread(name='"Lector"', target=acumula5)
hilo1.start()
hilo2.start()