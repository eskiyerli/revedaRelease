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

import math

# shape class definition for symbol editor.
# base class for all shapes: rectangle, circle, line
from PySide6.QtCore import QPoint, QRect, QRectF, Qt, QLine, QLineF
from PySide6.QtGui import (QPen, QFont, QFontMetrics, QPainterPath, QTextOption,
                           QFontDatabase, )
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsSceneMouseEvent, )
from quantiphy import Quantity
import revedaEditor.common.net as net
import revedaEditor.backend.dataDefinitions as ddef
import pdk.callbacks as cb



class shape(QGraphicsItem):
    def __init__(self, pen: QPen, gridTuple: tuple) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        # self.setZValue(self.layer.z)
        self._pen = pen
        self._gridTuple = gridTuple
        self._angle = 0  # rotation angle
        self._stretch: bool = False

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = value.toPoint()
            sceneRect = self.scene().sceneRect()
            viewRect = self.scene().views()[0].viewport().rect()
            newPos.setX(round(newPos.x() / self._gridTuple[0]) * self._gridTuple[0])
            newPos.setY(round(newPos.y() / self._gridTuple[1]) * self._gridTuple[1])

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

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.prepareGeometryChange()
        self.setRotation(value)  # self.update(self.boundingRect())

    @property
    def pen(self):
        return self._pen

    @pen.setter
    def pen(self, value):
        self._pen = value  # self.update(self.boundingRect())

    @property
    def gridTuple(self):
        return self._gridTuple

    @gridTuple.setter
    def gridTuple(self, value: int):
        self._gridTuple = value

    @property
    def stretch(self):
        return self._stretch

    @stretch.setter
    def stretch(self, value: bool):
        self._stretch = value  # self.update(self.boundingRect())

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if self.scene().changeOrigin:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        else:
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def sceneEvent(self, event):
        """
        Do not propagate event if shape needs to keep still.
        """

        if self.scene() and (self.scene().changeOrigin or self.scene().drawMode):
            return False
        else:
            super().sceneEvent(event)
            return True

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)  # self.setSelected(False)

    def hoverEnterEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setCursor(Qt.ArrowCursor)
        self.setOpacity(0.75)
        self.setFocus()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().hoverLeaveEvent(event)
        self.setCursor(Qt.CrossCursor)
        self.setOpacity(1)
        self.clearFocus()

    def contextMenuEvent(self, event):
        self.scene().itemContextMenu.exec_(event.screenPos())

    def snapToBase(self, number, base):
        """
        Restrict a number to the multiples of base
        """
        return base * int(round(number / base))

    def snapToGrid(self, point: QPoint, gridTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(gridTuple[0] * int(round(point.x() / gridTuple[0])),
                      gridTuple[1] * int(round(point.y() / gridTuple[1])), )


class rectangle(shape):
    """
    rect: QRect defined by top left corner and bottom right corner. QRect(Point1,Point2)
    """

    sides = ["Left", "Right", "Top", "Bottom"]

    def __init__(self, start: QPoint, end: QPoint, pen: QPen, grid: tuple, ):
        super().__init__(pen, grid)
        self._rect = QRectF(start, end).normalized()
        self._start = self._rect.topLeft()
        self._end = self._rect.bottomRight()
        self._stretchSide = None

    def boundingRect(self):
        return self._rect.normalized().adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.drawRect(self._rect)
            if self.stretch:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                if self._stretchSide == rectangle.sides[0]:
                    painter.drawLine(self.rect.topLeft(), self.rect.bottomLeft())
                elif self._stretchSide == rectangle.sides[1]:
                    painter.drawLine(self.rect.topRight(), self.rect.bottomRight())
                elif self._stretchSide == rectangle.sides[2]:
                    painter.drawLine(self.rect.topLeft(), self.rect.topRight())
                elif self._stretchSide == rectangle.sides[3]:
                    painter.drawLine(self.rect.bottomLeft(), self.rect.bottomRight())
        else:
            painter.setPen(self._pen)
            painter.drawRect(self._rect)

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, rect: QRect):
        self.prepareGeometryChange()
        self._rect = rect

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start: QPoint):
        self.prepareGeometryChange()
        self._rect = QRectF(start, self.end).normalized()
        self._start = start

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end: QPoint):
        self.prepareGeometryChange()
        self._rect = QRectF(self.start, end).normalized()
        self._end = end

    @property
    def centre(self):
        return QPoint(int(self._rect.x() + self._rect.width() / 2),
                      int(self._rect.y() + self._rect.height() / 2), )

    @property
    def height(self):
        return self.rect.height()

    @height.setter
    def height(self, height: int):
        self.prepareGeometryChange()
        self._rect.setHeight(height)

    @property
    def width(self):
        return self.rect.width()

    @width.setter
    def width(self, width):
        self.prepareGeometryChange()
        self.rect.setWidth(width)

    @property
    def objName(self):
        return "RECTANGLE"

    @property
    def left(self):
        return self.rect.left()

    @left.setter
    def left(self, left: int):
        self.rect.setLeft(left)

    @property
    def right(self):
        return self.rect.right()

    @right.setter
    def right(self, right: int):
        self.prepareGeometryChange()
        self.rect.setRight(right)

    @property
    def top(self):
        return self.rect.top()

    @top.setter
    def top(self, top: int):
        self.prepareGeometryChange()
        self.rect.setTop(top)

    @property
    def bottom(self):
        return self.rect.bottom()

    @bottom.setter
    def bottom(self, bottom: int):
        self.prepareGeometryChange()
        self.rect.setBottom(bottom)

    @property
    def origin(self):
        return self.rect.bottomLeft()

    @property
    def stretchSide(self):
        return self._stretchSide

    @stretchSide.setter
    def stretchSide(self, value: str):
        self.prepareGeometryChange()
        self._stretchSide = value

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        eventPos = event.pos().toPoint()
        if self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            if eventPos.x() == self.snapToBase(self._rect.left(), self.gridTuple[0]):
                if self._rect.top() <= eventPos.y() <= self._rect.bottom():
                    self.setCursor(Qt.SizeHorCursor)
                    self._stretchSide = rectangle.sides[0]
            elif eventPos.x() == self.snapToBase(self._rect.right(), self.gridTuple[0]):
                if self._rect.top() <= eventPos.y() <= self._rect.bottom():
                    self.setCursor(Qt.SizeHorCursor)
                    self._stretchSide = rectangle.sides[1]
            elif eventPos.y() == self.snapToBase(self._rect.top(), self.gridTuple[1]):
                if self._rect.left() <= eventPos.x() <= self._rect.right():
                    self.setCursor(Qt.SizeVerCursor)
                    self._stretchSide = rectangle.sides[2]
            elif eventPos.y() == self.snapToBase(self._rect.bottom(), self.gridTuple[1]):
                if self._rect.left() <= eventPos.x() <= self._rect.right():
                    self.setCursor(Qt.SizeVerCursor)
                    self._stretchSide = rectangle.sides[3]

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        eventPos = event.pos().toPoint()
        if self.stretch:
            self.prepareGeometryChange()
            if self.stretchSide == rectangle.sides[0]:
                self.setCursor(Qt.SizeHorCursor)
                self.rect.setLeft(eventPos.x())
            elif self.stretchSide == rectangle.sides[1]:
                self.setCursor(Qt.SizeHorCursor)
                self.rect.setRight(eventPos.x() - int(self.pen.width() / 2))
            elif self.stretchSide == rectangle.sides[2]:
                self.setCursor(Qt.SizeVerCursor)
                self.rect.setTop(eventPos.y())
            elif self.stretchSide == rectangle.sides[3]:
                self.setCursor(Qt.SizeVerCursor)
                self.rect.setBottom(eventPos.y() - int(self.pen.width() / 2))
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mouseReleaseEvent(event)
        # self.start = self.rect.topLeft()
        # self.end = self.rect.bottomRight()
        if self.stretch:
            self._stretch = False
            self._stretchSide = None
            self.setCursor(Qt.ArrowCursor)


