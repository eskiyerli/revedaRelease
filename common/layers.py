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