#%%
__author__ = 'Animadversio_Binxu'
from random import choice, shuffle
from itertools import chain
# from numpy.random import permutation
from time import time
from copy import copy, deepcopy
from source.util import Queue, Stack, PriorityQueue
from source.gameCore import *
#%%
# game = GameStateCtrl()
# game.GUI_loop()
#%% Heuristic Policies
""" Policies """
def randomPolicy(game, oneunit=False):
    """Select random action from the legal action space"""
    T0 = time()
    actseq, cumrew, curGame = [], 0, deepcopy(game)
    while True:
        moves, nextUIstate = curGame.getPossibleMoves()
        move = choice(moves)
        actseq.append(move)
        curGame, nextrewards = curGame.action_execute(*move, clone=False, show=False, reward=True)
        cumrew += nextrewards[curGame.curPlayer - 1]
        if oneunit and (move[0] in ["AOE","attack","stand","turnover"]): # end sample when one unit finish move
            break
        if not oneunit and move[0] == "turnover":  # end sample when turn is over
            break
    print("Random Traj finished %.2f sec, best rew %d" % (time() - T0, cumrew))
    return actseq, curGame, cumrew


def greedyPolicy(game, show=True, perm=False):
    """Search the action space of selection, move, attack.
    that maximize
            next step reward
    This is the prototype for all the following policies. Basic Queue search structure is the same, but the thing to
        maximize are different.
    """
    T0 = time()
    movseq_col = Stack()
    movseq_col.push(([], 0, game))
    whole_movseqs = PriorityQueue()  # [] #
    while not movseq_col.isEmpty():
        actseq, cumrew, curGame = movseq_col.pop()
        moves, nextUIstate = curGame.getPossibleMoves()
        if perm: shuffle(moves)  # moves = [moves[i] for i in permutation(len(moves))]
        for move in moves:  #
            next_actseq = copy(actseq)
            next_actseq.append(move)
            nextGame, nextrewards = curGame.action_execute(*move, clone=True, show=False, reward=True, checklegal=False)
            nextcumrew = cumrew + nextrewards[curGame.curPlayer - 1]  # use the reward for this player
            if move[0] in ["AOE","attack","stand","turnover"]:  # tree termination condition
                whole_movseqs.push((next_actseq, nextGame, nextcumrew), -nextcumrew)
                continue
            # move = choice(moves)
            movseq_col.push((next_actseq, nextcumrew, nextGame))
    # print(whole_movseqs)
    best_seq, best_state, best_rew = whole_movseqs.pop()
    if show: print("DFS finished %.2f sec, best rew %d" % (time() - T0, best_rew))
    return best_seq, best_state, best_rew


def greedyPolicy_approx(game, show=True, perm=False):
    """Search the action space of selection, move, attack that maximize
            next step reward

    Note, this routine function is used as the core of threat estimation. Thus its speed is optimized a lot!
    In `threat_unit` and `threat_pos` function it's used as the policy of the
        opponent.  the MoveAttackPair is used to fuse the steps and reduce search space.
        `getCombatStats` is used to simulate fight instead of conduct fight.
        Note here only attack reward is considered. Unit purchasing reward is not counted.
        Major part is to evaluation the enemy action sequence without really execute it. 
    """
    T0 = time()
    whole_movseqs = PriorityQueue()
    if game.UIstate == SELECT_MOVTARGET and game.curUnit is not None:  # This part is used by `threat_unit`
        """Best move after selecting an unit."""
        AtkMvPairs, MvStandPairs, AOEAtkPairs = game.getMovAttPair(game.curUnit)  # FIXED for AOE unit.
        for movact, atkact, attackedUnit in AtkMvPairs:
            harm, atkd_alive, harm2, atkr_alive, atkrReward = game.getCombatStats(game.curUnit,
                    attackedUnit, atkrpos=movact[1][0], atkdpos=atkact[1][0])
            # TODO may be do filtering to avoid being killed in attack
            whole_movseqs.push(([movact, atkact], atkrReward), -atkrReward)
        for movact, AOEact in AOEAtkPairs:
            harms, alives, AOEReward = game.getAOEStats(game.curUnit, AOEact[1][1], )
            whole_movseqs.push(([movact, AOEact], AOEReward), -AOEReward)
        for movact, standact in MvStandPairs:
            whole_movseqs.push(([movact, standact], 0), 0.0)
    elif game.UIstate == SELECT_UNIT:  # This part is used by `threat_general`
        selectablePos, selectableUnits = game.getSelectableUnit(unitList=None, curPlayer=None)
        for selPos, selUnit in zip(selectablePos, selectableUnits):
            AtkMvPairs, MvStandPairs, AOEAtkPairs = game.getMovAttPair(selUnit)  # FIXED for AOE unit.
            for movact, atkact, attackedUnit in AtkMvPairs:
                harm, atkd_alive, harm2, atkr_alive, atkrReward = game.getCombatStats(selUnit,
                                              attackedUnit, atkrpos=movact[1][0], atkdpos=atkact[1][0])
                # TODO may be do filtering to avoid being killed in attack
                whole_movseqs.push(([("select", [selPos]), movact, atkact], atkrReward), -atkrReward)
            for movact, AOEact in AOEAtkPairs:
                harms, alives, AOEReward = game.getAOEStats(selUnit, AOEact[1][1], )
                whole_movseqs.push(([("select", [selPos]), movact, AOEact], AOEReward), -AOEReward)
            for movact, standact in MvStandPairs:
                whole_movseqs.push(([("select", [selPos]), movact, standact], 0), 0.0)
        # Add buying to the considerations here.
        viablePos, viableTile = game.getPurchasablePos()
        affordableUnitType, affordableUnits = game.getAffordableUnit()
        for buyPos in viablePos:
            for unitType, buyUnit in zip(affordableUnitType, affordableUnits):
                buyUnit.pos = buyPos
                AtkMvPairs, MvStandPairs, AOEAtkPairs = game.getMovAttPair(buyUnit)  # FIXED for AOE unit.
                for movact, atkact, attackedUnit in AtkMvPairs:
                    harm, atkd_alive, harm2, atkr_alive, atkrReward = game.getCombatStats(buyUnit,
                                attackedUnit,atkrpos=movact[1][0],atkdpos=atkact[1][0])
                    # TODO may be do filtering to avoid being killed in attack
                    whole_movseqs.push(([("buy", [buyPos, unitType]), ("select", [buyPos]), movact, atkact], atkrReward), -atkrReward)
                for movact, AOEact in AOEAtkPairs:
                    harms, alives, AOEReward = game.getAOEStats(buyUnit, AOEact[1][1], )
                    whole_movseqs.push(([("buy", [buyPos, unitType]), ("select", [buyPos]), movact, AOEact], AOEReward), -AOEReward)
                for movact, standact in MvStandPairs:
                    whole_movseqs.push(([("buy", [buyPos, unitType]), ("select", [buyPos]), movact, standact], 0), 0.0)
    best_seq, best_rew = whole_movseqs.pop()
    if show: print("Approx Action maximization finished %.2f sec, best rew %d" % (time() - T0, best_rew))
    return best_seq, None, best_rew  # None is the state.

