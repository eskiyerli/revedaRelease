"""
======================= START OF LICENSE NOTICE =======================
  Copyright (C) 2022 Murat Eskiyerli. All Rights Reserved

  NO WARRANTY. THE PRODUCT IS PROVIDED BY DEVELOPER "AS IS" AND ANY
  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL DEVELOPER BE LIABLE FOR
  ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
  GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
  IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
  OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THE PRODUCT, EVEN
  IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
======================== END OF LICENSE NOTICE ========================
  Primary Author: Murat Eskiyerli

"""

# shape class definition for symbol editor.
# base class for all shapes: rectangle, circle, line
from PySide6.QtCore import (QPoint, QPointF, QRect, QRectF, Qt, QLine, )
from PySide6.QtGui import (QPen, QFont, QFontMetrics, QColor, QPainterPath, )
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsSceneMouseEvent,
                               QGraphicsPathItem, QGraphicsItemGroup, )
import math
import revedaeditor.pdk.callbacks as cb


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

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = value.toPoint()
            sceneRect = self.scene().sceneRect()
            viewRect = self.scene().views()[0].viewport().rect()
            newPos.setX(
                round(newPos.x() / self._gridTuple[0]) * self._gridTuple[0])
            newPos.setY(
                round(newPos.y() / self._gridTuple[1]) * self._gridTuple[1])

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
    def pen(self):
        return self._pen

    @pen.setter
    def pen(self, pen):
        self._pen = pen

    @property
    def gridTuple(self):
        return self._gridTuple

    @gridTuple.setter
    def gridTuple(self, gridTuple: tuple):
        self._gridTuple = gridTuple

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, angle):
        self._angle = angle

    @property
    def snapGrid(self):
        return self.scene().gridSize

    @snapGrid.setter
    def snapGrid(self, gridSize: int) -> None:
        self.scene().gridSize = gridSize

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if self.scene().changeOrigin:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        else:
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def sceneEvent(self, event):
        '''
        Do not propagate event if shape needs to keep still.
        '''

        if self.scene() and (
                self.scene().changeOrigin or self.scene().drawMode):
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

    def snap2grid(self, pos: QPoint, gridTuple: tuple) -> QPoint:
        return self.scene().snap2Grid(pos, gridTuple)

    def snapToGrid(self, number: int, base: int) -> int:
        return self.scene().snapGrid(number, base)


