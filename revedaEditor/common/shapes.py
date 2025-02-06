#    “Commons Clause” License Condition v1.0
#   #
#    The Software is provided to you by the Licensor under the License, as defined
#    below, subject to the following condition.
#
#    Without limiting other conditions in the License, the grant of rights under the
#    License will not include, and the License does not grant to you, the right to
#    Sell the Software.
#
#    For purposes of the foregoing, “Sell” means practicing any or all of the rights
#    granted to you under the License to provide to third parties, for a fee or other
#    consideration (including without limitation fees for hosting or consulting/
#    support services related to the Software), a product or service whose value
#    derives, entirely or substantially, from the functionality of the Software. Any
#    license notice or attribution required by the License must also include this
#    Commons Clause License Condition notice.
#
#   Add-ons and extensions developed for this software may be distributed
#   under their own separate licenses.
#
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
#

import math
from functools import cached_property
from platform import architecture
from typing import (List, Tuple, NamedTuple, Union, Dict, Set)

from PySide6.QtCore import (QPoint, QPointF, QRect, QRectF, Qt, QLine, QLineF, )
from PySide6.QtGui import (QBrush, QFont, QFontMetrics, QPainterPath, QTextOption,
                           QFontDatabase, QTransform, QPolygonF, QPolygon)
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsPolygonItem, QGraphicsSimpleTextItem,
                               QGraphicsRectItem, QGraphicsSceneMouseEvent,
                               QGraphicsSceneHoverEvent, QGraphicsScene)

from revedaEditor.backend.pdkPaths import importPDKModule
from bisect import bisect_right

schlyr = importPDKModule('schLayers')
symlyr = importPDKModule('symLayers')
import revedaEditor.common.net as net
from revedaEditor.common.labels import symbolLabel


class symbolShape(QGraphicsItem):
    def __init__(self) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        self._angle: float = 0.0  # rotation angle
        self._stretch: bool = False
        self._pen = symlyr.defaultPen
        self._draft: bool = False
        self._brush: QBrush = schlyr.draftBrush
        self._flipTuple = (1, 1)

    def __repr__(self):
        return "symbolShape()"

    @property
    def pen(self):
        return self._pen

    @property
    def brush(self):
        return self._brush

    @brush.setter
    def brush(self, value: QBrush):
        if isinstance(value, QBrush):
            self._brush = value

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.prepareGeometryChange()
        self.setRotation(value)

    @property
    def stretch(self):
        return self._stretch

    @stretch.setter
    def stretch(self, value: bool):
        self._stretch = value

    @property
    def draft(self) -> bool:
        return self._draft

    @draft.setter
    def draft(self, value: bool):
        assert isinstance(value, bool)
        self._draft = value
        # all the child items and their children should be also draft.
        for item in self.childItems():
            item.draft = True

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setSelected(True)
        if self.scene().editModes.moveItem:
            self.setFlag(QGraphicsItem.ItemIsMovable, True)

        super().mousePressEvent(event)

    def sceneEvent(self, event):
        """
        Do not propagate event if shape needs to keep still.
        """
        if self.scene() and (self.scene().editModes.changeOrigin or self.scene().drawMode):
            return False
        else:
            super().sceneEvent(event)
            return True

    def itemChange(self, change, value):
        if self.scene():
            match change:
                case QGraphicsItem.ItemSelectedHasChanged:
                    if value:
                        self.setZValue(self.zValue() + 10)
                    else:
                        self.setZValue(self.zValue() - 10)
        return super().itemChange(change, value)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)  # self.setSelected(False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self.setCursor(Qt.ArrowCursor)
        self.setOpacity(0.75)
        self.setFocus()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        super().hoverLeaveEvent(event)
        self.setCursor(Qt.CrossCursor)
        self.setOpacity(1)
        self.clearFocus()

    def contextMenuEvent(self, event):
        self.setSelected(True)
        self.scene().itemContextMenu.exec_(event.screenPos())

    @property
    def flipTuple(self):
        return self._flipTuple

    @flipTuple.setter
    def flipTuple(self, flipState: Tuple[int, int]):
        self.prepareGeometryChange()
        # Get the current transformation
        transform = self.transform()

        # Apply the scaling
        transform.scale(*flipState)

        # Set the new transformation
        self.setTransform(transform)
        self._flipTuple = (transform.m11(), transform.m22())