class circle(shape):
    def __init__(self, centre: QPoint, end: QPoint, pen: QPen, gridTuple: tuple):
        super().__init__(pen, gridTuple)
        xlen = abs(end.x() - centre.x())
        ylen = abs(end.y() - centre.y())
        self._radius = self.snapToBase(int(math.sqrt(xlen ** 2 + ylen ** 2)),
                                       self.gridTuple[0])
        self._centre = centre
        self._topLeft = self._centre - QPoint(self._radius, self._radius)
        self._rightBottom = self._centre + QPoint(self._radius, self._radius)
        self._end = self._centre + QPoint(self._radius, 0)  # along x-axis
        self._stretch = False
        self._startStretch = False

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.drawEllipse(self._centre, 1, 1)
            if self._stretch:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        else:
            painter.setPen(self._pen)
        painter.drawEllipse(self._centre, self._radius, self._radius)

    @property
    def centre(self):
        return self._centre

    @centre.setter
    def centre(self, centre: QPoint):
        self.prepareGeometryChange()
        self._centre = self.snapToGrid(centre, self._gridTuple)
        # self.topLeft = self._centre - QPoint(self._radius, self._radius)
        # self.rightBottom = self._centre + QPoint(self._radius, self._radius)
        self._end = self._centre + QPoint(self._radius, 0)

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, radius: int):
        self.prepareGeometryChange()
        self._radius = self.snapToBase(radius, self._gridTuple[0])
        self._end = self._centre + QPoint(self._radius, 0)
        self._topLeft = self._centre - QPoint(self._radius, self._radius)
        self._rightBottom = self._centre + QPoint(self._radius, self._radius)

    @property
    def centre(self):
        return self._centre

    @centre.setter
    def centre(self, value: QPoint):
        self.prepareGeometryChange()
        if isinstance(value, QPoint):
            self._centre = value

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value: QPoint):
        if isinstance(value, QPoint):
            self.prepareGeometryChange()
            self._end = value

    @property
    def rightBottom(self):
        return self._rightBottom

    @rightBottom.setter
    def rightBottom(self, value: QPoint):
        if isinstance(value, QPoint):
            self._rightBottom = value

    @property
    def topLeft(self):
        return self._topLeft

    @topLeft.setter
    def topLeft(self, value: QPoint):
        if isinstance(value, QPoint):
            self._topLeft = value

    @property
    def objName(self):
        return "CIRCLE"

    def boundingRect(self):
        return (
            QRectF(self._topLeft, self._rightBottom).normalized().adjusted(-2, -2, 2, 2))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if self.isSelected() and self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            # eventPos = self.snap2grid(event.pos(), self._gridTuple)
            eventPos = event.pos().toPoint()
            distance = self.snapToBase(math.sqrt((eventPos.x() - self._centre.x()) ** 2 + (
                    eventPos.y() - self._centre.y()) ** 2), self._gridTuple[0], )
            if distance == self._radius:
                self._startStretch = True
                self.setCursor(Qt.DragMoveCursor)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)
        if self._startStretch:
            eventPos = event.pos().toPoint()
            distance = self.snapToBase(math.sqrt((eventPos.x() - self._centre.x()) ** 2 + (
                    eventPos.y() - self._centre.y()) ** 2), self._gridTuple[0], )
            self.prepareGeometryChange()
            self._radius = distance

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if self._startStretch:
            self._startStretch = False
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self._topLeft = self._centre - QPoint(self._radius, self._radius)
            self._rightBottom = self._centre + QPoint(self._radius, self._radius)
            self._end = self._centre + QPoint(self._radius, 0)
            self.setCursor(Qt.ArrowCursor)