class rectangle(shape):
    """
    rect: QRect defined by top left corner and bottom right corner. QRect(Point1,Point2)
    """

    def __init__(self, start: QPoint, end: QPoint, pen: QPen, grid: tuple, ):
        super().__init__(pen, grid)
        self._rect = QRect(start, end).normalized()
        self._start = self._rect.topLeft()
        self._end = self._rect.bottomRight()
        self._pen = pen
        self._stretch: bool = False
        self._rectPos = self.scenePos()
        self._stretchSide = None

    def boundingRect(self):
        return self._rect.normalized().adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.drawRect(self._rect)
            if self._stretch:
                if self._stretchSide == "left":
                    painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                    painter.drawLine(self._rect.topLeft(),
                                     self._rect.bottomLeft())
                elif self._stretchSide == "right":
                    painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                    painter.drawLine(self._rect.topRight(),
                                     self._rect.bottomRight())
                elif self._stretchSide == "top":
                    painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                    painter.drawLine(self._rect.topLeft(), self._rect.topRight())
                elif self._stretchSide == "bottom":
                    painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                    painter.drawLine(self._rect.bottomLeft(),
                                     self._rect.bottomRight())

        else:
            painter.setPen(self._pen)
            painter.drawRect(self._rect)

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
        self._start = start

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end: QPoint):
        self._end = end

    @property
    def centre(self):
        return QPoint(int(self._rect.x() + self._rect.width() / 2),
                      int(self._rect.y() + self._rect.height() / 2), )

    @property
    def height(self):
        return self._rect.height()

    @property
    def width(self):
        return self._rect.width()

    def objName(self):
        return "RECTANGLE"

    @property
    def left(self):
        return self._rect.left()

    @property
    def right(self):
        return self._rect.right()

    @property
    def top(self):
        return self._rect.top()

    @property
    def bottom(self):
        return self._rect.bottom()

    @left.setter
    def left(self, left: int):
        self._rect.setLeft(left)

    @right.setter
    def right(self, right: int):
        self._rect.setRight(right)

    @top.setter
    def top(self, top: int):
        self._rect.setTop(top)

    @bottom.setter
    def bottom(self, bottom: int):
        self._rect.setBottom(bottom)

    @height.setter
    def height(self, height: int):
        self._rect.setHeight(height)

    @width.setter
    def width(self, width: int):
        self._rect.setWidth(width)

    @property
    def origin(self):
        return self._rect.bottomLeft()

    def bBox(self):
        return self._rect

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)
        if self._stretch:

            eventPos = self.snap2grid(event.pos(), self._gridTuple)

            if eventPos.x() == self.snapToGrid(self._rect.left(),
                                               self._gridTuple[0]):
                if (self._start.y() <= eventPos.y() <= self._end.y()):
                    self.setCursor(Qt.SizeHorCursor)
                    self._stretchSide = "left"
            elif eventPos.x() == self.snapToGrid(self._rect.right(),
                                                 self._gridTuple[0]):
                if (self._start.y() <= eventPos.y() <= self._end.y()):
                    self.setCursor(Qt.SizeHorCursor)
                    self._stretchSide = "right"

            elif eventPos.y() == self.snapToGrid(self._rect.top(),
                                                 self._gridTuple[1]):
                if (self._start.x() <= eventPos.x() <= self._end.x()):
                    self.setCursor(Qt.SizeVerCursor)
                    self._stretchSide = "top"

            elif eventPos.y() == self.snapToGrid(self._rect.bottom(),
                                                 self._gridTuple[1]):
                if (self._start.x() <= eventPos.x() <= self._end.x()):
                    self.setCursor(Qt.SizeVerCursor)
                    self._stretchSide = "bottom"

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:

        if self._stretch:
            eventPos = self.snap2grid(event.pos(), self._gridTuple)
            self.prepareGeometryChange()
            if self._stretchSide == "left":
                self.setCursor(Qt.SizeHorCursor)
                self._rect.setLeft(eventPos.x())
                # self._rect = QRect(self._rect.topLeft(), self._rect.bottomRight())
            elif self._stretchSide == "right":
                self.setCursor(Qt.SizeHorCursor)
                self._rect.setRight(eventPos.x())
                # self._rect = QRect(self._rect.topLeft(), self._rect.bottomRight())
            elif self._stretchSide == "top":
                self.setCursor(Qt.SizeVerCursor)
                self._rect.setTop(eventPos.y())
                # self._rect = QRect(self._rect.topLeft(), self._rect.bottomRight())
            elif self._stretchSide == "bottom":
                self.setCursor(Qt.SizeVerCursor)
                self._rect.setBottom(eventPos.y())
                # self._rect = QRect(self._rect.topLeft(), self._rect.bottomRight())
        else:
            super().mouseMoveEvent(event)
        self.update()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self._start = self._rect.topLeft()
        self._end = self._rect.bottomRight()
        self._stretch = False
        self._stretchSide = None
        super().mouseReleaseEvent(event)


