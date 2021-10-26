# 毎年最大の船を買い，全船速20
import functions as fn
def agent1(agentIndex, decisions, data, year):
    decisions, data = fn.order(agentIndex, decisions, data, year, 0, 24000, 0, 0, 0)
    decisions = fn.speedAll(agentIndex, decisions, 20)
    return decisions, data