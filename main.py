from OBDDefinitions import * 
from GPSReader import *
from SQLConnection import * 
from TrafficAPIConnection import *

from threading import Thread
from time import sleep
import MySQLdb
import logging

import datetime

#db = CarTrackingData 

#need mutliple persist functions
#1 - Start of Journey
#2 - Standard Journey recording
#3 - Over the speed limit journey

#pass in SQL connection?
import enum

class RecordingState(enum.Enum):
    Init = 1
    Moving = 2

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
            print("RPM")
            print(tempRPM)
            
            if (tempRPM != "") and (tempRPM is not None):
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
            
            
            if (tempSpeed != "") and (tempSpeed is not None):
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

#potentially have some kind of lock to serial BT threads!
     
GPSThread = GPSDataThread()
RPMThread = RPMDataThread()
SpeedThread = SpeedDataThread()

vehicleRecordingState = RecordingState.Init
journeyID = 0

while True:
    #may check if the thread is active?
    if GPSThread.coordinates != "" and GPSThread.coordinates is not None:
        print(GPSThread.coordinates)
        coordinates_values = GPSThread.coordinates.split(",")
        print(coordinates_values)
        
        longitude = coordinates_values[0]
        latitude = coordinates_values[1]  
     
        if vehicleRecordingState == RecordingState.Init and SpeedThread.speed > 0:
            #move to other class
            cursor = SQLInfo.dbConn.cursor()
            cursor.execute(
                "INSERT INTO Journeys " +
                " (startLatitude, startLongitude, startTime) " +
                " VALUES " +
                "(" +
                    longitude + ", " +
                    latitude + ", " +
                    "'" + str(datetime.datetime.now()) + "'" + 
                "); ")
            
            SQLInfo.dbConn.commit()
            
            journeyID = cursor.execute('select last_insert_id() from Journeys')
            print("Journey ID:")
            print(journeyID)
            
            cursor.close()
            
            print("Added Data")
            
            vehicleRecordingState = RecordingState.Moving
            
        elif (vehicleRecordingState == RecordingState.Moving):
            cursor = SQLInfo.dbConn.cursor()
     
            print("Instance Data")
            
            print("INSERT INTO JourneyDetails " +
                " (journeyID, latitude, longitude, speed, RPM, time) " +
                " VALUES " +
                "(" +
                    str(journeyID) + ", " +
                    str(float(longitude)) + ", " +
                    str(float(latitude)) + ", " +
                    str(int(SpeedThread.speed)) + ", " +
                    str(int(RPMThread.RPM)) + ", " +
                    "'" + str(datetime.datetime.now()) + "'" +
                "); ")
            
            cursor.execute(
                "INSERT INTO JourneyDetails " +
                " (journeyID, latitude, longitude, speed, RPM, time) " +
                " VALUES " +
                "(" +
                    str(journeyID) + ", " +
                    str(float(longitude)) + ", " +
                    str(float(latitude)) + ", " +
                    str(int(SpeedThread.speed)) + ", " +
                    str(int(RPMThread.RPM)) + ", " +
                    "'" + str(datetime.datetime.now()) + "'" +
                "); ")
            
            SQLInfo.dbConn.commit()
            cursor.close()   

            if SpeedThread.speed > GPSThread.speedLimit:
                cursor = SQLInfo.dbConn.cursor()

                cursor.execute(
                    "INSERT INTO JourneyDetails " +
                    " (journeyID, latitude, longitude, speed, speedLimit, RPM, time) " +
                    " VALUES " +
                    "(" +
                    str(journeyID) + ", " +
                    str(float(longitude)) + ", " +
                    str(float(latitude)) + ", " +
                    str(int(SpeedThread.speed)) + ", " +
                    str(int(GPSThread.speedLimit)) + ", " +
                    str(int(RPMThread.RPM)) + ", " +
                    "'" + str(datetime.datetime.now()) + "'); ")

                SQLInfo.dbConn.commit()
                cursor.close()   

        sleep(2) 