class circle(shape):
    def __init__(self, centre: QPoint, end: QPoint, pen: QPen, gridTuple: tuple):
        super().__init__(pen, gridTuple)
        xlen = abs(end.x() - centre.x())
        ylen = abs(end.y() - centre.y())
        self._radius = math.sqrt(xlen ** 2 + ylen ** 2)
        self._centre = centre
        self._topLeft = self._centre - QPoint(self._radius, self._radius)
        self._rightBottom = self._centre + QPoint(self._radius, self._radius)
        self._end = self._centre + QPoint(self._radius, 0)
        self._stretch = False
        self._startStretch = False

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
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
        self._centre = self.snap2grid(centre, self._gridTuple)
        # self.topLeft = self._centre - QPoint(self._radius, self._radius)
        # self.rightBottom = self._centre + QPoint(self._radius, self._radius)
        self._end = self._centre + QPoint(self._radius, 0)

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, radius: int):
        self.prepareGeometryChange()
        self._radius = self.snapToGrid(radius, self._gridTuple[0])
        # self.topLeft = self._centre - QPoint(self._radius, self._radius)
        # self.rightBottom = self._centre + QPoint(self._radius, self._radius)
        self._end = self._centre + QPoint(self._radius, 0)

    @property
    def centre(self):
        return self._centre

    @centre.setter
    def centre(self,value: QPoint):
        if isinstance(value,QPoint):
            self._centre = value

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self,value: QPoint):
        if isinstance(value, QPoint):
            self._end = value

    @property
    def rightBottom(self):
        return self._rightBottom

    @rightBottom.setter
    def rightBottom(self,value:QPoint):
        if isinstance(value, QPoint):
            self._rightBottom = value

    @property
    def topLeft(self):
        return self._topLeft

    @topLeft.setter
    def topLeft(self,value:QPoint):
        if isinstance(value, QPoint):
            self._topLeft = value

    @property
    def startStretch(self):
        return self._startStretch

    @startStretch.setter
    def startStretch(self,value: bool):
        if isinstance(value, bool):
            self._startStretch = value

    @property
    def stretch(self):
        return self._startStretch

    @startStretch.setter
    def stretch(self, value: bool):
        if isinstance(value, bool):
            self._stretch = value

    def objName(self):
        return "CIRCLE"

    def bBox(self):
        return QRect(self.topLeft, self.rightBottom)

    def boundingRect(self):
        return QRect(self._topLeft, self._rightBottom).normalized().adjusted(-2, -2, 2, 2)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.isSelected() and self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            eventPos = self.snap2grid(event.pos(), self._gridTuple)
            distance = self.snapToGrid(math.sqrt(
                (eventPos.x() - self._centre.x()) ** 2 + (
                        eventPos.y() - self._centre.y()) ** 2),
                self._gridTuple[0])
            if distance == self._radius:
                self._startStretch = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._startStretch:
            eventPos = self.snap2grid(event.pos(), self._gridTuple)
            distance = self.snapToGrid(math.sqrt(
                (eventPos.x() - self._centre.x()) ** 2 + (
                        eventPos.y() - self._centre.y()) ** 2),
                self._gridTuple[0])
            self.prepareGeometryChange()
            self._radius = distance
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self._startStretch:
            self._startStretch = False
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self._topLeft = self._centre - QPoint(self._radius, self._radius)
            self._rightBottom = self._centre + QPoint(self._radius, self._radius)
            self._end = self._centre + QPoint(self._radius, 0)
        super().mouseReleaseEvent(event)


class line(shape):
    """
    line class definition for symbol drawing.
    """

    def __init__(self, start: QPoint, end: QPoint, pen: QPen, grid: tuple, ):
        super().__init__(pen, grid)
        self._end = end
        self._start = start
        self._pen = pen
        self._stretch = False
        self._stretchSide = ""
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
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            if self._stretch:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
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
        return math.sqrt((self.start.x() - self._end.x()) ** 2 + (
                self.start.y() - self._end.y()) ** 2)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.isSelected() and self._stretch:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            eventPos = self.snap2grid(event.pos(), self._gridTuple)
            if eventPos == self.start:
                self._stretchSide = "start"
            elif eventPos == self._end:
                self._stretchSide = "end"
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        eventPos = self.snap2grid(event.pos(), self._gridTuple)
        if self._stretchSide == "start":
            self.prepareGeometryChange()
            self.start = eventPos
            self._line = QLine(self.start, self._end)
            self._rect = QRect(self.start, self._end).normalized()
        elif self._stretchSide == "end":
            self.prepareGeometryChange()
            self._end = eventPos
            self._line = QLine(self.start, self._end)
            self._rect = QRect(self.start, self._end).normalized()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self._stretch = False
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self._stretchSide = ""
        super().mouseReleaseEvent(event)


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
        self._rect = QRect(self._start.x() - 5, self._start.y() - 5, 10, 10)

    def boundingRect(self):
        return self._rect  #

    def paint(self, painter, option, widget):
        painter.setPen(self._pen)
        painter.setBrush(self._pen.color())
        painter.drawRect(self._rect)
        painter.setFont(QFont("Arial", 12))
        painter.drawText(QPoint(self._start.x() - 5, self._start.y() - 10),
                         self._pinName)
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

    def toSchematicPin(self, start: QPoint, pen: QPen, gridTuple):
        return schematicPin(start, pen, self.pinName, self.pinDir, self.pinType,
                            gridTuple)


