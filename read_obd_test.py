import serial
import time
import threading

ser = serial.Serial('/dev/rfcomm0', timeout=1, baudrate=10400)
ser.write(b'ATZ\r\n')
print(list(ser.readlines()))

while True:
    ser.write(b'010C\r\n')
    time.sleep(1)
    
    #https://stackoverflow.com/questions/17553543/pyserial-non-blocking-read-loop
    if (ser.inWaiting() > 0): #if incoming bytes are waiting to be read from the serial input buffer
        
        try: 
            data_str = ser.read(ser.inWaiting()).decode('ascii') #read the bytes and convert from binary array to ASCII
        finally:
            split_str = data_str.split(" ")
            print(data_str)
            print("split arr:")
            print(split_str)
            
            if (len(split_str) >= 2):
                split_str.pop(0)
                split_str.pop(len(split_str) - 1)
                
                print(split_str)
                
                
                
                code = split_str[0]
                data_a = split_str[1]
                
                print("code: " + code)
                print("data a: " + data_a)
                print("data a (int form): " + str(int(data_a, 16)))
                
                if len(split_str) >= 3:
                    data_b = split_str[2]
                    print("data b: " + data_b)
                    print("data b (int form): " + str(int(data_b, 16)))
                    
                    rpm = (256 * int(data_a, 16) + int(data_b, 16))/4
                    print("rpm: " + str(rpm))
                    
                    
        
    #print(list(ser.readlines()))
    



S