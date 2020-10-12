#%%
import pygame as pg
from source.util import Queue, Stack, PriorityQueue
from random import choice
from time import time
from copy import copy, deepcopy
pg.display.set_caption("SLG board")
SCREEN = pg.display.set_mode((800,500)) # get screen
screen = pg.display.get_surface()
# Setup Font
pg.font.init()
font = pg.font.SysFont("microsoftsansserif", 16, bold=True)
# Utility to detect DoubleClick
dbclock = pg.time.Clock()
DOUBLECLICKTIME = 250

LIGHTYELLOW = (247, 238, 214)
MAP_WIDTH = 800
MAP_HEIGHT = 500
TileW = 50
Margin = 2
CsrWidth = 5
UMargin = 20
playerColor = {1: (20, 20, 20), 2: (120, 20, 20)} # Color for each player number 

class Unit:
    def __init__(self, player, pos, cfg=None):
        self.player = player
        self.pos = pos
        self.alive = True
        self.moved = True
        self.Buff = [] # Buff is a state
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
            # self.exp
            # self.level
# List of Abilities
HEAVYMACHINE = 6
SoldierCfg = {"Type": "Soldier", "HP": 100, "Attack": 55, "Defence": 10, "Movepnt": 4, "AttackRng": (1, 1), "Ability": [], "ExtraAct": [],}
ArcherCfg = {"Type": "Archer", "HP": 100, "Attack": 45, "Defence":  5, "Movepnt": 4, "AttackRng": (2, 2), "Ability": [], "ExtraAct": [],}
KnightCfg = {"Type": "Knight", "HP": 100, "Attack": 60, "Defence":  15, "Movepnt": 6, "AttackRng": (1, 1), "Ability": [], "ExtraAct": [],}
CatapultCfg = {"Type": "Catapult", "HP": 100, "Attack": 70, "Defence":  5, "Movepnt": 3, "AttackRng": (2, 7), "Ability": [HEAVYMACHINE, ], "ExtraAct": [],}
valueDict = {"Soldier": 100, "Archer": 150, "Knight":400, "Catapult": 700}
#%%
def playerIterator(playerList):
    turn = 0
    while True:
        turn += 1
        for player in playerList: # and player is alive
            yield player, turn

