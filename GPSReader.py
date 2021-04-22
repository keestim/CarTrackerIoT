import serial              
from time import sleep
import sys
import asyncio

#code modified from:
#https://www.engineersgarage.com/microcontroller-projects/articles-raspberry-pi-neo-6m-gps-module-interfacing/
class GPSReader:
    def __init__(self, serialPort):
        self.serialPort = serialPort
        self.serialConnection = serial.Serial(serialPort)

        self.GPGGAInfo = "$GPGGA,"
        self.GPGGABuffer = []
        self.NMEABuffer = []

    def convertToDegrees(self, rawValue):
        decimalValue = rawValue/100.00
        degrees = int(decimalValue)

        mm_mmmm = (decimalValue - int(decimalValue))/0.6
        position = degrees + mm_mmmm
        position = "%.4f" %(position)
        return float(position)

    def getGPSString(self):
        serialData = str(self.serialConnection.readline())
        GPGGADataAvailable = serialData.find(self.GPGGAInfo)   #check for NMEA GPGGA string   

        if (GPGGADataAvailable > 0):
            self.GPGGABuffer = serialData.split("$GPGGA,",1)[1]  #store data coming after “$GPGGA,” string
            self.NMEABuffer = (self.GPGGABuffer.split(','))
            
            NMEATime = []
            NMEALatitude = []
            NMEALongitude = []
            
            NMEATime = self.NMEABuffer[0]                    #extract time from GPGGA string
            NMEALatitude = self.NMEABuffer[1]                #extract latitude from GPGGA string
            NMEALongitude = self.NMEABuffer[3]               #extract longitude from GPGGA string

            latitude = self.convertToDegrees(float(NMEALatitude))
            longitude = self.convertToDegrees(float(NMEALongitude))
            
            #latitude and longitude are mutliplied by -1, depending if the gps is location S or W, respectively
            latitude *= (1 if (self.NMEABuffer[4] == "W") else -1)
            longitude *= (1 if (self.NMEABuffer[2] == "S") else -1)
            
            #need to clear the serial buffer, due large amount of messages
            #Due to :self.serialConnection.readline()
            #only the last message in the serial buffer is read
            #Hence, same recorded location will be logged many times, if buffer isn't cleared!
            self.serialConnection.reset_output_buffer()
            self.serialConnection.reset_input_buffer()

            return str(latitude) + "," + str(longitude)
        else:
            return ""

