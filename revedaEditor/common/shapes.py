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

from PySide6.QtCore import (
    QPoint,
    QRect,
    QRectF,
    Qt,
    QLine,
    QLineF,
)
from PySide6.QtGui import (
    QBrush,
    QFont,
    QFontMetrics,
    QPainterPath,
    QTextOption,
    QFontDatabase,
    QTransform,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
)
from typing import (
    Union,
    NamedTuple,
)

import os
from dotenv import load_dotenv
load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):
    import pdk.symLayers as symlyr
    import pdk.schLayers as schlyr
else:
    import defaultPDK.symLayers as symlyr
    import defaultPDK.schLayers as schlyr

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
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mousePressEvent(event)

    def sceneEvent(self, event):
        """
        Do not propagate event if shape needs to keep still.
        """
        if self.scene().editModes.changeOrigin or self.scene().drawMode:
            return False
        else:
            super().sceneEvent(event)
            return True

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
        self.scene().itemContextMenu.exec_(event.screenPos())


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
        return QPoint(
            int(self._rect.x() + self._rect.width() / 2),
            int(self._rect.y() + self._rect.height() / 2),
        )

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
                eventPos.x() == self._rect.left()
                and self._rect.top() <= eventPos.y() <= self._rect.bottom()
            ):
                self.setCursor(Qt.SizeHorCursor)
                self._stretchSide = symbolRectangle.sides[0]
            elif (
                eventPos.x() == self._rect.right()
                and self._rect.top() <= eventPos.y() <= self._rect.bottom()
            ):
                self.setCursor(Qt.SizeHorCursor)
                self._stretchSide = symbolRectangle.sides[1]
            elif (
                eventPos.y() == self._rect.top()
                and self._rect.left() <= eventPos.x() <= self._rect.right()
            ):
                self.setCursor(Qt.SizeVerCursor)
                self._stretchSide = symbolRectangle.sides[2]
            elif (
                eventPos.y() == self._rect.bottom()
                and self._rect.left() <= eventPos.x() <= self._rect.right()
            ):
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
        self._radius = int(math.sqrt(xlen**2 + ylen**2))
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
            QRectF(self._topLeft, self._rightBottom).normalized().adjusted(-2, -2, 2, 2)
        )

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if self.isSelected() and self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            eventPos = event.pos().toPoint()
            distance = math.sqrt(
                (eventPos.x() - self._centre.x()) ** 2
                + (eventPos.y() - self._centre.y()) ** 2
            )
            if distance == self._radius:
                self._startStretch = True
                self.setCursor(Qt.DragMoveCursor)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)
        if self._startStretch:
            eventPos = event.pos().toPoint()
            distance = math.sqrt(
                (eventPos.x() - self._centre.x()) ** 2
                + (eventPos.y() - self._centre.y()) ** 2
            )
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
        if self._arcType == symbolArc.arcTypes[0]:
            painter.drawArc(self._rect, 0, 180 * 16)
        elif self._arcType == symbolArc.arcTypes[1]:
            painter.drawArc(self._rect, 90 * 16, 180 * 16)
        elif self._arcType == symbolArc.arcTypes[2]:
            painter.drawArc(self._rect, 180 * 16, 180 * 16)
        elif self._arcType == symbolArc.arcTypes[3]:
            painter.drawArc(self._rect, 270 * 16, 180 * 16)

    def boundingRect(self):
        return self.bRect


    @property
    def bRect(self):
        if self._arcType == symbolArc.arcTypes[0]:
            brect = QRectF(
                QRectF(
                    self._rect.left(),
                    self._rect.top(),
                    self._rect.width(),
                    0.5 * self._rect.height(),
                )
            ).adjusted(-2, -2, 2, 2)
        elif self._arcType == symbolArc.arcTypes[1]:
            brect = QRectF(
                QRectF(
                    self._rect.left(),
                    self._rect.top(),
                    0.5 * self._rect.width(),
                    self._rect.height(),
                )
            ).adjusted(-2, -2, 2, 2)
        elif self._arcType == symbolArc.arcTypes[2]:
            brect =  QRectF(
                self._rect.left(),
                self._rect.top() + self._rect.height() * 0.5,
                self._rect.width(),
                0.5 * self._rect.height(),
            ).adjusted(-2, -2, 2, 2)
        elif self._arcType == symbolArc.arcTypes[3]:
            brect = QRectF(
                self._rect.left() + 0.5 * self._rect.width(),
                self._rect.top(),
                0.5 * self._rect.width(),
                self._rect.height(),
            ).adjusted(-2, -2, 2, 2)
        return brect

    @property
    def adjustment(self):
        return self._adjustment
    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, arc_rect: QRect):
        assert isinstance(arc_rect, QRect)
        self._rect = arc_rect.normalized()

    def __repr__(self):
        return f"symbolArc({self._start},{self._end})"

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, point: QPoint):
        assert isinstance(point, QPoint)
        self.prepareGeometryChange()
        self._start = (point,)

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
        self._findAngle()
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
    def height(self) -> int:
        return self._height

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
                eventPos.x() == self._rect.left()
                and self._rect.top() <= eventPos.y() <= self._rect.bottom()
            ):
                self.setCursor(Qt.SizeHorCursor)
                self._stretchSide = symbolArc.sides[0]
            elif (
                eventPos.x() == self._rect.right()
                and self._rect.top() <= eventPos.y() <= self._rect.bottom()
            ):
                self.setCursor(Qt.SizeHorCursor)
                self._stretchSide = symbolArc.sides[1]
            elif (
                eventPos.y() == self._rect.top()
                and self._rect.left() <= eventPos.x() <= self._rect.right()
            ):
                self.setCursor(Qt.SizeVerCursor)
                self._stretchSide = symbolArc.sides[2]
            elif (
                eventPos.y() == self._rect.bottom()
                and self._rect.left() <= eventPos.x() <= self._rect.right()
            ):
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
    """
    line class definition for symbol drawing.
    """

    stretchSides = ["start", "end"]

    def __init__(
        self,
        start: QPoint,
        end: QPoint,
    ):
        super().__init__()
        self._end = end
        self._start = start
        self._stretch = False
        self._stretchSide = None
        self._pen = symlyr.symbolPen
        self._line = QLine(self._start, self._end)
        self._rect = QRect(self._start, self._end).normalized()
        self._horizontal = True  # True if line is horizontal, False if vertical

    def boundingRect(self):
        return self._rect.adjusted(-2, -2, 2, 2)

    def shape(self):
        path = QPainterPath()
        path.addRect(self._rect.adjusted(-2, -2, 2, 2))
        return path

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(symlyr.selectedSymbolPen)
            self.setZValue(symlyr.symbolLayer.z)
            if self._stretch:
                painter.setPen(symlyr.stretchSymbolPen)
                self.setZValue(symlyr.stretchSymbolLayer.z)
                if self._stretchSide == symbolLine.stretchSides[0]:
                    painter.drawEllipse(self._start, 2, 2)
                elif self._stretchSide == symbolLine.stretchSides[1]:
                    painter.drawEllipse(self._end, 2, 2)
        else:
            painter.setPen(symlyr.symbolPen)
            self.setZValue(symlyr.symbolLayer.z)
        painter.drawLine(self._line)

    def __repr__(self):
        return f"symbolLine({self._start},{self._end})"

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
            (self.start.x() - self._end.x()) ** 2
            + (self.start.y() - self._end.y()) ** 2
        )

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if self.isSelected() and self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            eventPos = event.pos().toPoint()
            if eventPos == self.start:
                self._stretchSide = symbolLine.stretchSides[0]
            elif eventPos == self._end:
                self._stretchSide = symbolLine.stretchSides[1]

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        eventPos = event.pos().toPoint()
        if self._stretchSide == symbolLine.stretchSides[0]:
            self.prepareGeometryChange()
            self.start = eventPos
            self._line = QLine(self.start, self._end)
            self._rect = QRect(self.start, self._end).normalized()
        elif self._stretchSide == symbolLine.stretchSides[1]:
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


