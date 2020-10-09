import pygame as pg
import source.constants as c
pg.display.set_caption("SLG board")
SCREEN = pg.display.set_mode((800,500)) # get screen
pg.display.update()

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
#%
from source.util import Queue
def getMovRange(pos, movpnt):
    cost = lambda xx, yy: 1
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
    cost = lambda xx, yy: 1
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

movRange = getMovRange((5, 5), 4)
clock = pg.time.Clock()
pg.time.get_ticks()
pg.display.flip()

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
IDLE = 0
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
        movRange = getMovRange((ui, uj), 3)
        drawLocation(screen, movRange, (160, 180, 180))  # draw a list of location in one color
        if K_confirm:
            mov2i, mov2j = ci, cj
            if (ci, cj) in movRange:
                print("Unit move (%d, %d) -> (%d, %d)"%(ui, uj, ci, cj))
                # move(unit, mov2i, mov2j)
                ui, uj = mov2i, mov2j
                UIstate = SELECT_ATTTARGET

    elif UIstate == SELECT_ATTTARGET:
        attRange = getAttackRange((ui, uj), 5, 6)
        drawLocation(screen, attRange, (220, 180, 180))  # draw a list of location in one color
        if K_confirm:
            if (ci, cj) in attRange:
                print("Unit @ (%d, %d) attack (%d, %d)"%(ui, uj, ci, cj))
                UIstate = SELECT_UNIT
    drawUnits(screen, [(ui, uj)])  # gameState
    drawCsrLocation(screen, [(ci, cj)])  # draw a list of location in one color
    pg.display.update()

