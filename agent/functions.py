# インポート
import numpy as np
import math
import matplotlib.pyplot as plt

## 規制フェーズ
# EEXI・補助率・税率を入力
def regulation(data, regulationList):
    for i in range(len(regulationList)):
        data[:, 3+i] = np.full(len(data), regulationList[i]).T
    return data

## 決定フェーズ
# 船の状態を更新
def availability(decisions, year):
    for agent in decisions:
        for fleet in agent:
            if (fleet[0] <= year) & (fleet[0]+20 >= year):
                fleet[7] = 1
            else:
                fleet[7] = 0
    return decisions

# 船を購入
def order(agentIndex, decisions, data, year, fuel, size, wps, sps, ccs,):
    newShip = np.array([year+2, fuel, size, wps, sps, ccs, 0, 0]).astype(float)
    emptyShip = np.zeros(8).astype(float)
    shape = decisions.shape
    decisions = decisions.reshape(decisions.size)
    for index in range(shape[0]):
        if index == agentIndex:
            decisions = np.insert(decisions, ((shape[1]+index)*index+shape[1])*shape[2], newShip)
        else:
            decisions = np.insert(decisions, ((shape[1]+index)*index+shape[1])*shape[2], emptyShip)
    decisions = decisions.reshape(shape[0], shape[1]+1, shape[2])
    fuelType = np.array([1, 1.05, 1.3, 2]).astype(float)
    data[agentIndex][11] = (fuelType[int(fuel)]+wps*0.1+sps*0.1+ccs*0.35)*(5101*size+35900000)*6
    return decisions, data

# 船をスクラップにする
def scrap(agentIndex, decisions, scrapList):
    for i in scrapList:
        decisions[agentIndex][i][7] = 0
    return decisions

# WPSを追加する
def wps(agentIndex, dicisions, data, fleetIndex, year):
    eqlhvShip = np.array([1, 40.4/48, 40.4/20.5, 40.4/120]).astype(float)
    eqlhvAux = np.array([1, 42.7/48, 42.7/20.5, 42.7/120]).astype(float)
    fuelTypeYear = np.array([[407, 518, 629, 740], [435, 524, 612, 701], [393, 419, 441, 459], [6347, 5234, 4232, 3341]]).astype(float)
    yearType = min([math.floor((year-2020)/10), 3])
    fuelType = np.array([1, 1.05, 1.3, 2]).astype(float)
    dicisions[agentIndex][fleetIndex][3] = 1
    costFuelDelta = fuel(data, decisions[agentIndex][fleetIndex], eqlhvShip, eqlhvAux)*fuelTypeYear[int(decisions[agentIndex][fleetIndex][1])][yearType]-6*fuelTypeYear[0][yearType]*(0.000000099*(1.28*(10.96*decisions[agentIndex][fleetIndex][2]+7024)+2376-(1-0.65*data[0][2])*(10.96*decisions[agentIndex][fleetIndex][2]+7024))*(1.28*(10.96*decisions[agentIndex][fleetIndex][2]+7024)+2376)**(-1/3)*(1.852*decisions[agentIndex][fleetIndex][6])**2*1.852*365*24*decisions[agentIndex][fleetIndex][6]*0.8+365*24*0.8/1000*(7.01+(10.96*decisions[agentIndex][fleetIndex][2]+7024)*0.0000868))
    costWps = (5101*decisions[agentIndex][fleetIndex][2]+35900000)*(fuelType[int(decisions[agentIndex][fleetIndex][1])]+decisions[agentIndex][fleetIndex][3]*0.1+decisions[agentIndex][fleetIndex][4]*0.1+decisions[agentIndex][fleetIndex][5]*0.35-1)
    data[agentIndex][12] = costFuelDelta+costWps*6
    return decisions, data

# SPSを追加する
def sps(agentIndex, dicisions, data, fleetIndex, year):
    eqlhvShip = np.array([1, 40.4/48, 40.4/20.5, 40.4/120]).astype(float)
    eqlhvAux = np.array([1, 42.7/48, 42.7/20.5, 42.7/120]).astype(float)
    fuelTypeYear = np.array([[407, 518, 629, 740], [435, 524, 612, 701], [393, 419, 441, 459], [6347, 5234, 4232, 3341]]).astype(float)
    yearType = min([math.floor((year-2020)/10), 3])
    fuelType = np.array([1, 1.05, 1.3, 2]).astype(float)
    dicisions[agentIndex][fleetIndex][4] = 1
    costFuelDelta = fuel(data, decisions[agentIndex][fleetIndex], eqlhvShip, eqlhvAux)*fuelTypeYear[int(decisions[agentIndex][fleetIndex][1])][yearType]-6*fuelTypeYear[0][yearType]*(0.000000099*(1.28*(10.96*decisions[agentIndex][fleetIndex][2]+7024)+2376-(1-0.65*data[0][2])*(10.96*decisions[agentIndex][fleetIndex][2]+7024))*(1.28*(10.96*decisions[agentIndex][fleetIndex][2]+7024)+2376)**(-1/3)*(1.852*decisions[agentIndex][fleetIndex][6])**2*1.852*365*24*decisions[agentIndex][fleetIndex][6]*0.8+365*24*0.8/1000*(7.01+(10.96*decisions[agentIndex][fleetIndex][2]+7024)*0.0000868))
    costSps = (5101*decisions[agentIndex][fleetIndex][2]+35900000)*(fuelType[int(decisions[agentIndex][fleetIndex][1])]+decisions[agentIndex][fleetIndex][3]*0.1+decisions[agentIndex][fleetIndex][4]*0.1+decisions[agentIndex][fleetIndex][5]*0.35-1)
    data[agentIndex][12] = costFuelDelta+costSps*6
    return decisions, data

