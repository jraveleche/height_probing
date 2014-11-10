# -*- coding: utf-8 -*-
'''
    height_probing_test.py
    Rodrigo Chang 09/07/2014

    Programa para realizar un mapeo de las alturas en una placa.

    Se dan:
    * el tamaño de la placa (mm)
    * la separación de la cuadrícula para medir (mm)
    * la distancia a avanzar en el eje Z (mm)

    El programa envia el codigo G al puerto serial especificado para mover
    la maquina y sensa en un GPIO si se ha cerrado el circuito entre la
    punta de la herramienta y la superficie de la placa de cobre.

    Las coordenadas en X se generan negativas. El primer punto siempre es (0,0,0)
'''

# Definiciones para puerto serial
PUERTO_SERIAL = '/dev/ttyACM0'
BAUDRATE = 9600

# Definicion del tamaño de la placa y avance
SIZE_X = 60.0
SIZE_Y = 50.0
DELTA_XY = 25.0
DELTA_Z = 0.1

'''
Imprime punto con formato
'''
def imprimirPunto(x,y):
    print x, '\t', y

'''
Cambia el formato de un numero
'''
def imprimirNumero(x):
    #return '{:10.4f}'.format(x)
    print '%10.3f' % x

'''
Genera una lista de listas con los puntos en los que se quiere
hacer la prueba de altura. Los puntos se generan con una trayectoria en S
para ahorrar tiempo de viaje de la maquina
    Recibe: Tamaño de la placa en X y Y, largo para cuadricula
    Devuelve: Lista de listas con formato [[x,y]]
'''
def generarPuntos(tam_x, tam_y, dxy):
    assert (tam_x > dxy) and (tam_y > dxy)
    # Estados para recorrer la cuadricula
    X_ASCENDENTE = 0
    X_DESCENDENTE = 1

    x = 0.0
    y = 0.0
    veces_y = int(tam_y / dxy)
    listaPuntos = []

    # Estado inicial
    modo = X_ASCENDENTE

    # Para cada fila en Y
    for j in range(veces_y + 1):
        y = j * dxy
        if (modo == X_ASCENDENTE):
            while (x <= tam_x):
                listaPuntos.append([x,y])
                imprimirPunto(x,y)
                x += dxy
            x -= dxy
            modo = X_DESCENDENTE
        else:
            while (x >= 0):
                listaPuntos.append([x,y])
                imprimirPunto(x,y)
                x -= dxy
            x = 0.0
            modo = X_ASCENDENTE

    return listaPuntos

generarPuntos(SIZE_X, SIZE_Y, DELTA_XY)
