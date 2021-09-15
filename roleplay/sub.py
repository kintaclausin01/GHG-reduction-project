import numpy as np
import pandas as pd
from scipy import interpolate
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import ScalarFormatter
from tkinter import *
from tkinter import ttk
import sys
import os
import random

def readinput(filename):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("variableAll")
    #display(csv_input[0:24])
    #print("\n")
    symbol = csv_input['Symbol']
    value = csv_input['Value']
    unit = csv_input['Unit']
    valueDict = {}
    unitDict = {}
    for i, j, k in zip(symbol, value, unit):
        valueDict[i] = float(j)
        unitDict[i] = str(k)
    return csv_input, valueDict, unitDict

def CeqLHVFunc(filename,fuelName):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("CeqLHV")
    #display(csv_input)
    #print("\n")
    fuelType = csv_input['Fuel type']
    CeqLHV = csv_input['CeqLHV']
    fuelDict = {}
    for i, j in zip(fuelType, CeqLHV):
        fuelDict[i] = float(j)
    return fuelDict[fuelName]

def Cco2Func(filename,fuelName):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("Cco2")
    #display(csv_input)
    #print("\n")
    fuelType = csv_input['Fuel type']
    Cco2 = csv_input['Cco2']
    Cco2Dict = {}
    for i, j in zip(fuelType, Cco2):
        Cco2Dict[i] = float(j)
    return Cco2Dict[fuelName]

def initialFleetFunc(filename):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    year = csv_input['Year']
    TEU = csv_input['TEU']
    iniFleetDict = {}
    k = 0
    for i, j in zip(year, TEU):
        iniFleetDict.setdefault(k,{})
        iniFleetDict[k]['year'] = int(i)
        iniFleetDict[k]['TEU'] = float(j)
        k += 1
    return iniFleetDict

def decisionListFunc(filename):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",").fillna(0)
    Year = csv_input['Year']
    Order = csv_input['Order']
    fuelType = csv_input['Fuel type']
    WPS = csv_input['WPS']
    SPS = csv_input['SPS']
    CCS = csv_input['CCS']
    CAP = csv_input['CAP']
    Speed = csv_input['Speed']
    valueDict = {}
    for i, j, k, l, m, n, o, p in zip(Year, Order, fuelType, WPS, SPS, CCS, CAP, Speed):
        valueDict.setdefault(int(i),{})
        valueDict[int(i)]['Order'] = int(j)
        valueDict[int(i)]['fuelType'] = k
        valueDict[int(i)]['WPS'] = int(l)
        valueDict[int(i)]['SPS'] = int(m)
        valueDict[int(i)]['CCS'] = int(n)
        valueDict[int(i)]['CAP'] = float(o)
        valueDict[int(i)]['Speed'] = float(p)
    return valueDict

