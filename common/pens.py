from PySide6.QtCore import (Qt)
from PySide6.QtGui import (QPen, QColor)
from common.layers import (wireLayer,symbolLayer,selectedWireLayer,pinLayer,labelLayer,
                           textLayer, draftLayer)


class pen(QPen):
    def __init__(self,pname:str,pcolor:QColor, pwidth:int,
                 plinestyle:Qt.PenStyle=Qt.SolidLine):
        super().__init__()
        self._pname = pname
        self._pcolor = pcolor
        self._pwidth = pwidth
        self._plinestyle = plinestyle
        self.setWidth(self._pwidth)
        self.setColor(self._pcolor)
        self.setStyle(self._plinestyle)

    @property
    def pname(self):
        return self._pname
    @classmethod
    def returnPen(cls,penName):
        match penName:
            case 'wirePen':
                rpen = cls('wirePen',wireLayer.color,2)
                rpen.setCosmetic(True)
            case 'symbolPen':
                rpen = cls("symbolPen",symbolLayer.color, 3)
                rpen.setCosmetic(True)
            case 'selectedWirePen':
                rpen = cls("selectedWirePen",selectedWireLayer.color, 2)
            case 'pinPen':
                rpen = cls('pinPen', pinLayer.color, 2)
            case 'labelPen':
                rpen = cls('labelPen',labelLayer.color, 1)
            case 'textPen':
                rpen = cls('textPen',textLayer.color, 1)
            case 'draftPen':
                rpen = cls('draftPen',draftLayer.color, 1, Qt.DashLine)
            case other:
                rpen = cls('otherPen', QColor('darkGray'), 1, Qt.DotLine )
        return rpen