class symbolPolygon(symbolShape):
    def __init__(self, points: list):
        super().__init__()
        self._points = points
        self._polygon = QPolygonF(self._points)
        self._selectedCorner = QPoint(0,0)
        self._selectedCornerIndex = 999
        self.setZValue(symlyr.symbolLayer.z)

    def __repr__(self):
        return f"symbolPolygon({self._points})"


    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(symlyr.selectedSymbolPen)
            if self._stretch and self._selectedCorner != QPoint(99999, 99999):
                painter.drawEllipse(self._selectedCorner, 5, 5)
        else:
            painter.setPen(symlyr.symbolPen)

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
        self.prepareGeometryChange()
        self._points = value
        self._polygon = QPolygonF(self._points)

    def addPoint(self, point: QPoint):
        self.prepareGeometryChange()
        self._points.append(point)
        self._polygon = QPolygonF(self._points)

    @property
    def tempLastPoint(self):
        return self._points[-1]

    @tempLastPoint.setter
    def tempLastPoint(self, value: QPoint):
        self.prepareGeometryChange()
        self._polygon = QPolygonF([*self._points, value])

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        eventPos = event.pos().toPoint()
        if self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            for point in self._points:
                if (eventPos - point).manhattanLength() <= self.scene().snapDistance:
                    self._selectedCorner = point
                    self._selectedCornerIndex = self._points.index(point)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        eventPos = event.pos().toPoint()
        if self._stretch and self._selectedCornerIndex != 999:
            self._points[self._selectedCornerIndex] = eventPos
            self.points = self._points
            self._selectedCorner = eventPos
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        if self.stretch:
            self._stretch = False
            self._stretchSide = None
            self.setCursor(Qt.ArrowCursor)
            self._selectedCorner = QPoint(99999,99999)
            self._selectedCornerIndex = 999


