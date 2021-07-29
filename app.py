# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, session, copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from threading import Lock, current_thread
import time
import json
import numpy as np
from roleplay import sub2 as rs
from pathlib import Path
import pandas as pd
from scipy import interpolate
import csv
import matplotlib as mpl
import matplotlib.pyplot as plt
import os
import sys
import roleplay.sub2 as rs
import shutil
import datetime

async_mode = None
thread = None
thread_lock = Lock()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

# My Functions
def background_thread():
    count = 0

# My Classes
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)

# prepare path for parameter files
path = str(Path(__file__).parent)
if os.name == 'nt':
    path = path+"\\parameters\\"
elif os.name == 'posix':
    path = path+"/parameters/"
parameterFile1 = path+"variableAll.csv"
parameterFile2 = path+"eqLHVship.csv"
parameterFile3 = path+"CO2Eff.csv"
parameterFile4 = path+"unitCostFuel.csv"
parameterFile5 = path+"costShipBasic.csv"
parameterFile6 = path+"initialFleet1.csv"
parameterFile7 = path+"initialFleet2.csv"
parameterFile8 = path+"initialFleet3.csv"
#parameterFile9 = path+decisionListName1+".csv"
#parameterFile10 = path+decisionListName2+".csv"
#parameterFile11 = path+decisionListName3+".csv"
parameterFile12 = path+"eqLHVaux.csv"

