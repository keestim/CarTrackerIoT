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

import RPi.GPIO as GPIO

import enum
import time

sharedLock = threading.Lock()
speechLock = threading.Lock()

excessRPMOutput = False
excessSpeedOutput = False

def AllowOBDSpeedRequest():
    SpeedThread.canRequestSpeed = True

def AllowOBDRPMRequest():
    RPMThread.canRequestRPM  = True

class LEDAvgRPMThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.start()

        self.highRPMPin = 17
        self.lowRPMPin = 19
        self.idleRPMPin = 26

    def killLights(self):
        GPIO.output(highRPMPin, GPIO.LOW)   
        GPIO.output(lowRPMPin, GPIO.LOW)    
        GPIO.output(idleRPMPin, GPIO.LOW)     
    
    def turnOnLight(self, pinNum):
        GPIO.output(highRPMPin, GPIO.HIGH)   

    def getAvgRPMValue(self):
        print(SQLInfo.getAvgRPMValue(
            " SELECT TimedRPMSubset.journeyID, AVG(TimedRPMSubset.RPM) " +
            " FROM ( " +
            "   SELECT " + 
            "       JourneyDetails.journeyID, " + 
            "       JourneyDetails.RPM, " +
            "       JourneyDetails.time, " +
            "       MaxTimeSelection.maxTime " +
            "   FROM " +
            "   JourneyDetails " +
            "   INNER JOIN ( " +
            "   SELECT " + 
            "   MAX(JourneyDetails.journeyID) as journeyID, MAX(JourneyDetails.time) as maxTime " + 
            "   FROM " + 
            "   JourneyDetails) AS MaxTimeSelection " + 
            "   ON " + 
            "   JourneyDetails.journeyID = MaxTimeSelection.journeyID " +
            "   HAVING " +
            "   JourneyDetails.time >= DATE_SUB(MaxTimeSelection.maxTime, INTERVAL 1 DAY_MINUTE)) " +
            "   AS TimedRPMSubset " +
            "   GROUP BY " +
            "   TimedRPMSubset.journeyID;"))   

    def run(self):
        while True:
            getAvgRPMValue()

            sleep(4)

class TextToSpeech(Thread):
    def __init__(self, inputText):
        super(TextToSpeech, self).__init__()
        self.outputText = inputText
        
    def run(self):
        cmd_beg= 'espeak '
        cmd_end= ' 2>/dev/null' # To dump the std errors to /dev/null
        call([cmd_beg + '"' + self.outputText + '"' + cmd_end], shell=True)
        sleep(0.2)
        speechLock.release()  

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
            coordinates_values = GPSThread.coordinates.split(",")
            
            print(coordinates_values)
            
            self.longitude = coordinates_values[0]
            self.latitude = coordinates_values[1]

            sleep(0.5)
            self.speedLimit = GetSpeedLimit(self.coordinates)
            sleep(1)
            
class RPMDataThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.RPMReaderObj = RPM(sharedLock, '/dev/rfcomm0')
        self.RPM = 0
        
        self.canRequestRPM = True
        
        sleep(1)
        self.start()
        
    def run(self):
        while True:
            if self.canRequestRPM:
                tempRPM = self.RPMReaderObj.requestSerialData()
                sleep(0.2)
                self.RPMReaderObj.sharedLock.release()
                
                if (tempRPM != "") and (tempRPM is not None) and not excessRPMOutput:
                    self.RPM = tempRPM
                    self.canRequestRPM = False
                    timer = threading.Timer(0.5, AllowOBDRPMRequest)
                    timer.start()

class SpeedDataThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.SpeedReaderObj = Speed(sharedLock, '/dev/rfcomm0')
        self.speed = 0
        
        self.canRequestSpeed = True
        
        self.start()
        
    def run(self):
        while True:
            if self.canRequestSpeed:
                tempSpeed = self.SpeedReaderObj.requestSerialData()
                sleep(0.2)
                self.SpeedReaderObj.sharedLock.release()            
                
                if (tempSpeed != "") and (tempSpeed is not None) and not excessSpeedOutput:
                    self.speed = tempSpeed
                    self.canRequestSpeed = False
                    timer = threading.Timer(0.5, AllowOBDSpeedRequest)
                    timer.start()


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

LEDRPMThread = LEDAvgRPMThread()

vehicleRecordingState = RecordingState.Init
journeyID = 0

voiceThread = TextToSpeech("Welcome. to. Car. Tracker. I. O. T. Device.")
voiceThread.start()

while True:
    if GPSThread.coordinates != "" and GPSThread.coordinates is not None:
     
        if vehicleRecordingState == RecordingState.Init and SpeedThread.speed > 0:
            journeyID = SQLInfo.executeQuery(
                "INSERT INTO Journeys " +
                " (startLatitude, startLongitude, startTime) " +
                " VALUES " +
                "(" +
                    GPSThread.longitude + ", " +
                    GPSThread.latitude + ", " +
                    "'" + str(datetime.datetime.now()) + "'" + 
                "); ", "Journeys")

            print("Journey ID:")
            print(journeyID)
                        
            vehicleRecordingState = RecordingState.Moving
            
        elif (vehicleRecordingState == RecordingState.Moving):
            cursor = SQLInfo.dbConn.cursor()

            print("INSERT INTO JourneyDetails " +
                " (journeyID, latitude, longitude, speed, RPM, time) " +
                " VALUES " +
                "(" +
                    str(journeyID) + ", " +
                    str(float(GPSThread.longitude)) + ", " +
                    str(float(GPSThread.latitude)) + ", " +
                    str(int(SpeedThread.speed)) + ", " +
                    str(int(RPMThread.RPM)) + ", " +
                    "'" + str(datetime.datetime.now()) + "'" +
                "); ")
            
            SQLInfo.executeQuery(
                "INSERT INTO JourneyDetails " +
                " (journeyID, latitude, longitude, speed, RPM, time) " +
                " VALUES " +
                "(" +
                    str(journeyID) + ", " +
                    str(float(GPSThread.longitude)) + ", " +
                    str(float(GPSThread.latitude)) + ", " +
                    str(int(SpeedThread.speed)) + ", " +
                    str(int(RPMThread.RPM)) + ", " +
                    "'" + str(datetime.datetime.now()) + "'" +
                "); ")
                        
            if RPMThread.RPM > 3000:
                try:
                    speechLock.acquire() 
                finally:
                    highRPMVoiceThread = TextToSpeech("High. R.P.M... Choose. higher. gear.")
                    highRPMVoiceThread.start()             
                
            if SpeedThread.speed > GPSThread.speedLimit:
                print("Speed LIMIT!!!!")
                print(GPSThread.speedLimit)
                
                excessSpeedOutput = True

                try:
                    speechLock.acquire()
                finally:
                    speedLimitVoiceThread = TextToSpeech("Exceeding. Speed. Limit.")
                    speedLimitVoiceThread.start()
                
                cursor = SQLInfo.dbConn.cursor()

                cursor.execute(
                    "INSERT INTO SpeedingOccurances " +
                    " (journeyID, latitude, longitude, speed, speedLimit, RPM, time) " +
                    " VALUES " +
                    "(" +
                    str(journeyID) + ", " +
                    str(float(GPSThread.longitude)) + ", " +
                    str(float(GPSThread.latitude)) + ", " +
                    str(int(SpeedThread.speed)) + ", " +
                    str(int(GPSThread.speedLimit)) + ", " +
                    str(int(RPMThread.RPM)) + ", " +
                    "'" + str(datetime.datetime.now()) + "'); ")

                SQLInfo.dbConn.commit()
                cursor.close()

                excessSpeedOutput = False

        sleep(2) 