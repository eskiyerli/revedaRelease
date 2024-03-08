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
    QStaticText,
    QPainterPath,
    QFont,
)
from PySide6.QtWidgets import (
    QGraphicsLineItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsEllipseItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneHoverEvent,
)
import pdk.schLayers as schlyr
import math
import itertools as itt
from typing import Union, Optional, NamedTuple


# class crossingDot(QGraphicsEllipseItem):
#     dotDiameter = schlyr.crossingDotDiameter
#
#     def __init__(self, point: QPoint):
#
#         self.point = point
#         self._radius = crossingDot.dotDiameter
#         super().__init__(point.x() - self._radius, point.y() - self._radius,
#                          2 * self._radius, 2 * self._radius)
#         self.setPen(schlyr.wirePen)
#         self.setBrush(schlyr.wireBrush)
#         self._name = None
#
#     def paint(self, painter, option, widget) -> None:
#         if self.isSelected():
#             painter.setPen(schlyr.selectedWirePen)
#             painter.setBrush(schlyr.selectedWireBrush)
#         else:
#             painter.setPen(schlyr.wirePen)
#             painter.setBrush(schlyr.wireBrush)
#         painter.drawEllipse(self.point, self._radius, self._radius)
#
#     def __repr__(self):
#         return f"crossingDot({self.point},{self._radius})"
#
#     def findNets(self) -> set["schematicNet"]:
#         if self.scene():
#             return {netItem for netItem in self.scene().items(self.sceneBoundingRect()) if
#                     isinstance(netItem, schematicNet)}
#         else:
#             return set()
#
#


class pointSelfIndex(NamedTuple):
    point: QPoint
    selfIndex: int


