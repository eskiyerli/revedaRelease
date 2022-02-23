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
import math
import circuitElements as cel
import copy


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
        return super().itemChange(change, value)

    def setSnapGrid(self, gridSize: int) -> None:
        self.gridSize = gridSize

    def snapGrid(self):
        return self.gridSize

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        self.setCursor(Qt.OpenHandCursor)
        self.setSelected(True)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        # self.setSelected(False)

    def hoverEnterEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().hoverEnterEvent(event)
        self.setCursor(Qt.ArrowCursor)
        self.setOpacity(0.75)
        self.setFocus()

    def hoverLeaveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().hoverLeaveEvent(event)
        self.setCursor(Qt.CrossCursor)
        self.setOpacity(1)
        self.clearFocus()

    def contextMenuEvent(self, event):
        self.scene().symbolContextMenu.exec_(event.screenPos())

    def snap2grid(self, pos: QPoint) -> QPoint:
        return QPoint(
            round(pos.x() / self.gridX) * self.gridX,
            round(pos.y() / self.gridY) * self.gridY,
        )


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
        self.start = start  # top left corner
        self.end = end  # bottom right corner
        self.rect = QRect(start, end)
        self.pen = pen
        self.stretch = False
        self.rectPos = self.scenePos()
        self.stretchSide = None

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
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.drawRect(self.rect)
            if self.stretch:
                if self.stretchSide == "left":
                    painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                    painter.drawLine(self.rect.topLeft(), self.rect.bottomLeft())
                elif self.stretchSide == "right":
                    painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                    painter.drawLine(self.rect.topRight(), self.rect.bottomRight())
                elif self.stretchSide == "top":
                    painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                    painter.drawLine(self.rect.topLeft(), self.rect.topRight())
                elif self.stretchSide == "bottom":
                    painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                    painter.drawLine(self.rect.bottomLeft(), self.rect.bottomRight())
            self.update()
        else:
            painter.setPen(self.pen)
            painter.drawRect(self.rect)
            self.stretch = False
            self.stretchSide = None
            self.update()

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

    def setHeight(self, height: int):
        self.rect.setHeight(height)

    def setWidth(self, width: int):
        self.rect.setWidth(width)

    def origin(self):
        return self.rect.bottomLeft()

    def bBox(self):
        return self.rect

    def Move(self, offset: QPoint):  # starts with capital letter
        self.moveBy(offset.x(), offset.y())

    def setScale(self, scale: float):
        self.setScale(scale, scale)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        eventPos = self.snap2grid(event.pos())
        if eventPos.x() == self.rect.left():
            if (
                self.start.y() <= eventPos.y() <= self.end.y()
                or self.start.y() >= eventPos.y() >= self.end.y()
            ):
                self.setCursor(Qt.SizeHorCursor)
                self.stretchSide = "left"
        elif eventPos.x() == self.rect.right():
            if (
                self.start.y() <= eventPos.y() <= self.end.y()
                or self.start.y() >= eventPos.y() >= self.end.y()
            ):
                self.setCursor(Qt.SizeHorCursor)
                self.stretchSide = "right"

        elif eventPos.y() == self.rect.top():
            if (
                self.start.x() <= eventPos.x() <= self.end.x()
                or self.start.x() >= eventPos.x() >= self.end.x()
            ):
                self.setCursor(Qt.SizeVerCursor)
                self.stretchSide = "top"

        elif eventPos.y() == self.rect.bottom():
            if (
                self.start.x() <= eventPos.x() <= self.end.x()
                or self.start.x() >= eventPos.x() >= self.end.x()
            ):
                self.setCursor(Qt.SizeVerCursor)
                self.stretchSide = "bottom"

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:

        if self.stretch:
            eventPos = self.snap2grid(event.pos())
            if self.stretchSide == "left":
                self.setCursor(Qt.SizeHorCursor)
                self.rect.setLeft(eventPos.x())
                self.rect = QRect(self.rect.topLeft(), self.rect.bottomRight())
            elif self.stretchSide == "right":
                self.setCursor(Qt.SizeHorCursor)
                self.rect.setRight(eventPos.x())
                self.rect = QRect(self.rect.topLeft(), self.rect.bottomRight())
            elif self.stretchSide == "top":
                self.setCursor(Qt.SizeVerCursor)
                self.rect.setTop(eventPos.y())
                self.rect = QRect(self.rect.topLeft(), self.rect.bottomRight())
            elif self.stretchSide == "bottom":
                self.setCursor(Qt.SizeVerCursor)
                self.rect.setBottom(eventPos.y())
                self.rect = QRect(self.rect.topLeft(), self.rect.bottomRight())
            self.update()

        else:
            self.update()
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.stretch = False
        super().mouseReleaseEvent(event)


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
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            if self.points == 2:
                painter.drawLine(self.start, self.end)
            else:
                midPoint = QPoint(self.end.x(), self.start.y())
                painter.drawLine(self.start, midPoint)
                painter.drawLine(midPoint, self.end)

    def objName(self):
        return "LINE"

    def nPoints(self):
        return self.points

    def setWidth(self, width: int):
        self.pen.setWidth(width)

    def bBox(self) -> QRect:
        return self.boundingRect()

    def width(self):
        return self.pen.width()

    def Move(self, offset: QPoint):
        self.start += offset
        self.end += offset

    def length(self):
        return math.sqrt(
            (self.start.x() - self.end.x()) ** 2 + (self.start.y() - self.end.y()) ** 2
        )


