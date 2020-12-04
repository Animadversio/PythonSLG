__author__ = 'Animadversio_Binxu'
import pygame as pg
from source.util import Queue, Stack, PriorityQueue
from copy import copy, deepcopy
# Setup window and screen
pg.display.set_caption("SLG board")
SCREEN = pg.display.set_mode((800,500)) # get screen
screen = pg.display.get_surface()
# Setup Font
pg.font.init()
font = pg.font.SysFont("microsoftsansserif", 16, bold=True)
# Utility to detect DoubleClick
dbclock = pg.time.Clock()
DOUBLECLICKTIME = 250
# Color, Layout Constants
LIGHTYELLOW = (247, 238, 214)
LIGHTBLUE = (214, 220, 247)
MAP_WIDTH = 800
MAP_HEIGHT = 500
TileW = 50
Margin = 2
CsrWidth = 5
UMargin = 20
playerColor = {1: (20, 20, 20), 2: (120, 20, 20)} # Color for each player number
#%% Units
class Unit:
    def __init__(self, player, pos, cfg=None):
        self.player = player
        self.pos = pos
        self.alive = True
        self.moved = True
        self.Buff = []  # Buff is a state
        # cfg
        if cfg is not None:
            for key, val in cfg.items():
                self.__setattr__(key, val)
        else:
            self.Type = ""
            self.HP = 100
            self.Attack = 40
            self.Defence = 10
            self.Movepnt = 4
            self.AttackRng = (1, 2)
            self.Ability = []
            self.ExtraAct = []
            # self.exp
            # self.level

    def __deepcopy__(self, memodict={}):
        U = Unit()
        for key, vals in self.__dict__.items():
            U.__dict__[key] = deepcopy(vals)
        return U

# List of Abilities
HEAVYMACHINE = 6
STORM = 7
HEAL = 8
SUMMON = 9
SoldierCfg = {"Type": "Soldier", "HP": 100, "Attack": 55, "Defence": 10, "Movepnt": 4, "AttackRng": (1, 1), "Ability": [], "ExtraAct": [],}
ArcherCfg = {"Type": "Archer", "HP": 100, "Attack": 45, "Defence":  5, "Movepnt": 4, "AttackRng": (2, 2), "Ability": [], "ExtraAct": [],}
KnightCfg = {"Type": "Knight", "HP": 100, "Attack": 60, "Defence":  15, "Movepnt": 6, "AttackRng": (1, 1), "Ability": [], "ExtraAct": [],}
CatapultCfg = {"Type": "Catapult", "HP": 100, "Attack": 70, "Defence":  5, "Movepnt": 3, "AttackRng": (3, 7), "Ability": [HEAVYMACHINE, ], "ExtraAct": [], }
StoneManCfg = {"Type": "StoneMan", "HP": 100, "Attack": 60, "Defence":  35, "Movepnt": 4, "AttackRng": (1, 1), "Ability": [], "ExtraAct": [],}
StormSummonerCfg = {"Type": "StormSummoner", "HP": 100, "Attack": 30, "Defence":  5, "Movepnt": 4, "AttackRng": (2, 6), "Ability": [], "ExtraAct": [STORM], }

CfgDict = {"Soldier": SoldierCfg, "Archer": ArcherCfg, "Knight": KnightCfg, "Catapult": CatapultCfg,
             "StoneMan": StoneManCfg, "StormSummoner": StormSummonerCfg, }
valueDict = {"Soldier": 100, "Archer": 150, "Knight": 400, "Catapult": 700,
             "StoneMan": 600, "StormSummoner": 600}
priceDict = {"Soldier": 100, "Archer": 150, "Knight": 400, "Catapult": 700,
             "StoneMan": 600, "StormSummoner": 600}
unitPrice = lambda unit: valueDict[unit.Type]
#%%
showpos = [(3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7)]
buyUnitPosMap = {pos:unitType for pos, unitType in zip(showpos, priceDict.keys())}
#%% Buildings
class Building:
    def __init__(self, player, pos, cfg=None):
        self.player = player
        self.pos = pos
        self.broken = False
        # self.Buff = []  # Buff is a state
        if cfg is not None:
            for key, val in cfg.items():
                self.__setattr__(key, val)
        else:
            self.Type = ""
            self.HP = 100
            self.TileAtk = 0
            self.TileDef = 0
            self.TileHeal = 0
            self.Earn = 0
            self.Props = []

    def __deepcopy__(self, memodict={}):
        B = Building(self.player, self.pos)
        for key, vals in self.__dict__.items():
            B.__dict__[key] = deepcopy(vals)
        return B

PURCHASE = 1
HEALING = 2
OCCUPIABLE = 3
CastleCfg = {"Type": "Castle", "TileAtk": 0, "TileDef": 15, "HP": 100, "Props": [PURCHASE, OCCUPIABLE], "Earn": 100}
VillageCfg = {"Type": "Village", "TileAtk": 0, "TileDef": 25, "HP": 100, "Props": [HEALING, OCCUPIABLE], "Earn": 50}
Building(None, (1, 1), CastleCfg)
#%%
def playerIterator(playerList):
    turn = 0
    while True:
        turn += 1
        for player in playerList: # and player is alive
            yield player, turn