class schematicNet(QGraphicsItem):
    _netSnapLines: dict
    __slots__ = (
        "_mode",
        "_name",
        "_nameConflict",
        "_nameAdded",
        "_nameSet",
        "_highlighted",
        "_flightLinesSet",
        "_connectedNetsSet",
        "_netIndexTupleSet",
        "_scene" "_netSnapLines",
        "_stretch",
        "_stretchSide",
        "_nameFont",
        "_nameItem",
        "_draftLine",
        "_shapeRect",
        "_boundingRect",
        "_angle",
        "_transformOriginPoint",
    )

    def __init__(self, start: QPoint, end: QPoint, mode: int = 0):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        # self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self._mode = 0
        self._name: str = ""
        self._nameConflict: bool = False
        self._nameAdded: bool = False
        self._nameSet: bool = False
        self._highlighted: bool = False
        self._flightLinesSet: set[schematicNet] = set()
        self._connectedNetsSet: set[schematicNet] = set()
        self._netSnapLines: dict = {}
        self._stretch: bool = False
        self._stretchSide: str = ""
        self._nameFont = QFont()
        self._nameFont.setPointSize(8)
        self._nameItem = QStaticText(self._name)
        self._draftLine = QLineF(start, end)
        self._transformOriginPoint = self._draftLine.p1()
        self._angle = None
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

    def paint(self, painter, option, widget=...):
        painter.setFont(self._nameFont)
        if self.isSelected():
            pen = schlyr.selectedWirePen
        elif self._stretch:
            pen = schlyr.stretchWirePen
        elif self._highlighted:
            pen = schlyr.hilightPen
        else:
            pen = schlyr.wirePen

        painter.setPen(pen)
        painter.drawLine(self._draftLine)
        # painter.drawEllipse(self._draftLine.p1(), 2, 2)
        if self._nameSet:
            painter.save()
            painter.translate(
                self._draftLine.center().x(), self._draftLine.center().y()
            )
            painter.rotate(self._angle)
            painter.drawStaticText(0, 0, self._nameItem)
            painter.restore()

    def sceneEvent(self, event):
        """
        Handle events related to the scene.

        Args:
            event: The event to handle.

        Returns:
            True if the event was handled successfully, False otherwise.
        """
        # Check if the current scene has the drawWire edit mode enabled
        if self.scene() and self.scene().editModes.drawWire:
            return False
        else:
            # Call the parent class's sceneEvent method to handle the event
            super().sceneEvent(event)
        return True

    def __repr__(self):
        return f"schematicNet({self.sceneEndPoints})"

    def itemChange(self, change, value):
        return super().itemChange(change, value)

    #
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        super().mousePressEvent(event)
        if self._stretch:
            eventPos = event.pos().toPoint()
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
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
        # else:
        #     orthoNets = list(filter(self.isOrthogonal, self.findOverlapNets()))
        #     for otherNet in orthoNets:
        #         for selfEnd, otherEnd in itt.product(self.sceneEndPoints, otherNet.sceneEndPoints):
        #             if selfEnd == otherEnd:
        #                 if otherNet.sceneEndPoints.index(otherEnd) == 0:
        #                     otherNet._stretchSide = 'p1'
        #                 else:
        #                     otherNet._stretchSide = 'p2'
        #                 self.scene().stretchNet(otherNet, otherNet._stretchSide)
        #                 break

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
            sceneNetsSet = self.scene().findSceneNetsSet() - {self}
            self._connectedNetsSet, _ = self.scene().traverseNets({self}, sceneNetsSet)
            # Highlight the connected netItems
            for netItem in self._connectedNetsSet:
                if not (netItem.nameAdded or netItem.nameSet):
                    netItem.nameAdded = True
                    netItem.name = self._name
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
            for flightLine in self._flightLinesSet:
                self.scene().removeItem(flightLine)
            self._flightLinesSet = set()
        [netItem.unhighlight() for netItem in self._connectedNetsSet]

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
            overlapNets = {
                netItem
                for netItem in self.scene().items(self.sceneShapeRect)
                if isinstance(netItem, schematicNet) and netItem is not self
            }
            if self._nameSet or self._nameAdded:
                for netItem in overlapNets:
                    netItem.name = self._name
                    netItem.nameSet = self._nameSet
                    netItem.nameAdded = self._nameAdded
        else:
            overlapNets = set()
        return overlapNets

    def mergeNets(self) -> tuple["schematicNet", "schematicNet"]:
        """
        Merges overlapping nets and returns the merged net.

        Returns:
            Optional[schematicNet]: The merged net if there are overlapping nets, otherwise returns self.
        """
        # Find other nets that overlap with self
        otherNets = self.findOverlapNets()

        # If there are other nets
        if otherNets:
            # Filter the other nets to find the parallel ones
            parallelNets = [
                netItem for netItem in otherNets if self.isParallel(netItem)
            ]

            # If there are parallel nets
            if parallelNets:
                # Create an initialRect variable and set it to self's sceneShapeRect
                initialRect = self.sceneShapeRect

                # Iterate over the parallel nets
                for netItem in parallelNets:
                    # Update the initialRect by uniting it with each parallel net's
                    # sceneShapeRect
                    initialRect = initialRect.united(netItem.sceneShapeRect)

                    # Remove each parallel net from the scene
                    if netItem.scene():
                        netItem.scene().removeItem(netItem)

                # Adjust the initialRect by 2 pixels on each side
                newNetPoints = initialRect.adjusted(2, 2, -2, -2)

                # Get the coordinates of the adjusted rectangle
                x1, y1, x2, y2 = newNetPoints.getCoords()

                # Create a new schematicNet with the snapped coordinates
                newNet = schematicNet(
                    self.snapToGrid(QPoint(x1, y1)), self.snapToGrid(QPoint(x2, y2))
                )

                # If self has a name, set the name and nameSet of the newNet
                if self._nameSet or self._nameAdded:
                    newNet.name = self._name
                    newNet.nameSet = self._nameSet
                    newNet.nameAdded = self._nameAdded

                return self, newNet  # original net, new net

        # If there are no other nets or no parallel nets, return self
        return self, self

    def snapToGrid(self, point: Union[QPoint, QPointF]) -> QPoint:
        if self.scene():
            return self.scene().snapToGrid(point, self.scene().snapTuple)
        else:
            return point

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name != "":  # net name should not be an empty string
            self.prepareGeometryChange()
            self._name = name
            self._nameItem = QStaticText(self._name)

    @property
    def nameSet(self) -> bool:
        """
        Check if the name of the net is explicitly set.

        Returns:
            bool: The value of the 'nameSet' attribute.
        """
        return self._nameSet

    @nameSet.setter
    def nameSet(self, value: bool):
        """
        If the name of the net is explicitly set, set this attribute to True.

        Args:
            value (bool): The value to set for the 'nameSet' attribute.

        Raises:
            AssertionError: If the input value is not a boolean.
        """
        assert isinstance(value, bool)
        self._nameSet = value

    @property
    def nameAdded(self) -> bool:
        """
        Name added is true if net name is set due to a connected net or pin.
        """
        return self._nameAdded

    @nameAdded.setter
    def nameAdded(self, value: bool):
        assert isinstance(value, bool)
        self._nameAdded = value

    @property
    def nameConflict(self) -> bool:
        """
        If two different names are attempted to be set for the net.
        """
        return self._nameConflict

    @nameConflict.setter
    def nameConflict(self, value: bool):
        assert isinstance(value, bool)
        self._nameConflict = value

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


class netFlightLine(QGraphicsPathItem):
    wireHighlightPen = QPen(
        schlyr.wireHilightLayer.pcolor,
        schlyr.wireHilightLayer.pwidth,
        schlyr.wireHilightLayer.pstyle,
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
        self.setPen(schlyr.guideLinePen)
        self._name: str = ""
        self._nameSet: bool = False

    @property
    def sceneEndPoints(self) -> list[QPoint]:
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
    def nameSet(self) -> bool:
        return self._nameSet

    @nameSet.setter
    def nameSet(self, value: bool):
        assert isinstance(value, bool)
        self._nameSet = value