def bestMovAttSeq(game, curunit, enemyHQpos=set(), occupReward=500):
    best_seq, best_rew = None, -1E8
    AtkMvPairs, MvStandPairs, AOEAtkPairs = game.getMovAttPair(curunit)  # FIXED for AOE unit.
    for movact, atkact, attackedUnit in AtkMvPairs:
        occupRew = (movact[1][0] in enemyHQpos) * occupReward
        harm, atkd_alive, harm2, atkr_alive, atkrReward = game.getCombatStats(curunit,
                                                                              attackedUnit, atkrpos=movact[1][0],
                                                                              atkdpos=atkact[1][0])
        # TODO may be do filtering to avoid being killed in attack
        if best_rew < atkrReward + occupRew: best_seq, best_rew = ([movact, atkact], atkrReward + occupRew)
    for movact, AOEact in AOEAtkPairs:
        occupRew = (movact[1][0] in enemyHQpos) * occupReward
        harms, alives, AOEReward = game.getAOEStats(curunit, AOEact[1][1], )
        if best_rew < AOEReward + occupRew: best_seq, best_rew = ([movact, AOEact], AOEReward + occupRew)
    for movact, standact in MvStandPairs:
        occupRew = (movact[1][0] in enemyHQpos) * occupReward
        if best_rew < occupRew: best_seq, best_rew = ([movact, standact], occupRew)
    return best_seq, best_rew

def _threat_greedyOccupPolicy(game, show=True, occupReward=500):
    """Get rid of tha action, retain the threat part. Esp. Add threat value for occupying the other sides' HQ"""
    T0 = time()
    # whole_movseqs = PriorityQueue()
    best_seq, best_rew = None, -1E8
    HQpos, _ = game.getEnemyHQPos()
    HQpos = set(HQpos)
    if game.UIstate == SELECT_MOVTARGET and game.curUnit is not None:  # This part is used by `threat_unit`
        """Best move after selecting an unit."""
        curbest_seq, curbest_rew = bestMovAttSeq(game, game.curUnit, enemyHQpos=HQpos, occupReward=occupReward)
        if best_rew < curbest_rew: best_seq, best_rew = curbest_seq, curbest_rew

    elif game.UIstate == SELECT_UNIT:  # This part is used by `threat_general`
        selectablePos, selectableUnits = game.getSelectableUnit(unitList=None, curPlayer=None)
        for selPos, selUnit in zip(selectablePos, selectableUnits):
            curbest_seq, curbest_rew = bestMovAttSeq(game, selUnit, enemyHQpos=HQpos, occupReward=occupReward)
            if best_rew < curbest_rew: best_seq, best_rew = [("select", [selPos]), *curbest_seq], curbest_rew
        """Best Move after buying a new unit."""
        viablePos, viableTile = game.getPurchasablePos()
        affordableUnitType, affordableUnits = game.getAffordableUnit()
        for buyPos in viablePos:
            for unitType, buyUnit in zip(affordableUnitType, affordableUnits):
                buyUnit.pos = buyPos
                curbest_seq, curbest_rew = bestMovAttSeq(game, buyUnit, enemyHQpos=HQpos, occupReward=occupReward)
                if best_rew < curbest_rew:  best_seq, best_rew = [("buy", [buyPos, unitType]), *curbest_seq], curbest_rew
    if show: print("Approx Action maximization finished %.2f sec, best rew %d" % (time() - T0, best_rew))
    return best_seq, None, best_rew  # None is the state.


def greedyRiskMinPolicy(game, show=True, perm=False, alpha=1.0):
    """
    Search the action space that maximize
            next step reward - alpha * risk(pos)
    Risk is defined by how much that location is covered by the other's attack.
    This is a good example of a slightly more complex policy
    """
    T0 = time()
    # Chart the enemy's coverages
    allEnemyPos, allEnemyUnit = game.getAllEnemyUnit()
    enemyCoverSets = {}  # the set of position that enemy can cover.
    harmValues = {}  # Attack value
    for pos, unit in zip(allEnemyPos, allEnemyUnit):
        coverSet = game.getUnitAttackCoverage(unit,)
        enemyCoverSets[pos] = coverSet
        harmValues[pos] = unit.Attack * unit.HP / 100.0  # TODO, minus the terrain defence

    def riskFun(pos, mask=[]):
        risk = 0.0
        for tarPos, coverSet in enemyCoverSets.items():
            if tarPos in mask: continue # the unit you just attacked...
            if pos in coverSet:
                # risk += harmValues[tarPos]  # Here it can be expectation, sum or Max.
                risk = max(risk, harmValues[tarPos])
        return risk

    movseq_col = Stack()
    movseq_col.push(([], 0, 0, game))
    whole_movseqs = PriorityQueue()
    while not movseq_col.isEmpty():
        actseq, cumrew, cumrisk, curGame = movseq_col.pop()
        moves, nextUIstate = curGame.getPossibleMoves()
        if perm: shuffle(moves)  # moves = [moves[i] for i in permutation(len(moves))]
        for move in moves:
            nextrisk = cumrisk
            next_actseq = copy(actseq)
            next_actseq.append(move)
            nextGame, nextrewards = curGame.action_execute(*move, clone=True, show=False, reward=True, checklegal=False)
            # Evaluation of the new Game state
            nextcumrew = cumrew + nextrewards[curGame.curIdx]  # use the reward for this player
            if move[0] in ["move"]:
                maxHarm = max(0.0, riskFun(move[1][0], mask=[]) - nextGame.curUnit.Defence)
                nextrisk += maxHarm / 100.0 * unitPrice(nextGame.curUnit) \
                    + (maxHarm >= nextGame.curUnit.HP) * unitPrice(nextGame.curUnit) # Additional risk for death.
                # TODO: Here the unitPrice could be extended to be the strategic value instead of purely price. (Considering its location etc.) can mask out more...
            if move[0] in ["AOE", "attack", "stand", "turnover"]:  # Search Tree terminates
                whole_movseqs.push((next_actseq, nextGame, nextcumrew, nextrisk), -nextcumrew + nextrisk * alpha)
                continue
            else:  # Search Tree continues
                movseq_col.push((next_actseq, nextcumrew, nextrisk, nextGame))
    best_seq, best_state, best_rew, bestrisk,  = whole_movseqs.pop()
    if show: print("DFS finished %.2f sec, best rew %d, least risk %d" % (time() - T0, best_rew, bestrisk))
    return best_seq, best_state, best_rew

