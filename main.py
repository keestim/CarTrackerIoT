from OBDDefinitions import * 
from GPSReader import *
from SQLConnection import * 

import MySQLdb

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



#need to store journey pk 
#need to know when to record start position, etc

#create class for gps?

while True:
    # test this
    print(get_gps_string())

