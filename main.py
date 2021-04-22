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

excessSpeedOutput = False

#the two records states the program can be in
class RecordingState(enum.Enum):
    Init = 1
    Moving = 2

#based off: https://learn.sparkfun.com/tutorials/python-programming-tutorial-getting-started-with-the-raspberry-pi/experiment-1-digital-input-and-output
#A class with a parent class of Thread was created to enable better system responsiveness 
#If all of the system functionality was synchronous, poor performance and significant issues would occur
class LEDAvgRPMThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.start()
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        #define pins for the various LEDs
        self.highRPMPin = 17
        self.lowRPMPin = 19
        self.idleRPMPin = 26
        
        GPIO.setup(self.highRPMPin ,GPIO.OUT)
        GPIO.setup(self.lowRPMPin,GPIO.OUT)
        GPIO.setup(self.idleRPMPin,GPIO.OUT)

        self.RPMValue = 0

    def killLights(self):
        #turn off all lights
        GPIO.output(self.highRPMPin, GPIO.LOW)   
        GPIO.output(self.lowRPMPin, GPIO.LOW)    
        GPIO.output(self.idleRPMPin, GPIO.LOW)     
    
    def turnOnLight(self, pinNum):
        #turn on the light for a specific input PIN number
        GPIO.output(pinNum, GPIO.HIGH)   

    #gets the average RPM value for the last 30 seconds of the current journey 
    def getAvgRPMValue(self):
        #query first first gets the maximum journey id and the last time that was recorded for that journey
        #then all journeyDetails records are collected that share that journey ID AND 
        #have a recorded time LESS THAN OR EQUAL TO 30 seconds, that this maximum time
        #then the average RPM of that collect data set is calculated and returned
        
        RPMData = SQLInfo.getResultQuery(
            " SELECT TimedRPMSubset.journeyID, AVG(TimedRPMSubset.RPM) " +
            " FROM ( " +
            "   SELECT " + 
            "       JourneyDetails.journeyID, " + 
            "       JourneyDetails.RPM, " +
            "       JourneyDetails.time, " +
            "       MaxTimeSelection.maxTime " +
            "   FROM " +
            "       JourneyDetails " +
            "   INNER JOIN ( " +
            "       SELECT " + 
            "           MAX(JourneyDetails.journeyID) as journeyID, MAX(JourneyDetails.time) as maxTime " + 
            "       FROM " + 
            "           JourneyDetails) AS MaxTimeSelection " + 
            "   ON " + 
            "       JourneyDetails.journeyID = MaxTimeSelection.journeyID " +
            "   HAVING " +
            "       JourneyDetails.time >= DATE_SUB(MaxTimeSelection.maxTime, INTERVAL 30 DAY_SECOND)) " +
            "   AS TimedRPMSubset " +
            "   GROUP BY " +
            "       TimedRPMSubset.journeyID" + 
            "   LIMIT 1")

        return RPMData[0][1]

    def run(self):
        while True:
            self.RPMValue = self.getAvgRPMValue()
            self.killLights()

            #state 1: IDLE
            #all car engines will idle at less than 1000 RPM
            #and a car would rarely operate at less than 1000 RPM whilst moving
            #hence, it state will occur when a car is stationary
            if self.RPMValue <= 1000:
                self.turnOnLight(self.idleRPMPin)
            #state 2:
            #econimical
            #Then will occur when a car is running, such that is will consume the minimal amount of fuel
            elif self.RPMValue <= 2200:
                self.turnOnLight(self.lowRPMPin)
            #state 3:
            #Aggressive
            #This state will likely be used when the driver is intending to drive fast
            #A car generally accelerate faster, then the RPMs are higher
            #High RPMs correlate to a higher fuel consumption
            else:
                self.turnOnLight(self.highRPMPin)

            sleep(4)

#thread for TextToSpeech, with thread locking implementation 
#to prevent multiple text to speech messages at once
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
        
        #loops until an actual value is received
        #the GPS device won't consistantly return a GPS string,
        #hence we need to request the serial GPS string, until there is an actual value returned
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
            #calls API to get speed limit for specified latitude and longitude
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

    def AllowOBDRPMRequest(self):
        self.canRequestRPM  = True
        
    def run(self):
        while True:
            if self.canRequestRPM:
                tempRPM = self.RPMReaderObj.requestSerialData()
                sleep(0.2)
                self.RPMReaderObj.sharedLock.release()
                
                if (tempRPM != "") and (tempRPM is not None):
                    self.RPM = tempRPM
                    self.canRequestRPM = False
                    timer = threading.Timer(0.5, self.AllowOBDRPMRequest)
                    timer.start()

class SpeedDataThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True

        #/dev/rfcomm0 I've configure the raspberry pi to communicate with the OBD sensor with
        #/dev/rfcomm0 is bound to the MAC address of the OBD device
        self.SpeedReaderObj = Speed(sharedLock, '/dev/rfcomm0')
        self.speed = 0
        
        self.canRequestSpeed = True
        
        self.start()

    def AllowOBDSpeedRequest(self):
        self.canRequestSpeed = True
        
    def run(self):
        while True:
            if self.canRequestSpeed:
                tempSpeed = self.SpeedReaderObj.requestSerialData()
                sleep(0.2)
                self.SpeedReaderObj.sharedLock.release()            
                
                if (tempSpeed != "") and (tempSpeed is not None) and not excessSpeedOutput:
                    self.speed = tempSpeed
                    self.canRequestSpeed = False
                    timer = threading.Timer(0.5, self.AllowOBDSpeedRequest)
                    timer.start()


def persistDataToDB(dbConn, GPSString, Speed, RPM):
    with dbConn:
        cursor = dbConn.cursor()
        cusrsor.execute()
        dbConn.commit()
        cursor.close()

SQLInfo = SQLConnection("SQLInfo.txt")
     
#start all of the threads
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

        #the Journey record will start once the vehicle start moving
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
                        
            #changes state to Moving
            vehicleRecordingState = RecordingState.Moving

        #whilst in the Moving state, it will keep recording vehicle data   
        elif (vehicleRecordingState == RecordingState.Moving):
            cursor = SQLInfo.dbConn.cursor()
            
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

            #when RPM exceeds 3000 RPM (i.e. High RPM)
        
            #locks are used, to ensure that there is only one text to voice message occur at a time
            #this prevents the user from being spammed with a constant stream of messages
            #Which don't provide any benefit over just having one message at a time
            if RPMThread.RPM > 3000:
                try:
                    speechLock.acquire() 
                finally:
                    highRPMVoiceThread = TextToSpeech("High. R.P.M... Choose. higher. gear.")
                    highRPMVoiceThread.start()             
                
            #when vehicle speed exceeds speed limit
            if SpeedThread.speed > GPSThread.speedLimit:    
                #excessSpeedOutput is used to prevent a new Speed value to be set
                #The driver may only be momentarily speed
                #so by the time this speeding information is recorded, the SpeedThread speed value may be updated
                #and will now be less than the speed limit       
                excessSpeedOutput = True

                #locks are used, to ensure that there is only one text to voice message occur at a time
                #this prevents the user from being spammed with a constant stream of messages
                #Which don't provide any benefit over just having one message at a time
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

        #sleep for 2 seconds, so that data isn't constantly recorded to database
        sleep(2) 