# UIState Definition
END_TURN = 0
SELECT_UNIT = 1
SELECT_ACTION = 2
SELECT_MOVTARGET = 3
SELECT_ATTTARGET = 4
SELECT_REMOVTARGET = 5
class GameStateCtrl:
    def __init__(G):
        G.playerList = [1, 2]
        G.curPlayer = G.playerList[-1] # UIState starts from END_TURN so it will transition into first player
        # G.playerIter = playerIterator(G.playerList)
        G.curTurn = 0
        G.screen = screen
        G.mapH = screen.get_height() // TileW
        G.mapW = screen.get_width() // TileW
        G.UIstate = END_TURN
        G.unitList = []
        G.curUnit = None
        G.unitList.append(Unit(player=1, pos=(2, 2), cfg=SoldierCfg))
        G.unitList.append(Unit(player=1, pos=(3, 2), cfg=SoldierCfg))
        G.unitList.append(Unit(player=1, pos=(2, 3), cfg=ArcherCfg))
        G.unitList.append(Unit(player=1, pos=(3, 4), cfg=KnightCfg))
        G.unitList.append(Unit(player=1, pos=(1, 1), cfg=CatapultCfg))
        G.unitList.append(Unit(player=2, pos=(5, 8), cfg=SoldierCfg))
        G.unitList.append(Unit(player=2, pos=(6, 8), cfg=SoldierCfg))
        G.unitList.append(Unit(player=2, pos=(7, 5), cfg=ArcherCfg))
        G.unitList.append(Unit(player=2, pos=(5, 5), cfg=KnightCfg))
        G.unitList.append(Unit(player=2, pos=(8, 8), cfg=CatapultCfg))

    def __deepcopy__(self, memodict={}):
        newG = GameStateCtrl()
        newG.__dict__['screen'] = self.__dict__['screen']
        for key, vals in self.__dict__.items():
            if key is 'screen': continue
            newG.__dict__[key] = deepcopy(vals)
        if self.curUnit is not None:
            unitId = self.unitList.index(self.curUnit) # re-establish the link between the list and the reference to it.
            newG.curUnit = newG.unitList[unitId]
        return newG

    def playerIterator(G):
        """This is really handy function but cause much pain!"""
        turn = 0
        while True:
            turn += 1
            for player in G.playerList:  # and player is alive
                yield player, turn

    def GUI_loop(G, GUI=True, csr_pos=(5, 6)):
        """This is less hierarchical, more linear programming style"""
        ci, cj = csr_pos # csr is a GUI concept not a gameState
        Exitflag = False
        while not Exitflag:
            # Input Processor
            K_confirm = False
            K_cancel = False
            K_Turnover = False
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    Exitflag = True
                if event.type == pg.MOUSEBUTTONDOWN:
                    mouseX, mouseY = pg.mouse.get_pos()
                    ci, cj = mouseX // TileW, mouseY // TileW
                    if dbclock.tick() < DOUBLECLICKTIME:
                        K_confirm = True
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_UP: cj -= 1
                    if event.key == pg.K_DOWN: cj += 1
                    if event.key == pg.K_LEFT: ci -= 1
                    if event.key == pg.K_RIGHT: ci += 1
                    if event.key == pg.K_SPACE: K_confirm = True
                    if event.key == pg.K_ESCAPE: K_cancel = True
                    if event.key == pg.K_TAB: K_Turnover = True
            G.drawBackground()
            # drawTerrain(screen, gameState)
            if K_Turnover:
                G.UIstate = END_TURN

            if G.UIstate is END_TURN:
                # nextPlayer, nextTurn = next(G.playerIter)  # playerList[playerList.index(curPlayer)+1]
                curIdx = G.playerList.index(G.curPlayer)
                if curIdx == len(G.playerList) - 1:
                    nextTurn, nextPlayer = G.curTurn + 1, G.playerList[0]
                else:
                    nextTurn, nextPlayer = G.curTurn, G.playerList[curIdx + 1]
                # Do sth at turn over
                for unit in G.unitList:
                    if unit.player is nextPlayer: unit.moved = False
                    if unit.player is G.curPlayer: unit.moved = True
                G.curPlayer, G.curTurn = nextPlayer, nextTurn
                G.UIstate = SELECT_UNIT
                # drawTurnover(screen)

            if G.UIstate == SELECT_UNIT:
                posDict = {unit.pos: unit for unit in G.unitList}
                selectable_pos, selectable_unit = G.getSelectableUnit()  # unitList, curPlayer  # add condition for selectable
                # unit_pos = [unit.pos for unit in unitList
                #             if unit.player == curPlayer and not unit.moved]  # add condition for selectable
                if K_confirm and (ci, cj) in selectable_pos:
                    print("Unit selected (%d, %d)"%(ci, cj))
                    # unitId = unit_pos.index((ci, cj))
                    G.curUnit = posDict[(ci, cj)] # unitList[unitId]
                    G.UIstate = SELECT_MOVTARGET

            elif G.UIstate == SELECT_MOVTARGET:
                unit_pos = [unit.pos for unit in G.unitList]
                obst_pos = G.getObstacleInRange(G.curUnit, None, )
                movRange = G.getMovRange(G.curUnit.pos, G.curUnit.Movepnt, obst_pos)
                G.drawLocation(movRange, (160, 180, 180))  # draw a list of location in one color
                if K_confirm and (ci, cj) in movRange and (ci, cj) not in unit_pos:
                    print("Unit move (%d, %d) -> (%d, %d)"%(*G.curUnit.pos, ci, cj))
                    # move(unit, mov2i, mov2j)
                    ui_orig, uj_orig = G.curUnit.pos  # record this just in case user cancels
                    G.curUnit.pos = ci, cj  # ui, uj
                    G.UIstate = SELECT_ATTTARGET
                    # UIstate = SELECT_ACTION
                if K_cancel:
                    G.UIstate = SELECT_UNIT

            elif G.UIstate == SELECT_ATTTARGET:
                attRange = G.getAttackRange(G.curUnit.pos, G.curUnit.AttackRng[0], G.curUnit.AttackRng[1])
                targetPos, targetUnits = G.getTargetInRange(G.curUnit, attRange)
                G.drawLocation(attRange, (220, 180, 180))  # draw a list of location in one color
                G.drawCsrLocation(targetPos, (250, 130, 130))
                if K_confirm:
                    if (ci, cj) in targetPos:  # confirmed attack
                        print("Unit @ (%d, %d) attack (%d, %d)" % (*G.curUnit.pos, ci, cj))
                        attacked = targetUnits[targetPos.index((ci, cj))]
                        # Real computation code for attack
                        harm = int(G.curUnit.Attack / 100.0 * G.curUnit.HP) - attacked.Defence
                        attacked.HP -= abs(harm)
                        if attacked.HP <= 0:
                            attacked.alive = False
                            G.unitList.pop(G.unitList.index(attacked))
                        attDis = abs(ci - G.curUnit.pos[0]) + abs(cj - G.curUnit.pos[1])
                        counterattack = (attacked.AttackRng[0] <= attDis <= attacked.AttackRng[1]) and attacked.alive # and bla bla bla
                        if counterattack:
                            harm2 = int(attacked.Attack / 100.0 * attacked.HP) - G.curUnit.Defence
                            G.curUnit.HP -= abs(harm2)
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
            # drawUnits(screen, [(ui, uj)])  # gameState
            G.drawUnitList(G.unitList)
            G.drawCsrLocation([(ci, cj)])  # draw a list of location in one color
            pg.display.update()

    def endTurn(G, show=True):
        # nextPlayer, nextTurn = next(G.playerIter)  # playerList[playerList.index(curPlayer)+1]
        curIdx = G.playerList.index(G.curPlayer)
        if curIdx == len(G.playerList) - 1:
            nextTurn, nextPlayer = G.curTurn + 1, G.playerList[0]
        else:
            nextTurn, nextPlayer = G.curTurn, G.playerList[curIdx + 1]
        # Do sth at turn over
        for unit in G.unitList:
            if unit.player is nextPlayer: unit.moved = False
            if unit.player is G.curPlayer: unit.moved = True
        if show: print("Turn Changed, Next player %d, Turn %d"%(nextPlayer, nextTurn))
        G.curPlayer, G.curTurn = nextPlayer, nextTurn
        G.UIstate = SELECT_UNIT

    def selectUnit(G, csr, show=True):
        posDict = {unit.pos: unit for unit in G.unitList}
        selectable_pos, selectable_unit = G.getSelectableUnit()  # unitList, curPlayer  # add condition for selectable
        if csr in selectable_pos:
            if show: print("Unit selected (%d, %d)" % (*csr, ))
            G.curUnit = posDict[csr]  # unitList[unitId]
            G.UIstate = SELECT_MOVTARGET
        else:
            raise ValueError

    def move(G, csr, show=True):
        # ci, cj = csr
        unit_pos = [unit.pos for unit in G.unitList]
        obst_pos = G.getObstacleInRange(G.curUnit, None, )
        movRange = G.getMovRange(G.curUnit.pos, G.curUnit.Movepnt, obst_pos)
        if show: G.drawLocation(movRange, (160, 180, 180))  # draw a list of location in one color
        if csr in movRange and csr not in unit_pos:
            if show: print("Unit move (%d, %d) -> (%d, %d)"%(*G.curUnit.pos, *csr, ))
            # move(unit, mov2i, mov2j)
            ui_orig, uj_orig = G.curUnit.pos  # record this just in case user cancels
            G.curUnit.pos = csr  # ui, uj
            G.UIstate = SELECT_ATTTARGET
        else:
            raise ValueError

    def attack(G, csr, show=True, reward=False):
        unitValue = lambda unit: valueDict[unit.Type] # value function for each value. Should be learnable
        attRange = G.getAttackRange(G.curUnit.pos, G.curUnit.AttackRng[0], G.curUnit.AttackRng[1])
        targetPos, targetUnits = G.getTargetInRange(G.curUnit, attRange)
        if show: G.drawLocation(attRange, (220, 180, 180))  # draw a list of location in one color
        if show: G.drawCsrLocation(targetPos, (250, 130, 130))
        ci, cj = csr
        if (ci, cj) in targetPos:  # confirmed attack
            if show: print("Unit @ (%d, %d) attack (%d, %d)" % (*G.curUnit.pos, ci, cj))
            attacked = targetUnits[targetPos.index((ci, cj))]
            # Real computation code for attack
            harm = int(G.curUnit.Attack / 100.0 * G.curUnit.HP) - attacked.Defence
            attacked.HP -= abs(harm)
            if attacked.HP <= 0:
                attacked.alive = False
                G.unitList.pop(G.unitList.index(attacked))
            if reward: attackerRew = harm / 100.0 * unitValue(attacked) + (not attacked.alive) * unitValue(attacked)
            attDis = abs(ci - G.curUnit.pos[0]) + abs(cj - G.curUnit.pos[1])
            counterattack = (attacked.AttackRng[0] <= attDis <= attacked.AttackRng[1]) and attacked.alive # and bla bla bla
            if counterattack:
                harm2 = int(attacked.Attack / 100.0 * attacked.HP) - G.curUnit.Defence
                G.curUnit.HP -= abs(harm2)
                # FIXED: Currently Attacker and Attacked could Die together!
                if G.curUnit.HP <= 0:
                    G.curUnit.alive = False
                    G.unitList.pop(G.unitList.index(G.curUnit))
                if reward: attackerRew -= harm2 / 100.0 * unitValue(G.curUnit) + (not G.curUnit.alive) * unitValue(attacked)
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

    def stand(G, show=True):
        if show: print("No target. Unit @ (%d, %d) stand by" % (*G.curUnit.pos,))
        G.curUnit.moved = True
        G.curUnit = None
        G.UIstate = SELECT_UNIT

    def getPossibleMoves(G, UIstate=None, curUnit=None, unitList=None):
        if UIstate is None: UIstate = G.UIstate
        if curUnit is None: curUnit = G.curUnit
        if unitList is None: unitList = G.unitList
        if UIstate is SELECT_UNIT:
            selectable_pos, _ = G.getSelectableUnit(unitList=unitList)
            if len(selectable_pos) > 0:
                return [("select", [pos]) for pos in selectable_pos], SELECT_UNIT
            else: # turn over is available if there is no unit to select
                return [("turnover", [])], SELECT_UNIT
        if UIstate is SELECT_MOVTARGET:
            unit_pos = [unit.pos for unit in unitList]
            obst_pos = G.getObstacleInRange(curUnit, None, unitList=unitList)
            movRange = G.getMovRange(curUnit.pos, curUnit.Movepnt, obst_pos)
            return [("move", [pos]) for pos in movRange if pos not in unit_pos], SELECT_ATTTARGET
        if UIstate is SELECT_ATTTARGET:
            attRange = G.getAttackRange(curUnit.pos, curUnit.AttackRng[0], curUnit.AttackRng[1])
            targetPos, targetUnits = G.getTargetInRange(curUnit, attRange, unitList=unitList)
            return [("stand", [])] + [("attack", [pos]) for pos in targetPos], SELECT_UNIT
        if UIstate is SELECT_REMOVTARGET:
            raise NotImplementedError
        if UIstate is END_TURN:
            return [("turnover", [])], SELECT_UNIT

    def action_execute(self, action_type, param=[], clone=False, show=True, reward=False):
        G = deepcopy(self) if clone else self
        rewards = [0.0 for player in G.playerList]
        if action_type is "turnover":
            G.endTurn(show=show)
        if action_type is "select":
            G.selectUnit(param[0], show=show)
        if action_type is "move":
            G.move(param[0], show=show)
        if action_type is "attack":
            rewards = G.attack(param[0], show=show, reward=reward)
        if action_type is "stand":
            G.stand(show=show)
        return G, rewards

    def action_seq_execute(self, actseq, clone=False, show=True, reward=False):
        G = deepcopy(self) if clone else self
        cum_rewards = [0.0 for player in G.playerList]
        for action_type, param in actseq:
            rewards = [0.0 for player in G.playerList]
            if action_type is "turnover":
                G.endTurn(show=show)
            if action_type is "select":
                G.selectUnit(param[0], show=show)
            if action_type is "move":
                G.move(param[0], show=show)
            if action_type is "attack":
                rewards = G.attack(param[0], show=show, reward=reward)
            if action_type is "stand":
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

    def drawCsrLocation(G, pos_list, color=(150, 200, 200), CsrWidth = CsrWidth):
        """Just an empty square indicating the position of cursor"""
        for i, j in pos_list:
            pg.draw.rect(G.screen, color,
                 pg.Rect(i * TileW + Margin + CsrWidth/2, j * TileW + Margin + CsrWidth/2, TileW - 2*Margin - CsrWidth, TileW - 2*Margin - CsrWidth), CsrWidth)

    def drawUnits(G, pos_list, color=(20, 20, 20)):
        for i, j in pos_list:
            pg.draw.rect(G.screen, color,
                 pg.Rect(i * TileW + UMargin/2, j * TileW + UMargin/2, TileW - UMargin, TileW - UMargin))

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
            HPcolor = (160, 20, 20) if unit.moved else (20, 160, 20)
            img = font.render('%d' % unit.HP, True, HPcolor)
            screen.blit(img, ((i + 1) * TileW - 28, (j +1) * TileW - 18))

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

    def getAttackRange(G, pos, LB, UB):
        # cost = lambda xx, yy: 1
        tovisit = Queue()
        tovisit.push((pos, 0))
        visited = set()
        poslist = []
        while not tovisit.isEmpty():
            curpos, curdis = tovisit.pop()
            visited.add(curpos)
            x, y = curpos
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                xx, yy = x + dx, y + dy
                if (xx, yy) in visited:
                    continue
                nextdis = curdis + 1
                if nextdis <= UB:
                    tovisit.push(((xx, yy), nextdis))
                    if nextdis >= LB:
                        poslist.append((xx, yy))
        return poslist

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

    def getTargetInRange(G, curUnit, attRange, unitList=None):
        if unitList is None: unitList = G.unitList
        targetPos = []
        targetUnit = []
        for unit in unitList:
            if unit.player is not curUnit.player and (attRange is None or unit.pos in attRange):
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
#%%
# gamestr = GameStateCtrl()
# actseq = []
# # game.GUI_loop()
# #%%
# game = gamestr
# for i in range(250):
#     moves, nextUIstate = game.getPossibleMoves()
#     move = choice(moves)
#     game.action_execute(*move, clone=False) # game =
#     actseq.append(move)
# print([unit.pos for unit in game.unitList])
# print([unit.player for unit in game.unitList])
# #%%
# game.GUI_loop()
#%%
def greedyPolicy(game):
    T0 = time()
    movseq_col = Stack()
    movseq_col.push(([], 0, game))
    whole_movseqs = PriorityQueue()  # [] #
    while not movseq_col.isEmpty():
        actseq, cumrew, curGame = movseq_col.pop()
        moves, nextUIstate = curGame.getPossibleMoves()
        for move in moves:  #
            next_actseq = copy(actseq)
            next_actseq.append(move)
            nextGame, nextrewards = curGame.action_execute(*move, clone=True, show=False, reward=True)
            nextcumrew = cumrew + nextrewards[curGame.curPlayer - 1] # use the reward for this player
            if move[0] is "attack" or move[0] is "stand":
                # whole_movseqs.append((next_actseq, nextGame, nextcumrew))
                # print("%d traj found" % len(whole_movseqs))
                whole_movseqs.push((next_actseq, nextGame, nextcumrew), -nextcumrew)
                # print("%d traj found" % len(whole_movseqs.heap))
                continue
            # move = choice(moves)
            movseq_col.push((next_actseq, nextcumrew, nextGame))
    best_seq, best_state, best_rew = whole_movseqs.pop()
    print("DFS finished %.2f sec, best rew %d" % (time() - T0, best_rew))
    return best_seq, best_state, best_rew