class label(shape):
    """
    label: text class definition for symbol drawing.
    labelText is what is shown on the symbol in a schematic
    """

    labelAlignments = ["Left", "Center", "Right"]
    labelOrients = ["R0", "R90", "R180", "R270", "MX", "MX90", "MY", "MY90"]
    labelUses = ["Normal", "Instance", "Pin", "Device", "Annotation"]
    labelTypes = ["Normal", "NLPLabel", "PyLabel"]
    predefinedLabels = ["[@cellName]", "[@modelName]", "[@instName]",
                        "[@libName]", "[@viewName]", "[@elementNum]", ]

    def __init__(self, start: QPoint, pen: QPen, labelDefinition: str = "",
                 grid: tuple = (10, 10), labelType: str = "Normal",
                 labelHeight: str = "12", labelAlign: str = "Left",
                 labelOrient: str = "R0", labelUse: str = "Normal", ):
        super().__init__(pen, grid)
        self._start = start  # top left corner
        self._pen = pen
        self._labelDefinition = labelDefinition  #
        self._labelName = None  # symbol property name
        self._labelText = None  # label text can be different from label
        # definition

        self._labelHeight = labelHeight
        self._labelAlign = labelAlign
        self._labelOrient = labelOrient
        self._labelUse = labelUse
        self._labelType = labelType
        self._labelFont = QFont("Arial")
        self._labelFont.setPointSize(int(float(self._labelHeight)))
        self.fm = QFontMetrics(self.labelFont)
        self._rect = self.fm.boundingRect(self.labelDefinition)
        self.setLabelName()

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
            painter.drawText(
                QPoint(self._start.x(), self._start.y() + self._rect.height()),
                self._labelText, )
        else:
            painter.drawText(
                QPoint(self._start.x(), self._start.y() + self._rect.height()),
                self.labelDefinition, )
        self.fm = QFontMetrics(self._labelFont)
        self._rect = self.fm.boundingRect(self._labelDefinition)

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self,value:QPoint):
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
    def labelName(self, labelName):
        self._labelName = labelName

    @property
    def labelDefinition(self):
        return self._labelDefinition

    @labelDefinition.setter
    def labelDefinition(self, labelDefinition):
        self._labelDefinition = labelDefinition

    @property
    def labelHeight(self):
        return self._labelHeight

    @labelHeight.setter
    def labelHeight(self,value: int):
        self._labelHeight = value

    @property
    def labelText(self):
        return self._labelText

    @labelText.setter
    def labelText(self, labelText):
        self._labelText = labelText
        self._rect = self.fm.boundingRect(self._labelText)

    def objName(self):
        return "LABEL"

    @property
    def labelType(self):
        return self._labelType

    @labelType.setter
    def labelType(self, labelType):
        if labelType in self.labelTypes:
            self._labelType = labelType
        else:
            print("Invalid label type")

    @property
    def labelAlign(self):
        return self._labelAlign

    @labelAlign.setter
    def labelAlign(self, labelAlignment):
        if labelAlignment in self.labelAlignments:
            self._labelAlign = labelAlignment
        else:
            print("Invalid label alignment")

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
        else:
            print("Invalid label use")

    @property
    def labelFont(self):
        return self._labelFont

    @labelFont.setter
    def labelFont(self, labelFont):
        self._labelFont = labelFont

    def moveBy(self, delta: QPoint):
        self._start += delta

    def setLabelName(self):
        """
        Creates a label name from label definition, such as [@w:w=%:] becomes
        w.
        """
        if self.labelType == "Normal":
            self.labelName = self.labelDefinition

        elif self.labelType == "NLPLabel":
            try:
                if self._labelDefinition == "[@cellName]":
                    self._labelName = "cellName"
                elif self.labelDefinition == "[@instName]":
                    self._labelName = "instName"
                elif self._labelDefinition == "[@libName]":
                    self._labelText = self.parentItem().libraryName
                    self._labelName = "libName"
                elif self._labelDefinition == "[@viewName]":
                    self._labelName = "viewName"
                elif self._labelDefinition == "[@modelName]":
                    self._labelName = "modelName"
                elif self._labelDefinition == "[@elementNum]":
                    self._labelName = "elementNum"
                else:
                    if ":" in self._labelDefinition:  # at least one colon
                        fieldsLength = len(self._labelDefinition.split(":"))
                        if fieldsLength == 1:
                            self.labelName = self._labelDefinition[1:-1]
                        elif 2 <= fieldsLength <= 3:  # two or more fields
                            self._labelName = \
                                self._labelDefinition.split(":")[0].split("@")[1]
                        else:
                            print("label format error.")
            except Exception as e:
                print(e)
        elif self._labelType == "PyLabel":
            self._labelName = \
                [string.strip() for string in self.labelDefinition.split("=")][
                    0]

    def labelDefs(self):
        """
        This method will create label name and text from label definition.
        """
        if self._labelType == "Normal":
            self._labelName = self._labelDefinition
            self._labelText = self._labelDefinition
        elif self._labelType == "NLPLabel":
            try:
                if self._labelDefinition == "[@cellName]":
                    self._labelText = self.parentItem().cellName
                    self._labelName = "cellName"
                elif self._labelDefinition == "[@instName]":
                    self._labelText = f"I{self.parentItem().counter}"
                    self._labelName = "instName"
                elif self._labelDefinition == "[@libName]":
                    self._labelText = self.parentItem().libraryName
                    self._labelName = "libName"
                elif self._labelDefinition == "[@viewName]":
                    self._labelText = self.parentItem().viewName
                    self._labelName = "viewName"
                elif self._labelDefinition == "[@modelName]":
                    self._labelText = self.parentItem().attr["modelName"]
                    self._labelName = "modelName"
                elif self._labelDefinition == "[@elementNum]":
                    self._labelText = self.parentItem().counter
                    self._labelName = "elementNum"
                else:
                    if ":" in self._labelDefinition:  # there is at least one colon
                        fieldsLength = len(self._labelDefinition.split(":"))
                        if fieldsLength == 1:
                            self._labelName = self._labelDefinition[1:-1]
                            self._labelText = f"{self._labelDefinition[1:-1]}=?"
                        elif (fieldsLength == 2):  # there is only one colon
                            self._labelName = \
                                self._labelDefinition.split(":")[0].split("@")[1]
                            self._labelText = f"{self._labelName}=?"
                        elif (fieldsLength == 3):  # there are two colons
                            self._labelName = \
                                self._labelDefinition.split(":")[0].split("@")[1]
                            self._labelText = (
                                f'{self._labelDefinition.split(":")[2][:-1]}')
                        else:
                            print("label format error.")
            except Exception as e:
                print(e)
        elif self._labelType == label.labelTypes[2]:  # pyLabel
            self._labelName = \
                [string.strip() for string in self.labelDefinition.split("=")][
                    0]
            self._labelText = f'{self._labelName} = ' \
                              f'{self._labelDefinition.split("=")[0]} ='
            # self.labelText = f'{self.labelName} = {str(eval([string.strip() for string in self.labelDefinition.split("=")][1]))}'
            # print(f' {self.labelText}')


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
        self.drawings = list()
        self.labelDict = {}  # labelName: label
        self.labels = []  # list of labels
        self.pins = []  # list of pins
        self.pinLocations = {}  # pinName: pinRect
        self.pinNetMap = {}  # pinName: netName
        for item in self.shapes:
            item.setFlag(QGraphicsItem.ItemIsSelectable, False)
            item.setFlag(QGraphicsItem.ItemStacksBehindParent, True)
            item.setParentItem(self)
            if type(item) is pin:
                self.pins.append(item)
            elif type(item) is label:
                self.labels.append(item)
            else:
                self.drawings.append(item)
        self.setFiltersChildEvents(True)
        self.setHandlesChildEvents(True)
        self.setFlag(QGraphicsItem.ItemContainsChildrenInShape, True)
        self.borderRect = self.drawings[0].sceneBoundingRect()
        if self.drawings[1:]:
            for draw in self.drawings[1:]:
                self.borderRect = self.borderRect.united(draw.sceneBoundingRect())

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.drawRect(self.borderRect)

    def boundingRect(self):
        return self.childrenBoundingRect()

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
        self._instanceName = value

    @property
    def counter(self):
        return self._counter

    @counter.setter
    def counter(self, value):
        self._counter = value


