from quantiphy import Quantity

class baseInst():
    def __init__(self, dict: dict):
        self._labelsDict = dict

class res(baseInst):
    def __init__(self,dict:dict):
        super().__init__(dict)

    def doubleR(self):
        Rvalue = self._labelsDict.get('R').labelValue
        if Rvalue.isalnum():
            return str(2*Quantity(Rvalue))
        else:
            return '?'

class nmos(baseInst):
    def __init__(self,dict:dict):
        super().__init__(dict)
        self.w = Quantity(self._labelsDict['w'].labelValue)
        self.l = Quantity(self._labelsDict['l'].labelValue)
        self.nf= Quantity(self._labelsDict['nf'].labelValue)
        self.sd1p8v = 0.28
        self.sa1p8v = sb1p8v = 0.265
        self.sourceDiffs = lambda nf: int(int(nf) / 2 + 1)

    def asparm(self):
        return self.sourceDiffs(self.nf)*(self.w/self.nf)*self.sd1p8v