# Threat of a unit, computed by recursive algorithm.
def threat_unit(game, unit, oppoPolicy=_threat_greedyOccupPolicy, policyParam={}):
    """ Meta method for estimating the threat of an enemy unit.
    The threat of a unit is affected by the state of unit and the opponent's policy.
    Under oppopolicy, the opponent's best move to achieve the maximal damage with a unit is the threat.
    Note here the oppoPolicy outputs single unit action seq instead of all unit actions.
        i.e. termination condition is finishing the tree for one unit.
    """
    hypo_game = deepcopy(game)
    if unit.player is not hypo_game.curPlayer:
        hypo_game.endTurn(show=False)
    # hypo_game.selectUnit(unit.pos)
    hypo_game.curUnit = hypo_game.unitList[game.unitList.index(unit)]
    hypo_game.curUnit.moved = False
    hypo_game.UIstate = SELECT_MOVTARGET
    bestenemy_seq, bestenemy_state, bestenemy_rew = oppoPolicy(hypo_game, show=False, **policyParam)
    return bestenemy_rew, bestenemy_seq


def threat_pos(game, pos, oppoPolicy=_threat_greedyOccupPolicy, policyParam={}):
    """ Meta method for estimating the threat of an enemy unit at pos
    Just another interface for the `threat_unit` function.
    """
    hypo_game = deepcopy(game)
    poslist = [unit.pos for unit in hypo_game.unitList]
    if pos not in poslist: # maybe that unit has died...
        return 0.0, []
    unit = hypo_game.unitList[poslist.index(pos)]
    if unit.player is not hypo_game.curPlayer:
        hypo_game.endTurn(show=False)
    # hypo_game.selectUnit(pos)
    hypo_game.curUnit = unit
    hypo_game.curUnit.moved = False
    hypo_game.UIstate = SELECT_MOVTARGET
    bestenemy_seq, bestenemy_state, bestenemy_rew = oppoPolicy(hypo_game, show=False, **policyParam)
    return bestenemy_rew, bestenemy_seq


def threat_general(game, curPlayer, oppoPolicy=_threat_greedyOccupPolicy, policyParam={}):
    """ Max over all possible units for the opponents is the general threat. """
    hypo_game = deepcopy(game)
    if curPlayer is hypo_game.curPlayer:
        hypo_game.endTurn(show=False)
    hypo_game.curUnit = None
    hypo_game.UIstate = SELECT_UNIT
    bestenemy_seq, bestenemy_state, bestenemy_rew = oppoPolicy(hypo_game, show=False, **policyParam)
    return bestenemy_rew, bestenemy_seq


def computeHPloss(curGame, nextGame, targ_pos):
    """Useful utility to compute the HP loss at given location in 2 game obj. Assume it's the same enemy"""
    poslist = [unit.pos for unit in curGame.unitList]
    nextposlist = [unit.pos for unit in nextGame.unitList]
    HP = curGame.unitList[poslist.index(targ_pos)].HP if targ_pos in poslist else 0
    HPnext = nextGame.unitList[nextposlist.index(targ_pos)].HP if targ_pos in nextposlist else 0
    HPloss = HP - HPnext  # FIX BUG in HPLoss
    return HPloss


def ThreatElimPolicy(game, gamma=0.9, perm=True):
    """Search the action space of selection, move, attack
    Maximize the threats eliminated """
    T0 = time()
    threat_bsl, _ = threat_general(game, game.curPlayer)
    targetPos, targetUnit = game.getAllEnemyUnit()
    threat_dict = {}
    for pos in targetPos:
        threat_bef, _ = threat_pos(game, pos)
        threat_dict[pos] = threat_bef
    movseq_col = Stack()  # DFS for action sequence
    movseq_col.push(([], 0, game))
    whole_movseqs = PriorityQueue()
    while not movseq_col.isEmpty():
        actseq, cumrew, curGame = movseq_col.pop()
        moves, nextUIstate = curGame.getPossibleMoves()
        if perm: shuffle(moves)  # [moves[i] for i in permutation(len(moves))]
        for move in moves:#
            next_actseq = copy(actseq)
            next_actseq.append(move)
            nextGame, nextrewards = curGame.action_execute(*move, clone=True, show=False, reward=True, checklegal=False)
            nextcumrew = cumrew + nextrewards[curGame.curIdx]  # use the reward for this player
            thr_elim_val = 0
            # TODO AOE
            if move[0] is "attack":
                targ_pos = move[1][0]
                # threat_aft, _ = threat_pos(nextGame, targ_pos)
                # thr_elim_val = threat_bef - threat_aft # This is more accurate MC method
                threat_bef = threat_dict[targ_pos]
                harmPercent = computeHPloss(curGame, nextGame, targ_pos) / 100.0
                thr_elim_val += threat_bef * harmPercent  # This is an approximation to the threat reduced.
            if move[0] is "AOE":  # Sum up the reduced HP and reduced threat for affected units.
                for targ_pos in move[1][1]:  # targetPosList for AOE attack
                    threat_bef = threat_dict[targ_pos]
                    harmPercent = computeHPloss(curGame, nextGame, targ_pos) / 100.0
                    thr_elim_val += threat_bef * harmPercent
            print("Threat Value reduced by %.1f" % (thr_elim_val))
            # if move[0] in ["AOE","attack"]:
            #     threat_all_aft, _ = threat_general(curGame, curGame.curPlayer)
            #     thr_elim_val = threat_bsl - threat_all_aft
            #     print("Threat Value reduced by %.1f" % (thr_elim_val, ))
            if move[0] in ["AOE", "attack", "stand", "turnover"]:
                whole_movseqs.push((next_actseq, nextGame, nextcumrew), -nextcumrew - thr_elim_val * gamma)
                continue
            else:
                movseq_col.push((next_actseq, nextcumrew, nextGame))
    best_seq, best_state, best_rew = whole_movseqs.pop()
    print("DFS + Threat Reduce finished %.2f sec, best rew %d" % (time() - T0, best_rew))
    return best_seq, best_state, best_rew


