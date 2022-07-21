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
