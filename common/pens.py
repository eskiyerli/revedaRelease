
#   “Commons Clause” License Condition v1.0
#  #
#   The Software is provided to you by the Licensor under the License, as defined
#   below, subject to the following condition.
#  #
#   Without limiting other conditions in the License, the grant of rights under the
#   License will not include, and the License does not grant to you, the right to
#   Sell the Software.
#  #
#   For purposes of the foregoing, “Sell” means practicing any or all of the rights
#   granted to you under the License to provide to third parties, for a fee or other
#   consideration (including without limitation fees for hosting or consulting/
#   support services related to the Software), a product or service whose value
#   derives, entirely or substantially, from the functionality of the Software. Any
#   license notice or attribution required by the License must also include this
#   Commons Clause License Condition notice.
#  #
#   Software: Revolution EDA
#   License: Mozilla Public License 2.0
#   Licensor: Revolution Semiconductor (Registered in the Netherlands)

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
