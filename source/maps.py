
class Map:
    def __init__(self):
        self.height
        self.width
        self.data = 

    def load(self): 

class Tile:
    def __init__(self):
        self.moveCost
        self.isDestroyable
        self.isHealing
        self.isProductible
        self.isCastle
        self.isTown
        self.isWater
    

class GameState:
    def __init__(self):
        self.map
        self.playerlist = [1, 2]
        self.playerLeft = [1, 2]
        self.unitlist = []
        pass

    def getMovableUnit(self, player):
        return [unit for unit in self.unitlist if unit.player==player 
                                                and not self.moved]

    def getMovableRange(self, unit): 
        """ UCS on the terrain cost """
        CostArr_mod = modifyMovCost(CostArr, ability)
        Obstacles = self.getUnpassable(player) # units that are not passable....
        pos_list, path_list = UCS_solve(unit.pos, CostArr_mod, unit.MovPnt)
        return pos_list, path_list

    def getAttackableRange(self, unit):
        pos_list, _ = self.getMovableRange(unit)
        attackRange = set()
        for pos in pos_list:
            attackRange.update(self.getAttackRangePos(self, pos, LB, UB))
        return attackRange

    def getAttackRangePos(self, pos, LB, UB):



    def getPath2Pos(self, unit, pos):


class Unit:
    def __init__(self):
        self.player
        self.alive
        self.moved
        self.pos
        # self.exp
        # self.level
        self.HP
        self.Attack
        self.Defence
        self.Movepnt
        self.Ability = []
        self.Buff = []

    def attack(self, target):
        pass

    def move(self, ):
        pass

    def heal(self, ): 

    
