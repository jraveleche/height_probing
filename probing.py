'''
    Height probing
    Autor: Rodrigo Chang
    Fecha: 3 de noviembre de 2014
    Ultima fecha de modificacion: 9 de noviembre de 2014

    Programa para hacer probing en PCB utilizando G38.2 de GRBL
    y la comunicacion por puerto serial
    COM3 115200 8N1
'''

import serial
import re
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from scipy import interpolate

# Datos por defecto para la cuadricula
DELTA_X = -10 # 1cm
DELTA_Y = 10
MILL_DEPTH = 0.100

# Patrón de captura de alturas devuelto por GRBL
PROBE_PATTERN = '\[PRB:[-\d.]+,[-\d.]+,([-\d.]+)\]'

# Patrón de reemplazo para archivos de código G
# Encuentra los códigos G1 que van hacia un punto X, Y
G1_PATTERN = 'G1 X([-0-9.]+) Y([-0-9.]+)'
# Encuentra los códigos G0 X# Y# y luego G1 Z# (rápido hacia coord. (X,Y) y baja la herramienta)
G0Z_PATTERN = 'G0 X([-0-9.]+) Y([-0-9.]+)\nG1 Z([-0-9.]+)'

# Archivo de salida por defecto para puntos X, Y, Z del mapa de alturas.
OUTPUT_FILE = 'mapa_alturas.txt'

# Puerto serial para GRBL
SERIAL_PORT = 'COM3'
BAUDRATE = 115200


'''
    Devuelve la lista de puntos utilizando una trayectoria en zig-zag
    l (int > 0) -> unidades de DELTA_X a utilizar para generar la lista
    h (int > 0) -> unidades de DELTA_Y a utilizar para generar la lista
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
    asegurarse que el area de puntos esté despejada. Mover la máquina de forma
    manual al punto que servirá como (0,0) y a cualquier altura.

    puntos -> lista de tuplas, e.g. [(x0, y0), (x1, y1), ..., (xi, yj)]
    port, baudrate -> nombre y velocidad del puerto serial
    filename -> Archivo de salida para escribir los puntos (x,y,z) separados por '\t'
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
            # Lee la linea recibida por GRBL
            l = puerto.readline()
            # Ver si el patron coincide con el formato dado por G38.2
            result = re.match(pattern, l, re.IGNORECASE)
            # Si el patron coincide
            if result != None:
                # Leer la profundidad recibida
                depth = float(result.groups()[0])
                # Si el punto es (0,0) utilizarlo como referencia z=0
                if punto == (0,0):
                    ref = depth

                # Obtener cada profundidad a partir de la referencia
                depth = depth - ref
                # Guardar la altura del punto en el diccionario e imprimirla en pantalla y al archivo
                probemap[punto] = depth
                print depth
                f.write('%-4.3f\t%-4.3f\t%-4.3f\n' % (punto[0], punto[1], depth))
                # Sale del ciclo infinito
                break

    # Fin del probing, cerrar el archivo
    f.close()
    print 'Fin del probing...'
    # Regresar al origen
    puerto.write('G1 Z1.000 F95.00\n')
    puerto.write('G0 X0 Y0\n')
    # Cerrar el puerto serial
    puerto.close()

    # Devolver el mapa de alturas
    return probemap


'''
    Recibe el mapa de alturas y devuelve las listas X, Y, Z correspondientes.
'''
def probeMapToList(probeMap):
    xm = []
    ym = []
    zm = []
    for p in probeMap.keys():
        xm.append(p[0])
        ym.append(p[1])
        zm.append(probeMap[p])

    return xm, ym, zm


'''
    Recibe el diccionario de puntos y alturas y grafica los puntos en una vista
    tridimensional, si recibe una función grafica tambien la superficie de interpolación.
'''
def graficarMapa(probeMap, function=None):
    # Obtener la lista de valores x,y,z
    xm, ym, zm = probeMapToList(probeMap)

    # Crea la ventana
    fig = plt.figure(1)
    ax = Axes3D(fig)
    # Graficar los puntos en 3D
    ax.plot(xm, ym, zm, 'go', linewidth=2, markersize=11)
    
    # Si se especifica la función, graficar la version interpolada
    if (function != None):
        xnew = np.arange(min(xm), max(xm), 0.1)
        ynew = np.arange(min(ym), max(ym), 0.1)
        znew = function(xnew, ynew)

        xx, yy = np.meshgrid(xnew, ynew)
        ax.plot_surface(xx, yy, znew, cmap=cm.coolwarm, rstride=20, cstride=20)

    # Muestra la grafica
    plt.show()
    #plt.savefig('mapaAlturas.pdf')


'''
    Obtiene la funcion de interpolacion utilizando TODOS los puntos de probeMap
    Utiliza la funcion interpolate.interp2d con 'cubic'
    
    Devuelve la funcion de interpolacion
'''
def interpolarMapa(probeMap):
    # Obtener la lista de valores x,y,z
    xm, ym, zm = probeMapToList(probeMap)
    # Interpolar la funcion
    f = interpolate.interp2d(xm, ym, zm, kind='cubic')
    # Devuelve el objeto de funcion
    return f


'''
    Modifica el archivo de código G con la funcion especificada
    filename -> str: La ruta hacia el archivo a modificar 
    f -> Es el objeto de funcion devuelto por interp2d para modificar los puntos X y Y
    prof_fresado -> profunidad de fresado a partir de z=0 (valor positivo)
