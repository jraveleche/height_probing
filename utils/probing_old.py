# Height probing
# Autor: Rodrigo Chang
# Fecha: 3 de noviembre de 2014
# Ultima fecha de modificacion: 5 de noviembre de 2014

# Programa para hacer probing en PCB utilizando G38.2 de GRBL
# y la comunicacion por puerto serial
# COM3 115200 8N1

import serial
import re
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt
from scipy import interpolate

# Datos para la cuadricula
DELTA_X = -10 # 1cm
DELTA_Y = 10
MILL_DEPTH = 0.115

# Patron de captura de alturas devuelto por GRBL
PROBE_PATTERN = '\[PRB:[-\d.]+,[-\d.]+,([-\d.]+)\]'

# Patron de reemplazo para archivos de código G
G1_PATTERN = 'G1 X([-0-9.]+) Y([-0-9.]+)'
G0Z_PATTERN = 'G0 X([-0-9.]+) Y([-0-9.]+)\nG1 Z([-0-9.]+)'

# Archivo de salida para alturas
OUTPUT_FILE = 'mapa_alturas.txt'

# Puerto serial para GRBL
SERIAL_PORT = 'COM3'
BAUDRATE = 115200

'''
    Devuelve la lista de puntos
    l -> unidades de DELTA_X a utilizar para generar la lista
    h -> unidades de DELTA_Y a utilizar para generar la lista
'''
def listaPuntos(l, h, dx=DELTA_X, dy=DELTA_Y):
    # Iterar sobre el eje Y y recorrer X en zigzag
    direccion = 0 # direccion inicial X en la direccion de DELTA_X
    puntos = [] # lista de puntos para devolver
    for j in range(h + 1):
        if (direccion == 0):
            for i in range(l + 1):
                puntos.append((i*dx, j*dy))
            direccion = 1
        else:
            for i in range(l, -1, -1):
                puntos.append((i*dx, j*dy))
            direccion = 0
    return puntos

'''
    Realiza el probing controlando el puerto serial especificado.
    Escribe en el archivo 'file' los puntos y devuelve un
    diccionario utilizando las tuplas de puntos (x,y) como llaves
    y las alturas como valores.

    CUIDADO: Esta funcion envia comandos para mover la maquina,
    asegurarse que el area de puntos esté despejada.

    puntos -> lista de tuplas => [(x0, y0), (x1, y1), ..., (xi, yj)]
    port, baudrate -> nombre y velocidad del puerto serial
    filename -> Archivo de salida para los puntos (x,y,z) separados por '\t'
    pattern -> Patron para detectar la lectura obtenida por GRBL para la funcion G38.2
'''
def realizarProbing(puntos, port=SERIAL_PORT, baudrate=BAUDRATE, pattern=PROBE_PATTERN, filename=OUTPUT_FILE):
    # Abrir el puerto serial
    print 'Iniciando conexion con puerto serial...'
    puerto = serial.Serial(port, baudrate, timeout=2)
    resp = puerto.readlines()
    for l in resp:
        print l,
    # Desbloquear
    puerto.write('$X\n')
    resp = puerto.readlines()
    for l in resp:
        print l,

    # Abrir un archivo y guardar los puntos
    probemap = {}
    f = open(filename, 'w')

    # Hacer probing para cada punto en la lista
    puerto.write('G90\n')
    puerto.write('G21\n')
    for punto in puntos:
        print 'Probando el punto (%-4.3f,%-4.3f)' % (punto[0], punto[1])
        puerto.write('G1 Z1.000 F95.00\n')
        puerto.write('G0 X%-4.3f Y%-4.3f\n' % (punto[0], punto[1]))
        puerto.write('G38.2 Z-20.000 F30.00\n')
        print 'Esperando lectura...',
        # Leer lineas hasta obtener el patron esperado
        while True:
            l = puerto.readline()
            result = re.match(pattern, l, re.IGNORECASE)
            # Si el patron coincide
            if result != None:
                depth = float(result.groups()[0])
                if punto == (0,0):
                    ref = depth

                # Ajuste para que el punto (0,0) sea z=0
                depth = depth - ref
                probemap[punto] = depth
                print depth
                f.write('%-4.3f\t%-4.3f\t%-4.3f\n' % (punto[0], punto[1], depth))
                break

    # Fin del probing
    f.close()
    print 'Fin del probing...'
    # Regresar al origen
    puerto.write('G0 Z1\n')
    puerto.write('G0 X0 Y0\n')
    # Cerrar el puerto serial
    puerto.close()

    # Devolver el mapa de alturas
    return probemap