class symbolRectangle(symbolShape):
    """
        rect: QRect defined by top left corner and bottom right corner. QRect(Point1,Point2)
    f"""

    sides = ["Left", "Right", "Top", "Bottom"]

    def __init__(self, start: QPoint, end: QPoint) -> None:
        super().__init__()
        self._rect = QRectF(start, end).normalized()
        self._start = self._rect.topLeft()
        self._end = self._rect.bottomRight()
        self._stretchSide = None
        self._pen = symlyr.symbolPen

    def boundingRect(self):
        return self._rect.normalized().adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget):
        if self.draft:
            painter.setPen(symlyr.draftPen)
            self.setZValue(symlyr.draftLayer.z)
        elif self.isSelected():
            painter.setPen(symlyr.selectedSymbolPen)
            self.setZValue(symlyr.symbolLayer.z)
            if self.stretch:
                painter.setPen(symlyr.stretchSymbolPen)
                self.setZValue(symlyr.stretchSymbolLayer.z)
                if self._stretchSide == symbolRectangle.sides[0]:
                    painter.drawLine(self.rect.topLeft(), self.rect.bottomLeft())
                elif self._stretchSide == symbolRectangle.sides[1]:
                    painter.drawLine(self.rect.topRight(), self.rect.bottomRight())
                elif self._stretchSide == symbolRectangle.sides[2]:
                    painter.drawLine(self.rect.topLeft(), self.rect.topRight())
                elif self._stretchSide == symbolRectangle.sides[3]:
                    painter.drawLine(self.rect.bottomLeft(), self.rect.bottomRight())
        else:
            painter.setPen(symlyr.symbolPen)
            self.setZValue(symlyr.symbolLayer.z)
        painter.drawRect(self._rect)

    def __repr__(self):
        return f"symbolRectangle({self._start},{self._end})"

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
        return self._rect.height()

    @height.setter
    def height(self, height: int):
        self.prepareGeometryChange()
        self._rect.setHeight(height)

    @property
    def width(self):
        return self._rect.width()

    @width.setter
    def width(self, width):
        self.prepareGeometryChange()
        self._rect.setWidth(width)

    @property
    def left(self):
        return self._rect.left()

    @left.setter
    def left(self, left: int):
        self._rect.setLeft(left)

    @property
    def right(self):
        return self._rect.right()

    @right.setter
    def right(self, right: int):
        self.prepareGeometryChange()
        self._rect.setRight(right)

    @property
    def top(self):
        return self._rect.top()

    @top.setter
    def top(self, top: int):
        self.prepareGeometryChange()
        self._rect.setTop(top)

    @property
    def bottom(self):
        return self._rect.bottom()

    @bottom.setter
    def bottom(self, bottom: int):
        self.prepareGeometryChange()
        self._rect.setBottom(bottom)

    @property
    def origin(self):
        return self._rect.bottomLeft()

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
            if (
                    eventPos.x() == self._rect.left() and self._rect.top() <= eventPos.y() <= self._rect.bottom()):
                self.setCursor(Qt.SizeHorCursor)
                self._stretchSide = symbolRectangle.sides[0]
            elif (
                    eventPos.x() == self._rect.right() and self._rect.top() <= eventPos.y() <= self._rect.bottom()):
                self.setCursor(Qt.SizeHorCursor)
                self._stretchSide = symbolRectangle.sides[1]
            elif (
                    eventPos.y() == self._rect.top() and self._rect.left() <= eventPos.x() <= self._rect.right()):
                self.setCursor(Qt.SizeVerCursor)
                self._stretchSide = symbolRectangle.sides[2]
            elif (
                    eventPos.y() == self._rect.bottom() and self._rect.left() <= eventPos.x() <= self._rect.right()):
                self.setCursor(Qt.SizeVerCursor)
                self._stretchSide = symbolRectangle.sides[3]

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        eventPos = event.pos().toPoint()
        if self.stretch:
            self.prepareGeometryChange()
            if self.stretchSide == symbolRectangle.sides[0]:
                self.setCursor(Qt.SizeHorCursor)
                self.rect.setLeft(eventPos.x())
            elif self.stretchSide == symbolRectangle.sides[1]:
                self.setCursor(Qt.SizeHorCursor)
                self.rect.setRight(eventPos.x() - int(self._pen.width() / 2))
            elif self.stretchSide == symbolRectangle.sides[2]:
                self.setCursor(Qt.SizeVerCursor)
                self.rect.setTop(eventPos.y())
            elif self.stretchSide == symbolRectangle.sides[3]:
                self.setCursor(Qt.SizeVerCursor)
                self.rect.setBottom(eventPos.y() - int(self._pen.width() / 2))
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mouseReleaseEvent(event)
        if self.stretch:
            self._stretch = False
            self._stretchSide = None
            self.setCursor(Qt.ArrowCursor)


class symbolCircle(symbolShape):
    def __init__(self, centre: QPoint, end: QPoint):
        super().__init__()
        xlen = abs(end.x() - centre.x())
        ylen = abs(end.y() - centre.y())
        self._radius = int(math.sqrt(xlen ** 2 + ylen ** 2))
        self._centre = centre
        self._topLeft = self._centre - QPoint(self._radius, self._radius)
        self._rightBottom = self._centre + QPoint(self._radius, self._radius)
        self._end = self._centre + QPoint(self._radius, 0)  # along x-axis
        self._stretch = False
        self._startStretch = False

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(symlyr.selectedSymbolPen)
            self.setZValue(symlyr.selectedSymbolLayer.z)
            painter.drawEllipse(self._centre, 1, 1)
            if self._stretch:
                painter.setPen(symlyr.stretchSymbolPen)
                self.setZValue(symlyr.stretchSymbolLayer.z)
        else:
            painter.setPen(symlyr.symbolPen)
            self.setZValue(symlyr.symbolLayer.z)
        painter.drawEllipse(self._centre, self._radius, self._radius)

    def __repr__(self):
        return f"symbolCircle({self._centre},{self._end})"

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, radius: int):
        self.prepareGeometryChange()
        self._radius = radius
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

    def boundingRect(self):
        return (
            QRectF(self._topLeft, self._rightBottom).normalized().adjusted(-2, -2, 2, 2))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if self.isSelected() and self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            eventPos = event.pos().toPoint()
            distance = math.sqrt((eventPos.x() - self._centre.x()) ** 2 + (
                        eventPos.y() - self._centre.y()) ** 2)
            if distance == self._radius:
                self._startStretch = True
                self.setCursor(Qt.DragMoveCursor)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)
        if self._startStretch:
            eventPos = event.pos().toPoint()
            distance = math.sqrt((eventPos.x() - self._centre.x()) ** 2 + (
                        eventPos.y() - self._centre.y()) ** 2)
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


