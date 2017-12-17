import datetime
import MySQLdb
import time


class Schedule:
    def __init__(self, dbRowId, timeOn, timeOff, targetTemp, name):
        self.timeOn = timeOn
        self.timeOff = timeOff
        self.targetTemp = targetTemp
        self.dbRowId = dbRowId
        self.name = name

    def getTimeOn(self):
        return self.timeOn

    def getTimeOff(self):
        return self.timeOff

    def getTargetTemp(self):
        return self.targetTemp

    def getDbRowId(self):
        return self.dbRowId

    def getName(self):
        return self.name




class cDBhandle:
    
    def __init__(self):
        # I run the MySQL on localhost(RPi) without direct internet connection, I can access it via VPN only, so solution below is safe
        self.dbhost = "localhost" 
        self.dbuser = "root"
        self.dbpass = "mirza"
        self.dbbase = "termostat"
        # Object status variables to pass between MySQL, daemon and Flask WebAPP
        self.currTemp = 0
        self.desiredTemp = 0
        self.deltaTempPlus = 0
        self.deltaTempMinus = 0
        self.holidayMode = 0
        self.weekendMode = 0
        self.summerMode = 0
        self.forceHW = 0
        self.forceCH = 0
        self.chStatus = 0
        self.hwStatus = 0
        self.planWeekdays = []
        self.planWeekends = []
        self.planHoliday = []
        self.getConfig()

    def getConfigDict(self):
        return {'forceCH': self.forceCH, 'forceHW': self.forceHW, 'currTemp': self.currTemp, 'desiredTemp': self.desiredTemp, 'holidayMode': self.holidayMode, 'weekendMode': self.weekendMode, 'summerMode' : self.summerMode}

    def updateModeInDB(self, mode, newValue):
        db = MySQLdb.connect(self.dbhost,self.dbuser,self.dbpass,self.dbbase)
        cursor = db.cursor()
        sql = "UPDATE config SET "+mode+"="+str(newValue)+" where id='1'"
        try:
            cursor.execute(sql)
            db.commit()
            db.close()
            return True
        except:
            db.close()
            return False    


    def updateTempInDB(self, table, id, value):
       db = MySQLdb.connect(self.dbhost,self.dbuser,self.dbpass,self.dbbase)
       cursor = db.cursor()
       sql = "UPDATE "+str(table)+" SET temp="+str(value)+" where id="+str(id)
       print sql
       try:
           cursor.execute(sql)
           db.commit()
           db.close()
           return True
       except:
           db.close()
           return False


    def setForceHW(self, newValue):
        self.forceHW = newValue


    def setForceCH(self, newValue):
        self.forceCH = newValue


    def getConfig(self):
        db = MySQLdb.connect(self.dbhost,self.dbuser,self.dbpass,self.dbbase)
        cursor = db.cursor()
        try:
            sql = "SELECT * from config WHERE id = '1'"
            cursor.execute(sql)
            configFromDB = cursor.fetchone()
            db.commit()
            self.deltaTempMinus = configFromDB[1] 
            self.deltaTempPlus = configFromDB[2]
            self.holidayMode = configFromDB[3]
            self.weekendMode = configFromDB[4]
            self.summerMode = configFromDB[5]
            #self.forceHW = configFromDB[6]
            #self.forceCH = configFromDB[7]
            self.targetTemp = 0
            sql = "SELECT * from plan_weekdays"
            cursor.execute(sql)
            results = cursor.fetchall()
            del self.planWeekdays[:]
            for row in results:
                db_id = row[0]
                start_at = str(row[1]).zfill(8)
                end_at = str(row[2]).zfill(8)
                tempToHeat = row[3]
                self.planWeekdays.append(Schedule(db_id, start_at, end_at, tempToHeat, 'plan_weekdays'))
            sql = "SELECT * from plan_weekends"
            cursor.execute(sql)
            results = cursor.fetchall()
            del self.planWeekends[:]
            for row in results:
                db_id = row[0]
                start_at = str(row[1]).zfill(8)
                end_at = str(row[2]).zfill(8)
                tempToHeat = row[3]
                self.planWeekends.append(Schedule(db_id, start_at, end_at, tempToHeat, 'plan_weekends'))
            sql = "SELECT * from plan_holiday"
            cursor.execute(sql)
            results = cursor.fetchall()
            del self.planHoliday[:]
            for row in results:
                db_id = row[0]
                start_at = str(row[1]).zfill(8)
                end_at = str(row[2]).zfill(8)
                tempToHeat = row[3]
                self.planHoliday.append(Schedule(db_id, start_at, end_at, tempToHeat, 'plan_holiday'))
            db.close()
            return True
        except:
            db.close()
            return False
        

    def logCHOn(self):
        db = MySQLdb.connect(self.dbhost,self.dbuser,self.dbpass,self.dbbase)
        cursor = db.cursor()
        sql = "INSERT INTO chlog(heat_on) VALUES(NOW())"
        try:
            cursor.execute(sql)
            db.commit()
            db.close()
            return True
        except:
            db.close()
            return False

    def logCHOff(self):
        db = MySQLdb.connect(self.dbhost,self.dbuser,self.dbpass,self.dbbase)
        cursor = db.cursor()
        sql = "SELECT TIMESTAMPDIFF(MINUTE, (SELECT heat_on FROM chlog WHERE id = (SELECT MAX(id) as id  from chlog)), NOW())"
        try:
            cursor.execute(sql)
            tSinceLastOn = cursor.fetchone()
            sql = "SELECT MAX(id) as id from chlog"
            cursor.execute(sql)
            lastid = cursor.fetchone()
            sql = '{}{} {}{}'.format('UPDATE chlog SET heat_off = NOW(), heat_time = ',tSinceLastOn[0],'WHERE id = ',lastid[0])
            cursor.execute(sql)
            db.commit()
            db.close()
            return True
        except:
            db.close()
            return False

    
    def logHWOn(self):
        db = MySQLdb.connect(self.dbhost,self.dbuser,self.dbpass,self.dbbase)
        cursor = db.cursor()
        sql = "INSERT INTO hwlog(heat_on) VALUES(NOW())"
        try:
            cursor.execute(sql)
            db.commit()
            db.close()
            return True
        except:
            db.close()
            return False


    def logHWOff(self):
        db = MySQLdb.connect(self.dbhost,self.dbuser,self.dbpass,self.dbbase)
        cursor = db.cursor()
        sql = "SELECT TIMESTAMPDIFF(MINUTE, (SELECT heat_on FROM hwlog WHERE id = (SELECT MAX(id) as id from hwlog)), NOW())"
        try:
            cursor.execute(sql)
            tSinceLastOn = cursor.fetchone()
            sql = "SELECT MAX(id) as id from hwlog"
            cursor.execute(sql)
            lastid = cursor.fetchone()
            sql = '{}{} {}{}'.format('UPDATE hwlog SET heat_off = NOW(), heat_time = ',tSinceLastOn[0],'WHERE id = ',lastid[0])
            cursor.execute(sql)
            db.commit()
            db.close()
            return True
        except:
            db.close()
            return False

