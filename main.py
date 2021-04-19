from OBDDefinitions import * 
from GPSReader import *
from SQLConnection import * 
from TrafficAPIConnection import *

from threading import Thread
from time import sleep
import MySQLdb
import logging

#db = CarTrackingData 

#need mutliple persist functions
#1 - Start of Journey
#2 - Standard Journey recording
#3 - Over the speed limit journey

#pass in SQL connection?

class GPSDataThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.GPSObj = GPSReader("/dev/ttyS0")
        self.coordinates = ""
        self.speedLimit = 0
        
        self.start()
    
    def getGPSCoordinates(self):
        outputCoordinates = ""
        
        #loops until an actual value is received!
        while (outputCoordinates == ""):
            outputCoordinates = self.GPSObj.getGPSString()
        
        return outputCoordinates
        
    def run(self):
        while True:
            self.coordinates = self.getGPSCoordinates()        
            self.speedLimit = GetSpeedLimit(self.coordinates)
            
class RPMDataThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.RPMReaderObj = RPM('/dev/rfcomm0')
        self.RPM = 0
        
        self.start()
        
    def run(self):
        while True:
            tempRPM = self.RPMReaderObj.requestSerialData()
            if tempRPM != "":
                self.RPM = tempRPM

class SpeedDataThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.SpeedReaderObj = Speed('/dev/rfcomm0')
        self.speed = 0
        
        self.start()
        
    def run(self):
        while True:
            tempSpeed = self.SpeedReaderObj.requestSerialData()
            if tempSpeed != "":
                self.speed = tempSpeed

def persistDataToDB(dbConn, GPSString, Speed, RPM):
    with dbConn:
        cursor = dbConn.cursor()
        cusrsor.execute()
        dbConn.commit()
        cursor.close()

#ensure that user name and password and stored in external file
#THAT'S NOT TRACKED BY GIT

#check db name!
#maybe have a shell script to auto add tables, etc


SQLInfo = SQLConnection("SQLInfo.txt")

#initalise with a "start" value!


#need to store journey pk 
#need to know when to record start position, etc
 
     
#add mutli threading?
     
GPSThread = GPSDataThread()
RPMThread = RPMDataThread()
#SpeedThread = SpeedDataThread()



#maybe have an enum to dictate states?
     
while True:
    #may check if the thread is active?
    #print(GPSThread.coordinates)
    #print(GPSThread.speedLimit)
    print("RPM: ")
    print(RPMThread.RPM)
    sleep(1)
    

