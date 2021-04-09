import serial              
from time import sleep
import sys

ser = serial.Serial("/dev/ttyS0")
gpgga_info = "$GPGGA,"
GPGGA_buffer = 0
NMEA_buff = 0

def convert_to_degrees(raw_value):
    decimal_value = raw_value/100.00
    degrees = int(decimal_value)
    mm_mmmm = (decimal_value - int(decimal_value))/0.6
    position = degrees + mm_mmmm
    position = "%.4f" %(position)
    return float(position)

def get_gps_string():
    received_data = (str)(ser.readline()) #read NMEA string received
    GPGGA_data_available = received_data.find(gpgga_info)   #check for NMEA GPGGA string                
    if (GPGGA_data_available > 0):
        GPGGA_buffer = received_data.split("$GPGGA,",1)[1]  #store data coming after “$GPGGA,” string
        NMEA_buff = (GPGGA_buffer.split(','))
        nmea_time = []
        nmea_latitude = []
        nmea_longitude = []
        
        nmea_time = NMEA_buff[0]                    #extract time from GPGGA string
        nmea_latitude = NMEA_buff[1]                #extract latitude from GPGGA string
        nmea_longitude = NMEA_buff[3]               #extract longitude from GPGGA string

        lat = (float)(nmea_latitude)
        lat = convert_to_degrees(lat)
        longi = (float)(nmea_longitude)
        longi = convert_to_degrees(longi)
        
        lat *= (1 if (NMEA_buff[4] == "W") else -1)
        longi *= (1 if (NMEA_buff[2] == "S") else -1)
        
        return str(lat) + "," + str(longi)
    else:
        #maybe have some handling for this!
        return "no data yet"
               