from collections import defaultdict
# UIState Definition
END_TURN = 0
SELECT_UNIT = 1
SELECT_ACTION = 2
SELECT_MOVTARGET = 3
SELECT_ATTTARGET = 4
SELECT_BUY = 5
SELECT_AOETARGET = 6
SELECT_HEALTARGET = 7
SELECT_REMOVTARGET = 8
class GameStateCtrl:
    def __init__(G, withUnit=True, withBuilding=True):
        G.playerList = [1, 2]
        G.curIdx = len(G.playerList) - 1
        G.curPlayer = G.playerList[-1] # UIState starts from END_TURN so it will transition into first player
        G.playerFund = [0, 100]
        G.playerIncome = [100, 100]
        # G.playerIter = playerIterator(G.playerList)
        G.curTurn = 0
        G.screen = screen
        G.mapH = screen.get_height() // TileW # FIXME, screen and mapsize can decouple
        G.mapW = screen.get_width() // TileW
        G.UIstate = END_TURN
        G.unitList = []
        G.buildingList = []
        G.curUnit = None
        G.curBldg = None
        if withBuilding:
            G.buildingList.append(Building(player=1, pos=(1, 1), cfg=CastleCfg))
            G.buildingList.append(Building(player=2, pos=(13, 7), cfg=CastleCfg))
            G.buildingList.append(Building(player=1, pos=(1, 2), cfg=VillageCfg))
            G.buildingList.append(Building(player=2, pos=(13, 8), cfg=VillageCfg))

        if withUnit: # a default chess board configuration
            G.unitList.append(Unit(player=1, pos=(3, 2), cfg=SoldierCfg))
            G.unitList.append(Unit(player=1, pos=(3, 3), cfg=SoldierCfg))
            G.unitList.append(Unit(player=1, pos=(3, 4), cfg=SoldierCfg))
            G.unitList.append(Unit(player=1, pos=(3, 5), cfg=SoldierCfg))
            G.unitList.append(Unit(player=1, pos=(2, 3), cfg=ArcherCfg))
            G.unitList.append(Unit(player=1, pos=(2, 4), cfg=ArcherCfg))
            G.unitList.append(Unit(player=1, pos=(4, 3), cfg=KnightCfg))
            G.unitList.append(Unit(player=1, pos=(4, 4), cfg=StoneManCfg))
            G.unitList.append(Unit(player=1, pos=(2, 2), cfg=StormSummonerCfg))
            G.unitList.append(Unit(player=1, pos=(1, 3), cfg=CatapultCfg))
            G.unitList.append(Unit(player=1, pos=(1, 2), cfg=CatapultCfg))
            G.unitList.append(Unit(player=2, pos=(11, 2), cfg=SoldierCfg))
            G.unitList.append(Unit(player=2, pos=(11, 3), cfg=SoldierCfg))
            G.unitList.append(Unit(player=2, pos=(11, 4), cfg=SoldierCfg))
            G.unitList.append(Unit(player=2, pos=(12, 3), cfg=ArcherCfg))
            G.unitList.append(Unit(player=2, pos=(12, 2), cfg=ArcherCfg))
            G.unitList.append(Unit(player=2, pos=(10, 3), cfg=KnightCfg))
            G.unitList.append(Unit(player=2, pos=(10, 2), cfg=StoneManCfg))
            G.unitList.append(Unit(player=2, pos=(12, 4), cfg=StormSummonerCfg))
            G.unitList.append(Unit(player=2, pos=(13, 3), cfg=CatapultCfg))
            G.unitList.append(Unit(player=2, pos=(13, 4), cfg=CatapultCfg))

    def __deepcopy__(self, memodict={}):
        """ Key function to accelerate the tree search process """
        # Do a shallow copy for most things as they are basic datatype.
        # Screen will do a reference copy.
        newG = copy(self)
        newG.unitList = [copy(unit) for unit in self.unitList]
        newG.buildingList = [copy(bldg) for bldg in self.buildingList]
        newG.playerFund = copy(self.playerFund)
        newG.playerIncome = copy(self.playerIncome)
        # newG.__dict__['screen'] = self.__dict__['screen']
        # for key, vals in self.__dict__.items():
        #     if key is 'screen': continue
        #     newG.__dict__[key] = deepcopy(vals)
        if self.curUnit is not None:
            # curUnit is referencing the unit in current unitList, not the one in the previous object.
            # re-establish the link between the list and the reference to it.
            unitId = self.unitList.index(self.curUnit)
            newG.curUnit = newG.unitList[unitId]
        return newG

    def __lt__(self, other):
        """A very crude comparison function for GameState"""
        return len(self.unitList) < len(other.unitList)

    def playerIterator(G):
        """This is really handy function but cause much pain when copying!"""
        turn = 0
        while True:
            turn += 1
            for player in G.playerList:  # and player is alive
                yield player, turn

    def GUI_loop(G, GUI=True, csr_pos=(5, 6), oneturn=False):
        """This is less hierarchical, more linear programming style game loop"""
        ci, cj = csr_pos # csr is a construct in GUI not a gameState, not stored
        Exitflag = False

        button1 = pg.Rect(105, 100, 40, 25)
        button2 = pg.Rect(105, 125, 40, 25)
        while not Exitflag: # Main Event Loop
            # Input Processor
            K_confirm = False
            K_cancel = False
            K_Turnover = False
            B_A = False
            B_B = False
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    Exitflag = True
                if event.type == pg.MOUSEBUTTONDOWN:
                    mouseX, mouseY = pg.mouse.get_pos()
                    ci, cj = mouseX // TileW, mouseY // TileW
                    if dbclock.tick() < DOUBLECLICKTIME:
                        K_confirm = True
                    if button1.collidepoint((mouseX, mouseY)): B_A = True
                    if button2.collidepoint((mouseX, mouseY)): B_B = True
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_UP: cj -= 1
                    if event.key == pg.K_DOWN: cj += 1
                    if event.key == pg.K_LEFT: ci -= 1
                    if event.key == pg.K_RIGHT: ci += 1
                    if event.key == pg.K_SPACE: K_confirm = True
                    if event.key == pg.K_ESCAPE: K_cancel = True
                    if event.key == pg.K_TAB: K_Turnover = True
                    if event.key == pg.K_1: B_A = True
                    if event.key == pg.K_2: B_B = True
            G.drawBackground()
            # drawTerrain(screen, gameState)
            if K_Turnover:
                if oneturn:
                    Exitflag = True  # If human only plays one turn then this will end the GUI event loop.
                G.UIstate = END_TURN

            if G.UIstate is END_TURN:
                # nextPlayer, nextTurn = next(G.playerIter)  # playerList[playerList.index(curPlayer)+1]

                G.endTurn()
                # curIdx = G.playerList.index(G.curPlayer)
                # if curIdx == len(G.playerList) - 1:
                #     nextTurn, nextPlayer = G.curTurn + 1, G.playerList[0]
                # else:
                #     nextTurn, nextPlayer = G.curTurn, G.playerList[curIdx + 1]
                # # Do sth at turn over
                # for unit in G.unitList:
                #     if unit.player is nextPlayer: unit.moved = False
                #     if unit.player is G.curPlayer: unit.moved = True
                # G.curPlayer, G.curTurn = nextPlayer, nextTurn
                # G.UIstate = SELECT_UNIT
                # drawTurnover(screen)

            if G.UIstate == SELECT_UNIT:
                posDict = {unit.pos: unit for unit in G.unitList}
                selectable_pos, selectable_unit = G.getSelectableUnit()  # unitList, curPlayer  # add condition for selectable
                selectable_tilepos, selectable_bldgs = G.getSelectableTile()  # unitList, curPlayer  # add condition for selectable
                # unit_pos = [unit.pos for unit in unitList
                #             if unit.player == curPlayer and not unit.moved]  # add condition for selectable
                if K_confirm and (ci, cj) in selectable_pos:
                    # unitId = unit_pos.index((ci, cj))
                    G.curUnit = posDict[(ci, cj)] # unitList[unitId]
                    G.UIstate = SELECT_MOVTARGET
                    print("Unit %s selected (%d, %d)" % (G.curUnit.Type, ci, cj))
                elif K_confirm and (ci, cj) in selectable_tilepos:
                    G.UIstate = SELECT_BUY
                    G.curBldg = selectable_bldgs[selectable_tilepos.index((ci, cj))]
                    print("Location (%d, %d) selected" % (ci, cj))

            elif G.UIstate == SELECT_MOVTARGET:
                unit_pos = [unit.pos for unit in G.unitList if unit is not G.curUnit]
                obst_pos = G.getObstacleInRange(G.curUnit, None, )
                movRange = G.getMovRange(G.curUnit.pos, G.curUnit.Movepnt, obst_pos)
                G.drawLocation(movRange, (160, 180, 180))  # draw a list of location in one color
                if K_confirm and (ci, cj) in movRange and (ci, cj) not in unit_pos:
                    print("Unit %s move (%d, %d) -> (%d, %d)"%(G.curUnit.Type, *G.curUnit.pos, ci, cj))
                    # move(unit, mov2i, mov2j)
                    ui_orig, uj_orig = G.curUnit.pos  # record this just in case user cancels
                    G.move((ci, cj), show=True, checklegal=True)
                    # G.curUnit.pos = ci, cj  # ui, uj
                    # G.UIstate = SELECT_ATTTARGET
                    # UIstate = SELECT_ACTION
                if K_cancel:
                    G.UIstate = SELECT_UNIT

            elif G.UIstate == SELECT_ACTION:
                button1 = pg.Rect(55, 50, 90, 30)
                button2 = pg.Rect(55, 85, 90, 30)
                pg.draw.rect(screen, [220, 200, 200], button1)
                pg.draw.rect(screen, [220, 200, 200], button2)
                screen.blit(font.render('STORM', True, [0,0,0]), (55, 60))
                screen.blit(font.render('Attack', True, [0,0,0]), (55, 95))
                if B_A:
                    G.UIstate = SELECT_AOETARGET
                if B_B:
                    G.UIstate = SELECT_ATTTARGET
                if K_cancel:
                    G.curUnit.pos = ui_orig, uj_orig
                    G.UIstate = SELECT_MOVTARGET

            elif G.UIstate == SELECT_AOETARGET:
                attRange = G.getAttackRange(G.curUnit.pos, G.curUnit.AttackRng[0], G.curUnit.AttackRng[1])
                centRange, targetPosList = G.getAOETargetInRange(G.curUnit, attRange, unitList=G.unitList, radius=1)
                targetUnion = list(set().union(*targetPosList))
                G.drawLocation(centRange, (220, 180, 180))  # draw a list of location in one color
                G.drawCircTarget(targetUnion, (240, 130, 130))
                if K_confirm and (ci, cj) in centRange:
                    posList = targetPosList[centRange.index((ci, cj))]
                    print("Unit %s (%d, %d) Attack AOE (%d, %d)" % (G.curUnit.Type, *G.curUnit.pos, ci, cj))
                    print(posList)
                    G.attack_AOE((ci, cj), posList, show=True, reward=True, checklegal=True)

                if K_cancel:
                    G.UIstate = SELECT_ACTION

            elif G.UIstate == SELECT_ATTTARGET:
                attRange = G.getAttackRange(G.curUnit.pos, G.curUnit.AttackRng[0], G.curUnit.AttackRng[1])
                targetPos, targetUnits, _ = G.getTargetInRange(G.curUnit, attRange)
                G.drawLocation(attRange, (220, 180, 180))  # draw a list of location in one color
                G.drawCsrLocation(targetPos, (250, 130, 130))
                if K_confirm:
                    if (ci, cj) in targetPos:  # confirmed attack
                        attacked = targetUnits[targetPos.index((ci, cj))]
                        print("Unit %s @ (%d, %d) attack %s (%d, %d)" % (G.curUnit.Type, *G.curUnit.pos, attacked.Type, ci, cj))
                        # Real computation code for attack
                        harm = max(1, int(G.curUnit.Attack / 100.0 * G.curUnit.HP) - attacked.Defence)
                        attacked.HP -= harm
                        if attacked.HP <= 0:
                            attacked.alive = False
                            G.unitList.pop(G.unitList.index(attacked))
                        attDis = abs(ci - G.curUnit.pos[0]) + abs(cj - G.curUnit.pos[1])
                        counterattack = (attacked.AttackRng[0] <= attDis <= attacked.AttackRng[1]) and attacked.alive # and bla bla bla
                        if counterattack:
                            harm2 = max(1, int(attacked.Attack / 100.0 * attacked.HP) - G.curUnit.Defence)
                            G.curUnit.HP -= harm2
                            # FIXED: Currently Attacker and Attacked could Die together!
                            if G.curUnit.HP <= 0:
                                G.curUnit.alive = False
                                G.unitList.pop(G.unitList.index(G.curUnit))

                    if len(targetPos) == 0:
                        print("No target. Unit @ (%d, %d) stand by" % (*G.curUnit.pos,))
                    G.curUnit.moved = True
                    G.curUnit = None
                    G.UIstate = SELECT_UNIT
                    # UIstate = SELECT_REMOVTARGET
                if K_cancel:
                    G.curUnit.pos = ui_orig, uj_orig
                    G.UIstate = SELECT_MOVTARGET
            elif G.UIstate == SELECT_BUY:
                G.drawBuyScreen()
                if K_confirm:
                    if (ci, cj) in buyUnitPosMap:
                        unitType = buyUnitPosMap[(ci, cj)]
                        # if priceDict[unitType] <= G.playerFund[G.curIdx]:
                        G.buyUnit(G.curBldg.pos, unitType)
                if K_cancel:
                    G.UIstate = SELECT_UNIT

            # drawUnits(screen, [(ui, uj)])  # gameState
            if not G.UIstate is SELECT_BUY:
                G.drawBuildingList()
                G.drawUnitList(G.unitList)
                G.drawCsrLocation([(ci, cj)])  # Csr on top of Unit.
            pg.display.update()

    def endTurn(G, show=True):
        # nextPlayer, nextTurn = next(G.playerIter)  # playerList[playerList.index(curPlayer)+1]
        # curIdx = G.playerList.index(G.curPlayer)
        if G.curIdx == len(G.playerList) - 1:
            nextTurn, nextPlayer, nextIdx = G.curTurn + 1, G.playerList[0], 0
        else:
            nextTurn, nextPlayer, nextIdx = G.curTurn, G.playerList[G.curIdx + 1], G.curIdx + 1
        # Do sth at turn over
        for unit in G.unitList:
            if unit.player is nextPlayer: unit.moved = False
            if unit.player is G.curPlayer: unit.moved = True
        # Re calculate the income for this player at turn change
        G.playerIncome[nextIdx] = 0.0
        for bldg in G.buildingList:
            if bldg.player == nextPlayer:
                G.playerIncome[nextIdx] += bldg.Earn
        # Get the income this turn
        G.playerFund[nextIdx] += G.playerIncome[nextIdx]
        if show: print("Turn Changed, Next player %d, Turn %d. Income %d, Current Fund %d"
            %(nextPlayer, nextTurn, G.playerIncome[nextIdx], G.playerFund[nextIdx]))
        G.curPlayer, G.curIdx, G.curTurn = nextPlayer, nextIdx, nextTurn
        G.UIstate = SELECT_UNIT

    def selectUnit(G, csr, show=True):
        posDict = {unit.pos: unit for unit in G.unitList}
        selectable_pos, selectable_unit = G.getSelectableUnit()  # unitList, curPlayer  # add condition for selectable
        if csr in selectable_pos:
            G.curUnit = posDict[csr]  # unitList[unitId]
            G.UIstate = SELECT_MOVTARGET
            if show: print("Unit %s selected (%d, %d)" % (G.curUnit.Type, *csr, ))
        else:
            raise ValueError

    def buyUnit(G, csr, unittype, show=True, checklegal=True):
        G.curIdx = G.playerList.index(G.curPlayer)
        if G.playerFund[G.curIdx] >= priceDict[unittype]:
            G.playerFund[G.curIdx] -= priceDict[unittype]
        else:
            if show: print("Not enough fund, cannot afford %s"%unittype)
            G.UIstate = SELECT_UNIT
            return
        newUnit = Unit(player=G.curPlayer, pos=csr, cfg=CfgDict[unittype])
        newUnit.moved = False  # specify whether a newly bought unit could move at first gen.
        if show: print("Buy unit %s at (%d, %d)" % (unittype, *csr))
        G.unitList.append(newUnit)
        G.UIstate = SELECT_UNIT

    def move(G, csr, show=True, checklegal=True):
        # ci, cj = csr
        if checklegal:
            unit_pos = [unit.pos for unit in G.unitList if unit is not G.curUnit]
            obst_pos = G.getObstacleInRange(G.curUnit, None, )
            movRange = G.getMovRange(G.curUnit.pos, G.curUnit.Movepnt, obst_pos)
            if show: G.drawLocation(movRange, (160, 180, 180))  # draw a list of location in one color
        if not checklegal or (checklegal and csr in movRange and csr not in unit_pos):
            if show: print("Unit %s move (%d, %d) -> (%d, %d)"%(G.curUnit.Type, *G.curUnit.pos, *csr, ))
            # move(unit, mov2i, mov2j)
            ui_orig, uj_orig = G.curUnit.pos  # record this just in case user cancels
            G.curUnit.pos = csr  # ui, uj
            if len(G.curUnit.ExtraAct) == 0:
                G.UIstate = SELECT_ATTTARGET
            else:
                G.UIstate = SELECT_ACTION
        else:
            raise ValueError

    def attack(G, csr, show=True, reward=False, checklegal=True):
        unitValue = lambda unit: valueDict[unit.Type]  # value function for each value. Should be learnable
        if show:
            attRange = G.getAttackRange(G.curUnit.pos, G.curUnit.AttackRng[0], G.curUnit.AttackRng[1])
            targetPos, targetUnits, targetDist = G.getTargetInRange(G.curUnit, attRange)
            G.drawLocation(attRange, (220, 180, 180))  # draw a list of location in one color
            G.drawCsrLocation(targetPos, (250, 130, 130))
        else:  # if not show, then combine the attackrange into target finding.
            targetPos, targetUnits, targetDist = G.getTargetInRange(G.curUnit, None)
        ci, cj = csr
        if (ci, cj) in targetPos:  # confirmed attack
            attacked = targetUnits[targetPos.index((ci, cj))]
            # Real computation code for attack
            harm = max(1, int(G.curUnit.Attack / 100.0 * G.curUnit.HP) - attacked.Defence)  # - tile.Defence
            if attacked.HP - harm <= 0: # FIX over kill problem
                harm = attacked.HP
                attacked.HP = 0
                attacked.alive = False
                G.unitList.pop(G.unitList.index(attacked))
            else:
                attacked.HP -= harm
            if reward: attackerRew = harm / 100.0 * unitValue(attacked) + (not attacked.alive) * unitValue(attacked) # no over reward for over kill
            attDis = abs(ci - G.curUnit.pos[0]) + abs(cj - G.curUnit.pos[1])
            counterattack = (attacked.AttackRng[0] <= attDis <= attacked.AttackRng[1]) and attacked.alive # and bla bla bla
            if counterattack:
                harm2 = max(1, int(attacked.Attack / 100.0 * attacked.HP) - G.curUnit.Defence)
                # FIXED: Currently Attacker and Attacked could Die together!
                if G.curUnit.HP - harm2 <= 0:
                    harm2 = G.curUnit.HP
                    G.curUnit.HP = 0
                    G.curUnit.alive = False
                    G.unitList.pop(G.unitList.index(G.curUnit))
                else:
                    G.curUnit.HP -= harm2
                if reward: attackerRew -= harm2 / 100.0 * unitValue(G.curUnit) + (not G.curUnit.alive) * unitValue(attacked)
            if show:
                print("Unit %s @ (%d, %d) attack %s (%d, %d) (-HP %d %s)" % (G.curUnit.Type, *G.curUnit.pos, attacked.Type, ci, cj, harm, "" if attacked.alive else "killed"))
                if counterattack: print("-> Unit %s @ (%d, %d) counterattack %s (%d, %d) (-HP %d %s)" % (attacked.Type, ci, cj, G.curUnit.Type, *G.curUnit.pos, harm2, "" if G.curUnit.alive else "killed"))
        if len(targetPos) == 0:
            if show: print("No target. Unit @ (%d, %d) stand by" % (*G.curUnit.pos,))
            if reward: attackerRew = 0.0
        G.curUnit.moved = True
        G.curUnit = None
        G.UIstate = SELECT_UNIT
        # compute the reward of this action for each player
        if reward:
            attackedRew = - attackerRew
            rewards = [attackerRew, attackedRew] if attacked.player == 2 else [attackedRew, attackerRew]
            return rewards
        else:
            return [0.0 for player in G.playerList]

    def attack_AOE(G, centPos, posList, show=True, reward=False, checklegal=False):
        unitValue = lambda unit: valueDict[unit.Type]  # value function for each value. Should be learnable
        # attRange = G.getAttackRange(G.curUnit.pos, G.curUnit.AttackRng[0], G.curUnit.AttackRng[1])
        # targetPos, targetUnits = G.getTargetInRange(G.curUnit, attRange)
        # if show: G.drawLocation(attRange, (220, 180, 180))  # draw a list of location in one color
        if show: G.drawCsrLocation(posList, (250, 130, 130))
        unit_pos = [unit.pos for unit in G.unitList]
        if reward:  attackerRew = 0  # cumulate reward for each attacked enemy
        if show: print("Unit %s @ (%d, %d) AOE attack :" % (G.curUnit.Type, *G.curUnit.pos,), posList)
        for targpos in posList:  # confirmed attack
            attacked = G.unitList[unit_pos.index(targpos)]#targetUnits[targetPos.index((ci, cj))]
            # Real computation code for attack
            # harm = int(G.curUnit.Attack / 100.0 * G.curUnit.HP) - attacked.Defence
            harm = max(1, G.curUnit.Attack - attacked.Defence)  # AOE Magic don't suffer from HP loss #FIXME
            isEnemy = 1 if G.curUnit.player != attacked.player else -1  # AOE can harm friemd team!
            if attacked.HP - harm <= 0:
                harm = attacked.HP
                attacked.HP = 0
                attacked.alive = False
                G.unitList.pop(G.unitList.index(attacked))
                unit_pos = [unit.pos for unit in G.unitList]
            else:
                attacked.HP -= harm
            if reward: attackerRew += isEnemy * (harm / 100.0 * unitValue(attacked) + (not attacked.alive) * unitValue(attacked))
        G.curUnit.moved = True
        G.curUnit = None
        G.UIstate = SELECT_UNIT
        # compute the reward of this action for each player
        if reward:
            attackedRew = - attackerRew
            rewards = [attackerRew, attackedRew] if attacked.player == 2 else [attackedRew, attackerRew]
            return rewards
        else:
            return [0.0 for player in G.playerList]

    def stand(G, show=True):
        if show: print("No target. Unit %s @ (%d, %d) stand by" % (G.curUnit.Type, *G.curUnit.pos,))
        G.curUnit.moved = True
        G.curUnit = None
        G.UIstate = SELECT_UNIT

    def getPossibleMoves(G, UIstate=None, curUnit=None, unitList=None):
        """ Get Legal Action Space for Given state.
        This is a key API for policy algorithms. """
        if UIstate is None: UIstate = G.UIstate
        if curUnit is None: curUnit = G.curUnit
        if unitList is None: unitList = G.unitList
        if UIstate is SELECT_UNIT:
            selectable_pos, _ = G.getSelectableUnit(unitList=unitList)
            selectable_tilepos, _ = G.getSelectableTile()
            legalActs = [("turnover", [])]
            if len(selectable_pos) > 0: # select unit here
                # legalActs = legalActs[1:] # Allow or not allow turnover when there is still feasible acts.
                legalActs += [("select", [pos]) for pos in selectable_pos] # , SELECT_UNIT
            # else:  # turn over is available if there is no unit to select
            if len(selectable_tilepos) > 0:  # buy units here.
                curFund = G.playerFund[G.curIdx]
                affordableTypes = [type for type, price in priceDict.items() if price <= curFund]
                for pos in selectable_tilepos:
                    legalActs += [("buy", [pos, unitType]) for unitType in affordableTypes]
            # return [("turnover", [])], SELECT_UNIT
            return legalActs, SELECT_UNIT
        if UIstate is SELECT_MOVTARGET:
            unit_pos = [unit.pos for unit in unitList if unit is not curUnit] # other unit's position. Or you cannot stay put
            obst_pos = G.getObstacleInRange(curUnit, None, unitList=unitList)
            movRange = G.getMovRange(curUnit.pos, curUnit.Movepnt, obst_pos)
            return [("move", [pos]) for pos in movRange if pos not in unit_pos], SELECT_ATTTARGET
        if UIstate is SELECT_ACTION:
            actions = [("useAttack", [])]
            if STORM in curUnit.ExtraAct:
                actions.append(("useStorm", []))
            if HEAL in curUnit.ExtraAct:
                actions.append(("useHeal", []))
            return actions, (SELECT_ATTTARGET, SELECT_AOETARGET)
        if UIstate is SELECT_AOETARGET:
            attRange = G.getAttackRange(curUnit.pos, curUnit.AttackRng[0], curUnit.AttackRng[1])
            centPosList, targetPosList = G.getAOETargetInRange(curUnit, attRange, unitList=unitList, radius=1)
            return [("stand", [])] + [("AOE", [cent, posList]) for cent, posList in zip(centPosList, targetPosList)], SELECT_UNIT
        if UIstate is SELECT_ATTTARGET:
            # attRange = G.getAttackRange(curUnit.pos, curUnit.AttackRng[0], curUnit.AttackRng[1])
            # targetPos, targetUnits = G.getTargetInRange(curUnit, attRange, unitList=unitList)
            targetPos, targetUnits, targetDist = G.getTargetInRange(curUnit, None, unitList=unitList)
            return [("stand", [])] + [("attack", [pos]) for pos in targetPos], SELECT_UNIT
        if UIstate is SELECT_REMOVTARGET:
            raise NotImplementedError
        if UIstate is END_TURN:
            return [("turnover", [])], SELECT_UNIT

    def action_execute(self, action_type, param=[], clone=False, show=True, reward=False, checklegal=True):
        """
        clone: Either copy game state and execute the transition or inplace change the current game State
        checklegal: A flag sent into the specific action functions, whether or not check the action is legal
            (e.g. attacking nowhere, move to obstacle). During model based searching, all actions proposed will be
            legal, so no need for that. But for User in the loop scenario, need more checking.
        show: print the action or not.
        """
        G = deepcopy(self) if clone else self
        rewards = [0.0 for player in G.playerList]
        if action_type is "turnover":
            G.endTurn(show=show)
        if action_type is "select":
            G.selectUnit(param[0], show=show)
        if action_type is "buy":
            G.buyUnit(param[0], param[1], show=show, checklegal=checklegal)
        if action_type is "move":
            G.move(param[0], show=show, checklegal=checklegal)
        if action_type is "useAttack":  # Change UIstate, nothing really happens
            G.UIstate = SELECT_ATTTARGET
        if action_type is "useStorm":
            G.UIstate = SELECT_AOETARGET
        if action_type is "useHeal":
            G.UIstate = SELECT_HEALTARGET
        if action_type is "attack":
            rewards = G.attack(param[0], show=show, reward=reward, checklegal=checklegal) # attack will generate real rewards!
        if action_type is "AOE":
            rewards = G.attack_AOE(param[0], param[1], show=show, reward=reward, checklegal=checklegal) # attack will generate real rewards!
        if action_type is "stand":
            G.stand(show=show)
        return G, rewards

    def action_seq_execute(self, actseq, clone=False, show=True, reward=False, checklegal=True):
        """Sequential version of `action_execute` return cumulated reward from this sequence"""
        G = deepcopy(self) if clone else self
        cum_rewards = [0.0 for player in G.playerList]
        for action_type, param in actseq:
            rewards = [0.0 for player in G.playerList]
            if action_type is "turnover":
                G.endTurn(show=show)
            elif action_type is "select":
                G.selectUnit(param[0], show=show)
            elif action_type is "buy":
                G.buyUnit(param[0], param[1], show=show, checklegal=checklegal)
            elif action_type is "move":
                G.move(param[0], show=show, checklegal=checklegal)
            elif action_type is "useAttack":
                G.UIstate = SELECT_ATTTARGET
            elif action_type is "useStorm":
                G.UIstate = SELECT_AOETARGET
            elif action_type is "useHeal":
                G.UIstate = SELECT_HEALTARGET
            elif action_type is "attack":  # attack will generate real rewards!
                rewards = G.attack(param[0], show=show, reward=reward, checklegal=checklegal)
            elif action_type is "AOE":  # attack will generate real rewards!
                rewards = G.attack_AOE(param[0], param[1], show=show, reward=reward, checklegal=checklegal)
            elif action_type is "stand":
                G.stand(show=show)
            cum_rewards = [cum_rewards[i] + rewards[i] for i, _ in enumerate(G.playerList)]
        return G, cum_rewards

    def drawBackground(G):
        pg.draw.rect(G.screen, LIGHTYELLOW, pg.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT), 0)
        for i in range(MAP_WIDTH // TileW):
            for j in range(MAP_HEIGHT // TileW):
                pg.draw.rect(G.screen, (  200, 200, 200), pg.Rect(i*TileW+Margin, j*TileW+Margin, TileW-2*Margin, TileW-2*Margin))

    def drawLocation(G, pos_list, color=(150, 200, 200)):
        for i, j in pos_list:
            pg.draw.rect(G.screen, color,
                 pg.Rect(i * TileW + Margin, j * TileW + Margin, TileW - 2*Margin, TileW - 2*Margin))

    def drawCircTarget(G, pos_list, color=(150, 200, 200)):
        for i, j in pos_list:
            pg.draw.circle(G.screen, color, (int((i+1/2) * TileW), int((j+1/2) * TileW)),
                               (TileW - 2*Margin) // 2 )

    def drawCsrLocation(G, pos_list, color=(150, 200, 200), CsrWidth = CsrWidth):
        """Just an empty square indicating the position of cursor"""
        for i, j in pos_list:
            pg.draw.rect(G.screen, color,
                 pg.Rect(i * TileW + Margin + CsrWidth/2, j * TileW + Margin + CsrWidth/2, TileW - 2*Margin - CsrWidth, TileW - 2*Margin - CsrWidth), CsrWidth)

    def drawBuyScreen(G, ):
        # tmpUnitList
        # G.drawUnitList(tmpUnitList)
        pg.draw.rect(G.screen, LIGHTBLUE, pg.Rect(5*Margin, 5*Margin, MAP_WIDTH-10*Margin, MAP_HEIGHT-10*Margin), 0)
        showpos = [(3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7)]
        for i, j in showpos:
            pg.draw.rect(G.screen, (200, 200, 200),
                pg.Rect(i*TileW+Margin, j*TileW+Margin, TileW-2*Margin, TileW-2*Margin))

        curFund = G.playerFund[G.curIdx]
        for unitpos, (unitType, price) in zip(showpos, priceDict.items()):
            i, j = unitpos
            if unitType is "Soldier":
                pg.draw.rect(G.screen, playerColor[G.curPlayer],
                 pg.Rect(i * TileW + UMargin/2, j * TileW + UMargin/2, TileW - UMargin, TileW - UMargin))
            elif unitType is "Archer":
                pg.draw.circle(G.screen, playerColor[G.curPlayer], (int((i+1/2) * TileW), int((j+1/2) * TileW)),
                               (TileW - UMargin) // 2 )
            elif unitType is "Catapult":
                pg.draw.polygon(G.screen, playerColor[G.curPlayer], [(int((i  ) * TileW), int((j + 1 / 2) * TileW)),
                                                                    (int((i + 1 / 2) * TileW), int((j + 1) * TileW)),
                                                                    (int((i + 1) * TileW), int((j + 1 / 2) * TileW)),
                                                                    (int((i + 1 / 2) * TileW), int((j) * TileW)),] )
            elif unitType is "Knight":
                pg.draw.polygon(G.screen, playerColor[G.curPlayer], [(int((i  ) * TileW), int((j ) * TileW)),
                                                                    (int((i + 1 ) * TileW), int((j ) * TileW)),
                                                                    (int((i + 1 / 2) * TileW), int((j + 1) * TileW)), ] )
            elif unitType is "StoneMan":
                pg.draw.polygon(G.screen, playerColor[G.curPlayer], [(int((i + 1) * TileW), int((j + 2 / 4) * TileW)),
                                                                     (int((i + 3 / 4) * TileW), int((j + 1 / 4) * TileW)),
                                                                    (int((i + 1 / 4) * TileW), int((j + 1 / 4) * TileW)),
                                                                    (int((i) * TileW), int((j + 2 / 4) * TileW)),
                                                                    (int((i + 1 / 4) * TileW), int((j + 3 / 4) * TileW)),
                                                                    (int((i + 3 / 4) * TileW), int((j + 3 / 4) * TileW)), ] )
            elif unitType is "StormSummoner":
                pg.draw.polygon(G.screen, playerColor[G.curPlayer], [(int((i) * TileW), int((j + 1 / 4) * TileW)),
                                                                    (int((i + 1) * TileW), int((j + 1 / 4) * TileW)),
                                                                    (int((i + 3 / 4) * TileW), int((j + 3 / 4) * TileW)),
                                                                    (int((i + 1 / 4) * TileW), int((j + 3 / 4) * TileW)), ] )
            Pricecolor = (160, 20, 20) if price > curFund else (20, 160, 20) # different HP color denotes moved or un-moved unit
            img = font.render('%d' % price, True, Pricecolor)
            screen.blit(img, ((i + 1) * TileW - 28, (j +1) * TileW - 18))

    def drawUnitList(G, UnitList=None, ):
        """# Really draw unit lists!Represent different types of units with shapes"""
        if UnitList is None: UnitList = G.unitList
        for unit in UnitList:
            if not unit.alive: continue
            i, j = unit.pos
            if unit.Type is "Soldier":
                pg.draw.rect(G.screen, playerColor[unit.player],
                 pg.Rect(i * TileW + UMargin/2, j * TileW + UMargin/2, TileW - UMargin, TileW - UMargin))
            elif unit.Type is "Archer":
                pg.draw.circle(G.screen, playerColor[unit.player], (int((i+1/2) * TileW), int((j+1/2) * TileW)),
                               (TileW - UMargin) // 2 )
            elif unit.Type is "Catapult":
                pg.draw.polygon(G.screen, playerColor[unit.player], [(int((i  ) * TileW), int((j + 1 / 2) * TileW)),
                                                                    (int((i + 1 / 2) * TileW), int((j + 1) * TileW)),
                                                                    (int((i + 1) * TileW), int((j + 1 / 2) * TileW)),
                                                                    (int((i + 1 / 2) * TileW), int((j) * TileW)),] )
            elif unit.Type is "Knight":
                pg.draw.polygon(G.screen, playerColor[unit.player], [(int((i  ) * TileW), int((j ) * TileW)),
                                                                    (int((i + 1 ) * TileW), int((j ) * TileW)),
                                                                    (int((i + 1 / 2) * TileW), int((j + 1) * TileW)), ] )
            elif unit.Type is "StoneMan":
                pg.draw.polygon(G.screen, playerColor[unit.player], [(int((i + 1) * TileW), int((j + 2 / 4) * TileW)),
                                                                     (int((i + 3 / 4) * TileW), int((j + 1 / 4) * TileW)),
                                                                    (int((i + 1 / 4) * TileW), int((j + 1 / 4) * TileW)),
                                                                    (int((i) * TileW), int((j + 2 / 4) * TileW)),
                                                                    (int((i + 1 / 4) * TileW), int((j + 3 / 4) * TileW)),
                                                                    (int((i + 3 / 4) * TileW), int((j + 3 / 4) * TileW)), ] )
            elif unit.Type is "StormSummoner":
                pg.draw.polygon(G.screen, playerColor[unit.player], [(int((i) * TileW), int((j + 1 / 4) * TileW)),
                                                                    (int((i + 1) * TileW), int((j + 1 / 4) * TileW)),
                                                                    (int((i + 3 / 4) * TileW), int((j + 3 / 4) * TileW)),
                                                                    (int((i + 1 / 4) * TileW), int((j + 3 / 4) * TileW)), ] )
            HPcolor = (160, 20, 20) if unit.moved else (20, 160, 20) # different HP color denotes moved or un-moved unit
            img = font.render('%d' % unit.HP, True, HPcolor)
            screen.blit(img, ((i + 1) * TileW - 28, (j +1) * TileW - 18))

    def drawBuildingList(G, buildingList=None, ):
        """# Really draw unit lists!Represent different types of units with shapes"""
        if buildingList is None: buildingList = G.buildingList
        for bldg in buildingList:
            # if not unit.alive: continue
            i, j = bldg.pos
            if bldg.Type is "Castle":
                pg.draw.polygon(G.screen, playerColor[bldg.player],[(int((i) * TileW), int((j + 1 / 4) * TileW)),
                                                                    (int((i + 1) * TileW), int((j + 1 / 4) * TileW)),
                                                                    (int((i + 6.5 / 8) * TileW), int((j + 3 / 8) * TileW)),
                                                                    (int((i + 6.5 / 8) * TileW), int((j + 7 / 8) * TileW)),
                                                                    (int((i + 1.5 / 8) * TileW), int((j + 7 / 8) * TileW)),
                                                                    (int((i + 1.5 / 8) * TileW), int((j + 3 / 8) * TileW)), ], 3)
            elif bldg.Type is "Village":
                pg.draw.polygon(G.screen, playerColor[bldg.player], [(int((i + 0.5 / 8) * TileW), int((j + 3 / 8) * TileW)),
                                                                     (int((i + 2 / 4) * TileW), int((j + 0.5 / 8) * TileW)),
                                                                     (int((i + 7.5 / 8) * TileW), int((j + 3 / 8) * TileW)),
                                                                     (int((i + 3 / 4) * TileW), int((j + 3 / 8) * TileW)),
                                                                     (int((i + 3 / 4) * TileW), int((j + 6 / 8) * TileW)),
                                                                     (int((i + 1 / 4) * TileW), int((j + 6 / 8) * TileW)),
                                                                     (int((i + 1 / 4) * TileW), int((j + 3 / 8) * TileW)), ], 3)

    def getSelectableTile(G, curPlayer=None, buildingList=None):
        if curPlayer is None: curPlayer = G.curPlayer
        if buildingList is None: buildingList = G.buildingList
        unitPoses = set(unit.pos for unit in G.unitList)
        selectablePos = []
        selectableTile = []
        for bldg in buildingList:
            if bldg.player == curPlayer and PURCHASE in bldg.Props:
                if bldg.pos in unitPoses: continue
                selectablePos.append(bldg.pos)
                selectableTile.append(bldg)
        return selectablePos, selectableTile

    def getMovRange(G, pos, movpnt, obstacles=[]):
        cost = lambda xx, yy: 1 if (xx, yy) not in obstacles else 1E5
        tovisit = Queue()
        tovisit.push((pos, movpnt))
        visited = set()
        while not tovisit.isEmpty():
            curpos, curmvp = tovisit.pop()
            if curpos in visited:
                continue
            visited.add(curpos)
            x, y = curpos
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                xx, yy = x + dx, y + dy
                nextmvp = curmvp - cost(xx, yy)
                if nextmvp >= 0 and (0 <= xx < G.mapW) and (0 <= yy < G.mapH): # prune out of map positions
                    tovisit.push(((xx, yy), nextmvp))
        return list(visited)  # list(mvp)

    def getAttackRange(G, pos, LB, UB):  # FIXED: BE MORE EFFICIENT, Use double forloop.
        """Actually this is only necessary for GUI, not for computer! """
        # cost = lambda xx, yy: 1
        x, y = pos
        poslist = set()
        for dx in range(-UB, UB + 1):
            for dy in range(-UB + abs(dx), min(- LB + abs(dx) + 1, 0)):
                poslist.add((x + dx, y + dy))
            for dy in range(max(LB - abs(dx), 0), UB - abs(dx) + 1):
                poslist.add((x + dx, y + dy))
        return list(poslist)
        # Older BFS naive version.
        # tovisit = Queue()
        # tovisit.push((pos, 0))
        # visited = set()
        # while not tovisit.isEmpty():
        #     curpos, curdis = tovisit.pop()
        #     visited.add(curpos)
        #     x, y = curpos
        #     for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
        #         xx, yy = x + dx, y + dy
        #         if (xx, yy) in visited:
        #             continue
        #         nextdis = curdis + 1
        #         if nextdis <= UB:
        #             tovisit.push(((xx, yy), nextdis))
        #             if nextdis >= LB:
        #                 poslist.append((xx, yy))
        # return poslist

    def getSelectableUnit(G, unitList=None, curPlayer=None):
        if unitList is None: unitList = G.unitList
        if curPlayer is None: curPlayer = G.curPlayer
        selectablePos = []
        selectableUnit = []
        for unit in unitList:
            if unit.player == curPlayer and not unit.moved:
                selectablePos.append(unit.pos)
                selectableUnit.append(unit)
        return selectablePos, selectableUnit

    def getTargetInRange(G, curUnit, attRange, unitList=None, AttackRng=None):
        """attRange can be None to indicate all opponent units"""
        if unitList is None: unitList = G.unitList
        targetPos = []
        targetUnit = []
        targetDist = []
        if attRange is None:
            ci, cj = G.curUnit.pos
            LB, UB = G.curUnit.AttackRng if AttackRng is None else AttackRng
            for unit in unitList:
                if unit.player is not curUnit.player:
                    attDis = abs(ci - unit.pos[0]) + abs(cj - unit.pos[1])
                    if LB <= attDis <= UB:
                        targetPos.append(unit.pos)
                        targetUnit.append(unit)
                        targetDist.append(attDis)
        else:
            ci, cj = G.curUnit.pos
            for unit in unitList:
                if unit.player is not curUnit.player and unit.pos in attRange:
                    attDis = abs(ci - unit.pos[0]) + abs(cj - unit.pos[1])
                    targetPos.append(unit.pos)
                    targetUnit.append(unit)
                    targetDist.append(attDis)
        return targetPos, targetUnit, targetDist

    def getDxDyList(G, radius):
        """Small utility function to get dx, dy pairs within an L1 radius"""
        dxdy = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius+abs(dx), radius-abs(dx)+1):
                dxdy.append((dx, dy))
        return dxdy

    def getAOETargetInRange(G, curUnit, attRange, unitList=None, radius=1):
        if unitList is None: unitList = G.unitList
        attRange = set(attRange)
        # augAttRange = G.getAttackRange(curUnit.pos, curUnit.AttackRng[0] - radius, curUnit.AttackRng[1] + radius)
        # targetPos, targetUnit = G.getTargetInRange(curUnit, augAttRange, unitList) # Increase efficiency!
        targetPos, targetUnit, targetDist = G.getTargetInRange(curUnit, None, unitList=unitList,
                            AttackRng=(curUnit.AttackRng[0] - radius, curUnit.AttackRng[1] + radius))
        centerTargetDict = dict()
        for unitpos, unit in zip(targetPos, targetUnit):
            x, y = unitpos
            for dx, dy in G.getDxDyList(radius):
                xx, yy = x + dx, y + dy
                if (xx, yy) in attRange:
                    if (xx, yy) in centerTargetDict:
                        centerTargetDict[(xx, yy)].append(unitpos)
                    else:
                        centerTargetDict[(xx, yy)] = [unitpos]

        centerPos = list(centerTargetDict.keys())
        targetPosList = [centerTargetDict[cent] for cent in centerPos]
        return centerPos, targetPosList, # targetUnitList

    def getMovAttPair(G, curUnit, unitList=None, radius=1):
        """An offline calculation, not assuming the unit is moved or not.
        This calculation is super efficient! """
        if unitList is None: unitList = G.unitList
        unit_pos = set([unit.pos for unit in unitList if
                    unit is not curUnit])  # other unit's position. Or you cannot stay put
        obst_pos = G.getObstacleInRange(curUnit, None, unitList=unitList)
        movRange = set(G.getMovRange(curUnit.pos, curUnit.Movepnt, obst_pos))
        valMovRange = movRange.difference(unit_pos)
        LB, UB = curUnit.AttackRng
        allEnemyPos, allEnemyUnit = G.getAllEnemyUnit(unitList) # assuming curPlayer is player of the curUnit
        AtkMvPairs = []
        AOEAtkPairs = []
        MvStandPairs = [] # no attack no reward
        canSTORM = STORM in curUnit.ExtraAct
        for movpos in valMovRange:
            if canSTORM: centerTargetDict = defaultdict(set)
            for tarpos, tarUnit in zip(allEnemyPos, allEnemyUnit):
                tarDist = (abs(movpos[0] - tarpos[0]) + abs(movpos[1] - tarpos[1]))
                if LB <= tarDist <= UB:
                    AtkMvPairs.append([("move", [movpos]), ("attack", [tarpos]), tarUnit])
                if canSTORM and LB - radius <= tarDist <= UB + radius:
                    x, y = tarpos
                    for dx, dy in G.getDxDyList(radius):
                        xx, yy = x + dx, y + dy
                        if LB <= (abs(movpos[0] - xx) + abs(movpos[1] - yy)) <= UB:
                            centerTargetDict[(xx, yy)].add(tarpos)
            if canSTORM: AOEAtkPairs.extend(
                    [[("move", [movpos]), ("AOE", [cent, posList])] for cent, posList in centerTargetDict.items()])
            # Evaluation func
            MvStandPairs.append([("move", [movpos]), ("stand", [])])  # no attack just stand.
        return AtkMvPairs, MvStandPairs, AOEAtkPairs

    def getCombatStats(G, attacker, attacked, atkrpos=None, atkdpos=None):
        """Key func to simulate Combat and output stats for AI usage.
        An offline calculation, """
        if atkrpos is None: atkrpos = attacker.pos
        if atkdpos is None: atkdpos = attacked.pos
        harm = max(1, int(attacker.Attack / 100.0 * attacker.HP) - attacked.Defence)  # - tile[atkdpos].Defence
        atkd_HP_aft = attacked.HP - harm
        atkd_alive = True
        if atkd_HP_aft <= 0:  atkd_alive = False
        attDis = abs(atkrpos[0] - atkdpos[0]) + abs(atkrpos[1] - atkdpos[1])
        counterattack = (attacked.AttackRng[0] <= attDis <= attacked.AttackRng[1]) and atkd_alive  # and bla bla bla
        harm2, atkr_alive = 0, True
        if counterattack:
            harm2 = max(1, int(attacked.Attack / 100.0 * atkd_HP_aft) - attacker.Defence)  # - tile[atkrpos].Defence
            atkr_HP_aft = attacker.HP - harm2
            if atkr_HP_aft <= 0:  atkr_alive = False
        # Compute reward value
        atkrReward = harm / 100.0 * unitPrice(attacked) + (not atkd_alive) * unitPrice(attacked)
        if counterattack:
            atkrReward -= harm2 / 100.0 * unitPrice(attacker) + (not atkr_alive) * unitPrice(attacker)
        return harm, atkd_alive, harm2, atkr_alive, atkrReward

    def getAOEStats(G, attacker, attackedPoses, ):
        """This is the counterpart for `getCombatStats` but for AOE attack (where there is no counter attack now.)"""
        harms = []
        alives = []
        AOEReward = 0
        unit_pos = [unit.pos for unit in G.unitList]
        for targpos in attackedPoses:
            attacked = G.unitList[unit_pos.index(targpos)]
            harm = max(1, attacker.Attack - attacked.Defence)  # AOE Magic don't suffer from HP loss #FIXME
            isEnemy = 1 if attacker.player != attacked.player else -1  # AOE can harm friemd team!
            if attacked.HP - harm <= 0:
                harm = attacked.HP
                alives.append(False)
            else:
                alives.append(True)
            harms.append(attacked.HP)
            AOEReward += isEnemy * (harm / 100.0 * unitPrice(attacked) + (not attacked.alive) * unitPrice(attacked))
        return harms, alives, AOEReward

    def getUnitAttackCoverage(G, curUnit, movRange=None, unitList=None):
        if unitList is None: unitList = G.unitList
        if movRange is None:
            unit_pos = set([unit.pos for unit in unitList if
                            unit is not curUnit])  # other unit's position. Or you can stay on top of unit in same player
            obst_pos = G.getObstacleInRange(curUnit, None, unitList=unitList)
            movRange = set(G.getMovRange(curUnit.pos, curUnit.Movepnt, obst_pos))
            movRange = movRange.difference(unit_pos)
        coverSet = set()
        for movpos in movRange:
            coverSet.update(G.getAttackRange(movpos, *curUnit.AttackRng))
        return coverSet

    def getAllEnemyUnit(G, unitList=None):
        """"""
        if unitList is None: unitList = G.unitList
        targetPos = []
        targetUnit = []
        for unit in unitList:
            if unit.player is not G.curPlayer:
                targetPos.append(unit.pos)
                targetUnit.append(unit)
        return targetPos, targetUnit

    def getObstacleInRange(G, curUnit, movRange, unitList=None):
        if unitList is None: unitList = G.unitList
        targetPos = []
        # targetUnit = []
        for unit in unitList:
            if unit.player is not curUnit.player and (movRange is None or unit.pos in movRange):
                targetPos.append(unit.pos)
                #targetUnit.append(unit)
        return targetPos# , targetUnit

if __name__=="__main__":
    game = GameStateCtrl()
    game.GUI_loop()