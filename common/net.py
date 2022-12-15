
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

# net class definition.
from PySide6.QtCore import (QPoint, Qt)
from PySide6.QtGui import (QPen, QStaticText, )
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsItem, QGraphicsEllipseItem)


class schematicNet(QGraphicsLineItem):
    '''
    Base schematic net class.
    '''
    uses = ["SIGNAL", "ANALOG", "CLOCK", "GROUND", "POWER", ]

    def __init__(self, start: QPoint, end: QPoint, pen: QPen):
        assert isinstance(pen, QPen)
        self._pen = pen
        self._name = None
        self._horizontal = True
        self._start = start
        self._end = end
        self._nameSet = False  # if a name has been set
        self._nameConflict = False  # if a name conflict has been detected

        x1, y1 = self._start.x(), self._start.y()
        x2, y2 = self._end.x(), self._end.y()

        if abs(x1 - x2) >= abs(y1 - y2):  # horizontal
            self._horizontal = True
            self._start = QPoint(min(x1, x2), y1)
            self._end = QPoint(max(x1, x2), y1)
            super().__init__(self._start.x(), y1, self._end.x(), y1)
        else:
            self._horizontal = False
            self._start = QPoint(x1, min(y1, y2))
            self._end = QPoint(x1, max(y1, y2))
            super().__init__(x1, self._start.y(), x1, self._end.y())

        self.setPen(self._pen)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.white, 2, Qt.SolidLine))
        else:
            painter.setPen(self._pen)
        painter.drawLine(self._start, self._end)
        if self.name is not None:
            painter.drawStaticText(self._start, QStaticText(self.name))
            # if there is name conflict, draw the line and name in red.
            if self._nameConflict:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                painter.drawStaticText(self._start, QStaticText(self.name))
                painter.drawLine(self._start, self._end)

    def sceneEvent(self, event):
        try:
            if self.scene().drawWire:
                return False
            else:
                super().sceneEvent(event)
                return True
        except AttributeError:
            return False

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start: QPoint):
        self._start = start

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end: QPoint):
        self._end = end

    @property
    def pen(self):
        return self._pen

    @pen.setter
    def pen(self, pen: QPen):
        self._pen = pen

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        # self._nameSet = True

    @property
    def horizontal(self):
        return self._horizontal

    @horizontal.setter
    def horizontal(self, value: bool):
        self._horizontal = value

    @property
    def nameSet(self) -> bool:
        return self._nameSet

    @nameSet.setter
    def nameSet(self, value: bool):
        assert isinstance(value,bool)
        self._nameSet = value

    @property
    def nameConflict(self) -> bool:
        return self._nameConflict

    @nameConflict.setter
    def nameConflict(self, value: bool):
        assert isinstance(value,bool)
        self._nameConflict = value

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

    def contextMenuEvent(self, event):
        self.scene().itemContextMenu.exec_(event.screenPos())


class crossingDot(QGraphicsEllipseItem):
    def __init__(self, point: QPoint, radius: int, pen: QPen):
        self.radius = radius
        self._pen = pen
        self.point = point
        super().__init__(point.x() - radius, point.y() - radius, 2 * radius, 2 * radius)
        self.setPen(pen)
        self.setBrush(pen.color())

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.white, 2, Qt.SolidLine))
            painter.setBrush(Qt.white)
        else:
            painter.setPen(self._pen)
            painter.setBrush(self._pen.color())
        painter.drawEllipse(self.point, self.radius, self.radius)