class symbolPin(symbolShape):
    """
    symbol pin class definition for symbol drawing.
    """

    pinDirs = ["Input", "Output", "Inout"]
    pinTypes = ["Signal", "Ground", "Power", "Clock", "Digital", "Analog"]

    def __init__(
        self,
        start: QPoint,
        pinName: str,
        pinDir: str,
        pinType: str,
    ):
        super().__init__()

        self._start = start  # centre of pin
        self._pinName = pinName
        self._pinDir = pinDir
        self._pinType = pinType
        self._connected = False  # True if the pin is connected to a net.
        self._rect = QRect(self._start.x() - 5, self._start.y() - 5, 10, 10)

    def __str__(self):
        return f"symbolPin: {self._pinName} {self.mapToScene(self._start)}"

    def boundingRect(self):
        return self._rect  #

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(symlyr.selectedSymbolPinPen)
            painter.setBrush(symlyr.selectedSymbolPinBrush)
        else:
            painter.setPen(symlyr.symbolPinPen)
            painter.setBrush(symlyr.symbolPinBrush)
        painter.setFont(QFont("Arial", 12))
        painter.drawRect(self._rect)
        if (
            str(type(self.scene()))
            == "<class 'revedaEditor.gui.editorScenes.symbolScene'>"
        ):
            painter.drawText(
                QPoint(self._start.x() - 5, self._start.y() - 10), self._pinName
            )

    def __repr__(self):
        return f"pin({self._start},{self._pinName}, {self._pinDir}, {self._pinType})"

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self.prepareGeometryChange()
        self._start = start
        self._rect = QRect(self._start.x() - 5, self._start.y() - 5, 10, 10)

    @property
    def rect(self)->QRect:
        return self._rect

    @rect.setter
    def rect(self, inputRect:QRect):
        self._rect = inputRect
        self._start = inputRect.center()

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

    def toSchematicPin(self, start: QPoint):
        return schematicPin(start, self.pinName, self.pinDir, self.pinType)


