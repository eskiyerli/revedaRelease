# net class definition.
from PySide6.QtCore import (QPoint, Qt)
from PySide6.QtGui import (QPen, QStaticText, )
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsItem, QGraphicsSceneMouseEvent, QGraphicsEllipseItem)



class schematicNet(QGraphicsLineItem):
    uses = ["SIGNAL", "ANALOG", "CLOCK", "GROUND", "POWER", ]

    def __init__(self, start: QPoint, end: QPoint, pen: QPen):
        assert isinstance(pen, QPen)
        self.pen = pen
        self.name = None
        self.horizontal = True
        self.start = start
        self.end = end
        self.nameSet = False  # if a name has been set
        self.nameConflict = False  # if a name conflict has been detected

        x1, y1 = self.start.x(), self.start.y()
        x2, y2 = self.end.x(), self.end.y()

        if abs(x1 - x2) >= abs(y1 - y2):  # horizontal
            self.horizontal = True
            self.start = QPoint(min(x1, x2), y1)
            self.end = QPoint(max(x1, x2), y1)
            super().__init__(self.start.x(), y1, self.end.x(), y1)
        else:
            self.horizontal = False
            self.start = QPoint(x1, min(y1, y2))
            self.end = QPoint(x1, max(y1, y2))
            super().__init__(x1, self.start.y(), x1, self.end.y())

        self.setPen(self.pen)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.white, 2, Qt.SolidLine))
        else:
            painter.setPen(self.pen)
        painter.drawLine(self.start, self.end)
        if self.name is not None:
            painter.drawStaticText(self.start, QStaticText(self.name))
            # if there is name conflict, draw the line and name in red.
            if self.nameConflict:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                painter.drawStaticText(self.start, QStaticText(self.name))
                painter.drawLine(self.start, self.end)

    def setName(self, name):
        self.name = name
        self.nameSet = True

    def itemChange(self, change, value):

        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = value.toPoint()
            sceneRect = self.scene().sceneRect()
            gridTuple = self.scene().gridTuple
            viewRect = self.scene().views()[0].viewport().rect()
            newPos.setX(round(newPos.x() / gridTuple[0]) * gridTuple[0])
            newPos.setY(round(newPos.y() / gridTuple[1]) * gridTuple[1])

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
        return super().itemChange(change, value)

class crossingDot(QGraphicsEllipseItem):
    def __init__(self, point: QPoint, radius: int, pen: QPen):
        self.radius = radius
        self.pen = pen
        self.point = point
        super().__init__(point.x()-radius, point.y()-radius, 2*radius, 2*radius)
        self.setPen(pen)
        self.setBrush(pen.color())

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.white, 2, Qt.SolidLine))
            painter.setBrush(Qt.white)
        else:
            painter.setPen(self.pen)
            painter.setBrush(self.pen.color())
        painter.drawEllipse(self.point, self.radius, self.radius)