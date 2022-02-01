# shape class definition for symbol editor.
# base class for all shapes: rectangle, circle, line
from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtGui import (
    QPen,
    QFont,
    QFontMetrics,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
)

import circuitElements as cel


class shape(QGraphicsItem):
    def __init__(self, pen: QPen, grid: tuple) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        # self.setZValue(self.layer.z)
        self.gridX = grid[0]
        self.gridY = grid[1]

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = value.toPoint()
            sceneRect = self.scene().sceneRect()
            viewRect = self.scene().views()[0].viewport().rect()
            newPos.setX(round(newPos.x() / self.gridX) * self.gridX)
            newPos.setY(round(newPos.y() / self.gridY) * self.gridY)
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

    def hoverEnterEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setCursor(Qt.ArrowCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneMouseEvent) -> None: 
        self.setCursor(Qt.CrossCursor)
        super().hoverLeaveEvent(event)    

class rectangle(shape):
    """
    rect: QRect defined by top left corner and bottom right corner. QRect(Point1,Point2)
    """

    def __init__(
        self,
        start: QPoint,
        end: QPoint,
        pen: QPen,
        grid: tuple,
    ):
        super().__init__(pen, grid)
        self.start = start # top left corner
        self.end = end   # bottom right corner
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
        end: QPoint,
        pen: QPen,
        grid: tuple,
    ):
        super().__init__(pen, grid)
        self.end = end
        self.start = start
        self.pen = pen
        self.points = 2

    def boundingRect(self):
        minX = min(self.start.x(), self.end.x())
        maxX = max(self.start.x(), self.end.x())
        minY = min(self.start.y(), self.end.y())
        maxY = max(self.start.y(), self.end.y())
        return QRect(
            QPoint(minX - 0.5 * self.gridX, minY - 0.5 * self.gridY),
            QPoint(maxX + self.gridX * 0.5, maxY + self.gridY * 0.5),
        )

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        if self.start.x() != self.end.x():
            if self.start.y() != self.end.y():
                midPoint = QPoint(self.end.x(), self.start.y())
                painter.drawLine(self.start, midPoint)
                painter.drawLine(midPoint, self.end)
                self.points = 3
            else:
                painter.drawLine(self.start, self.end)
        else:
            if self.start.y() != self.end.y():
                painter.drawLine(self.start, self.end)
            else:
                painter.drawPoint(self.start)

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

    rect: QRect defined by top left corner and bottom right corner. QRect(Point1,Point2)
    """

    def __init__(
        self,
        start: QPoint,
        pen: QPen,
        pinName:str,
        pinDir:str,
        pinType:str,
        grid: tuple,
    ):
        super().__init__(pen, grid)
        self.start = start # top left corner
        self.pen = pen
        self.pinName = pinName
        self.pinDir = pinDir
        self.pinType = pinType
        self.rect = QRect(start.x()-5,start.y()-5, 10, 10)

    def boundingRect(self):
        return self.rect  #

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.setBrush(self.pen.color())
        painter.drawRect(self.rect)
        painter.setFont(QFont("Arial", 12))
        painter.drawText(QPoint(self.start.x()-5,self.start.y()-10),self.pinName )

    def name(self):
        return self.pinName

    def setName(self, name):
        self.pinName = name

    def setDir(self, direction: str):
        if direction in self.pinDirections:
            self.pinDir = direction

    def getDir(self):
        return self.pinDir

    def setUse(self, use: str):
        if use in self.pinUses:
            self.pinUse = use

class label(shape):
    """

    rect: QRect defined by top left corner and bottom right corner. QRect(Point1,Point2)
    """

    def __init__(
        self,
        start: QPoint,
        pen: QPen,
        labelName:str,
        grid: tuple,
        labelType:str="Normal",
        labelHeight:str="12",
        labelAlignment:str="Left",
        labelOrient:str="R0",
        labelUse:str="Normal",        
    ):
        super().__init__(pen, grid)
        self.start = start # top left corner
        self.pen = pen
        self.labelName = labelName
        self.labelHeight = labelHeight
        self.labelAlignment = labelAlignment
        self.labelOrient = labelOrient
        self.labelUse = labelUse
        self.labelType = labelType
        self.labelFont = QFont("Arial", int(self.labelHeight))
        self.fm = QFontMetrics(self.labelFont)
        self.rect=self.fm.boundingRect(self.labelName)

    def boundingRect(self):
        return QRect(self.start.x(),self.start.y(),self.rect.width(),self.rect.height())  #

    def paint(self, painter, option, widget):
        self.rect=self.fm.boundingRect(self.labelName)
        painter.setFont(self.labelFont)
        painter.setPen(self.pen)
        painter.drawText(self.rect,Qt.AlignCenter,self.labelName)
