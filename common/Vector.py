
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


        

 

