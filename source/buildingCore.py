#%% Buildings
from copy import deepcopy
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