def fleetPreparationFunc(fleetAll,initialFleetFile,numCompany,startYear,lastYear,tOpSch,tbid,parameterFile2,parameterFile3,parameterFile5):
    fleetAll.setdefault(numCompany,{})
    fleetAll[numCompany].setdefault('total',{})
    fleetAll[numCompany]['total']['S'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['g'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['gTilde'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['dcostShippingTilde'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['cta'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['overDi'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['costShipAll'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['costFuelAll'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['costAll'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['maxCta'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['rocc'] = np.zeros(lastYear-startYear+1)

    initialFleets = initialFleetFunc(initialFleetFile)

    for i in range(len(initialFleets)):
        orderYear = initialFleets[i]['year'] - tbid
        iniT = startYear - initialFleets[i]['year']
        iniCAPcnt = initialFleets[i]['TEU']
        fleetAll = orderShipFunc(fleetAll,numCompany,'HFO',0,0,0,iniCAPcnt,tOpSch,tbid,iniT,orderYear,parameterFile2,parameterFile3,parameterFile5)
    return fleetAll

def unitCostFuelFunc(filename,fuelName,year):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("unitCostFuel")
    #display(csv_input)
    #print("\n")
    measureYear = np.array(csv_input['Year'],dtype='float64')
    measureHFO = np.array(csv_input['HFO'],dtype='float64')
    measure = np.array(csv_input[fuelName],dtype='float64')
    fittedHFO = interpolate.interp1d(measureYear, measureHFO)
    fitted = interpolate.interp1d(measureYear, measure)
    if year >= 2020:
        interp = fitted(year)
        interpHFO = fittedHFO(year)
    else:
        interp = measure[0]
        interpHFO = measureHFO[0]
    return interp, interpHFO

def rShipBasicFunc(filename,fuelName,CAPcnt):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("CeqLHV")
    #display(csv_input)
    #print("\n")
    fuelType = csv_input['Fuel type']
    rShipBasic = csv_input['rShipBasic']
    fuelDict = {}
    for i, j in zip(fuelType, rShipBasic):
        fuelDict[i] = float(j)
    return fuelDict[fuelName]

def wDWTFunc(kDWT1,CAPcnt,kDWT2):
    wDWT = kDWT1*CAPcnt+kDWT2
    return wDWT

def wFLDFunc(kFLD1,wDWT,kFLD2):
    wFLD = kFLD1*wDWT+kFLD2
    return wFLD

def dFunc(Dyear,Hday,v,Rrun):
    d = Dyear*Hday*v*Rrun
    return d

def fShipFunc(kShip1,kShip2,wDWT,wFLD,rocc,CNM2km,v,d,rWPS,windPr,CeqLHV):
    fShipORG = (kShip1/1000)*(wFLD-(1-kShip2*rocc)*wDWT)*(wFLD**(-1/3))*((CNM2km*v)**2)*CNM2km*d
    if windPr:
        fShip = CeqLHV*fShipORG*(1-rWPS)
    else:
        fShip = CeqLHV*fShipORG
    return fShipORG, fShip

def fAuxFunc(Dyear,Hday,Rrun,kAux1,kAux2,wDWT,rSPS,solar):
    fAuxORG = Dyear*Hday*Rrun*(kAux1+kAux2*wDWT)/1000
    if solar:
        fAux = fAuxORG*(1-rSPS)
    else:
        fAux = fAuxORG
    return fAuxORG, fAux

def gFunc(Cco2,fShip,Cco2DF,fAux,rCCS,CCS):
    gORG = Cco2*fShip+Cco2DF*fAux
    if CCS:
        g = gORG*(1-rCCS)
    else:
        g = gORG
    return gORG, g

def maxCtaFunc(CAPcnt,d):
    maxCta = CAPcnt*d
    return maxCta

def ctaFunc(CAPcnt,rocc,d):
    cta = CAPcnt*rocc*d
    return cta

def costFuelShipFunc(unitCostFuelHFO, unitCostFuel, fShipORG, fShip):
    costFuelShipORG = unitCostFuelHFO*fShipORG
    costFuelShip = unitCostFuel*fShip
    dcostFuelShip = costFuelShip - costFuelShipORG
    return costFuelShipORG, costFuelShip, dcostFuelShip

def costFuelAuxFunc(unitCostDF, fAuxORG, fAux):
    costFuelAuxORG = unitCostDF*fAuxORG
    costFuelAux = unitCostDF*fAux
    dcostFuelAux = costFuelAux - costFuelAuxORG
    return costFuelAuxORG, costFuelAux, dcostFuelAux

def costFuelAllFunc(costFuelShip, costFuelAux, dcostFuelShip, dcostFuelAux):
    costFuelAll = costFuelShip+costFuelAux
    dcostFuelAll = dcostFuelShip+dcostFuelAux
    return costFuelAll, dcostFuelAll

def costShipFunc(kShipBasic1, CAPcnt, kShipBasic2, rShipBasic, dcostWPS, dcostSPS, dcostCCS, flagWPS, flagSPS, flagCCS):
    costShipBasicHFO = kShipBasic1 * CAPcnt + kShipBasic2
    costShipBasic = rShipBasic * costShipBasicHFO
    cAdditionalEquipment = 1
    if flagWPS:
        cAdditionalEquipment += dcostWPS
    elif flagSPS:
        cAdditionalEquipment += dcostSPS
    elif flagCCS:
        cAdditionalEquipment += dcostCCS
    costShipAll = cAdditionalEquipment * costShipBasic
    return costShipBasicHFO, costShipBasic, costShipAll

def additionalShippingFeeFunc(tOp, tOpSch, dcostFuelAll, costShipAll, costShipBasicHFO):
    if tOp <= tOpSch:
        dcostShipping = dcostFuelAll + (costShipAll-costShipBasicHFO)/tOpSch
    else:
        dcostShipping = dcostFuelAll
    return dcostShipping

def demandScenarioFunc(year,kDem1,kDem2,kDem3,kDem4):
    Di = (kDem1*year**2 + kDem2*year + kDem3)*1000000000/kDem4
    return Di

def orderShipFunc(fleetAll,numCompany,fuelName,WPS,SPS,CCS,CAPcnt,tOpSch,tbid,iniT,currentYear,parameterFile2,parameterFile3,parameterFile5):
    NumFleet = len(fleetAll[numCompany])
    fleetAll[numCompany].setdefault(NumFleet,{})
    fleetAll[numCompany][NumFleet]['fuelName'] = fuelName
    fleetAll[numCompany][NumFleet]['WPS'] = WPS
    fleetAll[numCompany][NumFleet]['SPS'] = SPS
    fleetAll[numCompany][NumFleet]['CCS'] = CCS
    fleetAll[numCompany][NumFleet]['CAPcnt'] = float(CAPcnt)
    fleetAll[numCompany][NumFleet]['CeqLHV'] = CeqLHVFunc(parameterFile2,fleetAll[numCompany][NumFleet]['fuelName'])
    fleetAll[numCompany][NumFleet]['Cco2'] = Cco2Func(parameterFile3,fleetAll[numCompany][NumFleet]['fuelName'])
    fleetAll[numCompany][NumFleet]['rShipBasic'] = rShipBasicFunc(parameterFile5,fleetAll[numCompany][NumFleet]['fuelName'],fleetAll[numCompany][NumFleet]['CAPcnt'])
    fleetAll[numCompany][NumFleet]['delivery'] = currentYear+tbid
    fleetAll[numCompany][NumFleet]['tOp'] = iniT
    if iniT > 0:
        fleetAll[numCompany][NumFleet]['costShipBasicHFO'] = 0
        fleetAll[numCompany][NumFleet]['costShipBasic'] = 0
        fleetAll[numCompany][NumFleet]['costShipAll'] = 0
    fleetAll[numCompany][NumFleet]['v'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['rocc'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['wDWT'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['wFLD'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['d'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['fShipORG'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['fAuxORG'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['gORG'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['costFuelShipORG'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['costFuelShip'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['dcostFuelShip'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['costFuelAuxORG'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['costFuelAux'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['dcostFuelAux'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['dcostFuelAll'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['fShip'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['fAux'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['g'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['cta'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['costFuelAll'] = np.zeros(tOpSch)
    #fleetAll[numCompany][NumFleet]['costShipBasicHFO'] = np.zeros(tOpSch)
    #fleetAll[numCompany][NumFleet]['costShipBasic'] = np.zeros(tOpSch)
    #fleetAll[numCompany][NumFleet]['costShipAll'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['dcostShipping'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['gTilde'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['dcostShippingTilde'] = np.zeros(tOpSch)
    return fleetAll

#def yearlyOperationFunc(fleetAll,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,v,valueDict,parameterFile4):　# tkinterによるInput用
def yearlyOperationFunc(fleetAll,numCompany,Dtotal,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,v,valueDict,parameterFile4):
    NumFleet = len(fleetAll[numCompany])

    j = 0
    maxCta = 0
    currentYear = startYear+elapsedYear
    for i in range(1,NumFleet):
        if fleetAll[numCompany][i]['delivery'] <= currentYear and fleetAll[numCompany][i]['tOp'] < tOpSch:
            tOpTemp = fleetAll[numCompany][i]['tOp']
            fleetAll[numCompany][i]['v'][tOpTemp] = v
            fleetAll[numCompany][i]['wDWT'][tOpTemp] = wDWTFunc(valueDict["kDWT1"],fleetAll[numCompany][i]['CAPcnt'],valueDict["kDWT2"])
            fleetAll[numCompany][i]['wFLD'][tOpTemp] = wFLDFunc(valueDict["kFLD1"],fleetAll[numCompany][i]['wDWT'][tOpTemp],valueDict["kFLD2"])
            fleetAll[numCompany][i]['d'][tOpTemp] = dFunc(valueDict["Dyear"],valueDict["Hday"],fleetAll[numCompany][i]['v'][tOpTemp],valueDict["Rrun"])
            maxCta += NShipFleet * maxCtaFunc(fleetAll[numCompany][i]['CAPcnt'],fleetAll[numCompany][i]['d'][tOpTemp])
            j += 1
    
    fleetAll[numCompany]['total']['maxCta'][elapsedYear] = maxCta
    Di = fleetAll[numCompany]['total']['overDi'][elapsedYear] + Dtotal / 3 # depends on score
    if Di / maxCta <= 1.0 and Di / maxCta > 0.0:
        fleetAll[numCompany]['total']['rocc'][elapsedYear] = Di / maxCta
    elif Di / maxCta > 1.0:
        fleetAll[numCompany]['total']['rocc'][elapsedYear] = 1.0
        fleetAll[numCompany]['total']['overDi'][elapsedYear] = (Di / maxCta - 1.0) * maxCta
    else:
        print('ERROR: rocc should be 0.0 < rocc but now',Di/maxCta,'.')
        sys.exit()

    numFleetAlive = 0
    for i in range(1,NumFleet):
        if fleetAll[numCompany][i]['delivery'] <= currentYear and fleetAll[numCompany][i]['tOp'] < tOpSch:
            tOpTemp = fleetAll[numCompany][i]['tOp']
            if tOpTemp == 0:
                fleetAll[numCompany][i]['costShipBasicHFO'], fleetAll[numCompany][i]['costShipBasic'], fleetAll[numCompany][i]['costShipAll'] = costShipFunc(valueDict["kShipBasic1"], fleetAll[numCompany][i]["CAPcnt"], valueDict["kShipBasic2"], fleetAll[numCompany][i]['rShipBasic'], valueDict["dcostWPS"], valueDict["dcostSPS"], valueDict["dcostCCS"], fleetAll[numCompany][i]['WPS'], fleetAll[numCompany][i]['SPS'], fleetAll[numCompany][i]['CCS'])
                fleetAll[numCompany]['total']['costShipAll'][elapsedYear] += NShipFleet * fleetAll[numCompany][i]['costShipAll']
            unitCostFuel, unitCostFuelHFO = unitCostFuelFunc(parameterFile4,fleetAll[numCompany][i]['fuelName'],currentYear)
            fleetAll[numCompany][i]['cta'][tOpTemp] = ctaFunc(fleetAll[numCompany][i]['CAPcnt'],fleetAll[numCompany]['total']['rocc'][elapsedYear],fleetAll[numCompany][i]['d'][tOpTemp])
            fleetAll[numCompany][i]['fShipORG'][tOpTemp], fleetAll[numCompany][i]['fShip'][tOpTemp] = fShipFunc(valueDict["kShip1"],valueDict["kShip2"],fleetAll[numCompany][i]['wDWT'][tOpTemp],fleetAll[numCompany][i]['wFLD'][tOpTemp],fleetAll[numCompany]['total']['rocc'][elapsedYear],valueDict["CNM2km"],fleetAll[numCompany][i]['v'][tOpTemp],fleetAll[numCompany][i]['d'][tOpTemp],valueDict["rWPS"],fleetAll[numCompany][i]['WPS'],fleetAll[numCompany][i]['CeqLHV'])
            fleetAll[numCompany][i]['fAuxORG'][tOpTemp], fleetAll[numCompany][i]['fAux'][tOpTemp] = fAuxFunc(valueDict["Dyear"],valueDict["Hday"],valueDict["Rrun"],valueDict["kAux1"],valueDict["kAux2"],fleetAll[numCompany][i]['wDWT'][tOpTemp],valueDict["rSPS"],fleetAll[numCompany][i]['SPS'])
            fleetAll[numCompany][i]['gORG'][tOpTemp], fleetAll[numCompany][i]['g'][tOpTemp] = gFunc(fleetAll[numCompany][i]['Cco2'],fleetAll[numCompany][i]['fShip'][tOpTemp],valueDict["Cco2DF"],fleetAll[numCompany][i]['fAux'][tOpTemp],valueDict["rCCS"],fleetAll[numCompany][i]['CCS'])     
            fleetAll[numCompany][i]['costFuelShipORG'][tOpTemp], fleetAll[numCompany][i]['costFuelShip'][tOpTemp], fleetAll[numCompany][i]['dcostFuelShip'][tOpTemp] = costFuelShipFunc(unitCostFuelHFO, unitCostFuel, fleetAll[numCompany][i]['fShipORG'][tOpTemp], fleetAll[numCompany][i]['fShip'][tOpTemp])
            fleetAll[numCompany][i]['costFuelAuxORG'][tOpTemp], fleetAll[numCompany][i]['costFuelAux'][tOpTemp], fleetAll[numCompany][i]['dcostFuelAux'][tOpTemp] = costFuelAuxFunc(valueDict["unitCostDF"], fleetAll[numCompany][i]['fAuxORG'][tOpTemp], fleetAll[numCompany][i]['fAux'][tOpTemp])
            fleetAll[numCompany][i]['costFuelAll'][tOpTemp], fleetAll[numCompany][i]['dcostFuelAll'][tOpTemp] = costFuelAllFunc(fleetAll[numCompany][i]['costFuelShip'][tOpTemp], fleetAll[numCompany][i]['costFuelAux'][tOpTemp], fleetAll[numCompany][i]['dcostFuelShip'][tOpTemp], fleetAll[numCompany][i]['dcostFuelAux'][tOpTemp])
            fleetAll[numCompany][i]['dcostShipping'][tOpTemp] = additionalShippingFeeFunc(tOpTemp, tOpSch, fleetAll[numCompany][i]['dcostFuelAll'][tOpTemp], fleetAll[numCompany][i]['costShipAll'], fleetAll[numCompany][i]['costShipBasicHFO'])
            fleetAll[numCompany][i]['gTilde'][tOpTemp] = fleetAll[numCompany][i]['g'][tOpTemp] / fleetAll[numCompany][i]['cta'][tOpTemp]
            fleetAll[numCompany][i]['dcostShippingTilde'][tOpTemp] = fleetAll[numCompany][i]['dcostShipping'][tOpTemp] / fleetAll[numCompany][i]['cta'][tOpTemp]
            fleetAll[numCompany]['total']['g'][elapsedYear] += NShipFleet * fleetAll[numCompany][i]['g'][tOpTemp]
            fleetAll[numCompany]['total']['cta'][elapsedYear] += NShipFleet * fleetAll[numCompany][i]['cta'][tOpTemp]
            fleetAll[numCompany]['total']['dcostShippingTilde'][elapsedYear] += NShipFleet * fleetAll[numCompany][i]['dcostShippingTilde'][tOpTemp]
            fleetAll[numCompany]['total']['costFuelAll'][elapsedYear] += NShipFleet * fleetAll[numCompany][i]['costFuelAll'][tOpTemp]
            numFleetAlive += 1

    fleetAll[numCompany]['total']['costAll'][elapsedYear] = fleetAll[numCompany]['total']['costFuelAll'][elapsedYear] + fleetAll[numCompany]['total']['costShipAll'][elapsedYear]
    fleetAll[numCompany]['total']['gTilde'][elapsedYear] = fleetAll[numCompany]['total']['g'][elapsedYear] / fleetAll[numCompany]['total']['cta'][elapsedYear]

    Si = 0
    for i in range(1,NumFleet):
        if fleetAll[numCompany][i]['delivery'] <= currentYear:
            tOpTemp = fleetAll[numCompany][i]['tOp']
            if tOpTemp < tOpSch:
                Si += fleetAll[numCompany][i]['dcostShippingTilde'][tOpTemp] - Alpha * fleetAll[numCompany][i]['gTilde'][tOpTemp]
                fleetAll[numCompany][i]['tOp'] += 1
    if numFleetAlive > 0:
        fleetAll[numCompany]['total']['S'][elapsedYear] = Si / numFleetAlive
    else:
        fleetAll[numCompany]['total']['S'][elapsedYear] = 0

    fleetAll['year'][elapsedYear] = currentYear
    return fleetAll

def buttonCommandOrder(fleetAll,v1,v2,v3,v4,v5,tOpSch,tbid,iniT,currentYear,parameterFile2,parameterFile3,parameterFile5):
    def inner():
        fleetTemp = fleetAll
        fleetTemp = orderShipFunc(fleetTemp,v1.get(),v2.get(),v3.get(),v4.get(),v5.get(),tOpSch,tbid,iniT,currentYear,parameterFile2,parameterFile3,parameterFile5)
        return fleetTemp
    return inner

def buttonCommandSkip(root):
    def inner():
        root.quit()
        root.destroy()
    return inner

def orderShipInputFunc(fleetAll,tOpSch,tbid,iniT,currentYear,parameterFile2,parameterFile3,parameterFile5):
    root = Tk()
    root.title('Order Fleet')
    root.geometry('500x300')

    # Frame
    frame = ttk.Frame(root, padding=20)
    frame.pack()

    # Combobox fuelName
    v1 = StringVar()
    fuel = ['HFO', 'LNG', 'NH3', 'H2']
    cb1 = ttk.Combobox(frame, textvariable=v1, values=fuel, width=20)
    cb1.set(fuel[0])

    # Checkbutton WPS
    v2 = StringVar()
    v2.set('0') # 初期化
    cb2 = ttk.Checkbutton(frame, padding=(10), text='WPS: Wind Propulsion System', variable=v2)

    # Checkbutton SPS
    v3 = StringVar()
    v3.set('0') # 初期化
    cb3 = ttk.Checkbutton(frame, padding=(10), text='SPS: Solar Propulsion System', variable=v3)

    # Checkbutton CCS
    v4 = StringVar()
    v4.set('0') # 初期化
    cb4 = ttk.Checkbutton(frame, padding=(10), text='CCS: Carbon Capture and Storage', variable=v4)

    # Scale
    v5 = IntVar()
    v5.set(20000)
    sc = Scale(frame,orient="horizontal",length=200,variable=v5,from_=0,to=50000,label='CAPcnt [TEU]')

    # Button
    button1 = ttk.Button(frame, text='Order', command=buttonCommandOrder(fleetAll,v1,v2,v3,v4,v5,tOpSch,tbid,iniT,currentYear,parameterFile2,parameterFile3,parameterFile5))
    button2 = ttk.Button(frame, text='Skip', command=buttonCommandSkip(root))

    # Layout
    cb1.grid(row=0, column=0)
    cb2.grid(row=1, column=0)
    cb3.grid(row=2, column=0)
    cb4.grid(row=3, column=0)
    sc.grid(row=4, column=0)
    button1.grid(row=5, column=0, columnspan=2)
    button2.grid(row=5, column=1, columnspan=2)

    root.deiconify()
    root.mainloop()

    return fleetAll

def buttonCommandSpeed(fleetAll, startYear,elapsedYear,NShipFleet,Alpha,tOpSch,v,valueDict,parameterFile4,root):
    def inner():
        fleetTemp = fleetAll
        fleetTemp = yearlyOperationFunc(fleetTemp,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,v,valueDict,parameterFile4)
        root.quit()
        root.destroy()
        return fleetTemp
    return inner

def yearlyOperationInputFunc(fleetAll,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,valueDict,parameterFile4):
    NumFleet = len(fleetAll[numCompany])
    currentYear = startYear+elapsedYear

    root = Tk()
    root.title('Yealy Operation in %s: Input Service Speed [kt]' % currentYear)
    root.geometry('500x300')

    # Frame
    frame = ttk.Frame(root, padding=20)
    frame.pack()

    # Label
    label = Label(frame,text="Input Service Speed [kt].",justify=LEFT)
    label.grid(row=0, column=0)

    # Scale
    v = []
    sc = []
    j = 0
    for i in range(1,NumFleet):
        if fleetAll[i]['delivery'] <= currentYear and fleetAll[i]['tOp'] < tOpSch:
            v.append(DoubleVar(value=20))
            FleetName = 'Fleet ' + str(i)
            sc.append(Scale(frame,orient="horizontal",length=200,variable=v[j],from_=0,to=50,label=FleetName))
            sc[j].grid(row=j+1, column=0)
            j += 1

    # Button
    button = ttk.Button(frame, text='Complete', command=buttonCommandSpeed(fleetAll,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,v,valueDict,parameterFile4,root))

    # Layout
    button.grid(row=i+1, column=0, columnspan=2)

    root.mainloop()

    return fleetAll
    
def buttonCommandOutput(root):
    def inner():
        root.quit()
        root.destroy()
    return inner

def outputGUIFunc(fleetAll,startYear,elapsedYear,tOpSch):
    #fig = plt.figure()
    fig = Figure(figsize=(5, 4), dpi=100)
    ax1 = fig.add_subplot(121)
    ax1.plot(fleetAll['year'][0:elapsedYear],fleetAll['S'][0:elapsedYear])

    ax2 = fig.add_subplot(122)
    NumFleet = len(fleetAll[numCompany])
    currentYear = startYear+elapsedYear
    for i in range(1,NumFleet):
        if fleetAll[i]['delivery'] <= currentYear and fleetAll[i]['tOp'] < tOpSch:
            print(fleetAll['year'][0:elapsedYear], fleetAll[i]['g'][0:elapsedYear])
            if i == 1:
                ax2.bar(fleetAll['year'][0:elapsedYear], fleetAll[i]['g'][0:elapsedYear])
            else:
                ax2.bar(fleetAll['year'][0:elapsedYear], fleetAll[i]['g'][0:elapsedYear], bottom=fleetAll[i-1]['g'][0:elapsedYear])

    # Tkinter Class
    root = Tk()

    # Frame
    frame = ttk.Frame(root, padding=20)
    frame.pack()

    # Canvas
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=0)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas.get_tk_widget().grid(row=0, column=0)

    def on_key_press(event):
        print("you pressed {}".format(event.key))
        key_press_handler(event, canvas, toolbar)

    def _quit():
        root.quit()     # stops mainloop
        root.destroy()  # this is necessary on Windows to prevent

    canvas.mpl_connect("key_press_event", on_key_press)

    # Button
    button = Button(master=frame, text="Resume Operation", command=_quit)
    button.grid(row=1, column=0)

    # root
    mainloop()

def outputEachCompanyFunc(fleetAll,numCompany,startYear,elapsedYear,lastYear,tOpSch,decisionListName):
    fig, ax = plt.subplots(2, 2, figsize=(10.0, 10.0))
    plt.subplots_adjust(wspace=0.4, hspace=0.6)

    SPlot = fleetAll[numCompany]['total']['S'][:elapsedYear+1]
    ax[0,0].plot(fleetAll['year'][:elapsedYear+1],fleetAll[numCompany]['total']['S'][:elapsedYear+1])
    ax[0,0].set_title(r"$ ( \Delta C_{shipping} - \alpha g) \ / \ cta$")
    ax[0,0].set_xlabel('Year')
    ax[0,0].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[0,0].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    #ax[0].set_ylabel('Year')

    gTildePlot = fleetAll[numCompany]['total']['gTilde'][:elapsedYear+1]*1000000
    ax[1,0].plot(fleetAll['year'][:elapsedYear+1],fleetAll[numCompany]['total']['gTilde'][:elapsedYear+1]*1000000)
    ax[1,0].set_title("g / cta")
    ax[1,0].set_xlabel('Year')
    ax[1,0].set_ylabel('g / (TEU $\cdot$ NM)')
    #ax[1,0].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[1,0].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))

    gPlot = fleetAll[numCompany]['total']['g'][:elapsedYear+1]/1000000
    ax[0,1].plot(fleetAll['year'][:elapsedYear+1],fleetAll[numCompany]['total']['g'][:elapsedYear+1]/1000000)
    ax[0,1].set_title("g")
    ax[0,1].set_xlabel('Year')
    ax[0,1].set_ylabel('Millions ton')
    ax[0,1].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[0,1].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))

    dcostShippingTildePlot = fleetAll[numCompany]['total']['dcostShippingTilde'][:elapsedYear+1]
    ax[1,1].plot(fleetAll['year'][:elapsedYear+1],fleetAll[numCompany]['total']['dcostShippingTilde'][:elapsedYear+1])
    ax[1,1].set_title("$\Delta C_{shipping} \ / \ cta$")
    ax[1,1].set_xlabel('Year')
    ax[1,1].set_ylabel('\$ / (TEU $\cdot$ NM)')
    ax[1,1].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[1,1].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
                #if i == 1:
                #    ax2.bar(fleetAll['year'][:elapsedYear+1], simu)
                #else:
                #    ax2.bar(fleetAll['year'][:elapsedYear+1], simu, bottom=simuSum)
    
    #fig.tight_layout()
    
    if os.name == 'nt':
        plt.show()
    elif os.name == 'posix':
        plt.savefig("Company"+str(numCompany)+decisionListName+".jpg")
        np.savetxt("Company"+str(numCompany)+decisionListName+'_S.csv',SPlot)
        np.savetxt("Company"+str(numCompany)+decisionListName+'_gTilde.csv',gTildePlot)
        np.savetxt("Company"+str(numCompany)+decisionListName+'_g.csv',gPlot)
        np.savetxt("Company"+str(numCompany)+decisionListName+'_dcostShippingTilde.csv',dcostShippingTildePlot)

def outputAllCompanyFunc(fleetAll,startYear,elapsedYear,lastYear,tOpSch,unitDict,decisionListNameList):
    year = fleetAll['year'][:elapsedYear+1]
    
    fig, axes = plt.subplots(3, 4, figsize=(16.0, 11.0))
    plt.subplots_adjust(wspace=0.4, hspace=0.6)

    for j, listName in enumerate(decisionListNameList,1):
        for ax, keyi in zip(fig.axes, fleetAll[j]['total'].keys()):
            ax.plot(year,fleetAll[j]['total'][keyi][:elapsedYear+1],label="Company"+str(j))
            ax.set_title(keyi)
            ax.set_xlabel('Year')
            ax.legend()
            ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
            ax.set_ylabel(unitDict[keyi])
    
    if os.name == 'nt':
        plt.show()
    elif os.name == 'posix':
        plt.savefig("TotalValues.jpg")
        for j, listName in enumerate(decisionListNameList,1):
            valueName = []
            outputList = []
            for i, keyi in enumerate(fleetAll[j]['total'].keys(),1):
                valueName.append(keyi)
                outputList.append(fleetAll[j]['total'][keyi][:elapsedYear+1])
                    
            outputData = np.stack(outputList,1)
            outputDf = pd.DataFrame(data=outputData, index=year, columns=valueName, dtype='float')
            outputDf.to_csv("Company"+str(j)+'_'+listName+'.csv')

    figDict = {}
    for j, listName in enumerate(decisionListNameList,1):
        for keyFleet in fleetAll[j].keys():
            valueName = []
            outputList = []
            if type(keyFleet) is int:
                for keyValue in fleetAll[j][keyFleet].keys():
                    if type(fleetAll[j][keyFleet][keyValue]) is np.ndarray:
                        valueName.append(keyValue)
                        #if keyFleet == 1 and j == 1:
                        #    fig, ax = plt.subplots(1, 1, figsize=(12.0, 8.0))
                        #    figDict.setdefault(keyValue,ax)

                        plotArr = np.zeros(lastYear-startYear+1)
                        if fleetAll[j][keyFleet]['delivery'] >= startYear:
                            plotArr[fleetAll[j][keyFleet]['delivery']-startYear:fleetAll[j][keyFleet]['delivery']-startYear+fleetAll[j][keyFleet]['tOp']] = fleetAll[j][keyFleet][keyValue][:fleetAll[j][keyFleet]['tOp']]
                        else:
                            plotArr[:tOpSch-startYear+fleetAll[j][keyFleet]['delivery']] = fleetAll[j][keyFleet][keyValue][startYear-fleetAll[j][keyFleet]['delivery']:fleetAll[j][keyFleet]['tOp']]
                        
                        outputList.append(plotArr)

                        #figDict[keyValue].plot(year,plotArr,label="Fleet"+str(keyFleet))
                        #figDict[keyValue].set_title(keyValue)
                        #figDict[keyValue].set_xlabel('Year')
                        #figDict[keyValue].legend()
                        #figDict[keyValue].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
                        #figDict[keyValue].set_ylabel(unitDict[keyValue])

                        #if j == len(decisionListNameList) and keyFleet == len(list(fleetAll[j].keys()))-1 and os.name == 'nt':
                        #    plt.show()
                        #elif j == len(decisionListNameList) and keyFleet == len(list(fleetAll[j].keys()))-1 and os.name == 'posix':
                        #    plt.savefig(str(keyValue)+".jpg")

                if os.name == 'posix':
                    outputData = np.stack(outputList,1)
                    outputDf = pd.DataFrame(data=outputData, index=year, columns=valueName, dtype='float')
                    outputDf.to_csv("Company"+str(j)+'_'+listName+'_'+'Fleet'+str(keyFleet)+'.csv')