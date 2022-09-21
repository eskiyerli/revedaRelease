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
        w = Quantity(self._labelsDict['w'].labelValue)
        l = Quantity(self._labelsDict['l'].labelValue)
        nf= Quantity(self._labelsDict['nf'].labelValue)
        sd1p8v = 0.28
        sa1p8v = sb1p8v = 0.265
        sourceDiffs = lambda nf: int(int(nf) / 2 + 1)