def ThreatElimPolicy_recurs(game, show=True, gamma=0.9, perm=True, recursL=1):
    """Search the action space of selection, move, attack"""
    if recursL <= 0:
        best_seq, best_state, best_rew = greedyPolicy(game, show=show, perm=perm)
        return best_seq, best_state, best_rew
    T0 = time()
    # threat_bsl, _ = threat_general(game, game.curPlayer, oppoPolicy=ThreatElimPolicy_recurs,
    #                                policyParam={"recursL": recursL-1})
    targetPos, targetUnit = game.getAllEnemyUnit()
    threat_dict = {}  # threats are computed in a recursive fashion.
    for pos in targetPos:
        threat_bef, _ = threat_pos(game, pos, oppoPolicy=ThreatElimPolicy_recurs,
                                   policyParam={"recursL": recursL-1})
        threat_dict[pos] = threat_bef
    movseq_col = Stack()
    movseq_col.push(([], 0, game))
    whole_movseqs = PriorityQueue()  # [] #
    while not movseq_col.isEmpty():
        actseq, cumrew, curGame = movseq_col.pop()
        moves, nextUIstate = curGame.getPossibleMoves()
        if perm: shuffle(moves)  # [moves[i] for i in permutation(len(moves))]
        for move in moves:#
            next_actseq = copy(actseq)
            next_actseq.append(move)
            nextGame, nextrewards = curGame.action_execute(*move, clone=True, show=False, reward=True, checklegal=False)
            nextcumrew = cumrew + nextrewards[curGame.curPlayer - 1] # use the reward for this player
            thr_elim_val = 0
            if move[0] is "attack":
                targ_pos = move[1][0]
                # threat_aft, _ = threat_pos(nextGame, targ_pos)
                # thr_elim_val = threat_bef - threat_aft # This is more accurate MC method
                threat_bef = threat_dict[targ_pos]
                harmPercent = computeHPloss(curGame, nextGame, targ_pos) / 100.0
                thr_elim_val += threat_bef * harmPercent  # This is less accurate
            if move[0] is "AOE":
                for targ_pos in move[1][1]:  # targetPosList for AOE attack
                    threat_bef = threat_dict[targ_pos]
                    harmPercent = computeHPloss(curGame, nextGame, targ_pos) / 100.0
                    thr_elim_val += threat_bef * harmPercent
            if show: print("Lev %d Threat Value reduced by %.1f" % (recursL, thr_elim_val))
            # if move[0] in ["AOE","attack"]:
            #     threat_all_aft, _ = threat_general(curGame, curGame.curPlayer)
            #     thr_elim_val = threat_bsl - threat_all_aft
            #     print("Threat Value reduced by %.1f" % (thr_elim_val, ))
            if move[0] in ["AOE","attack","stand","turnover"]:
                whole_movseqs.push((next_actseq, nextGame, nextcumrew), -nextcumrew - thr_elim_val * gamma)
                continue
            movseq_col.push((next_actseq, nextcumrew, nextGame))
    best_seq, best_state, best_rew = whole_movseqs.pop()
    print("DFS + Threat Reduce finished %.2f sec, best rew %d" % (time() - T0, best_rew))
    return best_seq, best_state, best_rew


def greedyRiskThreatMinPolicy(game, show=True, perm=False, gamma=0.9, alpha=0.2):
    """Search the action space of selection, move, attack
    Search the action space that maximize
            next step reward + gamma * threat_elim - alpha * risk(pos)
    """
    T0 = time()
    # Chart the enemy's coverages
    allEnemyPos, allEnemyUnit = game.getAllEnemyUnit()
    threat_dict = {}
    enemyCoverSets = {}
    harmValues = {}
    for pos, unit in zip(allEnemyPos, allEnemyUnit):
        coverSet = game.getUnitAttackCoverage(unit,)
        enemyCoverSets[pos] = coverSet
        harmValues[pos] = unit.Attack * unit.HP / 100.0
        threat_bef, _ = threat_pos(game, pos)
        threat_dict[pos] = threat_bef

    def riskFun(pos, mask=[]):
        risk = 0.0
        for tarPos, coverSet in enemyCoverSets.items():
            if tarPos in mask: continue # the unit you just attacked...
            if pos in coverSet:
                # risk += harmValues[tarPos]
                risk = max(risk, harmValues[tarPos])
        return risk

    movseq_col = Stack()  # Note the search tree is maintained by stack, so it's a BFS not A*
    movseq_col.push(([], 0, 0, game))
    whole_movseqs = PriorityQueue()  # [] #
    while not movseq_col.isEmpty():
        actseq, cumrew, cumrisk, curGame = movseq_col.pop()
        # if curGame.UIstate == SELECT_MOVTARGET:
        moves, nextUIstate = curGame.getPossibleMoves()
        if perm: shuffle(moves)  # moves = [moves[i] for i in permutation(len(moves))]
        for move in moves:  #
            nextrisk = cumrisk
            next_actseq = copy(actseq)
            next_actseq.append(move)
            nextGame, nextrewards = curGame.action_execute(*move, clone=True, show=False, reward=True, checklegal=False)
            # Evaluate the nextState x this move
            nextcumrew = cumrew + nextrewards[curGame.curIdx]  # use the reward for this player
            if move[0] in ["move"]:  # can mask out more the one you attack pose less threat to you
                maxHarm = max(0.0, riskFun(move[1][0], mask=[]) - nextGame.curUnit.Defence)
                nextrisk += maxHarm / 100.0 * unitPrice(nextGame.curUnit) \
                        + (maxHarm >= nextGame.curUnit.HP) * unitPrice(nextGame.curUnit)  # Additional risk for death.
                # TODO: Here the unitPrice could be extended to be the strategic value instead of purely price. (Considering its location etc.) can mask out more...
            thr_elim_val = 0
            if move[0] is "attack":
                targ_pos = move[1][0]
                threat_bef = threat_dict[targ_pos]
                harmPercent = computeHPloss(curGame, nextGame, targ_pos) / 100.0
                thr_elim_val += threat_bef * harmPercent  # This is less accurate
            if move[0] is "AOE":
                for targ_pos in move[1][1]:  # targetPosList for AOE attack
                    threat_bef = threat_dict[targ_pos]
                    harmPercent = computeHPloss(curGame, nextGame, targ_pos) / 100.0
                    thr_elim_val += threat_bef * harmPercent
            # print("Threat Value reduced by %.1f" % (thr_elim_val))
            if move[0] in ["AOE", "attack", "stand", "turnover"]:  # Search Termination condition. Evaluate
                whole_movseqs.push((next_actseq, nextGame, nextcumrew, nextrisk, thr_elim_val), -nextcumrew + nextrisk * alpha - thr_elim_val * gamma)
                continue
            movseq_col.push((next_actseq, nextcumrew, nextrisk, nextGame))
    # print(whole_movseqs)
    best_seq, best_state, best_rew, bestrisk, best_threat_elim = whole_movseqs.pop()  # Pop from the best of all the leaves
    if show: print("DFS finished %.2f sec, best rew %d, least risk %d, threat elim %d" % (time() - T0, best_rew, bestrisk, best_threat_elim))
    return best_seq, best_state, best_rew


