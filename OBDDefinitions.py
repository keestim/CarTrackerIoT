import serial
import time
import threading
import logging
from time import sleep

class OBDData:
    def __init__(self, lock, serialPort, pidCode, numBits):
        self.numBits = numBits
        self.pidCode = pidCode
        self.serialPort = serialPort
        self.serialConnection = serial.Serial(serialPort, timeout=1, baudrate=10400)

        #Thread locking info
        #https://www.bogotobogo.com/python/Multithread/python_multithreading_Synchronization_Lock_Objects_Acquire_Release.php
        #refer to it as "shared" lock!
        
        self.value = 0
        self.sharedLock = lock

    def convertHexValues(self, msgComponents):
        hexValueArray = []
        
        try:
            for hexString in msgComponents:
                hexValueArray.append(int(hexString, 16))

            return hexValueArray
        except:
            return 
    
    def getProcessedValue(self, dataArray):
        return dataArray[0]

    def requestSerialData(self):
        print("attempting to acquire a lock")
        
        try:
            #self.lock.acquire()
            logging.debug('Acquired a lock')
        finally:
            #time.sleep(1)
            
            try:
                print(self.pidCode.encode('utf_8') + b'\r\n')
                self.serialConnection.write(self.pidCode.encode('utf_8') + b'\r\n')
                
            except:
                print("Serial Connection unable to write!")
            finally:
                #time.sleep(1)
            
                #https://stackoverflow.com/questions/17553543/pyserial-non-blocking-read-loop
                
                #need to handle:
                #File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
                #OSError: [Errno 5] Input/output error
                #ADD TRY-EXCEPTION BLOCK!
                msgComponents = ""
                
                try:
                    if (self.serialConnection.inWaiting() > 0): #if incoming bytes are waiting to be read from the serial input buffer
                        dataStr = self.serialConnection.read(self.serialConnection.inWaiting()).decode('ascii') #read the bytes and convert from binary array to ASCII
                        
                        print("Data String")
                        print(dataStr)
                        if self.pidCode not in dataStr or "NO" in dataStr:
                            return                        
                        
                        msgComponents = dataStr.split(" ")
                        print(msgComponents)

                except:
                    print("No bytes received from serial connection!")
            
                if (len(msgComponents) > 2):
                    print("entering critical section")
                    print(msgComponents)
                    
                    #remove first and last elements as they are noise
                    msgComponents.pop(0)
                    msgComponents.pop(len(msgComponents) - 1)

                    return self.getProcessedValue(self.convertHexValues(msgComponents))
                                 
  

class Speed(OBDData):
    def __init__(self, lock, serialPort):
        super().__init__(lock, serialPort, '010D', 1)

    def getProcessedValue(self, dataArray):
        return dataArray[1]


class RPM(OBDData):
    def __init__(self, lock, serialPort):
        super().__init__(lock, serialPort, '010C', 2)

    def getProcessedValue(self, dataArray):
        print("getting RPM Value!")
        
        print(dataArray)
        return (256 * dataArray[1] + dataArray[2])/4

