# -*- coding: utf-8 -*-
from tkinter.constants import N
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
import matplotlib.colors as mcolors
import shutil
import datetime

async_mode = None
thread = None
thread_lock = Lock()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode, ping_timeout=300)

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
NShipFleet = int(valueDict['NShipFleet'])
tbid = int(valueDict['tbid'])
colors = mcolors.get_named_colors_mapping()
colorList = [colors['tomato'],colors['orange'],colors['royalblue'],colors['olivedrab'],colors['magenta'],colors['lightskyblue']]

# prepare fleets ramdomly by initialFleet files
initialFleets = [parameterFile6,parameterFile7,parameterFile8]

# prepare regulator decision
nRegAct = {}
nRegDec = {}
regYear = {}
regDec = {}

NshipComp = {}
Nregulator = {}
userDict = {}
gameDict = {}
fleets = {}
regulatorIDs = {}
sumCta = {}
figTotal = {}
NgameTotal = 0
kDem4 = {}
IMOgoal = {}
lastYear = {}

# Routing
@app.route('/')
def index():
    return render_template('index.html', valueDict=valueDict)

@socketio.event
def connect_event():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    #emit('my_response_connect')

@socketio.event
def login_event(message):
    userID = request.sid
    if message['iflogin'] == 'Create':
        nameExist = False
        for name in userDict.keys():
            if name == message['name']:
                nameExist = True
        if not nameExist:
            userDict.setdefault(message['name'],{})
            userDict[message['name']]['gameID'] = 0
            userDict[message['name']]['password'] = message['pw']
            userDict[message['name']]['userID'] = userID
            userDict[message['name']]['login'] = True
            join_room('loginRoom',sid=userID)
    else:
        nameExist = False
        for name in userDict.keys():
            if name == message['name']:
                if userDict[name]['password'] == message['pw']:
                    userDict[name]['userID'] = userID
                    userDict[name]['login'] = True
                    nameExist = True
                    join_room('loginRoom',sid=userID)
    emit('my_response_login', {'name': message['name'], 'iflogin': message['iflogin'], 'userDict': json.dumps(userDict,cls=MyEncoder), 'exist': nameExist})
    emit('my_response_loginTable', {'userDict': json.dumps(userDict,cls=MyEncoder)}, room='loginRoom')

