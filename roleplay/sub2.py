from logging import log
import numpy as np
import pandas as pd
from scipy import interpolate
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import ScalarFormatter
from flask import Flask, render_template, request
from tkinter import *
from tkinter import ttk
import sys
import os
import shutil
import random
from matplotlib.ticker import MaxNLocator
from pathlib import Path
import math
import copy
#import cv2
import time
import json
import base64
import io
import datetime
#from decimal import Decimal, ROUND_HALF_UP

def readinput(filename):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    symbol = csv_input['Symbol']
    value = csv_input['Value']
    unit = csv_input['Unit']
    valueDict = {}
    unitDict = {}
    for i, j, k in zip(symbol, value, unit):
        valueDict[i] = float(j)
        unitDict[i] = str(k)
    return valueDict, unitDict

def CeqLHVFunc(filename,fuelName):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    fuelType = csv_input['Fuel type']
    CeqLHV = csv_input['CeqLHV']
    fuelDict = {}
    for i, j in zip(fuelType, CeqLHV):
        fuelDict[i] = float(j)
    return fuelDict[fuelName]

def Cco2Func(filename,fuelName):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
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
    Fee = csv_input['Fee']
    valueDict = {}
    for i, j, k, l, m, n, o, p, q in zip(Year, Order, fuelType, WPS, SPS, CCS, CAP, Speed, Fee):
        valueDict.setdefault(int(i),{})
        valueDict[int(i)]['Order'] = int(j)
        valueDict[int(i)]['fuelType'] = k
        valueDict[int(i)]['WPS'] = int(l)
        valueDict[int(i)]['SPS'] = int(m)
        valueDict[int(i)]['CCS'] = int(n)
        valueDict[int(i)]['CAP'] = float(o)
        valueDict[int(i)]['Speed'] = float(p)
        valueDict[int(i)]['Fee'] = float(q)
    return valueDict

