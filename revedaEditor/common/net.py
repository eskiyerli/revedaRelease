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
from PySide6.QtCore import (QPoint, Qt, QLineF, QRectF, QPointF, )
from PySide6.QtGui import (QPen, QStaticText, QPainterPath, QFont, )
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsItem, QGraphicsPathItem,
                               QGraphicsEllipseItem, QGraphicsSceneMouseEvent,
                               QGraphicsSceneHoverEvent, )
import pdk.schLayers as schlyr
import math
import itertools as itt
from typing import Union, Optional, NamedTuple


class crossingDot(QGraphicsEllipseItem):
    dotDiameter = schlyr.crossingDotDiameter

    def __init__(self, point: QPoint):

        self.point = point
        self._radius = crossingDot.dotDiameter
        super().__init__(point.x() - self._radius, point.y() - self._radius,
                         2 * self._radius, 2 * self._radius)
        self.setPen(schlyr.wirePen)
        self.setBrush(schlyr.wireBrush)
        self._name = None

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(schlyr.selectedWirePen)
            painter.setBrush(schlyr.selectedWireBrush)
        else:
            painter.setPen(schlyr.wirePen)
            painter.setBrush(schlyr.wireBrush)
        painter.drawEllipse(self.point, self._radius, self._radius)

    def __repr__(self):
        return f"crossingDot({self.point},{self._radius})"

    def findNets(self) -> set["schematicNet"]:
        if self.scene():
            return {netItem for netItem in self.scene().items(self.sceneBoundingRect()) if
                    isinstance(netItem, schematicNet)}
        else:
            return set()


class selfIndNetIndTuple(NamedTuple):
    selfIndex: int
    net: QGraphicsItem
    netEndIndex: int


class pointSelfIndex(NamedTuple):
    point: QPoint
    selfIndex: int


