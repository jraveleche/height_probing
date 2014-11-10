# -*- coding: utf-8 -*-
'''
Genera una lista de listas con los puntos en los que se quiere
hacer la prueba de altura. 
    Recibe: Tamaño de la placa en X y Y, largo para cuadricula
    Devuelve: Lista de listas con formato [[x,y]]
'''
def generarPuntos(tam_x, tam_y, dxy):
    assert (tam_x > dxy) and (tam_y > dxy)
    x = 0
    y = 0
    veces_x = int(tam_x / dxy)
    veces_y = int(tam_y / dxy)
    puntos = []

    for i in range(veces_x):
        x = i*dxy
        y = 0
        for j in range(veces_y):
            y = j*dxy
            puntoSimple = [x, y]
            print puntoSimple
            puntos.append(puntoSimple)

    return puntos