def fleetPreparationFunc(fleetAll,initialFleetFile,numCompany,startYear,lastYear,elapsedYear,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5):
    fleetAll.setdefault(numCompany,{})
    fleetAll[numCompany].setdefault('total',{})
    fleetAll[numCompany]['total']['sale'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['g'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['gTilde'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['costTilde'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['saleTilde'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['cta'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['overDi'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['costShipBasicHFO'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['costShip'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['costFuel'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['dcostFuel'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['costAdd'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['costAll'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['maxCta'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['rocc'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['costRfrb'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['dcostEco'] = np.zeros(lastYear-startYear+1)
    #fleetAll[numCompany]['total']['dCostCnt'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['costCnt'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['nTransCnt'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['atOnce'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['mSubs'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['mTax'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['balance'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['demand'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['profit'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['profitSum'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['gSum'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['Idx'] = np.zeros(lastYear-startYear+1)
    fleetAll[numCompany]['total']['lastOrderFuel'] = 'HFO/Diesel'
    fleetAll[numCompany]['total']['lastOrderCAP'] = 20000
    initialFleets = initialFleetFunc(initialFleetFile)

    for i in range(len(initialFleets)):
        orderYear = initialFleets[i]['year'] - tbid
        iniT = startYear - initialFleets[i]['year']
        iniCAPcnt = initialFleets[i]['TEU']
        fleetAll = orderShipFunc(fleetAll,numCompany,'HFO',0,0,0,iniCAPcnt,tOpSch,tbid,iniT,orderYear,elapsedYear,valueDict,NShipFleet,True,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
    return fleetAll

def unitCostFuelFunc(filename,fuelName,year):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
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

def fAuxFunc(Dyear,Hday,Rrun,kAux1,kAux2,wDWT,rSPS,solar,CeqLHV):
    fAuxORG = Dyear*Hday*Rrun*(kAux1+kAux2*wDWT)/1000
    if solar:
        fAux = CeqLHV*fAuxORG*(1-rSPS)
    else:
        fAux = CeqLHV*fAuxORG
    return fAuxORG, fAux

def gFunc(Cco2ship,fShip,Cco2aux,fAux,rCCS,CCS):
    gORG = Cco2ship*fShip+Cco2aux*fAux
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

def costFuelFunc(unitCostFuelHFO, unitCostFuel, fShipORG, fAuxORG, fShip, fAux):
    costFuelORG = unitCostFuelHFO*(fShipORG+fAuxORG)
    costFuel = unitCostFuel*(fShip+fAux)
    dcostFuel = costFuel - costFuelORG
    return costFuelORG, costFuel, dcostFuel

def costShipFunc(kShipBasic1, CAPcnt, kShipBasic2, rShipBasic, dcostWPS, dcostSPS, dcostCCS, flagWPS, flagSPS, flagCCS):
    costShipBasicHFO = kShipBasic1 * CAPcnt + kShipBasic2
    costShipBasic = rShipBasic * costShipBasicHFO
    cAdditionalEquipment = 0
    if flagWPS:
        cAdditionalEquipment += dcostWPS
    elif flagSPS:
        cAdditionalEquipment += dcostSPS
    elif flagCCS:
        cAdditionalEquipment += dcostCCS
    costShipAdd = cAdditionalEquipment * costShipBasicHFO
    costShip = costShipBasic + costShipAdd
    return costShipBasicHFO, costShipBasic, costShipAdd, costShip

def additionalShippingFeeFunc(tOp, tOpSch, dcostFuelAll, costShipAll, costShipBasicHFO):
    if tOp <= tOpSch:
        dcostShipping = dcostFuelAll + (costShipAll-costShipBasicHFO)/tOpSch
    else:
        dcostShipping = dcostFuelAll
    return dcostShipping

def demandScenarioFunc(year,kDem1,kDem2,kDem3,kDem4):
    Di = (kDem1*year**2 + kDem2*year + kDem3)*1000000000/kDem4
    return Di

def playOrderFunc(cost,playOrder):
    unique, counts = np.unique(cost, return_counts=True)
    if np.amax(counts) == 1:
        playOrderNew = playOrder[np.argsort(cost)]
    elif np.amax(counts) == 2:
        minCost = np.amin(cost)
        maxCost = np.amax(cost)
        if minCost == unique[counts == 1]:
            playOrderNew = np.zeros(3)
            playOrderNew[0] = playOrder[cost == minCost]
            playOrderNew[1:3] = np.random.permutation(playOrder[cost!=minCost])
        else:
            playOrderNew = np.zeros(3)
            playOrderNew[2] = playOrder[cost == maxCost]
            playOrderNew[0:2] = np.random.permutation(playOrder[cost!=maxCost])
    else:
        playOrderNew = np.random.permutation(playOrder)
    return playOrderNew

def rEEDIreqCurrentFunc(wDWT,rEEDIreq):
    if wDWT >= 200000:
        rEEDIreqCurrent = rEEDIreq[0]
    elif wDWT >= 120000:
        rEEDIreqCurrent = rEEDIreq[1]
    else:
        rEEDIreqCurrent = rEEDIreq[2]
    return rEEDIreqCurrent

def EEDIreqFunc(kEEDI1,wDWT,kEEDI2,rEEDIreq):
    EEDIref = kEEDI1*wDWT**kEEDI2
    EEDIreq = (1-rEEDIreq)*EEDIref
    return EEDIref, EEDIreq

def EEDIattFunc(wDWT,wMCR,kMCR1,kMCR2,kMCR3,kPAE1,kPAE2,rCCS,vDsgn,rWPS,Cco2ship,SfcM,SfcA,rSPS,Cco2aux,EEDIreq,flagWPS,flagSPS,flagCCS):
    if wDWT < wMCR:
        MCRM = kMCR1*wDWT + kMCR2
    else:
        MCRM = kMCR3
    PA = kPAE1*MCRM+kPAE2

    def _EEDIcalc(vDsgnRed):
        if flagWPS:
            rWPStemp = rWPS
        else:
            rWPStemp = 0
        if flagSPS:
            rSPStemp = rSPS
        else:
            rSPStemp = 0
        if flagCCS:
            rCCStemp = rCCS
        else:
            rCCStemp = 0
        return ((1-rCCStemp)/(0.7*wDWT*vDsgnRed))*((1-rWPStemp)*Cco2ship*0.75*MCRM*SfcM*(vDsgnRed/vDsgn)**3 + (1-rSPStemp)*Cco2aux*PA*SfcA)

    vDsgnRed = vDsgn
    EEDIatt = _EEDIcalc(vDsgnRed)
    while EEDIatt > EEDIreq:
        vDsgnRed -= 1
        if vDsgnRed == 0:
            break
        EEDIatt = _EEDIcalc(vDsgnRed)
        

    return MCRM, PA, EEDIatt, vDsgnRed

def regPreFunc(nDec):
    regDec = {}
    regDec['rEEDIreq'] = np.zeros((nDec,3))
    regDec['Subsidy'] = np.zeros(nDec)
    regDec['Ctax'] = np.zeros(nDec)
    regDec['rEEDIreq'][0,0] = 0.5
    regDec['rEEDIreq'][0,1] = 0.45
    regDec['rEEDIreq'][0,2] = 0.35
    return regDec

def regDecFunc(regDec,nReg,currentYear):
    
    def _regDecGui1(regDec,nReg,currentYear):

        def _buttonCommand(regDec,nReg,root):
            if float(v1.get()) <= 100 and float(v2.get()) <= 100 and float(v3.get()) <= 100 and float(v1.get()) >= 0 and float(v2.get()) >= 0 and float(v3.get()) >= 0:
                regDec['rEEDIreq'][nReg,0] = float(v1.get()) / 100
                regDec['rEEDIreq'][nReg,1] = float(v2.get()) / 100
                regDec['rEEDIreq'][nReg,2] = float(v3.get()) / 100
                root.quit()
                root.destroy()
            else:
                button['state'] = 'disabled'
            
        def _buttonCommandCheck():
            if float(v1.get()) <= 100 and float(v2.get()) <= 100 and float(v3.get()) <= 100 and float(v1.get()) >= 0 and float(v2.get()) >= 0 and float(v3.get()) >= 0:
                button['state'] = 'normal'
            else:
                button['state'] = 'disabled'

        root = Tk()
        root.title('Regulator : Reduction Rate for EEXI / EEDI in '+str(currentYear))
        width = 600
        height = 300
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)
        root['bg'] = '#a3d6cc'

        style = ttk.Style()
        style.theme_use('default')
        style.configure('new.TFrame', foreground='black', background='#a3d6cc')
        style.configure('new.TLabel', foreground='black', background='#a3d6cc')
        style.configure('new.TButton', foreground='black', background='#a3d6cc')
        style.configure('new.TCheckbutton', foreground='black', background='#a3d6cc')
        style.configure('new.TEntry', foreground='black', background='#a3d6cc')

        # Frame
        frame = ttk.Frame(root, style='new.TFrame', padding=20)
        frame.pack()

        # Checkbutton
        v1 = StringVar()
        if nReg == 0:
            v1.set('0') # 初期化
        else:
            v1.set(str(100*regDec['rEEDIreq'][nReg-1,0])) # 初期化
        cb1 = ttk.Entry(frame, style='new.TEntry', textvariable=v1)
        label1 = ttk.Label(frame, style='new.TLabel',text='wDWT >= 200,000', padding=(5, 2))
        label11 = ttk.Label(frame, style='new.TLabel',text='% <= 100%', padding=(5, 2))
        label111 = ttk.Label(frame, style='new.TLabel',text='0% <=', padding=(5, 2))

        labelExpl = ttk.Label(frame, style='new.TLabel', text='Guide: Input reduction rate for EEXI / EEDI, and then click "Check" & "Next".', padding=(5, 2))

        # Checkbutton
        v2 = StringVar()
        if nReg == 0:
            v2.set('0') # 初期化
        else:
            v2.set(str(100*regDec['rEEDIreq'][nReg-1,1])) # 初期化
        cb2 = ttk.Entry(frame, style='new.TEntry', textvariable=v2)
        label2 = ttk.Label(frame, style='new.TLabel',text='120,000 <= wDWT < 200,000', padding=(5, 2))
        label22 = ttk.Label(frame, style='new.TLabel',text='% <= 100%', padding=(5, 2))
        label222 = ttk.Label(frame, style='new.TLabel',text='0% <=', padding=(5, 2))

        # Checkbutton
        v3 = StringVar()
        if nReg == 0:
            v3.set('0') # 初期化
        else:
            v3.set(str(100*regDec['rEEDIreq'][nReg-1,2])) # 初期化
        cb3 = ttk.Entry(frame, style='new.TEntry', textvariable=v3)
        label3 = ttk.Label(frame, style='new.TLabel',text='wDWT < 120,000', padding=(5, 2))
        label33 = ttk.Label(frame, style='new.TLabel',text='% <= 100%', padding=(5, 2))
        label333 = ttk.Label(frame, style='new.TLabel',text='0% <=', padding=(5, 2))

        # Button
        button = ttk.Button(frame, style='new.TButton',text='Next', state='disabled', command=lambda: _buttonCommand(regDec,nReg,root))
        button1 = ttk.Button(frame, style='new.TButton',text='Check', command=lambda: _buttonCommandCheck())

        # Layout
        label11.grid(row=0, column=3)
        cb1.grid(row=0, column=2)
        label111.grid(row=0, column=1)
        label1.grid(row=0, column=0)
        label22.grid(row=1, column=3)
        cb2.grid(row=1, column=2)
        label222.grid(row=1, column=1)
        label2.grid(row=1, column=0)
        label33.grid(row=2, column=3)
        cb3.grid(row=2, column=2)
        label333.grid(row=2, column=1)
        label3.grid(row=2, column=0)
        button.grid(row=3, column=3)
        button1.grid(row=3, column=2)
        labelExpl.grid(row=5, column=0, columnspan=3)

        root.deiconify()
        root.mainloop()

        return regDec

    def _regDecGui2(regDec,nReg,currentYear):

        def _buttonCommand(regDec,nReg,root):
            if float(v1.get()) <= 100 and float(v1.get()) >= 0 and float(v2.get()) >= 0:
                regDec['Subsidy'][nReg] = float(v1.get()) / 100
                regDec['Ctax'][nReg] = float(v2.get())
                root.quit()
                root.destroy()
            else:
                button['state'] = 'disabled'

        def _buttonCommandCheck():
            if float(v1.get()) <= 100 and float(v1.get()) >= 0 and float(v2.get()) >= 0:
                button['state'] = 'normal'
            else:
                button['state'] = 'disabled'

        root = Tk()
        root.title('Regulator : Subsidy & Carbon tax in'+str(currentYear))
        width = 800
        height = 300
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)
        root['bg'] = '#a3d6cc'

        style = ttk.Style()
        style.theme_use('default')
        style.configure('new.TFrame', foreground='black', background='#a3d6cc')
        style.configure('new.TLabel', foreground='black', background='#a3d6cc')
        style.configure('new.TButton', foreground='black', background='#a3d6cc')
        style.configure('new.TCheckbutton', foreground='black', background='#a3d6cc')
        style.configure('new.TEntry', foreground='black', background='#a3d6cc')

        # Frame
        frame = ttk.Frame(root, style='new.TFrame', padding=20)
        frame.pack()

        # Checkbutton
        v1 = StringVar()
        if nReg == 0:
            v1.set('0') # 初期化
        else:
            v1.set(str(int(100*regDec['Subsidy'][nReg-1]))) # 初期化
        cb1 = ttk.Entry(frame, style='new.TEntry', textvariable=v1)
        label1 = ttk.Label(frame, style='new.TLabel', text='Subsidy rate', padding=(5, 2))
        label11 = ttk.Label(frame, style='new.TLabel', text='% <= 100%', padding=(5, 2))
        label111 = ttk.Label(frame, style='new.TLabel', text='0% <=', padding=(5, 2))

        labelExpl = ttk.Label(frame, style='new.TLabel', text='Guide: Input subsidy and carbon tax, and then click "Check" & "Next".', padding=(5, 2))


        # Checkbutton
        v2 = StringVar()
        if nReg == 0:
            v2.set('0') # 初期化
        else:
            v2.set(str(int(regDec['Ctax'][nReg-1]))) # 初期化
        cb2 = ttk.Entry(frame, style='new.TEntry', textvariable=v2)
        label2 = ttk.Label(frame, style='new.TLabel', text='Carbon tax [$/ton]', padding=(5, 2))
        #label22 = ttk.Label(frame, style='new.TLabel', text='% <= 100%', padding=(5, 2))
        label222 = ttk.Label(frame, style='new.TLabel', text='0 <=', padding=(5, 2))

        # Button
        button = ttk.Button(frame, style='new.TButton', text='Next', state='disabled', command=lambda: _buttonCommand(regDec,nReg,root))
        button1 = ttk.Button(frame, style='new.TButton', text='Check', command=lambda: _buttonCommandCheck())

        # Layout
        label11.grid(row=0, column=3)
        cb1.grid(row=0, column=2)
        label111.grid(row=0, column=1)
        label1.grid(row=0, column=0)
        #label22.grid(row=1, column=3)
        cb2.grid(row=1, column=2)
        label222.grid(row=1, column=1)
        label2.grid(row=1, column=0)
        button.grid(row=3, column=3)
        button1.grid(row=3, column=2)
        labelExpl.grid(row=5, column=0, columnspan=3)

        root.deiconify()
        root.mainloop()

        return regDec

    regDec = _regDecGui1(regDec,nReg,currentYear)
    regDec = _regDecGui2(regDec,nReg,currentYear)

    return regDec
    
def scrapRefurbishFunc(fleetAll,numCompany,elapsedYear,currentYear,valueDict,tOpSch,rEEDIreq):
       
    def _scrapOrRefurbishGui(fleetAll,numCompany,tOpSch,valueDict,currentYear,rEEDIreq):
        def _buttonCommandCheckButton(fleetAll,valueDict,rEEDIreq,v,Sys):
            NumFleet = len(fleetAll[numCompany])
            numAlive = 0
            for keyFleet in range(1,NumFleet):
                if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
                    tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
                    fleetAll[numCompany][keyFleet][Sys] = int(v[numAlive].get())
                    rEEDIreqCurrent = rEEDIreqCurrentFunc(fleetAll[numCompany][keyFleet]['wDWT'],rEEDIreq)
                    fleetAll[numCompany][keyFleet]['EEDIref'][tOpTemp], fleetAll[numCompany][keyFleet]['EEDIreq'][tOpTemp] = EEDIreqFunc(valueDict['kEEDI1'],fleetAll[numCompany][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                    fleetAll[numCompany][keyFleet]['MCRM'][tOpTemp], fleetAll[numCompany][keyFleet]['PA'][tOpTemp], fleetAll[numCompany][keyFleet]['EEDIatt'][tOpTemp], fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp] = EEDIattFunc(fleetAll[numCompany][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleetAll[numCompany][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleetAll[numCompany][keyFleet]['Cco2aux'],fleetAll[numCompany][keyFleet]['EEDIreq'][tOpTemp],fleetAll[numCompany][keyFleet]['WPS'],fleetAll[numCompany][keyFleet]['SPS'],fleetAll[numCompany][keyFleet]['CCS'])
                    label14[numAlive]['text'] = str(int(fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp]))
                    label15[numAlive]['text'] = str('{:.3g}'.format(fleetAll[numCompany][keyFleet]['EEDIreq'][tOpTemp]))
                    label16[numAlive]['text'] = str('{:.3g}'.format(fleetAll[numCompany][keyFleet]['EEDIatt'][tOpTemp]))
                    if valueDict['vMin'] < fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp]:
                        button2['state'] = 'normal'
                    numAlive += 1
                    #fleetAll[numCompany][keyFleet] = fleetAll[numCompany][keyFleet]
        
        def _buttonCommandNext(root,fleetAll,numCompany,tOpSch):
            NumFleet = len(fleetAll[numCompany])
            j = 0
            goAhead = True
            for keyFleet in range(1,NumFleet):
                if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
                    tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
                    if valueDict['vMin'] > fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp] and v4[j].get() != '1':
                        goAhead = False
                    j += 1
            if goAhead:
                j = 0
                for keyFleet in range(1,NumFleet):
                    if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
                        if v4[j].get() == '1':
                            fleetAll[numCompany][keyFleet]['tOp'] = tOpSch
                        j += 1
                root.quit()
                root.destroy()
            else:
                button2['state'] = 'disabled'

        def _buttonCommandCheck(fleetAll,valueDict,rEEDIreq):
            NumFleet = len(fleetAll[numCompany])
            numAlive = 0
            goAhead = True
            for keyFleet in range(1,NumFleet):
                if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
                    tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
                    fleetAll[numCompany][keyFleet]['WPS'] = int(v1[numAlive].get())
                    fleetAll[numCompany][keyFleet]['SPS'] = int(v2[numAlive].get())
                    fleetAll[numCompany][keyFleet]['CCS'] = int(v3[numAlive].get())
                    rEEDIreqCurrent = rEEDIreqCurrentFunc(fleetAll[numCompany][keyFleet]['wDWT'],rEEDIreq)
                    fleetAll[numCompany][keyFleet]['EEDIref'][tOpTemp], fleetAll[numCompany][keyFleet]['EEDIreq'][tOpTemp] = EEDIreqFunc(valueDict['kEEDI1'],fleetAll[numCompany][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                    fleetAll[numCompany][keyFleet]['MCRM'][tOpTemp], fleetAll[numCompany][keyFleet]['PA'][tOpTemp], fleetAll[numCompany][keyFleet]['EEDIatt'][tOpTemp], fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp] = EEDIattFunc(fleetAll[numCompany][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleetAll[numCompany][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleetAll[numCompany][keyFleet]['Cco2aux'],fleetAll[numCompany][keyFleet]['EEDIreq'][tOpTemp],fleetAll[numCompany][keyFleet]['WPS'],fleetAll[numCompany][keyFleet]['SPS'],fleetAll[numCompany][keyFleet]['CCS'])
                    if valueDict['vMin'] > fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp] and v4[numAlive].get() != '1':
                        goAhead = False
                    numAlive += 1
            if goAhead:
                button2['state'] = 'normal'

        def _buttonCommandNext2(root):
            root.quit()
            root.destroy()             
                    
        def _buttonCommandAtOnce(Sys):
            NumFleet = len(fleetAll[numCompany])
            j = 0
            for keyFleet in range(1,NumFleet):
                if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
                    if Sys == 'WPS':
                        if label10[j].state() != ('disabled', 'selected'):
                            if v1[j].get() == '1':
                                v1[j].set('0')
                            elif v1[j].get() == '0':
                                v1[j].set('1')
                        fleetAll[numCompany][keyFleet][Sys] = int(v1[j].get())
                    elif Sys == 'SPS':
                        if label11[j].state() != ('disabled', 'selected'):
                            if v2[j].get() == '1':
                                v2[j].set('0')
                            elif v2[j].get() == '0':
                                v2[j].set('1')
                        fleetAll[numCompany][keyFleet][Sys] = int(v2[j].get())
                    elif Sys == 'CCS':
                        if label12[j].state() != ('disabled', 'selected') and label12[j].state() != ('disabled',):
                            if v3[j].get() == '1':
                                v3[j].set('0')
                            elif v3[j].get() == '0':
                                v3[j].set('1')
                        fleetAll[numCompany][keyFleet][Sys] = int(v3[j].get())
                    tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
                    rEEDIreqCurrent = rEEDIreqCurrentFunc(fleetAll[numCompany][keyFleet]['wDWT'],rEEDIreq)
                    fleetAll[numCompany][keyFleet]['EEDIref'][tOpTemp], fleetAll[numCompany][keyFleet]['EEDIreq'][tOpTemp] = EEDIreqFunc(valueDict['kEEDI1'],fleetAll[numCompany][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
                    fleetAll[numCompany][keyFleet]['MCRM'][tOpTemp], fleetAll[numCompany][keyFleet]['PA'][tOpTemp], fleetAll[numCompany][keyFleet]['EEDIatt'][tOpTemp], fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp] = EEDIattFunc(fleetAll[numCompany][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleetAll[numCompany][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleetAll[numCompany][keyFleet]['Cco2aux'],fleetAll[numCompany][keyFleet]['EEDIreq'][tOpTemp],fleetAll[numCompany][keyFleet]['WPS'],fleetAll[numCompany][keyFleet]['SPS'],fleetAll[numCompany][keyFleet]['CCS'])
                    label14[j]['text'] = str(int(fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp]))
                    label15[j]['text'] = str('{:.3g}'.format(fleetAll[numCompany][keyFleet]['EEDIreq'][tOpTemp]))
                    label16[j]['text'] = str('{:.3g}'.format(fleetAll[numCompany][keyFleet]['EEDIatt'][tOpTemp]))
                    if valueDict['vMin'] < fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp]:
                        button2['state'] = 'normal'
                    fleetAll[numCompany][keyFleet] = fleetAll[numCompany][keyFleet]
                    j += 1

        root = Tk()
        root.title('Company '+str(numCompany)+' : Scrap or Refurbish in '+str(currentYear))
        width = 1000
        height = 500
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)
        canvas = Canvas(root, width=width, height=height)

        # Frame
        style = ttk.Style()
        style.theme_use('default')
        if numCompany == 1:
            color = '#ffcccc'
        elif numCompany == 2:
            color = '#ffedab'
        elif numCompany == 3:
            color = '#a4a8d4'
        root['bg'] = color
        style.configure('new.TFrame', foreground='black', background=color)
        style.configure('new.TLabel', foreground='black', background=color)
        style.configure('new.TButton', foreground='black', background=color)
        style.configure('new.TCheckbutton', foreground='black', background=color)
        frame = ttk.Frame(root, style='new.TFrame', padding=20)
        frame.pack()

        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        vbar = Scrollbar(root, orient="vertical")
        vbar.config(command=canvas.yview)
        vbar.pack(side=RIGHT,fill="y")
        canvas['bg'] = color
        canvas.create_window((placeX, placeY), window=frame, anchor=CENTER)
        canvas.pack()
        canvas.update_idletasks()
        canvas.configure(yscrollcommand=vbar.set)
        canvas.yview_moveto(0)

        # Label
        label0 = ttk.Label(frame, style='new.TLabel', text='No.', padding=(5, 2))
        labelDeli = ttk.Label(frame, style='new.TLabel',text='Delivery year', padding=(5, 2))
        label1 = ttk.Label(frame, style='new.TLabel',text='Fuel type', padding=(5, 2))
        label2 = ttk.Label(frame, style='new.TLabel',text='Capacity [TEU]', padding=(5, 2))
        label3 = ttk.Label(frame, style='new.TLabel',text='WPS', padding=(5, 2))
        label4 = ttk.Label(frame, style='new.TLabel',text='SPS', padding=(5, 2))
        label5 = ttk.Label(frame, style='new.TLabel',text='CCS', padding=(5, 2))
        label7 = ttk.Label(frame, style='new.TLabel',text='Maximum speed [kt]', padding=(5, 2))
        label152 = ttk.Label(frame, style='new.TLabel',text='EEXIreq [g/(ton*NM)]', padding=(5, 2))
        label162 = ttk.Label(frame, style='new.TLabel',text='EEXIatt [g/(ton*NM)]', padding=(5, 2))
        labelScrap = ttk.Label(frame, style='new.TLabel',text='Scrap', padding=(5, 2))
        label00 = []
        labelDeli1 = []
        label8 = []
        label9 = []
        label10 = []
        label11 = []
        label12 = []
        label14 = []
        label15 = []
        label16 = []
        buttonScrap = []
        v1 = []
        v2 = []
        v3 = []
        v4 = []
        NumFleet = len(fleetAll[numCompany])
        for keyFleet in range(1,NumFleet):
            fleetAll[numCompany][keyFleet] = fleetAll[numCompany][keyFleet]
            if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
                labelDeli1.append(ttk.Label(frame, style='new.TLabel',text=str(fleetAll[numCompany][keyFleet]['delivery']), padding=(5, 2)))
                label00.append(ttk.Label(frame, style='new.TLabel',text=str(keyFleet), padding=(5, 2)))
                tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
                if fleetAll[numCompany][keyFleet]['fuelName'] == 'HFO':
                    label8.append(ttk.Label(frame, style='new.TLabel',text='HFO/Diesel', padding=(5, 2)))
                else:
                    label8.append(ttk.Label(frame, style='new.TLabel',text=fleetAll[numCompany][keyFleet]['fuelName'], padding=(5, 2)))
                label9.append(ttk.Label(frame, style='new.TLabel',text=str(int(fleetAll[numCompany][keyFleet]['CAPcnt'])), padding=(5, 2)))
                v1.append(StringVar())
                if fleetAll[numCompany][keyFleet]['WPS']:
                    v1[-1].set('1')
                    label10.append(ttk.Checkbutton(frame, style='new.TCheckbutton', padding=(10), state='disable', command=lambda: _buttonCommandCheckButton(fleetAll,valueDict,rEEDIreq,v1,'WPS'),variable=v1[-1]))
                else:
                    v1[-1].set('0')
                    label10.append(ttk.Checkbutton(frame, style='new.TCheckbutton',padding=(10), command=lambda: _buttonCommandCheckButton(fleetAll,valueDict,rEEDIreq,v1,'WPS'),variable=v1[-1]))
                v2.append(StringVar())
                if fleetAll[numCompany][keyFleet]['SPS']:
                    v2[-1].set('1')
                    label11.append(ttk.Checkbutton(frame, style='new.TCheckbutton',padding=(10), state='disable', command=lambda: _buttonCommandCheckButton(fleetAll,valueDict,rEEDIreq,v2,'SPS'),variable=v2[-1]))
                else:
                    v2[-1].set('0')
                    label11.append(ttk.Checkbutton(frame, style='new.TCheckbutton',padding=(10), command=lambda: _buttonCommandCheckButton(fleetAll,valueDict,rEEDIreq,v2,'SPS'),variable=v2[-1]))
                v3.append(StringVar())
                if fleetAll[numCompany][keyFleet]['CCS']:
                    v3[-1].set('1')
                    label12.append(ttk.Checkbutton(frame, style='new.TCheckbutton',padding=(10), state='disable', command=lambda: _buttonCommandCheckButton(fleetAll,valueDict,rEEDIreq,v3,'CCS'),variable=v3[-1]))
                elif currentYear < valueDict['addSysYear']+2:
                    v3[-1].set('0')
                    label12.append(ttk.Checkbutton(frame, style='new.TCheckbutton', padding=(10), state='disable', command=lambda: _buttonCommandCheckButton(fleetAll,valueDict,rEEDIreq,v3,'CCS'),variable=v3[-1]))
                else:
                    v3[-1].set('0')
                    label12.append(ttk.Checkbutton(frame, style='new.TCheckbutton',padding=(10), command=lambda: _buttonCommandCheckButton(fleetAll,valueDict,rEEDIreq,v3,'CCS'),variable=v3[-1]))
                label14.append(ttk.Label(frame, style='new.TLabel',text=str(int(fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp])), padding=(5, 2)))
                label15.append(ttk.Label(frame, style='new.TLabel',text='{:.3g}'.format(fleetAll[numCompany][keyFleet]['EEDIreq'][tOpTemp]), padding=(5, 2)))
                label16.append(ttk.Label(frame, style='new.TLabel',text='{:.3g}'.format(fleetAll[numCompany][keyFleet]['EEDIatt'][tOpTemp]), padding=(5, 2)))
                v4.append(StringVar())
                buttonScrap.append(ttk.Checkbutton(frame, style='new.TCheckbutton',padding=(10), variable=v4[-1]))

        labelExpl = ttk.Label(frame, style='new.TLabel', text='Guide: Check additional systems and scrap button if you want, and then click "Check" & "Next". You can check all the button at once by "Check all at once".', padding=(5, 2))
        labelExpl2 = ttk.Label(frame, style='new.TLabel', text='Guide: You have no fleet. Click "Next".', padding=(5, 2))
        
        # Button
        button1 = ttk.Button(frame, style='new.TButton', text='Check', command=lambda: _buttonCommandCheck(fleetAll,valueDict,rEEDIreq))
        button2 = ttk.Button(frame, style='new.TButton', text='Next', state='disabled', command=lambda: _buttonCommandNext(root,fleetAll,numCompany,tOpSch))
        buttonWPS = ttk.Button(frame, style='new.TButton', text='Check all WPS at once', command=lambda: _buttonCommandAtOnce('WPS'))
        buttonSPS = ttk.Button(frame, style='new.TButton', text='Check all SPS at once', command=lambda: _buttonCommandAtOnce('SPS'))
        buttonCCS = ttk.Button(frame, style='new.TButton', text='Check all CCS at once', command=lambda: _buttonCommandAtOnce('CCS'))
        button22 = ttk.Button(frame, style='new.TButton',text='Next', command=lambda: _buttonCommandNext2(root))

        # Layout
        if len(label8) > 0:
            label0.grid(row=0, column=0)
            labelDeli.grid(row=0, column=1)
            label1.grid(row=0, column=2)
            label2.grid(row=0, column=3)
            label3.grid(row=0, column=4)
            label4.grid(row=0, column=5)
            label5.grid(row=0, column=6)
            label7.grid(row=0, column=7)
            label152.grid(row=0, column=8)
            label162.grid(row=0, column=9)
            labelScrap.grid(row=0, column=10)
            for i, j in enumerate(label8):
                labelDeli1[i].grid(row=i+1, column=1, pady=0)
                label00[i].grid(row=i+1, column=0, pady=0)
                label8[i].grid(row=i+1, column=2, pady=0)
                label9[i].grid(row=i+1, column=3, pady=0)
                label10[i].grid(row=i+1, column=4, pady=0)
                label11[i].grid(row=i+1, column=5, pady=0)
                label12[i].grid(row=i+1, column=6, pady=0)
                label14[i].grid(row=i+1, column=7, pady=0)
                label15[i].grid(row=i+1, column=8, pady=0)
                label16[i].grid(row=i+1, column=9, pady=0)
                buttonScrap[i].grid(row=i+1, column=10, pady=0)
            button1.grid(row=i+2, column=9)
            button2.grid(row=i+2, column=10)
            buttonWPS.grid(row=i+2, column=1)
            buttonSPS.grid(row=i+2, column=2)
            buttonCCS.grid(row=i+2, column=3)
            labelExpl.grid(row=i+3, column=0, columnspan=10)
        else:
            labelExpl2.grid(row=0, column=0)
            button22.grid(row=0, column=1)

        root.deiconify()
        root.mainloop()

        return fleetAll

    def _dcostCntGui(fleetAll,numCompany,elapsedYear):
        
        def _buttonCommand(fleetAll,numCompany,elapsedYear,root,v):
            fleetAll[numCompany]['total']['dcostCnt'][elapsedYear] = v.get()
            root.destroy()
            root.quit()

        root = Tk()
        root.title('Company '+str(numCompany)+' : Additional Shipping Fee Per Container in '+str(currentYear))
        width = 500
        height = 200
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)

        # Frame
        style = ttk.Style()
        style.theme_use('default')
        if numCompany == 1:
            color = '#ffcccc'
        elif numCompany == 2:
            color = '#ffedab'
        elif numCompany == 3:
            color = '#a4a8d4'
        root['bg'] = color
        style.configure('new.TFrame', foreground='black', background=color)
        style.configure('new.TLabel', foreground='black', background=color)
        style.configure('new.TButton', foreground='black', background=color)
        style.configure('new.TCheckbutton', foreground='black', background=color)
        style.configure('new.TEntry', foreground='black', background=color)
        frame = ttk.Frame(root, style='new.TFrame', padding=20)
        frame.pack()

        v1 = StringVar()
        if elapsedYear == 0:
            v1.set('0')
        else:
            v1.set(str(int(fleetAll[numCompany]['total']['dcostCnt'][elapsedYear-1])))
        cb1 = ttk.Entry(frame, style='new.TEntry', textvariable=v1)
        label1 = ttk.Label(frame, style='new.TLabel', text='Additional container fee dC (-1000 <= dC <= 1000)', padding=(5, 2))
        label2 = ttk.Label(frame, style='new.TLabel', text='Nominal shipping cost: 1500 $/container', padding=(5, 2))
        label3 = ttk.Label(frame, style='new.TLabel', text='$', padding=(5, 2))
        labelExpl = ttk.Label(frame, style='new.TLabel', text='Guide: Input additional shipping fee per container, and then click "Complete".', padding=(5, 2))

        button = ttk.Button(frame, style='new.TButton', text='Complete', command=lambda: _buttonCommand(fleetAll,numCompany,elapsedYear,root,v1))

        label1.grid(row=1, column=0)
        label2.grid(row=0, column=0)
        label3.grid(row=1, column=2)
        cb1.grid(row=1, column=1)
        button.grid(row=2, column=1)
        labelExpl.grid(row=3, column=0,columnspan=5)

        root.deiconify()
        root.mainloop()

        return fleetAll

    # calculate EEDI
    NumFleet = len(fleetAll[numCompany])
    for keyFleet in range(1,NumFleet):
        tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
        if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
            rEEDIreqCurrent = rEEDIreqCurrentFunc(fleetAll[numCompany][keyFleet]['wDWT'],rEEDIreq)
            fleetAll[numCompany][keyFleet]['EEDIref'][tOpTemp], fleetAll[numCompany][keyFleet]['EEDIreq'][tOpTemp] = EEDIreqFunc(valueDict['kEEDI1'],fleetAll[numCompany][keyFleet]['wDWT'],valueDict['kEEDI2'],rEEDIreqCurrent)
            fleetAll[numCompany][keyFleet]['MCRM'][tOpTemp], fleetAll[numCompany][keyFleet]['PA'][tOpTemp], fleetAll[numCompany][keyFleet]['EEDIatt'][tOpTemp], fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp] = EEDIattFunc(fleetAll[numCompany][keyFleet]['wDWT'],valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],fleetAll[numCompany][keyFleet]['Cco2ship'],valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],fleetAll[numCompany][keyFleet]['Cco2aux'],fleetAll[numCompany][keyFleet]['EEDIreq'][tOpTemp],fleetAll[numCompany][keyFleet]['WPS'],fleetAll[numCompany][keyFleet]['SPS'],fleetAll[numCompany][keyFleet]['CCS'])      
    
    # decide to scrap or refurbish currently alive fleet
    fleetAll = _scrapOrRefurbishGui(fleetAll,numCompany,tOpSch,valueDict,currentYear,rEEDIreq)
    for keyFleet in range(1,NumFleet):
        tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
        if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
            cAdditionalEquipment = 0
            if fleetAll[numCompany][keyFleet]['lastWPS'] != fleetAll[numCompany][keyFleet]['WPS'] and fleetAll[numCompany][keyFleet]['WPS']:
                cAdditionalEquipment += valueDict['dcostWPS']
            elif fleetAll[numCompany][keyFleet]['lastSPS'] != fleetAll[numCompany][keyFleet]['SPS'] and fleetAll[numCompany][keyFleet]['SPS']:
                cAdditionalEquipment += valueDict['dcostSPS']
            elif fleetAll[numCompany][keyFleet]['lastCCS'] != fleetAll[numCompany][keyFleet]['CCS'] and fleetAll[numCompany][keyFleet]['CCS']:
                cAdditionalEquipment += valueDict['dcostCCS']
            fleetAll[numCompany][keyFleet]['lastWPS'] = fleetAll[numCompany][keyFleet]['WPS']
            fleetAll[numCompany][keyFleet]['lastSPS'] = fleetAll[numCompany][keyFleet]['SPS']
            fleetAll[numCompany][keyFleet]['lastCCS'] = fleetAll[numCompany][keyFleet]['CCS']
            fleetAll[numCompany][keyFleet]['costRfrb'][tOpTemp] = cAdditionalEquipment * fleetAll[numCompany][keyFleet]['costShipBasicHFO']

    # decide additional shipping fee per container
    #_dcostCntGui(fleetAll,numCompany,elapsedYear)

    return fleetAll

def orderShipFunc(fleetAll,numCompany,fuelName,WPS,SPS,CCS,CAPcnt,tOpSch,tbid,iniT,currentYear,elapsedYear,valueDict,NShipFleet,ifIni,parameterFile2,parameterFile12,parameterFile3,parameterFile5):
    NumFleet = len(fleetAll[numCompany])
    fleetAll[numCompany].setdefault(NumFleet,{})
    fleetAll[numCompany][NumFleet]['fuelName'] = fuelName
    fleetAll[numCompany][NumFleet]['WPS'] = WPS
    fleetAll[numCompany][NumFleet]['SPS'] = SPS
    fleetAll[numCompany][NumFleet]['CCS'] = CCS
    fleetAll[numCompany][NumFleet]['lastWPS'] = WPS
    fleetAll[numCompany][NumFleet]['lastSPS'] = SPS
    fleetAll[numCompany][NumFleet]['lastCCS'] = CCS
    fleetAll[numCompany][NumFleet]['CAPcnt'] = float(CAPcnt)
    fleetAll[numCompany][NumFleet]['wDWT'] = wDWTFunc(valueDict["kDWT1"],fleetAll[numCompany][NumFleet]['CAPcnt'],valueDict["kDWT2"])
    fleetAll[numCompany][NumFleet]['wFLD'] = wFLDFunc(valueDict["kFLD1"],fleetAll[numCompany][NumFleet]['wDWT'],valueDict["kFLD2"])
    fleetAll[numCompany][NumFleet]['CeqLHVship'] = CeqLHVFunc(parameterFile2,fleetAll[numCompany][NumFleet]['fuelName'])
    fleetAll[numCompany][NumFleet]['CeqLHVaux'] = CeqLHVFunc(parameterFile12,fleetAll[numCompany][NumFleet]['fuelName'])
    fleetAll[numCompany][NumFleet]['Cco2ship'] = Cco2Func(parameterFile3,fleetAll[numCompany][NumFleet]['fuelName'])
    if fuelName == 'HFO':
        fleetAll[numCompany][NumFleet]['Cco2aux'] = Cco2Func(parameterFile3,'Diesel')
    else:
        fleetAll[numCompany][NumFleet]['Cco2aux'] = Cco2Func(parameterFile3,fleetAll[numCompany][NumFleet]['fuelName'])
    fleetAll[numCompany][NumFleet]['rShipBasic'] = rShipBasicFunc(parameterFile5,fleetAll[numCompany][NumFleet]['fuelName'],fleetAll[numCompany][NumFleet]['CAPcnt'])
    fleetAll[numCompany][NumFleet]['delivery'] = currentYear+tbid
    fleetAll[numCompany][NumFleet]['tOp'] = iniT
    fleetAll[numCompany][NumFleet]['costShipBasicHFO'], fleetAll[numCompany][NumFleet]['costShipBasic'], fleetAll[numCompany][NumFleet]['costShipAdd'], fleetAll[numCompany][NumFleet]['costShip'] = costShipFunc(valueDict["kShipBasic1"], fleetAll[numCompany][NumFleet]["CAPcnt"], valueDict["kShipBasic2"], fleetAll[numCompany][NumFleet]['rShipBasic'], valueDict["dcostWPS"], valueDict["dcostSPS"], valueDict["dcostCCS"], fleetAll[numCompany][NumFleet]['WPS'], fleetAll[numCompany][NumFleet]['SPS'], fleetAll[numCompany][NumFleet]['CCS'])
    if iniT == 0 and not ifIni:
        fleetAll[numCompany]['total']['costShip'][elapsedYear+2] += NShipFleet * fleetAll[numCompany][NumFleet]['costShip']
        fleetAll[numCompany]['total']['costShipBasicHFO'][elapsedYear+2] += NShipFleet * fleetAll[numCompany][NumFleet]['costShipBasicHFO']
    fleetAll[numCompany][NumFleet]['v'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['d'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['fShipORG'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['fAuxORG'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['gORG'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['costFuelORG'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['costFuel'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['dcostFuel'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['fShip'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['fAux'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['g'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['cta'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['dcostShipping'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['gTilde'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['costRfrb'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['EEDIref'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['EEDIreq'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['EEDIatt'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['vDsgnRed'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['MCRM'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['PA'] = np.zeros(tOpSch)
    fleetAll[numCompany][NumFleet]['year'] = np.zeros(tOpSch)
    return fleetAll

def orderPhaseFunc(fleetAll,numCompany,valueDict,elapsedYear,tOpSch,tbid,currentYear,rEEDIreq,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5):

    def _orderShipGui(fleetAll,numCompany,valueDict,elapsedYear,tOpSch,tbid,currentYear,rEEDIreq,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5):
        def _EEDIcalc(rEEDIreq,parameterFile3,valueDict):
            fuelType = v1.get()
            CAP = float(v2.get())
            WPS = int(v3.get())
            SPS = int(v4.get())
            CCS = int(v5.get())
            wDWT = wDWTFunc(valueDict['kDWT1'],CAP,valueDict['kDWT2'])
            rEEDIreqCurrent = rEEDIreqCurrentFunc(wDWT,rEEDIreq)
            if fuelType == 'HFO/Diesel':
                Cco2ship = Cco2Func(parameterFile3,'HFO')
                Cco2aux = Cco2Func(parameterFile3,'Diesel')
            else:
                Cco2ship = Cco2Func(parameterFile3,fuelType)
                Cco2aux = Cco2Func(parameterFile3,fuelType)
            _, EEDIreq = EEDIreqFunc(valueDict['kEEDI1'],wDWT,valueDict['kEEDI2'],rEEDIreqCurrent)
            _, _, EEDIatt, vDsgnRed = EEDIattFunc(wDWT,valueDict['wMCR'],valueDict['kMCR1'],valueDict['kMCR2'],valueDict['kMCR3'],valueDict['kPAE1'],valueDict['kPAE2'],valueDict['rCCS'],valueDict['vDsgn'],valueDict['rWPS'],Cco2ship,valueDict['SfcM'],valueDict['SfcA'],valueDict['rSPS'],Cco2aux,EEDIreq,WPS,SPS,CCS)
            return CAP, vDsgnRed, EEDIreq, EEDIatt

        def _buttonCommandAnother(fleetAll,numCompany,tOpSch,tbid,currentYear,elapsedYear,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5):
            CAP, vDsgnRed, EEDIreq, EEDIatt = _EEDIcalc(rEEDIreq,parameterFile3,valueDict)
            if valueDict['vMin'] <= vDsgnRed and CAP >= 8000 and CAP <= 24000:
                if v1.get() == 'HFO/Diesel':
                    fuelName = 'HFO'
                else:
                    fuelName = v1.get()
                fleetAll = orderShipFunc(fleetAll,numCompany,fuelName,int(v3.get()),int(v4.get()),int(v5.get()),float(v2.get()),tOpSch,tbid,0,currentYear,elapsedYear,valueDict,NShipFleet,False,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
                fleetAll[numCompany]['total']['lastOrderFuel'] = v1.get()
                fleetAll[numCompany]['total']['lastOrderCAP'] = v2.get()
                cb1.delete(0,"end")
                cb1.insert(0, fleetAll[numCompany]['total']['lastOrderCAP'])
                v3.set('0')
                v4.set('0')
                v5.set('0')
                cb2.var = v3
                cb3.var = v4
                cb4.var = v5
                label6['text'] = 'None'
                label7['text'] = 'None'
                label8['text'] = 'None'
                button1['state'] = 'disabled'
                button2['state'] = 'disabled'
            else:
                button1['state'] = 'disabled'
                button2['state'] = 'disabled'

        def _buttonCommandComplete(root,fleetAll,numCompany,tOpSch,tbid,currentYear,elapsedYear,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5):
            CAP, vDsgnRed, EEDIreq, EEDIatt = _EEDIcalc(rEEDIreq,parameterFile3,valueDict)
            if valueDict['vMin'] <= vDsgnRed and CAP >= 8000 and CAP <= 24000:
                if v1.get() == 'HFO/Diesel':
                    fuelName = 'HFO'
                else:
                    fuelName = v1.get()
                fleetAll = orderShipFunc(fleetAll,numCompany,fuelName,int(v3.get()),int(v4.get()),int(v5.get()),float(v2.get()),tOpSch,tbid,0,currentYear,elapsedYear,valueDict,NShipFleet,False,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
                fleetAll[numCompany]['total']['lastOrderFuel'] = v1.get()
                fleetAll[numCompany]['total']['lastOrderCAP'] = v2.get()
                root.quit()
                root.destroy()
            else:
                button1['state'] = 'disabled'
                button2['state'] = 'disabled'

        def _buttonCommandCheck(valueDict,parameterFile3,rEEDIreq):
            CAP, vDsgnRed, EEDIreq, EEDIatt = _EEDIcalc(rEEDIreq,parameterFile3,valueDict)
            label6['text'] = str(str(int(vDsgnRed)))
            label7['text'] = str('{:.3g}'.format(EEDIreq))
            label8['text'] = str('{:.3g}'.format(EEDIatt))
            if valueDict['vMin'] < vDsgnRed:
                button1['state'] = 'normal'
                button2['state'] = 'normal'
            if CAP >= 8000 and CAP <= 24000:
                button1['state'] = 'normal'
                button2['state'] = 'normal'
        
        def _buttonCommandNoOrder(root):
            root.quit()
            root.destroy()

        root = Tk()
        root.title('Company '+str(numCompany)+' : Order Ship in '+str(currentYear))
        width = 1000
        height = 300
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)

        # Frame
        style = ttk.Style()
        style.theme_use('default')
        if numCompany == 1:
            color = '#ffcccc'
        elif numCompany == 2:
            color = '#ffedab'
        elif numCompany == 3:
            color = '#a4a8d4'
        root['bg'] = color
        style.configure('new.TFrame', foreground='black', background=color)
        style.configure('new.TLabel', foreground='black', background=color)
        style.configure('new.TButton', foreground='black', background=color)
        style.configure('new.TCheckbutton', foreground='black', background=color)
        style.configure('new.TEntry', foreground='black', background=color)
        style.configure('new.TCombobox', foreground='black', background=color)
        frame = ttk.Frame(root, style='new.TFrame', padding=20)
        frame.pack()

        # Label
        label1 = ttk.Label(frame, style='new.TLabel', text='Fuel type', padding=(5, 2))
        label2 = ttk.Label(frame, style='new.TLabel', text='Capacity (8000<=Capacity<=24000) [TEU]', padding=(5, 2))
        label3 = ttk.Label(frame, style='new.TLabel', text='Maximum speed [kt]', padding=(5, 2))
        label4 = ttk.Label(frame, style='new.TLabel', text='EEDIreq [g/(ton*NM)]', padding=(5, 2))
        label5 = ttk.Label(frame, style='new.TLabel', text='EEDIatt [g/(ton*NM)]', padding=(5, 2))
        label6 = ttk.Label(frame, style='new.TLabel', text='None', padding=(5, 2))
        label7 = ttk.Label(frame, style='new.TLabel', text='None', padding=(5, 2))
        label8 = ttk.Label(frame, style='new.TLabel', text='None', padding=(5, 2))
        label9 = ttk.Label(frame, style='new.TLabel', text='WPS', padding=(5, 2))
        label10 = ttk.Label(frame, style='new.TLabel', text='SPS', padding=(5, 2))
        label11 = ttk.Label(frame, style='new.TLabel', text='CCS', padding=(5, 2))
        labelExpl = ttk.Label(frame, style='new.TLabel', text='Guide: When you want to order a fleet, select the setting and click "another fleet" or "complete". Ohterwise, click "No order".', padding=(5, 2))

        # List box
        if currentYear < valueDict['addSysYear']:
            fuelTypeList = ['HFO/Diesel','LNG']
        else:
            fuelTypeList = ['HFO/Diesel','LNG','NH3','H2']
        v1 = StringVar()
        lb = ttk.Combobox(frame, style='new.TCombobox', textvariable=v1,values=fuelTypeList)
        if elapsedYear == 0:
            lb.set('HFO/Diesel')
        else:
            lb.set(fleetAll[numCompany]['total']['lastOrderFuel'])

        # Entry
        v2 = StringVar()
        if elapsedYear == 0:
            v2.set('20000')
        else:
            v2.set(str(fleetAll[numCompany]['total']['lastOrderCAP']))
        cb1 = ttk.Entry(frame, style='new.TEntry', textvariable=v2)

        # Checkbutton
        v3 = StringVar()
        v3.set('0') # 初期化
        cb2 = ttk.Checkbutton(frame, style='new.TCheckbutton', padding=(10), text='WPS', variable=v3)
        
        # Checkbutton
        v4 = StringVar()
        v4.set('0') # 初期化
        cb3 = ttk.Checkbutton(frame, style='new.TCheckbutton', padding=(10), text='SPS', variable=v4)
       
        # Checkbutton
        v5 = StringVar()
        if currentYear >= valueDict['addSysYear']:
            v5.set('0') # 初期化
            cb4 = ttk.Checkbutton(frame, style='new.TCheckbutton', padding=(10), text='CCS', variable=v5)
        else:
            v5.set('0') # 初期化
            cb4 = ttk.Checkbutton(frame, state='disable', style='new.TCheckbutton', padding=(10), text='CCS', variable=v5)

        # Button
        button1 = ttk.Button(frame, style='new.TButton', text='Another fleet', state='disabled', command=lambda: _buttonCommandAnother(fleetAll,numCompany,tOpSch,tbid,currentYear,elapsedYear,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5))
        button2 = ttk.Button(frame, style='new.TButton', text='Complete', state='disabled', command=lambda: _buttonCommandComplete(root,fleetAll,numCompany,tOpSch,tbid,currentYear,elapsedYear,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5))
        button3 = ttk.Button(frame, style='new.TButton', text='EEDI check', command=lambda: _buttonCommandCheck(valueDict,parameterFile3,rEEDIreq))
        button4 = ttk.Button(frame, style='new.TButton', text='No order', command=lambda: _buttonCommandNoOrder(root))

        # Layout
        label1.grid(row=0, column=0)
        label2.grid(row=0, column=1)
        label3.grid(row=2, column=1)
        label4.grid(row=2, column=2)
        label5.grid(row=2, column=3)
        label6.grid(row=3, column=1)
        label7.grid(row=3, column=2)
        label8.grid(row=3, column=3)
        label9.grid(row=0, column=2)
        label10.grid(row=0, column=3)
        label11.grid(row=0, column=4)
        cb1.grid(row=1, column=1)
        cb2.grid(row=1, column=2)
        cb3.grid(row=1, column=3)
        cb4.grid(row=1, column=4)
        lb.grid(row=1, column=0)
        button1.grid(row=4, column=2)
        button2.grid(row=4, column=4)
        button3.grid(row=4, column=1)
        button4.grid(row=4, column=0)
        labelExpl.grid(row=5, column=0, columnspan=5)

        root.deiconify()
        root.mainloop()

        return fleetAll

    fleetAll = _orderShipGui(fleetAll,numCompany,valueDict,elapsedYear,tOpSch,tbid,currentYear,rEEDIreq,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)

    return fleetAll

def yearlyCtaFunc(fleetAll,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,v,valueDict):
    NumFleet = len(fleetAll[numCompany])
    j = 0
    maxCta = 0
    currentYear = startYear+elapsedYear
    for keyFleet in range(1,NumFleet):
        if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
            tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
            fleetAll[numCompany][keyFleet]['v'][tOpTemp] = float(v[j].get()) # input for each fleet
            fleetAll[numCompany][keyFleet]['d'][tOpTemp] = dFunc(valueDict["Dyear"],valueDict["Hday"],fleetAll[numCompany][keyFleet]['v'][tOpTemp],valueDict["Rrun"])
            maxCta += NShipFleet * maxCtaFunc(fleetAll[numCompany][keyFleet]['CAPcnt'],fleetAll[numCompany][keyFleet]['d'][tOpTemp])
            j += 1
    fleetAll[numCompany]['total']['maxCta'][elapsedYear] = maxCta
    return fleetAll

def yearlyOperationFunc(fleetAll,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,valueDict,rSubs,rTax,parameterFile4):
    NumFleet = len(fleetAll[numCompany])
    currentYear = startYear+elapsedYear
    fleetAll[numCompany]['total']['costRfrb'][elapsedYear] = 0
    fleetAll[numCompany]['total']['g'][elapsedYear] = 0
    fleetAll[numCompany]['total']['cta'][elapsedYear] = 0
    fleetAll[numCompany]['total']['costFuel'][elapsedYear] = 0
    for keyFleet in range(1,NumFleet):
        if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
            tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
            unitCostFuel, unitCostFuelHFO = unitCostFuelFunc(parameterFile4,fleetAll[numCompany][keyFleet]['fuelName'],currentYear)
            fleetAll[numCompany][keyFleet]['cta'][tOpTemp] = ctaFunc(fleetAll[numCompany][keyFleet]['CAPcnt'],fleetAll[numCompany]['total']['rocc'][elapsedYear],fleetAll[numCompany][keyFleet]['d'][tOpTemp])
            fleetAll[numCompany][keyFleet]['fShipORG'][tOpTemp], fleetAll[numCompany][keyFleet]['fShip'][tOpTemp] = fShipFunc(valueDict["kShip1"],valueDict["kShip2"],fleetAll[numCompany][keyFleet]['wDWT'],fleetAll[numCompany][keyFleet]['wFLD'],fleetAll[numCompany]['total']['rocc'][elapsedYear],valueDict["CNM2km"],fleetAll[numCompany][keyFleet]['v'][tOpTemp],fleetAll[numCompany][keyFleet]['d'][tOpTemp],valueDict["rWPS"],fleetAll[numCompany][keyFleet]['WPS'],fleetAll[numCompany][keyFleet]['CeqLHVship'])
            fleetAll[numCompany][keyFleet]['fAuxORG'][tOpTemp], fleetAll[numCompany][keyFleet]['fAux'][tOpTemp] = fAuxFunc(valueDict["Dyear"],valueDict["Hday"],valueDict["Rrun"],valueDict["kAux1"],valueDict["kAux2"],fleetAll[numCompany][keyFleet]['wDWT'],valueDict["rSPS"],fleetAll[numCompany][keyFleet]['SPS'],fleetAll[numCompany][keyFleet]['CeqLHVaux'])
            fleetAll[numCompany][keyFleet]['gORG'][tOpTemp], fleetAll[numCompany][keyFleet]['g'][tOpTemp] = gFunc(fleetAll[numCompany][keyFleet]['Cco2ship'],fleetAll[numCompany][keyFleet]['fShip'][tOpTemp],fleetAll[numCompany][keyFleet]['Cco2aux'],fleetAll[numCompany][keyFleet]['fAux'][tOpTemp],valueDict["rCCS"],fleetAll[numCompany][keyFleet]['CCS'])     
            fleetAll[numCompany][keyFleet]['costFuelORG'][tOpTemp], fleetAll[numCompany][keyFleet]['costFuel'][tOpTemp], fleetAll[numCompany][keyFleet]['dcostFuel'][tOpTemp] = costFuelFunc(unitCostFuelHFO, unitCostFuel, fleetAll[numCompany][keyFleet]['fShipORG'][tOpTemp], fleetAll[numCompany][keyFleet]['fAuxORG'][tOpTemp], fleetAll[numCompany][keyFleet]['fShip'][tOpTemp], fleetAll[numCompany][keyFleet]['fAux'][tOpTemp])
            fleetAll[numCompany][keyFleet]['dcostShipping'][tOpTemp] = additionalShippingFeeFunc(tOpTemp, tOpSch, fleetAll[numCompany][keyFleet]['dcostFuel'][tOpTemp], fleetAll[numCompany][keyFleet]['costShip'], fleetAll[numCompany][keyFleet]['costShipBasicHFO'])
            fleetAll[numCompany][keyFleet]['gTilde'][tOpTemp] = fleetAll[numCompany][keyFleet]['g'][tOpTemp] / fleetAll[numCompany][keyFleet]['cta'][tOpTemp]
            fleetAll[numCompany]['total']['costRfrb'][elapsedYear] += NShipFleet * fleetAll[numCompany][keyFleet]['costRfrb'][tOpTemp]
            fleetAll[numCompany]['total']['g'][elapsedYear] += NShipFleet * fleetAll[numCompany][keyFleet]['g'][tOpTemp]
            fleetAll[numCompany]['total']['cta'][elapsedYear] += NShipFleet * fleetAll[numCompany][keyFleet]['cta'][tOpTemp]
            fleetAll[numCompany]['total']['costFuel'][elapsedYear] += NShipFleet * fleetAll[numCompany][keyFleet]['costFuel'][tOpTemp]
            fleetAll[numCompany]['total']['dcostFuel'][elapsedYear] += NShipFleet * fleetAll[numCompany][keyFleet]['dcostFuel'][tOpTemp]
                
    for keyFleet in range(1,NumFleet):
        if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
            fleetAll[numCompany][keyFleet]['year'][fleetAll[numCompany][keyFleet]['tOp']] = currentYear
            fleetAll[numCompany][keyFleet]['tOp'] += 1

    fleetAll[numCompany]['total']['costAll'][elapsedYear] = fleetAll[numCompany]['total']['costFuel'][elapsedYear] + fleetAll[numCompany]['total']['costShip'][elapsedYear] + fleetAll[numCompany]['total']['costRfrb'][elapsedYear]
    fleetAll[numCompany]['total']['dcostEco'][elapsedYear] = fleetAll[numCompany]['total']['dcostFuel'][elapsedYear] + fleetAll[numCompany]['total']['costShip'][elapsedYear]-fleetAll[numCompany]['total']['costShipBasicHFO'][elapsedYear] + fleetAll[numCompany]['total']['costRfrb'][elapsedYear]
    fleetAll[numCompany]['total']['nTransCnt'][elapsedYear] = fleetAll[numCompany]['total']['cta'][elapsedYear] / valueDict['dJPNA']
    fleetAll[numCompany]['total']['costCnt'][elapsedYear] = (valueDict['costCntMax']-valueDict['costCntMin']) / (1+math.e**(-valueDict['aSgmd']*(fleetAll[numCompany]['total']['rocc'][elapsedYear]-valueDict['roccNom']))) + valueDict['costCntMin']
    fleetAll[numCompany]['total']['sale'][elapsedYear] = fleetAll[numCompany]['total']['nTransCnt'][elapsedYear] * fleetAll[numCompany]['total']['costCnt'][elapsedYear]
    fleetAll[numCompany]['total']['gTilde'][elapsedYear] = fleetAll[numCompany]['total']['g'][elapsedYear] / fleetAll[numCompany]['total']['cta'][elapsedYear]
    fleetAll[numCompany]['total']['costTilde'][elapsedYear] = fleetAll[numCompany]['total']['costAll'][elapsedYear] / fleetAll[numCompany]['total']['cta'][elapsedYear]
    fleetAll[numCompany]['total']['saleTilde'][elapsedYear] = fleetAll[numCompany]['total']['sale'][elapsedYear] / fleetAll[numCompany]['total']['cta'][elapsedYear]
    fleetAll[numCompany]['total']['mSubs'][elapsedYear] = rSubs * fleetAll[numCompany]['total']['dcostEco'][elapsedYear]
    fleetAll[numCompany]['total']['mTax'][elapsedYear] = rTax * fleetAll[numCompany]['total']['g'][elapsedYear]
    fleetAll[numCompany]['total']['balance'][elapsedYear] = fleetAll[numCompany]['total']['mTax'][elapsedYear] - fleetAll[numCompany]['total']['mSubs'][elapsedYear]
    fleetAll[numCompany]['total']['profit'][elapsedYear] = fleetAll[numCompany]['total']['sale'][elapsedYear] - fleetAll[numCompany]['total']['costAll'][elapsedYear] - fleetAll[numCompany]['total']['balance'][elapsedYear]
    fleetAll[numCompany]['total']['profitSum'][elapsedYear] += fleetAll[numCompany]['total']['profit'][elapsedYear]
    fleetAll[numCompany]['total']['gSum'][elapsedYear] += fleetAll[numCompany]['total']['g'][elapsedYear]
    fleetAll[numCompany]['total']['Idx'][elapsedYear] = fleetAll[numCompany]['total']['profitSum'][elapsedYear] / fleetAll[numCompany]['total']['gSum'][elapsedYear]
    return fleetAll

def decideSpeedFunc(fleetAll,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,valueDict):
    def _surviceSpeedGui(fleetAll,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,valueDict):
        
        def _buttonCommandNext(root,fleetAll,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,valueDict):
            NumFleet = len(fleetAll[numCompany])
            j = 0
            goAhead = True
            for keyFleet in range(1,NumFleet):
                if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
                    tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
                    if float(v13[j].get()) < 12 or float(v13[j].get()) > fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp]:
                        goAhead = False
                    j += 1
            if goAhead:
                fleetAll = yearlyCtaFunc(fleetAll,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,v13,valueDict)
                fleetAll[numCompany]['total']['atOnce'][elapsedYear] = float(vAtOnce.get())
                root.quit()
                root.destroy()
            else:
                button2['state'] = 'disabled'
        
        def _buttonCommandNext2(root):
            root.quit()
            root.destroy()

        def _buttonCommandCalc(fleetAll,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,valueDict):
            fleetAll = yearlyCtaFunc(fleetAll,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,v13,valueDict)
            #labelRes4['text'] = str('{:.3g}'.format(fleetAll[numCompany]['total']['cta'][elapsedYear]))
            #labelRes6['text'] = str('{:.4g}'.format(fleetAll[numCompany]['total']['rocc'][elapsedYear]))
            #labelRes8['text'] = str('{:.3g}'.format(fleetAll[numCompany]['total']['costFuel'][elapsedYear]))
            #labelRes10['text'] = str('{:.3g}'.format(fleetAll[numCompany]['total']['g'][elapsedYear]))
            button2['state'] = 'normal'
            NumFleet = len(fleetAll[numCompany])
            j = 0
            for keyFleet in range(1,NumFleet):
                if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
                    tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
                    if float(v13[j].get()) < 12 or float(v13[j].get()) > fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp]:
                        button2['state'] = 'disabled'
                    j += 1

        def _buttonCommandAtOnce():
            NumFleet = len(fleetAll[numCompany])
            j = 0
            for keyFleet in range(1,NumFleet):
                if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
                    tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
                    #if fleetAll[numCompany][keyFleet]['v'][tOpTemp-1] == 0:
                    #    v13[j].set(str(int(min([float(vAtOnce.get()),fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp]]))))
                    #else:
                    #    v13[j].set(str(int(min([float(vAtOnce.get()),fleetAll[numCompany][keyFleet]['v'][tOpTemp-1]]))))
                    v13[j].set(str(int(min([float(vAtOnce.get()),fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp]]))))
                    j += 1
            button1['state'] = 'normal'

        root = Tk()
        root.title('Company '+str(numCompany)+' : Service Speed in '+str(startYear+elapsedYear))
        width = 1100
        height = 400
        placeX = root.winfo_screenwidth()/2 - width/2
        placeY = root.winfo_screenheight()/2 - height/2
        widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
        root.geometry(widgetSize)
        canvas = Canvas(root, width=width, height=height)

        # Frame
        style = ttk.Style()
        style.theme_use('default')
        if numCompany == 1:
            color = '#ffcccc'
        elif numCompany == 2:
            color = '#ffedab'
        elif numCompany == 3:
            color = '#a4a8d4'
        root['bg'] = color
        style.configure('new.TFrame', foreground='black', background=color)
        style.configure('new.TLabel', foreground='black', background=color)
        style.configure('new.TButton', foreground='black', background=color)
        style.configure('new.TCheckbutton', foreground='black', background=color)
        style.configure('new.TEntry', foreground='black', background=color)
        frame = ttk.Frame(root, style='new.TFrame', padding=20)
        frame.pack()
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        vbar = Scrollbar(root, orient="vertical")
        vbar.config(command=canvas.yview)
        vbar.pack(side=RIGHT,fill="y")
        canvas['bg'] = color
        canvas.create_window((placeX, placeY), window=frame, anchor=CENTER)
        canvas.pack()
        canvas.update_idletasks()
        canvas.configure(yscrollcommand=vbar.set)
        canvas.yview_moveto(0)

        # Label
        labelAtOnce = ttk.Label(frame, style='new.TLabel', text='Input all service speeds at once (12<=) [kt]:', padding=(5, 2))
        vAtOnce = StringVar()
        if elapsedYear == 0:
            vAtOnce.set('18')
        else:
            vAtOnce.set(str(int(fleetAll[numCompany]['total']['atOnce'][elapsedYear-1])))
        labelAtOnce2 = ttk.Entry(frame, style='new.TEntry', textvariable=vAtOnce)
        #labelRes1 = ttk.Label(frame, style='new.TLabel',text='Assigned demand [TEU*NM]:', padding=(5, 2))
        #labelRes2 = ttk.Label(frame, style='new.TLabel',text=str('{:.3g}'.format(Di)), padding=(5, 2))
        #labelRes3 = ttk.Label(frame, style='new.TLabel',text='Cargo trasnsport amount [TEU*NM]:', padding=(5, 2))
        #labelRes4 = ttk.Label(frame, style='new.TLabel',text='None', padding=(5, 2))
        #labelRes5 = ttk.Label(frame, style='new.TLabel',text='Occupancy rate [%]:', padding=(5, 2))
        #labelRes6 = ttk.Label(frame, style='new.TLabel',text='None', padding=(5, 2))
        #labelRes7 = ttk.Label(frame, style='new.TLabel',text='Fuel cost [$]:', padding=(5, 2))
        #labelRes8 = ttk.Label(frame, style='new.TLabel',text='None', padding=(5, 2))
        #labelRes9 = ttk.Label(frame, style='new.TLabel',text='CO2 [ton]:', padding=(5, 2))
        #labelRes10 = ttk.Label(frame, style='new.TLabel',text='None', padding=(5, 2))
        label0 = ttk.Label(frame, style='new.TLabel',text='No.', padding=(5, 2))
        label1 = ttk.Label(frame, style='new.TLabel',text='Fuel type', padding=(5, 2))
        label2 = ttk.Label(frame, style='new.TLabel',text='Capacity [TEU]', padding=(5, 2))
        label3 = ttk.Label(frame, style='new.TLabel',text='WPS', padding=(5, 2))
        label4 = ttk.Label(frame, style='new.TLabel',text='SPS', padding=(5, 2))
        label5 = ttk.Label(frame, style='new.TLabel',text='CCS', padding=(5, 2))
        label6 = ttk.Label(frame, style='new.TLabel',text='Service speed (12<=) [kt]', padding=(5, 2))
        label7 = ttk.Label(frame, style='new.TLabel',text='Maximum speed [kt]', padding=(5, 2))
        label00 = []
        label8 = []
        label9 = []
        label10 = []
        label11 = []
        label12 = []
        label13 = []
        label14 = []
        v13 = []
        currentYear = startYear+elapsedYear
        NumFleet = len(fleetAll[numCompany])
        for keyFleet in range(1,NumFleet):
            if fleetAll[numCompany][keyFleet]['delivery'] <= currentYear and fleetAll[numCompany][keyFleet]['tOp'] < tOpSch:
                label00.append(ttk.Label(frame, style='new.TLabel',text=str(keyFleet), padding=(5, 2)))
                tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
                if fleetAll[numCompany][keyFleet]['fuelName'] == 'HFO':
                    label8.append(ttk.Label(frame, style='new.TLabel',text='HFO/Diesel', padding=(5, 2)))
                else:
                    label8.append(ttk.Label(frame, style='new.TLabel',text=fleetAll[numCompany][keyFleet]['fuelName'], padding=(5, 2)))
                label9.append(ttk.Label(frame, style='new.TLabel',text=str(int(fleetAll[numCompany][keyFleet]['CAPcnt'])), padding=(5, 2)))
                if fleetAll[numCompany][keyFleet]['WPS']:
                    label10.append(ttk.Label(frame, style='new.TLabel',text='Yes', padding=(5, 2)))
                else:
                    label10.append(ttk.Label(frame, style='new.TLabel',text='No', padding=(5, 2)))
                if fleetAll[numCompany][keyFleet]['SPS']:
                    label11.append(ttk.Label(frame, style='new.TLabel',text='Yes', padding=(5, 2)))
                else:
                    label11.append(ttk.Label(frame, style='new.TLabel',text='No', padding=(5, 2)))
                if fleetAll[numCompany][keyFleet]['CCS']:
                    label12.append(ttk.Label(frame, style='new.TLabel',text='Yes', padding=(5, 2)))
                else:
                    label12.append(ttk.Label(frame, style='new.TLabel',text='No', padding=(5, 2)))
                tOpTemp = fleetAll[numCompany][keyFleet]['tOp']
                v13.append(StringVar())
                if fleetAll[numCompany][keyFleet]['v'][tOpTemp-1] == 0:
                    #v13[-1].set(str(int(fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp])))
                    v13[-1].set(str(int(18)))
                else:
                    v13[-1].set(str(int(fleetAll[numCompany][keyFleet]['v'][tOpTemp-1])))
                #v13[-1].set('None')
                label13.append(ttk.Entry(frame, style='new.TEntry',textvariable=v13[-1]))
                label14.append(ttk.Label(frame, style='new.TLabel',text=str(int(fleetAll[numCompany][keyFleet]['vDsgnRed'][tOpTemp])), padding=(5, 2)))

        labelExpl = ttk.Label(frame, style='new.TLabel', text='Guide: Input a service speed for all fleets at first and click "Input", and then change each speed if you want. After inputting all values, click "Check" and "Next".', padding=(5, 2))
        labelExpl2 = ttk.Label(frame, style='new.TLabel', text='Guide: You have no fleet. Click "Next".', padding=(5, 2))

        # Button
        button1 = ttk.Button(frame, style='new.TButton',text='Check', state='disabled', command=lambda: _buttonCommandCalc(fleetAll,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,valueDict))
        button2 = ttk.Button(frame, style='new.TButton',text='Next', state='disabled', command=lambda: _buttonCommandNext(root,fleetAll,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,valueDict))
        button22 = ttk.Button(frame, style='new.TButton',text='Next', command=lambda: _buttonCommandNext2(root))
        button3 = ttk.Button(frame, style='new.TButton',text='Input', command=lambda: _buttonCommandAtOnce())

        # Layout
        if len(label8) > 0:
            #labelRes1.grid(row=0, column=1)
            #labelRes2.grid(row=0, column=2)
            #labelRes3.grid(row=0, column=1)
            #labelRes4.grid(row=0, column=2)
            #labelRes5.grid(row=1, column=1)
            #labelRes6.grid(row=1, column=2)
            #labelRes7.grid(row=1, column=4)
            #labelRes8.grid(row=1, column=5)
            #labelRes9.grid(row=2, column=1)
            #labelRes10.grid(row=2, column=2)
            label0.grid(row=3, column=0)
            label1.grid(row=3, column=1)
            label2.grid(row=3, column=2)
            label3.grid(row=3, column=3)
            label4.grid(row=3, column=4)
            label5.grid(row=3, column=5)
            label6.grid(row=3, column=6)
            label7.grid(row=3, column=7)
            for i, j in enumerate(label8):
                label00[i].grid(row=i+4, column=0)
                label8[i].grid(row=i+4, column=1)
                label9[i].grid(row=i+4, column=2)
                label10[i].grid(row=i+4, column=3)
                label11[i].grid(row=i+4, column=4)
                label12[i].grid(row=i+4, column=5)
                label13[i].grid(row=i+4, column=6)
                label14[i].grid(row=i+4, column=7)
            labelAtOnce.grid(row=i+5, column=1)
            labelAtOnce2.grid(row=i+5, column=2)
            button3.grid(row=i+5, column=3)
            button1.grid(row=i+5, column=6)
            button2.grid(row=i+5, column=7)
            labelExpl.grid(row=i+6, column=0,columnspan=8)
        else:
            labelExpl2.grid(row=0, column=0)
            button22.grid(row=0, column=1)

        root.deiconify()
        root.mainloop()

        return fleetAll

    fleetAll = _surviceSpeedGui(fleetAll,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,valueDict)

    return fleetAll

def outputGuiFunc(fleetAll,startYear,elapsedYear,lastYear,tOpSch,unitDict):
    def _eachFrame(frame,fig,keyi,keyList,root):
        '''
        def _on_key_press(event):
            #print("you pressed {}".format(event.key))
            key_press_handler(event, canvas, toolbar)
        '''

        def _buttonCommandNext(root,fig):
            for keyi in keyList:
                if type(fleetAll[1]['total'][keyi]) is np.ndarray:
                    fig[keyi].clf()
                    plt.close(fig[keyi])
            root.quit()     # stops mainloop
            root.destroy()  # this is necessary on Windows to prevent
            
        def _buttonCommandShow(frameShow):
            frameShow.tkraise()

        frameEach = frame[keyi]
        frameEach.grid(row=0, column=0, sticky="nsew")

        # Canvas
        canvas = FigureCanvasTkAgg(fig[keyi], master=frameEach)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.03, rely=0.1)

        '''
        toolbar = NavigationToolbar2Tk(canvas, root)
        toolbar.update()
        canvas.get_tk_widget().grid(row=1, column=0)
        canvas.mpl_connect("key_press_event", _on_key_press)
        '''

        # Button
        button1 = Button(master=frameEach, text="Next Year", command=lambda: _buttonCommandNext(root,fig))
        button1.place(relx=0.22, rely=0.9)
        button2 = Button(master=frameEach, text="Show", command=lambda: _buttonCommandShow(frame[v.get()]))
        button2.place(relx=0.59, rely=0.9)

        # List box
        v = StringVar()
        lb = ttk.Combobox(frameEach,textvariable=v,values=keyList)
        lb.set(keyi)
        lb.place(relx=0.66, rely=0.9)

    # Tkinter Class
    root = Tk()
    root.title('Result in '+str(startYear+elapsedYear))
    root.geometry('800x600+300+200')
    width = 800
    height = 600
    placeX = root.winfo_screenwidth()/2 - width/2
    placeY = root.winfo_screenheight()/2 - height/2
    widgetSize = str(width)+'x'+str(height)+'+'+str(int(placeX))+'+'+str(int(placeY))
    root.geometry(widgetSize)

    fig = {}
    frame = {}
    keyList = list(fleetAll[1]['total'].keys())
    for keyi in keyList:
        if type(fleetAll[1]['total'][keyi]) is np.ndarray:
            fig[keyi] = outputAllCompany2Func(fleetAll,startYear,elapsedYear,keyi,unitDict)
            frame[keyi] = ttk.Frame(root, height=height, width=width)
    
    for keyi in keyList:
        if type(fleetAll[1]['total'][keyi]) is np.ndarray:
            _eachFrame(frame,fig,keyi,keyList,root)

    frame[keyList[0]].tkraise()

    # root
    mainloop()

def outputGui2Func(fleetAll,valueDict,startYear,elapsedYear,lastYear,tOpSch,unitDict):
    def _eachFrameCO2(frame,fig,keyi,ifTotal):
        def _buttonCommandShow(totalOrTilde):
            if totalOrTilde == 'Total':
                frameTotal[keyi].tkraise()
            else:
                frameComp[keyi].tkraise()

        frameEach = frame[keyi]
        frameEach.grid(row=0, column=1, pady=0,sticky="nsew")

        # Canvas
        canvas = FigureCanvasTkAgg(fig[keyi], master=frameEach)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.03, rely=0.1)

        # Button
        v1 = StringVar()
        button1 = ttk.Combobox(frameEach,textvariable=v1,values=['Total','Each company'])
        if ifTotal:
            button1.set('Total')
        else:
            button1.set('Each company')
        button1.place(relx=0.45, rely=0.9)

        button2 = Button(master=frameEach, text="Show", command=lambda: _buttonCommandShow(v1.get()))
        button2.place(relx=0.8, rely=0.9)

    def _eachFrameProfit(frame,fig,keyi):
        frameEach = frame[keyi]
        frameEach.grid(row=0, column=0, pady=0,sticky="nsew")

        # Canvas
        canvas = FigureCanvasTkAgg(fig[keyi], master=frameEach)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.03, rely=0.1)

    def _eachFrameIndex(frame,fig,keyi):
        frameEach = frame[keyi]
        frameEach.grid(row=1, column=0, pady=0,sticky="nsew")

        # Canvas
        canvas = FigureCanvasTkAgg(fig[keyi], master=frameEach)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.03, rely=0.1)

    def _eachFrameSel(frame,fig,keyi,keyList,ifSelTotal):
        def _buttonCommandShow(keyi,ifTotal):
            if ifTotal == 'Total':
                frameSelTotal[keyi].tkraise()
            else:
                frameSel[keyi].tkraise()
        
        def _buttonCommandNext(root,fig):
            for keyi in keyList:
                if type(fleetAll[1]['total'][keyi]) is np.ndarray:
                    fig[keyi].clf()
                    figTotal[keyi].clf()
                    plt.close(fig[keyi])
            root.quit()     # stops mainloop
            root.destroy()  # this is necessary on Windows to prevent

        frameEach = frame[keyi]
        frameEach.grid(row=1, column=1, pady=0, sticky="nsew")

        # Canvas
        canvas = FigureCanvasTkAgg(fig[keyi], master=frameEach)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.03, rely=0.1)

        # List box
        v1 = StringVar()
        lb = ttk.Combobox(frameEach,textvariable=v1,values=keyList)
        lb.set(keyi)
        lb.place(relx=0.45, rely=0.9)

        # Button
        v2 = StringVar()
        button1 = ttk.Combobox(frameEach,textvariable=v2,values=['Total','Each company'])
        if ifSelTotal:
            button1.set('Total')
        else:
            button1.set('Each company')
        button1.place(relx=0.02, rely=0.9)
        button2 = Button(master=frameEach, text="Show", command=lambda: _buttonCommandShow(v1.get(),v2.get()))
        button2.place(relx=0.8, rely=0.9)

        buttonNext = Button(master=root, text="Next Year", command=lambda: _buttonCommandNext(root,fig))
        buttonNext.place(relx=0.9, rely=0.9)
      
    # Tkinter Class
    root = Tk()
    root.title('Result in '+str(startYear+elapsedYear))
    width = root.winfo_screenwidth()-400
    height = root.winfo_screenheight()-80
    placeX = 0
    placeY = 0
    widgetSize = str(int(width))+'x'+str(int(height))+'+'+str(int(placeX))+'+'+str(int(placeY))
    root.geometry(widgetSize)

    fig = {}
    frameComp = {}
    frameTotal = {}
    frameSel = {}
    frameSelTotal = {}
    figTotal = {}
    removeList = []
    keyList = list(fleetAll[1]['total'].keys())
    figWidth,figHeight = width/2-50, height/2
    for keyi in keyList:
        if type(fleetAll[1]['total'][keyi]) is np.ndarray:
            fig[keyi] = outputAllCompany2Func(fleetAll,valueDict,startYear,elapsedYear,keyi,unitDict,figWidth/100-1,figHeight/100-1)
            figTotal[keyi] = outputAllCompanyTotalFunc(fleetAll,valueDict,startYear,elapsedYear,keyi,unitDict,figWidth/100-1,figHeight/100-1)
            frameComp[keyi] = ttk.Frame(root, height=figHeight, width=figWidth)
            frameTotal[keyi] = ttk.Frame(root, height=figHeight, width=figWidth)
            frameSel[keyi] = ttk.Frame(root, height=figHeight, width=figWidth)
            frameSelTotal[keyi] = ttk.Frame(root, height=figHeight, width=figWidth)
        else:
            removeList.append(keyi)

    for keyi in removeList:
        keyList.remove(keyi)
    

    _eachFrameCO2(frameComp,fig,'g',False)
    _eachFrameCO2(frameTotal,figTotal,'g',True)

    _eachFrameProfit(frameComp,fig,'profit')

    _eachFrameIndex(frameComp,fig,'Idx')

    for keyi in keyList:
        if type(fleetAll[1]['total'][keyi]) is np.ndarray:
            _eachFrameSel(frameSel,fig,keyi,keyList,False)
            _eachFrameSel(frameSelTotal,figTotal,keyi,keyList,True)
    #frame[keyList[0]].tkraise()

    # root
    mainloop()

    return fleetAll

def outputEachCompanyFunc(fleetAll,numCompany,startYear,elapsedYear,lastYear,tOpSch,decisionListName):
    fig, ax = plt.subplots(2, 2, figsize=(10.0, 10.0))
    plt.subplots_adjust(wspace=0.4, hspace=0.6)
    fleetAll[numCompany]['total'] = fleetAll[numCompany]['total']

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

def outputAllCompanyFunc(fleetAll,startYear,elapsedYear,lastYear,tOpSch,unitDict):
        
    currentYear = startYear+elapsedYear
    if elapsedYear > 0:
        year = fleetAll['year'][:elapsedYear+1]
        
        fig, axes = plt.subplots(3, 6, figsize=(16.0, 9.0))
        plt.subplots_adjust(wspace=0.4, hspace=0.6)

        for numCompany in range(1,4):
            for ax, keyi in zip(fig.axes, fleetAll[numCompany]['total'].keys()):
                ax.plot(year,fleetAll[numCompany]['total'][keyi][:elapsedYear+1],label="Company"+str(numCompany))
                ax.set_title(keyi)
                ax.set_xlabel('Year')
                ax.legend()
                #ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
                ax.set_ylabel(unitDict[keyi])
                ax.title.set_size(10)
                ax.xaxis.label.set_size(10)
                #ax.get_xaxis().get_major_formatter().set_useOffset(False)
                #ax.get_xaxis().set_major_locator(MaxNLocator(integer=True))
                ax.set_xticks(year)
                ax.yaxis.label.set_size(10)
    else:
        fig, axes = plt.subplots(3, 6, figsize=(16.0, 9.0))
        plt.subplots_adjust(wspace=0.4, hspace=0.6)

        for numCompany in range(1,4):
            for ax, keyi in zip(fig.axes, fleetAll[numCompany]['total'].keys()):
                ax.scatter(startYear,fleetAll[numCompany]['total'][keyi][0],label="Company"+str(numCompany))
                ax.set_title(keyi)
                ax.set_xlabel('Year')
                ax.legend()
                #ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
                ax.set_ylabel(unitDict[keyi])
                ax.title.set_size(10)
                ax.xaxis.label.set_size(10)
                #ax.set_xticks(np.array([startYear-1,startYear,startYear+1]))
                ax.set_xticks(np.array([startYear]))
                ax.yaxis.label.set_size(10)

    
    '''
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
    '''

    '''
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
    '''

    return fig

def outputAllCompany2Func(fleetAll,valueDict,startYear,elapsedYear,keyi,unitDict,figWidth,figHeight):
    plt.rcParams.update({'figure.max_open_warning': 0})
    currentYear = startYear+elapsedYear
    #fig, ax = plt.subplots(1, 1, figsize=(figWidth, figHeight))
    fig = Figure(figsize=(figWidth, figHeight))
    ax = fig.add_subplot(1,1,1)
    #plt.subplots_adjust(wspace=0.4, hspace=0.6)
    ticArr = np.array([2020,2025,2030,2035,2040,2045,2050])
    if elapsedYear > 0:
        year = fleetAll['year'][:elapsedYear+1]
        for numCompany in range(1,4):
            if numCompany == 1:
                color = 'tomato'
            elif numCompany == 2:
                color = 'gold'
            elif numCompany == 3:
                color = 'royalblue'
            ax.plot(year,fleetAll[numCompany]['total'][keyi][:elapsedYear+1],color=color, marker=".",label="Company"+str(numCompany))
            ax.set_title(keyi)
            ax.set_xlabel('Year')
            ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
            ax.set_ylabel(unitDict[keyi])
            #ax.title.set_size(10)
            #ax.xaxis.label.set_size(10)
            #ax.get_xaxis().get_major_formatter().set_useOffset(False)
            #ax.get_xaxis().set_major_locator(MaxNLocator(integer=True))
            ax.set_xticks(ticArr)
            #ax.yaxis.label.set_size(10)
    else:
        for numCompany in range(1,4):
            if numCompany == 1:
                color = 'tomato'
            elif numCompany == 2:
                color = 'gold'
            elif numCompany == 3:
                color = 'royalblue'
            ax.scatter(startYear,fleetAll[numCompany]['total'][keyi][0],color=color,label="Company"+str(numCompany))
            ax.set_title(keyi)
            ax.set_xlabel('Year')
            ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
            ax.set_ylabel(unitDict[keyi])
            #ax.title.set_size(10)
            #ax.xaxis.label.set_size(10)
            #ax.set_xticks(np.array([startYear-1,startYear,startYear+1]))
            ax.set_xticks(np.array([startYear]))
            #ax.yaxis.label.set_size(10)
    if keyi == 'g':
        IMOgoal = np.full(ticArr.shape,valueDict['IMOgoal']/3)
        color = 'olivedrab'
        ax.plot(ticArr,IMOgoal,color=color, marker=".",label="IMO goal")
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(0, y_max)
    ax.legend()
    return fig

def outputAllCompanyAppFunc(fleetAll,valueDict,startYear,elapsedYear,keyi,unitDict,figWidth,figHeight,NshipComp):
    plt.rcParams.update({'figure.max_open_warning': 0})
    currentYear = startYear+elapsedYear
    fig, ax = plt.subplots(1, 1, figsize=(figWidth, figHeight))
    #fig = Figure(figsize=(figWidth, figHeight))
    #ax = fig.add_subplot(1,1,1)
    #plt.subplots_adjust(wspace=0.4, hspace=0.6)
    ticArr = np.array([2020,2025,2030,2035,2040,2045,2050])
    if elapsedYear > 0:
        year = fleetAll['year'][:elapsedYear+1]
        for numCompany in range(1,NshipComp+1):
            if numCompany == 1:
                color = 'tomato'
            elif numCompany == 2:
                color = 'gold'
            elif numCompany == 3:
                color = 'royalblue'
            ax.plot(year,fleetAll[numCompany]['total'][keyi][:elapsedYear+1],color=color, marker=".",label="Company"+str(numCompany))
            ax.set_title(keyi)
            ax.set_xlabel('Year')
            ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
            ax.set_ylabel(unitDict[keyi])
            #ax.title.set_size(10)
            #ax.xaxis.label.set_size(10)
            #ax.get_xaxis().get_major_formatter().set_useOffset(False)
            #ax.get_xaxis().set_major_locator(MaxNLocator(integer=True))
            ax.set_xticks(ticArr)
            #ax.yaxis.label.set_size(10)
    else:
        for numCompany in range(1,NshipComp+1):
            if numCompany == 1:
                color = 'tomato'
            elif numCompany == 2:
                color = 'gold'
            elif numCompany == 3:
                color = 'royalblue'
            ax.scatter(startYear,fleetAll[numCompany]['total'][keyi][0],color=color,label="Company"+str(numCompany))
            ax.set_title(keyi)
            ax.set_xlabel('Year')
            ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
            ax.set_ylabel(unitDict[keyi])
            #ax.title.set_size(10)
            #ax.xaxis.label.set_size(10)
            #ax.set_xticks(np.array([startYear-1,startYear,startYear+1]))
            ax.set_xticks(np.array([startYear]))
            #ax.yaxis.label.set_size(10)
    if keyi == 'g':
        IMOgoal = np.full(ticArr.shape,valueDict['IMOgoal']/3)
        color = 'olivedrab'
        ax.plot(ticArr,IMOgoal,color=color, marker=".",label="IMO goal")
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(0, y_max)
    ax.legend()
    resPath = Path(__file__).parent
    #resPath /= '../app/static'
    resPath = 'roleplay/../app/static'
    plt.ioff()
    figName = keyi+'Each'+datetime.datetime.now().strftime('%Y%m%d%H%M%S')+'.png'
    plt.savefig(str(resPath)+'/'+figName)
    plt.close()
    return figName

def outputAllCompanyTotalAppFunc(fleetAll,valueDict,startYear,elapsedYear,keyi,unitDict,figWidth,figHeight,NshipComp):
    plt.rcParams.update({'figure.max_open_warning': 0})
    currentYear = startYear+elapsedYear
    fig, ax = plt.subplots(1, 1, figsize=(figWidth, figHeight))
    #fig = Figure(figsize=(figWidth, figHeight))
    #ax = fig.add_subplot(1,1,1)
    #plt.subplots_adjust(wspace=0.4, hspace=0.6)
    ticArr = np.array([2020,2025,2030,2035,2040,2045,2050])
    year = fleetAll['year'][:elapsedYear+1]
    for numCompany in range(1,NshipComp+1):
        if numCompany == 1:
            color = 'tomato'
        elif numCompany == 2:
            color = 'gold'
        elif numCompany == 3:
            color = 'royalblue'
        #ax.plot(year,fleetAll[numCompany]['total'][keyi][:elapsedYear+1],color=color, marker=".",label="Company"+str(numCompany))
        tempArr = copy.deepcopy(fleetAll[numCompany]['total'][keyi][:elapsedYear+1])
        if numCompany == 1:
            barArray = tempArr
            ax.bar(year, barArray, color=color, label="Company"+str(numCompany))
        else:
            ax.bar(year, tempArr, bottom=barArray, color=color, label="Company"+str(numCompany))
            barArray += tempArr
        ax.set_title(keyi)
        ax.set_xlabel('Year')
        ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
        ax.set_ylabel(unitDict[keyi])
        #ax.title.set_size(10)
        #ax.xaxis.label.set_size(10)
        #ax.get_xaxis().get_major_formatter().set_useOffset(False)
        #ax.get_xaxis().set_major_locator(MaxNLocator(integer=True))
        ax.set_xticks(ticArr)
        #ax.yaxis.label.set_size(10)
    if keyi == 'g':
        IMOgoal = np.full(ticArr.shape,valueDict['IMOgoal'])
        color = 'olivedrab'
        ax.plot(ticArr,IMOgoal,color=color, marker=".",label="IMO goal")
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(0, y_max)
    ax.legend()
    resPath = Path(__file__).parent
    #resPath /= '../app/static'
    resPath = 'roleplay/../app/static'
    plt.ioff()
    figName = keyi+'Total'+datetime.datetime.now().strftime('%Y%m%d%H%M%S')+'.png'
    plt.savefig(str(resPath)+'/'+figName)
    plt.close()
    return figName

def outputAllCompanyTotalFunc(fleetAll,valueDict,startYear,elapsedYear,keyi,unitDict,figWidth,figHeight):
    plt.rcParams.update({'figure.max_open_warning': 0})
    currentYear = startYear+elapsedYear
    #fig, ax = plt.subplots(1, 1, figsize=(figWidth, figHeight))
    fig = Figure(figsize=(figWidth, figHeight))
    ax = fig.add_subplot(1,1,1)
    #plt.subplots_adjust(wspace=0.4, hspace=0.6)
    ticArr = np.array([2020,2025,2030,2035,2040,2045,2050])
    if elapsedYear >= 0:
        year = fleetAll['year'][:elapsedYear+1]
        for numCompany in range(1,4):
            if numCompany == 1:
                color = 'tomato'
            elif numCompany == 2:
                color = 'gold'
            elif numCompany == 3:
                color = 'royalblue'
            #ax.plot(year,fleetAll[numCompany]['total'][keyi][:elapsedYear+1],color=color, marker=".",label="Company"+str(numCompany))
            tempArr = copy.deepcopy(fleetAll[numCompany]['total'][keyi][:elapsedYear+1])
            if numCompany == 1:
                barArray = tempArr
                ax.bar(year, barArray, color=color, label="Company"+str(numCompany))
            else:
                ax.bar(year, tempArr, bottom=barArray, color=color, label="Company"+str(numCompany))
                barArray += tempArr
            ax.set_title(keyi)
            ax.set_xlabel('Year')
            ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
            ax.set_ylabel(unitDict[keyi])
            #ax.title.set_size(10)
            #ax.xaxis.label.set_size(10)
            #ax.get_xaxis().get_major_formatter().set_useOffset(False)
            #ax.get_xaxis().set_major_locator(MaxNLocator(integer=True))
            ax.set_xticks(ticArr)
            #ax.yaxis.label.set_size(10)
    '''else:
        for numCompany in range(1,4):
            ax.scatter(startYear,fleetAll[numCompany]['total'][keyi][0],label="Company"+str(numCompany))
            ax.set_title(keyi)
            ax.set_xlabel('Year')
            ax.legend()
            ax.ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
            ax.set_ylabel(unitDict[keyi])
            #ax.title.set_size(10)
            #ax.xaxis.label.set_size(10)
            #ax.set_xticks(np.array([startYear-1,startYear,startYear+1]))
            ax.set_xticks(np.array([startYear]))
            #ax.yaxis.label.set_size(10)'''
    if keyi == 'g':
        IMOgoal = np.full(ticArr.shape,valueDict['IMOgoal'])
        color = 'olivedrab'
        ax.plot(ticArr,IMOgoal,color=color, marker=".",label="IMO goal")
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(0, y_max)
    ax.legend()
    return fig

def outputCsvFunc(fleetAll,startYear,elapsedYear,lastYear,tOpSch):
    resPath = Path(__file__).parent
    resPath /= '../results'
    shutil.rmtree(resPath)
    os.mkdir(resPath)
    year = fleetAll['year'][:elapsedYear+1]
    tOps = np.arange(tOpSch)
    for numCompany in range(1,4):
        valueName = []
        outputList = []
        for keyi in fleetAll[numCompany]['total'].keys():
            if type(fleetAll[numCompany]['total'][keyi]) is np.ndarray:
                valueName.append(keyi)
                outputList.append(fleetAll[numCompany]['total'][keyi][:elapsedYear+1])
                    
        outputData1 = np.stack(outputList,1)
        outputDf1 = pd.DataFrame(data=outputData1, index=year, columns=valueName, dtype='float')
        outputDf1.to_csv(str(resPath)+"\Company"+str(numCompany)+'.csv')

        for keyFleet in fleetAll[numCompany].keys():
            valueName = []
            outputList = []
            if type(keyFleet) is int:
                fleetAll[numCompany][keyFleet] = fleetAll[numCompany][keyFleet]
                for keyValue in fleetAll[numCompany][keyFleet].keys():
                    if type(fleetAll[numCompany][keyFleet][keyValue]) is np.ndarray:
                        valueName.append(keyValue)
                        outputList.append(fleetAll[numCompany][keyFleet][keyValue])
                
                outputData2 = np.stack(outputList,1)
                outputDf2 = pd.DataFrame(data=outputData2, index=fleetAll[numCompany][keyFleet]['year'], columns=valueName, dtype='float')
                outputDf2.to_csv(str(resPath)+"\Company"+str(numCompany)+'_'+'Fleet'+str(keyFleet)+'.csv')