class symbolArc(symbolShape):
    """
    Class to draw arc shapes. Can have four directions.
    """

    arcTypes = ["Up", "Right", "Down", "Left"]
    sides = ["Left", "Right", "Top", "Bottom"]

    def __init__(self, start: QPoint, end: QPoint):
        super().__init__()
        self._start = start
        self._end = end
        self._rect = QRectF(self._start, self._end).normalized()
        self._arcLine = QLineF(self._start, self._end)
        self._arcAngle = 0
        self._width = self._rect.width()
        self._height = self._rect.height()
        self._pen = symlyr.symbolPen
        self._adjustment = int(self._pen.width() / 2)
        self._stretchSide = None
        self._findAngle()
        self._brect = QRectF(0, 0, 0, 0)

    def _findAngle(self):
        self._arcAngle = self._arcLine.angle()
        if 90 >= self._arcAngle >= 0:
            self._arcType = symbolArc.arcTypes[0]
        elif 180 >= self._arcAngle > 90:
            self._arcType = symbolArc.arcTypes[1]
        elif 270 >= self._arcAngle > 180:
            self._arcType = symbolArc.arcTypes[2]
        elif 360 > self._arcAngle > 270:
            self._arcType = symbolArc.arcTypes[3]

    @property
    def arcType(self):
        return self._arcType

    @arcType.setter
    def arcType(self, type: str):
        self.prepareGeometryChange()
        self._arcType = type


    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(symlyr.selectedSymbolPen)
            painter.drawRect(self.bRect)
            self.setZValue(symlyr.selectedSymbolLayer.z)
            if self._stretch:
                painter.setPen(symlyr.stretchSymbolPen)
                self.setZValue(symlyr.stretchSymbolLayer.z)
                if self._stretchSide == symbolArc.sides[0]:
                    painter.drawLine(self._rect.topLeft(), self._rect.bottomLeft())
                elif self._stretchSide == symbolArc.sides[1]:
                    painter.drawLine(self._rect.topRight(), self._rect.bottomRight())
                elif self._stretchSide == symbolArc.sides[2]:
                    painter.drawLine(self._rect.topLeft(), self._rect.topRight())
                elif self._stretchSide == symbolArc.sides[3]:
                    painter.drawLine(self._rect.bottomLeft(), self._rect.bottomRight())
        else:
            painter.setPen(symlyr.symbolPen)
            self.setZValue(symlyr.symbolLayer.z)

        self.arcDraw(painter)

    def arcDraw(self, painter):
        # Define the mapping of arc types to starting angles
        ARC_ANGLES = {
            symbolArc.arcTypes[0]: 0,
            symbolArc.arcTypes[1]: 90,
            symbolArc.arcTypes[2]: 180,
            symbolArc.arcTypes[3]: 270
        }

        # Get the starting angle and draw the arc
        startAngle = ARC_ANGLES.get(self._arcType, 0) * 16
        painter.drawArc(self._rect, startAngle, 180 * 16)

    def boundingRect(self):
        return self.bRect

    @property
    def bRect(self):
        if self._arcType == symbolArc.arcTypes[0]:
            brect = QRectF(QRectF(self._rect.left(), self._rect.top(), self._rect.width(),
                0.5 * self._rect.height(), )).adjusted(-2, -2, 2, 2)
        elif self._arcType == symbolArc.arcTypes[1]:
            brect = QRectF(QRectF(self._rect.left(), self._rect.top(), 0.5 * self._rect.width(),
                self._rect.height(), )).adjusted(-2, -2, 2, 2)
        elif self._arcType == symbolArc.arcTypes[2]:
            brect = QRectF(self._rect.left(), self._rect.top() + self._rect.height() * 0.5,
                self._rect.width(), 0.5 * self._rect.height(), ).adjusted(-2, -2, 2, 2)
        elif self._arcType == symbolArc.arcTypes[3]:
            brect = QRectF(self._rect.left() + 0.5 * self._rect.width(), self._rect.top(),
                           0.5 * self._rect.width(), self._rect.height(), ).adjusted(-2, -2, 2,
                                                                                     2)
        return brect

    @property
    def adjustment(self):
        return self._adjustment

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, arcRect: QRect):
        self._rect = arcRect.normalized()

    def __repr__(self):
        return f"symbolArc({self._start},{self._end})"

    @property
    def start(self) -> QPoint:
        return self._start

    @start.setter
    def start(self, point: QPoint):
        assert isinstance(point, QPoint)
        self.prepareGeometryChange()
        self._start = point

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, point: QPoint):
        self.prepareGeometryChange()
        self._end = point
        self._arcLine = QLineF(self._start, self._end)
        self._arcAngle = self._arcLine.angle()
        self._findAngle()
        self._rect = QRectF(self._start, self._end).normalized()

    @property
    def width(self) -> int:
        return int(self.rect.width())

    @width.setter
    def width(self, width):
        self._width = width
        self.prepareGeometryChange()
        self.rect.setWidth(self._width)

    @property
    def height(self) -> int:
        return int(self.rect.height())

    @height.setter
    def height(self, height: int):
        self._height = height
        self.prepareGeometryChange()
        self.rect.setHeight(self._height)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        eventPos = event.pos().toPoint()
        if self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            if (
                    eventPos.x() == self._rect.left() and self._rect.top() <= eventPos.y() <= self._rect.bottom()):
                self.setCursor(Qt.SizeHorCursor)
                self._stretchSide = symbolArc.sides[0]
            elif (
                    eventPos.x() == self._rect.right() and self._rect.top() <= eventPos.y() <= self._rect.bottom()):
                self.setCursor(Qt.SizeHorCursor)
                self._stretchSide = symbolArc.sides[1]
            elif (
                    eventPos.y() == self._rect.top() and self._rect.left() <= eventPos.x() <= self._rect.right()):
                self.setCursor(Qt.SizeVerCursor)
                self._stretchSide = symbolArc.sides[2]
            elif (
                    eventPos.y() == self._rect.bottom() and self._rect.left() <= eventPos.x() <= self._rect.right()):
                self.setCursor(Qt.SizeVerCursor)
                self._stretchSide = symbolArc.sides[3]

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)

        eventPos = event.pos().toPoint()
        if self._stretch:
            self.prepareGeometryChange()
            if self._stretchSide == symbolArc.sides[0]:
                self.setCursor(Qt.SizeHorCursor)
                self._rect.setLeft(eventPos.x())
            elif self._stretchSide == symbolArc.sides[1]:
                self.setCursor(Qt.SizeHorCursor)
                self._rect.setRight(eventPos.x() - self._adjustment)
            elif self._stretchSide == symbolArc.sides[2]:
                self.setCursor(Qt.SizeVerCursor)
                self._rect.setTop(eventPos.y())
            elif self._stretchSide == symbolArc.sides[3]:
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

            if self._arcType == symbolArc.arcTypes[0]:
                self._start = self._rect.bottomLeft()
                self._end = self._rect.topRight()
            elif self._arcType == symbolArc.arcTypes[1]:
                self._start = self._rect.topLeft()
                self._end = self._rect.bottomRight()
            elif self._arcType == symbolArc.arcTypes[2]:
                self._start = self._rect.topRight()
                self._end = self._rect.bottomLeft()
            elif self._arcType == symbolArc.arcTypes[3]:
                self._start = self._rect.bottomRight()
                self._end = self._rect.topLeft()
            self._rect = QRectF(self._start, self._end).normalized()

