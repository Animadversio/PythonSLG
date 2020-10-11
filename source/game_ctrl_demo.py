import pygame as pg
import source.constants as c
pg.display.set_caption("SLG board")
SCREEN = pg.display.set_mode((800,500)) # get screen
pg.font.init()
font = pg.font.SysFont("microsoftsansserif", 16)
print('system font :', font)

screen = pg.display.get_surface() # the screen used in subsequent things

c.MAP_WIDTH = 800
c.MAP_HEIGHT = 500
image = pg.Surface([50, 50])
rect = image.get_rect()
x, y = 100,200
image.blit(SCREEN, (0, 0), (x, y, 50, 50))
image.set_colorkey((  100,   0,   0))
# image = pg.transform.scale(image,
#                            (int(rect.width*scale),
#                             int(rect.height*scale)))
#%% Functions to draw a basic map
TileW = 50
Margin = 2
def drawBackground(screen):
    pg.draw.rect(screen, c.LIGHTYELLOW, pg.Rect(0, 0, c.MAP_WIDTH, c.MAP_HEIGHT), 0)
    for i in range(c.MAP_WIDTH // TileW):
        for j in range(c.MAP_HEIGHT // TileW):
            pg.draw.rect(screen, (  200, 200, 200), pg.Rect(i*TileW+Margin, j*TileW+Margin, TileW-2*Margin, TileW-2*Margin))

def drawLocation(screen, pos_list, color=(150, 200, 200)):
    for i, j in pos_list:
        pg.draw.rect(screen, color,
             pg.Rect(i * TileW + Margin, j * TileW + Margin, TileW - 2*Margin, TileW - 2*Margin))

CsrWidth = 5
def drawCsrLocation(screen, pos_list, color=(150, 200, 200), CsrWidth = CsrWidth):
    """Just an empty square indicating the position of cursor"""
    for i, j in pos_list:
        pg.draw.rect(screen, color,
             pg.Rect(i * TileW + Margin + CsrWidth/2, j * TileW + Margin + CsrWidth/2, TileW - 2*Margin - CsrWidth, TileW - 2*Margin - CsrWidth), CsrWidth)

UMargin = 20
def drawUnits(screen, pos_list, color=(20, 20, 20)):
    for i, j in pos_list:
        pg.draw.rect(screen, color,
             pg.Rect(i * TileW + UMargin/2, j * TileW + UMargin/2, TileW - UMargin, TileW - UMargin))
# Really draw unit lists!
font = pg.font.SysFont("microsoftsansserif", 16, bold=True)
playerColor = {1: (20, 20, 20), 2: (120, 20, 20)}
def drawUnitList(screen, UnitList, ):
    """Represent different types of units with shapes"""
    for unit in UnitList:
        if not unit.alive: continue
        i, j = unit.pos
        if unit.Type is "Soldier":
            pg.draw.rect(screen, playerColor[unit.player],
             pg.Rect(i * TileW + UMargin/2, j * TileW + UMargin/2, TileW - UMargin, TileW - UMargin))
        elif unit.Type is "Archer":
            pg.draw.circle(screen, playerColor[unit.player], (int((i+1/2) * TileW), int((j+1/2) * TileW)),
                           (TileW - UMargin) // 2 )
        elif unit.Type is "Catapult":
            pg.draw.polygon(screen, playerColor[unit.player], [(int((i  ) * TileW), int((j + 1 / 2) * TileW)),
                                                                (int((i + 1 / 2) * TileW), int((j + 1) * TileW)),
                                                                (int((i + 1) * TileW), int((j + 1 / 2) * TileW)),
                                                                (int((i + 1 / 2) * TileW), int((j) * TileW)),] )
        elif unit.Type is "Knight":
            pg.draw.polygon(screen, playerColor[unit.player], [(int((i  ) * TileW), int((j ) * TileW)),
                                                                (int((i + 1 ) * TileW), int((j ) * TileW)),
                                                                (int((i + 1 / 2) * TileW), int((j + 1) * TileW)), ] )
        HPcolor = (160, 20, 20) if unit.moved else (20, 160, 20)
        img = font.render('%d' % unit.HP, True, HPcolor)
        screen.blit(img, ((i + 1) * TileW - 28, (j +1) * TileW - 18))
#%
from source.util import Queue
def getMovRange(pos, movpnt, obstacles=[]):
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

def getAttackRange(pos, LB, UB):
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

def getSelectableUnit(unitList, curPlayer):
    selectablePos = []
    selectableUnit = []
    for unit in unitList:
        if unit.player == curPlayer and not unit.moved:
            selectablePos.append(unit.pos)
            selectableUnit.append(unit)
    return selectablePos, selectableUnit


def getTargetInRange(curUnit, attRange, unitList):
    targetPos = []
    targetUnit = []
    for unit in unitList:
        if unit.player is not curUnit.player and (attRange is None or unit.pos in attRange):
            targetPos.append(unit.pos)
            targetUnit.append(unit)
    return targetPos, targetUnit

def getObstacleInRange(curUnit, movRange, unitList):
    targetPos = []
    # targetUnit = []
    for unit in unitList:
        if unit.player is not curUnit.player and (movRange is None or unit.pos in movRange):
            targetPos.append(unit.pos)
            #targetUnit.append(unit)
    return targetPos# , targetUnit

movRange = getMovRange((5, 5), 4)
# clock = pg.time.Clock()
# pg.time.get_ticks()
pg.display.flip()
#%%
class Unit:
    def __init__(self, player, pos, cfg=None):
        self.player = player
        self.pos = pos
        self.alive = True
        self.moved = True
        self.Buff = []
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
HEAVYMACHINE = 6
SoldierCfg = {"Type": "Soldier", "HP": 100, "Attack": 55, "Defence": 10, "Movepnt": 4, "AttackRng": (1, 1), "Ability": [], "ExtraAct": [],}
ArcherCfg = {"Type": "Archer", "HP": 100, "Attack": 45, "Defence":  5, "Movepnt": 4, "AttackRng": (2, 2), "Ability": [], "ExtraAct": [],}
KnightCfg = {"Type": "Knight", "HP": 100, "Attack": 60, "Defence":  15, "Movepnt": 6, "AttackRng": (1, 1), "Ability": [], "ExtraAct": [],}
CatapultCfg = {"Type": "Catapult", "HP": 100, "Attack": 70, "Defence":  5, "Movepnt": 3, "AttackRng": (2, 7), "Ability": [HEAVYMACHINE, ], "ExtraAct": [],}
#%% Demo of Game Loop with Turn Change (Interface to Human)
END_TURN = 0
SELECT_UNIT = 1
SELECT_ACTION = 2
SELECT_MOVTARGET = 3
SELECT_ATTTARGET = 4

# Utility to detect DoubleClick
dbclock = pg.time.Clock()
DOUBLECLICKTIME = 250
#
UIstate = SELECT_UNIT  # SELECT_UNIT
Exitflag = False
playerList = [1, 2]
def playerIterator(playerList):
    turn = 0
    while True:
        turn += 1
        for player in playerList: # and player is alive
            yield player, turn
playerIter = playerIterator(playerList)
curPlayer, curTurn = next(playerIter) # 1, 1
# Initialize Units
unitList = []
unitList.append(Unit(player=1, pos=(2, 2), cfg=SoldierCfg))
unitList.append(Unit(player=1, pos=(3, 2), cfg=SoldierCfg))
unitList.append(Unit(player=1, pos=(2, 3), cfg=ArcherCfg))
unitList.append(Unit(player=1, pos=(3, 4), cfg=KnightCfg))
unitList.append(Unit(player=1, pos=(1, 1), cfg=CatapultCfg))
unitList.append(Unit(player=2, pos=(5, 8), cfg=SoldierCfg))
unitList.append(Unit(player=2, pos=(6, 8), cfg=SoldierCfg))
unitList.append(Unit(player=2, pos=(7, 5), cfg=ArcherCfg))
unitList.append(Unit(player=2, pos=(5, 5), cfg=KnightCfg))
unitList.append(Unit(player=2, pos=(8, 8), cfg=CatapultCfg))

unit_pos = [unit.pos for unit in unitList]
curUnit = None
ci, cj = (5, 5)
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
    drawBackground(screen)
    # drawTerrain(screen, gameState)
    if K_Turnover:
        nextPlayer, nextTurn = next(playerIter)# playerList[playerList.index(curPlayer)+1]
        # Do sth at turn over
        for unit in unitList:
            if unit.player is nextPlayer: unit.moved = False
            if unit.player is curPlayer: unit.moved = True
        curPlayer, curTurn = nextPlayer, nextTurn
        UIstate = SELECT_UNIT
        # drawTurnover(screen)

    if UIstate == SELECT_UNIT:
        posDict = {unit.pos: unit for unit in unitList}
        selectable_pos, selectable_unit = getSelectableUnit(unitList, curPlayer)  # add condition for selectable
        # unit_pos = [unit.pos for unit in unitList
        #             if unit.player == curPlayer and not unit.moved]  # add condition for selectable
        if K_confirm and (ci, cj) in selectable_pos:
            print("Unit selected (%d, %d)"%(ci, cj))
            # unitId = unit_pos.index((ci, cj))
            curUnit = posDict[(ci, cj)] # unitList[unitId]
            UIstate = SELECT_MOVTARGET

    elif UIstate == SELECT_MOVTARGET:
        obst_pos = getObstacleInRange(curUnit, None, unitList)
        movRange = getMovRange(curUnit.pos, curUnit.Movepnt, obst_pos)
        drawLocation(screen, movRange, (160, 180, 180))  # draw a list of location in one color
        if K_confirm and (ci, cj) in movRange:
            print("Unit move (%d, %d) -> (%d, %d)"%(*curUnit.pos, ci, cj))
            # move(unit, mov2i, mov2j)
            ui_orig, uj_orig = curUnit.pos  # record this just in case user cancels
            curUnit.pos = ci, cj  # ui, uj
            # if it can attack
            UIstate = SELECT_ATTTARGET
            # UIstate = SELECT_ACTION
        if K_cancel:
            UIstate = SELECT_UNIT

    elif UIstate == SELECT_ATTTARGET:
        attRange = getAttackRange(curUnit.pos, curUnit.AttackRng[0], curUnit.AttackRng[1])
        targetPos, targetUnits = getTargetInRange(curUnit, attRange, unitList)
        drawLocation(screen, attRange, (220, 180, 180))  # draw a list of location in one color
        drawCsrLocation(screen, targetPos, (250, 130, 130))
        if K_confirm:
            if (ci, cj) in targetPos:  # confirmed attack
                print("Unit @ (%d, %d) attack (%d, %d)" % (*curUnit.pos, ci, cj))
                attacked = targetUnits[targetPos.index((ci, cj))]
                # Real computation code for attack
                harm = int(curUnit.Attack / 100.0 * curUnit.HP) - attacked.Defence
                attacked.HP -= abs(harm)
                attDis = abs(ci - curUnit.pos[0]) + abs(cj - curUnit.pos[1])
                counterattack = attacked.AttackRng[0] <= attDis <= attacked.AttackRng[1]  # and bla bla bla
                if counterattack:
                    harm2 = int(attacked.Attack / 100.0 * attacked.HP) - curUnit.Defence
                    curUnit.HP -= abs(harm2)
                # TODO: Currently Attacker and Attacked could Die together!
                if curUnit.HP <= 0:
                    unitList.pop(unitList.index(curUnit))
                if attacked.HP <= 0:
                    unitList.pop(unitList.index(attacked))
            if len(targetPos) == 0:
                print("No target. Unit @ (%d, %d) stand by" % (*curUnit.pos,))
            curUnit.moved = True
            curUnit = None
            UIstate = SELECT_UNIT
            # UIstate = SELECT_REMOVTARGET
        if K_cancel:
            curUnit.pos = ui_orig, uj_orig
            UIstate = SELECT_MOVTARGET
    # drawUnits(screen, [(ui, uj)])  # gameState
    drawUnitList(screen, unitList)
    drawCsrLocation(screen, [(ci, cj)])  # draw a list of location in one color
    pg.display.update()
 #%%

# Actuate Attack
#%% OBSOLETE
#%% Demo of controling an discrete cursor
flag = True
pos = (5,5)
ii, jj = pos
while flag:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            flag = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP: jj -= 1
            if event.key == pg.K_DOWN: jj += 1
            if event.key == pg.K_LEFT: ii -= 1
            if event.key == pg.K_RIGHT: ii += 1
    movRange = getMovRange((ii, jj), 3)
    attRange = getAttackRange((ii, jj), 5, 6)

    drawBackground(screen)
    # drawTerrain(screen, gameState)
    # drawUnits(screen, gameState)
    drawLocation(screen, movRange, (160, 180, 180)) # draw a list of location in one color
    drawLocation(screen, attRange, (220, 180, 180)) # draw a list of location in one color
    drawCsrLocation(screen, [(ii, jj)]) # draw a list of location in one color
    pg.display.update()

#%% Basic Game Loop!
# UI state
END_TURN = 0
SELECT_UNIT = 1
SELECT_MENU = 2
SELECT_MOVTARGET = 3
SELECT_ATTTARGET = 4

UIstate = SELECT_MOVTARGET#SELECT_UNIT
flag = True
pos = (5, 5)
ci, cj = pos
ui, uj = 7, 7
while flag:
    K_confirm = False
    for event in pg.event.get():
        if event.type == pg.QUIT:
            flag = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP: cj -= 1
            if event.key == pg.K_DOWN: cj += 1
            if event.key == pg.K_LEFT: ci -= 1
            if event.key == pg.K_RIGHT: ci += 1
            if event.key == pg.K_SPACE: K_confirm = True
    drawBackground(screen)
    # drawTerrain(screen, gameState)
    if UIstate == SELECT_UNIT:
        if K_confirm and ci == ui and cj == uj:
            print("Unit selected (%d, %d)"%(ui, uj))
            UIstate = SELECT_MOVTARGET

    elif UIstate == SELECT_MOVTARGET:
        movRange = getMovRange((ui, uj), 4)
        drawLocation(screen, movRange, (160, 180, 180))  # draw a list of location in one color
        if K_confirm and (ci, cj) in movRange:
            print("Unit move (%d, %d) -> (%d, %d)"%(ui, uj, ci, cj))
            # move(unit, mov2i, mov2j)
            ui, uj = ci, cj
            # if it can attack
            UIstate = SELECT_ATTTARGET

    elif UIstate == SELECT_ATTTARGET:
        attRange = getAttackRange((ui, uj), 2, 2)
        drawLocation(screen, attRange, (220, 180, 180))  # draw a list of location in one color
        # posTarget = getPosTarget(unit, attRange, )
        # drawLocation(screen, posTarget, (150, 100, 100))  # draw a list of location in one color
        if K_confirm and (ci, cj) in attRange:
            print("Unit @ (%d, %d) attack (%d, %d)"%(ui, uj, ci, cj))
            UIstate = SELECT_UNIT

    drawUnits(screen, [(ui, uj)])  # gameState
    drawCsrLocation(screen, [(ci, cj)])  # draw a list of location in one color
    pg.display.update()