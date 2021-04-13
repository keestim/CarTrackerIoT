import serial
import time
import threading

class OBDData:
    def __init__(self, serialPort, pidCode, numBits):
        self.numBits = numBits
        self.pidCode = pidCode
        self.serialPort = serialPort
        self.serialConnection = serial.Serial(serialPort, timeout=1, baudrate=10400)

    def convertHexValues(msgComponents):
        hexValueArray = []
        
        for hexString in msgComponents:
            hexValueArray.push(int(hexString, 16))

        return hexValueArray

    def requestSerialData():
        #test this!!!!
        self.serialConnection.write(b'' + pidCode + '\r\n')
        time.sleep(1)
        
        #https://stackoverflow.com/questions/17553543/pyserial-non-blocking-read-loop
        if (self.serialConnection.inWaiting() > 0): #if incoming bytes are waiting to be read from the serial input buffer
            try: z
                dataStr = self.serialConnection.read(self.serialConnection.inWaiting()).decode('ascii') #read the bytes and convert from binary array to ASCII
            finally:
                msgComponents = dataStr.split(" ")

                if (len(msgComponents) >= 2):
                    #remove first and last elements as they are noise
                    msgComponents.pop(0)
                    msgComponents.pop(len(split_str) - 1)
                    
                    return getProcessedValue(convertHexValues(msgComponents))

class Speed(OBDData):
    def __init__(self, serialPort):
        super().__init__(serialPort, "010D", 1)

    def getProcessedValue(dataArray):
        return dataArray[0]


class RPM(OBDData):
    def __init__(self, serialPort):
        super().__init__(serialPort, "010C", 2)

    def getProcessedValue(dataArray):
        return (256 * dataArray[0] + dataArray[1])/4