class symbolLine(symbolShape):
    stretchSides = ("start", "end")
    _BOUNDING_OFFSET = 10
    _SHAPE_OFFSET = 2
    _ELLIPSE_SIZE = 2

    def __init__(self, start: QPoint, end: QPoint):
        super().__init__()
        self._end = end
        self._start = start
        self._stretch = False
        self._stretchSide = None
        self._pen = symlyr.symbolPen
        self._updateGeometry()
        self._horizontal = True

    def __repr__(self):
        return f"symbolLine({self._start}, {self._end})"

    def _updateGeometry(self):
        self._line = QLine(self._start, self._end)
        self._rect = QRect(self._start, self._end).normalized()

    def boundingRect(self):
        return self._rect.adjusted(-self._BOUNDING_OFFSET, -self._BOUNDING_OFFSET,
                                   self._BOUNDING_OFFSET, self._BOUNDING_OFFSET)

    def shape(self):
        path = QPainterPath()
        path.addRect(self._rect.adjusted(-self._SHAPE_OFFSET, -self._SHAPE_OFFSET,
                                         self._SHAPE_OFFSET, self._SHAPE_OFFSET))
        return path

    def paint(self, painter, option, widget):
        is_selected = self.isSelected()
        if is_selected:
            painter.setPen(symlyr.selectedSymbolPen)
            self.setZValue(symlyr.symbolLayer.z)

            if self._stretch:
                painter.setPen(symlyr.stretchSymbolPen)
                self.setZValue(symlyr.stretchSymbolLayer.z)
                # Draw stretch handles
                painter.drawEllipse(self._start, self._ELLIPSE_SIZE, self._ELLIPSE_SIZE)
                painter.drawEllipse(self._end, self._ELLIPSE_SIZE, self._ELLIPSE_SIZE)
        else:
            painter.setPen(symlyr.symbolPen)
            self.setZValue(symlyr.symbolLayer.z)

        painter.drawLine(self._line)

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start: QPoint):
        if start != self._start:  # Only update if changed
            self.prepareGeometryChange()
            self._start = start
            self._updateGeometry()

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end: QPoint):
        if end != self._end:  # Only update if changed
            self.prepareGeometryChange()
            self._end = end
            self._updateGeometry()

    @property
    def length(self):
        dx = self.start.x() - self._end.x()
        dy = self.start.y() - self._end.y()
        return math.hypot(dx, dy)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if self.isSelected() and self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            eventPos = event.pos().toPoint()
            # Check if click is near start or end point
            if (eventPos - self._start).manhattanLength() <= 2:
                self._stretchSide = "start"
            elif (eventPos - self._end).manhattanLength() <= 2:
                self._stretchSide = "end"
            else:
                self._stretchSide = None

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._stretchSide:
            self.prepareGeometryChange()
            eventPos = event.pos().toPoint()

            if self._stretchSide == "start":
                self._start = eventPos
            else:
                self._end = eventPos

            self._updateGeometry()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self._stretchSide = None
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mouseReleaseEvent(event)


class symbolPolygon(symbolShape):
    _NO_SELECTION = 999  # Constant for no selection
    _DEFAULT_CORNER = QPoint(99999, 99999)  # Constant for default corner
    _CORNER_SIZE = 5  # Size of corner markers

    def __init__(self, points: list):
        super().__init__()
        self._points = points
        self._polygon = QPolygonF(self._points)
        self._selectedCorner = QPoint(0, 0)
        self._selectedCornerIndex = self._NO_SELECTION
        self.setZValue(symlyr.symbolLayer.z)

    def __repr__(self):
        return f"symbolPolygon({self._points})"

    def paint(self, painter, option, widget):
        is_selected = self.isSelected()
        painter.setPen(symlyr.selectedSymbolPen if is_selected else symlyr.symbolPen)

        # Draw corner marker if in stretch mode and corner is selected
        if is_selected and self._stretch and self._selectedCorner != self._DEFAULT_CORNER:
            painter.drawEllipse(self._selectedCorner, self._CORNER_SIZE, self._CORNER_SIZE)

        painter.drawPolygon(self._polygon)

    def boundingRect(self) -> QRectF:
        return self._polygon.boundingRect()

    @property
    def polygon(self):
        return self._polygon

    @property
    def points(self) -> list:
        return self._points

    @points.setter
    def points(self, value: list):
        if value != self._points:  # Only update if points actually changed
            self.prepareGeometryChange()
            self._points = value
            self._updatePolygon()

    def _updatePolygon(self):
        self._polygon = QPolygonF(self._points)

    def addPoint(self, point: QPoint):
        self.prepareGeometryChange()
        self._points.append(point)
        self._updatePolygon()

    @property
    def tempLastPoint(self):
        return self._points[-1]

    @tempLastPoint.setter
    def tempLastPoint(self, value: QPoint):
        self.prepareGeometryChange()
        self._polygon = QPolygonF([*self._points, value])

    def _findNearestPoint(self, eventPos: QPoint) -> tuple[int, QPoint]:
        """Find the nearest point to the event position"""
        for i, point in enumerate(self._points):
            if (eventPos - point).manhattanLength() <= self.scene().snapDistance:
                return i, point
        return self._NO_SELECTION, None

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            eventPos = event.pos().toPoint()
            index, point = self._findNearestPoint(eventPos)
            if point is not None:
                self._selectedCorner = point
                self._selectedCornerIndex = index

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._stretch and self._selectedCornerIndex != self._NO_SELECTION:
            eventPos = event.pos().toPoint()
            self._points[self._selectedCornerIndex] = eventPos
            self.prepareGeometryChange()
            self._updatePolygon()
            self._selectedCorner = eventPos
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        if self.stretch:
            self._resetStretchState()

    def _resetStretchState(self):
        """Reset the stretch state of the polygon"""
        self._stretch = False
        self._stretchSide = None
        self.setCursor(Qt.ArrowCursor)
        self._selectedCorner = self._DEFAULT_CORNER
        self._selectedCornerIndex = self._NO_SELECTION