# CCSを追加する
def css(agentIndex, dicisions, data, fleetIndex, year):
    eqlhvShip = np.array([1, 40.4/48, 40.4/20.5, 40.4/120]).astype(float)
    eqlhvAux = np.array([1, 42.7/48, 42.7/20.5, 42.7/120]).astype(float)
    fuelTypeYear = np.array([[407, 518, 629, 740], [435, 524, 612, 701], [393, 419, 441, 459], [6347, 5234, 4232, 3341]]).astype(float)
    yearType = min([math.floor((year-2020)/10), 3])
    fuelType = np.array([1, 1.05, 1.3, 2]).astype(float)
    dicisions[agentIndex][fleetIndex][5] = 1
    costFuelDelta = fuel(data, decisions[agentIndex][fleetIndex], eqlhvShip, eqlhvAux)*fuelTypeYear[int(decisions[agentIndex][fleetIndex][1])][yearType]-6*fuelTypeYear[0][yearType]*(0.000000099*(1.28*(10.96*decisions[agentIndex][fleetIndex][2]+7024)+2376-(1-0.65*data[0][2])*(10.96*decisions[agentIndex][fleetIndex][2]+7024))*(1.28*(10.96*decisions[agentIndex][fleetIndex][2]+7024)+2376)**(-1/3)*(1.852*decisions[agentIndex][fleetIndex][6])**2*1.852*365*24*decisions[agentIndex][fleetIndex][6]*0.8+365*24*0.8/1000*(7.01+(10.96*decisions[agentIndex][fleetIndex][2]+7024)*0.0000868))
    costCcs = (5101*decisions[agentIndex][fleetIndex][2]+35900000)*(fuelType[int(decisions[agentIndex][fleetIndex][1])]+decisions[agentIndex][fleetIndex][3]*0.1+decisions[agentIndex][fleetIndex][4]*0.1+decisions[agentIndex][fleetIndex][5]*0.35-1)
    data[agentIndex][12] = costFuelDelta+costCcs*6
    return decisions, data

# 特定の船の速度を特定の速さにする
def speedSet(agentIndex, decisions, fleet, speed):
    decisions[agentIndex][fleet][6] = speed
    return decisions

# 全ての船速を同じ値にする
def speedAll(agentIndex, decisions, speed):
    decisions[agentIndex][:, 6] = np.full(len(decisions[0]), speed).T
    return decisions

## 計算フェーズ
# 初期値を入力
def initialOperation(decisions, data, year):
    decisions = availability(decisions, year)
    data = demand(data, year)
    data = capacity(decisions, data)
    data = occupancyRate(data)
    return decisions, data

# 毎年の計算
def yearlyOperation(decisions, data, year):
    data = demand(data, year)
    data = capacity(decisions, data)
    data = occupancyRate(data)
    data = co2(decisions, data)
    data = sale(data)
    data = costFuel(decisions, data, year)
    data = subsidy_and_tax(data)
    data = profit(data)
    data = costTotal(data)
    return data

# グラフ出力用の配列を作成
def dataYearly(data, dataTotal, year, startYear):
    agentIndex = 0
    for agent in dataTotal:
        agent[year-startYear] = data[agentIndex]
        agentIndex += 1
    return dataTotal

