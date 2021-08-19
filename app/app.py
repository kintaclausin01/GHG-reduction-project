# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response, session, copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from threading import Lock, current_thread
import time
import json
import numpy as np
import os
import sys
parent_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(parent_dir)
from roleplay import sub2 as rs
from pathlib import Path
import pandas as pd
from scipy import interpolate
import csv
import matplotlib as mpl
import matplotlib.pyplot as plt
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
pathPara = 'app/../parameters/'
#if os.name == 'nt':
#    pathPara = path.replace('app','parameters\\')
#elif os.name == 'posix':
#    pathPara = path.replace('app','parameters/')
parameterFile1 = pathPara+"variableAll.csv"
parameterFile2 = pathPara+"eqLHVship.csv"
parameterFile3 = pathPara+"CO2Eff.csv"
parameterFile4 = pathPara+"unitCostFuel.csv"
parameterFile5 = pathPara+"costShipBasic.csv"
parameterFile6 = pathPara+"initialFleet1.csv"
parameterFile7 = pathPara+"initialFleet2.csv"
parameterFile8 = pathPara+"initialFleet3.csv"
#parameterFile9 = path+decisionListName1+".csv"
#parameterFile10 = path+decisionListName2+".csv"
#parameterFile11 = path+decisionListName3+".csv"
parameterFile12 = pathPara+"eqLHVaux.csv"

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

# prepare regulator decision
nRegAct = {}
nRegDec = {}
regDec = rs.regPreFunc(len(regYear)+1)

NshipComp = {}
Nregulator = {}
userDict = {}
gameDict = {}
fleets = {}
regulatorIDs = {}
sumCta = {}
figEach = {}
figTotal = {}
Ngame = 0

# Routing
@app.route('/')
def index():
    return render_template('userSelection.html', valueDict=valueDict)

@socketio.event
def connect_event():
    userID = request.sid
    userDict.setdefault(userID,{})
    userDict[userID]['Ngame'] = 0
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    #emit('my_response_connect')

@socketio.event
def newGame_event():
    global Ngame
    global gameDict
    global userDict
    global fleets
    Ngame += 1
    fleets.setdefault(Ngame,{})
    fleets[Ngame]['year'] = np.zeros(lastYear-startYear+1)
    figEach.setdefault(Ngame,{})
    figTotal.setdefault(Ngame,{})
    NshipComp[Ngame] = 0
    Nregulator[Ngame] = 0
    sumCta[Ngame] = 0
    regulatorIDs[Ngame] = []
    nRegAct[Ngame] = 0
    nRegDec[Ngame] = 0
    gameDict.setdefault(Ngame,{})
    for userID in userDict.keys():
        if userDict[userID]['Ngame'] == 0:
            gameDict[Ngame].setdefault(userID,{})
            gameDict[Ngame][userID]['userNo'] = len(gameDict[Ngame])
            gameDict[Ngame][userID]['userType'] = 'Not selected'
            gameDict[Ngame][userID]['userName'] = 'None'
            gameDict[Ngame][userID]['elapsedYear'] = 0
            gameDict[Ngame][userID]['state'] = 'Connected'
    emit('my_response_newGame', broadcast=True)