class arc(shape):
    """
    Class to draw arc shapes. Can have four directions.
    """

    arcTypes = ["Up", "Right", "Down", "Left"]
    sides = ["Left", "Right", "Top", "Bottom"]

    def __init__(self, start: QPoint, end: QPoint, pen: QPen, gridTuple: tuple):
        super().__init__(pen, gridTuple)
        self._start = start
        self._end = end
        self._rect = QRectF(self._start, self._end).normalized()
        self._arcLine = QLineF(self._start, self._end)
        self._arcAngle = 0
        self._width = self._rect.width()
        self._height = self._rect.height()
        self._adjustment = int(self.pen.width() / 2)
        self._stretchSide = None
        self.findAngle()

    def findAngle(self):
        self._arcAngle = self._arcLine.angle()
        if 90 >= self._arcAngle >= 0:
            self._arcType = arc.arcTypes[0]
        elif 180 >= self._arcAngle > 90:
            self._arcType = arc.arcTypes[1]
        elif 270 >= self._arcAngle > 180:
            self._arcType = arc.arcTypes[2]
        elif 360 > self._arcAngle > 270:
            self._arcType = arc.arcTypes[3]

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.drawRect(self.rect)
            self.arcDraw(painter)
            if self._stretch:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                self.arcDraw(painter)
                if self._stretchSide == arc.sides[0]:
                    painter.drawLine(self._rect.topLeft(), self._rect.bottomLeft())
                elif self._stretchSide == arc.sides[1]:
                    painter.drawLine(self._rect.topRight(), self._rect.bottomRight())
                elif self._stretchSide == arc.sides[2]:
                    painter.drawLine(self._rect.topLeft(), self._rect.topRight())
                elif self._stretchSide == arc.sides[3]:
                    painter.drawLine(self._rect.bottomLeft(), self._rect.bottomRight())
        else:
            painter.setPen(self._pen)
            self.arcDraw(painter)

    def arcDraw(self, painter):
        if self._arcType == arc.arcTypes[0]:
            painter.drawArc(self._rect, 0, 180 * 16)
        elif self._arcType == arc.arcTypes[1]:
            painter.drawArc(self._rect, 90 * 16, 180 * 16)
        elif self._arcType == arc.arcTypes[2]:
            painter.drawArc(self._rect, 180 * 16, 180 * 16)
        elif self._arcType == arc.arcTypes[3]:
            painter.drawArc(self._rect, 270 * 16, 180 * 16)

    def boundingRect(self):
        return self._rect.adjusted(-2, -2, 2, 2)

    @property
    def objName(self):
        return "ARC"

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, arc_rect: QRect):
        assert isinstance(arc_rect, QRect)
        self._rect = arc_rect.normalized()

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, point: QPoint):
        assert isinstance(point, QPoint)
        self.prepareGeometryChange()
        self._start = self.snapToGrid(point, self.gridTuple)

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, point: QPoint):
        assert isinstance(point, QPoint)
        self.prepareGeometryChange()
        self._end = point
        self._arcLine = QLineF(self._start, self._end)
        self._arcAngle = self._arcLine.angle()
        self.findAngle()
        self._rect = QRectF(self._start, self._end).normalized()

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width):
        self._width = width
        self.prepareGeometryChange()
        self.rect.setWidth(self._width)

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, height):
        self._height = height
        self.prepareGeometryChange()
        self.rect.setHeight(self._height)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        eventPos = event.pos().toPoint()
        if self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            if eventPos.x() == self.snapToBase(self._rect.left(), self.gridTuple[0]):
                if self._rect.top() <= eventPos.y() <= self._rect.bottom():
                    self.setCursor(Qt.SizeHorCursor)
                    self._stretchSide = arc.sides[0]
            elif eventPos.x() == self.snapToBase(self._rect.right(), self.gridTuple[0]):
                if self._rect.top() <= eventPos.y() <= self._rect.bottom():
                    self.setCursor(Qt.SizeHorCursor)
                    self._stretchSide = arc.sides[1]
            elif eventPos.y() == self.snapToBase(self._rect.top(), self.gridTuple[1]):
                if self._rect.left() <= eventPos.x() <= self._rect.right():
                    self.setCursor(Qt.SizeVerCursor)
                    self._stretchSide = arc.sides[2]
            elif eventPos.y() == self.snapToBase(self._rect.bottom(), self.gridTuple[1]):
                if self._rect.left() <= eventPos.x() <= self._rect.right():
                    self.setCursor(Qt.SizeVerCursor)
                    self._stretchSide = arc.sides[3]

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)

        eventPos = event.pos().toPoint()
        if self._stretch:
            self.prepareGeometryChange()
            if self._stretchSide == arc.sides[0]:
                self.setCursor(Qt.SizeHorCursor)
                self._rect.setLeft(eventPos.x())
            elif self._stretchSide == arc.sides[1]:
                self.setCursor(Qt.SizeHorCursor)
                self._rect.setRight(eventPos.x() - self._adjustment)
            elif self._stretchSide == arc.sides[2]:
                self.setCursor(Qt.SizeVerCursor)
                self._rect.setTop(eventPos.y())
            elif self._stretchSide == arc.sides[3]:
                self.setCursor(Qt.SizeVerCursor)
                self._rect.setBottom(eventPos.y() - self._adjustment)
            self.update()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mouseReleaseEvent(event)
        if self.stretch:
            self._stretch = False
            self._stretchSide = None
            self.setCursor(Qt.ArrowCursor)

            if self._arcType == arc.arcTypes[0]:
                self._start = self.snapToGrid(self._rect.bottomLeft(), self.gridTuple)
                self._end = self.snapToGrid(self._rect.topRight(), self.gridTuple)
            elif self._arcType == arc.arcTypes[1]:
                self._start = self.snapToGrid(self._rect.topLeft(), self.gridTuple)
                self._end = self.snapToGrid(self._rect.bottomRight(), self.gridTuple)
            elif self._arcType == arc.arcTypes[2]:
                self._start = self.snapToGrid(self._rect.topRight(), self.gridTuple)
                self._end = self.snapToGrid(self._rect.bottomLeft(), self.gridTuple)
            elif self._arcType == arc.arcTypes[3]:
                self._start = self.snapToGrid(self._rect.bottomRight(), self.gridTuple)
                self._end = self.snapToGrid(self._rect.topLeft(), self.gridTuple)
            self._rect = QRectF(self._start, self._end).normalized()