def greedyRiskThreatMinMaxPolicy(game, show=True, perm=False, gamma=0.9, beta=0.4, alpha=0.4):
    """Search the action space of selection, move, attack
    Search the action space that maximize
            next step reward + gamma * threat_elim + beta * threat_posing - alpha * risk(pos)
    """
    T0 = time()
    # Chart the enemy's coverages
    allEnemyPos, allEnemyUnit = game.getAllEnemyUnit()
    threat_dict = {}
    enemyCoverSets = {}
    harmValues = {}  # The attack value discounted by its HP.
    for pos, unit in zip(allEnemyPos, allEnemyUnit):
        coverSet = game.getUnitAttackCoverage(unit,)
        enemyCoverSets[pos] = coverSet
        harmValues[pos] = unit.Attack * unit.HP / 100.0
        threat_bef, _ = threat_pos(game, pos)
        threat_dict[pos] = threat_bef

    def riskFun(pos, mask=[]):
        risk = 0.0
        for tarPos, coverSet in enemyCoverSets.items():
            if tarPos in mask: continue # the unit you just attacked...
            if pos in coverSet:
                # risk += harmValues[tarPos]
                risk = max(risk, harmValues[tarPos])
        return risk

    movseq_col = Stack()
    movseq_col.push(([], 0, 0, game))
    whole_movseqs = PriorityQueue()  # [] #
    while not movseq_col.isEmpty():
        actseq, cumrew, cumrisk, curGame = movseq_col.pop()
        # if curGame.UIstate == SELECT_MOVTARGET:
        moves, nextUIstate = curGame.getPossibleMoves()
        if perm: shuffle(moves)  # moves = [moves[i] for i in permutation(len(moves))]
        for move in moves:  #
            nextrisk = cumrisk
            next_actseq = copy(actseq)
            next_actseq.append(move)
            nextGame, nextrewards = curGame.action_execute(*move, clone=True, show=False, reward=True, checklegal=False)
            # Evaluate the nextState x this move
            nextcumrew = cumrew + nextrewards[curGame.curIdx]  # use the reward for this player
            if move[0] in ["move"]:  # can mask out more the one you attack pose less threat to you
                maxHarm = max(0.0, riskFun(move[1][0], mask=[]) - nextGame.curUnit.Defence)
                nextrisk += maxHarm / 100.0 * unitPrice(nextGame.curUnit) \
                             + (maxHarm >= nextGame.curUnit.HP) * unitPrice(nextGame.curUnit)  # Additional risk for death.
                # TODO: Here the unitPrice could be extended to be the strategic value instead of purely price. (Considering its location etc.) can mask out more...
            thr_elim_val = 0
            if move[0] is "attack":
                targ_pos = move[1][0]
                threat_bef = threat_dict[targ_pos]
                harmPercent = computeHPloss(curGame, nextGame, targ_pos) / 100.0  # should be positive now
                thr_elim_val += threat_bef * harmPercent  # This is less accurate
            if move[0] is "AOE":
                for targ_pos in move[1][1]:  # targetPosList for AOE attack
                    threat_bef = threat_dict[targ_pos]
                    harmPercent = computeHPloss(curGame, nextGame, targ_pos) / 100.0  # should be positive now
                    thr_elim_val += threat_bef * harmPercent
            # print("Threat Value reduced by %.1f" % (thr_elim_val))
            threat_posing = 0.0 # This simulation is too slow, need a better way to estimate it.
            if move[0] in ["AOE", "attack", "stand"]:
                # threat_posing, threat_mov = threat_unit(curGame, curGame.curUnit)
                threat_posing, threat_mov = threat_unit(curGame, curGame.curUnit, oppoPolicy=greedyPolicy_approx)
            if move[0] in ["AOE", "attack", "stand", "turnover"]:
                whole_movseqs.push((next_actseq, nextGame, nextcumrew, nextrisk, thr_elim_val, threat_posing),
                                   -nextcumrew + nextrisk * alpha - threat_posing * beta - thr_elim_val * gamma)
                continue
            movseq_col.push((next_actseq, nextcumrew, nextrisk, nextGame))
    # print(whole_movseqs)
    best_seq, best_state, best_rew, bestrisk, best_threat_elim, best_thr_posing = whole_movseqs.pop()
    if show: print("DFS finished %.2f sec, best rew %d, least risk %d, threat elim %d, threat posing %d" %
                   (time() - T0, best_rew, bestrisk, best_threat_elim, best_thr_posing))
    return best_seq, best_state, best_rew


