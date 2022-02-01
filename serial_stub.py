import serial
import sys
import time

port     = '/dev/ttyUSB1'
baudrate = 19200
timeout  = 1
bytesize = 8
stopbits = serial.STOPBITS_ONE
rsize    = 100
test_message = 'Received'

cnt = 0
while 1:
    with serial.Serial(port=port, baudrate=baudrate, bytesize=bytesize, timeout=timeout, stopbits=stopbits) as s:
        r = ''
        r = s.read(rsize)
        if r:
            print('%d: %s'%(cnt,r))
            time.sleep(1)
            s.write(b'%s: %s\r\n'%(bytes(test_message,'utf8'),r))
    cnt = cnt + 1