class symbolPin(symbolShape):
    """
    symbol pin class definition for symbol drawing.
    """
    PIN_HEIGHT = 10
    PIN_WIDTH = 10
    TEXT_MARGIN = 5

    pinDirs = ["Input", "Output", "Inout"]
    pinTypes = ["Signal", "Ground", "Power", "Clock", "Digital", "Analog"]

    def __init__(self, start: QPoint, pinName: str, pinDir: str, pinType: str, ):
        super().__init__()

        self._start = start  # centre of pin
        self._pinName = pinName
        self._pinDir = pinDir
        self._pinType = pinType
        self._connected = False  # True if the pin is connected to a net.
        self._highlighted = False
        self._pinRectItem = QGraphicsRectItem(QRect(self._start.x() - self.PIN_WIDTH / 2,
                                                    self._start.y() - self.PIN_HEIGHT / 2,
                                                    self.PIN_WIDTH, self.PIN_HEIGHT))
        self._pinRectItem.setPen(symlyr.symbolPinPen)
        self._pinRectItem.setBrush(symlyr.symbolPinBrush)
        self._pinRectItem.setParentItem(self)
        self._pinRect = self._pinRectItem.rect().adjusted(-2, -2, 2, 2)
        self._pinNameItem = QGraphicsSimpleTextItem(self._pinName)
        self._font = QFont("Arial", 14)
        # textBoundingRectHeight = self._pinNameItem.boundingRect().height()
        self._pinNameItem.setFont(self._font)
        self._pinNameItem.setPos(self._start.x() - self.PIN_WIDTH / 2,
                                 self._start.y() - self.PIN_HEIGHT / 2 + self.TEXT_MARGIN)
        self._pinNameItem.setBrush(symlyr.symbolPinBrush)
        # self._pinNameItem.setDefaultTextColor(pdk.symLayers.symbolPinLayer.bcolor)
        self._pinNameItem.setParentItem(self)
        self.setFiltersChildEvents(True)
        self.setHandlesChildEvents(True)
        self.setFlag(QGraphicsItem.ItemContainsChildrenInShape, True)

    def __str__(self):
        return f"symbolPin: {self._pinName} {self.mapToScene(self._start)}"

    def boundingRect(self):
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget):
        pass

    def __repr__(self):
        return f"pin({self._start},{self._pinName}, {self._pinDir}, {self._pinType})"

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.setSelected(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSceneHasChanged:
            # The scene change is complete
            if self.scene().__class__.__name__ == 'schematicScene':
                self._pinNameItem.setVisible(False)
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            if value:
                self.scene().selectedSymbolPin = self
            else:
                self.scene().selectedSymbolPin = None
        return super().itemChange(change, value)

    def shape(self):
        path = QPainterPath()
        path.addRect(self._pinRect)
        return path

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self.prepareGeometryChange()
        self._start = start
        self._pinRectItem = QGraphicsRectItem(QRect(self._start.x() - self.PIN_WIDTH / 2,
                                                    self._start.y() - self.PIN_HEIGHT / 2,
                                                    self.PIN_WIDTH, self.PIN_HEIGHT), self)
        self._pinRect = self._pinRectItem.rect()

    @property
    def pinName(self):
        return self._pinName

    @pinName.setter
    def pinName(self, pinName):
        if pinName != "":
            self.prepareGeometryChange()
            self._pinName = pinName

    @property
    def pinDir(self):
        return self._pinDir

    @pinDir.setter
    def pinDir(self, direction: str):
        if direction in symbolPin.pinDirs:
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

    @property
    def highlighted(self):
        return self._highlighted

    @highlighted.setter
    def highlighted(self, value: bool):
        if isinstance(value, bool):
            self._highlighted = value

    def toSchematicPin(self, start: QPoint):
        return schematicPin(start, self.pinName, self.pinDir, self.pinType)


class text(symbolShape):
    """
    This class is for text annotations on symbol or schematics.
    """

    textAlignments = ["Left", "Center", "Right"]
    textOrients = ["R0", "R90", "R180", "R270"]

    def __init__(self, start: QPoint, textContent: str, fontFamily: str, fontStyle: str,
                 textHeight: str, textAlign: str, textOrient: str, ):
        super().__init__()
        self._start = start
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
        self.setOrient()
        if self._textAlign == text.textAlignments[0]:
            self._textOptions.setAlignment(Qt.AlignmentFlag.AlignLeft)
        elif self._textAlign == text.textAlignments[1]:
            self._textOptions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        elif self._textAlign == text.textAlignments[2]:
            self._textOptions.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._rect = self._fm.boundingRect(QRect(0, 0, 400, 400),
                                           Qt.AlignmentFlag.AlignCenter, self._textContent)

    def __repr__(self):
        return (f"text({self._start},{self._textContent}, {self._textFont.family()},"
                f" {self._textFont.style()}, {self._textHeight}, {self._textAlign},"
                f"{self._textOrient})")

    def setOrient(self):
        if self._textOrient == text.textOrients[0]:
            self.setRotation(0)
        elif self._textOrient == text.textOrients[1]:
            self.setRotation(90)
        elif self._textOrient == text.textOrients[2]:
            self.setRotation(180)
        elif self._textOrient == text.textOrients[3]:
            self.setRotation(270)
        elif self._textOrient == text.textOrients[4]:
            self.flip("x")
        elif self._labelOrient == text.textOrients[5]:
            self.flip("x")
            self.setRotation(90)
        elif self._labelOrient == text.textOrients[6]:
            self.flip("y")
            self.setRotation(90)

    def flip(self, direction: str):
        currentTransform = self.transform()
        newTransform = QTransform()
        if direction == "x":
            currentTransform = newTransform.scale(-1, 1) * currentTransform
        elif direction == "y":
            currentTransform = newTransform.scale(1, -1) * currentTransform
        self.setTransform(currentTransform)

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
                     self._rect.width(), self._rect.height(), ).normalized().adjusted(-2,
                                                                                      -2, 2,
                                                                                      2)

    def paint(self, painter, option, widget):
        painter.setFont(self._textFont)
        if self.isSelected():
            painter.setPen(schlyr.selectedTextPen)
            painter.drawRect(self.boundingRect().adjusted(2, 2, -2, -2))
            self.setZValue(schlyr.selectedTextLayer.z)
        else:
            painter.setPen(schlyr.textPen)
            self.setZValue(schlyr.textLayer.z)
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
    def textHeight(self) -> str:
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