def greedyRiskThreatMinMaxExactPolicy(game, show=True, perm=False, gamma=0.9, beta=0.4, alpha=0.4, HQWeight=1, enemyWeight=2):
    """Search the action space of selection, move, attack (Current best strategy)
    Search the action space that maximize
            next step reward + gamma * threat_elim + beta * threat_posing - alpha * risk(pos)
    """
    T0 = time()
    # Chart the enemy's coverages
    allEnemyPos, allEnemyUnit = game.getAllEnemyUnit()
    threat_dict = {}
    enemyCoverSets = {}
    harmValues = {}  # The attack value discounted by its HP.
    for pos, unit in zip(allEnemyPos, allEnemyUnit):
        coverSet = game.getUnitAttackCoverage(unit,)
        enemyCoverSets[pos] = coverSet
        harmValues[pos] = unit.Attack * unit.HP / 100.0
        threat_bef, _ = threat_pos(game, pos)
        threat_dict[pos] = threat_bef
    threat_bsl, _ = threat_general(game, game.curPlayer, oppoPolicy=_threat_greedyOccupPolicy)
    def riskFun(pos, mask=[], defence=0):
        """Need more development"""
        risk = 0.0
        for tarPos, coverSet in enemyCoverSets.items():
            if tarPos in mask: continue # the unit you just attacked...
            if pos in coverSet:
                # risk = max(1, harmValues[tarPos] - defence)
                risk = max(risk, max(1, harmValues[tarPos] - defence)) # This may be too pessimistic...
                # risk = max(risk, harmValues[tarPos])
        return risk

    movseq_col = Stack()
    movseq_col.push(([], 0, 0, game))
    whole_movseqs = PriorityQueue()  # [] #
    while not movseq_col.isEmpty():
        actseq, cumrew, cumrisk, curGame = movseq_col.pop()
        # if curGame.UIstate == SELECT_MOVTARGET:
        moves, nextUIstate = curGame.getPossibleMoves()
        if perm: shuffle(moves)  # moves = [moves[i] for i in permutation(len(moves))]
        for move in moves:  #
            nextrisk = cumrisk
            next_actseq = copy(actseq)
            next_actseq.append(move)
            nextGame, nextrewards = curGame.action_execute(*move, clone=True, show=False, reward=True, checklegal=False)
            # Intermediate Evaluate the nextState x this move.
            # In terms of, accumlated reward, risk, threat posing, threat eliminating
            nextcumrew = cumrew + nextrewards[curGame.curIdx]  # use the reward for this player
            if move[0] in ["move"]:  # can mask out more the one you attack pose less threat to you
                # maxHarm = max(0.0, riskFun(move[1][0], mask=[]) - nextGame.curUnit.Defence)
                sumHarm = max(0.0, riskFun(move[1][0], mask=[], defence=nextGame.curUnit.Defence))
                nextrisk += (max(sumHarm, nextGame.curUnit.HP) / 100.0 \
                              + (sumHarm >= nextGame.curUnit.HP)) * unitPrice(nextGame.curUnit)  # Additional risk for death.
                # TODO: Here the unitPrice could be extended to be the strategic value instead of purely price. (Considering its location etc.) can mask out more...
            thr_elim_val = 0.0
            if move[0] is ["AOE", "attack", "stand"]:  # this is threat elimination in global sense. much more accurate
                thr_reduc_val, thr_reduc_mov = threat_general(curGame, game.curPlayer, oppoPolicy=_threat_greedyOccupPolicy)
                thr_elim_val = threat_bsl - thr_reduc_val
            # print("Threat Value reduced by %.1f" % (thr_elim_val))
            threat_posing = 0.0  #
            HQattract = 0.0
            enemyattract = 0.0
            if move[0] in ["AOE", "attack", "stand"]:  # nextGame.curUnit is None
                threat_posing, threat_mov = threat_unit(curGame, curGame.curUnit, oppoPolicy=_threat_greedyOccupPolicy)
                HQattract = 1.0 / (nextGame.getClosestEnemyHQDist(curGame.curUnit.pos)[0] + 0.01)
                enemyattract = 1.0 / nextGame.getClosestEnemyDist(curGame.curUnit.pos)[0]

            if move[0] in ["AOE", "attack", "stand", "turnover"]:  # Search Tree terminates
                whole_movseqs.push((next_actseq, nextGame, nextcumrew, nextrisk, thr_elim_val, threat_posing, HQattract, enemyattract),
                                   -nextcumrew + nextrisk * alpha - threat_posing * beta - thr_elim_val * gamma
                                   - HQattract * HQWeight - enemyattract * enemyWeight)
                continue
            else:  # Search Tree grows. nextcumrew and nextrisk are kept for updates.
                movseq_col.push((next_actseq, nextcumrew, nextrisk, nextGame))
    best_seq, best_state, best_rew, bestrisk, best_threat_elim, best_thr_posing, bestHQattr, bestenemyattr = whole_movseqs.pop()
    if show: print("DFS finished %.2f sec (%d act seqs), best rew %d, least risk %d, threat elim %d, threat posing %d HQattr %.1f enemyAttr %.1f" %
                   (time() - T0, len(whole_movseqs.heap), best_rew, bestrisk, best_threat_elim, best_thr_posing, bestHQattr, bestenemyattr))
    return best_seq, best_state, best_rew


