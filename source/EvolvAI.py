__author__ = 'Animadversio_Binxu'
from source.gameAICore import *
from random import gauss, random
import pickle, json
def clip(v, LB, UB):
    return min(UB, max(LB, v))

match_results = []
param_evol = []
sigma = dict(gamma=0.1, beta=0.1, alpha=0.1, HQWeight=0.1, enemyWeight=0.1, occupThreat=10)
bound = dict(gamma=(0, 4), beta=(0, 4), alpha=(0, 4), HQWeight=(0.5,10), enemyWeight=(0.5,10), occupThreat=(100,1000))
param0 = dict(gamma=1.5, beta=2.0, alpha=0.3, HQWeight=1, enemyWeight=2, occupThreat=500)
param1 = param0
T0 = time()
for geni in range(50):
    param1 = param0
    param2 = {k: clip(v + gauss(0, sigma[k]), *bound[k]) for k, v in param0.items()}
    print("Gen%d(%.3fsec)\nOriginal AI param %s\nPK Challenger AI param %s " % (geni, time() - T0, param1, param2,))
    # This is the basic loop for playing an action sequence step by step
    playerAI = {1: ("Origin", greedyRiskThreatMinMaxExactPolicy, param1),
                2: ("Mutant", greedyRiskThreatMinMaxExactPolicy, param2)}
    game = gameSetup2()
    winner12, gameDict12, act_record12 = gamePlay(game, playerAI, display=True)
    match_results.append((playerAI, winner12, gameDict12, act_record12))

    playerAI = {2: ("Origin", greedyRiskThreatMinMaxExactPolicy, param1),
                1: ("Mutant", greedyRiskThreatMinMaxExactPolicy, param2)}
    game = gameSetup2()
    winner21, gameDict21, act_record21 = gamePlay(game, playerAI, display=True)
    match_results.append((playerAI, winner21, gameDict21, act_record21))
    if winner21 == 2 and winner12 == 1:
        print("Gen%d(%.3fsec)\nOriginal AI win consistently param %s "%(geni, time() - T0, param1, ))
        param0 = param1
    elif winner21 == 1 and winner12 == 2:
        print("Gen%d(%.3fsec)\nChallenger AI win consistently param %s "%(geni, time() - T0, param2, ))
        param0 = param2
    else:
        param0 = {k1: (v1+v2)/2 for (k1,v1), (k2,v2) in zip(param1.items(), param2.items())}
        print("Gen%d(%.3fsec)\nTwo AI get tie! Merge them param %s " % (geni, time() - T0, param0, ))
    param_evol.append((geni, param1, param2, winner12, winner21, gameDict12, gameDict21))
    pickle.dump(param_evol, open("evol_param_trace2.pkl", "wb"))
    json.dump(param_evol, open("evol_param_trace2.json", mode="w"))
#%%
import pandas as pd
param0_tab = pd.DataFrame([param[1] for param in param_evol])
param1_tab = pd.DataFrame([param[2] for param in param_evol])
win_tab = pd.DataFrame([{"win12":param[3],"win21":param[4]} for param in param_evol])
stat_tab = pd.DataFrame([param[5] for param in param_evol])
summaryTab = pd.concat([param0_tab,param1_tab,win_tab,stat_tab],axis=1)
#%%
{'gamma': 1.95, 'beta': 2.00, 'alpha': 0.06, 'HQWeight': 1.32, 'enemyWeight': 1.64, 'occupThreat': 478}
playerAI = {2: ("Origin", greedyRiskThreatMinMaxExactPolicy, param0),
            1: "human"} #("Mutant", greedyRiskThreatMinMaxExactPolicy, param2)}4
game = gameSetup2()
winner_H, gameDict_H, act_record_H = gamePlay(game, playerAI, display=True)
# match_results.append((playerAI, winner12, gameDict12, act_record12))