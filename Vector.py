# vector class
# (C) Revolution Semiconductor, 2021
# All rights reserved
import math
from PySide6.QtGui import QVector2D as QVec2

class Vector(QVec2):
    def __init__(self, *args):
        if len(args) == 4:
            self.x = args[2] - args[0]
            self.y = args[3] - args[1]
        elif len(args) == 2:
            self.x = args[0]
            self.y = args[1]  
        elif len(args) == 0:
            self.x = 0
            self.y = 0
        else:
            raise ValueError("Vector: wrong number of arguments")
        if hasattr(self,'x') and hasattr(self,'y'): # check if dx and dy are defined
            super().__init__(self.x,self.y)
        
    def normal(self):
        return Vector(self.x, self.y).normalized()


        

 