class line(shape):
    """
    line class definition for symbol drawing.
    """

    stretchSides = ["start", "end"]

    def __init__(self, start: QPoint, end: QPoint, pen: QPen, grid: tuple, ):
        super().__init__(pen, grid)
        self._end = end
        self._start = start
        self._pen = pen
        self._stretch = False
        self._stretchSide = None
        self._line = QLine(self._start, self._end)
        self._rect = QRect(self._start, self._end).normalized()
        self._horizontal = True  # True if line is horizontal, False if vertical

    def boundingRect(self):
        return self._rect.adjusted(-2, -2, 2, 2)

    def shape(self):
        path = QPainterPath()
        path.addRect(self._rect.adjusted(-2, -2, 2, 2))
        return path

    def shape(self):
        path = QPainterPath()
        path.addRect(self._rect.adjusted(-2, -2, 2, 2))
        return path

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            if self._stretch:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                if self._stretchSide == line.stretchSides[0]:
                    painter.drawEllipse(self._start, self.gridTuple[0], self.gridTuple[1])
                elif self._stretchSide == line.stretchSides[1]:
                    painter.drawEllipse(self._end, self.gridTuple[0], self.gridTuple[1])
        else:
            painter.setPen(self._pen)
        painter.drawLine(self._line)

    def objName(self):
        return "LINE"

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, rect: QRect):
        self._rect = rect

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start: QPoint):
        self.prepareGeometryChange()
        self._start = start
        self._line = QLine(self._start, self._end)
        self._rect = QRect(self._start, self._end).normalized()

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end: QPoint):
        self.prepareGeometryChange()
        self._end = end
        self._line = QLine(self._start, self._end)
        self._rect = QRect(self._start, self._end).normalized()

    @property
    def pen(self):
        return self._pen

    @pen.setter
    def pen(self, pen: QPen):
        self._pen = pen

    @property
    def width(self):
        return self._pen.width()

    @width.setter
    def width(self, width: int):
        self._pen.setWidth(width)

    def bBox(self) -> QRect:
        return self.boundingRect()

    def Move(self, offset: QPoint):
        self.start += offset
        self._end += offset

    @property
    def length(self):
        return math.sqrt(
            (self.start.x() - self._end.x()) ** 2 + (self.start.y() - self._end.y()) ** 2)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if self.isSelected() and self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            eventPos = event.pos().toPoint()
            if eventPos == self.start:
                self._stretchSide = line.stretchSides[0]
            elif eventPos == self._end:
                self._stretchSide = line.stretchSides[1]

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        eventPos = event.pos().toPoint()
        if self._stretchSide == line.stretchSides[0]:
            self.prepareGeometryChange()
            self.start = eventPos
            self._line = QLine(self.start, self._end)
            self._rect = QRect(self.start, self._end).normalized()
        elif self._stretchSide == line.stretchSides[1]:
            self.prepareGeometryChange()
            self._end = eventPos
            self._line = QLine(self.start, self._end)
            self._rect = QRect(self.start, self._end).normalized()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self._stretch = False
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self._stretchSide = ""


class pin(shape):
    """
    symbol pin class definition for symbol drawing.
    """

    pinDirs = ["Input", "Output", "Inout"]
    pinTypes = ["Signal", "Ground", "Power", "Clock", "Digital", "Analog"]

    def __init__(self, start: QPoint, pen: QPen, pinName: str = "",
                 pinDir: str = pinDirs[0], pinType: str = pinTypes[0],
                 grid: tuple = (10, 10), ):
        super().__init__(pen, grid)

        self._start = start  # centre of pin
        self._pinName = pinName
        self._pinDir = pinDir
        self._pinType = pinType
        self._connected = False  # True if the pin is connected to a net.
        self._rect = QRect(self._start.x() - 5, self._start.y() - 5, 10, 10)

    def __repr__(self):
        return f"pin: {self._pinName} {self.mapToScene(self._start)}"

    def boundingRect(self):
        return self._rect  #

    def paint(self, painter, option, widget):
        painter.setPen(self._pen)
        painter.setBrush(self._pen.color())
        painter.drawRect(self._rect)
        painter.setFont(QFont("Arial", 12))
        painter.drawText(QPoint(self._start.x() - 5, self._start.y() - 10), self._pinName)
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.setBrush(Qt.yellow)
            painter.drawRect(self._rect)

    def objName(self):
        return "PIN"

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = start

    @property
    def pinName(self):
        return self._pinName

    @pinName.setter
    def pinName(self, pinName):
        if pinName != "":
            self._pinName = pinName

    @property
    def pinDir(self):
        return self._pinDir

    @pinDir.setter
    def pinDir(self, direction: str):
        if direction in self.pinDirections:
            self._pinDir = direction

    @property
    def pinType(self):
        return self._pinType

    @pinType.setter
    def pinType(self, pintype: str):
        if pintype in self.pinTypes:
            self._pinType = pintype

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, value: bool):
        if isinstance(value, bool):
            self._connected = value

    def toSchematicPin(self, start: QPoint, pen: QPen, gridTuple):
        return schematicPin(start, pen, self.pinName, self.pinDir, self.pinType, gridTuple)


