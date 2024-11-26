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

import os

# net class definition.
from PySide6.QtCore import (
    QPoint,
    Qt,
    QLineF,
    QRectF,
    QPointF,
)
from PySide6.QtGui import (
    QPen,
    QPainterPath,
    QPainter,
)
from PySide6.QtWidgets import (
    QGraphicsLineItem,
    QGraphicsSimpleTextItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
)
from dotenv import load_dotenv

load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):
    import pdk.schLayers as schLayers

else:
    import defaultPDK.schLayers as schLayers

import math
from typing import Type, Set
from enum import IntEnum



class NetMode(IntEnum):
    ORTHOGONAL = 0
    DIAGONAL = 1
    FREE = 2


class customIntEnum(IntEnum):
    @classmethod
    def _missing_(cls, value):
        # Handle out-of-range values
        return cls(max(min(value, max(cls)), min(cls)))

    def increment(self):
        """Increment the enum value, wrapping around if necessary."""
        try:
            return self.__class__(self.value + 1)
        except ValueError:
            return self.__class__(min(self.__class__))

    def decrement(self):
        """Decrement the enum value, wrapping around if necessary."""
        try:
            return self.__class__(self.value - 1)
        except ValueError:
            return self.__class__(max(self.__class__))

class netNameStrengthEnum(customIntEnum):
    NONAME = 0
    WEAK = 1
    INHERIT = 2
    SET = 3

class schematicNetLine(QGraphicsLineItem):
    def __init__(self, start: QPoint, end: QPoint, mode: int = 0):
        super().__init__(start, end)
        