class schematicSymbol(symbolShape):
    def __init__(self, shapes: list, attr: dict):
        super().__init__()
        self._shapes = shapes  # list of shapes in the symbol
        self._symattrs = attr  # parameters common to all instances of symbol
        self._counter = 0  # item's number on schematic
        self._libraryName = ""
        self._cellName = ""
        self._viewName = ""
        self._instanceName = ""
        self._netlistLine = ""
        self._labels: Dict[str, symbolLabel] = dict()  # dict of labels
        self._pins: Dict[str, symbolPin] = dict()  # dict of pins
        self._netlistIgnore: bool = False
        self._draft: bool = False
        self._pinLocations: dict[str, Union[QRect, QRectF]] = dict()  # pinName: pinRect
        self.pinNetMap: dict[str, str] = dict()  # pinName: netName
        self._pinNetIndexTupleSet: set[pinNetIndexTuple] = set()
        self._snapLines: dict[symbolPin, set[net.schematicNet]] = dict()
        self._shapeRectF = QRectF(0, 0, 0, 0)
        self._borderRect = QRect(0, 0, 0, 0)
        self.addShapes()
        self.setFiltersChildEvents(True)
        self.setHandlesChildEvents(True)
        self.setFlag(QGraphicsItem.ItemContainsChildrenInShape, True)
        self._start = self.childrenBoundingRect().bottomLeft()

    def addShapes(self):
        for item in self._shapes:
            item.setFlag(QGraphicsItem.ItemIsSelectable, False)
            item.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
            item.setParentItem(self)
            if type(item) is symbolPin:
                self._pins[item.pinName] = item
            elif type(item) is symbolLabel:
                self._labels[item.labelName] = item

    def __repr__(self):
        return f"schematicSymbol({self._instanceName})"

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if self.scene():
            if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
                return self._handlePositionChange(value)
            elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
                self._updateSnapLines()
            elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
                self.scene().selectedSymbol = self if value else None
        return super().itemChange(change, value)

    def _handlePositionChange(self, newPos: QPointF) -> QPointF:

        if self._snapLines is None:
            self._initializeSnapLines()
        else:
            self._updateSnapLines()
        return newPos

    def _initializeSnapLines(self):
        self._snapLines: Dict[QGraphicsItem, Set[net.guideLine]] = {}
        pin_net_tuples = self.findPinNetIndexTuples()

        if not pin_net_tuples:
            return None

        scene = self.scene()  # Cache scene reference

        # Pre-allocate sets for all pins
        uniquePins = {item.pin for item in pin_net_tuples}
        self._snapLines.update({pin: set() for pin in uniquePins})

        # Batch process all items
        for item in pin_net_tuples:
            startPoint = item.pin.mapToScene(item.pin.start).toPoint()
            endPoint = item.net.sceneEndPoints[item.netEndIndex - 1]

            if startPoint == endPoint:
                scene.removeItem(item.net)
                continue

            # Create and configure snap line
            snapLine = net.guideLine(startPoint, endPoint)
            snapLine.inherit(item.net)

            # Batch scene operations
            scene.addItem(snapLine)
            scene.removeItem(item.net)

            # Add to existing set
            self._snapLines[item.pin].add(snapLine)

    def _updateSnapLines(self):
        if self._snapLines is None:
            return

        for pin, snapLinesSet in self._snapLines.items():
            pin_start = pin.mapToScene(pin.start)
            for snapLine in list(
                    snapLinesSet):  # Create a copy to safely modify during iteration
                current_end = snapLine.line().p2()
                new_line = QLineF(pin_start, current_end)

                # Only update if there's a significant change
                if (new_line.length() > 1 and  # Avoid very short lines
                        (abs(new_line.dx()) > 1 or abs(
                            new_line.dy()) > 1)):  # Avoid unnecessary updates
                    snapLine.setLine(new_line)
                else:
                    # Remove unnecessary lines
                    self.scene().removeItem(snapLine)
                    snapLinesSet.remove(snapLine)

        # Clean up empty sets
        self._snapLines = {pin: lines for pin, lines in self._snapLines.items() if lines}

    def paint(self, painter, option, widget):
        self.setZValue(symlyr.symbolLayer.z)
        if self._draft:
            painter.setPen(symlyr.draftPen)
            self.setZValue(symlyr.draftLayer.z)
        if self.isSelected():
            painter.setPen(symlyr.selectedSymbolPen)
            painter.drawRect(self.boundingRect())
            self.setZValue(symlyr.selectedSymbolLayer.z)
        else:
            self.setZValue(symlyr.symbolLayer.z)
        if self.netlistIgnore:
            painter.setPen(schlyr.ignoreSymbolPen)
            painter.drawLine(self.boundingRect().bottomLeft(),
                             self.boundingRect().topRight())
            painter.drawLine(self.boundingRect().topLeft(),
                             self.boundingRect().bottomRight())

    def boundingRect(self):
        return self.childrenBoundingRect()

    def findPinNetIndexTuples(self):
        """
        Find all pin-net-index tuples in the schematic.

        Returns:
            set: A set of pinNetIndexTuple objects representing pin-net connections.
        """

        def findConnectionIndex(pinRect, netEndpoints):
            """Helper function to find the connection index between a pin and net endpoints."""
            for index, endpoint in enumerate(netEndpoints):
                if pinRect.contains(endpoint):
                    return index
            return None

        pinNetTuples = set()
        scene = self.scene()

        for pin in self._pins.values():
            pinRect = pin.sceneBoundingRect()

            # Get all schematic nets in pin's area
            netItems = [item for item in scene.items(pinRect) if
                        isinstance(item, net.schematicNet)]

            # Process each net
            for netItem in netItems:
                connectionIndex = findConnectionIndex(pinRect, netItem.sceneEndPoints)

                if connectionIndex is not None:
                    pinNetTuples.add(pinNetIndexTuple(pin, netItem, connectionIndex))

        return pinNetTuples

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        # Check if the click is on any of the pins
        for pin in self._pins.values():
            if pin.contains(self.mapToItem(pin, event.pos())):
                self.scene().selectedSymbolPin = pin
                pin.highlighted = True
                # You can handle the pin click here, or pass the event to the pin
                pin.mousePressEvent(event)
                return  # Stop processing after handling pin click
        self._snapLines = None
        # If not on a pin, handle as normal
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
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

    # TODO: figure out what is wrong here
    @instanceName.setter
    def instanceName(self, value: str):
        """
        If instance name is changed and [@instName] label exists, change it too.
        """
        self._instanceName = value
        if self.labels.get("instanceName", None):
            self.labels["instanceName"].labelValue = value
            self.labels["instanceName"].update()

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
        self._angle = value  # for label in self.labels.values():  #     label.angle = -value

    @property
    def labels(self):
        return self._labels  # dictionary

    @cached_property
    def pins(self):
        if self.symattrs.get("pinOrder"):
            pinOrderList = self.symattrs.get("pinOrder").split(",")
            orderedPins = {key.strip(): self._pins[key.strip()] for key in pinOrderList}
            return orderedPins
        else:
            return self._pins

    @property
    def shapes(self):
        return self._shapes

    @shapes.setter
    def shapes(self, shapeList: list):
        self.prepareGeometryChange()
        self._shapes = shapeList
        self.addShapes()

    @property
    def symattrs(self):
        return self._symattrs

    @symattrs.setter
    def symattrs(self, attrDict: dict):
        self._symattrs = attrDict

    @property
    def netlistIgnore(self) -> bool:
        return self._netlistIgnore

    @netlistIgnore.setter
    def netlistIgnore(self, value: bool):
        assert isinstance(value, bool)
        self._netlistIgnore = value

    @property
    def flipTuple(self):
        return self._flipTuple

    @flipTuple.setter
    def flipTuple(self, flipState: Tuple[int, int]):
        self.prepareGeometryChange()
        # Get the current transformation
        transform = self.transform()
        # Apply the scaling
        transform.scale(*flipState)
        # Set the new transformation
        self.setTransform(transform)
        self._flipTuple = (transform.m11(), transform.m22())
        labelTransform, invertible = transform.inverted()
        if invertible:
            for label in self.labels.values():
                label.setTransform(labelTransform)
        self.update()

    @property
    def start(self):
        return self._start.toPoint()


