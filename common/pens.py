from PySide6.QtCore import (Qt)
from PySide6.QtGui import (QPen, QColor)
class pen(QPen):
    def __init__(self,pname:str,pcolor:QColor, pwidth:int,
                 plinestyle:Qt.PenStyle=Qt.SolidLine):
        super().__init__()
        self.pname = pname
        self.pcolor = pcolor
        self.width = pwidth
        self.plinestyle = plinestyle
        self.setWidth(pwidth)
        self.setColor(pcolor)
        self.setStyle(plinestyle)