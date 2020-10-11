import pygame as pg
from source.util import Queue
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
playerColor = {1: (20, 20, 20), 2: (120, 20, 20)}

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

#%%
def playerIterator(playerList):
    turn = 0
    while True:
        turn += 1
        for player in playerList: # and player is alive
            yield player, turn

END_TURN = 0
SELECT_UNIT = 1
SELECT_ACTION = 2
SELECT_MOVTARGET = 3
SELECT_ATTTARGET = 4
class GameStateCtrl:
    def __init__(G):
        G.curPlayer = 2
        G.playerList = [1, 2]
        G.playerIter = playerIterator(G.playerList)
        G.curTurn = 0
        G.screen = screen
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

    def GUI_loop(G, GUI=True, csr_pos=(5, 6)):
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
                nextPlayer, nextTurn = next(G.playerIter)# playerList[playerList.index(curPlayer)+1]
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
                obst_pos = G.getObstacleInRange(G.curUnit, None, )
                movRange = G.getMovRange(G.curUnit.pos, G.curUnit.Movepnt, obst_pos)
                G.drawLocation(movRange, (160, 180, 180))  # draw a list of location in one color
                if K_confirm and (ci, cj) in movRange:
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
                        attDis = abs(ci - G.curUnit.pos[0]) + abs(cj - G.curUnit.pos[1])
                        counterattack = attacked.AttackRng[0] <= attDis <= attacked.AttackRng[1]  # and bla bla bla
                        if counterattack:
                            harm2 = int(attacked.Attack / 100.0 * attacked.HP) - G.curUnit.Defence
                            G.curUnit.HP -= abs(harm2)
                        # TODO: Currently Attacker and Attacked could Die together!
                        if G.curUnit.HP <= 0:
                            G.unitList.pop(G.unitList.index(G.curUnit))
                        if attacked.HP <= 0:
                            G.unitList.pop(G.unitList.index(attacked))
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
                if nextmvp >= 0:
                    tovisit.push(((xx, yy), nextmvp))
        return list(visited)

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
game = GameStateCtrl()
game.GUI_loop()





#%%
# getSuccessor
stepState = SELECT_UNIT

if stepState is SELECT_UNIT:
    selectable_pos, selectable_unit = getSelectableUnit(unitList, curPlayer)  # Possible moves
    # Actuate Select
    if len(selectable_pos) is 0:
        nextState = END_TURN
        curPlayer = next(playerIter)

stepState = SELECT_MOVTARGET
obst_pos = getObstacleInRange(curUnit, None, unitList)
movRange = getMovRange(curUnit.pos, curUnit.Movepnt, obst_pos)
# Actuate Move

stepState = SELECT_ATTTARGET
attRange = getAttackRange(curUnit.pos, curUnit.AttackRng[0], curUnit.AttackRng[1])
targetPos, targetUnits = getTargetInRange(curUnit, attRange, unitList)