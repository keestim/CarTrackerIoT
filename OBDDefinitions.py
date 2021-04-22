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
        
        self.value = 0
        self.sharedLock = lock

    #message data is hexadecimal form, need to convert to decimal values
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
        try:
            #lock serial write and read, so only on thread can send and receive messages at once
            #i.e. prevents speed thread from receiving rpm messages
            self.sharedLock.acquire()
        finally:
            
            try:
                #need to encode message as byte type, as it's a serial message
                self.serialConnection.write(self.pidCode.encode('utf_8') + b'\r\n')
                
            except:
                print("Serial Connection unable to write!")
            finally:
                time.sleep(1)
            
                #https://stackoverflow.com/questions/17553543/pyserial-non-blocking-read-loop
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
                    #remove first and last elements as they are noise
                    msgComponents.pop(0)
                    msgComponents.pop(len(msgComponents) - 1)
                    sleep(0.5)

                    return self.getProcessedValue(self.convertHexValues(msgComponents))

#child class where the actual implementation occurs                     
class Speed(OBDData):
    def __init__(self, lock, serialPort):
        #010D is the OBD pid for Vehicle Speed
        super().__init__(lock, serialPort, '010D', 1)

    def getProcessedValue(self, dataArray):
        if dataArray is not None:
            if len(dataArray) >= 2:
                return dataArray[1]


class RPM(OBDData):
    def __init__(self, lock, serialPort):
        #010C is the OBD pid for RPM
        super().__init__(lock, serialPort, '010C', 2)

    def getProcessedValue(self, dataArray):
        if dataArray is not None:
            #formula for processing serial array into RPM value
            if len(dataArray) >= 3:
                return (256 * dataArray[1] + dataArray[2])/4