class text(shape):
    """
    This class is for text annotations on symbol or schematics.
    """

    textAlignments = ["Left", "Center", "Right"]
    textOrients = ["R0", "R90", "R180", "R270"]

    def __init__(self, start: QPoint, pen: QPen, textContent: str = "",
                 grid: tuple = (10, 10), fontFamily="Helvetica", fontStyle="Regular",
                 textHeight: str = "12", textAlign: str = "Left", textOrient: str = "R0", ):
        super().__init__(pen, grid)

        self._start = start
        self._pen = pen
        self._textContent = textContent
        self._textHeight = textHeight
        self._textAlign = textAlign
        self._textOrient = textOrient
        self._textFont = QFont(fontFamily)
        self._textFont.setStyleName(fontStyle)
        self._textFont.setPointSize(int(float(self._textHeight)))
        self._textFont.setKerning(True)
        self.setOpacity(1)
        self._fm = QFontMetrics(self._textFont)
        self._textOptions = QTextOption()
        if self._textAlign == text.textAlignments[0]:
            self._textOptions.setAlignment(Qt.AlignmentFlag.AlignLeft)
        elif self._textAlign == text.textAlignments[1]:
            self._textOptions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif self._textAlign == text.textAlignments[2]:
            self._textOptions.setAlignment(Qt.AlignmentFlag.AlignRight)

    def boundingRect(self):
        if self._textAlign == text.textAlignments[0]:
            self._rect = self._fm.boundingRect(QRect(0, 0, 400, 400),
                                               Qt.AlignmentFlag.AlignLeft,
                                               self._textContent)
        elif self._textAlign == text.textAlignments[1]:
            self._rect = self._fm.boundingRect(QRect(0, 0, 400, 400),
                                               Qt.AlignmentFlag.AlignCenter,
                                               self._textContent)
        elif self._textAlign == text.textAlignments[2]:
            self._rect = self._fm.boundingRect(QRect(0, 0, 400, 400),
                                               Qt.AlignmentFlag.AlignRight,
                                               self._textContent)
        return QRect(self._start.x(), self._start.y() - self._rect.height(),
                     self._rect.width(), self._rect.height(), )

    def paint(self, painter, option, widget):
        painter.setFont(self._textFont)
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.drawRect(self.boundingRect())
        else:
            painter.setPen(self._pen)
        painter.drawText(self.boundingRect(), self._textContent, o=self._textOptions)

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value: QPoint):
        self._start = value

    @property
    def textContent(self):
        return self._textContent

    @textContent.setter
    def textContent(self, inputText: str):
        if isinstance(inputText, str):
            self._textContent = inputText
        else:
            self.scene().logger.error(f"Not a string: {inputText}")

    @property
    def fontFamily(self) -> str:
        return self._textFont.family()

    @fontFamily.setter
    def fontFamily(self, familyName):
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamilies = [family for family in fontFamilies if
                         QFontDatabase.isFixedPitch(family)]
        if familyName in fixedFamilies:
            self._textFont.setFamily(familyName)
        else:
            self.scene().logger.error(f"Not a valid font name: {familyName}")

    @property
    def fontStyle(self) -> str:
        return self._textFont.styleName()

    @fontStyle.setter
    def fontStyle(self, value: str):
        if value in QFontDatabase.styles(self._textFont.family()):
            self._textFont.setStyleName(value)
        else:
            self.scene().logger.error(f"Not a valid font style: {value}")

    @property
    def textHeight(self) -> int:
        return self._textHeight

    @textHeight.setter
    def textHeight(self, value: int):
        fontSizes = [str(size) for size in QFontDatabase.pointSizes(self._textFont.family(),
                                                                    self._textFont.styleName())]
        if value in fontSizes:
            self._textHeight = value
        else:
            self.scene().logger.error(f"Not a valid font height: {value}")
            self.scene().logger.warning(f"Valid font heights are: {fontSizes}")

    @property
    def textFont(self) -> QFont:
        return self._textFont

    @textFont.setter
    def textFont(self, value: QFont):
        assert isinstance(value, QFont)
        self._textFont = value

    @property
    def textAlignment(self):
        return self._textAlign

    @textAlignment.setter
    def textAlignment(self, value):
        if value in text.textAlignments:
            self._textAlign = value
        else:
            self.scene().logger.error(f"Not a valid text alignment value: {value}")

    @property
    def textOrient(self):
        return self._textOrient

    @textOrient.setter
    def textOrient(self, value):
        if value in text.textOrients:
            self._textOrient = value
        else:
            self.scene().logger.error(f"Not a valid text orientation: {value}")


