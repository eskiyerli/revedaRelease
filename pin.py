# pin class definition
# (C) 2021 Revolution Semiconductor
import net


class pin:
    def __init__(self, name, dir, use, net: net, ports: list):
        self.name = name
        self.dir = dir
        self.use = use
        self.net = net
        self.ports = ports
        self.dirs = [
            "DB_PIN_INPUT",
            "DB_PIN_OUTPUT",
            "DB_PIN_INOUT",
            "DB_PIN_FEEDTHRU",
            "DB_PIN_TRISTATE",
        ]
        self.uses = [
            "DB_PIN_SIGNAL",
            "DB_PIN_ANALOG",
            "DB_PIN_CLOCK",
            "DB_PIN_GROUND",
            "DB_PIN_POWER",
            "DB_PIN_RESET",
            "DB_PIN_SCAN",
            "DB_PIN_TIEOFF",
        ]

    def __str__(self):
        return (
            self.name
            + " "
            + self.dir
            + " "
            + self.use
            + " "
            + self.net.cellName
            + " "
            + str(self.ports)
        )

    def __repr__(self):
        return (
            self.name
            + " "
            + self.dir
            + " "
            + self.use
            + " "
            + self.net.cellName
            + " "
            + str(self.ports)
        )

    def name(self, *args):
        if len(args) == 0:
            return self.name
        elif len(args) == 1:
            self.name = args[0]
        else:
            raise Exception("Invalid number of arguments")

    def setDir(self, dir):
        if dir in self.dirs:
            self.dir = dir
        else:
            raise Exception("Invalid direction")

    def getDir(self):
        return self.dir

    def setUse(self, use):
        if use in self.uses:
            self.use = use
        else:
            raise Exception("Invalid use")

    def getUse(self):
        return self.use

    def setNet(self, net): # net is a net object
        self.net = net

    def getNet(self): # net is a net object
        return self.net

    def getNetName(self):
        return self.net.cellName # net is a net object

    def dbObjType(self):
        return "PIN"

    def setPorts(self, ports):
        self.ports = ports    
    
    def getPorts(self):
        return self.ports

    def getNumPorts(self):
        return len(self.ports)

    def addPort(self, port):
        self.ports.append(port)

    def deletePort(self, port):
        self.ports.remove(port)
        




