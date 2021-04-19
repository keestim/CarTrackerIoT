import serial
import time
import threading

class OBDData:
    def __init__(self, serialPort, pidCode, numBits):
        self.numBits = numBits
        self.pidCode = pidCode
        self.serialPort = serialPort
        self.serialConnection = serial.Serial(serialPort, timeout=1, baudrate=10400)

    def convertHexValues(self, msgComponents):
        hexValueArray = []
        
        for hexString in msgComponents:
            hexValueArray.append(int(hexString, 16))

        return hexValueArray
    
    def getProcessedValue(self, dataArray):
        return dataArray[0]

    def requestSerialData(self):
        try:
            print(self.pidCode.encode('utf_8') + b'\r\n')
            self.serialConnection.write(self.pidCode.encode('utf_8') + b'\r\n')
        except:
            print("Serial Connection unable to write!")
        finally:
            time.sleep(1)
        
            #https://stackoverflow.com/questions/17553543/pyserial-non-blocking-read-loop
            
            #need to handle:
            #File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
            #OSError: [Errno 5] Input/output error
            #ADD TRY-EXCEPTION BLOCK!
            msgComponents = ""
            
            try:
                if (self.serialConnection.inWaiting() > 0): #if incoming bytes are waiting to be read from the serial input buffer
                    dataStr = self.serialConnection.read(self.serialConnection.inWaiting()).decode('ascii') #read the bytes and convert from binary array to ASCII
                    
                    if self.pidCode not in dataStr:
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
    def __init__(self, serialPort):
        super().__init__(serialPort, '010D', 1)

    def getProcessedValue(self, dataArray):
        return dataArray[1]


class RPM(OBDData):
    def __init__(self, serialPort):
        super().__init__(serialPort, '010C', 2)

    def getProcessedValue(self, dataArray):
        print("getting RPM Value!")
        
        print(dataArray)
        return (256 * dataArray[1] + dataArray[2])/4

