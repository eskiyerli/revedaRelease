# net class definition.


class net:
    def __init__(self, name: str, pins:list, instPins:list, cellview: str):
        self.name = name
        self.pins = pins
        self.instPins = instPins
        self.cellview = cellview
        self.uses = [
            "DB_SIGNAL",
            "DB_ANALOG",
            "DB_CLOCK",
            "DB_GROUND",
            "DB_POWER",
            "DB_RESET",
            "DB_SCAN",
            "DB_TIEOFF",
            "DB_TIEHI",
            "DB_TIELO",
        ]
        self.use = "DB_SIGNAL"  # default use
        self.sources = ['DB_DIST', 'DB_NETLIST', 'DB_TEST', 'DB_TIMING', 'DB_USER',]
        self.source = 'DB_DIST'  # default source
        self.global_ = False  # default not global
        self.special = False  # default not special


    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def cellview(self):
        return self.cellview

    def pins(self):
        return self.pins

    def instPins(self):
        return self.instPins

    def name(self, *args):
        if len(args) == 0:
            return self.name
        elif len(args) == 1:
            self.name = args[0]
        else:
            raise ValueError("Invalid number of arguments")

    def objType(self):
        return "NET"

    def objName(self):
        return "NET"

    def cellView(self):
        return self.cellview

    def setUse(self, use):
        if use in self.uses:
            self.use = use
        else:
            raise ValueError("Invalid use")

    def use(self): # returns use number of net
        return self.uses.index(self.use)

    def getUseStr(self):
        return self.use

    def setSource(self,source):
        if source in self.sources:
            self.source = source
        else:
            raise ValueError("Invalid source")

    def source(self): # returns source number of net
        return self.sources.index(self.source)
    
    def getSourceStr(self):
        return self.source

    def setGlobal(self, global_):
        self.global_ = True

    def isGlobal(self):
        return self.global_

    def setSpecial(self, special):
        self.special = True

    def isSpecial(self):
        return self.special

    def setPins(self, pins):
        self.pins = pins