class schematicNet(QGraphicsItem):
    # _netSnapLines: dict

    def __init__(self, start: QPoint, end: QPoint, mode: int = 0):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        # self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self._mode = 0
        self._stretch = False
        self._nameConflict: bool = False
        self._nameStrength: netNameStrengthEnum = netNameStrengthEnum.NONAME
        self._highlighted = False
        self._flightLinesSet: Set["schematicNet"] = set()
        self._connectedNetsSet: Set["schematicNet"] = set()
        self._netSnapLines: dict = {}
        self._draftLine = QLineF(start, end)
        self._transformOriginPoint = self._draftLine.p1()
        self._angle = None
        self._flip = (1,1)
        self.parallelNetsSet = set()
        match self._mode:
            case 0:
                self._angle = 90 * math.floor(
                    ((self._draftLine.angle() + 45) % 360) / 90
                )
            case 1:
                self._angle = 45 * math.floor(
                    ((self._draftLine.angle() + 22.5) % 360) / 45
                )
            case 2:
                self._angle = self._draftLine.angle()
        self._draftLine.setAngle(0)
        self.setTransformOriginPoint(self._transformOriginPoint)
        self._shapeRect = QRectF(self._draftLine.p1(), self._draftLine.p2()).adjusted(
            -2, -2, 2, 2
        )
        self._boundingRect = self._shapeRect.adjusted(-8, -8, 8, 8)
        self.setRotation(-self._angle)
        self._nameItem = netName('', self)
        self._nameItem.setPos(self._draftLine.center())
        self._nameItem.setParentItem(self)


    @property
    def draftLine(self):
        return self._draftLine

    @draftLine.setter
    def draftLine(self, line: QLineF):
        self.prepareGeometryChange()
        self._draftLine = line
        self._transformOriginPoint = line.p1()
        match self._mode:
            case 0:
                self._angle = 90 * math.floor(
                    ((self._draftLine.angle() + 45) % 360) / 90
                )
            case 1:
                self._angle = 45 * math.floor(
                    ((self._draftLine.angle() + 22.5) % 360) / 45
                )
            case 2:
                self._angle = self._draftLine.angle()
        self._draftLine.setAngle(0)
        self.setTransformOriginPoint(self._transformOriginPoint)

        self._shapeRect = (
            QRectF(self._draftLine.p1(), self._draftLine.p2())
            .normalized()
            .adjusted(-2, -2, 2, 2)
        )
        self._boundingRect = self._shapeRect.adjusted(-8, -8, 8, 8)
        self.setRotation(-self._angle)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self._shapeRect)
        return path

    def boundingRect(self):
        return self._boundingRect

    def paint(self, painter: QPainter, option, widget=None):
        pen = self._getPen()
        painter.setPen(pen)
        painter.drawLine(self._draftLine)

    def _getPen(self):
        if self.isSelected():
            return schLayers.selectedWirePen
        elif self._stretch:
            return schLayers.stretchWirePen
        elif self._highlighted:
            return schLayers.hilightPen
        elif self._nameConflict:
            return schLayers.errorWirePen
        else:
            return schLayers.wirePen

    def __repr__(self):
        return f"schematicNet({self.sceneEndPoints})"

    def itemChange(self, change, value):
        if self.scene():
            match change:
                case QGraphicsItem.ItemSelectedHasChanged:
                    if value:
                        self.setZValue(self.zValue() + 10)
                        self.scene().selectedNet= self
                    else:
                        self.setZValue(self.zValue() - 10)
                        self.scene().selectedNet = None
        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        super().mousePressEvent(event)
        if self.scene():
            if self.scene().editModes.moveItem:
                self.setFlag(QGraphicsItem.ItemIsMovable, True)
            elif self._stretch:
                eventPos = event.pos().toPoint()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                if (
                    eventPos - self._draftLine.p1().toPoint()
                ).manhattanLength() <= self.scene().snapDistance:
                    self.setCursor(Qt.SizeHorCursor)
                    self._stretchSide = "p1"
                elif (
                    eventPos - self._draftLine.p2().toPoint()
                ).manhattanLength() <= self.scene().snapDistance:
                    self.setCursor(Qt.SizeHorCursor)
                    self._stretchSide = "p2"
                self.scene().stretchNet(self, self._stretchSide)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.setSelected(False)
        if self.scene().editModes.moveItem:
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
            self.scene().mergeSplitNets(self)
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """
        Override the hoverEnterEvent method of QGraphicsItem.

        Args:
            event (QGraphicsSceneHoverEvent): The hover event.

        Returns:
            None
        """
        super().hoverEnterEvent(event)
        # Check if highlightNets flag is set in the scene
        if self.scene().highlightNets:
            self._highlighted = True
            self._connectedNetsSet = self.scene().findConnectedNetSet(self)

            # Highlight the connected netItems
            for netItem in self._connectedNetsSet:
                netItem.highlight()

            # Create flight lines and add them to the scene
            for netItem in self._connectedNetsSet:
                flightLine = netFlightLine(
                    self.mapToScene(self._draftLine.center()),
                    netItem.mapToScene(netItem.draftLine.center()),
                )
                self._flightLinesSet.add(flightLine)
                self.scene().addItem(flightLine)


    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        super().hoverLeaveEvent(event)
        if self._highlighted:
            self._highlighted = False
            self._clearFlightLines()
            self._unhighlightConnectedNets()

    def _clearFlightLines(self) -> None:
        for flight_line in self._flightLinesSet:
            self.scene().removeItem(flight_line)
        self._flightLinesSet.clear()

    def _unhighlightConnectedNets(self) -> None:
        for net_item in self._connectedNetsSet:
            net_item.unhighlight()

    def isParallel(self, otherNet: "schematicNet") -> bool:
        return abs((self.angle - otherNet.angle) % 180) < 1

    def isOrthogonal(self, otherNet: "schematicNet") -> bool:
        return abs((self.angle - otherNet.angle - 90) % 180) < 1

    def notParallel(self, otherNet: "schematicNet") -> bool:
        return not self.isParallel(otherNet)

    def findOverlapNets(self) -> set["schematicNet"]:
        """
        Find all netItems in the scene that overlap with self.sceneShapeRect.

        Returns:
            set: A set of netItems that overlap with self.sceneShapeRect.
        """
        if self.scene():
            overlapNets = {netItem for netItem in self.collidingItems() if isinstance(netItem, schematicNet)}
            return overlapNets - {self}

    def inherit(self, otherNet: Type["schematicNet"]):
        """
        Inherit the name of the other net if self name strength is less than SET.
        """
        assert isinstance(otherNet, schematicNet)
        if self.nameStrength.value == 3:
            if otherNet.nameStrength.value == 3 and self.name != otherNet.name:
                self.nameConflict = True
                otherNet.nameConflict = True
        else:
            self.name = otherNet.name
            self.nameStrength = otherNet.nameStrength.decrement()

    def inheritGuideLine(self, otherNet: Type["guideLine"]):
        self.name = otherNet.name
        self.nameStrength = otherNet.nameStrength

    @property
    def name(self) -> str:
        return self._nameItem.name

    @name.setter
    def name(self, name: str):
        if name:
            self.prepareGeometryChange()
            self._nameItem.name = name
            self._nameItem.setPos(self._draftLine.center())

    @property
    def nameStrength(self) -> netNameStrengthEnum:
        return self._nameItem.nameStrength

    @nameStrength.setter
    def nameStrength(self, value: netNameStrengthEnum):
        self._nameItem.nameStrength = value

    @property
    def nameConflict(self) -> bool:
        return self._nameItem.nameConflict

    @nameConflict.setter
    def nameConflict(self, value: bool):
        self._nameItem.nameConflict = value


    @property
    def endPoints(self):
        return [self._draftLine.p1().toPoint(), self._draftLine.p2().toPoint()]
    
    @property
    def sceneEndPoints(self):
        return [
            self.mapToScene(self._draftLine.p1()).toPoint(),
            self.mapToScene(self._draftLine.p2()).toPoint(),
        ]

    def highlight(self):
        self._highlighted = True
        self.update()

    def unhighlight(self):
        self._highlighted = False
        self.update()

    @property
    def highlighted(self):
        return self._highlighted

    @highlighted.setter
    def highlighted(self, value: bool):
        self._highlighted = value

    @property
    def sceneShapeRect(self) -> QRectF:
        return self.mapRectToScene(self._shapeRect).normalized().toRect()

    @property
    def stretch(self) -> bool:
        return self._stretch

    @stretch.setter
    def stretch(self, value: bool):
        self._stretch = value

    @property
    def stretchSide(self) -> int:
        """
        The end where the net is stretched.
        """
        return self._stretchSide

    @stretchSide.setter
    def stretchSide(self, value: str):
        self.prepareGeometryChange()
        self._stretchSide = value

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, value: float):
        self._angle = value

    @property
    def stretch(self) -> bool:
        return self._stretch

    @stretch.setter
    def stretch(self, value: bool):
        self._stretch = value

    @property
    def mode(self) -> int:
        return self._mode

