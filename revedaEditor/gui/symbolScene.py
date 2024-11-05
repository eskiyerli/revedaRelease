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

# from hashlib import new
import json
import os

# from hashlib import new
import pathlib
from copy import deepcopy
from typing import List

from dotenv import load_dotenv

# import numpy as np
from PySide6.QtCore import (
    QLineF,
    QPoint,
    QPointF,
    QRectF,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QPen,
)
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsLineItem,
    QGraphicsSceneMouseEvent,
)

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.undoStack as us
import revedaEditor.common.labels as lbl
import revedaEditor.common.shapes as shp  # import the shapes
import revedaEditor.fileio.loadJSON as lj
import revedaEditor.fileio.symbolEncoder as symenc
import revedaEditor.gui.propertyDialogues as pdlg
from revedaEditor.gui.editorScene import editorScene

load_dotenv()


# noinspection PyUnresolvedReferences
class symbolScene(editorScene):
    """
    Scene for Symbol editor.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        # drawing modes
        self.editModes = ddef.symbolModes(
            selectItem=True,
            deleteItem=False,
            moveItem=False,
            copyItem=False,
            rotateItem=False,
            changeOrigin=False,
            panView=False,
            drawPin=False,
            drawArc=False,
            drawRect=False,
            drawLine=False,
            addLabel=False,
            drawCircle=False,
            drawPolygon=False,
            stretchItem=False,
        )

        self.symbolShapes = ["line", "arc", "rect", "circle", "pin", "label", "polygon"]

        self.origin = QPoint(0, 0)
        # some default attributes
        self.newPin = None
        self.pinName = ""
        self.pinType = shp.symbolPin.pinTypes[0]
        self.pinDir = shp.symbolPin.pinDirs[0]
        self.labelDefinition = ""
        self.labelType = lbl.symbolLabel.labelTypes[0]
        self.labelOrient = lbl.symbolLabel.labelOrients[0]
        self.labelAlignment = lbl.symbolLabel.labelAlignments[0]
        self.labelUse = lbl.symbolLabel.labelUses[0]
        self.labelVisible = False
        self.labelHeight = "12"
        self.labelOpaque = True
        self.newLine = None
        self.newRect = None
        self.newCirc = None
        self.newArc = None
        self.newPolygon = None
        self.polygonGuideLine = None

    @property
    def drawMode(self):
        return any(
            (
                self.editModes.drawPin,
                self.editModes.drawArc,
                self.editModes.drawLine,
                self.editModes.drawRect,
                self.editModes.drawCircle,
                self.editModes.drawPolygon,
            )
        )

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(mouse_event)
        try:
            self.viewRect = self.parent.view.mapToScene(
                self.parent.view.viewport().rect()
            ).boundingRect()
            if mouse_event.button() == Qt.LeftButton:
                self.mousePressLoc = self.snapToGrid(
                    mouse_event.scenePos().toPoint(), self.snapTuple
                )
                if self.editModes.changeOrigin:  # change origin of the symbol
                    self.origin = self.mousePressLoc
                    self.editModes.changeOrigin = False
                # if self.editModes.selectItem:
                #     self.selectSceneItems(modifiers)
                if self.editModes.drawPin:
                    self.editorWindow.messageLine.setText("Add Symbol Pin")
                    self.newPin = self.pinDraw(self.mousePressLoc)
                    self.newPin.setSelected(True)
                elif self.editModes.drawLine:
                    self.newLine.setSelected(False)
                    self.newLine = None
                elif self.editModes.addLabel:
                    self.newLabel = self.labelDraw(
                        self.mousePressLoc,
                        self.labelDefinition,
                        self.labelType,
                        self.labelHeight,
                        self.labelAlignment,
                        self.labelOrient,
                        self.labelUse,
                    )
                    self.newLabel.setSelected(True)
                elif self.editModes.drawRect:
                    self.newRect = self.rectDraw(self.mousePressLoc, self.mousePressLoc)
                elif self.editModes.drawCircle:
                    self.editorWindow.messageLine.setText(
                        "Click on the center of the circle"
                    )
                    self.newCircle = self.circleDraw(
                        self.mousePressLoc, self.mousePressLoc
                    )
                elif self.editModes.drawPolygon:
                    if self.newPolygon is None:
                        # Create a new polygon
                        self.newPolygon = shp.symbolPolygon(
                            [self.mousePressLoc, self.mousePressLoc],
                        )
                        self.addUndoStack(self.newPolygon)
                        # Create a guide line for the polygon
                        self.polygonGuideLine = QGraphicsLineItem(
                            QLineF(
                                self.newPolygon.points[-2], self.newPolygon.points[-1]
                            )
                        )
                        self.polygonGuideLine.setPen(
                            QPen(QColor(255, 255, 0), 1, Qt.DashLine)
                        )
                        self.addUndoStack(self.polygonGuideLine)

                    else:
                        self.newPolygon.addPoint(self.mousePressLoc)
                elif self.editModes.drawArc:
                    self.editorWindow.messageLine.setText("Start drawing an arc")
                    self.newArc = self.arcDraw(self.mousePressLoc, self.mousePressLoc)
                if self.editModes.rotateItem:
                    self.editorWindow.messageLine.setText("Rotate item")
                    if self.selectedItems():
                        self.rotateSelectedItems(self.mousePressLoc)
        except Exception as e:
            self.logger.error(f"Error in mousePressEvent: {e}")

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(mouse_event)
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        if mouse_event.buttons() == Qt.LeftButton:
            if self.editModes.drawPin and self.newPin.isSelected():
                self.newPin.setPos(self.mouseMoveLoc - self.mousePressLoc)
            elif self.editModes.drawRect:
                self.editorWindow.messageLine.setText(
                    "Release mouse on the bottom left point"
                )
                self.newRect.end = self.mouseMoveLoc
            elif self.editModes.drawCircle:
                self.editorWindow.messageLine.setText("Extend Circle")
                radius = (
                                 (self.mouseMoveLoc.x() - self.mousePressLoc.x()) ** 2
                                 + (self.mouseMoveLoc.y() - self.mousePressLoc.y()) ** 2
                         ) ** 0.5
                self.newCircle.radius = radius
            elif self.editModes.drawArc:
                self.editorWindow.messageLine.setText("Extend Arc")
                self.newArc.end = self.mouseMoveLoc
            elif self.editModes.selectItem and modifiers == Qt.ShiftModifier:
                self._selectionRectItem.setRect(
                    QRectF(self.mousePressLoc, self.mouseMoveLoc)
                )
        else:
            if (
                    self.editModes.drawPolygon
                    and self.newPolygon is not None
                    and self.polygonGuideLine
            ):
                self.polygonGuideLine.setLine(
                    QLineF(self.newPolygon.points[-1], self.mouseMoveLoc)
                )
            elif self.editModes.drawLine and self.newLine is not None:
                self.editorWindow.messageLine.setText("Release mouse on the end point")
                self.newLine.end = self.mouseMoveLoc
        self.statusLine.showMessage(
            f"Cursor Position: {(self.mouseMoveLoc - self.origin).toTuple()}"
        )

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        try:
            self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
            modifiers = QGuiApplication.keyboardModifiers()
            if mouse_event.button() == Qt.LeftButton:
                if self.editModes.drawLine:
                    self.editorWindow.messageLine.setText("Drawing a Line")
                    self.newLine = self.lineDraw(self.mousePressLoc, self.mousePressLoc)
                    self.newLine.setSelected(True)

                elif self.editModes.drawCircle:
                    self.newCircle.setSelected(False)
                    self.newCircle.update()
                elif self.editModes.drawPin:
                    self.newPin.setSelected(False)
                    self.newPin = None
                elif self.editModes.drawRect:
                    self.newRect.setSelected(False)
                elif self.editModes.drawArc:
                    self.newArc.setSelected(False)
                elif self.editModes.addLabel:
                    self.newLabel.setSelected(False)
                    self.editModes.addLabel = False
        except Exception as e:
            self.logger.error(f"Error in Mouse Press Event: {e} ")

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseDoubleClickEvent(event)
        self.mouseDoubleClickLoc = event.scenePos().toPoint()
        try:
            if event.button() == Qt.LeftButton and self.editModes.drawPolygon:
                self.newPolygon.polygon.remove(0)
                self.newPolygon.points.pop(0)
                self.editModes.setMode("selectItem")
                self.newPolygon = None
                self.removeItem(self.polygonGuideLine)
                self.polygonGuideLine = None
        except Exception as e:
            self.logger.error(f"Error in mouse Double Click Event: {e}")

    def lineDraw(self, start: QPoint, current: QPoint):
        line = shp.symbolLine(start, current)
        # self.addItem(line)
        undoCommand = us.addShapeUndo(self, line)
        self.undoStack.push(undoCommand)
        return line

    def rectDraw(self, start: QPoint, end: QPoint):
        """
        Draws a rectangle on the scene
        """
        rect = shp.symbolRectangle(start, end)
        # self.addItem(rect)
        undoCommand = us.addShapeUndo(self, rect)
        self.undoStack.push(undoCommand)
        return rect

    def circleDraw(self, start: QPoint, end: QPoint):
        """
        Draws a circle on the scene
        """
        circle = shp.symbolCircle(start, end)
        # self.addItem(circle)
        undoCommand = us.addShapeUndo(self, circle)
        self.undoStack.push(undoCommand)
        return circle

    def arcDraw(self, start: QPoint, end: QPoint):
        """
        Draws an arc inside the rectangle defined by start and end points.
        """
        arc = shp.symbolArc(start, end)
        # self.addItem(arc)
        undoCommand = us.addShapeUndo(self, arc)
        self.undoStack.push(undoCommand)
        return arc

    def pinDraw(self, current):
        pin = shp.symbolPin(current, self.pinName, self.pinDir, self.pinType)
        # self.addItem(pin)
        undoCommand = us.addShapeUndo(self, pin)
        self.undoStack.push(undoCommand)
        return pin

    def labelDraw(
            self,
            current,
            labelDefinition,
            labelType,
            labelHeight,
            labelAlignment,
            labelOrient,
            labelUse,
    ):
        label = lbl.symbolLabel(
            current,
            labelDefinition,
            labelType,
            labelHeight,
            labelAlignment,
            labelOrient,
            labelUse,
        )
        label.labelVisible = self.labelOpaque
        label.labelDefs()
        label.setOpacity(1)
        undoCommand = us.addShapeUndo(self, label)
        self.undoStack.push(undoCommand)
        return label

    def copyItems(self, items: List):
        """
        Copies the selected items in the scene, creates a duplicate of each item,
        and adds them to the scene with a slight shift in position.
        """
        for item in items:
            # Serialize the item to JSON
            selectedItemJson = json.dumps(item, cls=symenc.symbolEncoder)

            # Deserialize the JSON back to a dictionary
            itemCopyDict = json.loads(selectedItemJson)

            # Create a new shape based on the item dictionary and the snap tuple
            shape = lj.symbolItems(self).create(itemCopyDict)

            # Create an undo command for adding the shape
            undo_command = us.addShapeUndo(self, shape)

            # Push the undo command to the undo stack
            self.undoStack.push(undo_command)

            # Shift the position of the shape by one grid unit to the right and down
            shape.setPos(
                QPoint(
                    item.pos().x() + 4 * self.snapTuple[0],
                    item.pos().y() + 4 * self.snapTuple[1],
                )
            )

    def moveBySelectedItems(self):
        if self.selectedItems():
            dlg = pdlg.moveByDialogue(self.editorWindow)
            dlg.xEdit.setText("0")
            dlg.yEdit.setText("0")
            if dlg.exec() == QDialog.Accepted:
                for item in self.selectedItems():
                    item.moveBy(
                        self.snapToBase(float(dlg.xEdit.text()), self.snapTuple[0]),
                        self.snapToBase(float(dlg.yEdit.text()), self.snapTuple[1]),
                    )
            self.editorWindow.messageLine.setText(
                f"Moved items by {dlg.xEdit.text()} and {dlg.yEdit.text()}"
            )
            self.editModes.setMode("selectItem")

    def itemProperties(self):
        """
        When item properties is queried.
        """
        selectedItems = [
            item for item in self.selectedItems() if item.parentItem() is None
        ]
        for item in selectedItems:
            if isinstance(item, shp.symbolRectangle):
                self.updateSymbolRectangle(item)
            elif isinstance(item, shp.symbolCircle):
                self.updateSymbolCircle(item)
            elif isinstance(item, shp.symbolArc):
                self.updateSymbolArc(item)
            elif isinstance(item, shp.symbolLine):
                self.updateSymbolLine(item)
            elif isinstance(item, shp.symbolPin):
                self.updateSymbolPin(item)
            elif isinstance(item, lbl.symbolLabel):
                self.updateSymbolLabel(item)
            elif isinstance(item, shp.symbolPolygon):
                self.updateSymbolPolygon(item)

    def updateSymbolRectangle(self, item):
        self.queryDlg = pdlg.rectPropertyDialog(self.editorWindow)
        [left, top, width, height] = item.rect.getRect()
        sceneTopLeftPoint = item.mapToScene(QPoint(left, top))
        self.queryDlg.rectLeftLine.setText(str(sceneTopLeftPoint.x()))
        self.queryDlg.rectTopLine.setText(str(sceneTopLeftPoint.y()))
        self.queryDlg.rectWidthLine.setText(str(width))  # str(width))
        self.queryDlg.rectHeightLine.setText(str(height))  # str(height))
        if self.queryDlg.exec() == QDialog.Accepted:
            newRectItem = shp.symbolRectangle(QPoint(0, 0), QPoint(0, 0))
            newRectItem.left = self.snapToBase(
                float(self.queryDlg.rectLeftLine.text()), self.snapTuple[0]
            )
            newRectItem.top = self.snapToBase(
                float(self.queryDlg.rectTopLine.text()), self.snapTuple[1]
            )
            newRectItem.width = self.snapToBase(
                float(self.queryDlg.rectWidthLine.text()), self.snapTuple[0]
            )
            newRectItem.height = self.snapToBase(
                float(self.queryDlg.rectHeightLine.text()), self.snapTuple[1]
            )

            self.undoStack.push(us.addDeleteShapeUndo(self, newRectItem, item))

    def updateSymbolCircle(self, item):
        self.queryDlg = pdlg.circlePropertyDialog(self.editorWindow)
        centre = item.mapToScene(item.centre).toTuple()
        radius = item.radius
        self.queryDlg.centerXEdit.setText(str(centre[0]))
        self.queryDlg.centerYEdit.setText(str(centre[1]))
        self.queryDlg.radiusEdit.setText(str(radius))
        if self.queryDlg.exec() == QDialog.Accepted:
            newCircleItem = shp.symbolCircle(QPoint(0, 0), QPoint(0, 0))
            centerX = self.snapToBase(
                float(self.queryDlg.centerXEdit.text()), self.snapTuple[0]
            )
            centerY = self.snapToBase(
                float(self.queryDlg.centerYEdit.text()), self.snapTuple[1]
            )
            newCircleItem.centre = QPoint(centerX, centerY)
            radius = self.snapToBase(
                float(self.queryDlg.radiusEdit.text()), self.snapTuple[0]
            )
            newCircleItem.radius = radius
            self.undoStack.push(us.addDeleteShapeUndo(self, newCircleItem, item))

    def updateSymbolLine(self, item):
        self.queryDlg = pdlg.linePropertyDialog(self.editorWindow)
        sceneLineStartPoint = item.mapToScene(item.start).toPoint()
        sceneLineEndPoint = item.mapToScene(item.end).toPoint()
        self.queryDlg.startXLine.setText(str(sceneLineStartPoint.x()))
        self.queryDlg.startYLine.setText(str(sceneLineStartPoint.y()))
        self.queryDlg.endXLine.setText(str(sceneLineEndPoint.x()))
        self.queryDlg.endYLine.setText(str(sceneLineEndPoint.y()))
        if self.queryDlg.exec() == QDialog.Accepted:
            startX = self.snapToBase(
                float(self.queryDlg.startXLine.text()), self.snapTuple[0]
            )
            startY = self.snapToBase(
                float(self.queryDlg.startYLine.text()), self.snapTuple[1]
            )
            endX = self.snapToBase(
                float(self.queryDlg.endXLine.text()), self.snapTuple[0]
            )
            endY = self.snapToBase(
                float(self.queryDlg.endYLine.text()), self.snapTuple[1]
            )
            newLine = shp.symbolLine(QPoint(startX, startY), QPoint(endX, endY))
            self.undoStack.push(us.addDeleteShapeUndo(self, newLine, item))

    def updateSymbolArc(self, item):
        self.queryDlg = pdlg.arcPropertyDialog(self.editorWindow)
        sceneStartPoint = item.mapToScene(item.start)
        self.queryDlg.startXEdit.setText(str(sceneStartPoint.x()))
        self.queryDlg.startYEdit.setText(str(sceneStartPoint.y()))
        self.queryDlg.widthEdit.setText(str(item.width))
        self.queryDlg.heightEdit.setText(str(item.height))
        self.queryDlg.arcTypeCombo.addItems(shp.symbolArc.arcTypes)
        self.queryDlg.arcTypeCombo.setCurrentText(item.arcType)
        if self.queryDlg.exec() == QDialog.Accepted:
            newArc = shp.symbolArc(QPoint(0, 0), QPoint(0, 0))
            startX = int(float(self.queryDlg.startXEdit.text()))
            startY = int(float(self.queryDlg.startYEdit.text()))
            start = self.snapToGrid(QPoint(startX, startY), self.snapTuple)
            width = self.snapToBase(
                float(self.queryDlg.widthEdit.text()), self.snapTuple[0]
            )
            height = self.snapToBase(
                float(self.queryDlg.heightEdit.text()), self.snapTuple[1]
            )
            newArc.arcType = self.queryDlg.arcTypeCombo.currentText()
            newArc.start = start
            newArc.width = width
            self.undoStack.push(us.addDeleteShapeUndo(self, newArc, item))
            newArc.height = height

    def updateSymbolLabel(self, item):
        self.queryDlg = pdlg.labelPropertyDialog(self.editorWindow)
        self.queryDlg.labelDefinition.setText(str(item.labelDefinition))
        self.queryDlg.labelHeightEdit.setText(str(item.labelHeight))
        self.queryDlg.labelAlignCombo.setCurrentText(item.labelAlign)
        self.queryDlg.labelOrientCombo.setCurrentText(item.labelOrient)
        self.queryDlg.labelUseCombo.setCurrentText(item.labelUse)
        if item.labelVisible:
            self.queryDlg.labelVisiCombo.setCurrentText("Yes")
        else:
            self.queryDlg.labelVisiCombo.setCurrentText("No")
        if item.labelType == "Normal":
            self.queryDlg.normalType.setChecked(True)
        elif item.labelType == "NLPLabel":
            self.queryDlg.NLPType.setChecked(True)
        elif item.labelType == "PyLabel":
            self.queryDlg.pyLType.setChecked(True)
        sceneStartPoint = item.mapToScene(item.start)
        self.queryDlg.labelXLine.setText(str(sceneStartPoint.x()))
        self.queryDlg.labelYLine.setText(str(sceneStartPoint.y()))
        if self.queryDlg.exec() == QDialog.Accepted:
            startX = int(float(self.queryDlg.labelXLine.text()))
            startY = int(float(self.queryDlg.labelYLine.text()))
            start = self.snapToGrid(QPoint(startX, startY), self.snapTuple)
            labelDefinition = self.queryDlg.labelDefinition.text()
            labelHeight = int(float(self.queryDlg.labelHeightEdit.text()))
            labelAlign = self.queryDlg.labelAlignCombo.currentText()
            labelOrient = self.queryDlg.labelOrientCombo.currentText()
            labelUse = self.queryDlg.labelUseCombo.currentText()
            labelType = lbl.symbolLabel.labelTypes[0]
            if self.queryDlg.NLPType.isChecked():
                labelType = lbl.symbolLabel.labelTypes[1]
            elif self.queryDlg.pyLType.isChecked():
                labelType = lbl.symbolLabel.labelTypes[2]
            newLabel = lbl.symbolLabel(
                start,
                labelDefinition,
                labelType,
                labelHeight,
                labelAlign,
                labelOrient,
                labelUse,
            )
            newLabel.labelVisible = (
                    self.queryDlg.labelVisiCombo.currentText() == "Yes"
            )
            newLabel.labelDefs()
            newLabel.setOpacity(1)
            self.undoStack.push(us.addDeleteShapeUndo(self, newLabel, item))

    def updateSymbolPin(self, item):
        self.queryDlg = pdlg.pinPropertyDialog(self.editorWindow)
        self.queryDlg.pinName.setText(str(item.pinName))
        self.queryDlg.pinType.setCurrentText(item.pinType)
        self.queryDlg.pinDir.setCurrentText(item.pinDir)
        sceneStartPoint = item.mapToScene(item.start).toPoint()
        self.queryDlg.pinXLine.setText(str(sceneStartPoint.x()))
        self.queryDlg.pinYLine.setText(str(sceneStartPoint.y()))
        if self.queryDlg.exec() == QDialog.Accepted:
            sceneStartX = int(float(self.queryDlg.pinXLine.text()))
            sceneStartY = int(float(self.queryDlg.pinYLine.text()))
            start = self.snapToGrid(
                QPoint(sceneStartX, sceneStartY), self.snapTuple
            )
            pinName = self.queryDlg.pinName.text()
            pinType = self.queryDlg.pinType.currentText()
            pinDir = self.queryDlg.pinDir.currentText()
            newPin = shp.symbolPin(start, pinName, pinDir, pinType)
            self.undoStack.push(us.addDeleteShapeUndo(self, newPin, item))

    def updateSymbolPolygon(self, item):
        pointsTupleList = [(point.x(), point.y()) for point in item.points]
        self.queryDlg = pdlg.symbolPolygonProperties(
            self.editorWindow, pointsTupleList
        )
        if self.queryDlg.exec() == QDialog.Accepted:
            tempPoints = []
            for i in range(self.queryDlg.tableWidget.rowCount()):
                xcoor = self.queryDlg.tableWidget.item(i, 1).text()
                ycoor = self.queryDlg.tableWidget.item(i, 2).text()
                if xcoor != "" and ycoor != "":
                    tempPoints.append(QPointF(float(xcoor), float(ycoor)))
            newPolygon = shp.symbolPolygon(tempPoints)
            self.undoStack.push(us.addDeleteShapeUndo(self, newPolygon, item))

    def loadSymbol(self, itemsList: List):
        if len(itemsList) > 2:
            snapGrid = itemsList[1].get("snapGrid", 10)
            self.majorGrid = snapGrid[0]  # dot/line grid spacing
            self.snapGrid = snapGrid[1]  # snapping grid size
            self.snapTuple = (self.snapGrid, self.snapGrid)
            self.snapDistance = 2 * self.snapGrid
            self.parent.view.snapTuple = self.snapTuple
            self.editorWindow.snapTuple = self.snapTuple
            self.attributeList = []
            for item in itemsList[2:]:
                if item is not None:
                    if item["type"] in self.symbolShapes:
                        itemShape = lj.symbolItems(self).create(item)
                        # items should be always visible in symbol view
                        if isinstance(itemShape, lbl.symbolLabel):
                            itemShape.setOpacity(1)
                        self.addItem(itemShape)
                    elif item["type"] == "attr":
                        attr = lj.symbolItems(self).createSymbolAttribute(item)
                        self.attributeList.append(attr)

    def saveSymbolCell(self, fileName: pathlib.Path):
        # items = self.items(self.sceneRect())  # get items in scene rect
        items = [item for item in self.items() if item.parentItem() is None]
        [
            labelItem.labelDefs()
            for labelItem in items
            if isinstance(labelItem, lbl.symbolLabel)
        ]
        items.insert(0, {"cellView": "symbol"})
        items.insert(1, {"snapGrid": self.snapTuple})
        if hasattr(self, "attributeList"):
            items.extend(self.attributeList)  # add attribute list to list

        with fileName.open(mode="w") as f:
            try:
                json.dump(items, f, cls=symenc.symbolEncoder, indent=4)
            except Exception as e:
                self.logger.error(f"Symbol save error: {e}")
        self.undoStack.clear()

    def reloadScene(self):
        items = [item for item in self.items() if item.parentItem() is None]
        if hasattr(self, "attributeList"):
            items.extend(self.attributeList)
        itemsList = json.loads(json.dumps(items, cls=symenc.symbolEncoder))
        self.clear()
        for item in itemsList:
            if item is not None:
                if item["type"] in self.symbolShapes:
                    itemShape = lj.symbolItems(self).create(item)
                    # items should be always visible in symbol view
                    if isinstance(itemShape, lbl.symbolLabel):
                        itemShape.setOpacity(1)
                    self.addItem(itemShape)
                elif item["type"] == "attr":
                    attr = lj.symbolItems(self).createSymbolAttribute(item)
                    self.attributeList.append(attr)

    def viewSymbolProperties(self):
        """
        View symbol properties dialog.
        """
        # copy symbol attribute list to another list by deepcopy to be safe
        attributeListCopy = deepcopy(self.attributeList)
        symbolPropDialogue = pdlg.symbolLabelsDialogue(
            self.editorWindow, self.items(), attributeListCopy
        )
        if symbolPropDialogue.exec() == QDialog.Accepted:
            for i, item in enumerate(symbolPropDialogue.labelItemList):
                # label name is not changed.
                item.labelHeight = int(
                    float(symbolPropDialogue.labelHeightList[i].text())
                )
                item.labelAlign = symbolPropDialogue.labelAlignmentList[i].currentText()
                item.labelOrient = symbolPropDialogue.labelOrientationList[
                    i
                ].currentText()
                item.labelUse = symbolPropDialogue.labelUseList[i].currentText()
                item.labelType = symbolPropDialogue.labelTypeList[i].currentText()
                item.update(item.boundingRect())
            # create an empty attribute list. If the dialog is OK, the local attribute list
            # will be copied to the symbol attribute list.
            localAttributeList = []
            for i, item in enumerate(symbolPropDialogue.attributeNameList):
                if item.text().strip() != "":
                    localAttributeList.append(
                        symenc.symbolAttribute(
                            item.text(), symbolPropDialogue.attributeDefList[i].text()
                        )
                    )
                self.attributeList = deepcopy(localAttributeList)