class schematicNet(QGraphicsItem):
    def __init__(self, start: QPoint, end: QPoint, mode: int = 0):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        # self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self._mode = 0
        self._name: str = ""
        self._nameConflict: bool = False
        self._nameAdded: bool = False
        self._nameSet: bool = False
        self._highlighted: bool = False
        self._flightLinesSet: set[schematicNet] = set()
        self._connectedNetsSet: set[schematicNet] = set()
        self._netIndexTupleSet: set[selfIndNetIndTuple] = set()
        self._pinLocIndexSet: set[pointSelfIndex] = set()
        self._pinSnapLines: dict[int, set[guideLine]] = {}
        self._netSnapLines: dict[int, set[guideLine]] = {}
        self._stretch: bool = False
        self._nameFont = QFont()
        self._nameFont.setPointSize(8)
        self._nameItem = QStaticText(self._name)
        self._draftLine = QLineF(start, end)
        self._stretchLine: Optional[guideLine] = None
        match self._mode:
            case 0:
                self._angle = 90 * math.floor(((self._draftLine.angle() + 45) % 360) / 90)
            case 1:
                self._angle = 45 * math.floor(((self._draftLine.angle() + 22.5) % 360) / 45)
        self._draftLine.setAngle(0)
        self.setTransformOriginPoint(self._draftLine.p1())
        if self.scene():
            self._draftLine.setP2(
                self.scene().snapToGrid(self._draftLine.p2(), self.scene().snapTuple))
        self._shapeRect = QRectF(self._draftLine.p1(), self._draftLine.p2()).adjusted(-2,
                                                                                      -2, 2,
                                                                                      2)
        self._boundingRect = self._shapeRect.adjusted(-8, -8, 8, 8)
        self.setRotation(-self._angle)

    @property
    def draftLine(self):
        return self._draftLine

    @draftLine.setter
    def draftLine(self, line: QLineF):
        self.prepareGeometryChange()
        self._draftLine = line
        match self._mode:
            case 0:
                self._angle = 90 * math.floor(((self._draftLine.angle() + 45) % 360) / 90)
            case 1:
                self._angle = 45 * math.floor(((self._draftLine.angle() + 22.5) % 360) / 45)
        self._draftLine.setAngle(0)
        self.setTransformOriginPoint(self._draftLine.p1())
        if self.scene():
            self._draftLine.setP2(
                self.scene().snapToGrid(self._draftLine.p2(), self.scene().snapTuple))
        self._shapeRect = (
            QRectF(self._draftLine.p1(), self._draftLine.p2()).normalized().adjusted(-2, -2,
                                                                                     2, 2))
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
            if self._stretch:
                pen = schlyr.stretchWirePen
        elif self._highlighted:
            pen = schlyr.hilightPen
        else:
            pen = schlyr.wirePen

        painter.setPen(pen)
        painter.drawLine(self._draftLine)
        if self._nameSet:
            painter.save()
            painter.translate(self._draftLine.center().x(), self._draftLine.center().y())
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
        if change == QGraphicsItem.ItemSceneChange and not value:
            self.mergeOrthoNets()
            self.clearDots()
        return super().itemChange(change, value)

    def mergeOrthoNets(self):
        cdots = self.findDots()
        for dot in cdots:
            orthoNets = list(filter(self.isOrthogonal, dot.findNets()))
            if orthoNets:
                self.scene().mergeNets(orthoNets[0])

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        self.mergeOrthoNets()
        self.clearDots()

        if self._stretch:
            self.startStretch(event)
        else:
            self.findSymPinConnections()
            self.findNetConnections()
            self.createPinSnapLines()
            self.createNetSnapLines()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:

        if self.stretch:
            self.extendStretch(event)
        else:
            if self._pinSnapLines:
                self.extendPinSnapLines()
            if self._netSnapLines:
                self.extendNetSnapLines()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):

        if self.stretch:
            self.endStretch()
        else:
            self.removePinSnapLines()
            self.removeNetSnapLines()
        # self.createDots()
        super().mouseReleaseEvent(event)

    def createPinSnapLines(self):
        for tupleItem in self._pinLocIndexSet:
            lineSet = self._pinSnapLines.setdefault(tupleItem.selfIndex, set())
            stretchLine = guideLine(tupleItem.point, tupleItem.point)
            lineSet.add(stretchLine)

    def createNetSnapLines(self):
        for tupleItem in self._netStretchTupleSet:
            print(f'net name is set: {tupleItem.net.nameSet}')
            lineSet = self._netSnapLines.setdefault(tupleItem.selfIndex, set())
            stretchLine = guideLine(
                tupleItem.net.sceneEndPoints[tupleItem.netEndIndex - 1],
                self.sceneEndPoints[tupleItem.selfIndex])
            if tupleItem.net.nameSet:
                stretchLine.name = tupleItem.net.name
                stretchLine.nameSet = True
            lineSet.add(stretchLine)
            if tupleItem.net.scene():
                self.scene().removeItem(tupleItem.net)
                self.scene().addItem(stretchLine)

    def extendPinSnapLines(self):
        for index, lineSet in self._pinSnapLines.items():
            for snapLine in lineSet:
                if not snapLine.scene():
                    self.scene().addItem(snapLine)
                snapLine.setLine(QLineF(snapLine.mapFromScene(self.sceneEndPoints[index]),
                                        snapLine.line().p2()))

    def extendNetSnapLines(self):
        for index, lineSet in self._netSnapLines.items():
            for snapLine in lineSet:
                snapLine.setLine(QLineF(snapLine.line().p1(),
                                        snapLine.mapFromScene(self.sceneEndPoints[index])))

    def removePinSnapLines(self):
        for snapLineSet in self._pinSnapLines.values():
            lines = []
            for snapLine in snapLineSet:
                lines = self.scene().addStretchWires(
                    snapLine.mapToScene(snapLine.line().p1()).toPoint(),
                    snapLine.mapToScene(snapLine.line().p2()).toPoint(), )
                if snapLine.scene():
                    self.scene().removeItem(snapLine)
                if lines:
                    self.scene().addListUndoStack(lines)

        self._pinSnapLines = dict()

    def removeNetSnapLines(self):
        for snapLineSet in self._netSnapLines.values():

            for snapLine in snapLineSet:
                lines = self.scene().addStretchWires(
                    snapLine.mapToScene(snapLine.line().p1()).toPoint(),
                    snapLine.mapToScene(snapLine.line().p2()).toPoint())
                if lines:
                    self.scene().addListUndoStack(lines)
                    for line in lines:
                        if snapLine.nameSet:
                            line.name = snapLine.name
                            line.nameSet = True
                if snapLine.scene():
                    self.scene().removeItem(snapLine)

        self._netSnapLines = dict()

    def startStretch(self, event):
        """
        Handle the start of the stretch of the net using one of the end points.
        """

        eventPos = event.scenePos().toPoint()
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        if (eventPos - self.mapToScene(
                self._draftLine.p1()).toPoint()).manhattanLength() <= self.scene().snapDistance:
            self.setCursor(Qt.SizeHorCursor)
            self._stretchLine = guideLine(self.mapToScene(self._draftLine.p1()), eventPos)
        elif (eventPos - self.mapToScene(
                self._draftLine.p2()).toPoint()).manhattanLength() <= self.scene().snapDistance:
            self.setCursor(Qt.SizeHorCursor)
            self._stretchLine = guideLine(self.mapToScene(self._draftLine.p2()), eventPos)

    def extendStretch(self, event):
        eventPos = event.scenePos().toPoint()
        if self._stretchLine is not None:
            if self._stretchLine.scene() is None:
                self.scene().addItem(self._stretchLine)
            self._stretchLine.setLine(QLineF(self._stretchLine.line().p1(),
                                             self._stretchLine.mapFromScene(eventPos), ))

    def endStretch(self):
        self._stretch = False
        self._stretchSide = None
        if self._stretchLine and self.scene():
            lines = self.scene().addStretchWires(*self._stretchLine.sceneEndPoints)
            self.scene().removeItem(self._stretchLine)
        if lines:
            self.scene().addListUndoStack(lines)
            self.scene().mergeSplitNets(lines[0])
        self._stretchLine = None
        self.setCursor(Qt.ArrowCursor)

    @property
    def innerRect(self) -> QRectF:
        return (
            QRectF(self._draftLine.p1(), self._draftLine.p2()).normalized().adjusted(2, 2,
                                                                                     -2,
                                                                                     -2))

    @property
    def sceneInnerRect(self) -> QRectF:
        return self.mapRectToScene(self.innerRect)

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
            # Create a set of connected netItems based on certain conditions
            self._connectedNetsSet = {netItem for netItem in self.scene().items() if (
                    isinstance(netItem, schematicNet) and (
                    self.nameSet or self.nameAdded) and netItem.name == self.name)}

            # Highlight the connected netItems
            for netItem in self._connectedNetsSet:
                netItem.highlight()

            # Create flight lines and add them to the scene
            for netItem in self._connectedNetsSet:
                flightLine = netFlightLine(self.mapToScene(self._draftLine.center()),
                                           netItem.mapToScene(netItem.draftLine.center()), )
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

    def containsDot(self, dot: crossingDot) -> bool:
        """
        Check if the dot is contained within the scene shape rectangle.

        Args:
            dot: The dot to check.

        Returns:
            True if the dot is contained within the scene shape rectangle, False otherwise.
        """
        if self.sceneShapeRect.contains(self.mapFromScene(dot.point)):
            return True
        return False

    def findOverlapNets(self) -> set["schematicNet"]:
        """
        Find all netItems in the scene that overlap with self.sceneShapeRect.

        Returns:
            set: A set of netItems that overlap with self.sceneShapeRect.
        """
        if self.scene():
            overlapNets = {netItem for netItem in self.scene().items(self.sceneShapeRect) if
                           isinstance(netItem, schematicNet) and netItem is not self}
        else:
            overlapNets = set()
        return overlapNets

    def findCrossingNets(self, otherNets: set) -> dict[int, list["schematicNet"]]:
        """
        Finds the crossing nets in the scene.

        Returns:
            dict: A dictionary with the index of each scene end point as the key, and a list
            of nets that cross that end point as the value.
        """

        orthoNets = list(filter(self.isOrthogonal, otherNets))
        crossingNets = dict()
        for netEnd in self.sceneEndPoints:
            crossingNets[self.sceneEndPoints.index(netEnd)] = list()
            for netItem in orthoNets:
                if netItem.sceneInnerRect.contains(netEnd):
                    crossingNets[self.sceneEndPoints.index(netEnd)].append(netItem)
        return crossingNets

    def createSplitNets(self, crossingNets: dict) -> set:
        """
        Create split nets based on the net connections.

        Args:
            crossingNets (dict): A dictionary containing the net connections. Keys are
            netEnds. Values are lists of netItems that are connected to the netEnd.

        Returns:
            set: A set of tuples representing netEnd they are connected,
            themselves and their connected end.
        """
        splitNetTuples = set()

        for endIndex, orthoNets in crossingNets.items():
            for orthoNet in orthoNets:
                # Create new net from endIndex to orthoNet draftLine.p2()
                newNet1 = schematicNet(self.sceneEndPoints[endIndex],
                                       orthoNet.mapToScene(orthoNet.draftLine.p2()), )

                # Create new net from orthoNet draftLine.p1() to endIndex
                newNet2 = schematicNet(orthoNet.mapToScene(orthoNet.draftLine.p1()),
                                       self.sceneEndPoints[endIndex], )
                # Set name and nameSet properties of newNet1 and newNet2
                if self._nameSet or self._nameAdded:
                    newNet1.name = self._name
                    newNet2.name = self._name
                    newNet1.nameSet = self._nameSet
                    newNet2.nameSet = self._nameSet
                    newNet1.nameAdded = self._nameAdded
                    newNet2.nameAdded = self._nameAdded
                self.scene().removeItem(orthoNet)
                splitNetTuples.add(selfIndNetIndTuple(endIndex, newNet1, 0))
                splitNetTuples.add(selfIndNetIndTuple(endIndex, newNet2, 1))
        return splitNetTuples

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
            parallelNets = [netItem for netItem in otherNets if self.isParallel(netItem)]

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
                newNet = schematicNet(self.snapToGrid(QPoint(x1, y1)),
                                      self.snapToGrid(QPoint(x2, y2)))

                # If self has a name, set the name and nameSet of the newNet
                if self._nameSet or self._nameAdded:
                    newNet.name = self._name
                    newNet.nameSet = self._nameSet
                    newNet.nameAdded = self._nameAdded

                return self, newNet  # original net, new net

        # If there are no other nets or no parallel nets, return self
        return self, self

    def clearDots(self):
        """
        Clears all crossingDot items from the net's scene shape area.
        """
        if self.scene():
            crossing_dots = [item for item in self.scene().items(self.sceneShapeRect) if
                             isinstance(item, crossingDot)]
            for dot in crossing_dots:
                self.scene().removeItem(dot)

    def createDots(self):
        """
        Create crossing dots at the intersection of nets.

        This function finds overlapping nets, generates combinations of two nets,
        and checks if they intersect at the same endpoints. If they do, a crossing
        dot is created at that intersection point.

        Parameters:
        - self: The instance of the class.

        Returns:
        - None
        """
        # Find overlapping nets
        otherNets = self.findOverlapNets()

        # Generate combinations of two nets
        netCombinations = set(itt.combinations(otherNets, 2))

        # Iterate over net combinations
        for netCombination in netCombinations:
            net2, net3 = netCombination

            # Check if both nets exist
            if net2 and net3:
                # Iterate over all possible combinations of endpoints
                for netEnd1, netEnd2, netEnd3 in itt.product(self.sceneEndPoints,
                                                             net2.sceneEndPoints,
                                                             net3.sceneEndPoints):
                    # Check if all endpoints are the same
                    if netEnd1 == netEnd2 and netEnd2 == netEnd3:
                        # Create a crossing dot at the intersection point if there is no dot
                        # there.
                        dots = [dotItem for dotItem in self.scene().items(QRectF(netEnd1,
                                                                                 netEnd1).adjusted(
                            -2, -2, 2, 2)) if isinstance(dotItem,
                                                         crossingDot)]
                        if not dots:
                            newDot = crossingDot(netEnd1)
                            self.scene().addItem(newDot)

    def findDots(self) -> list[crossingDot]:
        """
        Find all crossingDot items in the net shape.

        Returns:
            set: A set of crossingDot items.
        """
        crossing_dots = []
        if self.scene():
            crossing_dots = [item for item in self.scene().items(self.sceneShapeRect) if
                             isinstance(item, crossingDot)]
        return crossing_dots

    def findSymPinConnections(self):
        """
        Find the pin connections to a symbol in the scene.
        """

        # Set to store the index of pin locations
        self._pinLocIndexSet = set()
        connectedPins = []
        if self.scene():
            # Find the connected pins in the scene
            connectedPins = self.scene().findRectSymbolPin(self.sceneShapeRect)
        if connectedPins:
            # Iterate over the end points and connected pins
            for end, pin in itt.product(self.sceneEndPoints, connectedPins):
                # Check if the pin's bounding rectangle contains the end point
                if pin.sceneBoundingRect().contains(end):
                    # Add the index of the end point to the set
                    self._pinLocIndexSet.add(
                        pointSelfIndex(end, self.sceneEndPoints.index(end)))

    def findNetConnections(self):
        # Find the overlap nets
        overlapNets = self.findOverlapNets()
        self._netStretchTupleSet = set()
        for netItem in overlapNets:
            for selfEnd, netItemEnd in itt.product(self.sceneEndPoints,
                                                   netItem.sceneEndPoints):
                if selfEnd == netItemEnd:
                    self._netStretchTupleSet.add(
                        selfIndNetIndTuple(self.sceneEndPoints.index(selfEnd), netItem,
                                           netItem.sceneEndPoints.index(netItemEnd)))

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
        return [self.mapToScene(self._draftLine.p1()).toPoint(),
                self.mapToScene(self._draftLine.p2()).toPoint(), ]

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
    def stretchSide(self):
        """
        The end where the net is stretched.
        """
        return self._stretchSide

    @stretchSide.setter
    def stretchSide(self, value: str):
        self.prepareGeometryChange()
        self._stretchSide = value

    @property
    def angle(self):
        return self._angle


class netFlightLine(QGraphicsPathItem):
    wireHighlightPen = QPen(schlyr.wireHilightLayer.pcolor, schlyr.wireHilightLayer.pwidth,
                            schlyr.wireHilightLayer.pstyle, )

    def __init__(self, start: QPoint, end: QPoint):
        self._start = start
        self._end = end
        super().__init__()

    def __repr__(self):
        return f"netFlightLine({self.mapToScene(self._start)},{self.mapToScene(self._end)})"

    def paint(self, painter, option, widget) -> None:
        painter.setPen(netFlightLine.wireHighlightPen)
        line = QLineF(self._start, self._end)
        perpendicularLine = QLineF(line.center(),
                                   line.center() + QPointF(-line.dy(), line.dx()))
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
        return [self.mapToScene(self.line().p1()).toPoint(),
                self.mapToScene(self.line().p2()).toPoint(), ]

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
