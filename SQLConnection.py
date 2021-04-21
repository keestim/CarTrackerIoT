import MySQLdb

class SQLConnection:
    def __init__(self, authFilePath):
        self.getConnection(authFilePath)
        
        self.dbConn = MySQLdb.connect(self.Host, self.Username, self.Password, self.Database) or ("Could not connect to database")
        print(self.dbConn)
    
    def getConnection(self, authFilePath):
        f = open(authFilePath, "r")
        
        detailsArray = f.read().split("\t")
        self.Host = detailsArray[0]
        self.Username = detailsArray[1]
        self.Password = detailsArray[2]
        self.Database = detailsArray[3]
        
        print(self.Username)
        print(self.Password)
        
        f.close()

    def executeQuery(self, queryStr, targetTable = ""):
        cursor = self.dbConn.cursor()     
        cursor.execute(queryStr)
            
        self.dbConn.commit()
        
        returnStr = ""

        if (targetTable != ""):
            returnStr = cursor.execute('select last_insert_id() from ' + targetTable)
            
        cursor.close()

        return returnStr