@socketio.event
def userSelection_event(message):
    global Ngame
    global gameDict
    userID = request.sid
    userNo = gameDict[Ngame][userID]['userNo']
    userType = message['type']
    userName = message['name']
    gameDict[Ngame][userID]['userType'] = userType
    gameDict[Ngame][userID]['userName'] = userName
    gameDict[Ngame][userID]['state'] = 'Selected role'
    emit('my_response_userTable', {'type': message['type'], 'name': message['name'], 'no': userNo, 'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)}, broadcast=True)

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
    global Ngame
    global gameDict
    userID = request.sid
    userNo = gameDict[Ngame][userID]['userNo']
    userType = gameDict[Ngame][userID]['userType']
    userName = gameDict[Ngame][userID]['userName']
    elapsedYear = gameDict[Ngame][userID]['elapsedYear']
    currentYear = elapsedYear + startYear
    fleets[Ngame]['year'][elapsedYear] = currentYear
    if userType == 'Regulator':
        gameDict[Ngame][userID]['state'] = 'Waiting'
        if gameDict[Ngame][userID]['elapsedYear'] == 0:
            join_room('regulator',sid=userID)
            regulatorIDs[Ngame].append(userID)
            Nregulator[Ngame] += 1
            gameDict[Ngame][userID]['Nregulator'] = Nregulator[Ngame]
            gameDict[Ngame][userID]['NshipComp'] = 0
        if currentYear == regYear[nRegAct[Ngame]]:
            nRegDec[Ngame] += 1
            emit('my_response_regulator_operation', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][userID]['elapsedYear'], 'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder), 'regDec': json.dumps(regDec,cls=MyEncoder)})
        else:
            emit('my_response_selected_regulator', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][userID]['elapsedYear'], 'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)})
        if currentYear == regYear[nRegAct[Ngame]]+2:
            nRegAct[Ngame] += 1
    elif userType == 'Shipping Company':
        gameDict[Ngame][userID]['state'] = 'Yearly operation'
        if gameDict[Ngame][userID]['elapsedYear'] == 0:
            join_room('shipComp',sid=userID)
            NshipComp[Ngame] += 1
            gameDict[Ngame][userID]['NshipComp'] = NshipComp[Ngame]
            gameDict[Ngame][userID]['Nregulator'] = 0
            fleets[Ngame] = rs.fleetPreparationFunc(fleets[Ngame],np.random.choice(initialFleets),NshipComp[Ngame],startYear,lastYear,0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
        NshipCompTemp = gameDict[Ngame][userID]['NshipComp']
        for keyFleet in range(1,len(fleets[Ngame][NshipCompTemp])):
            if fleets[Ngame][NshipCompTemp][keyFleet]['delivery'] <= currentYear and fleets[Ngame][NshipCompTemp][keyFleet]['tOp'] < tOpSch:
                tOpTemp = fleets[Ngame][NshipCompTemp][keyFleet]['tOp']
                rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[Ngame][NshipCompTemp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct[Ngame]])
                fleets[Ngame][NshipCompTemp][keyFleet]['EEDIref'][tOpTemp], fleets[Ngame][NshipCompTemp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[Ngame][NshipCompTemp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                fleets[Ngame][NshipCompTemp][keyFleet]['MCRM'][tOpTemp], fleets[Ngame][NshipCompTemp][keyFleet]['PA'][tOpTemp], fleets[Ngame][NshipCompTemp][keyFleet]['EEDIatt'][tOpTemp], fleets[Ngame][NshipCompTemp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[Ngame][NshipCompTemp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[Ngame][NshipCompTemp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[Ngame][NshipCompTemp][keyFleet]['Cco2aux'],fleets[Ngame][NshipCompTemp][keyFleet]['EEDIreq'][tOpTemp],fleets[Ngame][NshipCompTemp][keyFleet]['WPS'],fleets[Ngame][NshipCompTemp][keyFleet]['SPS'],fleets[Ngame][NshipCompTemp][keyFleet]['CCS'])
        emit('my_response_selected_shipComp', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][userID]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'NshipComp': NshipCompTemp, 'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)})
    
#emit('redirect',{url_for()})
@socketio.event
def regulatorOperation_event(message):
    global nRegAct
    global nRegDec
    regDec['rEEDIreq'][nRegDec[Ngame],0] = float(message['rEEDIreq1']) / 100
    regDec['rEEDIreq'][nRegDec[Ngame],1] = float(message['rEEDIreq2']) / 100
    regDec['rEEDIreq'][nRegDec[Ngame],2] = float(message['rEEDIreq3']) / 100
    regDec['Subsidy'][nRegDec[Ngame]] = float(message['Subsidy']) / 100
    regDec['Ctax'][nRegDec[Ngame]] = float(message['Ctax'])

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
    global Ngame
    global gameDict
    userID = request.sid
    userNo = gameDict[Ngame][userID]['userNo']
    userType = gameDict[Ngame][userID]['userType']
    userName = gameDict[Ngame][userID]['userName']
    NshipComp = gameDict[Ngame][userID]['NshipComp']
    currentYear = gameDict[Ngame][userID]['elapsedYear'] + startYear
    for keyFleet in range(1,len(fleets[Ngame][NshipComp])):
        if fleets[Ngame][NshipComp][keyFleet]['delivery'] <= currentYear and fleets[Ngame][NshipComp][keyFleet]['tOp'] < tOpSch:
            fleets[Ngame][NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
            fleets[Ngame][NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
            fleets[Ngame][NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
            tOpTemp = fleets[Ngame][NshipComp][keyFleet]['tOp']
            rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct[Ngame]])
            fleets[Ngame][NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
            fleets[Ngame][NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['PA'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2aux'],fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[Ngame][NshipComp][keyFleet]['WPS'],fleets[Ngame][NshipComp][keyFleet]['SPS'],fleets[Ngame][NshipComp][keyFleet]['CCS'])
    emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][userID]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'NshipComp': NshipComp})

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
    global Ngame
    global gameDict
    orderList = {}
    for keyFleet in range(1,len(sysDict)+1):
        if fuelTypeDict[str(keyFleet)] == 'HFO/Diesel':
            Cco2ship = rs.Cco2Func(parameterFile3,'HFO')
            Cco2aux = rs.Cco2Func(parameterFile3,'Diesel')
        else:
            Cco2ship = rs.Cco2Func(parameterFile3,fuelTypeDict[str(keyFleet)])
            Cco2aux = rs.Cco2Func(parameterFile3,fuelTypeDict[str(keyFleet)])
        wDWT = rs.wDWTFunc(valueDict['kDWT1'],float(CAPcntDict[str(keyFleet)]),valueDict['kDWT2'])
        rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(wDWT,regDec['rEEDIreq'][nRegAct[Ngame]])
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
    global Ngame
    global gameDict
    userID = request.sid
    userNo = gameDict[Ngame][userID]['userNo']
    userType = gameDict[Ngame][userID]['userType']
    userName = gameDict[Ngame][userID]['userName']
    NshipComp = gameDict[Ngame][userID]['NshipComp']
    emit('my_response_scrap', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][userID]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'ifScrap': message['val'], 'NshipComp': NshipComp})

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
    global Ngame
    global gameDict
    userID = request.sid
    userNo = gameDict[Ngame][userID]['userNo']
    userType = gameDict[Ngame][userID]['userType']
    userName = gameDict[Ngame][userID]['userName']
    NshipComp = gameDict[Ngame][userID]['NshipComp']
    currentYear = gameDict[Ngame][userID]['elapsedYear'] + startYear
    for keyFleet in range(1,len(fleets[Ngame][NshipComp])):
        if fleets[Ngame][NshipComp][keyFleet]['delivery'] <= currentYear and fleets[Ngame][NshipComp][keyFleet]['tOp'] < tOpSch:
            fleets[Ngame][NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
            fleets[Ngame][NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
            fleets[Ngame][NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
            tOpTemp = fleets[Ngame][NshipComp][keyFleet]['tOp']
            rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct[Ngame]])
            fleets[Ngame][NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
            fleets[Ngame][NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['PA'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2aux'],fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[Ngame][NshipComp][keyFleet]['WPS'],fleets[Ngame][NshipComp][keyFleet]['SPS'],fleets[Ngame][NshipComp][keyFleet]['CCS'])
    emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][userID]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'NshipComp': NshipComp})

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
    global Ngame
    global gameDict
    userID = request.sid
    userNo = gameDict[Ngame][userID]['userNo']
    userType = gameDict[Ngame][userID]['userType']
    userName = gameDict[Ngame][userID]['userName']
    NshipComp = gameDict[Ngame][userID]['NshipComp']
    currentYear = gameDict[Ngame][userID]['elapsedYear'] + startYear
    for keyFleet in range(1,len(fleets[Ngame][NshipComp])):
        if fleets[Ngame][NshipComp][keyFleet]['delivery'] <= currentYear and fleets[Ngame][NshipComp][keyFleet]['tOp'] < tOpSch:
            fleets[Ngame][NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
            fleets[Ngame][NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
            fleets[Ngame][NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
            tOpTemp = fleets[Ngame][NshipComp][keyFleet]['tOp']
            rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct[Ngame]])
            fleets[Ngame][NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
            fleets[Ngame][NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['PA'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2aux'],fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[Ngame][NshipComp][keyFleet]['WPS'],fleets[Ngame][NshipComp][keyFleet]['SPS'],fleets[Ngame][NshipComp][keyFleet]['CCS'])
    emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][userID]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'NshipComp': NshipComp})

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
    global Ngame
    global gameDict
    userID = request.sid
    userNo = gameDict[Ngame][userID]['userNo']
    userType = gameDict[Ngame][userID]['userType']
    userName = gameDict[Ngame][userID]['userName']
    NshipComp = gameDict[Ngame][userID]['NshipComp']
    currentYear = gameDict[Ngame][userID]['elapsedYear'] + startYear
    for keyFleet in range(1,len(fleets[Ngame][NshipComp])):
        if fleets[Ngame][NshipComp][keyFleet]['delivery'] <= currentYear and fleets[Ngame][NshipComp][keyFleet]['tOp'] < tOpSch:
            fleets[Ngame][NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
            fleets[Ngame][NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
            fleets[Ngame][NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
            tOpTemp = fleets[Ngame][NshipComp][keyFleet]['tOp']
            rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],regDec['rEEDIreq'][nRegAct[Ngame]])
            fleets[Ngame][NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
            fleets[Ngame][NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['PA'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2aux'],fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[Ngame][NshipComp][keyFleet]['WPS'],fleets[Ngame][NshipComp][keyFleet]['SPS'],fleets[Ngame][NshipComp][keyFleet]['CCS'])
    emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][userID]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'NshipComp': NshipComp})

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
    global Ngame
    global gameDict
    userID = request.sid
    userNo = gameDict[Ngame][userID]['userNo']
    userType = gameDict[Ngame][userID]['userType']
    userName = gameDict[Ngame][userID]['userName']
    NshipComp = gameDict[Ngame][userID]['NshipComp']
    emit('my_response_speedAtOnce', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][userID]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][userID]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'speed': message['val'], 'NshipComp': NshipComp})

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
    global Ngame
    global gameDict
    userID = request.sid
    userNo = gameDict[Ngame][userID]['userNo']
    userType = gameDict[Ngame][userID]['userType']
    userName = gameDict[Ngame][userID]['userName']
    NshipComp = gameDict[Ngame][userID]['NshipComp']
    if message['fuelType'] == 'HFO/Diesel':
        Cco2ship = rs.Cco2Func(parameterFile3,'HFO')
        Cco2aux = rs.Cco2Func(parameterFile3,'Diesel')
    else:
        Cco2ship = rs.Cco2Func(parameterFile3,message['fuelType'])
        Cco2aux = rs.Cco2Func(parameterFile3,message['fuelType'])
    wDWT = rs.wDWTFunc(valueDict['kDWT1'],float(message['CAPcnt']),valueDict['kDWT2'])
    rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(wDWT,regDec['rEEDIreq'][nRegAct[Ngame]])
    EEDIref, EEDIreq = rs.EEDIreqFunc(valueDict['kEEDI1'],wDWT,valueDict['kEEDI2'],rEEDIreqCurrent)
    _, _, EEDIatt, vDsgnRed = rs.EEDIattFunc(wDWT,valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],Cco2ship,valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],Cco2aux,EEDIreq,int(message['WPS']),int(message['SPS']),int(message['CCS']))
    emit('my_response_orderList', {'vDsgnRed': vDsgnRed, 'EEDIreq': EEDIreq, 'EEDIatt': EEDIatt, 'keyFleet': message['keyFleet'], 'currentYear': gameDict[Ngame][userID]['elapsedYear']+startYear})

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
    global Ngame
    global gameDict
    userID = request.sid
    userNo = gameDict[Ngame][userID]['userNo']
    userType = gameDict[Ngame][userID]['userType']
    userName = gameDict[Ngame][userID]['userName']
    NshipComp = gameDict[Ngame][userID]['NshipComp']
    elapsedYear = gameDict[Ngame][userID]['elapsedYear']
    gameDict[Ngame][userID]['state'] = 'Waiting results'
    maxCta = 0
    currentYear = elapsedYear + startYear
    for keyFleet in range(1,len(fleets[Ngame][NshipComp])):
        if fleets[Ngame][NshipComp][keyFleet]['delivery'] <= currentYear and fleets[Ngame][NshipComp][keyFleet]['tOp'] < tOpSch:
            if int(fleetDict[str(keyFleet)]['scrap']):
                fleets[Ngame][NshipComp][keyFleet]['tOp'] = tOpSch
            else:
                tOpTemp = fleets[Ngame][NshipComp][keyFleet]['tOp']
                fleets[Ngame][NshipComp][keyFleet]['v'][tOpTemp] = fleetDict[str(keyFleet)]['speed']
                fleets[Ngame][NshipComp][keyFleet]['d'][tOpTemp] = rs.dFunc(valueDict["Dyear"],valueDict["Hday"],fleets[Ngame][NshipComp][keyFleet]['v'][tOpTemp],valueDict["Rrun"])
                maxCta += NShipFleet * rs.maxCtaFunc(fleets[Ngame][NshipComp][keyFleet]['CAPcnt'],fleets[Ngame][NshipComp][keyFleet]['d'][tOpTemp])
    fleets[Ngame][NshipComp]['total']['maxCta'][elapsedYear] = maxCta
    sumCta[Ngame] += maxCta
    for order in range(1,len(orderDict)+1):
        if orderDict[str(order)]['fuelType'] == 'HFO/Diesel':
            fleets[Ngame] = rs.orderShipFunc(fleets[Ngame],NshipComp,'HFO',int(orderDict[str(order)]['WPS']),int(orderDict[str(order)]['SPS']),int(orderDict[str(order)]['CCS']),float(orderDict[str(order)]['CAPcnt']),tOpSch,tbid,0,currentYear,elapsedYear,valueDict,NShipFleet,False,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
        else:
            fleets[Ngame] = rs.orderShipFunc(fleets[Ngame],NshipComp,orderDict[str(order)]['fuelType'],int(orderDict[str(order)]['WPS']),int(orderDict[str(order)]['SPS']),int(orderDict[str(order)]['CCS']),float(orderDict[str(order)]['CAPcnt']),tOpSch,tbid,0,currentYear,elapsedYear,valueDict,NShipFleet,False,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
    emit('my_response_userTable', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': elapsedYear, 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': currentYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)}, broadcast=True)
    emit('my_response_nextYear', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': elapsedYear, 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': currentYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)})

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
    global Ngame
    global gameDict
    userID = request.sid
    userNo = gameDict[Ngame][userID]['userNo']
    userType = gameDict[Ngame][userID]['userType']
    userName = gameDict[Ngame][userID]['userName']
    elapsedYear = gameDict[Ngame][userID]['elapsedYear']
    currentYear = elapsedYear+startYear
    Dtotal = rs.demandScenarioFunc(currentYear,valueDict["kDem1"],valueDict["kDem2"],valueDict["kDem3"],valueDict["kDem4"])
    for userID in gameDict[Ngame].keys():
        NshipComp = gameDict[Ngame][userID]['NshipComp']
        if NshipComp != 0:
            fleets[Ngame][NshipComp]['total']['demand'][elapsedYear] = Dtotal
            if Dtotal <= valueDict["rDMax"]*sumCta[Ngame] and Dtotal / sumCta[Ngame] > 0.0:
                fleets[Ngame][NshipComp]['total']['rocc'][elapsedYear] = Dtotal / sumCta[Ngame]
            elif Dtotal > valueDict["rDMax"]*sumCta[Ngame]:
                fleets[Ngame][NshipComp]['total']['rocc'][elapsedYear] = valueDict["rDMax"]
            fleets[Ngame] = rs.yearlyOperationFunc(fleets[Ngame],NshipComp,startYear,elapsedYear,NShipFleet,tOpSch,valueDict,regDec['Subsidy'][nRegAct[Ngame]],regDec['Ctax'][nRegAct[Ngame]],parameterFile4)
    # prepare the result figures
    #resPath = Path(__file__).parent
    resPath = 'roleplay/../app/static'
    shutil.rmtree(resPath)
    os.mkdir(resPath)
    removeList = []
    figWidth = 600
    figHeight = 500
    NshipCompTotal = 0
    for userID in gameDict[Ngame].keys():
        if gameDict[Ngame][userID]['userType'] == 'Shipping Company':
            NshipCompTotal += 1
    keyList = list(fleets[Ngame][1]['total'].keys())
    #figWidth,figHeight = width/2-50, height/2
    for keyi in keyList:
        if type(fleets[Ngame][1]['total'][keyi]) is np.ndarray:
            figEach[Ngame][keyi] = rs.outputAllCompanyAppFunc(fleets[Ngame],valueDict,startYear,elapsedYear,keyi,unitDict,figWidth/100-1,figHeight/100-1,NshipCompTotal)
            figTotal[Ngame][keyi] = rs.outputAllCompanyTotalAppFunc(fleets[Ngame],valueDict,startYear,elapsedYear,keyi,unitDict,figWidth/100-1,figHeight/100-1,NshipCompTotal)
        else:
            removeList.append(keyi)
    for keyi in removeList:
        keyList.remove(keyi)
    emit('my_response_yearlyOperation',{'keyList': keyList, 'figEach': json.dumps(figEach[Ngame],cls=MyEncoder), 'figTotal': json.dumps(figTotal[Ngame],cls=MyEncoder)},room='shipComp')
    emit('my_response_yearlyOperation',{'keyList': keyList, 'figEach': json.dumps(figEach[Ngame],cls=MyEncoder), 'figTotal': json.dumps(figTotal[Ngame],cls=MyEncoder)},room='regulator')
    for userID in gameDict[Ngame].keys():
        gameDict[Ngame][userID]['elapsedYear'] += 1

@socketio.event
def resultSelect_event():
    global figEach
    global figTotal
    global Ngame
    emit('my_response_result',{'figEach': json.dumps(figEach[Ngame],cls=MyEncoder), 'figTotal': json.dumps(figTotal[Ngame],cls=MyEncoder)},room='shipComp')

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
    global userDict
    global Ngame
    print('Client disconnected', request.sid)
    userID = request.sid
    userDict[userID]['Ngame'] = Ngame

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