class pin(shape):
    """
    rect: QRect defined by top left corner and bottom right corner. QRect(Point1,Point2)
    """

    pinDirs = ["Input", "Output", "Inout"]
    pinTypes = ["Signal", "Ground", "Power", "Clock", "Digital", "Analog"]

    def __init__(
        self,
        start: QPoint,
        pen: QPen,
        pinName: str,
        pinDir: str,
        pinType: str,
        grid: tuple,
    ):
        super().__init__(pen, grid)
        self.start = start  # top left corner
        self.pen = pen
        self.pinName = pinName
        self.pinDir = pinDir
        self.pinType = pinType
        self.rect = QRect(self.start.x() - 5, self.start.y() - 5, 10, 10)

    def boundingRect(self):
        minX = self.start.x() - 5
        maxX = self.start.x() + 5
        minY = self.start.y() - 5
        maxY = self.start.y() + 5
        return QRect(
            QPoint(minX - 0.5 * self.gridX, minY - 0.5 * self.gridY),
            QPoint(maxX + self.gridX * 0.5, maxY + self.gridY * 0.5),
        )

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.setBrush(self.pen.color())
        painter.drawRect(self.rect)
        painter.setFont(QFont("Arial", 12))
        painter.drawText(QPoint(self.start.x() - 5, self.start.y() - 10), self.pinName)
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.setBrush(Qt.yellow)
            painter.drawRect(self.rect)

    def objName(self):
        return "PIN"

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

    labelAlignments = ["Left", "Center", "Right"]
    labelOrients = ["R0", "R90", "R180", "R270", "MX", "MX90", "MY", "MY90"]
    labelUses = ["Normal", "Instance", "Pin", "Device", "Annotation"]
    labelTypes = ["Normal", "NLPLabel", "PyLabel"]

    def __init__(
        self,
        start: QPoint,
        pen: QPen,
        labelName: str,
        grid: tuple,
        labelType: str,
        labelHeight: str = "12",
        labelAlign: str = "Left",
        labelOrient: str = "R0",
        labelUse: str = "Normal",
    ):
        super().__init__(pen, grid)
        self.start = start  # top left corner
        self.pen = pen
        self.labelName = labelName
        self.labelHeight = labelHeight
        self.labelAlign = labelAlign
        self.labelOrient = labelOrient
        self.labelUse = labelUse
        self.labelType = labelType
        self.labelFont = QFont("Arial", int(self.labelHeight))
        self.fm = QFontMetrics(self.labelFont)
        self.rect = self.fm.boundingRect(self.labelName)

    def boundingRect(self):
        return QRect(
            self.start.x(),
            self.start.y(),
            self.rect.width() + self.gridX * 0.5,
            self.rect.height() + self.gridY * 0.5,
        )  #

    def paint(self, painter, option, widget):
        # self.rect = self.fm.boundingRect(self.labelName)
        painter.setFont(self.labelFont)
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.drawText(
                QPoint(self.start.x(), self.start.y() + self.rect.height()),
                self.labelName,
            )
            painter.drawRect(self.boundingRect())
        else:
            painter.setPen(self.pen)
            painter.drawText(
                QPoint(self.start.x(), self.start.y() + self.rect.height()),
                self.labelName,
            )
        self.fm = QFontMetrics(self.labelFont)
        self.rect = self.fm.boundingRect(self.labelName)

    def left(self):
        return self.start.x()

    def right(self):
        return self.start.x() + self.boundingRect().width()

    def top(self):
        return self.start.y()

    def bottom(self):
        return self.start.y() + self.boundingRect().height()

    def width(self):
        return self.boundingRect().width()

    def height(self):
        return self.rect.boundingRect().height()

    def setLabel(self, label):
        self.labelName = label
        self.rect = self.fm.boundingRect(self.labelName)

    def objName(self):
        return "LABEL"

    def setType(self, labelType):
        if labelType in self.labelTypes:
            self.labelType = labelType
        else:
            print("Invalid label type")

    def setAlign(self, labelAlignment):
        if labelAlignment in self.labelAlignments:
            self.labelAlign = labelAlignment
        else:
            print("Invalid label alignment")

    def setOrient(self, labelOrient):
        if labelOrient in self.labelOrients:
            self.labelOrient = labelOrient
        else:
            print("Invalid label orientation")

    def setUse(self, labelUse):
        if labelUse in self.labelUses:
            self.labelUse = labelUse
        else:
            print("Invalid label use")

    def moveBy(self, delta: QPoint):
        self.start += delta