class label(shape):
    """
    label: text class definition for symbol drawing.
    labelText is what is shown on the symbol in a schematic
    """

    labelAlignments = ["Left", "Center", "Right"]
    labelOrients = ["R0", "R90", "R180", "R270", "MX", "MX90", "MY", "MY90"]
    labelUses = ["Normal", "Instance", "Pin", "Device", "Annotation"]
    labelTypes = ["Normal", "NLPLabel", "PyLabel"]
    predefinedLabels = ["[@libName]", "[@cellName]", "[@viewName]", "[@instName]",
                        "[@modelName]", "[@elementNum]" ]

    def __init__(self, start: QPoint, pen: QPen, labelDefinition: str = "",
                 grid: tuple = (10, 10), labelType: str = "Normal", labelHeight: str = "12",
                 labelAlign: str = "Left", labelOrient: str = "R0",
                 labelUse: str = "Normal", ):
        super().__init__(pen, grid)
        self._start = start  # top left corner
        self._pen = pen
        self._labelDefinition = labelDefinition  # label definition is what is
        # entered in the symbol editor
        self._labelName = None  # label Name
        self._labelValue = None  # label value
        self._labelText = None  # Displayed label
        self._labelHeight = labelHeight
        self._labelAlign = labelAlign
        self._labelOrient = labelOrient
        self._labelUse = labelUse
        self._labelType = labelType
        self._labelFont = QFont("Arial")
        self._labelFont.setPointSize(int(float(self._labelHeight)))
        self._labelFont.setKerning(False)
        self._labelVisible: bool = False
        self._labelValueSet: bool = False
        # labels are visible by default
        self.setOpacity(1)
        self._fm = QFontMetrics(self._labelFont)
        self._rect = self._fm.boundingRect(self._labelDefinition)

    def __repr__(self):
        return f"label: {self._labelText} for {self._labelDefinition} at {self._start}, " \
               f"value =  {self._labelValue}"
    def boundingRect(self):
        return QRect(self._start.x(), self._start.y(), self._rect.width(),
                     self._rect.height())  #

    def paint(self, painter, option, widget):
        # self._rect = self.fm.boundingRect(self.labelName)
        self._labelFont.setPointSize(int(self._labelHeight))
        painter.setFont(self._labelFont)
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.drawRect(self.boundingRect())
        else:
            painter.setPen(self._pen)
        if self._labelText:
            painter.drawText(QPoint(self._start.x(), self._start.y() + self._rect.height()),
                             self._labelText, )
        else:
            painter.drawText(QPoint(self._start.x(), self._start.y() + self._rect.height()),
                             self._labelDefinition, )
        self._fm = QFontMetrics(self._labelFont)
        self._rect = self._fm.boundingRect(self._labelDefinition)

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value: QPoint):
        self._start = value

    @property
    def left(self):
        return self._start.x()

    @property
    def right(self):
        return self._start.x() + self.boundingRect().width()

    @property
    def top(self):
        return self._start.y()

    @property
    def bottom(self):
        return self._start.y() + self.boundingRect().height()

    @property
    def width(self):
        return self.boundingRect().width()

    @property
    def height(self):
        return self.boundingRect().height()

    @property
    def labelName(self):
        return self._labelName

    @labelName.setter
    def labelName(self, labelName:str):
        self._labelName = labelName

    @property
    def labelDefinition(self):
        return self._labelDefinition

    @labelDefinition.setter
    def labelDefinition(self, labelDefinition:str):
        if isinstance(labelDefinition, str):
            self._labelDefinition = labelDefinition.strip()

    @property
    def labelValue(self):
        return self._labelValue

    @labelValue.setter
    def labelValue(self, labelValue):
        self._labelValue = labelValue
        self._labelValueSet = True
        self.labelDefs()

    @property
    def labelValueSet(self) -> bool:
        return self._labelValueSet

    @labelValueSet.setter
    def labelValueSet(self, value: bool):
        if isinstance(value, bool):
            self._labelValueSet = value

    @property
    def labelHeight(self):
        return self._labelHeight

    @labelHeight.setter
    def labelHeight(self, value: int):
        self._labelHeight = value

    @property
    def labelText(self):
        return self._labelText

    @labelText.setter
    def labelText(self, labelText):
        self._labelText = labelText
        self._rect = self._fm.boundingRect(self._labelText)

    def objName(self):
        return "LABEL"

    @property
    def labelType(self):
        return self._labelType

    @labelType.setter
    def labelType(self, labelType):
        if labelType in self.labelTypes:
            self._labelType = labelType
        elif self.scene():
            self.scene().logger.error("Invalid label type")

    @property
    def labelAlign(self):
        return self._labelAlign

    @labelAlign.setter
    def labelAlign(self, labelAlignment):
        if labelAlignment in self.labelAlignments:
            self._labelAlign = labelAlignment
        elif self.scene():
            self.scene().logger.error("Invalid label alignment")

    @property
    def labelOrient(self):
        return self._labelOrient

    @labelOrient.setter
    def labelOrient(self, labelOrient):
        if labelOrient in self.labelOrients:
            self._labelOrient = labelOrient
        else:
            print("Invalid label orientation")

    @property
    def labelUse(self):
        return self._labelUse

    @labelUse.setter
    def labelUse(self, labelUse):
        if labelUse in self.labelUses:
            self._labelUse = labelUse
        elif self.scene():
            self.scene().logger.error("Invalid label use")

    @property
    def labelFont(self):
        return self._labelFont

    @labelFont.setter
    def labelFont(self, labelFont: QFont):
        self._labelFont = labelFont

    @property
    def labelVisible(self) -> bool:
        return self._labelVisible

    @labelVisible.setter
    def labelVisible(self, value: bool):
        assert isinstance(value, bool)
        if value:
            self.setOpacity(1)
            self._labelVisible = True
        else:
            self.setOpacity(0.001)
            self._labelVisible = False

    def moveBy(self, delta: QPoint):
        self._start += delta

    def labelDefs(self):
        """
        This method will create label name, value andtext from label
        definition. It should be run label is defined or redefined.
        """
        self.prepareGeometryChange()
        if self._labelType == label.labelTypes[0]:
            self._labelName = self._labelDefinition
            self._labelText = self._labelDefinition
            self._labelValue = None
            self._labelValueSet = True
        elif self.labelType == label.labelTypes[1]:
            try:
                if self._labelDefinition in label.predefinedLabels:
                    self._labelValueSet = True
                    match self.labelDefinition:
                        case "[@cellName]":
                            self._labelName = "cellName"
                            self._labelValue = self.parentItem().cellName
                            self._labelText = self._labelValue
                        case "[@instName]":
                            self._labelName = "instName"
                            self._labelValue = f"I{self.parentItem().counter}"
                            self._labelText = self._labelValue
                        case "[@libName]":
                            self._labelName = "libName"
                            self._labelValue = self.parentItem().libraryName
                            self._labelText = self._labelValue
                        case "[@viewName]":
                            self._viewName = "viewName"
                            self._labelValue = self.parentItem().viewName
                            self._labelText = self._labelValue
                        case "[@modelName]":
                            self._labelName = "modelName"
                            self._labelValue = self.parentItem().attr.get(
                                    "modelName", "")
                            self._labelText = self._labelValue
                        case "[@elementNum]":
                            self._labelName = "elementNum"
                            self._labelValue = f"{self.parentItem().counter}"
                            self._labelText = self._labelValue
                else:
                    labelFields = (self._labelDefinition.lstrip("[@").rstrip("]").rstrip(
                                ":").split(":"))
                    self._labelName = labelFields[0].strip()
                    match len(labelFields):
                        case 1:
                            if not self._labelValueSet:
                                self._labelValue = "?"
                            self._labelText = self._labelValue
                        case 2:
                            if self._labelValueSet:
                                self._labelText = (
                                    labelFields[1].strip().replace("%", self._labelValue))
                            else:
                                self._labelValue = "?"
                        case 3:
                            tempLabelValue = (
                                    labelFields[2].strip().split("=")[-1].split()[-1])
                            if self.labelValueSet:
                                self._labelText = labelFields[2
                                    ].replace(tempLabelValue, self.labelValue)
                            else:
                                self._labelText = labelFields[2]
                                self._labelValue = tempLabelValue

            except Exception as e:
                if self.scene():
                    self.scene().logger.error(e)
        elif self._labelType == label.labelTypes[2]:  # pyLabel
            try:
                labelFields = self._labelDefinition.strip().split("=")
                self._labelName = labelFields[0].strip()
                labelFunction = labelFields[1].strip()
                # pass the PDK callback class named with "cellName" the labels
                # dictionary of instance.w
                expression = (f"cb.{self.parentItem().cellName}(self.parentItem().labels).{labelFunction}")
                self._labelValue = Quantity(eval(expression)).render(prec=3)
                self._labelText = f"{self._labelName}={self._labelValue}"
            except Exception as e:
                if self.scene():
                    self.scene().logger.error(e)


