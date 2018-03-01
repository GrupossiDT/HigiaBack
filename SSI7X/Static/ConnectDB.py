import psycopg2
from psycopg2.sql import NULL
import SSI7X.Static.config_DB as mConf  # @UnresolvedImport
from psycopg2.extras import RealDictCursor

class ConnectDB():
   
    hostName = mConf.DB_HOST
    username = mConf.DB_USER_NAME
    password = mConf.DB_PASSWORD
    database = mConf.DB_NAME
    myconn = NULL
    
    def connet(self):
        try:
            self.myconn = psycopg2.connect(host = self.hostName, user = self.username, password = self.password, dbname = self.database)
            return True
        except psycopg2.OperationalError as e:  # @UnusedVariable
            return False
            
    def disconnet(self):
        self.myconn.close()
        
    def querySelect(self,table, columns, clause = NULL):
        strQuery="SELECT "+ columns +" FROM "+table 
        
        if clause != NULL:
            strQuery+=" WHERE "+ clause
        
        try:
            self.connet()    
            cur = self.myconn.cursor(cursor_factory=RealDictCursor)
            cur.execute(strQuery)
            r = cur.fetchall()
            self.disconnet()
            return r
        except psycopg2.OperationalError as e:
            return e
    
    def queryInsert(self,table,objectValues, returnColumn = NULL):
        strColumnNames = ""
        strColumnValues = ""
        for key, value in objectValues.items():
            strColumnNames += key+ ","
            strColumnValues += "'"+value + "',"
             
        strQuery = "INSERT INTO "+table+" (" + strColumnNames.strip(',') +") VALUES("+ strColumnValues.strip(',') +")"
        
        if returnColumn != NULL:
            strQuery += " RETURNING " + returnColumn
        
        try:
            self.connet()    
            cur = self.myconn.cursor()
            cur.execute(strQuery)
            
            if returnColumn != NULL:
                r = cur.fetchone()[0]
            else:
                r=1    
            
            self.myconn.commit()
            self.disconnet()
        
            return r
        
        except psycopg2.OperationalError as e:
            print(e)
            return -1 
        
    
    def queryUpdate(self,table,objectValues,clause = NULL):
        set=''
        for key, value in objectValues.items():
            strValue = str(value)
            if not strValue.isnumeric(): 
                set += key + "='" + value + "',"
            else:
                set += key + "=" + str(value) + ","
                
        strQuery ="UPDATE "+table+" SET " +set.strip(',')
        
        if clause != NULL:
            strQuery +=" WHERE " +clause
            
        print(strQuery)
        try:   
            self.connet()   
            cur = self.myconn.cursor()
            cur.execute(strQuery) 
            self.myconn.commit()
            self.disconnet()
            
            return True
        except psycopg2.OperationalError as e:
            return False
    
    
    def queryUpdateFree(self,strUpdate):
        try:   
            self.connet()   
            cur = self.myconn.cursor()
            cur.execute(strUpdate) 
            self.myconn.commit()
            self.disconnet()
            
            return True
        except psycopg2.OperationalError as e:
            return False
    
    def queryDelete(self,table,clause = NULL):
        try:
            strQuery ="DELETE FROM "+ table
            if clause != NULL:
                strQuery +=" WHERE " + clause
                 
            self.connet()   
            cur = self.myconn.cursor()
            cur.execute(strQuery) 
            self.myconn.commit()
            self.disconnet()
            return True
        except psycopg2.OperationalError as e:
            return e
    
    def queryFree(self,strQuery):
        if strQuery != NULL:
            try:
                self.connet()
                cur = self.myconn.cursor(cursor_factory=RealDictCursor)
                cur.execute(strQuery)
                r = cur.fetchall()
                self.disconnet()
                return  r
            except psycopg2.OperationalError as e:
                return e