class text(symbolShape):
    """
    This class is for text annotations on symbol or schematics.
    """

    textAlignments = ["Left", "Center", "Right"]
    textOrients = ["R0", "R90", "R180", "R270"]

    def __init__(
        self,
        start: QPoint,
        textContent: str,
        fontFamily: str,
        fontStyle: str,
        textHeight: str,
        textAlign: str,
        textOrient: str,
    ):
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
        self._rect = self._fm.boundingRect(
            QRect(0, 0, 400, 400), Qt.AlignmentFlag.AlignCenter, self._textContent
        )

    def __repr__(self):
        return (
            f"text({self._start},{self._textContent}, {self._textFont.family()},"
            f" {self._textFont.style()}, {self._textHeight}, {self._textAlign},"
            f"{self._textOrient})"
        )

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
            self._rect = self._fm.boundingRect(
                QRect(0, 0, 400, 400), Qt.AlignmentFlag.AlignLeft, self._textContent
            )
        elif self._textAlign == text.textAlignments[1]:
            self._rect = self._fm.boundingRect(
                QRect(0, 0, 400, 400), Qt.AlignmentFlag.AlignCenter, self._textContent
            )
        elif self._textAlign == text.textAlignments[2]:
            self._rect = self._fm.boundingRect(
                QRect(0, 0, 400, 400), Qt.AlignmentFlag.AlignRight, self._textContent
            )
        return QRect(
            self._start.x(),
            self._start.y() - self._rect.height(),
            self._rect.width(),
            self._rect.height(),
        )

    def paint(self, painter, option, widget):
        painter.setFont(self._textFont)
        if self.isSelected():
            painter.setPen(schlyr.selectedTextPen)
            painter.drawRect(self.boundingRect())
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
        fixedFamilies = [
            family for family in fontFamilies if QFontDatabase.isFixedPitch(family)
        ]
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
        fontSizes = [
            str(size)
            for size in QFontDatabase.pointSizes(
                self._textFont.family(), self._textFont.styleName()
            )
        ]
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


class pinNetIndexTuple(NamedTuple):
    pin: symbolPin
    net: net.schematicNet
    netEndIndex: int


class schematicSymbol(symbolShape):
    def __init__(self, shapes: list, attr: dict):
        super().__init__()
        assert shapes is not None  # must not be an empty list
        self._shapes = shapes  # list of shapes in the symbol
        self._symattrs = attr  # parameters common to all instances of symbol
        self._counter = 0  # item's number on schematic
        self._libraryName = ""
        self._cellName = ""
        self._viewName = ""
        self._instanceName = ""
        self._netlistLine = ""
        self._labels: dict[str, symbolLabel] = dict()  # dict of labels
        self._pins: dict[str, symbolPin] = dict()  # dict of pins
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

    def addShapes(self):
        for item in self._shapes:
            item.setFlag(QGraphicsItem.ItemIsSelectable, False)
            item.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
            item.setParentItem(self)
            if type(item) is symbolPin:
                self._pins[item.pinName] = item
            elif type(item) is symbolLabel:
                self._labels[item.labelName] = item
            # if type(item) is not symbolLabel:
            #     self._shapeRectF = self._shapeRectF.united(item.boundingRect())
            # self._borderRect = self._shapeRectF.toRect().normalized()

    def __repr__(self):
        return f"schematicSymbol({self._shapes})"

    def itemChange(self, change, value):
        if self.scene():
            match change:
                case QGraphicsItem.ItemPositionChange:
                    if self._snapLines is None:
                        self._snapLines = dict()
                        self.findPinNetIndexTuples()
                        for item in self._pinNetIndexTupleSet:
                            self._snapLines.setdefault(item.pin, set())
                            snapLine = net.guideLine(
                                item.pin.mapToScene(item.pin.start).toPoint(),
                                item.net.sceneEndPoints[item.netEndIndex - 1],
                            )
                            snapLine.inherit(item.net)
                            self.scene().addItem(snapLine)
                            self._snapLines[item.pin].add(snapLine)
                            self.scene().removeItem(item.net)
                    else:
                        for pin, snapLinesSet in self._snapLines.items():
                            for snapLine in snapLinesSet:
                                snapLine.setLine(
                                    QLineF(
                                        snapLine.mapFromScene(pin.mapToScene(pin.start)),
                                        snapLine.line().p2(),
                                    )
                                )
                case QGraphicsItem.ItemPositionHasChanged:
                    if self._snapLines is not None:
                        for pin, snapLinesSet in self._snapLines.items():
                            for snapLine in snapLinesSet:
                                snapLine.setLine(
                                    QLineF(
                                        snapLine.mapFromScene(pin.mapToScene(pin.start)),
                                        snapLine.line().p2(),
                                    )
                                )
                case QGraphicsItem.ItemSelectedHasChanged:
                    if value:
                        self.scene().selectedSymbol = self
                    else:
                        self.scene().selectedSymbol = None

        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        self.setZValue(symlyr.symbolLayer.z)
        if self._draft:
            painter.setPen(symlyr.draftPen)
            self.setZValue(symlyr.draftLayer.z)
        if self.isSelected():
            painter.setPen(symlyr.selectedSymbolPen)
            painter.drawRect(self.boundingRect())
            self.setZValue(symlyr.selectedSymbolLayer.z)
        if self.netlistIgnore:
            painter.setPen(schlyr.ignoreSymbolPen)
            painter.drawLine(self.boundingRect().bottomLeft(), self.boundingRect().topRight())
            painter.drawLine(self.boundingRect().topLeft(), self.boundingRect().bottomRight())

    def boundingRect(self):
        return self.childrenBoundingRect()

    # def shape(self):
    #     path = QPainterPath()
    #     path.addRect(self._shapeRectF.toRect())
    #     return path

    def findPinNetIndexTuples(self):
        # Create an empty set to store pin-net-index tuples
        self._pinNetIndexTupleSet = set()
        # Iterate over each pin in the collection
        for pinItem in self._pins.values():
            # Find all the net items connected to the pin
            for netItem in self.scene().items(pinItem.sceneBoundingRect()):
                if isinstance(netItem, net.schematicNet):
                    connectList = list(
                        map(pinItem.sceneBoundingRect().contains, netItem.sceneEndPoints))
                    endIndex = connectList.index(True)
                    if any(connectList):
                        self._pinNetIndexTupleSet.add(
                            pinNetIndexTuple(pinItem, netItem, endIndex)
                        )

            # netsConnected = [
            #     netItem
            #     for netItem in self.scene().items(pinItem.sceneBoundingRect())
            #     if isinstance(netItem, net.schematicNet)
            #     and any(list(map(pinItem.sceneBoundingRect().contains,
            #                      netItem.sceneEndPoints)))
            #
            #     # and
            #     # pinItem.mapToScene(pinItem.start).toPoint()
            #     # in netItem.sceneEndPoints
            # ]
            # # Iterate over each connected net item
            # for netItem in netsConnected:
            #     # Find the index of the pin in the net item's scene end points
            #     endIndex = netItem.sceneEndPoints.index(
            #         pinItem.mapToScene(pinItem.start).toPoint()
            #     )
            #
            #     # Create a pin-net-index tuple and add it to the set
            #     self._pinNetIndexTupleSet.add(
            #         pinNetIndexTuple(pinItem, netItem, endIndex)
            #     )

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:

        super().mousePressEvent(event)
        self._snapLines = None

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

    @instanceName.setter
    def instanceName(self, value: str):
        """
        If instance name is changed and [@instName] label exists, change it too.
        """
        self._instanceName = value
        if self.labels.get("instanceName", None):
            self.labels["instanceName"].labelValue = value
            # self.labels["instanceName"].labelValueSet = True
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
        self._angle = value
        for label in self.labels.values():
            label.angle = -value

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


