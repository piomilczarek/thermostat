from flask import Flask, request, render_template, jsonify, json, g, current_app
from modules import database, heater
import time, os, sys, datetime, thread

app = Flask(__name__)

config = database.cDBhandle()
heater = heater.cHeater()


#reset of the relays (on/off)
heater.turnCHOn()
heater.turnHWOn()
time.sleep(0.1)
heater.turnCHOff()
heater.turnHWOff()




def getJSONstatusFromDB(config, heater):
    config.getConfig()
    status = config.getConfigDict()
    status['chStatus'] = heater.chStatus
    status['hwStatus'] = heater.hwStatus
    return status

def getJSONstatus(config, heater):
    #config.getConfig()
    status = config.getConfigDict()
    status['chStatus'] = heater.chStatus
    status['hwStatus'] = heater.hwStatus
    return status

def getTargetSchedule(config): #returns desired temeprature from the heating schedule
    curr_time = str(datetime.datetime.now()).split(" ")[1][:8]
    dayOfTheWeek = datetime.datetime.today().weekday()
    if dayOfTheWeek < 5: 
        scheduleList = config.planWeekdays
    else: 
        scheduleList = config.planWeekends

    if config.holidayMode == 1: 
        scheduleList = config.planHoliday

    if config.weekendMode == 1: 
        scheduleList = config.planWeekends

    for schedule in scheduleList:
        if schedule.getTimeOn() < curr_time < schedule.getTimeOff():
            return schedule
    return 0 #


def heatingDemon(config, heater):
    try:
        while 1:
        #Summer Mode - ensure the hot water is available during the summer when, schedule base on temperature would never the heating on.
        #Simple but effective. Check if summer mode is on, if yes just heat the HW X min in the morning and X min in the afternoon using ForceHW switch
        #do not heat the water when HolidayMode is ON
            if config.summerMode == 1 and config.holidayMode == 0 and config.forceHW == 0:
                if datetime.time(5, 50) < datetime.datetime.now().time() < datetime.time(5, 51): #turn on the HW for 25 min around 5:50-5:51                    config.setForceHW(35)
                    config.setForceHW(35)
                if datetime.time(17, 30) < datetime.datetime.now().time() < datetime.time(17, 31): #turn on the HW for 35 min around 17:30-17:31
                    config.setForceHW(35)

        #Start of Force HW/CH Check
            if config.forceCH>0: 
                if heater.chStatus == 0:
                    heater.turnCHOn()
                    config.logCHOn()
                    heater.turnHWOn() #when forcing Central Heating I want to heat water too 
                    config.logHWOn()
                else:
                    diff = int(str(datetime.datetime.now()-heater.lastOnCH).split(":")[1]) #get the heater On timestamp and check the diff vs. actual time, if diff is equal to ForceCH value, switch off the heater
                    if diff == config.forceCH:
                        heater.turnCHOff()
                        config.logCHOff()
                        config.setForceCH(0)

            if config.forceHW>0:
                if heater.hwStatus == 0:
                    heater.turnHWOn()
                    config.logHWOn()
                else:
                    diff = int(str(datetime.datetime.now()-heater.lastOnHW).split(":")[1])
                    if diff == config.forceHW:
                        heater.turnHWOff()
                        config.logHWOff()
                        config.setForceHW(0)
        #End of Force HW/CH Check
            
        #->Start of normal check Weekdays, Weekends, Holidays      
            try:
                while not heater.checkTemp(): #read sensor, chceck CRC and save Room tempt to heater.CurrTemp
                    #print "Error in reading temp from the sensor (CRC) - trying again in 2s"
                    time.sleep(1)
            except:
                pass

            try:    
                targetTemp = getTargetSchedule(config).getTargetTemp()
                currentSensorTemp = heater.getCurrTemp()
                config.desiredTemp = targetTemp
                config.currTemp = currentSensorTemp
            except:
                targetTemp = 0
            """
            print targetTemp - config.deltaTempMinus    
            print currentSensorTemp
            print targetTemp + config.deltaTempPlus
            print heater.chStatus
            print heater.hwStatus
            """
            if currentSensorTemp <= targetTemp - config.deltaTempMinus and heater.chStatus == 0 and config.forceCH == 0:
                heater.turnCHOn()
                config.logCHOn()

            if currentSensorTemp <= targetTemp - config.deltaTempMinus and heater.hwStatus == 0 and config.forceHW == 0:
                heater.turnHWOn()
                config.logHWOn()

            if currentSensorTemp > targetTemp + config.deltaTempPlus and heater.chStatus == 1 and config.forceCH == 0:
                heater.turnCHOff()
                config.logCHOff()

            if currentSensorTemp > targetTemp+config.deltaTempPlus and heater.hwStatus == 1 and config.forceHW == 0 and config.forceCH == 0:
                heater.turnHWOff()
                config.logHWOff()
        #->End of normal check

        #loop every x seconds
            #print (targetTemp)
            """
            print 'Target temp '+str(config.desiredTemp)
            print 'Current temp '+str(config.currTemp)
            print 'ForceCH: '+str(config.forceCH)
            print 'ForceHW '+str(config.forceHW)
            print 'HolidayMode '+str(config.holidayMode)
            print 'SummerMode '+str(config.summerMode)
            print 'WeekendMode '+str(config.weekendMode)
            """
            time.sleep(1)
    except KeyboardInterrupt: #manual/exceptional shut down - if the heater is ON, switch OFF
        if heater.chStatus == 1:
            heater.turnCHOff()
            config.logCHOff()
        if heater.hwStatus == 1:
            heater.turnHWOff() 
            config.logHWOff()
        print "CTRL+C\n"


