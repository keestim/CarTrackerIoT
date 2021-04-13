import serial              
from time import sleep
import sys

class GPSReader:
    def __init__(self, serialPort):
        self.serialPort = serialPort
        self.serialConnection = serial.Serial(serialPort)

        self.GPGGAInfo = "$GPGGA,"
        self.GPGGABuffer = []
        self.NMEABuffer = []

    def convertToDegrees(rawValue):
        decimalValue = rawValue/100.00
        degrees = int(decimalValue)

        #what is mm_mmmm
        #something to do with rounding!

        mm_mmmm = (decimalValue - int(decimalValue))/0.6
        position = degrees + mm_mmmm
        position = "%.4f" %(position)
        return float(position)

    def getGPSString():
        serialData = str(self.serialConnection.readline())
        GPGGADataAvailable = serialData.find(self.GPGGAInfo)   #check for NMEA GPGGA string   

        if (GPGGADataAvailable > 0):
            self.GPGGABuffer = received_data.split("$GPGGA,",1)[1]  #store data coming after “$GPGGA,” string
            self.NMEABuffer = (self.GPGGABuffer.split(','))
            
            NMEATime = []
            NMEALatitude = []
            NMEALongitude = []
            
            NMEATime = self.NMEABuffer[0]                    #extract time from GPGGA string
            NMEALatitude = self.NMEABuffer[1]                #extract latitude from GPGGA string
            NMEALongitude = self.NMEABuffer[3]               #extract longitude from GPGGA string

            latitude = convertToDegrees(float(NMEALatitude))
            longitude = convert_to_degrees(float(NMEALongitude))
            
            latitude *= (1 if (self.NMEABuffer[4] == "W") else -1)
            longitude *= (1 if (self.NMEABuffer[2] == "S") else -1)
            
            return str(latitude) + "," + str(longitude)
        else:
            return ""
  
ser = serial.Serial("/dev/ttyS0")
