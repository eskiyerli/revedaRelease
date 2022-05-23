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
from PySide6.QtCore import (
    QPoint,
    QPointF,
    QRect,
    Qt,
    QLine,
)
from PySide6.QtGui import (
    QPen,
    QFont,
    QFontMetrics,
    QColor,
    QPainterPath,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QGraphicsPathItem,
    QGraphicsItemGroup,
)
import math
import circuitElements as cel
import copy


class shape(QGraphicsItem):
    def __init__(self, pen: QPen, gridTuple: tuple) -> None:
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        # self.setZValue(self.layer.z)
        self.pen = pen
        self.gridTuple = gridTuple

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = value.toPoint()
            sceneRect = self.scene().sceneRect()
            viewRect = self.scene().views()[0].viewport().rect()
            newPos.setX(round(newPos.x() / self.gridTuple[0]) * self.gridTuple[0])
            newPos.setY(round(newPos.y() / self.gridTuple[1]) * self.gridTuple[1])

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
        # self.setSelected(True)

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
        self.scene().itemContextMenu.exec_(event.screenPos())

    def snap2grid(self, pos: QPoint) -> QPoint:
        return self.scene().snap2Grid(pos, self.gridTuple)

    def snapToGrid(self, number: int, base: int) -> int:
        return self.scene().snapGrid(number, base)


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
        self.rect = QRect(start, end).normalized()
        self.pen = pen
        self.stretch = False
        self.rectPos = self.scenePos()
        self.stretchSide = None

    def boundingRect(self):
        return self.rect.normalized().adjusted(-2, -2, 2, 2)

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

        else:
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
        if self.stretch:
            self.prepareGeometryChange()
            eventPos = self.snap2grid(event.pos())

            if eventPos.x() == self.snapToGrid(self.rect.left(), self.gridTuple[0]):
                if (
                    self.start.y() <= eventPos.y() <= self.end.y()
                    or self.start.y() >= eventPos.y() >= self.end.y()
                ):
                    self.setCursor(Qt.SizeHorCursor)
                    self.stretchSide = "left"
            elif eventPos.x() == self.snapToGrid(self.rect.right(), self.gridTuple[0]):
                if (
                    self.start.y() <= eventPos.y() <= self.end.y()
                    or self.start.y() >= eventPos.y() >= self.end.y()
                ):
                    self.setCursor(Qt.SizeHorCursor)
                    self.stretchSide = "right"

            elif eventPos.y() == self.snapToGrid(self.rect.top(), self.gridTuple[1]):
                if (
                    self.start.x() <= eventPos.x() <= self.end.x()
                    or self.start.x() >= eventPos.x() >= self.end.x()
                ):
                    self.setCursor(Qt.SizeVerCursor)
                    self.stretchSide = "top"

            elif eventPos.y() == self.snapToGrid(self.rect.bottom(), self.gridTuple[1]):
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
        else:
            super().mouseMoveEvent(event)
        self.update()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.start = self.rect.topLeft()
        self.end = self.rect.bottomRight()
        self.stretch = False
        self.stretchSide = None
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
        self.stretch = False
        self.stretchSide = ""
        self.line = QLine(self.start, self.end)
        self.rect = QRect(self.start, self.end).normalized()
        self.horizontal = True  # True if line is horizontal, False if vertical

    def boundingRect(self):
        return self.rect.adjusted(-2, -2, 2, 2)

    def shape(self):
        path = QPainterPath()
        path.addRect(self.rect.adjusted(-2, -2, 2, 2))
        return path

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            # if self.stretch:
            #     painter.setPen(QPen(Qt.red, 1, Qt.SolidLine))
            #     if self.stretchSide == "x1_horizontal" or self.stretchSide == "y1_vertical":
            #         painter.drawRect(self.line.x1() - 5, self.line.y1() - 5, 10, 10)
            #     elif self.stretchSide == "x2_horizontal" or self.stretchSide == "y2_vertical":
            #         painter.drawRect(self.line.x2() - 5, self.line.y2() - 5, 10, 10)
        else:
            painter.setPen(self.pen)
        painter.drawLine(QLine(self.start, self.end))
        # length = self.line.x1() - self.line.x2()
        # height = self.line.y1() - self.line.y2()
        # if abs(length) >= abs(height):  # horizontal
        #     self.line = QLine(self.start, QPoint(self.end.x(), self.start.y()))
        #     painter.drawLine(self.line)
        #     self.horizontal = True
        # else:  # vertical
        #     self.line = QLine(self.start, QPoint(self.start.x(), self.end.y()))
        #     painter.drawLine(self.line)
        #     self.horizontal = False

    def objName(self):
        return "LINE"

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

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:

        super().mousePressEvent(event)
        # if self.stretch:
        #     eventPos = self.snap2grid(event.pos())
        #     if eventPos == self.line.p1() or eventPos == self.line.p2():
        #         if self.horizontal:
        #             if eventPos.x() == self.line.x1():
        #                 self.stretchSide = "x1_horizontal"
        #             elif eventPos.x() == self.line.x2():
        #                 self.stretchSide = "x2_horizontal"
        #         elif not self.horizontal:
        #             if eventPos.y() == self.line.y1():
        #                 self.stretchSide = "y1_vertical"
        #             elif eventPos.y() == self.line.y2():
        #                 self.stretchSide = "y2_vertical"

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        # if self.stretch:
        #     eventPos = self.snap2grid(event.pos())
        #     if self.stretchSide == "x1_horizontal":
        #         self.line.setP1(QPoint(eventPos.x(), self.line.y1()))
        #     elif self.stretchSide == "x2_horizontal":
        #         self.line.setP2(QPoint(eventPos.x(), self.line.y2()))
        #     elif self.stretchSide == "y1_vertical":
        #         self.line.setP1(QPoint(self.line.x1(), eventPos.y()))
        #     elif self.stretchSide == "y2_vertical":
        #         self.line.setP2(QPoint(self.line.x2(), eventPos.y()))
        # elif self.isSelected():
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        # self.start = self.line.p1()
        # self.end = self.line.p2()
        # self.stretch = False
        # self.stretchSide = ""


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
        return self.rect  #

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
    label:
    """

    labelAlignments = ["Left", "Center", "Right"]
    labelOrients = ["R0", "R90", "R180", "R270", "MX", "MX90", "MY", "MY90"]
    labelUses = ["Normal", "Instance", "Pin", "Device", "Annotation"]
    labelTypes = ["Normal", "NLPLabel", "PyLabel"]
    predefinedLabels = [
        "[@cellName]",
        "[@modelName]",
        "[@instName]",
        "[@libName]",
        "[@viewName]",
        "[@elementNum]",
    ]

    def __init__(
        self,
        start: QPoint,
        pen: QPen,
        labelDefinition: str,
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
        self.labelDefinition = labelDefinition  #
        self.labelName = None  # symbol property name
        self.labelText = None  # label text can be different from label definition

        self.labelHeight = labelHeight
        self.labelAlign = labelAlign
        self.labelOrient = labelOrient
        self.labelUse = labelUse
        self.labelType = labelType
        self.labelFont = QFont("Arial")
        self.labelFont.setPointSize(int(self.labelHeight))
        self.fm = QFontMetrics(self.labelFont)
        self.rect = self.fm.boundingRect(self.labelDefinition)
        self.setLabelName()

    def boundingRect(self):
        return QRect(
            self.start.x(), self.start.y(), self.rect.width(), self.rect.height()
        )  #

    def paint(self, painter, option, widget):
        # self.rect = self.fm.boundingRect(self.labelName)
        self.labelFont.setPointSize(int(self.labelHeight))
        painter.setFont(self.labelFont)
        if self.isSelected():
            painter.setPen(QPen(Qt.yellow, 2, Qt.DashLine))
            painter.drawRect(self.boundingRect())
        else:
            painter.setPen(self.pen)
        if self.labelText:
            painter.drawText(
                QPoint(self.start.x(), self.start.y() + self.rect.height()),
                self.labelText,
            )
        else:
            painter.drawText(
                QPoint(self.start.x(), self.start.y() + self.rect.height()),
                self.labelDefinition,
            )
        self.fm = QFontMetrics(self.labelFont)
        self.rect = self.fm.boundingRect(self.labelDefinition)

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
        return self.boundingRect().height()

    def setText(self, label):
        self.labelText = label
        self.rect = self.fm.boundingRect(self.labelText)

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

    def setLabelName(self):
        if self.labelType == "Normal":
            self.labelName = self.labelDefinition

        elif self.labelType == "NLPLabel":
            try:
                if self.labelDefinition == "[@cellName]":
                    self.labelName = "cellName"
                elif self.labelDefinition == "[@instName]":
                    self.labelName = "instName"
                elif self.labelDefinition == "[@libName]":
                    self.labelText = self.parentItem().libraryName
                    self.labelName = "libName"
                elif self.labelDefinition == "[@viewName]":
                    self.labelName = "viewName"
                elif self.labelDefinition == "[@modelName]":
                    self.labelName = "modelName"
                elif self.labelDefinition == "[@elementNum]":
                    self.labelName = "elementNum"
                else:
                    if ":" in self.labelDefinition:  # there is at least one colon
                        fieldsLength = len(self.labelDefinition.split(":"))
                        if fieldsLength == 1:
                            self.labelName = self.labelDefinition[1:-1]
                        elif (
                            len(self.labelDefinition.split(":")) == 2
                        ):  # there is only one colon
                            self.labelName = self.labelDefinition.split(":")[0].split(
                                "@"
                            )[1]
                        elif (
                            len(self.labelDefinition.split(":")) == 3
                        ):  # there are two colons
                            self.labelName = self.labelDefinition.split(":")[0].split(
                                "@"
                            )[1]
                        else:
                            print("label format error.")
            except Exception as e:
                print(e)

    def labelDefs(self):
        """
        This method will create label name and text from label definition.
        """
        if self.labelType == "Normal":
            self.labelName = self.labelDefinition
            self.setText(self.labelDefinition)
        elif self.labelType == "NLPLabel":
            try:
                if self.labelDefinition == "[@cellName]":
                    self.labelText = self.parentItem().cellName
                    self.labelName = "cellName"
                elif self.labelDefinition == "[@instName]":
                    self.labelText = f"I{self.parentItem().counter}"
                    self.labelName = "instName"
                elif self.labelDefinition == "[@libName]":
                    self.labelText = self.parentItem().libraryName
                    self.labelName = "libName"
                elif self.labelDefinition == "[@viewName]":
                    self.labelText = self.parentItem().viewName
                    self.labelName = "viewName"
                elif self.labelDefinition == "[@modelName]":
                    self.labelText = self.parentItem().attr["modelName"]
                    self.labelName = "modelName"
                elif self.labelDefinition == "[@elementNum]":
                    self.labelText = self.parentItem().counter
                    self.labelName = "elementNum"
                else:
                    if ":" in self.labelDefinition:  # there is at least one colon
                        fieldsLength = len(self.labelDefinition.split(":"))
                        if fieldsLength == 1:
                            self.labelName = self.labelDefinition[1:-1]
                            self.labelText = f"{self.labelDefinition[1:-1]}=?"
                        elif (
                            len(self.labelDefinition.split(":")) == 2
                        ):  # there is only one colon
                            self.labelName = self.labelDefinition.split(":")[0].split(
                                "@"
                            )[1]
                            self.labelText = f"{self.labelName}=?"
                        elif (
                            len(self.labelDefinition.split(":")) == 3
                        ):  # there are two colons
                            self.labelName = self.labelDefinition.split(":")[0].split(
                                "@"
                            )[1]
                            self.labelText = (
                                f'{self.labelDefinition.split(":")[2][:-1]}'
                            )
                        else:
                            print("label format error.")
            except Exception as e:
                print(e)


class symbolShape(shape):
    def __init__(self, pen: QPen, gridTuple: tuple, shapes: list, attr: dict):
        super().__init__(pen, gridTuple)
        assert shapes is not None  # must not be an empty list
        self.shapes = shapes  # list of shapes in the symbol
        self.attr = attr  # generic symbol parameters
        self.pinLocations = {}
        self.counter = 0  # item's number on schematic
        self.libraryName = ""
        self.cellName = ""
        self.viewName = ""
        self.instanceName = ""
        self.labelDict = {}  # labelName: label
        self.labels = []  # list of labels
        self.pins = []  # list of pins
        self.pinLocations = {}  # pinName: pinLocation
        for item in self.shapes:
            item.setParentItem(self)
            if type(item) is pin:
                self.pins.append(item)
            elif type(item) is label:
                self.labels.append(item)
        for item in self.shapes:
            if type(item) is pin:
                self.pinLocations[item.pinName] = (
                    item.start + item.scenePos().toPoint()
                ).toTuple()
        self.setFiltersChildEvents(True)
        self.setHandlesChildEvents(True)
        self.setFlag(QGraphicsItem.ItemContainsChildrenInShape, True)

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(self.pen)
            painter.drawRect(self.boundingRect())

    def boundingRect(self):
        return self.childrenBoundingRect()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.scene().drawWire:
            self.setFlag(QGraphicsItem.ItemIsSelectable, False)
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
        else:
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
            super().mousePressEvent(event)
            self.setCursor(Qt.OpenHandCursor)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for item in self.shapes:
                if type(item) is pin:
                    self.pinLocations[item.pinName] = (
                        item.start + item.scenePos().toPoint()
                    ).toTuple()
        return super().itemChange(change, value)