valueDict, unitDict = rs.readinput(parameterFile1)
tOpSch = int(valueDict['tOpSch'])
startYear = int(valueDict['startYear'])
lastYear = int(valueDict['lastYear'])
NShipFleet = int(valueDict['NShipFleet'])
tbid = int(valueDict['tbid'])
regYear = np.linspace(valueDict['regStart'],valueDict['lastYear'],int((valueDict['lastYear']-valueDict['regStart'])//valueDict['regSpan']+1))
#regYear = np.linspace(2021,valueDict['lastYear'],int((valueDict['lastYear']-valueDict['regStart'])//valueDict['regSpan']+1))

# prepare fleets
initialFleets = [parameterFile6,parameterFile7,parameterFile8]
fleets = {'year': np.zeros(lastYear-startYear+1)}

# prepare regulator decision
nRegAct = 0
nRegDec = 0
regDec = rs.regPreFunc(len(regYear)+1)

NshipComp = 0
Nregulator = 0
Nuser = 0
userDict = {}
regulatorIDs = []
sumCta = 0
figEach = {}
figTotal = {}

# Routing
@app.route('/')
def index():
    global Nuser
    Nuser += 1
    return render_template('userSelection.html', Nuser=Nuser, valueDict=valueDict)

@socketio.event
def connect_event(message):
    userID = request.sid
    userDict.setdefault(userID,{})
    userDict[userID]['userNo'] = int(message['no'])
    userDict[userID]['userType'] = 'Not selected'
    userDict[userID]['userName'] = 'None'
    userDict[userID]['elapsedYear'] = 0
    userDict[userID]['state'] = 'Connected'
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response_connect', {'no': message['no']})

@socketio.event
def userSelection_event(message):
    userID = request.sid
    userNo = message['no']
    userType = message['type']
    userName = message['name']
    userDict[userID]['userNo'] = userNo
    userDict[userID]['userType'] = userType
    userDict[userID]['userName'] = userName
    userDict[userID]['elapsedYear'] = 0
    userDict[userID]['state'] = 'Selected role'
    emit('my_response_userTable', {'type': message['type'], 'name': message['name'], 'no': message['no'], 'userDict': json.dumps(userDict,cls=MyEncoder)}, broadcast=True)

@socketio.event
def userSelected_event():
    global fleets
    global userDict
    global NshipComp
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    global nRegDec
    userID = request.sid
    userNo = userDict[userID]['userNo']
    userType = userDict[userID]['userType']
    userName = userDict[userID]['userName']
    elapsedYear = userDict[userID]['elapsedYear']
    currentYear = elapsedYear + startYear
    fleets['year'][elapsedYear] = currentYear
    if userType == 'Regulator':
        userDict[userID]['state'] = 'Waiting'
        if userDict[userID]['elapsedYear'] == 0:
            join_room('regulator',sid=userID)
            regulatorIDs.append(userID)
            Nregulator += 1
            userDict[userID]['Nregulator'] = Nregulator
            userDict[userID]['NshipComp'] = 0
        if currentYear == regYear[nRegAct]:
            nRegDec += 1
            emit('my_response_regulator_operation', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear'], 'userDict': json.dumps(userDict,cls=MyEncoder), 'regDec': json.dumps(regDec,cls=MyEncoder)})
        else:
            emit('my_response_selected_regulator', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear'], 'userDict': json.dumps(userDict,cls=MyEncoder)})
        if currentYear == regYear[nRegAct]+2:
            nRegAct += 1
    elif userType == 'Shipping Company':
        userDict[userID]['state'] = 'Yearly operation'
        if userDict[userID]['elapsedYear'] == 0:
            join_room('shipComp',sid=userID)
            NshipComp += 1
            userDict[userID]['NshipComp'] = NshipComp
            userDict[userID]['Nregulator'] = 0
            fleets = rs.fleetPreparationFunc(fleets,np.random.choice(initialFleets),NshipComp,startYear,lastYear,0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
        NshipCompTemp = userDict[userID]['NshipComp']
        for keyFleet in range(1,len(fleets[NshipCompTemp])):
            if fleets[NshipCompTemp][keyFleet]['delivery'] <= currentYear and fleets[NshipCompTemp][keyFleet]['tOp'] < tOpSch:
                tOpTemp = fleets[NshipCompTemp][keyFleet]['tOp']
                rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[NshipCompTemp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct])
                fleets[NshipCompTemp][keyFleet]['EEDIref'][tOpTemp], fleets[NshipCompTemp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[NshipCompTemp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                fleets[NshipCompTemp][keyFleet]['MCRM'][tOpTemp], fleets[NshipCompTemp][keyFleet]['PA'][tOpTemp], fleets[NshipCompTemp][keyFleet]['EEDIatt'][tOpTemp], fleets[NshipCompTemp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[NshipCompTemp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[NshipCompTemp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[NshipCompTemp][keyFleet]['Cco2aux'],fleets[NshipCompTemp][keyFleet]['EEDIreq'][tOpTemp],fleets[NshipCompTemp][keyFleet]['WPS'],fleets[NshipCompTemp][keyFleet]['SPS'],fleets[NshipCompTemp][keyFleet]['CCS'])
        emit('my_response_selected_shipComp', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear'], 'fleets': json.dumps(fleets,cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': userDict[userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs,cls=MyEncoder), 'NshipComp': NshipCompTemp, 'userDict': json.dumps(userDict,cls=MyEncoder)})
    
#emit('redirect',{url_for()})
@socketio.event
def regulatorOperation_event(message):
    global nRegAct
    global nRegDec
    regDec['rEEDIreq'][nRegDec,0] = float(message['rEEDIreq1']) / 100
    regDec['rEEDIreq'][nRegDec,1] = float(message['rEEDIreq2']) / 100
    regDec['rEEDIreq'][nRegDec,2] = float(message['rEEDIreq3']) / 100
    regDec['Subsidy'][nRegDec] = float(message['Subsidy']) / 100
    regDec['Ctax'][nRegDec] = float(message['Ctax'])

@socketio.event
def cbs_event(message):
    global fleets
    global userDict
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    userID = request.sid
    userNo = userDict[userID]['userNo']
    userType = userDict[userID]['userType']
    userName = userDict[userID]['userName']
    NshipComp = userDict[userID]['NshipComp']
    currentYear = userDict[userID]['elapsedYear'] + startYear
    for keyFleet in range(1,len(fleets[NshipComp])):
        if fleets[NshipComp][keyFleet]['delivery'] <= currentYear and fleets[NshipComp][keyFleet]['tOp'] < tOpSch:
            fleets[NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
            fleets[NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
            fleets[NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
            tOpTemp = fleets[NshipComp][keyFleet]['tOp']
            rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[NshipComp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct])
            fleets[NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
            fleets[NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[NshipComp][keyFleet]['PA'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[NshipComp][keyFleet]['Cco2aux'],fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[NshipComp][keyFleet]['WPS'],fleets[NshipComp][keyFleet]['SPS'],fleets[NshipComp][keyFleet]['CCS'])
    emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear'], 'fleets': json.dumps(fleets,cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': userDict[userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs,cls=MyEncoder), 'NshipComp': NshipComp})

@socketio.event
def orderChange_event(fuelTypeDict,CAPcntDict,sysDict):
    global fleets
    global userDict
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    orderList = {}
    for keyFleet in range(1,len(sysDict)+1):
        if fuelTypeDict[str(keyFleet)] == 'HFO/Diesel':
            Cco2ship = rs.Cco2Func(parameterFile3,'HFO')
            Cco2aux = rs.Cco2Func(parameterFile3,'Diesel')
        else:
            Cco2ship = rs.Cco2Func(parameterFile3,fuelTypeDict[str(keyFleet)])
            Cco2aux = rs.Cco2Func(parameterFile3,fuelTypeDict[str(keyFleet)])
        wDWT = rs.wDWTFunc(valueDict['kDWT1'],float(CAPcntDict[str(keyFleet)]),valueDict['kDWT2'])
        rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(wDWT,regDec['rEEDIreq'][nRegAct])
        EEDIref, EEDIreq = rs.EEDIreqFunc(valueDict['kEEDI1'],wDWT,valueDict['kEEDI2'],rEEDIreqCurrent)
        _, _, EEDIatt, vDsgnRed = rs.EEDIattFunc(wDWT,valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],Cco2ship,valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],Cco2aux,EEDIreq,int(sysDict[str(keyFleet)]['WPS']),int(sysDict[str(keyFleet)]['SPS']),int(sysDict[str(keyFleet)]['CCS']))
        orderList.setdefault(keyFleet,{})
        orderList[keyFleet]['vDsgnRed'] = vDsgnRed
        orderList[keyFleet]['EEDIreq'] = EEDIreq
        orderList[keyFleet]['EEDIatt'] = EEDIatt
    emit('my_response_orderChange', {'orderList': json.dumps(orderList,cls=MyEncoder)})

@socketio.event
def scrap_event(message):
    global fleets
    global userDict
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    userID = request.sid
    userNo = userDict[userID]['userNo']
    userType = userDict[userID]['userType']
    userName = userDict[userID]['userName']
    NshipComp = userDict[userID]['NshipComp']
    emit('my_response_scrap', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear'], 'fleets': json.dumps(fleets,cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': userDict[userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs,cls=MyEncoder), 'ifScrap': message['val'], 'NshipComp': NshipComp})

@socketio.event
def wpsAtOnce_event(message):
    global fleets
    global userDict
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    userID = request.sid
    userNo = userDict[userID]['userNo']
    userType = userDict[userID]['userType']
    userName = userDict[userID]['userName']
    NshipComp = userDict[userID]['NshipComp']
    currentYear = userDict[userID]['elapsedYear'] + startYear
    for keyFleet in range(1,len(fleets[NshipComp])):
        if fleets[NshipComp][keyFleet]['delivery'] <= currentYear and fleets[NshipComp][keyFleet]['tOp'] < tOpSch:
            fleets[NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
            fleets[NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
            fleets[NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
            tOpTemp = fleets[NshipComp][keyFleet]['tOp']
            rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[NshipComp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct])
            fleets[NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
            fleets[NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[NshipComp][keyFleet]['PA'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[NshipComp][keyFleet]['Cco2aux'],fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[NshipComp][keyFleet]['WPS'],fleets[NshipComp][keyFleet]['SPS'],fleets[NshipComp][keyFleet]['CCS'])
    emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear'], 'fleets': json.dumps(fleets,cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': userDict[userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs,cls=MyEncoder), 'NshipComp': NshipComp})

@socketio.event
def spsAtOnce_event(message):
    global fleets
    global userDict
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    userID = request.sid
    userNo = userDict[userID]['userNo']
    userType = userDict[userID]['userType']
    userName = userDict[userID]['userName']
    NshipComp = userDict[userID]['NshipComp']
    currentYear = userDict[userID]['elapsedYear'] + startYear
    for keyFleet in range(1,len(fleets[NshipComp])):
        if fleets[NshipComp][keyFleet]['delivery'] <= currentYear and fleets[NshipComp][keyFleet]['tOp'] < tOpSch:
            fleets[NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
            fleets[NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
            fleets[NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
            tOpTemp = fleets[NshipComp][keyFleet]['tOp']
            rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[NshipComp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct])
            fleets[NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
            fleets[NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[NshipComp][keyFleet]['PA'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[NshipComp][keyFleet]['Cco2aux'],fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[NshipComp][keyFleet]['WPS'],fleets[NshipComp][keyFleet]['SPS'],fleets[NshipComp][keyFleet]['CCS'])
    emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear'], 'fleets': json.dumps(fleets,cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': userDict[userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs,cls=MyEncoder), 'NshipComp': NshipComp})

@socketio.event
def ccsAtOnce_event(message):
    global fleets
    global userDict
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    userID = request.sid
    userNo = userDict[userID]['userNo']
    userType = userDict[userID]['userType']
    userName = userDict[userID]['userName']
    NshipComp = userDict[userID]['NshipComp']
    currentYear = userDict[userID]['elapsedYear'] + startYear
    for keyFleet in range(1,len(fleets[NshipComp])):
        if fleets[NshipComp][keyFleet]['delivery'] <= currentYear and fleets[NshipComp][keyFleet]['tOp'] < tOpSch:
            fleets[NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
            fleets[NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
            fleets[NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
            tOpTemp = fleets[NshipComp][keyFleet]['tOp']
            rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[NshipComp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct])
            fleets[NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
            fleets[NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[NshipComp][keyFleet]['PA'][tOpTemp], fleets[NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[NshipComp][keyFleet]['Cco2aux'],fleets[NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[NshipComp][keyFleet]['WPS'],fleets[NshipComp][keyFleet]['SPS'],fleets[NshipComp][keyFleet]['CCS'])
    emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear'], 'fleets': json.dumps(fleets,cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': userDict[userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs,cls=MyEncoder), 'NshipComp': NshipComp})

@socketio.event
def speedAtOnce_event(message):
    global fleets
    global userDict
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    userID = request.sid
    userNo = userDict[userID]['userNo']
    userType = userDict[userID]['userType']
    userName = userDict[userID]['userName']
    NshipComp = userDict[userID]['NshipComp']
    emit('my_response_speedAtOnce', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': userDict[userID]['elapsedYear'], 'fleets': json.dumps(fleets,cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': userDict[userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs,cls=MyEncoder), 'speed': message['val'], 'NshipComp': NshipComp})

@socketio.event
def orderList_event(message):
    global fleets
    global userDict
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    userID = request.sid
    userNo = userDict[userID]['userNo']
    userType = userDict[userID]['userType']
    userName = userDict[userID]['userName']
    NshipComp = userDict[userID]['NshipComp']
    if message['fuelType'] == 'HFO/Diesel':
        Cco2ship = rs.Cco2Func(parameterFile3,'HFO')
        Cco2aux = rs.Cco2Func(parameterFile3,'Diesel')
    else:
        Cco2ship = rs.Cco2Func(parameterFile3,message['fuelType'])
        Cco2aux = rs.Cco2Func(parameterFile3,message['fuelType'])
    wDWT = rs.wDWTFunc(valueDict['kDWT1'],float(message['CAPcnt']),valueDict['kDWT2'])
    rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(wDWT,regDec['rEEDIreq'][nRegAct])
    EEDIref, EEDIreq = rs.EEDIreqFunc(valueDict['kEEDI1'],wDWT,valueDict['kEEDI2'],rEEDIreqCurrent)
    _, _, EEDIatt, vDsgnRed = rs.EEDIattFunc(wDWT,valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],Cco2ship,valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],Cco2aux,EEDIreq,int(message['WPS']),int(message['SPS']),int(message['CCS']))
    emit('my_response_orderList', {'vDsgnRed': vDsgnRed, 'EEDIreq': EEDIreq, 'EEDIatt': EEDIatt, 'keyFleet': message['keyFleet'], 'currentYear': userDict[userID]['elapsedYear']+startYear})

@socketio.event
def nextYear_event(fleetDict, orderDict):
    global fleets
    global userDict
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    global sumCta
    userID = request.sid
    userNo = userDict[userID]['userNo']
    userType = userDict[userID]['userType']
    userName = userDict[userID]['userName']
    NshipComp = userDict[userID]['NshipComp']
    elapsedYear = userDict[userID]['elapsedYear']
    userDict[userID]['state'] = 'Viewing results'
    maxCta = 0
    currentYear = elapsedYear + startYear
    for keyFleet in range(1,len(fleets[NshipComp])):
        if fleets[NshipComp][keyFleet]['delivery'] <= currentYear and fleets[NshipComp][keyFleet]['tOp'] < tOpSch:
            if int(fleetDict[str(keyFleet)]['scrap']):
                fleets[NshipComp][keyFleet]['tOp'] = tOpSch
            else:
                tOpTemp = fleets[NshipComp][keyFleet]['tOp']
                fleets[NshipComp][keyFleet]['v'][tOpTemp] = fleetDict[str(keyFleet)]['speed']
                fleets[NshipComp][keyFleet]['d'][tOpTemp] = rs.dFunc(valueDict["Dyear"],valueDict["Hday"],fleets[NshipComp][keyFleet]['v'][tOpTemp],valueDict["Rrun"])
                maxCta += NShipFleet * rs.maxCtaFunc(fleets[NshipComp][keyFleet]['CAPcnt'],fleets[NshipComp][keyFleet]['d'][tOpTemp])
    fleets[NshipComp]['total']['maxCta'][elapsedYear] = maxCta
    sumCta += maxCta
    for order in range(1,len(orderDict)+1):
        if orderDict[str(order)]['fuelType'] == 'HFO/Diesel':
            fleets = rs.orderShipFunc(fleets,NshipComp,'HFO',int(orderDict[str(order)]['WPS']),int(orderDict[str(order)]['SPS']),int(orderDict[str(order)]['CCS']),float(orderDict[str(order)]['CAPcnt']),tOpSch,tbid,0,currentYear,elapsedYear,valueDict,NShipFleet,False,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
        else:
            fleets = rs.orderShipFunc(fleets,NshipComp,orderDict[str(order)]['fuelType'],int(orderDict[str(order)]['WPS']),int(orderDict[str(order)]['SPS']),int(orderDict[str(order)]['CCS']),float(orderDict[str(order)]['CAPcnt']),tOpSch,tbid,0,currentYear,elapsedYear,valueDict,NShipFleet,False,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
    emit('my_response_userTable', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': elapsedYear, 'fleets': json.dumps(fleets,cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': currentYear,  'regulatorIDs': json.dumps(regulatorIDs,cls=MyEncoder), 'userDict': json.dumps(userDict,cls=MyEncoder)}, broadcast=True)
    emit('my_response_nextYear', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': elapsedYear, 'fleets': json.dumps(fleets,cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': currentYear,  'regulatorIDs': json.dumps(regulatorIDs,cls=MyEncoder), 'userDict': json.dumps(userDict,cls=MyEncoder)})

@socketio.event
def yearlyOperation_event():
    global fleets
    global userDict
    global Nregulator
    global tOpSch
    global startYear
    global regulatorIDs
    global regDec
    global nRegAct
    global sumCta
    global figEach
    global figTotal
    userID = request.sid
    userNo = userDict[userID]['userNo']
    userType = userDict[userID]['userType']
    userName = userDict[userID]['userName']
    elapsedYear = userDict[userID]['elapsedYear']
    currentYear = elapsedYear+startYear
    Dtotal = rs.demandScenarioFunc(currentYear,valueDict["kDem1"],valueDict["kDem2"],valueDict["kDem3"],valueDict["kDem4"])
    for userID in userDict.keys():
        NshipComp = userDict[userID]['NshipComp']
        if NshipComp != 0:
            fleets[NshipComp]['total']['demand'][elapsedYear] = Dtotal
            if Dtotal <= valueDict["rDMax"]*sumCta and Dtotal / sumCta > 0.0:
                fleets[NshipComp]['total']['rocc'][elapsedYear] = Dtotal / sumCta
            elif Dtotal > valueDict["rDMax"]*sumCta:
                fleets[NshipComp]['total']['rocc'][elapsedYear] = valueDict["rDMax"]
            fleets = rs.yearlyOperationFunc(fleets,NshipComp,startYear,elapsedYear,NShipFleet,tOpSch,valueDict,regDec['Subsidy'][nRegAct],regDec['Ctax'][nRegAct],parameterFile4)
    # prepare the result figures
    resPath = Path(__file__).parent
    resPath /= 'static/figures'
    shutil.rmtree(resPath)
    os.mkdir(resPath)
    removeList = []
    figWidth = 400
    figHeight = 400
    NshipCompTotal = 0
    for userID in userDict.keys():
        if userDict[userID]['userType'] == 'Shipping Company':
            NshipCompTotal += 1
    keyList = list(fleets[1]['total'].keys())
    #figWidth,figHeight = width/2-50, height/2
    for keyi in keyList:
        if type(fleets[1]['total'][keyi]) is np.ndarray:
            figEach[keyi] = rs.outputAllCompanyAppFunc(fleets,valueDict,startYear,elapsedYear,keyi,unitDict,figWidth/100-1,figHeight/100-1,NshipCompTotal)
            figTotal[keyi] = rs.outputAllCompanyTotalAppFunc(fleets,valueDict,startYear,elapsedYear,keyi,unitDict,figWidth/100-1,figHeight/100-1,NshipCompTotal)
        else:
            removeList.append(keyi)
    for keyi in removeList:
        keyList.remove(keyi)
    emit('my_response_yearlyOperation',{'keyList': keyList, 'figEach': json.dumps(figEach,cls=MyEncoder), 'figTotal': json.dumps(figTotal,cls=MyEncoder)},room='shipComp')
    emit('my_response_yearlyOperation',{'keyList': keyList, 'figEach': json.dumps(figEach,cls=MyEncoder), 'figTotal': json.dumps(figTotal,cls=MyEncoder)},room='regulator')
    for userID in userDict.keys():
        userDict[userID]['elapsedYear'] += 1

@socketio.event
def resultSelect_event():
    global figEach
    global figTotal
    emit('my_response_result',{'figEach': json.dumps(figEach,cls=MyEncoder), 'figTotal': json.dumps(figTotal,cls=MyEncoder)},room='shipComp')



@socketio.event
def my_broadcast_event(message):
    global NshipComp
    NshipComp += 1
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count'], 'nshipcomp': str(NshipComp)},
         broadcast=True)


@socketio.event
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.event
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close_room')
def on_close_room(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         to=message['room'])
    close_room(message['room'])

@socketio.event
def my_room_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         to=message['room'])

@socketio.event
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)

@socketio.event
def my_ping():
    emit('my_pong')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)

'''@app.route('/')
def test():
    title = "User Selection"
    return render_template('userSelection.html', title=title)'''

'''@app.route('/userSelection', methods=['POST', 'GET'])
def userSelection():
    title = "User Selection"
    name = 'hoge'
    global NshipComp
    print(NshipComp)
    return render_template('userSelection.html', name=name, title=title)'''

'''@app.route('/shipCompScrpRfrb', methods=['POST', 'GET'])
def shipCompScrpRfrb():
    title = "Ship Company's Scrap & Refurbish"
    name = 'hoge'
    global NshipComp
    print(NshipComp)
    return render_template('shipCompScrpRfrb.html', name=name, title=title)

@app.route('/userSelected', methods=['POST', 'GET'])
def userSelected():
    title = "User Selected"
    global NshipComp
    global Nregulator
    global fleets
    if request.method == 'POST':
        userType = request.form.get('radio')
        name = request.form.get('name')
        if userType == 'regulator':
            Nregulator += 1
            return render_template('regulator.html', name=name, title=title)
        elif userType == 'shipComp':
            NshipComp += 1
            fleets = rs.fleetPreparationFunc(fleets,np.random.choice(initialFleets),NshipComp,startYear,lastYear,0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
            return render_template('shipCompScrpRfrb.html', name=name, fleets=fleets, NshipComp=NshipComp, Nregulator=Nregulator)
    else:
        return redirect(url_for('user'))'''


if __name__ == '__main__':
    #socketio.run(app, host='0.0.0.0', port=5001, debug=True)
    socketio.run(app, host='0.0.0.0',  port=80, debug=True)

#http://localhost:3000/