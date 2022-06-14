# pin class definition
# (C) 2021 Revolution Semiconductor
import net
import shape as shp
from PySide6.QtCore import (
    QPoint,
)

class pin(shp.pin):
    def __init__(self, loc: QPoint,
                 pen: shp.pen, name: str = None):
        super().__init__(start, end, pen, name)
        self.type = "pin"
        