class netName(QGraphicsSimpleTextItem):
    def __init__(self, name: str, parent: schematicNet):
        super().__init__(name, parent)
        self.parent = parent
        self.setBrush(schLayers.wireBrush)
        self._nameConflict = False
        self._nameStrength = netNameStrengthEnum.NONAME
        self.setRotation(self.parent.angle)

    def setSelected(self, selected):
        super().setSelected(selected)
        if selected:
            self.setBrush(schLayers.selectedWireBrush)
        else:
            self.setBrush(schLayers.wireBrush)
        self.update()

    @property
    def nameConflict(self) -> bool:
        return self._nameConflict

    @nameConflict.setter
    def nameConflict(self, value: bool):
        if value:
            self.setBrush(schLayers.errorWireBrush)
        else:
            self.setBrush(schLayers.wireBrush)
        self.update()

    @property
    def nameStrength(self) -> netNameStrengthEnum:
        return self._nameStrength

    @nameStrength.setter
    def nameStrength(self, value: netNameStrengthEnum):
        self._nameStrength = value
        if self._nameStrength == netNameStrengthEnum.SET:
            self.setVisible(True)
        else:
            self.setVisible(False)

    @property
    def name(self) -> str:
        return self.text()

    @name.setter
    def name(self, value: str):
        self.prepareGeometryChange()
        self.setText(value)
        self.setRotation(self.parent.angle)
        if self._nameStrength == netNameStrengthEnum.SET:
            self.setVisible(True)
        else:
            self.setVisible(False)



class netFlightLine(QGraphicsPathItem):
    wireHighlightPen = QPen(
        schLayers.wireHilightLayer.pcolor,
        schLayers.wireHilightLayer.pwidth,
        schLayers.wireHilightLayer.pstyle,
    )

    def __init__(self, start: QPoint, end: QPoint):
        self._start = start
        self._end = end
        super().__init__()

    def __repr__(self):
        return f"netFlightLine({self.mapToScene(self._start)},{self.mapToScene(self._end)})"

    def paint(self, painter, option, widget) -> None:
        painter.setPen(netFlightLine.wireHighlightPen)
        line = QLineF(self._start, self._end)
        perpendicularLine = QLineF(
            line.center(), line.center() + QPointF(-line.dy(), line.dx())
        )
        perpendicularLine.setLength(100)

        path = QPainterPath()
        path.moveTo(self._start)
        path.quadTo(perpendicularLine.p2(), self._end)
        painter.drawPath(path)


class guideLine(QGraphicsLineItem):
    def __init__(self, start: QPoint, end: QPoint):
        self._start = start
        self._end = end
        super().__init__(QLineF(self._start, self._end))
        self.setPen(schLayers.guideLinePen)
        self.pen().setCosmetic(True)
        self._name: str = ""
        self._nameStrength: netNameStrengthEnum = netNameStrengthEnum.NONAME

    @property
    def sceneEndPoints(self) -> list[QPoint]:
        """
        Returns a list of the end points of the net in scene coordinates.

        Returns:
            list[QPoint]: A list of the end points of the net in scene coordinates.
        """
        return [
            self.mapToScene(self.line().p1()).toPoint(),
            self.mapToScene(self.line().p2()).toPoint(),
        ]

    def __repr__(self):
        return f"guideLine({self.mapToScene(self.line().p1()), self.mapToScene(self.line().p2())}"

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name != "":  # net name should not be an empty string
            self._name = name

    @property
    def nameStrength(self) -> netNameStrengthEnum:
        return self._nameStrength

    @nameStrength.setter
    def nameStrength(self, value: netNameStrengthEnum):
        assert isinstance(value, netNameStrengthEnum)
        self._nameStrength = value

    def inherit(self, otherNet: [schematicNet]):
        """
        This method is used to carry the name information of the original net
        to stretch net.
        """
        assert isinstance(otherNet, schematicNet)
        self.name = otherNet.name
        self.nameStrength = otherNet.nameStrength