# グラフ出力
def showResults(decisions, dataTotal, startYear, lastYear):
    x = np.arange(startYear, lastYear+1, 1)
    figTotal = plt.figure()
    figTotal.suptitle('Total')
    
    fig = figTotal.add_subplot(3, 2, 1)
    fig.set_title('Demand and Supply')
    y = dataTotal[0][:, 0]
    fig.plot(x, y)
    height = np.zeros(len(dataTotal[0]))
    for agent in dataTotal:
        z = agent[:, 1]
        fig.bar(x, z, bottom=height)
        height += z
    
    fig = figTotal.add_subplot(3, 2, 2)
    fig.set_title('Occupancy Rate')
    y = dataTotal[0][:, 2]
    fig.plot(x, y)
    
    fig = figTotal.add_subplot(3, 2, 3)
    fig.set_title('EEXI')
    s = dataTotal[0][:, 3]
    fig.plot(x, s)
    m = dataTotal[0][:, 4]
    fig.plot(x, m)
    l = dataTotal[0][:, 5]
    fig.plot(x, l)
    
    fig = figTotal.add_subplot(3, 2, 4)
    fig.set_title('Subsidy Rate and Tax Rate')
    y = dataTotal[0][:, 6]
    fig.plot(x, y)
    z = dataTotal[0][:, 7]
    fig.plot(x, z)
    
    fig = figTotal.add_subplot(3, 2, 5)
    fig.set_title('CO2')
    height = np.zeros(len(dataTotal[0]))
    for agent in dataTotal:
        y = agent[:, 1]
        fig.bar(x, y, bottom=height)
        height += y
    
    fig = figTotal.add_subplot(3, 2, 6)
    fig.set_title('Profit')
    height = np.zeros(len(dataTotal[0]))
    for agent in dataTotal:
        y = agent[:, 1]
        fig.bar(x, y, bottom=height)
        height += y
    
    figAgent = plt.figure()
    figAgent.suptitle('Agents')
    titles = ['CO2', 'Sale', 'Fuel Cost', 'Ship Cost', 'Refurbish Cost', 'Subsidy', 'Tax', 'Profit', 'TotalCost'] 
    for index in range(len(titles)):
        fig = figAgent.add_subplot(3, 3, index+1)
        fig.set_title(titles[index])
        for agent in dataTotal:
            y = agent[:, index+8]
            fig.plot(x, y)
    plt.show()

# 総需要を入力
def demand(data, year):
    data[:, 0] = np.full(len(data), 1000000000/20*(0.61*year**2-2400*year+2372174)).T
    return data

# 積載率を入力
def occupancyRate(data):
    demand = data[0][0]
    capacity = sum(data[:, 1])
    data[:, 2] = np.full(len(data), min([0.9, demand/capacity])).T
    return data

# 積載量を入力
def capacity(decisions, data):
    agentIndex = 0
    for agent in decisions:
        capacityTotal = 0
        for fleet in agent:
            if fleet[7] == 1:
                capacityTotal += fleet[2]*fleet[6]
        data[agentIndex][1] = capacityTotal*6*0.8*24*365
        agentIndex += 1
    return data

# CO2を入力
def co2(decisions, data):
    eqlhvShip = np.array([1, 40.4/48, 40.4/20.5, 40.4/120]).astype(float)
    eqlhvAux = np.array([1, 42.7/48, 42.7/20.5, 42.7/120]).astype(float)
    fuelType = np.array([3.16, 2.75, 0, 0]).astype(float)
    agentIndex = 0
    for agent in decisions:
        co2Total = 0
        for fleet in agent:
            if fleet[7] == 1:
                co2Total += (1-fleet[5]*0.85)*fuelType[int(fleet[1])]*fuel(data, fleet, eqlhvShip, eqlhvAux)
        data[agentIndex][8] = co2Total
        agentIndex +=1
    return data

# 売上げを入力
def sale(data):
    for agent in data:
        e = math.e
        agent[9] = agent[1]*agent[2]/5000*(2000/(1+e**(-20*(agent[2]-0.7)))+500)
    return data

# 燃料費を入力
def costFuel(decisions, data, year):
    eqlhvShip = np.array([1, 40.4/48, 40.4/20.5, 40.4/120]).astype(float)
    eqlhvAux = np.array([1, 42.7/48, 42.7/20.5, 42.7/120]).astype(float)
    fuelType = np.array([[407, 518, 629, 740], [435, 524, 612, 701], [393, 419, 441, 459], [6347, 5234, 4232, 3341]]).astype(float)
    yearType = min([math.floor((year-2020)/10), 3])
    agentIndex = 0
    for agent in decisions:
        costFuelTotal = 0
        for fleet in agent:
            if fleet[7] == 1:
                costFuelTotal += fuelType[int(fleet[1])][yearType]*fuel(data, fleet, eqlhvShip, eqlhvAux)
        data[agentIndex][10] = costFuelTotal
        agentIndex += 1
    return data

# 補助金と炭素税を入力
def subsidy_and_tax(data):
    for agent in data:
        agent[13] = agent[6]*agent[12]
        agent[14] = agent[7]*agent[8]
    return data

# 利益を入力
def profit(data):
    for agent in data:
        agent[15] = agent[9]-agent[16]+agent[13]-agent[14]
    return data

# 総コストを入力
def costTotal(data):
    for agent in data:
        agent[16] = agent[10]+agent[11]+agent[12]
    return data

# 消費燃料を計算
def fuel(data, fleet, eqlhvShip, eqlhvAux):
    fuelShip = eqlhvShip[int(fleet[1])]*(1-0.15*fleet[3])*0.000000099*(1.28*(10.96*fleet[2]+7024)+2376-(1-0.65*data[0][2])*(10.96*fleet[2]+7024))*(1.28*(10.96*fleet[2]+7024)+2376)**(-1/3)*(1.852*fleet[6])**2*1.852*365*24*fleet[6]*0.8
    fuelAux = eqlhvAux[int(fleet[1])]*(1-0.05*fleet[4])*365*24*0.8/1000*(7.01+(10.96*fleet[2]+7024)*0.0000868)
    return (fuelShip+fuelAux)*6