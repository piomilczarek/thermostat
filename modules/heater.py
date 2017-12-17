import RPi.GPIO as GPIO
import datetime

class cHeater:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(23, GPIO.OUT) #CH Pin in RPi
        GPIO.setup(24, GPIO.OUT) #HW Pin in Rpo
        self.chStatus = 0
        self.hwStatus = 0
        self.currTemp = -1
        self.lastOffCH = 0
        self.lastOffHW = 0
        self.lastOnCH = 0
        self.lastOnHW = 0

    def getCurrTemp(self):
        return self.currTemp

    def checkTemp(self):
        try:
            tempfile = open("/sys/bus/w1/devices/28-0516607603ff/w1_slave") #location of the temperature sensor file(move to the cfg?)
            thetext = tempfile.read()
            tempfile.close()
            crc = thetext.split("\n")[0].split(" ")[11]
            tempdata = thetext.split("\n")[1].split(" ")[9]
            if crc == "YES":
                temperature = float(tempdata[2:])
                temperature = temperature / 1000
                self.currTemp = temperature
                return True
            else:
                self.currTemp = ""
                return False
        except:
            self.currTemp = ""
            return False

    
    def turnCHOff(self):
        try:
            if self.chStatus==1:
                self.lastOffCH=datetime.datetime.now()
                GPIO.output(23, GPIO.HIGH)
                self.chStatus = 0
                print "CH OFF"
                return True
            else: return False
        except:
            print "Raspberry GPIO problem!"
            return False

    def turnCHOn(self):
        try:
            if self.chStatus==0:
                self.lastOnCH=datetime.datetime.now()
                GPIO.output(23, GPIO.LOW)
                self.chStatus = 1
                print "CH ON"
                return True
            else: return False
        except:
            print "Raspberry GPIO problem!"
            return False

    def turnHWOff(self):
        try:
            if self.hwStatus==1:
                self.lastOffHW=datetime.datetime.now()
                GPIO.output(24, GPIO.HIGH)
                self.hwStatus = 0
                print "HW OFF"
                return True
            else: return False
        except:
            print "Raspberry GPIO problem!"
            return False

    def turnHWOn(self):
        try:
            if self.hwStatus==0:
                self.lastOnHW=datetime.datetime.now()
                GPIO.output(24, GPIO.LOW)
                print "HW ON"
                self.hwStatus = 1
                return True
            else: return False
        except:
            print "Raspberry GPIO problem!"
            return False

