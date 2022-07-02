# Schematic and symbol editor classes
# (C) Revolution Semiconductor, 2021

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
        return self.name == other.cellName and self.color == other.color and self.z == other.z and self.visible == other.visible

    def __ne__(self, other):
        return not self.__eq__(other)

    def layerDelete(self):
        del self