#%%
# game = GameStateCtrl()
# game.endTurn()
# best_seq, best_state, best_rew = ThreatElimPolicy(game)
# _, cumrew = game.action_seq_execute(best_seq, show=True, reward=True)
# best_seq, best_state, best_rew = ThreatElimPolicy(game)
# _, cumrew = game.action_seq_execute(best_seq, show=True, reward=True)
# # hypo_game_post = deepcopy(game)
# hypo_game_post.action_execute("attack", (5,5))
# hypo_game_post.endTurn()
# hypo_game_post.selectUnit((5, 5))
# bestenemy_seq_post, bestenemy_state_post, bestenemy_rew_post = greedyPolicy(hypo_game_post)
#%%
# game = GameStateCtrl()
# game.GUI_loop()
#%%
# G = GameStateCtrl(withUnit=False)
# G.unitList.append(Unit(player=1, pos=(3, 2), cfg=SoldierCfg))
# G.unitList.append(Unit(player=1, pos=(3, 3), cfg=SoldierCfg))
# G.unitList.append(Unit(player=1, pos=(3, 4), cfg=SoldierCfg))
# G.unitList.append(Unit(player=1, pos=(3, 5), cfg=SoldierCfg))
# G.unitList.append(Unit(player=1, pos=(3, 6), cfg=SoldierCfg))
# G.unitList.append(Unit(player=1, pos=(3, 7), cfg=SoldierCfg))
# G.unitList.append(Unit(player=1, pos=(2, 3), cfg=ArcherCfg))
# G.unitList.append(Unit(player=1, pos=(2, 4), cfg=ArcherCfg))
# G.unitList.append(Unit(player=1, pos=(2, 5), cfg=ArcherCfg))
# G.unitList.append(Unit(player=1, pos=(2, 6), cfg=ArcherCfg))
# G.unitList.append(Unit(player=1, pos=(4, 7), cfg=KnightCfg))
# G.unitList.append(Unit(player=1, pos=(4, 6), cfg=KnightCfg))
# G.unitList.append(Unit(player=1, pos=(4, 5), cfg=KnightCfg))
# G.unitList.append(Unit(player=1, pos=(4, 3), cfg=KnightCfg))
# G.unitList.append(Unit(player=1, pos=(4, 2), cfg=KnightCfg))
# G.unitList.append(Unit(player=1, pos=(4, 1), cfg=KnightCfg))
# G.unitList.append(Unit(player=1, pos=(4, 0), cfg=KnightCfg))
# G.unitList.append(Unit(player=1, pos=(4, 4), cfg=StoneManCfg))
# G.unitList.append(Unit(player=1, pos=(2, 2), cfg=StormSummonerCfg))
# G.unitList.append(Unit(player=1, pos=(1, 3), cfg=CatapultCfg))
# G.unitList.append(Unit(player=1, pos=(1, 2), cfg=CatapultCfg))
# G.unitList.append(Unit(player=2, pos=(11, 2), cfg=SoldierCfg))
# G.unitList.append(Unit(player=2, pos=(11, 3), cfg=SoldierCfg))
# G.unitList.append(Unit(player=2, pos=(11, 4), cfg=SoldierCfg))
# G.unitList.append(Unit(player=2, pos=(12, 3), cfg=ArcherCfg))
# G.unitList.append(Unit(player=2, pos=(12, 2), cfg=ArcherCfg))
# G.unitList.append(Unit(player=2, pos=(10, 4), cfg=KnightCfg))
# # G.unitList.append(Unit(player=2, pos=(10, 3), cfg=KnightCfg))
# G.unitList.append(Unit(player=2, pos=(10, 0), cfg=StoneManCfg))
# G.unitList.append(Unit(player=2, pos=(10, 5), cfg=StoneManCfg))
# G.unitList.append(Unit(player=2, pos=(10, 2), cfg=StoneManCfg))
# G.unitList.append(Unit(player=2, pos=(10, 1), cfg=StoneManCfg))
# # G.unitList.append(Unit(player=2, pos=(10, 0), cfg=StoneManCfg))
# G.unitList.append(Unit(player=2, pos=(12, 4), cfg=StormSummonerCfg))
# G.unitList.append(Unit(player=2, pos=(12, 1), cfg=StormSummonerCfg))
# G.unitList.append(Unit(player=2, pos=(11, 1), cfg=StormSummonerCfg))
# G.unitList.append(Unit(player=2, pos=(13, 3), cfg=CatapultCfg))
# G.unitList.append(Unit(player=2, pos=(13, 4), cfg=CatapultCfg))
# G.unitList.append(Unit(player=2, pos=(13, 2), cfg=CatapultCfg))
# G.unitList.append(Unit(player=2, pos=(13, 1), cfg=CatapultCfg))
# G.GUI_loop()
#%% Setup the chess board
def gameSetup():
    G = GameStateCtrl(withUnit=False)
    G.unitList.append(Unit(player=1, pos=(3, 2), cfg=SoldierCfg))
    G.unitList.append(Unit(player=1, pos=(3, 3), cfg=SoldierCfg))
    G.unitList.append(Unit(player=1, pos=(3, 4), cfg=SoldierCfg))
    G.unitList.append(Unit(player=1, pos=(3, 5), cfg=SoldierCfg))
    G.unitList.append(Unit(player=1, pos=(3, 6), cfg=SoldierCfg))
    G.unitList.append(Unit(player=1, pos=(3, 7), cfg=SoldierCfg))
    G.unitList.append(Unit(player=1, pos=(2, 3), cfg=ArcherCfg))
    G.unitList.append(Unit(player=1, pos=(2, 4), cfg=ArcherCfg))
    G.unitList.append(Unit(player=1, pos=(2, 5), cfg=ArcherCfg))
    G.unitList.append(Unit(player=1, pos=(2, 6), cfg=ArcherCfg))
    G.unitList.append(Unit(player=1, pos=(2, 7), cfg=ArcherCfg))
    G.unitList.append(Unit(player=1, pos=(4, 8), cfg=KnightCfg))
    G.unitList.append(Unit(player=1, pos=(4, 7), cfg=KnightCfg))
    G.unitList.append(Unit(player=1, pos=(4, 6), cfg=KnightCfg))
    G.unitList.append(Unit(player=1, pos=(4, 5), cfg=KnightCfg))
    G.unitList.append(Unit(player=1, pos=(4, 3), cfg=KnightCfg))
    # G.unitList.append(Unit(player=1, pos=(4, 2), cfg=KnightCfg))
    # G.unitList.append(Unit(player=1, pos=(4, 1), cfg=KnightCfg))
    # G.unitList.append(Unit(player=1, pos=(4, 0), cfg=KnightCfg))
    G.unitList.append(Unit(player=1, pos=(4, 4), cfg=StoneManCfg))
    G.unitList.append(Unit(player=1, pos=(2, 2), cfg=StormSummonerCfg))
    G.unitList.append(Unit(player=1, pos=(1, 3), cfg=CatapultCfg))
    G.unitList.append(Unit(player=1, pos=(1, 2), cfg=CatapultCfg))
    G.unitList.append(Unit(player=2, pos=(11, 2), cfg=SoldierCfg))
    G.unitList.append(Unit(player=2, pos=(11, 3), cfg=SoldierCfg))
    # G.unitList.append(Unit(player=2, pos=(11, 4), cfg=SoldierCfg))
    G.unitList.append(Unit(player=2, pos=(12, 3), cfg=ArcherCfg))
    G.unitList.append(Unit(player=2, pos=(12, 2), cfg=ArcherCfg))
    G.unitList.append(Unit(player=2, pos=(10, 4), cfg=KnightCfg))
    # G.unitList.append(Unit(player=2, pos=(10, 3), cfg=KnightCfg))
    G.unitList.append(Unit(player=2, pos=(10, 6), cfg=StoneManCfg))
    G.unitList.append(Unit(player=2, pos=(10, 5), cfg=StoneManCfg))
    G.unitList.append(Unit(player=2, pos=(10, 3), cfg=StoneManCfg))
    G.unitList.append(Unit(player=2, pos=(10, 2), cfg=StoneManCfg))
    G.unitList.append(Unit(player=2, pos=(10, 1), cfg=StoneManCfg))
    G.unitList.append(Unit(player=2, pos=(10, 0), cfg=StoneManCfg))
    # G.unitList.append(Unit(player=2, pos=(12, 4), cfg=StormSummonerCfg))
    G.unitList.append(Unit(player=2, pos=(12, 1), cfg=StormSummonerCfg))
    G.unitList.append(Unit(player=2, pos=(11, 1), cfg=StormSummonerCfg))
    G.unitList.append(Unit(player=2, pos=(13, 3), cfg=CatapultCfg))
    G.unitList.append(Unit(player=2, pos=(13, 4), cfg=CatapultCfg))
    G.unitList.append(Unit(player=2, pos=(13, 2), cfg=CatapultCfg))
    G.unitList.append(Unit(player=2, pos=(13, 1), cfg=CatapultCfg))
    return G
