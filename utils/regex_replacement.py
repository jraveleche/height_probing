import re

G1_PATTERN = 'G1 X([-0-9.]+) Y([-0-9.]+)'
G0Z_PATTERN = 'G0 X([-0-9.]+) Y([-0-9.]+)\nG1 Z([-0-9.]+)'

def g(x,y):
    return -(x*2 + y**2)/10

def f_repl_g1(f):
    def repl_g1_in(match):
        x = float(match.group(1))
        y = float(match.group(2))
        z = f(x, y)
        return ('G1 X%-4.4f Y%-4.4f Z%-4.3f' % (x, y, z))
    return repl_g1_in

def repl_g1(matchobj):
    x = float(matchobj.group(1))
    y = float(matchobj.group(2))
    z = -(x**2 + y**2)/10
    #return matchobj.group(0) + (' Z%-4.3f' % z)
    return ('G1 X%-4.4f Y%-4.4f Z%-4.3f' % (x, y, z))

def repl_g0z(matchobj):
    x = float(matchobj.group(1))
    y = float(matchobj.group(2))
    z = -(x**2 + y**2)/10
    return ('G0 X%-4.4f Y%-4.4f\nG1 Z%-4.3f' % (x, y, z))

gcode_ex = 'G90\nG0 Z3.0000\nM3\nG4 P4.0000\nG0 X-4.1793 Y12.6670\nG1 Z-0.1150 F70.00\nG1 X-6.6157 Y12.6670 F95.00\nG1 X-6.8143 Y12.6985\nG1 X-7.0055 Y12.7606'

new_g1 = re.sub(G1_PATTERN, f_repl_g1(g), gcode_ex)
print 'Reemplazo de codigos G1:\n'
print new_g1

new_g0 = re.sub(G1_PATTERN, repl_g1, gcode_ex)
print '\nReemplazo de codigos G0XY Z:\n'
print new_g0
