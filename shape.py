# shape class definition
# base class for all shapes: rectangle, circle, line
from PySide6.QtWidgets import (
    QGraphicsItem,
)
from PySide6.QtGui import (
    QPen,
)
from PySide6.QtCore import QPoint, QPointF, QRect, Qt


import circuitElements as cel


class shape(QGraphicsItem):
    def __init__(self, shapeLayer: cel.layer) -> None:
        super().__init__()
        self.layer = shapeLayer
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setZValue(self.layer.z)
        self.gridSize = 10

    def itemChange(self, change, value):
        if (change == QGraphicsItem.ItemPositionChange and self.scene()):
            newPos = value.toPoint()
            newPos.setX(round(newPos.x() / self.gridSize) * self.gridSize)
            newPos.setY(round(newPos.y() / self.gridSize) * self.gridSize)
            return newPos
        # return QGraphicsItem.itemChange(self, change, value)
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
        rect: QRect,
        shapeLayer: cel.layer,
        width: int = 1,
        lineStyle=Qt.SolidLine,
    ):
        super().__init__(shapeLayer)
        self.rect = rect
        self.pen = QPen(shapeLayer.color, width, lineStyle)
        self.loc = self.rect.topLeft()

    def boundingRect(self):
        return self.rect  #

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.drawRect(self.rect)


    def centre(self):
        return QPoint(
            self.rect.x() + self.rect.width() / 2,
            self.rect.y() + self.rect.height() / 2,
        )

    def height(self):
        return self.rect.height()

    def width(self):
        return self.rect.width()

    def objName(self):
        return "RECTANGLE"
