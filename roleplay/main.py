from . import sub as rs
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import interpolate
import csv
import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt

def roleplayRun():
    elapsedYear = 0
    tOpSch = 5
    startYear = 2021
    lastYear = 2025
    Di = 100000
    NShipFleet = 20
    Alpha = 1
    tbid = 2

    path = str(Path(__file__).parent)
    path = path.replace('roleplay','parameters')
    parameterFile1 = path+"\\variableAll3.csv"
    parameterFile2 = path+"\\eqLHV.csv"
    parameterFile3 = path+"\\CO2Eff.csv"
    parameterFile4 = path+"\\unitCostFuel.csv"
    parameterFile5 = path+"\\costShipBasic.csv"

    variableAll, valueDict = rs.readinput(parameterFile1)

    # prepare initial fleets
    fleets = {'S': np.zeros(lastYear-startYear+1)}
    fleets['year'] = np.zeros(lastYear-startYear+1)
    orderYear = 2016 # must be less than startYear - tbid
    iniT = startYear-orderYear-tbid
    fleets = rs.orderShipFunc(fleets,'HFO','1','1','1',20000,tOpSch,tbid,iniT,orderYear,parameterFile2,parameterFile3,parameterFile5)

    # start ship operation
    for i in range(lastYear-startYear+1):
    # scrap old fleet
        for j in range(1,len(fleets)-1):
            if fleets[j]['tOp'] == tOpSch:
                print('    Fleet',j,'was scrapped due to too old.')

    # order fleet
        fleets = rs.orderShipInputFunc(fleets,tOpSch,tbid,0,startYear+i,parameterFile2,parameterFile3,parameterFile5)
        
        fleets = rs.yearlyOperationInputFunc(fleets,Di,startYear,i,NShipFleet,Alpha,tOpSch,valueDict,parameterFile4)
    
        #rs.outputFunc(fleets,startYear,i,tOpSch)
        # g or others should be summed up