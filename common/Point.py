
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

# point object
from PySide6.QtCore import Qt, QPoint

class Point:
    def __init__(self, x, y) -> QPoint:
        self.x = x
        self.y = y

        self= QPoint(x, y)

    def __str__(self) -> str:
        return f"({self.x},{self.y})"

    def __repr__(self) -> str:
        return f"point({self.x},{self.y})"

    def getX(self) -> int:
        return self.x

    def getY(self) -> int:
        return self.y

    def setX(self, x) -> None:
        self.x = x

    def setY(self, y) -> None:
        self.y = y

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Point):
            return self.x == o.x and self.y == o.y
        return False

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __gt__(self, o: object) -> bool:
        if isinstance(o, Point):
            return self.x > o.x and self.y > o.y
        return False

    def __lt__(self, o: object) -> bool:
        if isinstance(o, Point):
            return self.x < o.x and self.y < o.y
        return False