@app.route("/", methods=["GET", "POST"])
def index():
    global config
    global heater
    currentState = getJSONstatus(config, heater)
    return render_template("index.html")

@app.route('/robot/api/<command>', methods = ['PUT'])
def webCommand(command):
    global config
    global heater

    if command == 'getStatus':
        tempDict = getJSONstatus(config, heater)
        #tempDict = { 'currTemp': heater.getCurrTemp(), 'chStatus': heater.chStatus, 'hwStatus': heater.hwStatus }
        return jsonify(tempDict)

    if command == 'ForceCH':
        if config.forceCH > 0:
            config.setForceCH(0)
        else:
            config.setForceCH(20)

    elif command == 'ForceHW':
        if config.forceHW > 0:
            config.setForceHW(0)
        else:
            config.setForceHW(35)

    elif command == 'SummerMode':
        if config.summerMode == 1: 
            config.summerMode = 0
            config.updateModeInDB('SummerMode', 0)
        else:
            config.summerMode = 1
            config.updateModeInDB('SummerMode', 1)

    elif command == 'HolidayMode':
        if config.holidayMode == 1:
            config.holidayMode = 0
            config.updateModeInDB('HolidayMode', 0)
            config.desiredTemp = getTargetSchedule(config).getTargetTemp()
        else:
            config.holidayMode = 1
            config.updateModeInDB('HolidayMode', 1)
            config.desiredTemp = getTargetSchedule(config).getTargetTemp()

    elif command == 'WeekendMode':
        if config.weekendMode == 1:
            config.updateModeInDB('WeekendMode', 0)
            config.weekendMode = 0
        else:
            config.updateModeInDB('WeekendMode', 1)
            config.weekendMode = 1

    elif command == 'TempPlus':
        currentSchedule = getTargetSchedule(config)
        config.updateTempInDB(currentSchedule.getName(), currentSchedule.getDbRowId(), currentSchedule.getTargetTemp()+0.1)
        config.desiredTemp = getTargetSchedule(config).getTargetTemp()+0.1
 
    elif command == 'TempMinus':
        currentSchedule = getTargetSchedule(config)
        config.updateTempInDB(currentSchedule.getName(), currentSchedule.getDbRowId(), currentSchedule.getTargetTemp()-0.1)
        config.desiredTemp = getTargetSchedule(config).getTargetTemp()-0.1

    currentState = getJSONstatusFromDB(config, heater)
    return jsonify(currentState)


if __name__ == '__main__':
    try:
        thread.start_new_thread(heatingDemon,(config, heater) )
    except:
        print "Error: unable to start the thread"
    app.run(host='0.0.0.0', debug=True, port=8000, use_reloader=False)



