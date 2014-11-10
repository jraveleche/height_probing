# Prueba de GPIO con pull-up y POLLING al pin

import RPi.GPIO as GPIO
import time

PIN_TEST = 7

# Configurar la numeracion
GPIO.setmode(GPIO.BOARD)
# Configurar la entrada
GPIO.setup(PIN_TEST, GPIO.IN, pull_up_down = GPIO.PUD_UP)

# Prueba con polling al pin cada 100ms
try:
	while True:
		print GPIO.input(PIN_TEST)
		time.sleep(0.1)
except KeyboardInterrupt:
	print 'Termina polling'


# Prueba detectando el evento, hace algo continuamente
# y cuando detecta el cambio realiza una accion
'''
GPIO.add_event_detect(PIN_TEST, GPIO.FALLING)
i = 0
try:
	while True:
		print 'Llevo ', i, ' cuentas'
		i += 1
		if GPIO.event_detected(PIN_TEST):
			print 'Flanco de bajada detectado!!!'
		time.sleep(1)
except KeyboardInterrupt:
	print 'Termina rutina constante'
'''
