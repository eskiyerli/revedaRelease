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

import itertools as itt
import json

import pathlib
import time
from collections import Counter
from typing import Union, Set, Dict, Tuple, List
from PySide6.QtCore import (QPoint, QPointF, QRect, QRectF, Qt, QLineF, Signal, Slot)
from PySide6.QtGui import (QTextDocument, QFontDatabase, QFont, QGuiApplication,
                           QPainterPath, )
from PySide6.QtWidgets import (QComboBox, QDialog, QGraphicsRectItem,
                               QGraphicsSceneMouseEvent, QGraphicsItem, )

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.undoStack as us
import revedaEditor.common.labels as lbl
import revedaEditor.common.shapes as shp  # import the shapes
import revedaEditor.common.net as snet
import revedaEditor.fileio.loadJSON as lj
import revedaEditor.fileio.schematicEncoder as schenc
import revedaEditor.gui.editFunctions as edf
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.propertyDialogues as pdlg
from revedaEditor.backend.pdkPaths import importPDKModule
from revedaEditor.gui.editorScene import editorScene

schlyr = importPDKModule('schLayers')


class schematicScene(editorScene):
    wireEditFinished = Signal(snet.schematicNet)
    stretchNet = Signal(snet.schematicNet, str)

    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.instCounter = 0
        self.start = QPoint(0, 0)
        self.current = QPoint(0, 0)
        self.editModes = ddef.schematicModes(selectItem=True, deleteItem=False,
            moveItem=False, copyItem=False, rotateItem=False, changeOrigin=False,
            panView=False, drawPin=False, drawWire=False, drawText=False, addInstance=False,
            stretchItem=False, )
        self.selectModes = ddef.schematicSelectModes(selectAll=True, selectDevice=False,
            selectNet=False, selectPin=False, )
        self.instanceCounter = 0
        self.netCounter = 0
        self.selectedNet = None
        self.selectedPin = None
        self.selectedSymbol = None
        self.selectedSymbolPin = None
        # the same name
        self.instanceSymbolTuple = None
        # pin attribute defaults
        self.pinName = ""
        self.pinType = "Signal"
        self.pinDir = "Input"
        # self.wires = None
        self._newNet = None
        self._stretchNet = None
        self._newInstance = None
        self._newPin = None
        self._newText = None
        self.textTuple = None
        self._snapPointRect = QGraphicsRectItem()
        self._snapPointRect.setRect(QRect(-2, -2, 4, 4))
        self._snapPointRect.setZValue(100)
        self._snapPointRect.setVisible(False)
        self._snapPointRect.setPen(schlyr.guideLinePen)
        self.snapDistance: int = 5
        self.snapGrid = None
        self.highlightNets = False
        self.hierarchyTrail = ""
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamily = \
        [family for family in fontFamilies if QFontDatabase.isFixedPitch(family)][0]
        fontStyle = QFontDatabase.styles(fixedFamily)[1]
        self.fixedFont = QFont(fixedFamily)
        self.fixedFont.setStyleName(fontStyle)
        fontSize = [size for size in QFontDatabase.pointSizes(fixedFamily, fontStyle)][3]
        self.fixedFont.setPointSize(fontSize)
        self.fixedFont.setKerning(False)
        self.wireEditFinished.connect(self._handleWireFinished)
        self.stretchNet.connect(self._handleStretchNet)
        self._symbolCache = {}


    @property
    def drawMode(self):
        return any(
            (self.editModes.drawPin, self.editModes.drawWire, self.editModes.drawText))

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:

        super().mousePressEvent(event)
        modifiers = QGuiApplication.keyboardModifiers()
        if event.button() != Qt.LeftButton:
            return
        try:
            self.mousePressLoc = event.scenePos().toPoint()
            if self.editModes.selectItem:
                if (modifiers == Qt.KeyboardModifier.ShiftModifier or modifiers ==
                        Qt.KeyboardModifier.ControlModifier):
                    self._selectionRectItem = QGraphicsRectItem()
                    self._selectionRectItem.setRect(QRectF(self.mousePressLoc.x(),
                                                           self.mousePressLoc.y(),0,0))
                    self._selectionRectItem.setPen(schlyr.draftPen)
                    self.addItem(self._selectionRectItem)
        except Exception as e:
            self.logger.error(f"Mouse press error: {e}")

    def mouseMoveEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        """
        Handle mouse move event.

        :param mouseEvent: QGraphicsSceneMouseEvent instance
        """
        super().mouseMoveEvent(mouseEvent)
        self.mouseMoveLoc = mouseEvent.scenePos().toPoint()
        if self._newInstance and self.editModes.addInstance:
            message = "Place instance"
            self._newInstance.setPos(self.mouseMoveLoc)
        elif self._newPin and self.editModes.drawPin:
            message = "Place pin"
            self._newPin.setPos(self.mouseMoveLoc - self._newPin.start)
        elif self._newNet and self.editModes.drawWire:
            message = "Extend wire"
            netEndPoint = self.findSnapPoint(self.mouseMoveLoc, set())
            self._snapPointRect.setVisible(True)
            self._snapPointRect.setPos(netEndPoint)
            self._newNet.draftLine = QLineF(self._newNet.draftLine.p1(), netEndPoint, )
        elif self._stretchNet and self.editModes.stretchItem:
            netEndPoint = self.findSnapPoint(self.mouseMoveLoc, set())
            self._snapPointRect.setVisible(True)
            self._snapPointRect.setPos(netEndPoint)
            self._stretchNet.draftLine = QLineF(self._stretchNet.draftLine.p1(),
                                                netEndPoint, )
        elif self.editModes.selectItem and self._selectionRectItem:
            self._selectionRectItem.setRect(
                QRectF(self.mousePressLoc, self.mouseMoveLoc)
            )
        cursorPosition = self.snapToGrid(self.mouseMoveLoc - self.origin, self.snapTuple)
        # Show the cursor position in the status line
        self.statusLine.showMessage(
            f"Cursor Position: ({cursorPosition.x()}, {cursorPosition.y()})")

    def mouseReleaseEvent(self, mouseEvent: QGraphicsSceneMouseEvent) -> None:
        """
        Handle mouse release event.

        :param mouseEvent: QGraphicsSceneMouseEvent instance
        """
        try:
            self.mouseReleaseLoc = mouseEvent.scenePos().toPoint()
            self._handleMouseRelease(self.mouseReleaseLoc, mouseEvent.button())
        except Exception as e:
            self.logger.error(f"Mouse release error: {e}")
        super().mouseReleaseEvent(mouseEvent)

    def _handleMouseRelease(self, mouseReleaseLoc: QPoint, button: Qt.MouseButton) -> None:
        """
        Handle mouse release logic.

        :param mouseReleaseLoc: QPoint instance
        :param button: Qt.MouseButton instance
        """

        if button == Qt.LeftButton:
            modifiers = QGuiApplication.keyboardModifiers()
            if self.editModes.addInstance:
                self._handleAddInstance(mouseReleaseLoc)
            elif self.editModes.drawPin:
                self._handleDrawPin(mouseReleaseLoc)
            elif self.editModes.drawWire:
                self._handleDrawWire(mouseReleaseLoc)
            elif self.editModes.drawText:
                self._handleDrawText(mouseReleaseLoc)
            elif self.editModes.rotateItem:
                self.rotateSelectedItems(mouseReleaseLoc)
            elif self.editModes.stretchItem:
                self._handleStretchItem()
            elif self.editModes.selectItem and self._selectionRectItem:
                self._handleSelectionRect(modifiers)

    def _handleSelectionRect(self, modifiers):
        self.clearSelection()
        selectionMode = (Qt.ItemSelectionMode.IntersectsItemShape if
                                 self.partialSelection else Qt.ItemSelectionMode.ContainsItemShape)
        selectionPath = QPainterPath()
        selectionPath.addRect(self._selectionRectItem.sceneBoundingRect())
        match modifiers:
            case Qt.KeyboardModifier.ShiftModifier:
                self._handleShiftSelection(selectionMode, selectionPath)
            case Qt.KeyboardModifier.ControlModifier:
                for item in (self.items(selectionPath, mode=selectionMode)):
                    item.setSelected(not item.isSelected())
        self.removeItem(self._selectionRectItem)
        self._selectionRectItem = None

    def _handleShiftSelection(self, selectionMode, selectionPath):
        selectedItems = (self.items(selectionPath,
                                    mode=selectionMode))
        if self.selectModes.selectNet:
            selectedNets = (netItem for netItem in selectedItems if
                            isinstance(netItem, snet.schematicNet))

            # clear selection
            for net in selectedNets:
                net.setSelected(True)
        elif self.selectModes.selectDevice:
            selectedDevices = (item for item in selectedItems if
                               isinstance(item, shp.schematicSymbol))
            # clear selection
            for device in selectedDevices:
                device.setSelected(True)
        elif self.selectModes.selectPin:
            selectedPins = (item for item in selectedItems if
                            isinstance(item, shp.schematicPin))

            # clear selection
            for pin in selectedPins:
                pin.setSelected(True)
        else:
            self.setSelectionArea(selectionPath, mode=selectionMode)

    def _handleAddInstance(self, eventLoc: QPoint) -> None:
        """
        Handle add instance logic.

        :param eventLoc: QPoint instance
        """
        # if self._newInstance:
        #     self._newInstance = None
        self._newInstance = self.drawInstance(eventLoc)
        self._newInstance.setSelected(True)

    def _handleDrawPin(self, mouseReleaseLoc: QPoint) -> None:
        """
        Handle draw pin logic.

        :param mouseReleaseLoc: QPoint instance
        """
        # if self._newPin:
        #     self._newPin = None
        self._newPin = self.addPin(mouseReleaseLoc)
        self._newPin.setSelected(True)

    def _handleDrawWire(self, startPoint: QPoint) -> None:
        """
        Handle draw wire logic.
        """
        if self._newNet:  # finish net drawing
            # self.checkNewNet(self._newNet)
            self.wireEditFinished.emit(self._newNet)
            self._newNet = None
            self._snapPointRect.setVisible(False)
        startSnapPoint = self.findSnapPoint(startPoint, set())
        self._snapPointRect.setPos(startSnapPoint)
        self._newNet = snet.schematicNet(startSnapPoint, startSnapPoint)
        self._newNet.nameStrength = snet.netNameStrengthEnum.NONAME
        self.addUndoStack(self._newNet)

    def _handleDrawText(self, mouseReleaseLoc: QPoint) -> None:
        """
        Handle draw text logic.

        :param mouseReleaseLoc: QPoint instance
        """
        if self._newText:
            self._newText = None
            self.textTuple = None
        if self.textTuple:
            self._newText = shp.text(mouseReleaseLoc, *self.textTuple)

    def _handleStretchItem(self):
        if self._stretchNet:
            self._stretchNet.stretch = False
            self._stretchNet = None
            self._snapPointRect.setVisible(False)
            self.editModes.stretchItem = False

    def updateStretchNet(self):
        self._stretchNet.draftLine = QLineF(self._stretchNet.draftLine.p1(),
            self.mouseMoveLoc)

    @Slot(snet.schematicNet)
    def _handleWireFinished(self, newNet: snet.schematicNet):
        """
        check if the new net is valid. If it has zero length, remove it. Otherwise process it.

        """
        if newNet.draftLine.length()< self.snapDistance * 0.5:
            self.removeItem(newNet)
            self.undoStack.removeLastCommand()
        # else:
        #     self.mergeSplitNets(newNet)

    def mergeSplitNets(self, inputNet: snet.schematicNet):
        merged, mergedNet, parallelNetsSet = self.mergeNets(inputNet)
        if merged:
            inputNet.mergeNetNames(mergedNet)
            self.findNetsToSplit(mergedNet)
            splitSuccess, splitNetsSet = self.splitInputNet(mergedNet)  # input net is split
            parallelNetsSet.add(inputNet)  # original nets in the scene.
            if splitSuccess:
                for netItem in splitNetsSet-parallelNetsSet:
                    self.addItem(netItem)
                    netItem.inheritNetName(mergedNet)
                for netItem in parallelNetsSet-splitNetsSet:
                    self.removeItem(netItem)

            else: # input net is not split only merged
                mergedNet.highlighted = True
                for netItem in parallelNetsSet:
                    self.removeItem(netItem)
                self.addItem(mergedNet)
        else:
            self.findNetsToSplit(inputNet)
            splitSuccess, splitNetsSet = self.splitInputNet(inputNet)  # input net is split
            if splitSuccess:
                for netItem in splitNetsSet:
                    self.addItem(netItem)
                    netItem.inheritNetName(inputNet)
                self.removeItem(inputNet)

    def findNetsToSplit(self, inputNet: snet.schematicNet):
        """
        Split orthogonal nets intersecting with input net.
        Args:
            inputNet: net splitting other orthogonal nets
        """
        # Cache frequently accessed properties
        scene_shape_rect = inputNet.sceneShapeRect
        scene_items = self.items(scene_shape_rect)
        input_end_points = inputNet.sceneEndPoints

        # Pre-filter orthogonal nets
        ortho_nets = [
            netItem for netItem in scene_items
            if isinstance(netItem, snet.schematicNet)
               and inputNet.isOrthogonal(netItem)
        ]

        if not ortho_nets:
            return

        new_split_nets = []
        nets_to_remove = set()

        # Process each orthogonal net
        for netItem in ortho_nets:
            netItem_endpoints = netItem.sceneEndPoints
            netItem_rect = netItem.sceneShapeRect

            for netEnd in input_end_points:
                if not (netItem_rect.contains(netEnd) and netEnd not in netItem_endpoints):
                    continue

                if not inputNet.inheritNetName(netItem):
                    inputNet.nameConflict = True
                    netItem.nameConflict = True
                    return

                new_split_nets.extend([
                    snet.schematicNet(netItem_endpoints[0], netEnd),
                    snet.schematicNet(netEnd, netItem_endpoints[1])
                ])
                nets_to_remove.add(netItem)

        if not new_split_nets:
            return

        # Batch remove items
        for netItem in nets_to_remove:
            self.removeItem(netItem)

        # Add to undo stack and set properties
        self.addListUndoStack(new_split_nets)
        for netItem in new_split_nets:
            netItem.inheritNetName(inputNet)

    def splitInputNet(self, inputNet) -> tuple[bool, Set[snet.schematicNet]]:
        # Cache frequently accessed properties
        sceneShapeRect = inputNet.sceneShapeRect
        sceneItems = self.items(sceneShapeRect)

        # Combine all point collection operations into a single pass
        splitPointsSet = set()
        orthoNets = []

        # Single iteration through scene items to collect all relevant points
        for item in sceneItems:
            if isinstance(item, snet.schematicNet) and inputNet.isOrthogonal(item):
                orthoNets.append(item)
            elif isinstance(item, (shp.symbolPin, shp.schematicPin)):
                splitPointsSet.add(item.mapToScene(item.start).toPoint())

        # Process orthogonal nets
        if orthoNets:
            for netItem in orthoNets:
                for netItemEnd in netItem.sceneEndPoints:
                    if sceneShapeRect.contains(netItemEnd):
                        if not inputNet.inheritNetName(netItem):
                            inputNet.nameConflict = True
                            netItem.nameConflict = True
                            break
                        splitPointsSet.add(netItemEnd)

        if not splitPointsSet:
            return False, set()

        # Create and process split points
        splitPointsList = [inputNet.sceneEndPoints[0], *splitPointsSet,
                           inputNet.sceneEndPoints[1]]
        orderedPoints = list(Counter(self.orderPoints(splitPointsList)).keys())

        # Create split nets
        splitNetSet = set()
        is_selected = inputNet.isSelected()

        # Pre-cache input net properties
        inputName = inputNet.name
        inputStrength = inputNet.nameStrength

        for i in range(len(orderedPoints) - 1):
            splitNet = snet.schematicNet(orderedPoints[i], orderedPoints[i + 1])
            if not splitNet.draftLine.isNull():
                splitNet.inheritNetName(inputNet)
                if is_selected:
                    splitNet.setSelected(True)
                if orthoNets:
                    splitNet.name = inputName
                    splitNet.nameStrength = inputStrength
                splitNetSet.add(splitNet)

        return True, splitNetSet

    def mergeNets(self, inputNet: snet.schematicNet) -> Tuple[
        bool, snet.schematicNet, set[snet.schematicNet]]:
        """
        Merges overlapping nets and returns the merged net.

        Returns:
            Optional[schematicNet]: The merged net if there are overlapping nets, otherwise returns self.
        """
        # Find other nets that overlap with self
        otherNets = inputNet.findOverlapNets()
        parallelNets = set()
        if otherNets:
            parallelNets = {netItem for netItem in otherNets if
                            inputNet.isParallel(netItem)} - {self}
        points = inputNet.sceneEndPoints
        nameConflict = False
        # If there are parallel nets
        if parallelNets:
            for netItem in parallelNets:
                nameConflict = not (inputNet.mergeNetNames(netItem))
                if nameConflict:
                    break
                points.extend(netItem.sceneEndPoints)
            if not nameConflict:
                furthestPoints = self.findFurthestPoints(points)
                returnNet = snet.schematicNet(*furthestPoints)
                return True, returnNet, parallelNets
            else:
                return False, inputNet, {}
        else:
            return False, inputNet, {}

    def findSnapPoint(self, eventLoc: QPoint, ignoredSet: set[snet.schematicNet]) -> QPoint:
        snapRect = QRect(eventLoc.x() - self.snapTuple[0], eventLoc.y() - self.snapTuple[1],
                         2 * self.snapTuple[0], 2 * self.snapTuple[1], )
        snapPoints = self.findConnectPoints(snapRect, ignoredSet)

        if self._newNet:
            snapPoints.update(self.findNetInterSect(self._newNet, snapRect))
        if snapPoints:
            lengths = [(snapPoint - eventLoc).manhattanLength() for snapPoint in snapPoints]
            closestPoint = list(snapPoints)[lengths.index(min(lengths))]
            return closestPoint
        else:
            return eventLoc

    def findConnectPoints(self, sceneRect: QRect, ignoredSet: set[QGraphicsItem]) -> set[
        QPoint]:
        snapPoints = set()
        rectItems = set(self.items(sceneRect)) - ignoredSet
        for item in rectItems:
            if isinstance(item, snet.schematicNet) and any(
                    list(map(sceneRect.contains, item.sceneEndPoints))):
                snapPoints.add(item.sceneEndPoints[
                    list(map(sceneRect.contains, item.sceneEndPoints)).index(True)])
            elif isinstance(item, shp.symbolPin):
                snapPoints.add(item.mapToScene(item.start).toPoint())
            elif isinstance(item, shp.schematicPin):
                snapPoints.add(item.mapToScene(item.start).toPoint())
        return snapPoints

    def findNetInterSect(self, inputNet: snet.schematicNet, rect: QRect) -> set[QPoint]:
        # Find all nets in the rectangle except the input net
        netsInSnapRectSet = {netItem for netItem in self.items(rect) if
                             isinstance(netItem, snet.schematicNet) and netItem.isOrthogonal(
                                 inputNet)}
        snapPointsSet = set()
        l1 = QLineF(inputNet.sceneEndPoints[0], inputNet.sceneEndPoints[1])
        unitVector = l1.unitVector()
        dx = unitVector.dx() if unitVector.dx() else 0
        dy = unitVector.dy() if unitVector.dy() else 0
        newEndX = l1.x2() + rect.width() * dx
        newEndY = l1.y2() + rect.height() * dy
        extendedL1 = QLineF(l1.p1(), QPointF(newEndX, newEndY))
        for netItem in netsInSnapRectSet:
            l2 = QLineF(netItem.sceneEndPoints[0], netItem.sceneEndPoints[1])
            (_, intersectPoint) = extendedL1.intersects(l2)
            if intersectPoint:
                snapPointsSet.add(intersectPoint.toPoint())
        return snapPointsSet

    def findNetStretchPoints(self, netItem: snet.schematicNet, snapDistance: int) -> dict[
        int, QPoint]:
        netEndPointsDict: dict[int, QPoint] = {}
        sceneEndPoints = netItem.sceneEndPoints
        for netEnd in sceneEndPoints:
            snapRect: QRect = QRect(netEnd.x() - snapDistance, netEnd.y() - snapDistance,
                                    2 * snapDistance, 2 * snapDistance, )
            snapRectItems = set(self.items(snapRect)) - {netItem}

            for item in snapRectItems:
                if isinstance(item, snet.schematicNet) and any(
                        list(map(snapRect.contains, item.sceneEndPoints))):
                    netEndPointsDict[sceneEndPoints.index(netEnd)] = netEnd
                elif (isinstance(item, shp.symbolPin) or isinstance(item,
                                                                    shp.schematicPin)) and snapRect.contains(
                    item.mapToScene(item.start).toPoint()):
                    netEndPointsDict[sceneEndPoints.index(netEnd)] = item.mapToScene(
                        item.start).toPoint()
                if netEndPointsDict.get(sceneEndPoints.index(
                    netEnd)):  # after finding one point, no need to iterate.
                    break
        return netEndPointsDict

    @staticmethod
    def orderPoints(points: list[QPoint]) -> list[QPoint]:
        currentPoint = points.pop(0)
        orderedPoints = [currentPoint]

        while points:
            distances = [(point - currentPoint).manhattanLength() for point in points]
            nearest_point_index = distances.index(min(distances))
            nearestPoint = points[nearest_point_index]
            orderedPoints.append(nearestPoint)
            currentPoint = points.pop(nearest_point_index)

        return orderedPoints

    @staticmethod
    def findFurthestPoints(points: list[QPoint]) -> tuple[QPoint, QPoint]:
        """
        Find the two points with the maximum distance between them.
        """
        max_distance = 0
        furthest_points = None

        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                distance = (points[i] - points[j]).manhattanLength()
                if distance > max_distance:
                    max_distance = distance
                    furthest_points = (points[i], points[j])

        return furthest_points[0], furthest_points[1]

    def _handleStretchNet(self, netItem: snet.schematicNet, stretchEnd: str):
        match stretchEnd:
            case "p2":
                self._stretchNet = snet.schematicNet(netItem.sceneEndPoints[0],
                    netItem.sceneEndPoints[1])
            case "p1":
                self._stretchNet = snet.schematicNet(netItem.sceneEndPoints[1],
                    netItem.sceneEndPoints[0])
        self._stretchNet.stretch = True
        self._stretchNet.inheritNetName(netItem)
        addDeleteStretchNetCommand = us.addDeleteShapeUndo(self, self._stretchNet, netItem)
        self.undoStack.push(addDeleteStretchNetCommand)

    def generatePinNetMap(self, sceneSymbolSet: set[shp.schematicSymbol]):
        """
        For symbols in sceneSymbolSet, find which pin is connected to which net. If a
        pin is not connected, assign to it a default net starting with d prefix.
        """
        netCounter = 0
        for symbolItem in sceneSymbolSet:
            for pinName, pinItem in symbolItem.pins.items():
                pinItem.connected = False  # clear connections
                pinConnectedNets = [netItem for netItem in
                    pinItem.collidingItems(mode=Qt.IntersectsItemBoundingRect) if
                    isinstance(netItem, snet.schematicNet)]
                # this will name the pin by first net it finds in the bounding rectangle of
                # the pin. If there are multiple nets in the bounding rectangle, the first
                # net in the list will be the one used.
                if pinConnectedNets:
                    symbolItem.pinNetMap[pinName] = pinConnectedNets[0].name
                    pinItem.connected = True

                if not pinItem.connected:
                    # assign a default net name prefixed with d(efault).
                    symbolItem.pinNetMap[pinName] = f"dnet{netCounter}"
                    self.logger.warning(f"left unconnected:{symbolItem.pinNetMap[pinName]}")
                    netCounter += 1
            # now reorder pinNetMap according pinOrder attribute
            if symbolItem.symattrs.get("pinOrder"):
                pinOrderList = list()
                [pinOrderList.append(item.strip()) for item in
                    symbolItem.symattrs.get("pinOrder").split(",")]
                symbolItem.pinNetMap = {pinName: symbolItem.pinNetMap[pinName] for pinName
                    in pinOrderList}

    def findSceneSymbolSet(self) -> set[shp.schematicSymbol]:
        """
        Find all the symbols on the scene as a set.
        """
        return {item for item in self.items() if isinstance(item, shp.schematicSymbol)}

    def findSceneNetsSet(self) -> set[snet.schematicNet]:
        return {item for item in self.items() if isinstance(item, snet.schematicNet)}

    def findRectSymbolPin(self, rect: Union[QRect, QRectF]) -> set[shp.symbolPin]:
        pinsRectSet = {item for item in self.items(rect) if isinstance(item, shp.symbolPin)}
        return pinsRectSet

    def findSceneSchemPinsSet(self) -> set[shp.schematicPin]:
        pinsSceneSet = {item for item in self.items() if isinstance(item, shp.schematicPin)}
        if pinsSceneSet:  # check pinsSceneSet is empty
            return pinsSceneSet
        else:
            return set()

    def findSceneTextSet(self) -> set[shp.text]:
        if textSceneSet := {item for item in self.items() if isinstance(item, shp.text)}:
            return textSceneSet
        else:
            return set()

    def addStretchWires(self, start: QPoint, end: QPoint) -> List["snet.schematicNet"]:
        """
        Add a trio of wires between two points.

        Args:
            start (QPoint): The starting point of the wire.
            end (QPoint): The ending point of the wire.

        Returns:
            List[snet.schematicNet]: A list of schematic net objects representing the wires.
        """
        try:
            if start == end:
                self.logger.warning("Start and end points are the same. No wire added.")
                return []

            if start.y() == end.y() or start.x() == end.x():
                # Horizontal or vertical line
                return [snet.schematicNet(start, end)]

            # Calculate intermediate points
            firstPointX = self.snapToBase((end.x() - start.x()) / 3 + start.x(),
                self.snapTuple[0])
            firstPoint = QPoint(firstPointX, start.y())
            secondPoint = QPoint(firstPointX, end.y())

            # Create wire segments
            lines = []
            segments = [(start, firstPoint), (firstPoint, secondPoint),
                (secondPoint, end), ]
            for seg_start, seg_end in segments:
                if seg_start != seg_end:
                    lines.append(snet.schematicNet(seg_start, seg_end))

            return lines

        except Exception as e:
            self.logger.error(f"Error in addStretchWires: {e}", exc_info=True)
            return []

    def addPin(self, pos: QPoint) -> shp.schematicPin:
        try:
            pin = shp.schematicPin(pos, self.pinName, self.pinDir, self.pinType)
            self.addUndoStack(pin)
            return pin
        except Exception as e:
            self.logger.error(f"Pin add error: {e}")

    def addNote(self, pos: QPoint) -> shp.text:
        """
        Changed the method name not to clash with qgraphicsscene addText method.
        """
        text = shp.text(pos, self.noteText, self.noteFontFamily, self.noteFontStyle,
            self.noteFontSize, self.noteAlign, self.noteOrient, )
        self.addUndoStack(text)
        return text

    def drawInstance(self, pos: QPoint):
        """
        Add an instance of a symbol to the scene.
        """
        instance = self.instSymbol(pos)
        if instance:  # Add check for None
            self.instanceCounter += 1
            self.addUndoStack(instance)
        return instance

    def instSymbol(self, pos: QPoint):
        view_path = self.instanceSymbolTuple.viewItem.viewPath

        try:
            # Try to get items from cache first
            items = self._symbolCache.get(view_path)
            if items is None:
                with open(view_path, "r") as temp:
                    items = json.load(temp)
                    self._symbolCache[view_path] = items

            if items[0]["cellView"] != "symbol":
                self.logger.error("Not a symbol!")
                return None

            # Use comprehensions for better performance
            itemAttributes = {
                item["nam"]: item["def"]
                for item in items[2:]
                if item["type"] == "attr"
            }

            itemShapes = [
                lj.symbolItems(self).create(item)
                for item in items[2:]
                if item["type"] != "attr"
            ]

            symbolInstance = shp.schematicSymbol(itemShapes, itemAttributes)

            # Batch property assignments
            instance_properties = {
                "pos": pos,
                "counter": self.instanceCounter,
                "instanceName": f"I{self.instanceCounter}",
                "libraryName": self.instanceSymbolTuple.libraryItem.libraryName,
                "cellName": self.instanceSymbolTuple.cellItem.cellName,
                "viewName": self.instanceSymbolTuple.viewItem.viewName
            }

            for prop, value in instance_properties.items():
                setattr(symbolInstance, prop, value)

            # Process labels
            for labelItem in symbolInstance.labels.values():
                labelItem.labelDefs()

            return symbolInstance

        except FileNotFoundError:
            self.logger.error(f"Symbol file not found: {view_path}")
            return None
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in symbol file: {view_path}")
            return None
        except Exception as e:
            self.logger.warning(f"instantiation error: {e}")
            return None

    def copySelectedItems(self):
        selectedItems = [item for item in self.selectedItems() if item.parentItem() is None]
        if selectedItems:
            for item in selectedItems:
                selectedItemJson = json.dumps(item, cls=schenc.schematicEncoder)
                itemCopyDict = json.loads(selectedItemJson)
                shape = lj.schematicItems(self).create(itemCopyDict)
                if shape is not None:
                    item.setSelected(False)
                    self.addUndoStack(shape)
                    shape.setSelected(True)
                    # shift position by four grid units to right and down
                    shape.setPos(QPoint(item.pos().x() + 4 * self.snapTuple[0],
                                        item.pos().y() + 4 * self.snapTuple[1], ))
                    if isinstance(shape, shp.schematicSymbol):
                        self.instanceCounter += 1
                        shape.instanceName = f"I{self.instanceCounter}"
                        shape.counter = int(self.instanceCounter)
                        [label.labelDefs() for label in shape.labels.values()]

    def saveSchematic(self, file: pathlib.Path):
        """
        Save the schematic to a file.

        Args:
            file (pathlib.Path): The file path to save the schematic to.

        Raises:
            Exception: If there was an error saving the schematic.
        """
        try:
            self.removeItem(self._snapPointRect)
            topLevelItems = []
            # Insert a cellview item at the beginning of the list
            topLevelItems.insert(0, {"viewType": "schematic"})
            topLevelItems.insert(1, {"snapGrid": self.snapTuple})
            topLevelItems.extend(
                [item for item in self.items() if item.parentItem() is None])
            with file.open(mode="w") as f:
                json.dump(topLevelItems, f, cls=schenc.schematicEncoder, indent=4)
            # if there is a parent editor, to reload the changes.
            if self.editorWindow.parentEditor is not None:
                editorType = self.findEditorTypeString(self.editorWindow.parentEditor)
                if editorType == "schematicEditor":
                    self.editorWindow.parentEditor.loadSchematic()
            self._snapPointRect.setVisible(False)
            self.addItem(self._snapPointRect)

            self.logger.info(f"Saved schematic to {self.editorWindow.cellName}"
                             f":{self.editorWindow.viewName}")
        except Exception as e:
            self.logger.error(e)

    @staticmethod
    def findEditorTypeString(editorWindow):
        """
        This function returns the type of the parent editor as a string.
        The type of the parent editor is determined by finding the last dot in the
        string representation of the type of the parent editor and returning the
        string after the last dot. If there is no dot in the string representation
        of the type of the parent editor, the entire string is returned.
        """
        index: int = str(type(editorWindow)).rfind(".")
        if index == -1:
            return str(type(editorWindow))
        else:
            return str(type(editorWindow))[index + 1: -2]

    def loadSchematic(self, filePathObj: pathlib.Path) -> None:
        """
        load schematic from item list
        """
        try:
            with filePathObj.open("r") as file:
                decodedData = json.load(file)

            # Unpack grid settings
            _, gridSettings, *itemData = decodedData
            snapGrid = gridSettings.get("snapGrid", [10, 10])
            self.majorGrid, self.snapGrid = snapGrid
            self.snapTuple = (self.snapGrid, self.snapGrid)
            self.snapDistance = 2 * self.snapGrid

            startTime = time.perf_counter()
            self.createSchematicItems(itemData)
            endTime = time.perf_counter()

            self.logger.info(f"Load time: {endTime - startTime:.4f} seconds")
            viewCenter = self.views()[0].viewRect.center()
            self._snapPointRect.setPos(viewCenter)
            self.addItem(self._snapPointRect)
        except Exception as e:
            self.logger.error(f"Cannot load layout: {e}")

    def createSchematicItems(self, itemsList: List[Dict]):
        shapesList = list()
        for itemDict in itemsList:
            itemShape = lj.schematicItems(self).create(itemDict)
            if (isinstance(itemShape,
                           shp.schematicSymbol) and itemShape.counter > self.instanceCounter):
                self.instanceCounter = itemShape.counter
                # increment item counter for next symbol
                self.instanceCounter += 1
            shapesList.append(itemShape)
        # self.undoStack.push(us.loadShapesUndo(self, shapesList))
        for itemShape in shapesList:
            self.addItem(itemShape)

    def reloadScene(self):
        topLevelItems = [item for item in self.items() if item.parentItem() is None]
        # Insert a layout item at the beginning of the list
        topLevelItems.insert(0, {"viewType": "schematic"})
        topLevelItems.insert(1, {"snapGrid": self.snapTuple})
        _, _, *itemData = json.loads(json.dumps(topLevelItems, cls=schenc.schematicEncoder))
        self.clear()
        self.createSchematicItems(itemData)

    def viewObjProperties(self):
        """
        Display the properties of the selected object.
        """
        try:
            selectedItems = [item for item in self.selectedItems() if
                item.parentItem() is None]
            if selectedItems:
                for item in selectedItems:
                    item.prepareGeometryChange()
                    if isinstance(item, shp.schematicSymbol):
                        self.setInstanceProperties(item)
                    elif isinstance(item, snet.schematicNet):
                        self.setNetProperties(item)
                    elif isinstance(item, shp.text):
                        self.setTextProperties(item)
                    elif isinstance(item, shp.schematicPin):
                        self.setSchematicPinProperties(item)
        except Exception as e:
            self.logger.error(e)

    def setInstanceProperties(self, item: shp.schematicSymbol):
        dlg = pdlg.instanceProperties(self.editorWindow)
        dlg.libNameEdit.setText(item.libraryName)
        dlg.cellNameEdit.setText(item.cellName)
        dlg.viewNameEdit.setText(item.viewName)
        dlg.instNameEdit.setText(item.instanceName)
        location = (item.scenePos() - self.origin).toTuple()
        dlg.xLocationEdit.setText(str(location[0]))
        dlg.yLocationEdit.setText(str(location[1]))
        dlg.angleEdit.setText(str(item.angle))
        row_index = 0
        # iterate through the item labels.
        for label in item.labels.values():
            if label.labelDefinition not in lbl.symbolLabel.predefinedLabels:
                dlg.instanceLabelsLayout.addWidget(edf.boldLabel(label.labelName[1:], dlg),
                    row_index, 0)
                labelValueEdit = edf.longLineEdit()
                labelValueEdit.setText(str(label.labelValue))
                dlg.instanceLabelsLayout.addWidget(labelValueEdit, row_index, 1)
                visibleCombo = QComboBox(dlg)
                visibleCombo.setInsertPolicy(QComboBox.NoInsert)
                visibleCombo.addItems(["True", "False"])
                if label.labelVisible:
                    visibleCombo.setCurrentIndex(0)
                else:
                    visibleCombo.setCurrentIndex(1)
                dlg.instanceLabelsLayout.addWidget(visibleCombo, row_index, 2)
                row_index += 1
        # now list instance attributes
        for counter, name in enumerate(item.symattrs.keys()):
            dlg.instanceAttributesLayout.addWidget(edf.boldLabel(name, dlg), counter, 0)
            labelType = edf.longLineEdit()
            labelType.setReadOnly(True)
            labelNameEdit = edf.longLineEdit()
            labelNameEdit.setText(item.symattrs.get(name))
            labelNameEdit.setToolTip(f"{name} attribute (Read Only)")
            dlg.instanceAttributesLayout.addWidget(labelNameEdit, counter, 1)
        if dlg.exec() == QDialog.Accepted:
            selectedItemJson = json.dumps(item, cls=schenc.schematicEncoder)
            itemCopyDict = json.loads(selectedItemJson)
            newInstance = lj.schematicItems(self).create(itemCopyDict)
            if newInstance is not None:

                newInstance.instanceName = dlg.instNameEdit.text().strip()
                newInstance.angle = float(dlg.angleEdit.text().strip())
                location = QPoint(int(float(dlg.xLocationEdit.text().strip())),
                    int(float(dlg.yLocationEdit.text().strip())), )
                tempDoc = QTextDocument()
                for i in range(dlg.instanceLabelsLayout.rowCount()):
                    # first create label name document with HTML annotations
                    tempDoc.setHtml(
                        dlg.instanceLabelsLayout.itemAtPosition(i, 0).widget().text())
                    # now strip html annotations
                    tempLabelName = f"@{tempDoc.toPlainText().strip()}"
                    # check if label name is in label dictionary of item.
                    if newInstance.labels.get(tempLabelName):
                        # this is where the label value is set.
                        newInstance.labels[tempLabelName].labelValue = (
                            dlg.instanceLabelsLayout.itemAtPosition(i, 1).widget().text())
                        visible = (dlg.instanceLabelsLayout.itemAtPosition(i,
                                                                           2).widget().currentText())
                        if visible == "True":
                            newInstance.labels[tempLabelName].labelVisible = True
                        else:
                            newInstance.labels[tempLabelName].labelVisible = False
                [labelItem.labelDefs() for labelItem in newInstance.labels.values()]
                newInstance.setPos(self.snapToGrid(location - self.origin, self.snapTuple))
                self.undoStack.push(us.addDeleteShapeUndo(self, newInstance, item))

    def setNetProperties(self, netItem: snet.schematicNet):
        dlg = pdlg.netProperties(self.editorWindow)
        dlg.netStartPointEditX.setText(
            str(round(netItem.mapToScene(netItem.draftLine.p1()).x())))
        dlg.netStartPointEditY.setText(
            str(round(netItem.mapToScene(netItem.draftLine.p1()).y())))
        dlg.netEndPointEditX.setText(
            str(round(netItem.mapToScene(netItem.draftLine.p2()).x())))
        dlg.netEndPointEditY.setText(
            str(round(netItem.mapToScene(netItem.draftLine.p2()).y())))
        dlg.netNameEdit.setText(netItem.name)

        if dlg.exec() == QDialog.Accepted:
            netname = dlg.netNameEdit.text().strip()
            netStartX = float(dlg.netStartPointEditX.text())
            netStartY = float(dlg.netStartPointEditY.text())
            netStart = self.snapToGrid(QPoint(netStartX, netStartY), self.snapTuple)
            netEndX = float(dlg.netEndPointEditX.text())
            netEndY = float(dlg.netEndPointEditY.text())
            netEnd = self.snapToGrid(QPoint(netEndX, netEndY), self.snapTuple)
            newNet = snet.schematicNet(netStart, netEnd, netItem.mode)
            newNet.nameStrength = snet.netNameStrengthEnum.SET
            newNet.name = netname
            self.undoStack.push(us.addDeleteNetUndo(self, newNet, netItem))

    def setTextProperties(self, item):
        dlg = pdlg.noteTextEdit(self.editorWindow)
        dlg.plainTextEdit.setText(item.textContent)
        dlg.familyCB.setCurrentText(item.fontFamily)
        dlg.fontStyleCB.setCurrentText(item.fontStyle)
        dlg.fontsizeCB.setCurrentText(item.textHeight)
        dlg.textAlignmCB.setCurrentText(item.textAlignment)
        dlg.textOrientCB.setCurrentText(item.textOrient)
        if dlg.exec() == QDialog.Accepted:
            # item.prepareGeometryChange()
            start = item.mapToScene(item.start)
            newText = shp.text(start, dlg.plainTextEdit.toPlainText(),
                dlg.familyCB.currentText(), dlg.fontStyleCB.currentText(),
                dlg.fontsizeCB.currentText(), dlg.textAlignmCB.currentText(),
                dlg.textOrientCB.currentText(), )
            self.rotateAnItem(start, newText, int(float(item.textOrient[1:])))
            self.undoStack.push(us.addDeleteShapeUndo(self, newText, item))
        return item

    def setSchematicPinProperties(self, item: shp.schematicPin):
        dlg = pdlg.schematicPinPropertiesDialog(self.editorWindow)
        dlg.pinName.setText(item.pinName)
        dlg.pinDir.setCurrentText(item.pinDir)
        dlg.pinType.setCurrentText(item.pinType)
        dlg.angleEdit.setText(str(item.angle))
        dlg.xlocationEdit.setText(str(item.mapToScene(item.start).x()))
        dlg.ylocationEdit.setText(str(item.mapToScene(item.start).y()))
        if dlg.exec() == QDialog.Accepted:
            pinName = dlg.pinName.text().strip()
            pinDir = dlg.pinDir.currentText()
            pinType = dlg.pinType.currentText()
            itemStartPos = QPoint(int(float(dlg.xlocationEdit.text().strip())),
                int(float(dlg.ylocationEdit.text().strip())), )
            start = self.snapToGrid(itemStartPos - self.origin, self.snapTuple)
            angle = float(dlg.angleEdit.text().strip())
            newPin = shp.schematicPin(start, pinName, pinDir, pinType)
            newPin.angle = angle
            self.undoStack.push(us.addDeleteShapeUndo(self, newPin, item))

    def hilightNets(self):
        """
        Show the connections the selected items.
        """
        try:
            self.highlightNets = bool(self.editorWindow.hilightNetAction.isChecked())
        except Exception as e:
            self.logger.error(e)

    def goDownHier(self):
        """
        Go down the hierarchy, opening the selected view.
        """
        if isinstance(self.selectedSymbol, shp.schematicSymbol):
            dlg = fd.goDownHierDialogue(self.editorWindow)
            libItem = libm.getLibItem(self.editorWindow.libraryView.libraryModel,
                self.selectedSymbol.libraryName)
            cellItem = libm.getCellItem(libItem, self.selectedSymbol.cellName)
            viewNames = [cellItem.child(i).text() for i in range(cellItem.rowCount()) if
                "schematic" in cellItem.child(i).text() or "symbol" in cellItem.child(
                    i).text()]
            dlg.viewListCB.addItems(viewNames)
            if dlg.exec() == QDialog.Accepted:
                libItem = libm.getLibItem(self.editorWindow.libraryView.libraryModel,
                    self.selectedSymbol.libraryName)
                cellItem = libm.getCellItem(libItem, self.selectedSymbol.cellName)
                viewItem = libm.getViewItem(cellItem, dlg.viewListCB.currentText())
                openViewTuple = (
                    self.editorWindow.libraryView.libBrowsW.openCellView(viewItem, cellItem,
                        libItem))
                if viewItem.viewType == "schematic":
                    parentInstanceName = [labelItem.labelValue for labelItem in
                                          self.selectedSymbol.labels.values() if
                                          labelItem.labelType == "NLPLabel" and labelItem.labelDefinition == "[@instName]"][
                        0]
                    self.editorWindow.appMainW.openViews[
                        openViewTuple].centralW.scene.hierarchyTrail = f'{self.hierarchyTrail}{parentInstanceName}.'
                if self.editorWindow.appMainW.openViews[openViewTuple]:
                    childWindow = self.editorWindow.appMainW.openViews[openViewTuple]
                    childWindow.parentEditor = self.editorWindow
                    childWindow.parentObj = self.selectedSymbol
                    childWindowType = self.findEditorTypeString(childWindow)

                    if childWindowType == "symbolEditor":
                        childWindow.symbolToolbar.addAction(childWindow.goUpAction)
                    elif childWindowType == "schematicEditor":
                        childWindow.schematicToolbar.addAction(childWindow.goUpAction)
                    if dlg.buttonId == 2:
                        childWindow.centralW.scene.readOnly = True

    def ignoreSymbol(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                if isinstance(item, shp.schematicSymbol):
                    item.netlistIgnore = not item.netlistIgnore
        else:
            self.logger.warning("No symbol selected")

    def selectInRectItems(self, selectionRect: QRect, partialSelection=False):
        """
        Select items in the scene.
        """

        mode = Qt.IntersectsItemShape if partialSelection else Qt.ContainsItemShape
        if self.selectModes.selectAll:
            [item.setSelected(True) for item in self.items(selectionRect, mode=mode)]
        elif self.selectModes.selectDevice:
            [item.setSelected(True) for item in self.items(selectionRect, mode=mode) if
                isinstance(item, shp.schematicSymbol)]
        elif self.selectModes.selectNet:
            [item.setSelected(True) for item in self.items(selectionRect, mode=mode) if
                isinstance(item, snet.schematicNet)]
        elif self.selectModes.selectPin:
            [item.setSelected(True) for item in self.items(selectionRect, mode=mode) if
                isinstance(item, shp.schematicPin)]

    def renumberInstances(self):

        symbolList = [item for item in self.items() if
            isinstance(item, shp.schematicSymbol)]
        self.instanceCounter = 0
        for symbolInstance in symbolList:
            symbolInstance.counter = self.instanceCounter
            if symbolInstance.instanceName.startswith("I"):
                symbolInstance.instanceName = f"I{symbolInstance.counter}"
                self.instanceCounter += 1
        self.reloadScene()

    def nameSceneNets(self):
        """
        Name all nets in the scene.
        """
        self.netCounter = 0
        schematicSymbolSet = self.findSceneSymbolSet()
        sceneNetsSet: Set[snet.schematicNet] = self.findSceneNetsSet()
        self.clearNetStatus(sceneNetsSet)
        globalNetsSet = self.findGlobalNets(schematicSymbolSet)
        sceneNetsSet -= globalNetsSet
        schemPinConNetsSet = self.findSchPinNets()
        sceneNetsSet -= schemPinConNetsSet
        namedNetsSet = set(itt.filterfalse(lambda x: x.nameStrength.value != 3,
                                          sceneNetsSet))
        sceneNetsSet -= namedNetsSet
        nameSeedsSet = globalNetsSet | namedNetsSet | schemPinConNetsSet
        sceneNetsSet = self.groupNamedNets(nameSeedsSet, sceneNetsSet)
        self.netCounter = self.groupUnnamedNets(sceneNetsSet, self.netCounter)


    def traverseNets(self, netItem: snet.schematicNet,
            otherNetsSet: Set[snet.schematicNet]) -> Tuple[
        Set[snet.schematicNet], Set[snet.schematicNet]]:
        """
        Traverse the schematic to find all connected nets starting from a given set.

        This function uses an iterative approach to avoid potential stack overflow
        issues with large schematics. It continues to search for connected nets
        until no new connections are found.

        Args:
            connectedSet: Set of initially connected nets.
            otherNetsSet: Set of other nets to check for connections.

        Returns:
            A tuple containing:
            - The final set of all connected nets.
            - The remaining set of unconnected nets.
        """
        while True:
            newFoundConnectedSet = set()
            connectedNetsSet = {netItem2 for netItem2 in otherNetsSet if
                self.checkNetConnect(netItem, netItem2)}
            for connectedNet in connectedNetsSet:
                if connectedNet.inheritNetName(netItem):
                    newFoundConnectedSet.add(connectedNet)
            if not newFoundConnectedSet:
                break
            otherNetsSet -= newFoundConnectedSet
            for netItem in newFoundConnectedSet:
                self.traverseNets(netItem, otherNetsSet)
        return otherNetsSet

    # Net finding methods
    def findGlobalNets(self, symbolSet: set[shp.schematicSymbol]) -> set[snet.schematicNet]:
        """
        This method finds all nets connected to global pins.
        """
        try:
            globalPinsSet = set()
            globalNetsSet = set()
            for symbolItem in symbolSet:
                for pinName, pinItem in symbolItem.pins.items():
                    if pinName[-1] == "!":
                        globalPinsSet.add(pinItem)
            for pinItem in globalPinsSet:
                pinNetSet = {netItem for netItem in pinItem.collidingItems(Qt.IntersectsItemShape)
                    if isinstance(netItem, snet.schematicNet)}
                for netItem in pinNetSet:
                    if netItem.nameStrength.value == 3:
                        if netItem.name != pinItem.pinName:
                            netItem.nameConflict = True
                            self.logger.error(f"Net name conflict at"
                                                   f" {pinItem.pinName} of "
                                              f"{pinItem.parent.instanceName}.")
                        else:
                            globalNetsSet.add(netItem)
                    else:
                        globalNetsSet.add(netItem)
                        netItem.name = pinItem.pinName
                        netItem.nameStrength = snet.netNameStrengthEnum.INHERIT
            return globalNetsSet

        except Exception as e:
            self.logger.error(f"Error in global nets:{e}")

    def findSchPinNets(self) -> set[snet.schematicNet]:
        # nets connected to schematic pins.
        schemPinConNetsSet = set()
        sceneSchemPinsSet = self.findSceneSchemPinsSet()
        for sceneSchemPin in sceneSchemPinsSet:
            pinNetSet = {netItem for netItem in
                self.items(sceneSchemPin.sceneBoundingRect()) if
                isinstance(netItem, snet.schematicNet)}
            for netItem in pinNetSet:
                if netItem.nameStrength.value == 3:
                    if netItem.name == sceneSchemPin.pinName:
                        schemPinConNetsSet.add(netItem)
                    else:
                        netItem.nameConflict = True
                        self.logger.error(
                            f"Net name conflict at {sceneSchemPin.pinName} of "
                            f"{sceneSchemPin.parent().instanceName}.")
                else:
                    schemPinConNetsSet.add(netItem)
                    netItem.name = sceneSchemPin.pinName
                    netItem.nameStrength = snet.netNameStrengthEnum.INHERIT
                netItem.update()
            schemPinConNetsSet.update(pinNetSet)
        return schemPinConNetsSet

    def findConnectedNetSet(self, startNet: snet.schematicNet, netSet: Set[snet.schematicNet]) -> Set[snet.schematicNet]:
        """
        find all the nets connected to a net including nets connected by name.
        """
        connectedSet, otherNetsSet = self.traverseNets({startNet}, netSet)
        # now check if any other name is connected due to a common name:
        for netItem in otherNetsSet:
            if netItem.name == startNet.name and (netItem.nameStrength.value > 1):
                connectedSet.add(netItem)
        return connectedSet - {startNet}

    # Net grouping methods
    def groupNamedNets(self, namedNetsSet: Set[snet.schematicNet],
            unnamedNetsSet: Set[snet.schematicNet]) -> Set[snet.schematicNet]:
        """
        Groups nets with the same name using namedNetsSet members as seeds and going
        through connections. Returns the set of still unnamed nets.
        """
        for netItem in namedNetsSet:
            unnamedNetsSet = self.traverseNets(netItem, unnamedNetsSet )
        return unnamedNetsSet

    def groupUnnamedNets(self, unnamedNetsSet: set[snet.schematicNet], nameCounter: int):
        """
        Groups nets together if they are connected and assign them default names
        if they don't have a name assigned.
        """
        try:
            initialNet = unnamedNetsSet.pop()
        except KeyError:  # initialNet set is empty
            return
        else:
            initialNet.name = "net" + str(nameCounter)
            initialNet.nameStrength = snet.netNameStrengthEnum.INHERIT
            unnamedNetsSet = self.traverseNets(initialNet, unnamedNetsSet )
            print(nameCounter)
            nameCounter += 1
            if len(unnamedNetsSet) > 1:
                self.groupUnnamedNets(unnamedNetsSet, nameCounter)
            elif len(unnamedNetsSet) == 1:
                lastNet = unnamedNetsSet.pop()
                lastNet.name = "net" + str(nameCounter)
                lastNet.nameStrength = snet.netNameStrengthEnum.INHERIT
        return nameCounter
    # Main method

    @staticmethod
    def checkNetConnect(netItem, otherNetItem):
        """
        Determine if a net is connected to another one. One net should end on the other net.
        """
        if otherNetItem is not netItem:
            for netItemEnd, otherEnd in itt.product(netItem.sceneEndPoints,
                    otherNetItem.sceneEndPoints):
                # not a very elegant solution to mistakes in net end points.
                if (netItemEnd - otherEnd).manhattanLength() <= 1:
                    return True
        else:
            return False

    @staticmethod
    def clearNetStatus(netsSet: set[snet.schematicNet]):
        """
        Clear all assigned net names
        """
        for netItem in netsSet:
            netItem.nameConflict = False
            if netItem.nameStrength.value < 3:
                netItem.nameStrength = snet.netNameStrengthEnum.NONAME

    # @staticmethod
    # def checkPinNetConnect(pinItem: shp.schematicPin, netItem: snet.schematicNet):
    #     """
    #     Determine if a pin is connected to a net.
    #     """
    #     return bool(pinItem.sceneBoundingRect().intersects(netItem.sceneBoundingRect()))