class symbolShape(shape):
    def __init__(self, pen: QPen, gridTuple: tuple, shapes: list, attr: dict):
        super().__init__(pen, gridTuple)
        assert shapes is not None  # must not be an empty list
        self.shapes = shapes  # list of shapes in the symbol
        self.attr = attr  # parameters common to all instances of symbol
        self._counter = 0  # item's number on schematic
        self._libraryName = ""
        self._cellName = ""
        self._viewName = ""
        self._instanceName = ""
        self._netlistLine = ""
        # self._simViewName = None
        self._angle = 0.0
        self._drawings = list()
        self._labels = dict()  # dict of labels
        self._pins = dict()  # dict of pins
        self.pinLocations = dict()  # pinName: pinRect
        self.pinNetMap = dict()  # pinName: netName
        self.pinNetTupleList = list()
        for item in self.shapes:
            item.setFlag(QGraphicsItem.ItemIsSelectable, False)
            item.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
            item.setParentItem(self)
            if type(item) is pin:
                self._pins[item.pinName] = item
            elif type(item) is label:
                self._labels[item.labelName] = item
            else:
                self._drawings.append(item)
        self.setFiltersChildEvents(True)
        self.setHandlesChildEvents(True)
        self.setFlag(QGraphicsItem.ItemContainsChildrenInShape, True)
        self.borderRect = self._drawings[0].sceneBoundingRect()
        if self._drawings[1:]:
            for draw in self._drawings[1:]:
                self.borderRect = self.borderRect.united(draw.sceneBoundingRect())
        self.dashLines = dict()

    def __repr__(self):
        return (f"symbolShape(name={self.cellName}, scene position= {self.scenePos()}, "
                f"pins = {self.pins}, labels = {self.labels}, ")

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.drawRect(self.borderRect)

    def boundingRect(self):
        return self.childrenBoundingRect()

    def sceneEvent(self, event):
        try:  # if net is being drawn, do not accept any event.
            if self.scene().drawWire:
                return False
            else:
                super().sceneEvent(event)
                return True
        except AttributeError:
            return False

    def itemChange(self, change, value):

        if self.scene() and change == QGraphicsItem.ItemPositionHasChanged:
            # item's position has changed
            # do something here
            for item in self.pinNetTupleList:
                if item.net.isVisible():
                    item.net.hide()
                self.dashLines[item.net].start = item.pin.mapToScene(item.pin.start)
        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.dashLines = dict()
        self.pinNetTupleList = list()
        view = self.scene().parent.view
        viewNets = [item for item in view.items() if isinstance(item, net.schematicNet)]
        # create a named tuple to record whether the pin is located at the start or at
        # the end of the net.
        pins = [item for item in self.pins.values()]
        for pinItem in pins:
            for viewNet in viewNets:
                if pinItem.sceneBoundingRect().adjusted(-2, -2, 2, 2).contains(
                        viewNet.start):
                    self.pinNetTupleList.append(ddef.pinNetTuple(pinItem, viewNet, "start"))
                elif pinItem.sceneBoundingRect().adjusted(-2, -2, 2, 2).contains(
                        viewNet.end):
                    self.pinNetTupleList.append(ddef.pinNetTuple(pinItem, viewNet, "end"))

        for item in self.pinNetTupleList:
            pinSceneLoc = item.pin.mapToScene(item.pin.start)
            if item.netEnd == 'start':
                self.dashLines[item.net] = net.schematicNet(pinSceneLoc, item.net.end,
                                                            self.scene().otherPen)
            elif item.netEnd == 'end':
                self.dashLines[item.net] = net.schematicNet(pinSceneLoc, item.net.start,
                                                            self.scene().otherPen)
            self.scene().addItem(self.dashLines[item.net])
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        for key, net in self.dashLines.items():
            wires = self.scene().addWires(net.start, self.scene().wirePen)

            self.scene().extendWires(wires, net.start, net.end)
            finalWires = self.scene().pruneWires(wires, self.scene().wirePen)
            if key.nameSet:
                for wire in finalWires:
                    wire.name = key.name
            self.scene().removeItem(key)
            self.scene().removeItem(net)
        # self.dashLines =dict()
        super().mouseReleaseEvent(event)

    @property
    def libraryName(self):
        return self._libraryName

    @libraryName.setter
    def libraryName(self, value):
        self._libraryName = value

    @property
    def cellName(self):
        return self._cellName

    @cellName.setter
    def cellName(self, value: str):
        self._cellName = value

    @property
    def viewName(self):
        return self._viewName

    @viewName.setter
    def viewName(self, value: str):
        self._viewName = value

    @property
    def instanceName(self):
        return self._instanceName

    @instanceName.setter
    def instanceName(self, value: str):
        '''
        If instance name is changed and [@instName] label exists, change it too.
        '''
        self._instanceName = value
        if self.labels.get('instanceName', None):
            self.labels['instanceName'].labelValue = value
            self.labels['instanceName'].labelValueSet = True
            self.labels['instanceName'].update()

    @property
    def counter(self) -> int:
        return self._counter

    @counter.setter
    def counter(self, value: int):
        assert isinstance(value, int)
        self._counter = value

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value: float):
        self.setRotation(value)
        self._angle = value

    @property
    def labels(self):
        return self._labels # dictionary

    @property
    def pins(self):
        return self._pins

    @property
    def drawings(self):
        return self._drawings

