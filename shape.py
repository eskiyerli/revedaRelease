# shape class definition for symbol editor.
# base class for all shapes: rectangle, circle, line
from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtGui import (QPen, QFont,)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
)

import circuitElements as cel


class shape(QGraphicsItem):
    def __init__(self, pen:QPen) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        # self.setZValue(self.layer.z)
        self.gridSize = 10
        

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = value.toPoint()
            sceneRect = self.scene().sceneRect()
            viewRect = self.scene().views()[0].viewport().rect()
            newPos.setX(round(newPos.x() / self.gridSize) * self.gridSize)
            newPos.setY(round(newPos.y() / self.gridSize) * self.gridSize)
            if not sceneRect.contains(newPos):
                # Keep the item inside the scene rect.
                if newPos.x() > sceneRect.right():
                    sceneRect.setRight(newPos.x())
                    viewRect.setRight(newPos.x())
                elif newPos.x() < sceneRect.left():
                    sceneRect.setLeft(newPos.x())
                    viewRect.setLeft(newPos.x())
                if newPos.y() > sceneRect.bottom():
                    sceneRect.setBottom(newPos.y())
                    viewRect.setBottom(newPos.y())
                elif newPos.y() < sceneRect.top():
                    sceneRect.setTop(newPos.y())
                    viewRect.setTop(newPos.y())
            return newPos
        # # return QGraphicsItem.itemChange(self, change, value)
        return super().itemChange(change, value)

    def setSnapGrid(self, gridSize: int) -> None:
        self.gridSize = gridSize

    def snapGrid(self):
        return self.gridSize


class rectangle(shape):
    """

    rect: QRect defined by top left corner and bottom right corner. QRect(Point1,Point2)
    """

    def __init__(
        self,
        start: QPoint,
        end: QPoint,
        pen: QPen,
    ):
        super().__init__(pen)
        self.rect = QRect(start, end)
        self.pen = pen

    def boundingRect(self):
        return self.rect  #

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.drawRect(self.rect)

    def centre(self):
        return QPoint(
            int(self.rect.x() + self.rect.width() / 2),
            int(self.rect.y() + self.rect.height() / 2),
        )

    def height(self):
        return self.rect.height()

    def width(self):
        return self.rect.width()

    def objName(self):
        return "RECTANGLE"

    def objType(self):
        return "RECTANGLE"

    def left(self):
        return self.rect.left()

    def right(self):
        return self.rect.right()

    def top(self):
        return self.rect.top()

    def bottom(self):
        return self.rect.bottom()

    def setLeft(self, left: int):
        self.rect.setLeft(left)

    def setRight(self, right: int):
        self.rect.setRight(right)

    def setTop(self, top: int):
        self.rect.setTop(top)

    def setBottom(self, bottom: int):
        self.rect.setBottom(bottom)

    def origin(self):
        return self.rect.bottomLeft()

    def bBox(self):
        return self.rect


class line(shape):
    """
    line class definition for symbol drawing.
    """

    def __init__(
        self,
        start: QPoint,
        current: QPoint,
        pen: QPen,
    ):
        super().__init__(pen=pen)
        self.current = current
        self.start = start
        self.pen = pen
        self.points = 2

    def boundingRect(self):
        return QRect(self.start.x(), self.start.y(), self.current.x(), self.current.y())

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        if self.start.x() != self.current.x():
            if self.start.y() != self.current.y():
                midPoint = QPoint(self.current.x(), self.start.y())
                painter.drawLine(self.start, midPoint)
                painter.drawLine(midPoint, self.current)
                self.points = 3
            else:
                painter.drawLine(self.start, self.current)
        else:
            if self.start.y() != self.current.y():
                painter.drawLine(self.start, self.current)
            else:
                painter.drawPoint(self.start)

    def pos(self):
        return self.start

    def objName(self):
        return "LINE"

    def objType(self):
        return "LINE"

    def nPoints(self):
        return self.points

    def setWidth(self, width: int):
        self.pen.setWidth(width)

    def bBox(self) -> QRect:
        return self.boundingRect()


class pin(shape):
    """
    pin class definition for symbol drawing.
    """

    def __init__(
        self,
        centre: QPoint,
        pen: QPen,
        pinName: str = "",
    ):
        super().__init__(pen)
        self.centre = centre
        self.pinName = pinName
        self.rect = QRect(self.centre.x() - 5, self.centre.y() - 5, 10, 10)
        self.pen = pen
        self.pinDirections = ['INPUT', 'OUTPUT', 'INOUT']
        self.pinDir = self.pinDirections[2] # default to INOUT
        self.pinUses = ['SIGNAL', 'POWER', 'GROUND', 'CLOCK', 'TRISTATE']

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.setBrush(self.pen.color())
        painter.drawRect(self.rect)
        painter.setFont(QFont("Arial", 10))
        textLoc = QPoint(self.pos.x() - 2.5, self.pos.y() - 10)
        painter.drawText(textLoc, self.pinName)

    def name(self):
        return self.pinName

    def setName(self,name):
        self.pinName = name

    def setDir(self,direction: str):
        if direction in self.pinDirections:
            self.pinDir = direction

    def getDir(self):
        return self.pinDir

    def setUse(self,use: str):
        if use in self.pinUses:
            self.pinUse = use

