from OBDDefinitions import * 
from GPSReader import *

RPMReader = RPM('/dev/rfcomm0')

while True:
    # test this
    print(get_gps_string())