class schematicPin(shape):
    pinDirs = ["Input", "Output", "Inout"]
    pinTypes = ["Signal", "Ground", "Power", "Clock", "Digital", "Analog"]

    def __init__(self, start: QPoint, pen: QPen, pinName, pinDir, pinType,
                 gridTuple: tuple):
        super().__init__(pen, gridTuple)
        self._start = start
        self._pinName = pinName
        self._pinDir = pinDir
        self._pinType = pinType

    def paint(self, painter, option, widget):

        painter.setPen(self._pen)
        painter.setBrush(self._pen.color())
        painter.setFont(QFont("Arial", 12))
        match self.pinDir:
            case "Input":
                painter.drawPolygon(
                    [QPoint(self._start.x() - 10, self._start.y() - 10),
                     QPoint(self._start.x() + 10, self._start.y() - 10),
                     QPoint(self._start.x() + 20, self._start.y()),
                     QPoint(self._start.x() + 10, self._start.y() + 10),
                     QPoint(self._start.x() - 10, self._start.y() + 10)])
            case "Output":
                painter.drawPolygon(
                    [QPoint(self._start.x() - 20, self._start.y()),
                     QPoint(self._start.x() - 10, self._start.y() - 10),
                     QPoint(self._start.x() + 10, self._start.y() - 10),
                     QPoint(self._start.x() + 10, self._start.y() + 10),
                     QPoint(self._start.x() - 10, self._start.y() + 10)])
            case "Inout":
                painter.drawPolygon(
                    [QPoint(self._start.x() - 20, self._start.y()),
                     QPoint(self._start.x() - 10, self._start.y() - 10),
                     QPoint(self._start.x() + 10, self._start.y() - 10),
                     QPoint(self._start.x() + 20, self._start.y()),
                     QPoint(self._start.x() + 10, self._start.y() + 10),
                     QPoint(self._start.x() - 10, self._start.y() + 10)])
        painter.drawText(self._start.x(), self._start.y() - 20, self.pinName)
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            # painter.setBrush(Qt.yellow)
            painter.drawRect(
                QRect.span(QPoint(self._start.x() - 10, self._start.y() - 10),
                           QPoint(self._start.x() + 10, self._start.y() + 10)))

    def boundingRect(self):
        return QRect(self._start.x() - 10, self._start.y() - 10, 30, 20).adjusted(
            -5, -10, 5, 5)

    def sceneEvent(self, event):
        if self.scene().drawWire:
            return False
        else:
            super().sceneEvent(event)
            return True

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setPos(event.scenePos() - event.buttonDownPos(Qt.LeftButton))

    def toSymbolPin(self, start: QPoint, pen: QPen, gridTuple: tuple):
        return pin(start, pen, self.pinName, self.pinDir, self.pinType,
                   gridTuple)

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