'''
    Grafica el mapa de alturas y la funcion de interpolacion con 'cubic'
    Devuelve la funcion de interpolacion
'''
def interpolarMapa(probeMap):
    # Obtener la lista de valores x,y,z
    xm = []
    ym = []
    zm = []
    for p in probeMap.keys():
        xm.append(p[0])
        ym.append(p[1])
        zm.append(probeMap[p])

    print xm
    print ym
    print zm
    # Interpolar la funcion
    f = interpolate.interp2d(xm, ym, zm, kind='cubic')

    fig = plt.figure(1)
    ax = Axes3D(fig)
    # Graficar los puntos
    ax.plot(xm, ym, zm, 'go', linewidth=2, markersize=11)
    # Graficar la version interpolada
    xnew = np.arange(min(xm), max(xm), 0.1)
    ynew = np.arange(min(ym), max(ym), 0.1)
    znew = f(xnew, ynew)

    xx, yy = np.meshgrid(xnew, ynew)
    ax.plot_surface(xx, yy, znew, cmap=cm.coolwarm, rstride=20, cstride=20)

    # Muestra la grafica
    plt.show()
    #plt.savefig('mapaAlturas.pdf')
    # Devuelve el objeto de funcion
    return f


'''
    Modifica el archivo de código G con la funcion especificada
    filename -> str: La ruta hacia el archivo a modificar 
    f -> Es el objeto de funcion devuelto por interp2d para modificar los puntos X y Y
    prof_fresado -> profunidad de fresado a partir de z=0 (valor positivo)
'''
def modificarArchivo(filename, f, prof_fresado):
    def opt_name(s, prefix):
        assert '.' in s
        i = -1
        while s[i] != '.':
            i = i - 1
        old_ext = s[i:]
        return s[-len(s): i] + prefix + old_ext
	
    def f_repl_g1(f):
        def repl_g1(match):
            x = float(match.group(1))
            y = float(match.group(2))
            z = f(x, y)[0] - prof_fresado
            return ('G1 X%-4.4f Y%-4.4f Z%-4.3f' % (x, y, z))
        return repl_g1

    def f_repl_g0z(f):
        def repl_g0z(match):
            x = float(match.group(1))
            y = float(match.group(2))
            z = f(x, y)[0] - prof_fresado
            return ('G0 X%-4.4f Y%-4.4f\nG1 Z%-4.3f' % (x, y, z))
        return repl_g0z
    
    gcode = open(filename, 'r').read()
    # Limpiar el codigo G de espacios dobles o mas
    gcode = re.sub('[ ]{2,}', ' ', gcode)
    gcode = re.sub(' \n', '\n', gcode)

    # Reemplazar las ocurrencias de G1 X# Y# enviando la funcion de superficie
    gcode = re.sub(G1_PATTERN, f_repl_g1(f), gcode)
    # Reemplazar las ocurrencias de G0 X# Y#\nG1 Z# enviando la funcion de superficie
    gcode = re.sub(G0Z_PATTERN, f_repl_g0z(f), gcode)

    # Guardar el archivo modificado
    wf = open(opt_name(filename, '.LEV'), 'w')
    wf.write(gcode)
    wf.close()
    

'''
    Programa principal
'''
'''
print '=- Programa de Probing -='
length_x = int(raw_input('Ingrese largo en X [mm]: '))
length_y = int(raw_input('Ingrese alto en Y [mm]: '))

# Obtener la lista de puntos
l = abs(length_x / DELTA_X)
h = abs(length_y / DELTA_Y)
puntos = listaPuntos(l, h)
print puntos

# Obtener las alturas de los puntos
probemap = realizarProbing(puntos)
print 'Mapa de alturas...', probemap
'''
#probemap = {(0, 0): 0.0, (-10, 10): -0.08599999999999985, (-10, 0): -0.02299999999999991, (0, 10): -0.04799999999999993}
probemap = {(-10, 20): -0.05700000000000001, (0, 0): 0.0, (-20, 0): 0.002999999999999999, (0, 20): -0.012000000000000002, (-30, 20): -0.13899999999999998, (-10, 30): -0.095, (-30, 10): -0.082, (-30, 0): -0.012000000000000002, (-20, 20): -0.101, (0, 10): 0.019, (0, 30): -0.031, (-30, 30): -0.178, (-20, 10): -0.063, (-10, 10): -0.025, (-10, 0): 0.026, (-20, 30): -0.146}
# Graficar el mapa y obtener la funcion de interpolacion
f = interpolarMapa(probemap)

modificarArchivo('cubo_test.bot.etch.OPT.nc', f, MILL_DEPTH)