game = GameStateCtrl()
game.endTurn()
for i in range(20):
    best_seq, best_state, best_rew = greedyPolicy(game)
    _, cumrew = game.action_seq_execute(best_seq, show=True, reward=True)
game.GUI_loop()
#%% This demonstrates Two Greedy agents playing with each other. 
game = GameStateCtrl()
game.endTurn()
# This is the basic loop for playing an action sequence step by step
Exitflag = False
while not Exitflag:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            Exitflag = True
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_TAB:
                best_seq, best_state, best_rew = greedyPolicy(game)
                _, cumrew = game.action_seq_execute(best_seq, show=True, reward=True)
    game.drawBackground()
    game.drawUnitList()
    pg.display.update()

#%% DFS search engine
# def DFS, even a single round has > 3287649 possible action sequences as defined here.
game = GameStateCtrl()
game.endTurn()
T0 = time()
movseq_col = Stack()
movseq_col.push(([], 0, game))
whole_movseqs = PriorityQueue() # [] #
while not movseq_col.isEmpty():
    actseq, cumrew, curGame = movseq_col.pop()
    moves, nextUIstate = curGame.getPossibleMoves()
    # if len(movseq_col.list) > 500 or len(whole_movseqs) > 100:
    #     break
    #     print("%d traj found"%len(whole_movseqs))
    for move in moves: #
        next_actseq = copy(actseq)
        next_actseq.append(move)
        nextGame, nextrewards = curGame.action_execute(*move, clone=True, show=False, reward=True)
        nextcumrew = cumrew + nextrewards[curGame.curPlayer-1]
        if move[0] is "attack" or move[0] is "stand":
            # whole_movseqs.append((next_actseq, nextGame, nextcumrew))
            # print("%d traj found" % len(whole_movseqs))
            whole_movseqs.push((next_actseq, nextGame, nextcumrew), -nextcumrew)
            print("%d traj found" % len(whole_movseqs.heap))
            continue
        # move = choice(moves)
        movseq_col.push((next_actseq, nextcumrew, nextGame))
print("%.2f sec" % (time() - T0)) # selecting and moving one of the units has 192 different move seqs. Finished in .25sec
# print([unit.pos for unit in game.unitList])
# print([unit.player for unit in game.unitList])
#%%
# getSuccessor
# stepState = SELECT_UNIT
#
# if stepState is SELECT_UNIT:
#     selectable_pos, selectable_unit = getSelectableUnit(unitList, curPlayer)  # Possible moves
#     # Actuate Select
#     if len(selectable_pos) is 0:
#         nextState = END_TURN
#         curPlayer = next(playerIter)
#
# stepState = SELECT_MOVTARGET
# obst_pos = getObstacleInRange(curUnit, None, unitList)
# movRange = getMovRange(curUnit.pos, curUnit.Movepnt, obst_pos)
# # Actuate Move
#
# stepState = SELECT_ATTTARGET
# attRange = getAttackRange(curUnit.pos, curUnit.AttackRng[0], curUnit.AttackRng[1])
# targetPos, targetUnits = getTargetInRange(curUnit, attRange, unitList)