import serial
import time
import threading

ser = serial.Serial('/dev/rfcomm0', timeout=2, baudrate=10400)
ser.write(b'ATZ\r\n')
print(list(ser.readlines()))

while True:
    ser.write(b'010C\r\n')
    time.sleep(1)
    print(list(ser.readlines()))
    



