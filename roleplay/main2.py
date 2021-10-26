from . import sub2 as rs
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import interpolate
import csv
import matplotlib as mpl
#mpl.use('TkAgg')
import matplotlib.pyplot as plt
import os
import sys

#def roleplayRun(decisionListName1,decisionListName2,decisionListName3):
def roleplayRun():
    
    path = str(Path(__file__).parent)

    if os.name == 'nt':
        path = path.replace('roleplay','parameters') + '\\'
    elif os.name == 'posix':
        path = path.replace('roleplay','parameters') + '/'

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
    fleets = {'year': np.zeros(lastYear-startYear+1)}
    fleets = rs.fleetPreparationFunc(fleets,parameterFile6,1,startYear,lastYear,0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
    fleets = rs.fleetPreparationFunc(fleets,parameterFile7,2,startYear,lastYear,0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
    fleets = rs.fleetPreparationFunc(fleets,parameterFile8,3,startYear,lastYear,0,tOpSch,tbid,valueDict,NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)

    # prepare regulator decision
    regDec = rs.regPreFunc(len(regYear)+1)
    
    # prepare dicisionList dictionary
    #decisionList = {}
    #decisionList.setdefault(1,rs.decisionListFunc(parameterFile9))
    #decisionList.setdefault(2,rs.decisionListFunc(parameterFile10))
    #decisionList.setdefault(3,rs.decisionListFunc(parameterFile11))

    # start ship operation
    nRegAct = 0
    nRegDec = 0
    for elapsedYear in range(lastYear-startYear+1):
        currentYear = startYear+elapsedYear
        fleets['year'][elapsedYear] = currentYear

        #'''
        # requlator's decision phase
        if currentYear == regYear[nRegAct]:
            nRegDec += 1
            regDec = rs.regDecFunc(regDec,nRegDec,currentYear)
        if currentYear == regYear[nRegAct]+2:
            nRegAct += 1

        # scrap & refurbish, order and speed decision phase (also decide additional shipping fee per container)
        playOrder = np.array([1,2,3])
        sumCta = 0
        for numCompany in playOrder:
            fleets = rs.scrapRefurbishFunc(fleets,numCompany,elapsedYear,currentYear,valueDict,tOpSch,regDec['rEEDIreq'][nRegAct])
            if currentYear <= lastYear-2:
                fleets = rs.orderPhaseFunc(fleets,numCompany,valueDict,elapsedYear,tOpSch,tbid,currentYear,regDec['rEEDIreq'][nRegAct],NShipFleet,parameterFile2,parameterFile12,parameterFile3,parameterFile5)
            fleets = rs.decideSpeedFunc(fleets,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,valueDict)
            sumCta += fleets[numCompany]['total']['maxCta'][elapsedYear]

        # demand calculation
        Dtotal = rs.demandScenarioFunc(currentYear,valueDict["kDem1"],valueDict["kDem2"],valueDict["kDem3"],valueDict["kDem4"])
        for numCompany in playOrder:
            fleets[numCompany]['total']['demand'][elapsedYear] = Dtotal
            if Dtotal <= valueDict["rDMax"]*sumCta and Dtotal / sumCta > 0.0:
                fleets[numCompany]['total']['rocc'][elapsedYear] = Dtotal / sumCta
            elif Dtotal > valueDict["rDMax"]*sumCta:
                fleets[numCompany]['total']['rocc'][elapsedYear] = valueDict["rDMax"]
        
        # yearly operation phase
        for numCompany in playOrder.astype(int):
            fleets = rs.yearlyOperationFunc(fleets,numCompany,startYear,elapsedYear,NShipFleet,tOpSch,valueDict,regDec['Subsidy'][nRegAct],regDec['Ctax'][nRegAct],parameterFile4)
        #'''
        
        fleets = rs.outputGui2Func(fleets,valueDict,startYear,elapsedYear,lastYear,tOpSch,unitDict)
        #rs.outputGuiFunc(fleets,startYear,elapsedYear,lastYear,tOpSch,unitDict)
        
        
        
    
    rs.outputCsvFunc(fleets,startYear,elapsedYear,lastYear,tOpSch)

    #rs.outputEachCompanyFunc(fleets,1,startYear,elapsedYear,lastYear,tOpSch,decisionListName1)
    #rs.outputEachCompanyFunc(fleets,2,startYear,elapsedYear,lastYear,tOpSch,decisionListName2)
    #rs.outputEachCompanyFunc(fleets,3,startYear,elapsedYear,lastYear,tOpSch,decisionListName3)
    #decisionListNameList = [decisionListName1, decisionListName2, decisionListName3]
    #rs.outputAllCompanyFunc(fleets,startYear,elapsedYear,lastYear,tOpSch,unitDict,decisionListNameList)