@socketio.event
def newGame_event(memberDict,gameName,gameSpan):
    global NgameTotal
    global gameDict
    global userDict
    global fleets
    global lastYear
    NgameTotal += 1
    fleets.setdefault(NgameTotal,{})
    lastYear[NgameTotal] = int(gameSpan)+startYear-1
    regYear[NgameTotal] = np.linspace(valueDict['regStart'],lastYear[NgameTotal],int((lastYear[NgameTotal]-valueDict['regStart'])//valueDict['regSpan']+1))
    regDec[NgameTotal] = rs.regPreFunc(len(regYear[NgameTotal])+1)
    fleets[NgameTotal]['year'] = np.zeros(lastYear[NgameTotal]-startYear+1)
    figTotal.setdefault(NgameTotal,{})
    NshipComp[NgameTotal] = 0
    Nregulator[NgameTotal] = 0
    regulatorIDs[NgameTotal] = []
    nRegAct[NgameTotal] = 0
    nRegDec[NgameTotal] = 0
    gameDict.setdefault(NgameTotal,{})
    gameName = 'game'+str(NgameTotal)
    for i,memberNo in enumerate(memberDict.keys()):
        member = memberDict[memberNo]
        userID = userDict[member]['userID']
        leave_room('loginRoom',sid=userID)
        join_room(gameName,sid=userID)
        userDict[member]['gameID'] = NgameTotal
        gameDict[NgameTotal].setdefault(member,{})
        gameDict[NgameTotal][member]['userNo'] = memberNo
        gameDict[NgameTotal][member]['userType'] = 'Not selected'
        gameDict[NgameTotal][member]['userName'] = member
        gameDict[NgameTotal][member]['elapsedYear'] = 0
        gameDict[NgameTotal][member]['status'] = 'Connected'
        sumCta[NgameTotal] = 0
        IMOgoal[NgameTotal] = 0
        if i < len(colorList):
            gameDict[NgameTotal][member]['color'] = colorList[i]
        else:
            gameDict[NgameTotal][member]['color'] = colors['black']
    emit('my_response_newGame', room=gameName)

@socketio.event
def userSelection_event(message):
    global userDict
    global gameDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            userType = message['type']
            userName = member
            gameDict[Ngame][member]['userType'] = userType
            gameDict[Ngame][member]['userName'] = userName
            gameDict[Ngame][member]['status'] = 'Role Selected'
    emit('my_response_userTable', {'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)}, room=gameName)

@socketio.event
def cbGameSelect_event(cbDict):
    userID = request.sid
    emit('my_response_cbGameSelect', {'cbDict': json.dumps(cbDict,cls=MyEncoder)}, room='loginRoom', skip_sid=userID)

@socketio.event
def userSelected_event():
    global fleets
    global userDict
    global NshipComp
    global Nregulator
    global regulatorIDs
    global regYear
    global regDec
    global nRegAct
    global nRegDec
    global gameDict
    global lastYear
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            userType = gameDict[Ngame][member]['userType']
            userName = gameDict[Ngame][member]['userName']
            userNo = gameDict[Ngame][member]['userNo']
            elapsedYear = gameDict[Ngame][member]['elapsedYear']
            currentYear = elapsedYear + startYear
            if currentYear <= lastYear[Ngame]:
                fleets[Ngame]['year'][elapsedYear] = currentYear
                if currentYear == regYear[NgameTotal][nRegAct[Ngame]]+2:
                    nRegAct[Ngame] += 1
                if userType == 'Regulator':
                    if gameDict[Ngame][member]['elapsedYear'] == 0:
                        regulatorIDs[Ngame].append(member)
                        Nregulator[Ngame] += 1
                        gameDict[Ngame][member]['Nregulator'] = Nregulator[Ngame]
                        gameDict[Ngame][member]['NshipComp'] = 0
                    if currentYear == regYear[NgameTotal][nRegAct[Ngame]]:
                        nRegDec[Ngame] += 1
                        gameDict[Ngame][member]['status'] = 'Deciding regulation'
                        emit('my_response_regulator_operation', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][member]['elapsedYear'], 'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder), 'regDec': json.dumps(regDec[Ngame],cls=MyEncoder)})
                    else:
                        gameDict[Ngame][member]['status'] = 'Waiting shipping companies'
                        emit('my_response_selected_regulator', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][member]['elapsedYear'], 'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)})
                        emit('my_response_nextYear', {'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)})
                    emit('my_response_userTable', {'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)}, room=gameName)
                elif userType == 'Shipping Company':
                    gameDict[Ngame][member]['status'] = 'Yearly operation'
                    if gameDict[Ngame][member]['elapsedYear'] == 0:
                        NshipComp[Ngame] += 1
                        gameDict[Ngame][member]['NshipComp'] = NshipComp[Ngame]
                        gameDict[Ngame][member]['Nregulator'] = 0
                        fleets[Ngame] = rs.fleetPreparationFunc(fleets[Ngame],np.random.choice(initialFleets),NshipComp[Ngame],startYear,lastYear[NgameTotal],0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
                    NshipCompTemp = gameDict[Ngame][member]['NshipComp']
                    for keyFleet in range(1,len(fleets[Ngame][NshipCompTemp])):
                        if fleets[Ngame][NshipCompTemp][keyFleet]['delivery'] <= currentYear and fleets[Ngame][NshipCompTemp][keyFleet]['tOp'] < tOpSch:
                            tOpTemp = fleets[Ngame][NshipCompTemp][keyFleet]['tOp']
                            rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[Ngame][NshipCompTemp][keyFleet]['wDWT'],regDec[Ngame]['rEEDIreq'][nRegAct[Ngame]])
                            fleets[Ngame][NshipCompTemp][keyFleet]['EEDIref'][tOpTemp], fleets[Ngame][NshipCompTemp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[Ngame][NshipCompTemp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                            fleets[Ngame][NshipCompTemp][keyFleet]['MCRM'][tOpTemp], fleets[Ngame][NshipCompTemp][keyFleet]['PA'][tOpTemp], fleets[Ngame][NshipCompTemp][keyFleet]['EEDIatt'][tOpTemp], fleets[Ngame][NshipCompTemp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[Ngame][NshipCompTemp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[Ngame][NshipCompTemp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[Ngame][NshipCompTemp][keyFleet]['Cco2aux'],fleets[Ngame][NshipCompTemp][keyFleet]['EEDIreq'][tOpTemp],fleets[Ngame][NshipCompTemp][keyFleet]['WPS'],fleets[Ngame][NshipCompTemp][keyFleet]['SPS'],fleets[Ngame][NshipCompTemp][keyFleet]['CCS'])
                    emit('my_response_userTable', {'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)}, room=gameName)
                    emit('my_response_selected_shipComp', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][member]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][member]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'NshipComp': NshipCompTemp, 'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder), 'lastYear': lastYear[Ngame]})
            else:
                userDict[member]['gameID'] = 0
                leave_room(gameName,sid=userID)
                join_room('loginRoom',sid=userID)
                emit('my_response_login', {'name': member, 'iflogin': True, 'userDict': json.dumps(userDict,cls=MyEncoder), 'exist': True})
                emit('my_response_loginTable', {'userDict': json.dumps(userDict,cls=MyEncoder)}, room='loginRoom')
    
@socketio.event
def regulatorOperation_event(message):
    global nRegAct
    global nRegDec
    global gameDict
    global userDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            regDec[Ngame]['rEEDIreq'][nRegDec[Ngame],0] = float(message['rEEDIreq1']) / 100
            regDec[Ngame]['rEEDIreq'][nRegDec[Ngame],1] = float(message['rEEDIreq2']) / 100
            regDec[Ngame]['rEEDIreq'][nRegDec[Ngame],2] = float(message['rEEDIreq3']) / 100
            regDec[Ngame]['Subsidy'][nRegDec[Ngame]] = float(message['Subsidy']) / 100
            regDec[Ngame]['Ctax'][nRegDec[Ngame]] = float(message['Ctax'])
            gameDict[Ngame][member]['status'] = 'Waiting shipping companies'
            emit('my_response_userTable', {'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)}, room=gameName)
            emit('my_response_nextYear', {'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)})

@socketio.event
def addOrder_event():
    global gameDict
    global userDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            elapsedYear = gameDict[Ngame][member]['elapsedYear']
            currentYear = elapsedYear + startYear
            emit('my_response_addOrder', {'currentYear': currentYear})

@socketio.event
def cbs_event(message):
    global fleets
    global userDict
    global Nregulator
    global regulatorIDs
    global regDec
    global nRegAct
    global gameDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            userType = gameDict[Ngame][member]['userType']
            userName = gameDict[Ngame][member]['userName']
            userNo = gameDict[Ngame][member]['userNo']
            NshipComp = gameDict[Ngame][member]['NshipComp']
            currentYear = gameDict[Ngame][member]['elapsedYear'] + startYear
            for keyFleet in range(1,len(fleets[Ngame][NshipComp])):
                if fleets[Ngame][NshipComp][keyFleet]['delivery'] <= currentYear and fleets[Ngame][NshipComp][keyFleet]['tOp'] < tOpSch:
                    fleets[Ngame][NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
                    fleets[Ngame][NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
                    fleets[Ngame][NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
                    tOpTemp = fleets[Ngame][NshipComp][keyFleet]['tOp']
                    rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],regDec[Ngame]['rEEDIreq'][nRegAct[Ngame]])
                    fleets[Ngame][NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                    fleets[Ngame][NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['PA'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2aux'],fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[Ngame][NshipComp][keyFleet]['WPS'],fleets[Ngame][NshipComp][keyFleet]['SPS'],fleets[Ngame][NshipComp][keyFleet]['CCS'])
            emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][member]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][member]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'NshipComp': NshipComp})

@socketio.event
def orderChange_event(fuelTypeDict,CAPcntDict,sysDict):
    global fleets
    global userDict
    global Nregulator
    global regulatorIDs
    global regDec
    global nRegAct
    global gameDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            orderList = {}
            for keyFleet in range(1,len(sysDict)+1):
                if fuelTypeDict[str(keyFleet)] == 'HFO/Diesel':
                    Cco2ship = rs.Cco2Func(parameterFile3,'HFO')
                    Cco2aux = rs.Cco2Func(parameterFile3,'Diesel')
                else:
                    Cco2ship = rs.Cco2Func(parameterFile3,fuelTypeDict[str(keyFleet)])
                    Cco2aux = rs.Cco2Func(parameterFile3,fuelTypeDict[str(keyFleet)])
                wDWT = rs.wDWTFunc(valueDict['kDWT1'],float(CAPcntDict[str(keyFleet)]),valueDict['kDWT2'])
                rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(wDWT,regDec[Ngame]['rEEDIreq'][nRegAct[Ngame]])
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
    global regulatorIDs
    global regDec
    global nRegAct
    global gameDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            userType = gameDict[Ngame][member]['userType']
            userName = gameDict[Ngame][member]['userName']
            userNo = gameDict[Ngame][member]['userNo']
            NshipComp = gameDict[Ngame][member]['NshipComp']
            emit('my_response_scrap', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][member]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][member]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'ifScrap': message['val'], 'NshipComp': NshipComp})

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
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            userType = gameDict[Ngame][member]['userType']
            userName = gameDict[Ngame][member]['userName']
            userNo = gameDict[Ngame][member]['userNo']
            NshipComp = gameDict[Ngame][member]['NshipComp']
            currentYear = gameDict[Ngame][member]['elapsedYear'] + startYear
            for keyFleet in range(1,len(fleets[Ngame][NshipComp])):
                if fleets[Ngame][NshipComp][keyFleet]['delivery'] <= currentYear and fleets[Ngame][NshipComp][keyFleet]['tOp'] < tOpSch:
                    fleets[Ngame][NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
                    fleets[Ngame][NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
                    fleets[Ngame][NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
                    tOpTemp = fleets[Ngame][NshipComp][keyFleet]['tOp']
                    rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],regDec[Ngame]['rEEDIreq'][nRegAct[Ngame]])
                    fleets[Ngame][NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                    fleets[Ngame][NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['PA'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2aux'],fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[Ngame][NshipComp][keyFleet]['WPS'],fleets[Ngame][NshipComp][keyFleet]['SPS'],fleets[Ngame][NshipComp][keyFleet]['CCS'])
            emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][member]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][member]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'NshipComp': NshipComp})

@socketio.event
def spsAtOnce_event(message):
    global fleets
    global userDict
    global Nregulator
    global regulatorIDs
    global regDec
    global nRegAct
    global gameDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            userType = gameDict[Ngame][member]['userType']
            userName = gameDict[Ngame][member]['userName']
            userNo = gameDict[Ngame][member]['userNo']
            NshipComp = gameDict[Ngame][member]['NshipComp']
            currentYear = gameDict[Ngame][member]['elapsedYear'] + startYear
            for keyFleet in range(1,len(fleets[Ngame][NshipComp])):
                if fleets[Ngame][NshipComp][keyFleet]['delivery'] <= currentYear and fleets[Ngame][NshipComp][keyFleet]['tOp'] < tOpSch:
                    fleets[Ngame][NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
                    fleets[Ngame][NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
                    fleets[Ngame][NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
                    tOpTemp = fleets[Ngame][NshipComp][keyFleet]['tOp']
                    rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],regDec[Ngame]['rEEDIreq'][nRegAct[Ngame]])
                    fleets[Ngame][NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                    fleets[Ngame][NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['PA'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2aux'],fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[Ngame][NshipComp][keyFleet]['WPS'],fleets[Ngame][NshipComp][keyFleet]['SPS'],fleets[Ngame][NshipComp][keyFleet]['CCS'])
            emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][member]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][member]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'NshipComp': NshipComp})

@socketio.event
def ccsAtOnce_event(message):
    global fleets
    global userDict
    global Nregulator
    global regulatorIDs
    global regDec
    global nRegAct
    global gameDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            userType = gameDict[Ngame][member]['userType']
            userName = gameDict[Ngame][member]['userName']
            userNo = gameDict[Ngame][member]['userNo']
            NshipComp = gameDict[Ngame][member]['NshipComp']
            currentYear = gameDict[Ngame][member]['elapsedYear'] + startYear
            for keyFleet in range(1,len(fleets[Ngame][NshipComp])):
                if fleets[Ngame][NshipComp][keyFleet]['delivery'] <= currentYear and fleets[Ngame][NshipComp][keyFleet]['tOp'] < tOpSch:
                    fleets[Ngame][NshipComp][keyFleet]['WPS'] = message[str(keyFleet)]['WPS']
                    fleets[Ngame][NshipComp][keyFleet]['SPS'] = message[str(keyFleet)]['SPS']
                    fleets[Ngame][NshipComp][keyFleet]['CCS'] = message[str(keyFleet)]['CCS']
                    tOpTemp = fleets[Ngame][NshipComp][keyFleet]['tOp']
                    rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],regDec[Ngame]['rEEDIreq'][nRegAct[Ngame]])
                    fleets[Ngame][NshipComp][keyFleet]['EEDIref'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp] = rs.EEDIreqFunc(valueDict['kEEDI1'],fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                    fleets[Ngame][NshipComp][keyFleet]['MCRM'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['PA'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['EEDIatt'][tOpTemp], fleets[Ngame][NshipComp][keyFleet]['vDsgnRed'][tOpTemp] = rs.EEDIattFunc(fleets[Ngame][NshipComp][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleets[Ngame][NshipComp][keyFleet]['Cco2aux'],fleets[Ngame][NshipComp][keyFleet]['EEDIreq'][tOpTemp],fleets[Ngame][NshipComp][keyFleet]['WPS'],fleets[Ngame][NshipComp][keyFleet]['SPS'],fleets[Ngame][NshipComp][keyFleet]['CCS'])
            emit('my_response_refurbish', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][member]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][member]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'NshipComp': NshipComp})

@socketio.event
def speedAtOnce_event(message):
    global fleets
    global userDict
    global Nregulator
    global regulatorIDs
    global regDec
    global nRegAct
    global gameDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            userType = gameDict[Ngame][member]['userType']
            userName = gameDict[Ngame][member]['userName']
            userNo = gameDict[Ngame][member]['userNo']
            NshipComp = gameDict[Ngame][member]['NshipComp']
    emit('my_response_speedAtOnce', {'type': userType, 'name': userName, 'no': userNo, 'elpsyear': gameDict[Ngame][member]['elapsedYear'], 'fleets': json.dumps(fleets[Ngame],cls=MyEncoder), 'tOpSch': tOpSch, 'currentYear': gameDict[Ngame][member]['elapsedYear']+startYear,  'regulatorIDs': json.dumps(regulatorIDs[Ngame],cls=MyEncoder), 'speed': message['val'], 'NshipComp': NshipComp})

@socketio.event
def orderList_event(message):
    global fleets
    global userDict
    global Nregulator
    global regulatorIDs
    global regDec
    global nRegAct
    global gameDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            userType = gameDict[Ngame][member]['userType']
            userName = gameDict[Ngame][member]['userName']
            userNo = gameDict[Ngame][member]['userNo']
            NshipComp = gameDict[Ngame][member]['NshipComp']
            if message['fuelType'] == 'HFO/Diesel':
                Cco2ship = rs.Cco2Func(parameterFile3,'HFO')
                Cco2aux = rs.Cco2Func(parameterFile3,'Diesel')
            else:
                Cco2ship = rs.Cco2Func(parameterFile3,message['fuelType'])
                Cco2aux = rs.Cco2Func(parameterFile3,message['fuelType'])
            wDWT = rs.wDWTFunc(valueDict['kDWT1'],float(message['CAPcnt']),valueDict['kDWT2'])
            rEEDIreqCurrent = rs.rEEDIreqCurrentFunc(wDWT,regDec[Ngame]['rEEDIreq'][nRegAct[Ngame]])
            EEDIref, EEDIreq = rs.EEDIreqFunc(valueDict['kEEDI1'],wDWT,valueDict['kEEDI2'],rEEDIreqCurrent)
            _, _, EEDIatt, vDsgnRed = rs.EEDIattFunc(wDWT,valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],Cco2ship,valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],Cco2aux,EEDIreq,int(message['WPS']),int(message['SPS']),int(message['CCS']))
            emit('my_response_orderList', {'vDsgnRed': vDsgnRed, 'EEDIreq': EEDIreq, 'EEDIatt': EEDIatt, 'keyFleet': message['keyFleet'], 'currentYear': gameDict[Ngame][member]['elapsedYear']+startYear})

@socketio.event
def nextYear_event(fleetDict, orderDict):
    global fleets
    global userDict
    global Nregulator
    global regulatorIDs
    global regDec
    global nRegAct
    global sumCta
    global gameDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            userType = gameDict[Ngame][member]['userType']
            userName = gameDict[Ngame][member]['userName']
            userNo = gameDict[Ngame][member]['userNo']
            NshipComp = gameDict[Ngame][member]['NshipComp']
            elapsedYear = gameDict[Ngame][member]['elapsedYear']
            gameDict[Ngame][member]['status'] = 'Waiting results'
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
            if currentYear <= lastYear[Ngame]-2:
                for order in range(1,len(orderDict)+1):
                    if orderDict[str(order)]['fuelType'] == 'HFO/Diesel':
                        fleets[Ngame] = rs.orderShipFunc(fleets[Ngame],NshipComp,'HFO',int(orderDict[str(order)]['WPS']),int(orderDict[str(order)]['SPS']),int(orderDict[str(order)]['CCS']),float(orderDict[str(order)]['CAPcnt']),tOpSch,tbid,0,currentYear,elapsedYear,valueDict,NShipFleet,False,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
                    else:
                        fleets[Ngame] = rs.orderShipFunc(fleets[Ngame],NshipComp,orderDict[str(order)]['fuelType'],int(orderDict[str(order)]['WPS']),int(orderDict[str(order)]['SPS']),int(orderDict[str(order)]['CCS']),float(orderDict[str(order)]['CAPcnt']),tOpSch,tbid,0,currentYear,elapsedYear,valueDict,NShipFleet,False,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
            emit('my_response_userTable', {'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)}, room=gameName)
            emit('my_response_nextYear', {'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)})

@socketio.event
def yearlyOperation_event():
    global fleets
    global userDict
    global Nregulator
    global regulatorIDs
    global regDec
    global nRegAct
    global sumCta
    global figTotal
    global gameDict
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
            for gameMember in gameDict[Ngame].keys():
                gameDict[Ngame][gameMember]['status'] = 'Viewing results'
            elapsedYear = gameDict[Ngame][member]['elapsedYear']
            currentYear = elapsedYear+startYear
            if elapsedYear == 0:
                Dtotal = sumCta[Ngame] * valueDict['rDMax']
                kDem4[Ngame] = rs.demandInitialFunc(Dtotal,startYear,valueDict["kDem1"],valueDict["kDem2"],valueDict['kDem3'])
            else:
                Dtotal = rs.demandScenarioFunc(currentYear,valueDict["kDem1"],valueDict["kDem2"],valueDict["kDem3"],kDem4[Ngame])
            for gameMember in gameDict[Ngame].keys():
                NshipComp = gameDict[Ngame][gameMember]['NshipComp']
                if NshipComp != 0:
                    fleets[Ngame][NshipComp]['total']['demand'][elapsedYear] = Dtotal
                    if Dtotal <= valueDict["rDMax"]*sumCta[Ngame] and Dtotal / sumCta[Ngame] > 0.0:
                        fleets[Ngame][NshipComp]['total']['rocc'][elapsedYear] = Dtotal / sumCta[Ngame]
                    elif Dtotal > valueDict["rDMax"]*sumCta[Ngame]:
                        fleets[Ngame][NshipComp]['total']['rocc'][elapsedYear] = valueDict["rDMax"]
                    fleets[Ngame] = rs.yearlyOperationFunc(fleets[Ngame],NshipComp,startYear,elapsedYear,NShipFleet,tOpSch,valueDict,regDec[Ngame]['Subsidy'][nRegAct[Ngame]],regDec[Ngame]['Ctax'][nRegAct[Ngame]],parameterFile4)
                    if elapsedYear == 0:
                        IMOgoal[Ngame] += fleets[Ngame][NshipComp]['total']['g'][elapsedYear]/2
            # prepare the result figures
            #resPath = Path(__file__).parent
            resPath = 'roleplay/../app/static'
            shutil.rmtree(resPath)
            os.mkdir(resPath)
            removeList = []
            figWidth = 600
            figHeight = 500
            #keyList = list(fleets[Ngame][1]['total'].keys())
            keyList = ['profit','g','Idx','sale','costAll','maxCta']
            for keyi in keyList:
                if type(fleets[Ngame][1]['total'][keyi]) is np.ndarray:
                    figTotal[Ngame][keyi] = rs.outputAllCompanyTotalAppLimitedFunc(fleets[Ngame],gameDict[Ngame],valueDict,kDem4[Ngame],IMOgoal[Ngame],startYear,elapsedYear,lastYear[Ngame],keyi,unitDict,figWidth/100-1,figHeight/100-1)
                else:
                    removeList.append(keyi)
            for keyi in removeList:
                keyList.remove(keyi)
            emit('my_response_yearlyOperation',{'currentYear': currentYear, 'keyList': keyList, 'figTotal': json.dumps(figTotal[Ngame],cls=MyEncoder), 'lastYear': lastYear[Ngame]},room=gameName)
            emit('my_response_userTable', {'gameDict': json.dumps(gameDict[Ngame],cls=MyEncoder)}, room=gameName)
            for gameMember in gameDict[Ngame].keys():
                gameDict[Ngame][gameMember]['elapsedYear'] += 1
                sumCta[Ngame] = 0

@socketio.event
def resultSelect_event():
    global figTotal
    userID = request.sid
    for member in userDict.keys():
        if userDict[member]['userID'] == userID:
            Ngame = userDict[member]['gameID']
            gameName = 'game'+str(Ngame)
    emit('my_response_result',{'figTotal': json.dumps(figTotal[Ngame],cls=MyEncoder)},room=gameName)

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
    for name in userDict.keys():
        if userDict[name]['userID'] == userID:
            userDict[name]['login'] = False
            userDict[name]['gameID'] = 0

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
            fleets = rs.fleetPreparationFunc(fleets,np.random.choice(initialFleets),NshipComp,startYear,lastYear[NgameTotal],0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
            return render_template('shipCompScrpRfrb.html', name=name, fleets=fleets, NshipComp=NshipComp, Nregulator=Nregulator)
    else:
        return redirect(url_for('user'))'''


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0',  port=3000, debug=True)

#http://localhost:3000/