# G.unitList.append(Unit(player=2, pos=(13, 1), cfg=CatapultCfg))
# G.GUI_loop()
#%%
def gamePlay(game, playerAI, SingleUnitTurn=False, automove=True, display=True):
    """
    game: any gameState obj
    playerAI: a dictionary mapping the playerID s in game to a string `human` or a tuple
        (AI_name_str, AI_policy_function, policy_parameter)

    automove: if False, we need to press a key to end turn for computer AIs.
    SingleUnitTurn: In this mode, each player is allowed to move only one unit in a turn. If false then can move all
    display: if False, only test output is kept.
    """
    total_rewards = [0.0 for player in game.playerList]
    act_history = []
    Exitflag = False
    while not Exitflag:
        if playerAI[game.curPlayer] == "human":
            game.GUI_loop(oneturn=True)
        else:
            policystr, policyFun, params = playerAI[game.curPlayer]
            Moveflag = automove # if True then without key tab, it's keeping moving.
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    Exitflag = True
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_TAB:
                        Moveflag = True
            if Moveflag:
                if SingleUnitTurn: game.endTurn()  # Each side move one unit each turn!
                best_seq, best_state, best_rew = policyFun(game, **params)
                _, cumrew = game.action_seq_execute(best_seq, show=True, reward=True,)  # TODO: save some events for learning purposes no?
                total_rewards = [total_rewards[i] + cumrew[i] for i, _ in enumerate(game.playerList)]
                act_history.extend(best_seq)
                # event_history.extent(events)
                if display:
                    game.drawBackground()
                    game.drawBuildingList()
                    game.drawUnitList()
                    pg.display.update()
        enemyPos, enemyUnit = game.getAllEnemyUnit()
        if len(enemyUnit) == 0:  
            print("Player %d Win the game! AI %s"%(game.curPlayer, playerAI[game.curPlayer]))
            Exitflag=True
    winner = game.curPlayer
    statDict = {"Turns":game.curTurn, "TotalRewards":total_rewards, "FinalFunds":game.playerFund}
    return winner, statDict, act_history
#%% This demonstrates Two Threat Elimination agents playing with each other.
# game = gameSetup()
# # This is the basic loop for playing an action sequence step by step
# playerAI = {1: ("DefAI", greedyRiskThreatMinMaxExactPolicy, dict(gamma=0.9, beta=0.8, alpha=0.3, show=True, perm=False)),#"human",
#             2: ("AggAI", greedyRiskThreatMinMaxExactPolicy, dict(gamma=1.2, beta=1.1, alpha=0.7, show=True, perm=False))}
# # playerAI = {1:"human", 2:"human"}
# # ("AI", greedyPolicy, dict())
# # ("RiskAI", greedyRiskMinPolicy, dict(alpha=0.1))
# # ("AI", greedyRiskThreatMinPolicy, dict(perm=False, gamma=0.7, alpha=0.15))
# # ("AI", greedyRiskThreatMinMaxPolicy, dict(perm=False, gamma=0.9, beta=0.5, alpha=0.6) #gamma=0.7, beta=0.4, alpha=0.15))
# # ("AI", ThreatElimPolicy, dict())
# # ("AI", ThreatElimPolicy_recurs, dict(recursL=2))
# winner, gameDict, act_record = gamePlay(game, playerAI)
# Risk fun, Value fun
#%%
match_results = []
for triali in range(10):
    # This is the basic loop for playing an action sequence step by step
    playerAI = {1: ("DefAI", greedyRiskThreatMinMaxExactPolicy, dict(gamma=1.5, beta=2.0, alpha=0.3, show=True, perm=False)),#"human",
                2: ("AggAI", greedyRiskThreatMinMaxExactPolicy, dict(gamma=1.2, beta=1.1, alpha=0.7, show=True, perm=False))}
    game = gameSetup()
    winner12, gameDict12, act_record12 = gamePlay(game, playerAI)
    match_results.append((playerAI, winner12, gameDict12, act_record12))

    playerAI = {2: ("DefAI", greedyRiskThreatMinMaxExactPolicy, dict(gamma=1.5, beta=2.0, alpha=0.3, show=True, perm=False)),#"human",
                1: ("AggAI", greedyRiskThreatMinMaxExactPolicy, dict(gamma=1.2, beta=1.1, alpha=0.7, show=True, perm=False))}
    game = gameSetup()
    winner21, gameDict21, act_record21 = gamePlay(game, playerAI)
    match_results.append((playerAI, winner21, gameDict21, act_record21))

#%%