class schematicPin(symbolShape):
    """
    schematic pin class.
    """

    pinDirs = ["Input", "Output", "Inout"]
    pinTypes = ["Signal", "Ground", "Power", "Clock", "Digital", "Analog"]

    def __init__(
        self,
        start: QPoint,
        pinName: str,
        pinDir: str,
        pinType: str,
    ):
        super().__init__()
        self._start = start
        self._pinName = pinName
        self._pinDir = pinDir
        self._pinType = pinType
        self._pinNetIndexTupleSet = set()

    def __repr__(self):
        return (
            f"schematicPin({self._start}, {self._pinName}, {self._pinDir}, "
            f"{self._pinType})"
        )

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(schlyr.selectedSchematicPinPen)
            painter.setBrush(schlyr.selectedSchematicPinBrush)
            painter.drawRect(
                QRect.span(
                    QPoint(self._start.x() - 10, self._start.y() - 10),
                    QPoint(self._start.x() + 10, self._start.y() + 10),
                )
            )
        else:
            painter.setPen(schlyr.schematicPinPen)
            painter.setBrush(schlyr.schematicPinBrush)
            self.setZValue(schlyr.schematicPinLayer.z)
        self.drawPin(painter)

    def drawPin(self, painter):
        painter.setFont(QFont("Arial", 12))
        match self.pinDir:
            case "Input":
                painter.drawPolygon(
                    [
                        QPoint(self._start.x() - 10, self._start.y() - 10),
                        QPoint(self._start.x() + 10, self._start.y() - 10),
                        QPoint(self._start.x() + 20, self._start.y()),
                        QPoint(self._start.x() + 10, self._start.y() + 10),
                        QPoint(self._start.x() - 10, self._start.y() + 10),
                    ]
                )
            case "Output":
                painter.drawPolygon(
                    [
                        QPoint(self._start.x() - 20, self._start.y()),
                        QPoint(self._start.x() - 10, self._start.y() - 10),
                        QPoint(self._start.x() + 10, self._start.y() - 10),
                        QPoint(self._start.x() + 10, self._start.y() + 10),
                        QPoint(self._start.x() - 10, self._start.y() + 10),
                    ]
                )
            case "Inout":
                painter.drawPolygon(
                    [
                        QPoint(self._start.x() - 20, self._start.y()),
                        QPoint(self._start.x() - 10, self._start.y() - 10),
                        QPoint(self._start.x() + 10, self._start.y() - 10),
                        QPoint(self._start.x() + 20, self._start.y()),
                        QPoint(self._start.x() + 10, self._start.y() + 10),
                        QPoint(self._start.x() - 10, self._start.y() + 10),
                    ]
                )
        painter.drawText(self._start.x(), self._start.y() - 20, self.pinName)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if value:
                self.scene().selectedPin= self
            else:
                self.scene().selectedPin = None
        return super().itemChange(change, value)

    def boundingRect(self):
        return QRect(self._start.x() - 10, self._start.y() - 10, 30, 20).adjusted(
            -5, -10, 5, 5
        )

    # def sceneEvent(self, event):
    #     """
    #     Do not propagate event if shape needs to keep still.
    #     """
    #     switch = not (
    #         self.scene().selectModes.selectAll or self.scene().selectModes.selectPin
    #     )
    #     if switch:
    #         # Propagate the event to colliding items
    #         [item.sceneEvent(event) for item in self.collidingItems()]
    #         return False
    #     else:
    #         super().sceneEvent(event)
    #         return True

    def findPinNetIndexTuples(self):
        # Create an empty set to store pin-net-index tuples
        self._pinNetIndexTupleSet = set()

        pinSceneConnectRect = self.mapRectToScene(
            QRect.span(
                QPoint(self._start.x() - 5, self._start.y() - 5),
                QPoint(self._start.x() + 5, self._start.y() + 5),
            )
        ).toRect()
        # Find all the net items connected to the pin
        netsConnected = [
            netItem
            for netItem in self.scene().items(pinSceneConnectRect)
            if isinstance(netItem, net.schematicNet)
        ]

        # Iterate over each connected net item
        for netItem in netsConnected:
            netEndIndex = list(
                map(pinSceneConnectRect.contains, netItem.sceneEndPoints)
            ).index(True)
            self._pinNetIndexTupleSet.add(pinNetIndexTuple(self, netItem, netEndIndex))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        self.findPinNetIndexTuples()
        for tupleItem in self._pinNetIndexTupleSet:
            self._snapLines = set()
            snapLine = net.guideLine(
                self.mapToScene(self.start),
                tupleItem.net.sceneEndPoints[tupleItem.netEndIndex - 1],
            )
            snapLine.inherit(tupleItem.net)

            self.scene().addItem(snapLine)
            self._snapLines.add(snapLine)
            self.scene().removeItem(tupleItem.net)
        super().mousePressEvent(event)

    #
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        lines: list[net.schematicNet] = []
        if hasattr(self, "snapLines"):
            for snapLine in self._snapLines:
                lines = self.scene().addStretchWires(
                    self.mapToScene(self.start).toPoint(),
                    snapLine.mapToScene(snapLine.line().p2()).toPoint(),
                )
                if lines:
                    for line in lines:
                        line.inheritGuideLine(snapLine)
                    self.scene().addListUndoStack(lines)
                self.scene().removeItem(snapLine)
        self._snapLines = dict()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)
        for snapLine in self._snapLines:
            snapLine.setLine(
                QLineF(
                    snapLine.mapFromScene(self.mapToScene(self.start)),
                    snapLine.line().p2(),
                )
            )

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
