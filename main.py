from OBDDefinitions import * 
from GPSReader import *
from SQLConnection import * 
from TrafficAPIConnection import *

import MySQLdb
import threading
import logging

import asyncio


from time import sleep

#db = CarTrackingData 

#need mutliple persist functions
#1 - Start of Journey
#2 - Standard Journey recording
#3 - Over the speed limit journey

#pass in SQL connection?
def persistDataToDB(dbConn, GPSString, Speed, RPM):
    with dbConn:
        cursor = dbConn.cursor()
        cusrsor.execute()
        dbConn.commit()
        cursor.close()

RPMReader = RPM('/dev/rfcomm0')
GPSValues = GPSReader("/dev/ttyS0")

#ensure that user name and password and stored in external file
#THAT'S NOT TRACKED BY GIT

#check db name!
#maybe have a shell script to auto add tables, etc


SQLInfo = SQLConnection("SQLInfo.txt")

#initalise with a "start" value!


#need to store journey pk 
#need to know when to record start position, etc

#create class for gps?


#USE THIS GUIDE:
#https://stackoverflow.com/questions/52246796/await-a-method-and-assign-a-variable-to-the-returned-value-with-asyncio
while True:
    print(GPSValues.getGPSString())
    coordinatesString = await GPSValues.getGPSString()
    print("coords: " +  coordinatesString)

    
    
    