class schematicPinPolygon(QGraphicsPolygonItem):
    def __init__(self, polygon: Union[QPolygonF, QPolygon], parent: QGraphicsScene):
        self._polygon = polygon
        self._parent = parent
        super().__init__(self._polygon, self._parent)

    def paint(self, painter, option, widget=...):
        if self.isSelected():
            painter.setPen(schlyr.selectedSchematicPinPen)
            painter.setBrush(schlyr.selectedSchematicPinBrush)
        else:
            painter.setPen(schlyr.schematicPinPen)
            painter.setBrush(schlyr.schematicPinBrush)
        painter.drawPolygon(self._polygon)


class schematicPin(symbolShape):
    """
    schematic pin class.
    """

    pinDirs = ["Input", "Output", "Inout"]
    pinTypes = ["Signal", "Ground", "Power", "Clock", "Digital", "Analog"]
    PIN_WIDTH = 40
    PIN_HEIGHT = 20
    TEXT_MARGIN = 10

    def __init__(self, start: QPoint, pinName: str, pinDir: str, pinType: str, ):
        super().__init__()
        self._start = start
        self._pinName = pinName
        self._pinDir = pinDir
        self._pinType = pinType
        self._pinNetIndexTupleSet = set()
        self._snapLines = dict()
        self._font = QFont("Arial", 12)
        self._updateTextMetrics()
        self._pinItem = schematicPinPolygon(self.pinPolygon, self)
        centre = self._pinItem.boundingRect().center()
        self._textItem = QGraphicsSimpleTextItem(self._pinName, self)
        self._textItem.setFont(self._font)
        self._textItem.setPos(centre.x(), centre.y())
        self._textItem.setBrush(QBrush(schlyr.schematicPinNameLayer.bcolor))
        self.setFiltersChildEvents(True)
        self.setHandlesChildEvents(True)
        self.setFlag(QGraphicsItem.ItemContainsChildrenInShape, True)
        self.flipTuple = (1, 1)

    def _updateTextMetrics(self):
        self.metrics = QFontMetrics(self._font)  # self._textHeight = self.metrics.height()

    def setFont(self, font):
        self._font = font
        self._updateTextMetrics()
        self.prepareGeometryChange()

    def __repr__(self):
        return (f"schematicPin({self._start}, {self._pinName}, {self._pinDir}, "
                f"{self._pinType})")

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(schlyr.selectedSchematicPinPen)
            painter.drawRect(self.childrenBoundingRect())
        self.setZValue(schlyr.schematicPinLayer.z)

    @property
    def pinPolygon(self):
        match self.pinDir:
            case "Input":
                return QPolygonF([QPoint(self._start.x() - self.PIN_HEIGHT / 2,
                                         self._start.y() - self.PIN_HEIGHT / 2),
                                  QPoint(self._start.x() + self.PIN_HEIGHT / 2,
                                         self._start.y() - self.PIN_HEIGHT / 2),
                                  QPoint(self._start.x() + self.PIN_WIDTH / 2,
                                         self._start.y()),
                                  QPoint(self._start.x() + self.PIN_HEIGHT / 2,
                                         self._start.y() + self.PIN_HEIGHT / 2),
                                  QPoint(self._start.x() - self.PIN_HEIGHT / 2,
                                         self._start.y() + self.PIN_HEIGHT / 2), ])
            case "Output":
                return QPolygonF(
                    [QPoint(self._start.x() - self.PIN_WIDTH / 2, self._start.y()),
                     QPoint(self._start.x() - self.PIN_HEIGHT / 2,
                            self._start.y() - self.PIN_HEIGHT / 2),
                     QPoint(self._start.x() + self.PIN_HEIGHT / 2,
                            self._start.y() - self.PIN_HEIGHT / 2),
                     QPoint(self._start.x() + self.PIN_HEIGHT / 2,
                            self._start.y() + self.PIN_HEIGHT / 2),
                     QPoint(self._start.x() - self.PIN_HEIGHT / 2,
                            self._start.y() + self.PIN_HEIGHT / 2), ])
            case "Inout":
                return QPolygonF(
                    [QPoint(self._start.x() - self.PIN_WIDTH / 2, self._start.y()),
                     QPoint(self._start.x() - self.PIN_HEIGHT / 2,
                            self._start.y() - self.PIN_HEIGHT / 2),
                     QPoint(self._start.x() + self.PIN_HEIGHT / 2,
                            self._start.y() - self.PIN_HEIGHT / 2),
                     QPoint(self._start.x() + self.PIN_WIDTH / 2, self._start.y()),
                     QPoint(self._start.x() + self.PIN_HEIGHT / 2,
                            self._start.y() + self.PIN_HEIGHT / 2),
                     QPoint(self._start.x() - self.PIN_HEIGHT / 2,
                            self._start.y() + self.PIN_HEIGHT / 2), ])

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if value:
                self.scene().selectedPin = self
            else:
                self.scene().selectedPin = None
        return super().itemChange(change, value)

    def boundingRect(self):
        return self.childrenBoundingRect()

    def shape(self):
        path = QPainterPath()
        # Add a shape for the pin
        pin_rect = QRect(self._start.x() - self.PIN_WIDTH / 2,
                         self._start.y() - self.PIN_HEIGHT / 2, self.PIN_WIDTH,
                         self.PIN_HEIGHT).normalized().adjusted(-5, -5, 5, 5)

        path.addRect(pin_rect)
        return path

    def findPinNetIndexTuples(self) -> List[Tuple['schematicPin', 'net.schematicNet', int]]:
        # Use a list instead of a set for better performance if order doesn't matter
        self._pinNetIndexTupleSet = []

        # Create a slightly larger rectangle around the pin for collision detection
        pin_rect = QRectF(self._start.x() - 5, self._start.y() - 5, 10, 10)
        pin_scene_rect = self.mapRectToScene(pin_rect)

        # Use a QPainterPath for more accurate collision detection
        pin_path = QPainterPath()
        pin_path.addRect(pin_scene_rect)

        # Find all items that collide with the pin's path
        colliding_items = self.scene().items(pin_path)

        # Filter for SchematicNet items and process them
        for item in colliding_items:
            if isinstance(item, net.schematicNet):
                for index, end_point in enumerate(item.sceneEndPoints):
                    if pin_scene_rect.contains(end_point):
                        self._pinNetIndexTupleSet.append(
                            pinNetIndexTuple(self, item, index))
                        break  # Assume only one end of a net can connect to a pin

        return self._pinNetIndexTupleSet

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        self.findPinNetIndexTuples()
        for tupleItem in self._pinNetIndexTupleSet:
            self._snapLines = set()
            snapLine = net.guideLine(self.mapToScene(self.start),
                                     tupleItem.net.sceneEndPoints[
                                         tupleItem.netEndIndex - 1], )
            snapLine.inherit(tupleItem.net)

            self.scene().addItem(snapLine)
            self._snapLines.add(snapLine)
            self.scene().removeItem(tupleItem.net)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        lines: list[net.schematicNet] = []
        if hasattr(self, "snapLines"):
            for snapLine in self._snapLines:
                lines = self.scene().addStretchWires(self.mapToScene(self.start).toPoint(),
                                                     snapLine.mapToScene(
                                                         snapLine.line().p2()).toPoint(), )
                if lines:
                    for line in lines:
                        line.inheritGuideLine(snapLine)
                    self.scene().addListUndoStack(lines)
                self.scene().removeItem(snapLine)
        self._snapLines = dict()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)
        if self._snapLines:
            for snapLine in self._snapLines:
                snapLine.setLine(QLineF(snapLine.mapFromScene(self.mapToScene(self.start)),
                                        snapLine.line().p2(), ))

    def toSymbolPin(self, start: QPoint):
        return symbolPin(start, self.pinName, self.pinDir, self.pinType)

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

    @property
    def flipTuple(self):
        return self._flipTuple

    @flipTuple.setter
    def flipTuple(self, flipState: Tuple[int, int]):
        self.prepareGeometryChange()
        # Get the current transformation
        transform = self._pinItem.transform()
        # Apply the scaling
        polygonStart = self._pinItem.boundingRect().center().toPoint()
        transform.translate(polygonStart.x(), polygonStart.y())
        transform.scale(*flipState)
        self._flipTuple = (transform.m11(), transform.m22())
        transform.translate(-polygonStart.x(), -polygonStart.y())
        # textTransform, invertible =transform.inverted()
        # if invertible:
        #     textTransform.translate(self.PIN_WIDTH*0.5*self._flipTuple[0],self.PIN_HEIGHT*0.5*self._flipTuple[1])
        #     self._textItem.setTransform(textTransform)

        # Set the new transformation
        self._pinItem.setTransform(transform, combine=False)


class pinNetIndexTuple(NamedTuple):
    pin: Union[symbolPin, schematicPin]
    net: net.schematicNet
    netEndIndex: int
