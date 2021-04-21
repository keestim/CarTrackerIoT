from OBDDefinitions import * 
from GPSReader import *
from SQLConnection import * 
from TrafficAPIConnection import *

from subprocess import call

from threading import Thread
from time import sleep
import MySQLdb
import logging

import datetime
from num2words import num2words

import enum

sharedLock = threading.Lock()

class TextToSpeech(Thread):
    def __init__(self, inputText):
        super(TextToSpeech, self).__init__()
        self.outputText = inputText
        
    def run(self):
        cmd_beg= 'espeak '
        cmd_end= ' 2>/dev/null' # To dump the std errors to /dev/null
        call([cmd_beg + '"' + self.outputText + '"' + cmd_end], shell=True)

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
            sleep(0.5)
        
        return outputCoordinates
        
    def run(self):
        while True:
            self.coordinates = self.getGPSCoordinates()
            sleep(0.5)
            self.speedLimit = GetSpeedLimit(self.coordinates)
            sleep(1)
            
class RPMDataThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.RPMReaderObj = RPM(sharedLock, '/dev/rfcomm0')
        self.RPM = 0
        
        self.start()
        
    def run(self):
        while True:
            tempRPM = self.RPMReaderObj.requestSerialData()
            sleep(0.2)
            self.RPMReaderObj.sharedLock.release()
            
            print("RPM")
            print(tempRPM)
            
            if (tempRPM != "") and (tempRPM is not None):
                self.RPM = tempRPM

class SpeedDataThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.SpeedReaderObj = Speed(sharedLock, '/dev/rfcomm0')
        self.speed = 0
        
        self.start()
        
    def run(self):
        while True:
            tempSpeed = self.SpeedReaderObj.requestSerialData()
            sleep(0.2)
            self.SpeedReaderObj.sharedLock.release()            
            
            if (tempSpeed != "") and (tempSpeed is not None):
                self.speed = tempSpeed

def persistDataToDB(dbConn, GPSString, Speed, RPM):
    with dbConn:
        cursor = dbConn.cursor()
        cusrsor.execute()
        dbConn.commit()
        cursor.close()

SQLInfo = SQLConnection("SQLInfo.txt")
     
GPSThread = GPSDataThread()
RPMThread = RPMDataThread()
SpeedThread = SpeedDataThread()

vehicleRecordingState = RecordingState.Init
journeyID = 0

voiceThread = TextToSpeech("Welcome. to. Car. Tracker. I. O. T. Device.")

voiceThread.start()

while True:
    #may check if the thread is active?
    if GPSThread.coordinates != "" and GPSThread.coordinates is not None:
        #print(GPSThread.coordinates)
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
                        
            vehicleRecordingState = RecordingState.Moving
            
        elif (vehicleRecordingState == RecordingState.Moving):
            cursor = SQLInfo.dbConn.cursor()

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
            
            if RPMThread.RPM > 3000:
                highRPMVoiceThread = TextToSpeech("High. R.P.M... Choose. higher. gear.")
                highRPMVoiceThread.start()            
            
            if SpeedThread.speed > GPSThread.speedLimit:
                speedLimitVoiceThread = TextToSpeech("Exceeding. Speed. Limit.")
                
                speedLimitVoiceThread.start()
                
                cursor = SQLInfo.dbConn.cursor()

                cursor.execute(
                    "INSERT INTO SpeedingOccurances " +
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
                
                sleep(1)

        sleep(2) 