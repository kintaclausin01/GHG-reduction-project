# エージェントの実行ファイル
import functions as fn
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

agentNum = 2 # エージェントの数を入力
import agent1 # エージェントを入力
csvInput0 = pd.read_csv(filepath_or_buffer='initialFleet1.csv', encoding='utf_8', sep=',') # 初期フリートを入力
initialFleet0 = csvInput0.values.astype(float) # 初期値をnumpy化
decisions = np.array([initialFleet0, initialFleet0]).astype(float) # エージェントの数だけ作る

data = np.zeros((agentNum, 17)).astype(float)
dataTotal = np.array([]).astype(float)
startYear = 2020 # 開始年を入力
lastYear = 2050 # 終了年を入力
dataTotal = np.zeros(((agentNum, lastYear-startYear+1, len(data[0]))))
year = startYear

decisions, data = fn.initialOperation(decisions, data, year)
while year <= lastYear:
    decisions = fn.availability(decisions, year)

    decisions, data = agent1.agent1(0, decisions, data, year) # エージェントの数だけ実行
    decisions, data = agent1.agent1(1, decisions, data, year) # エージェントの数だけ実行

    data = fn.yearlyOperation(decisions, data, year)
    dataTotal = fn.dataYearly(data, dataTotal, year, startYear)
    year += 1

fn.showResults(decisions, dataTotal, startYear, lastYear)