
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

# Schematic and symbol editor classes
# (C) Revolution Semiconductor, 2021
from PySide6.QtGui import (QColor)


class layer:
    def __init__(self, name, color, z, visible):
        self.name = name
        self.color = color  # QColor type
        self.z = z
        self.visible = visible

    def __str__(self):
        return f'{self.name}  {str(self.color.toTuple())} {str(self.z)} {str(self.visible)}'

    def __repr__(self):
        return f'{self.name}  {str(self.color.toTuple())} {str(self.z)} {str(self.visible)}'

    def __eq__(self, other):
        return (self.name == other.cellName and self.color == other.color and self.z ==
                other.z and self.visible == other.visible)

    def __ne__(self, other):
        return not self.__eq__(other)

    def layerDelete(self):
        del self


wireLayer = layer(name="wireLayer", color=QColor("cyan"), z=1, visible=True)
symbolLayer = layer(name="symbolLayer", color=QColor("green"), z=1, visible=True)
guideLineLayer = layer(name="guideLineLayer", color=QColor("white"), z=1, visible=True)
selectedWireLayer = layer(name="selectedWireLayer", color=QColor("red"), z=1,
                          visible=True)
pinLayer = layer(name="pinLayer", color=QColor("red"), z=2, visible=True)
labelLayer = layer(name="labelLayer", color=QColor("yellow"), z=3, visible=True)
textLayer = layer(name="textLayer", color=QColor("white"), z=4, visible=True)
otherLayer = layer(name='otherLayer', color=QColor('white'), z=1, visible= True)
draftLayer = layer(name='draftLayer', color = QColor('gray'), z=1, visible= True)