'''
def modificarArchivo(filename, f, prof_fresado):
    '''
        Funcion que recibe el nombre original del archivo y el prefijo a agregar.
        Devuelve el nuevo nombre del archivo
    '''
    def opt_name(s, prefix):
        assert '.' in s
        i = -1
        while s[i] != '.':
            i = i - 1
        old_ext = s[i:]
        return s[-len(s): i] + prefix + old_ext

    '''
        Reemplaza las ocurrencias utilizando el patrón G1_PATTERN, para cada punto (x,y)
        obtiene la profundidad z = f(x,y) y la agrega en código G
    '''
    def f_repl_g1(f):
        def repl_g1(match):
            x = float(match.group(1))
            y = float(match.group(2))
            z = f(x, y)[0] - prof_fresado
            return ('G1 X%-4.4f Y%-4.4f Z%-4.3f' % (x, y, z))
        return repl_g1

    '''
        Reemplaza las ocurrencias utilizando el patrón G0Z_PATTERN, para cada punto (x,y)
        obtiene la profundidad z = f(x,y) y la agrega en código G
    '''
    def f_repl_g0z(f):
        def repl_g0z(match):
            x = float(match.group(1))
            y = float(match.group(2))
            z = f(x, y)[0] - prof_fresado
            return ('G0 X%-4.4f Y%-4.4f\nG1 Z%-4.3f' % (x, y, z))
        return repl_g0z

    # Abre el archivo especificado y obtiene el código G
    gcode = open(filename, 'r').read()
    # Limpiar el codigo G de espacios dobles o más
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
    Imprime las instrucciones para iniciar el programa correctamente
    desde la linea de comandos
'''
def imprimeInstrucciones():
    #print '=- Programa de Probing -=\n'
    print 'Utilizacion correcta:'
    print '\tpython probing.py -f <archivo> <x> <y> <dx> <dy> <prof_z>'
    print '\tpython probing.py -f <archivo> <x> <y>'
    print '\tpython probing.py -p <x> <y> <dx> <dy>'
    print '\tpython probing.py -p <x> <y>\n'
    print 'x,y\t:\tDimensiones del area a probar'
    print 'dx, dy\t:\tCambios en ambos ejes, por defecto dx=-10mm, dy=10mm'
    print 'prof_z\t:\tProfundidad de fresado a partir de la superficie de contacto'


'''
    Realiza la rutina general de probing utilizando el tamaño de la placa.
    Opcionalmente modifica el archivo de código G especificado.
'''
def rutinaGeneral(length_x, length_y, dx = DELTA_X, dy = DELTA_Y, prof_z = MILL_DEPTH, filename=None):
    # Obtener la lista de puntos
    print 'Generando la lista de puntos...'
    l = abs(length_x / dx)
    h = abs(length_y / dy)
    puntos = listaPuntos(l, h, dx, dy)
    print 'La lista de puntos es: ', puntos

    # Obtener las alturas de los puntos
    print 'Realizando el mapa de alturas...'
    #probemap = realizarProbing(puntos)
    probemap = {(-10, 20): -0.057, (0, 0): 0.0, (-20, 0): 0.003, (0, 20): -0.012, (-30, 20): -0.139, (-10, 30): -0.095, (-30, 10): -0.082, (-30, 0): -0.012, (-20, 20): -0.101, (0, 10): 0.019, (0, 30): -0.031, (-30, 30): -0.178, (-20, 10): -0.063, (-10, 10): -0.025, (-10, 0): 0.026, (-20, 30): -0.146}
    print 'Se ha terminado el mapa, generando el modelo...'

    # Obtener la funcion de interpolacion
    f = interpolarMapa(probemap)
    # Graficar el mapa de alturas
    graficarMapa(probemap, function=f)

    # Si se especificó, modificar el archivo original con el mapa obtenido.
    if (filename != None):
        print 'Modificando el archivo original...'
        modificarArchivo(filename, f, prof_z)


'''
    Programa principal
'''
print '\n=- Programa de Probing -=\n'
args = len(sys.argv)

# Si sólo está el nombre del programa, pedir el tamaño de la placa
if (args == 1):
    length_x = int(raw_input('Ingrese largo en X [mm]: '))
    length_y = int(raw_input('Ingrese alto en Y [mm]: '))
    # Realizar procedimiento general
    rutinaGeneral(length_x, length_y)

# Si hay mas argumentos, revisar si es probing o modificacion de archivo
else:
    opcion = sys.argv[1]
    print 'Argumentos: ', args

    # Si la opción es solamente mapeo de alturas
    if (opcion == '-p') and (args in [4,6]):
        # Obtener los argumentos
        length_x = int(sys.argv[2])
        length_y = int(sys.argv[3])
        # Si se especifican todos los argumentos
        if (args == 6):
            delta_x = int(sys.argv[4])
            delta_y = int(sys.argv[5])
            # Realizar el procedimiento general
            rutinaGeneral(length_x, length_y, delta_x, delta_y)
        # Sino, tomar los valores especificados por defecto
        else:
            # Realizar el procedimiento general
            rutinaGeneral(length_x, length_y)
        
    # Si la opción es modificación de archivo
    elif (opcion == '-f') and (args in [5,8]):
        # Obtener los argumentos
        filename = sys.argv[2]
        
        # Revisar si el archivo existe
        if (os.path.isfile(filename)):
            length_x = int(sys.argv[3])
            length_y = int(sys.argv[4])
            # Si se especifican todos los argumentos
            if (args == 8):
                dx = int(sys.argv[5])
                dy = int(sys.argv[6])
                prof_z = float(sys.argv[7])
                # Realizar la rutina general especificando todos los parametros
                rutinaGeneral(length_x, length_y, dx, dy, prof_z, filename)
            # Sino, tomar los valores especificados por defecto
            else:
                # Realizar la rutina general con valores por defecto
                rutinaGeneral(length_x, length_y, filename=filename)
            
        # Si no existe el archivo especificado
        else:
            print 'El archivo especificado no existe...'
            
    # Si la opción indicada es incorrecta
    else:
        imprimeInstrucciones()