class schematicPin(shape):
    """
    schematic pin class.
    """

    pinDirs = ["Input", "Output", "Inout"]
    pinTypes = ["Signal", "Ground", "Power", "Clock", "Digital", "Analog"]

    def __init__(self, start: QPoint, pen: QPen, pinName, pinDir, pinType,
                 gridTuple: tuple):
        super().__init__(pen, gridTuple)
        self._start = start
        self._pinName = pinName
        self._pinDir = pinDir
        self._pinType = pinType

    def __repr__(self):
        return f"schematicPin({self._start}, {self._pen}, {self._pinName}, {self._pinDir}, {self._pinType})"

    def paint(self, painter, option, widget):

        painter.setPen(self._pen)
        painter.setBrush(self._pen.color())
        painter.setFont(QFont("Arial", 12))
        match self.pinDir:
            case "Input":
                painter.drawPolygon([QPoint(self._start.x() - 10, self._start.y() - 10),
                                     QPoint(self._start.x() + 10, self._start.y() - 10),
                                     QPoint(self._start.x() + 20, self._start.y()),
                                     QPoint(self._start.x() + 10, self._start.y() + 10),
                                     QPoint(self._start.x() - 10, self._start.y() + 10), ])
            case "Output":
                painter.drawPolygon([QPoint(self._start.x() - 20, self._start.y()),
                                     QPoint(self._start.x() - 10, self._start.y() - 10),
                                     QPoint(self._start.x() + 10, self._start.y() - 10),
                                     QPoint(self._start.x() + 10, self._start.y() + 10),
                                     QPoint(self._start.x() - 10, self._start.y() + 10), ])
            case "Inout":
                painter.drawPolygon([QPoint(self._start.x() - 20, self._start.y()),
                                     QPoint(self._start.x() - 10, self._start.y() - 10),
                                     QPoint(self._start.x() + 10, self._start.y() - 10),
                                     QPoint(self._start.x() + 20, self._start.y()),
                                     QPoint(self._start.x() + 10, self._start.y() + 10),
                                     QPoint(self._start.x() - 10, self._start.y() + 10), ])
        painter.drawText(self._start.x(), self._start.y() - 20, self.pinName)
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            # painter.setBrush(Qt.yellow)
            painter.drawRect(QRect.span(QPoint(self._start.x() - 10, self._start.y() - 10),
                                        QPoint(self._start.x() + 10,
                                               self._start.y() + 10), ))

    def boundingRect(self):
        return QRect(self._start.x() - 10, self._start.y() - 10, 30, 20).adjusted(-5, -10,
                                                                                  5, 5)

    def sceneEvent(self, event):
        if self.scene().drawWire:
            return False
        else:
            super().sceneEvent(event)
            return True

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setPos(event.scenePos() - event.buttonDownPos(Qt.LeftButton))

    def toSymbolPin(self, start: QPoint, pen: QPen, gridTuple: tuple):
        return pin(start, pen, self.pinName, self.pinDir, self.pinType, gridTuple)

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = start

    @property
    def pinName(self):
        return self._pinName

    @pinName.setter
    def pinName(self, pinName):
        if pinName != "":
            self._pinName = pinName

    @property
    def pinDir(self):
        return self._pinDir

    @pinDir.setter
    def pinDir(self, direction: str):
        if direction in self.pinDirs:
            self._pinDir = direction

    @property
    def pinType(self):
        return self._pinType

    @pinType.setter
    def pinType(self, pintype: str):
        if pintype in self.pinTypes:
            self._pinType = pintype
