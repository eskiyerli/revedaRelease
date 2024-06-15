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
import inspect
import itertools as itt
import json
import time

# from hashlib import new
import pathlib
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from typing import Union, Any


# import numpy as np
from PySide6.QtCore import (
    QEvent,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    Qt,
    QLineF,
)
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QTextDocument,
    QTransform,
    QPen,
    QFontDatabase,
    QFont,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QMenu,
    QGraphicsLineItem,
    QGraphicsItem,
)

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.undoStack as us
import revedaEditor.common.labels as lbl
import revedaEditor.common.layoutShapes as layp
import revedaEditor.common.layoutShapes as lshp  # import layout shapes
import revedaEditor.common.net as net
import revedaEditor.common.shapes as shp  # import the shapes
import revedaEditor.fileio.layoutEncoder as layenc
import revedaEditor.fileio.loadJSON as lj
import revedaEditor.fileio.schematicEncoder as schenc
import revedaEditor.fileio.symbolEncoder as symenc
import revedaEditor.gui.editFunctions as edf
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.layoutDialogues as ldlg
import revedaEditor.gui.propertyDialogues as pdlg

import os
from dotenv import load_dotenv
load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):
    import pdk.layoutLayers as laylyr
    import pdk.process as fabproc
    import pdk.schLayers as schlyr
    import pdk.pcells as pcells
else:
    import defaultPDK.layoutLayers as laylyr
    import defaultPDK.process as fabproc
    import defaultPDK.schLayers as schlyr
    import defaultPDK.pcells as pcells



class editorScene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.editorWindow = self.parent.parent
        self.majorGrid = self.editorWindow.majorGrid
        self.snapTuple = self.editorWindow.snapTuple
        self.mousePressLoc = None
        self.mouseMoveLoc = None
        self.mouseReleaseLoc = None
        # common edit modes
        self.editModes = ddef.editModes(
            selectItem=True,
            deleteItem=False,
            moveItem=False,
            copyItem=False,
            rotateItem=False,
            changeOrigin=False,
            panView=False,
            stretchItem=False,
        )
        self.readOnly = False  # if the scene is not editable
        self.undoStack = us.undoStack()

        self.origin = QPoint(0, 0)
        self.snapDistance = self.editorWindow.snapDistance
        self.cellName = self.editorWindow.file.parent.stem
        self.partialSelection = True
        self.selectionRectItem = None
        self._items = []
        self._itemsOffset = []
        self.libraryDict = self.editorWindow.libraryDict
        self.editModes.rotateItem = False
        self.itemContextMenu = QMenu()
        self.appMainW = self.editorWindow.appMainW
        self.logger = self.appMainW.logger
        self.messageLine = self.editorWindow.messageLine
        self.statusLine = self.editorWindow.statusLine
        self.installEventFilter(self)
        self.setMinimumRenderSize(2)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._itemsOffset = []
            self.mousePressLoc = event.scenePos().toPoint()
            self._items = [item for item in self.items(self.mousePressLoc) if
                           item.parentItem() is None]
            for item in self._items:
                self._itemsOffset.append(item.pos().toPoint() - self.mousePressLoc)

            if self.editModes.panView:
                self.centerViewOnPoint(self.mousePressLoc)
                self.messageLine.setText('Pan View at mouse press position')

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            self.mouseReleaseLoc = event.scenePos().toPoint()
            if self._items:
                if self.mouseReleaseLoc != self.mousePressLoc:
                    self.moveShapesUndoStack(self._items, self._itemsOffset, self.mousePressLoc,
                                            self.mouseReleaseLoc)

    def snapToBase(self, number, base):
        """
        Restrict a number to the multiples of base
        """
        return int(round(number / base)) * base

    def snapToGrid(self, point: QPoint, snapTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(
            self.snapToBase(point.x(), snapTuple[0]),
            self.snapToBase(point.y(), snapTuple[1]),
        )

    def rotateSelectedItems(self, point: QPoint):
        """
        Rotate selected items by 90 degree.
        """
        for item in self.selectedItems():
            self.rotateAnItem(point, item, 90)
        self.editModes.setMode("selectItem")

    def rotateAnItem(self, point: QPoint, item: QGraphicsItem, angle: int):
        rotationOriginPoint = item.mapFromScene(point)
        item.setTransformOriginPoint(rotationOriginPoint)
        item.angle += angle
        item.setRotation(item.angle)
        undoCommand = us.undoRotateShape(self, item, item.angle)
        self.undoStack.push(undoCommand)

    def eventFilter(self, source, event):
        """
        Mouse events should snap to background grid points.
        """
        if self.readOnly:  # if read only do not propagate any mouse events
            return True
        elif event.type() in [
            QEvent.GraphicsSceneMouseMove,
            QEvent.GraphicsSceneMousePress,
            QEvent.GraphicsSceneMouseRelease,
        ]:
            event.setScenePos(
                self.snapToGrid(event.scenePos(), self.snapTuple).toPointF()
            )
            return False
        else:
            return super().eventFilter(source, event)

    def copySelectedItems(self):
        pass

    # def selectSceneItems(self, modifiers):
    #     """
    #     Selects scene items based on the given modifiers.
    #     A selection rectangle is drawn if ShiftModifier is pressed,
    #     else a single item is selected. The function does not return anything.

    #     :param modifiers: The keyboard modifiers that determine the selection type.
    #     :type modifiers: Qt.KeyboardModifiers
    #     """
    #     if modifiers == Qt.ShiftModifier:
    #         self.editorWindow.messageLine.setText("Draw Selection Rectangle")
    #         self.selectionRectItem = QGraphicsRectItem(
    #             QRectF(self.mousePressLoc, self.mousePressLoc)
    #         )
    #         self.selectionRectItem.setPen(schlyr.draftPen)

    #         self.undoStack.push(us.addShapeUndo(self, self.selectionRectItem))
    #         # self.addItem(self.selectionRectItem)
    #     self.editorWindow.messageLine.setText(
    #         "Item selected" if self.selectedItems() else "Nothing selected"
    #     )

    def selectSceneItems(self, modifiers):
        """
        Selects scene items based on the given modifiers.
        A selection rectangle is drawn if ShiftModifier is pressed,
        else a single item is selected. The function does not return anything.

        :param modifiers: The keyboard modifiers that determine the selection type.
        :type modifiers: Qt.KeyboardModifiers
        """
        if modifiers == Qt.ShiftModifier:
            self.editorWindow.messageLine.setText("Draw Selection Rectangle")
            self.selectionRectItem = QGraphicsRectItem(
                QRectF(self.mousePressLoc, self.mousePressLoc)
            )
            self.selectionRectItem.setPen(schlyr.draftPen)
            self.undoStack.push(us.addShapeUndo(self, self.selectionRectItem))
            # self.addItem(self.selectionRectItem)
        else:
            self.editorWindow.messageLine.setText("Select an item")
            itemsAtMousePress = self.items(self.mousePressLoc)
            if itemsAtMousePress:
                [item.setSelected(True) for item in itemsAtMousePress]

        self.editorWindow.messageLine.setText(
            "Item selected" if self.selectedItems() else "Nothing selected"
        )

    def selectInRectItems(self, selectionRect: QRect, partialSelection=False):
        """
        Select items in the scene.
        """

        mode = Qt.IntersectsItemShape if partialSelection else Qt.ContainsItemShape
        [item.setSelected(True) for item in self.items(selectionRect, mode=mode)]

    def selectAll(self):
        """
        Select all items in the scene.
        """
        [item.setSelected(True) for item in self.items()]

    def deselectAll(self):
        """
        Deselect all items in the scene.
        """
        [item.setSelected(False) for item in self.selectedItems()]

    def deleteSelectedItems(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                # self.removeItem(item)
                undoCommand = us.deleteShapeUndo(self, item)
                self.undoStack.push(undoCommand)
            self.update()  # update the scene

    def stretchSelectedItems(self):
        if self.selectedItems() is not None:
            try:
                for item in self.selectedItems():
                    if hasattr(item, "stretch"):
                        item.stretch = True
            except AttributeError:
                self.messageLine.setText("Nothing selected")

    def fitItemsInView(self) -> None:
        self.setSceneRect(self.itemsBoundingRect().adjusted(-40, -40, 40, 40))
        self.views()[0].fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        self.views()[0].viewport().update()

    def moveSceneLeft(self) -> None:
        currentSceneRect = self.sceneRect()
        halfWidth = currentSceneRect.width() / 2.0
        newSceneRect = QRectF(
            currentSceneRect.left() - halfWidth,
            currentSceneRect.top(),
            currentSceneRect.width(),
            currentSceneRect.height(),
        )
        self.setSceneRect(newSceneRect)

    def moveSceneRight(self) -> None:
        currentSceneRect = self.sceneRect()
        halfWidth = currentSceneRect.width() / 2.0
        newSceneRect = QRectF(
            currentSceneRect.left() + halfWidth,
            currentSceneRect.top(),
            currentSceneRect.width(),
            currentSceneRect.height(),
        )
        self.setSceneRect(newSceneRect)

    def moveSceneUp(self) -> None:
        currentSceneRect = self.sceneRect()
        halfWidth = currentSceneRect.width() / 2.0
        newSceneRect = QRectF(
            currentSceneRect.left(),
            currentSceneRect.top() - halfWidth,
            currentSceneRect.width(),
            currentSceneRect.height(),
        )
        self.setSceneRect(newSceneRect)

    def moveSceneDown(self) -> None:
        currentSceneRect = self.sceneRect()
        halfWidth = currentSceneRect.width() / 2.0
        newSceneRect = QRectF(
            currentSceneRect.left(),
            currentSceneRect.top() + halfWidth,
            currentSceneRect.width(),
            currentSceneRect.height(),
        )
        self.setSceneRect(newSceneRect)

    def centerViewOnPoint(self, point: QPoint) -> None:
        view = self.views()[0]
        view_widget = view.viewport()
        width = view_widget.width()
        height = view_widget.height()
        self.setSceneRect(point.x() - width / 2, point.y() - height / 2, width, height)

    def addUndoStack(self, item: QGraphicsItem):
        undoCommand = us.addShapeUndo(self, item)
        self.undoStack.push(undoCommand)

    def deleteUndoStack(self, item: QGraphicsItem):
        undoCommand = us.deleteShapeUndo(self, item)
        self.undoStack.push(undoCommand)

    def addListUndoStack(self, itemList: list):
        undoCommand = us.addShapesUndo(self, itemList)
        self.undoStack.push(undoCommand)

    def moveShapesUndoStack(self, items: list[QGraphicsItem], itemsOffsetList: list[int],
                            start: QPoint, end: QPoint):
        undoCommand = us.undoMoveShapesCommand(items, itemsOffsetList, start, end)
        self.undoStack.push(undoCommand)

    def addUndoMacroStack(self, undoCommands: list, macroName: str = "Macro"):
        self.undoStack.beginMacro(macroName)
        for command in undoCommands:
            self.undoStack.push(command)
        self.undoStack.endMacro()


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
            modifiers = QGuiApplication.keyboardModifiers()
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
                if self.editModes.selectItem:
                    self.selectSceneItems(modifiers)
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
                self.selectionRectItem.setRect(
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
                elif self.editModes.selectItem and modifiers == Qt.ShiftModifier:
                    self.selectInRectItems(
                        self.selectionRectItem.rect(), self.partialSelection
                    )
                    self.removeItem(self.selectionRectItem)
                    self.selectionRectItem = None
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

    def copySelectedItems(self):
        """
        Copies the selected items in the scene, creates a duplicate of each item,
        and adds them to the scene with a slight shift in position.
        """
        for item in self.selectedItems():
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
        if not self.selectedItems():
            return
        for item in self.selectedItems():
            if isinstance(item, shp.symbolRectangle):
                self.queryDlg = pdlg.rectPropertyDialog(self.editorWindow)
                [left, top, width, height] = item.rect.getRect()
                sceneTopLeftPoint = item.mapToScene(QPoint(left, top))
                self.queryDlg.rectLeftLine.setText(str(sceneTopLeftPoint.x()))
                self.queryDlg.rectTopLine.setText(str(sceneTopLeftPoint.y()))
                self.queryDlg.rectWidthLine.setText(str(width))  # str(width))
                self.queryDlg.rectHeightLine.setText(str(height))  # str(height))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateRectangleShape(item)
            elif isinstance(item, shp.symbolCircle):
                self.queryDlg = pdlg.circlePropertyDialog(self.editorWindow)
                centre = item.mapToScene(item.centre).toTuple()
                radius = item.radius
                self.queryDlg.centerXEdit.setText(str(centre[0]))
                self.queryDlg.centerYEdit.setText(str(centre[1]))
                self.queryDlg.radiusEdit.setText(str(radius))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateCircleShape(item)
            elif isinstance(item, shp.symbolArc):
                self.queryDlg = pdlg.arcPropertyDialog(self.editorWindow)
                sceneStartPoint = item.mapToScene(item.start)
                self.queryDlg.startXEdit.setText(str(sceneStartPoint.x()))
                self.queryDlg.startYEdit.setText(str(sceneStartPoint.y()))
                self.queryDlg.widthEdit.setText(str(item.width))
                self.queryDlg.heightEdit.setText(str(item.height))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateArcShape(item)
            elif isinstance(item, shp.symbolLine):
                self.queryDlg = pdlg.linePropertyDialog(self.editorWindow)
                sceneLineStartPoint = item.mapToScene(item.start).toPoint()
                sceneLineEndPoint = item.mapToScene(item.end).toPoint()
                self.queryDlg.startXLine.setText(str(sceneLineStartPoint.x()))
                self.queryDlg.startYLine.setText(str(sceneLineStartPoint.y()))
                self.queryDlg.endXLine.setText(str(sceneLineEndPoint.x()))
                self.queryDlg.endYLine.setText(str(sceneLineEndPoint.y()))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateLineShape(item)
            elif isinstance(item, shp.symbolPin):
                self.queryDlg = pdlg.pinPropertyDialog(self.editorWindow)
                self.queryDlg.pinName.setText(str(item.pinName))
                self.queryDlg.pinType.setCurrentText(item.pinType)
                self.queryDlg.pinDir.setCurrentText(item.pinDir)
                sceneStartPoint = item.mapToScene(item.start).toPoint()
                self.queryDlg.pinXLine.setText(str(sceneStartPoint.x()))
                self.queryDlg.pinYLine.setText(str(sceneStartPoint.y()))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updatePinShape(item)
            elif isinstance(item, lbl.symbolLabel):
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
                    self.updateLabelShape(item)
            elif isinstance(item, shp.symbolPolygon):
                pointsTupleList = [(point.x(), point.y()) for point in item.points]
                self.queryDlg = pdlg.symbolPolygonProperties(
                    self.editorWindow, pointsTupleList
                )
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updatePolygonShape(item)

    def updateRectangleShape(self, item: shp.symbolRectangle):
        """
        Both dictionaries have the topleft corner of rectangle in scene coordinates.
        """
        origItemList = item.rect.getRect()  # in item coordinates
        left = self.snapToBase(
            float(self.queryDlg.rectLeftLine.text()), self.snapTuple[0]
        )
        top = self.snapToBase(
            float(self.queryDlg.rectTopLine.text()), self.snapTuple[1]
        )
        width = self.snapToBase(
            float(self.queryDlg.rectWidthLine.text()), self.snapTuple[0]
        )
        height = self.snapToBase(
            float(self.queryDlg.rectHeightLine.text()), self.snapTuple[1]
        )
        topLeftPoint = item.mapFromScene(QPoint(left, top))
        newItemList = [topLeftPoint.x(), topLeftPoint.y(), width, height]
        undoCommand = us.updateSymRectUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updateCircleShape(self, item: shp.symbolCircle):
        origItemList = [item.centre.x(), item.centre.y(), item.radius]
        centerX = self.snapToBase(
            float(self.queryDlg.centerXEdit.text()), self.snapTuple[0]
        )
        centerY = self.snapToBase(
            float(self.queryDlg.centerYEdit.text()), self.snapTuple[1]
        )
        radius = self.snapToBase(
            float(self.queryDlg.radiusEdit.text()), self.snapTuple[0]
        )
        centrePoint = item.mapFromScene(
            self.snapToGrid(QPoint(centerX, centerY), self.snapTuple)
        )
        newItemList = [centrePoint.x(), centrePoint.y(), radius]
        undoCommand = us.updateSymCircleUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updateArcShape(self, item: shp.symbolArc):
        origItemList = [item.start.x(), item.start.y(), item.width, item.height]
        startX = self.snapToBase(
            float(self.queryDlg.startXEdit.text()), self.snapTuple[0]
        )
        startY = self.snapToBase(
            float(self.queryDlg.startYEdit.text()), self.snapTuple[1]
        )
        start = item.mapFromScene(QPoint(startX, startY)).toPoint()
        width = self.snapToBase(
            float(self.queryDlg.widthEdit.text()), self.snapTuple[0]
        )
        height = self.snapToBase(
            float(self.queryDlg.heightEdit.text()), self.snapTuple[1]
        )
        newItemList = [start.x(), start.y(), width, height]
        undoCommand = us.updateSymArcUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updateLineShape(self, item: shp.symbolLine):
        """
        Updates line shape from dialogue entries.
        """
        origItemList = [item.start.x(), item.start.y(), item.end.x(), item.end.y()]
        startX = self.snapToBase(
            float(self.queryDlg.startXLine.text()), self.snapTuple[0]
        )
        startY = self.snapToBase(
            float(self.queryDlg.startYLine.text()), self.snapTuple[1]
        )
        endX = self.snapToBase(float(self.queryDlg.endXLine.text()), self.snapTuple[0])
        endY = self.snapToBase(float(self.queryDlg.endYLine.text()), self.snapTuple[1])
        start = item.mapFromScene(QPoint(startX, startY)).toPoint()
        end = item.mapFromScene(QPoint(endX, endY)).toPoint()
        newItemList = [start.x(), start.y(), end.x(), end.y()]
        undoCommand = us.updateSymLineUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updatePinShape(self, item: shp.symbolPin):
        origItemList = [
            item.start.x(),
            item.start.y(),
            item.pinName,
            item.pinDir,
            item.pinType,
        ]
        sceneStartX = self.snapToBase(
            float(self.queryDlg.pinXLine.text()), self.snapTuple[0]
        )
        sceneStartY = self.snapToBase(
            float(self.queryDlg.pinYLine.text()), self.snapTuple[1]
        )

        start = item.mapFromScene(QPoint(sceneStartX, sceneStartY)).toPoint()
        pinName = self.queryDlg.pinName.text()
        pinType = self.queryDlg.pinType.currentText()
        pinDir = self.queryDlg.pinDir.currentText()
        newItemList = [start.x(), start.y(), pinName, pinDir, pinType]
        undoCommand = us.updateSymPinUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updatePolygonShape(self, item):
        tempPoints = []
        for i in range(self.queryDlg.tableWidget.rowCount()):
            xcoor = self.queryDlg.tableWidget.item(i, 1).text()
            ycoor = self.queryDlg.tableWidget.item(i, 2).text()
            if xcoor != "" and ycoor != "":
                tempPoints.append(QPointF(float(xcoor), float(ycoor)))
        item.points = tempPoints

    def updateLabelShape(self, item: lbl.symbolLabel):
        """
        update label with new values.
        """
        origItemList = [
            item.start.x(),
            item.start.y(),
            item.labelDefinition,
            item.labelType,
            item.labelHeight,
            item.labelAlign,
            item.labelOrient,
            item.labelUse,
            item.labelVisible,
        ]
        sceneStartX = self.snapToBase(
            float(self.queryDlg.labelXLine.text()), self.snapTuple[0]
        )
        sceneStartY = self.snapToBase(
            float(self.queryDlg.labelYLine.text()), self.snapTuple[1]
        )
        start = item.mapFromScene(QPoint(sceneStartX, sceneStartY))
        labelDefinition = self.queryDlg.labelDefinition.text()
        labelHeight = self.queryDlg.labelHeightEdit.text()
        labelAlign = self.queryDlg.labelAlignCombo.currentText()
        labelOrient = self.queryDlg.labelOrientCombo.currentText()
        labelUse = self.queryDlg.labelUseCombo.currentText()
        labelVisible = self.queryDlg.labelVisiCombo.currentText() == "Yes"
        labelType = lbl.symbolLabel.labelTypes[0]
        if self.queryDlg.NLPType.isChecked():
            labelType = lbl.symbolLabel.labelTypes[1]
        elif self.queryDlg.pyLType.isChecked():
            labelType = lbl.symbolLabel.labelTypes[2]

        # set opacity to 1 so that the label is still visible on symbol editor

        newItemList = [
            start.x(),
            start.y(),
            labelDefinition,
            labelType,
            labelHeight,
            labelAlign,
            labelOrient,
            labelUse,
            labelVisible,
        ]
        undoCommand = us.updateSymLabelUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)
        item.setOpacity(1)

    def loadSymbol(self, itemsList: list):
        snapGrid = itemsList[1].get("snapGrid")
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
        items = self.items()
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

    def reloadScene(self):
        items = self.items()
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


class schematicScene(editorScene):
    newText: None

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.instCounter = 0
        self.start = QPoint(0, 0)
        self.current = QPoint(0, 0)
        self.editModes = ddef.schematicModes(
            selectItem=True,
            deleteItem=False,
            moveItem=False,
            copyItem=False,
            rotateItem=False,
            changeOrigin=False,
            panView=False,
            drawPin=False,
            drawWire=False,
            drawText=False,
            addInstance=False,
            stretchItem=False,
        )
        self.selectModes = ddef.schematicSelectModes(
            selectAll=True,
            selectDevice=False,
            selectNet=False,
            selectPin=False,
        )
        self.instanceCounter = 0
        self.netCounter = 0
        self.selectedNet = None
        self.selectedPin = None
        self.selectedSymbol = None
        self.schematicNets = {}  # netName: list of nets with the same name
        self.viewRect = None
        self.instanceSymbolTuple = None
        # pin attribute defaults
        self.pinName = ""
        self.pinType = "Signal"
        self.pinDir = "Input"
        self.parentView = None
        # self.wires = None
        self._newNet = None
        self._stretchNet = None
        self._totalNet = None
        self.newInstance = None
        self.newPin = None
        self.newText = None
        self._snapPointRect = None
        self.highlightNets = False
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamily = [
            family for family in fontFamilies if QFontDatabase.isFixedPitch(family)
        ][0]
        fontStyle = QFontDatabase.styles(fixedFamily)[1]
        self.fixedFont = QFont(fixedFamily)
        self.fixedFont.setStyleName(fontStyle)
        fontSize = [size for size in QFontDatabase.pointSizes(fixedFamily, fontStyle)][
            3
        ]
        self.fixedFont.setPointSize(fontSize)
        self.fixedFont.setKerning(False)
        self._changedRects: list[QRectF] = []
        # self.changed.connect(self.sceneChanged)

    #
    # def sceneChanged(self, rects: list):
    #
    #     self._changedRects = rects
    #     for rectArea in self._changedRects:
    #         netsInArea = [netItem for netItem in self.items(rectArea) if isinstance(netItem,
    #                                                                     net.schematicNet)]
    #
    #         if netsInArea:
    #             netEndPoints = []
    #             for netItem in netsInArea:
    #                 netEndPoints.extend(netItem.sceneEndPoints)
    #
    #             dotsInArea = {dotItem for dotItem in self.items(rectArea) if isinstance(
    #                 dotItem, net.crossingDot)}
    #             for dotItem in dotsInArea:
    #                 self.removeItem(dotItem)
    #
    #             pointCountsDict = Counter(netEndPoints)
    #             dotPoints = [point for point, count in pointCountsDict.items() if count >= 3]
    #             for dotPoint in dotPoints:
    #                 self.addItem(net.crossingDot(dotPoint))

    @property
    def drawMode(self):
        return any(
            (self.editModes.drawPin, self.editModes.drawWire, self.editModes.drawText)
        )

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(mouse_event)
        try:
            modifiers = QGuiApplication.keyboardModifiers()
            self.viewRect = self.parent.view.mapToScene(
                self.parent.view.viewport().rect()
            ).boundingRect()

            if mouse_event.button() == Qt.LeftButton:
                self.mousePressLoc = mouse_event.scenePos().toPoint()

                if self.editModes.addInstance:
                    self.newInstance = self.drawInstance(self.mousePressLoc)
                    self.newInstance.setSelected(True)
                elif self.editModes.drawWire:
                    self.editorWindow.messageLine.setText("Wire Mode")
                    if self._newNet:
                        self.checkNewNet(self._newNet)
                        self._newNet = None
                    self.mousePressLoc = self.findSnapPoint(
                        self.mousePressLoc, self.snapDistance, set()
                    )
                    self._newNet = net.schematicNet(
                        self.mousePressLoc, self.mousePressLoc
                    )
                elif self.editModes.changeOrigin:  # change origin of the schematic
                    self.origin = self.mousePressLoc
                    self.editModes.changeOrigin = False

                elif self.editModes.drawPin:
                    self.editorWindow.messageLine.setText("Add a pin")
                    self.newPin = self.addPin(self.mousePressLoc)
                    self.newPin.setSelected(True)

                elif self.editModes.drawText:
                    self.editorWindow.messageLine.setText("Add a text note")
                    self.newText = self.addNote(self.mousePressLoc)
                    # TODO: What is wrong here?
                    self.rotateAnItem(
                        self.mousePressLoc,
                        self.newText,
                        int(float(self.noteOrient[1:])),
                    )
                    self.newText.setSelected(True)
                elif self.editModes.rotateItem:
                    self.editorWindow.messageLine.setText("Rotate item")
                    if self.selectedItems():
                        self.rotateSelectedItems(self.mousePressLoc)
                elif self.editModes.selectItem:
                    self.selectSceneItems(modifiers)

        except Exception as e:
            self.logger.error(f"mouse press error: {e}")

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(mouse_event)
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        try:
            if mouse_event.buttons() == Qt.LeftButton:
                if self.editModes.addInstance:
                    # TODO: think how to do it with mapFromScene
                    self.newInstance.setPos(self.mouseMoveLoc - self.mousePressLoc)

                elif self.editModes.drawPin and self.newPin.isSelected():
                    self.newPin.setPos(self.mouseMoveLoc - self.mousePressLoc)

                elif self.editModes.drawText and self.newText.isSelected():
                    self.newText.setPos(self.mouseMoveLoc - self.mousePressLoc)
                elif self.editModes.selectItem and modifiers == Qt.ShiftModifier:
                    self.selectionRectItem.setRect(
                        QRectF(self.mousePressLoc, self.mouseMoveLoc)
                    )
            else:
                if self.editModes.drawWire and self._newNet is not None:
                    self.mouseMoveLoc = self.findSnapPoint(
                        self.mouseMoveLoc, self.snapDistance, {self._newNet}
                    )
                    if self._snapPointRect is None:
                        rect = QRectF(QPointF(-5, -5), QPointF(5, 5))
                        self._snapPointRect = QGraphicsRectItem(rect)
                        self._snapPointRect.setPen(schlyr.draftPen)
                        self.addItem(self._snapPointRect)
                    self._snapPointRect.setPos(self.mouseMoveLoc)
                    self._newNet.draftLine = QLineF(
                        self.mousePressLoc, self.mouseMoveLoc
                    )
                    if self._newNet.scene() is None:
                        self.addUndoStack(self._newNet)
                elif self.editModes.stretchItem and self._stretchNet is not None:
                    self._stretchNet.draftLine = QLineF(
                        self._stretchNet.draftLine.p1(), self.mouseMoveLoc
                    )
            self.editorWindow.statusLine.showMessage(
                f"Cursor Position: {str((self.mouseMoveLoc - self.origin).toTuple())}"
            )
        except Exception as e:
            self.logger.error(f"mouse move error: {e}")

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        try:
            self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
            modifiers = QGuiApplication.keyboardModifiers()
            if mouse_event.button() == Qt.LeftButton:
                if self.editModes.addInstance:
                    self.editModes.addInstance = False
                elif self.editModes.drawPin:
                    self.editModes.drawPin = False
                    self.newPin = None
                elif self.editModes.selectItem:
                    if modifiers == Qt.ShiftModifier:
                        self.selectInRectItems(
                            self.selectionRectItem.rect(), self.partialSelection
                        )
                        self.removeItem(self.selectionRectItem)
                        self.selectionRectItem = None
                # elif self.editModes.stretchItem and self._stretchNet:
                #     self._stretchNet = None
        except Exception as e:
            self.logger.error(f"mouse release error: {e}")
        super().mouseReleaseEvent(mouse_event)

    def checkNewNet(self, newNet: net.schematicNet):
        """
        check if the new net is valid. If it has zero length, remove it. Otherwise process it.

        """
        if newNet.draftLine.isNull():
            self.removeItem(newNet)
            self.undoStack.removeLastCommand()
        else:
            self.mergeSplitNets(newNet)

    def mergeSplitNets(self, inputNet: net.schematicNet):
        self.mergeNets(inputNet)  # output is self._totalNet
        overlapNets = self._totalNet.findOverlapNets()
        splitPoints = set()
        # inputNet splits overlapping nets
        for netItem in overlapNets:
            for end in netItem.endPoints:
                endPoint = self._totalNet.mapFromItem(netItem, end).toPoint() # map to totalNet (mergedNet) coordinates
                if self._totalNet.contains(endPoint) and endPoint not in self._totalNet.endPoints:
                    splitPoints.add(endPoint)
        if splitPoints:
            splitPointsList = list(splitPoints)
            splitPointsList.insert(0,self._totalNet.endPoints[0])
            splitPointsList.append(self._totalNet.endPoints[1])
            orderedPointsObj = map(self._totalNet.mapToScene,list(Counter(self.orderPoints(splitPointsList)).keys()))
            orderedPoints = [opoint.toPoint() for opoint in orderedPointsObj]
            # print(f'ordered points: {orderedPoints}')
            splitNetList = []
            for i in range(len(orderedPoints) - 1):
                splitNet = net.schematicNet(orderedPoints[i], orderedPoints[i + 1])
                splitNet.inherit(inputNet)
                splitNetList.append(splitNet)
                if inputNet.isSelected():
                    splitNet.setSelected(True)
            self.addListUndoStack(splitNetList)
            self.deleteUndoStack(self._totalNet)


    def mergeNets(self, inputNet: net.schematicNet) -> net.schematicNet:
        """
        Recursively merge nets until no changes are made.

        :param inputNet: The net to merge
        :return: The merged net
        """
        (origNet, mergedNet) = inputNet.mergeNets()
        if origNet.isSelected():
            mergedNet.setSelected(True)
        
        if origNet.sceneShapeRect == mergedNet.sceneShapeRect:
            # No changes, exit recursion
            self._totalNet = origNet
            return origNet
        
        # Remove original net and add merged net
        self.removeItem(origNet)
        self.addItem(mergedNet)
    
        # Recursively merge the new net
        return self.mergeNets(mergedNet)

    def removeSnapRect(self):
        if self._snapPointRect:
            self.removeItem(self._snapPointRect)
            self._snapPointRect = None

    def findSnapPoint(
        self, eventLoc: QPoint, snapDistance: int, ignoredSet: set[net.schematicNet]
    ) -> QPoint:
        snapRect = QRect(
            eventLoc.x() - snapDistance,
            eventLoc.y() - snapDistance,
            2 * snapDistance,
            2 * snapDistance,
        )
        snapPoints = self.findConnectPoints(snapRect, ignoredSet)
        if snapPoints:
            lengths = [
                (snapPoint - eventLoc).manhattanLength() for snapPoint in snapPoints
            ]
            closestPoint = list(snapPoints)[lengths.index(min(lengths))]
        else:
            closestPoint = eventLoc

        return closestPoint

    def findConnectPoints(
        self, sceneRect: QRect, ignoredSet: set[QGraphicsItem]
    ) -> set[QPoint]:
        snapPoints = set()
        rectItems = set(self.items(sceneRect)) - ignoredSet
        for item in rectItems:
            if isinstance(item, net.schematicNet) and any(
                list(map(sceneRect.contains, item.sceneEndPoints))
            ):
                snapPoints.add(
                    item.sceneEndPoints[
                        list(map(sceneRect.contains, item.sceneEndPoints)).index(True)
                    ]
                )
            elif isinstance(item, shp.symbolPin):
                snapPoints.add(item.mapToScene(item.start).toPoint())
            elif isinstance(item, shp.schematicPin):
                snapPoints.add(item.mapToScene(item.start).toPoint())
        return snapPoints

    def findNetStretchPoints(
        self, netItem: net.schematicNet, snapDistance: int
    ) -> dict[int, QPoint]:
        netEndPointsDict: dict[int, QPoint] = {}
        sceneEndPoints = netItem.sceneEndPoints
        for netEnd in sceneEndPoints:
            snapRect: QRect = QRect(
                netEnd.x() - snapDistance,
                netEnd.y() - snapDistance,
                2 * snapDistance,
                2 * snapDistance,
            )
            snapRectItems = set(self.items(snapRect)) - {netItem}

            for item in snapRectItems:
                if isinstance(item, net.schematicNet) and any(
                    list(map(snapRect.contains, item.sceneEndPoints))
                ):
                    netEndPointsDict[sceneEndPoints.index(netEnd)] = netEnd
                elif (
                    isinstance(item, shp.symbolPin)
                    or isinstance(item, shp.schematicPin)
                ) and snapRect.contains(item.mapToScene(item.start).toPoint()):
                    netEndPointsDict[sceneEndPoints.index(netEnd)] = item.mapToScene(
                        item.start
                    ).toPoint()
                if netEndPointsDict.get(
                    sceneEndPoints.index(netEnd)
                ):  # after finding one point, no need to iterate.
                    break
        return netEndPointsDict

    def findSplitPoints(self, targetNet: net.schematicNet) -> list[QPoint]:
        """
        This function finds the split points of a net.

        Parameters:
            targetNet (net.schematicNet): The net to find the split points of.

        Returns:
            list[QPoint]: A list of split points.

        This function searches for nets that are orthogonally aligned with the target net and
        for pins that are located within the target net's bounding rectangle. It returns a list
        of split points that are found.
        """
        splitPoints: set[QPoint | Any] = set()

        # Find split points for nets that are orthogonally aligned with the target net.
        # sceneRect = targetNet.sceneShapeRect
        collidingItems = set(self.collidingItems())

        for item in collidingItems:
            if (
                isinstance(item, net.schematicNet)
                and any(list(map(self.collidesWithItem, item.endPoints)))
                # and targetNet.isOrthogonal(item)
            ):
                print(item.sceneEndPoints)
        #         splitPoints.add(
        #             item.sceneEndPoints[
        #                 list(map(self.contains, item.sceneEndPoints)).index(True)
        #             ]
        #         )
        #     elif (
        #         isinstance(item, shp.symbolPin) or isinstance(item, shp.schematicPin)
        #     ) and self.contains(item.mapToScene(item.start).toPoint()):
        #         splitPoints.add(item.mapToScene(item.start).toPoint())

        # return list(splitPoints)
    
    
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


    def stretchNet(self, netItem: net.schematicNet, stretchEnd: str):
        match stretchEnd:
            case "p2":
                self._stretchNet = net.schematicNet(
                    netItem.sceneEndPoints[0], netItem.sceneEndPoints[1]
                )
            case "p1":
                self._stretchNet = net.schematicNet(
                    netItem.sceneEndPoints[1], netItem.sceneEndPoints[0]
                )
        self._stretchNet.stretch = True
        self._stretchNet.inherit(netItem)
        addDeleteStretchNetCommand = us.addDeleteShapeUndo(
            self, self._stretchNet, netItem
        )
        self.undoStack.push(addDeleteStretchNetCommand)

    @staticmethod
    def clearNetStatus(netsSet: set[net.schematicNet]):
        """
        Clear all assigned net names
        """
        for netItem in netsSet:
            netItem.nameConflict = False
            if netItem.nameStrength.value < 3:
                netItem.nameStrength = net.netNameStrengthEnum.NONAME

    # netlisting related methods.
    def groupAllNets(self, sceneNetsSet: set[net.schematicNet]) -> None:
        """
        This method starting from nets connected to pins, then named nets and unnamed
        nets, groups all the nets in the schematic.
        """
        try:
            # all the nets in the schematic in a set to remove duplicates
            # sceneNetsSet = self.findSceneNetsSet()
            self.clearNetStatus(sceneNetsSet)
            # first find nets connected to pins designating global nets.
            schematicSymbolSet = self.findSceneSymbolSet()
            globalNetsSet = self.findGlobalNets(schematicSymbolSet)
            sceneNetsSet -= globalNetsSet  # remove these nets from all nets set.
            # now remove nets connected to global nets from this set.
            sceneNetsSet = self.groupNamedNets(globalNetsSet, sceneNetsSet)
            # now find nets connected to schematic pins
            schemPinConNetsSet = self.findSchPinNets()
            sceneNetsSet -= schemPinConNetsSet
            # use these nets as starting nets to find other nets connected to them
            sceneNetsSet = self.groupNamedNets(schemPinConNetsSet, sceneNetsSet)
            # now find the set of nets whose name is set by the user
            namedNetsSet = set(
                [netItem for netItem in sceneNetsSet if netItem.nameStrength.value > 1]
            )
            # remove named nets from this remanining net set
            sceneNetsSet -= namedNetsSet
            # now remove already named net set from firstNetSet
            unnamedNets = self.groupNamedNets(namedNetsSet, sceneNetsSet)
            # now start netlisting from the unnamed nets
            self.groupUnnamedNets(unnamedNets, self.netCounter)
        except Exception as e:
            self.logger.error(e)

    def findGlobalNets(
        self, symbolSet: set[shp.schematicSymbol]
    ) -> set[net.schematicNet]:
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
            # self.logger.warning(f'global pins:{globalPinsSet}')
            for pinItem in globalPinsSet:
                pinNetSet = {
                    netItem
                    for netItem in self.items(pinItem.sceneBoundingRect())
                    if isinstance(netItem, net.schematicNet)
                }
                for netItem in pinNetSet:
                    if netItem.nameStrength.value == 3:
                        # check if net is already named explicitly
                        if netItem.name != pinItem.pinName:
                            netItem.nameConflict = True
                            self.logger.error(
                                f"Net name conflict at {pinItem.pinName} of "
                                f"{pinItem.parent.instanceName}."
                            )
                        else:
                            globalNetsSet.add(netItem)
                    else:
                        globalNetsSet.add(netItem)
                        netItem.name = pinItem.pinName
                        netItem.nameStrength = net.netNameStrengthEnum.INHERIT
            return globalNetsSet
        except Exception as e:
            self.logger.error(e)

    def findSchPinNets(self) -> set[net.schematicNet]:
        # nets connected to schematic pins.
        schemPinConNetsSet = set()
        # first start from schematic pins
        sceneSchemPinsSet = self.findSceneSchemPinsSet()
        for sceneSchemPin in sceneSchemPinsSet:
            pinNetSet = {
                netItem
                for netItem in self.items(sceneSchemPin.sceneBoundingRect())
                if isinstance(netItem, net.schematicNet)
            }
            for netItem in pinNetSet:
                if (
                    netItem.nameStrength.value == 3
                ):  # check if net name is not set explicitly
                    if netItem.name == sceneSchemPin.pinName:
                        schemPinConNetsSet.add(netItem)
                    else:
                        netItem.nameConflict = True
                        self.parent.parent.logger.error(
                            f"Net name conflict at {sceneSchemPin.pinName} of "
                            f"{sceneSchemPin.parent().instanceName}."
                        )
                else:
                    schemPinConNetsSet.add(netItem)
                    netItem.name = sceneSchemPin.pinName
                    netItem.nameStrength = net.netNameStrengthEnum.INHERIT
                netItem.update()
            schemPinConNetsSet.update(pinNetSet)
        return schemPinConNetsSet

    def groupNamedNets(
        self, namedNetsSet: set[net.schematicNet], unnamedNetsSet: set[net.schematicNet]
    ) -> set[net.schematicNet]:
        """
        Groups nets with the same name using namedNetsSet members as seeds and going
        through connections. Returns the set of still unnamed nets.
        """
        for netItem in namedNetsSet:
            self.schematicNets.setdefault(netItem.name, set())
            connectedNets, unnamedNetsSet = self.traverseNets(
                {
                    netItem,
                },
                unnamedNetsSet,
            )
            self.schematicNets[netItem.name] |= connectedNets
        # These are the nets not connected to any named net
        return unnamedNetsSet

    def groupUnnamedNets(self, unnamedNetsSet: set[net.schematicNet], nameCounter: int):
        """
        Groups nets together if they are connected and assign them default names
        if they don't have a name assigned.
        """
        # select a net from the set and remove it from the set
        try:
            initialNet = (
                unnamedNetsSet.pop()
            )  # assign it a name, net0, net1, net2, etc.
        except KeyError:  # initialNet set is empty
            pass
        else:
            initialNet.name = "net" + str(nameCounter)
            # now go through the set and see if any of the
            # nets are connected to the initial net
            # remove them from the set and add them to the initial net's set
            self.schematicNets[initialNet.name], unnamedNetsSet = self.traverseNets(
                {
                    initialNet,
                },
                unnamedNetsSet,
            )
            nameCounter += 1
            if len(unnamedNetsSet) > 1:
                self.groupUnnamedNets(unnamedNetsSet, nameCounter)
            elif len(unnamedNetsSet) == 1:
                lastNet = unnamedNetsSet.pop()
                lastNet.name = "net" + str(nameCounter)
                self.schematicNets[lastNet.name] = {lastNet}

    def traverseNets(
        self, connectedSet: set[net.schematicNet], otherNetsSet: set[net.schematicNet]
    ) -> tuple[set[net.schematicNet], set[net.schematicNet]]:
        """
        Start from a net and traverse the schematic to find all connected nets.
        If the connected net search
        is exhausted, remove those nets from the scene nets set and start again
        in another net until all
        the nets in the scene are exhausted.
        """
        newFoundConnectedSet = set()
        for netItem in connectedSet:
            for netItem2 in otherNetsSet:
                if self.checkNetConnect(netItem, netItem2):
                    netItem2.inherit(netItem)
                    if not netItem2.nameConflict:
                        newFoundConnectedSet.add(netItem2)
        # keep searching if you already found a net connected to the initial net
        if len(newFoundConnectedSet) > 0:
            connectedSet.update(newFoundConnectedSet)
            otherNetsSet -= newFoundConnectedSet
            self.traverseNets(connectedSet, otherNetsSet)
        return connectedSet, otherNetsSet

    def findConnectedNetSet(self, startNet: net.schematicNet) -> set[net.schematicNet]:
        """
        find all the nets connected to a net including nets connected by name.
        """

        sceneNetSet = self.findSceneNetsSet()
        connectedSet, otherNetsSet = self.traverseNets({startNet}, sceneNetSet)
        # now check if any other name is connected due to a common name:
        for netItem in otherNetsSet:
            if netItem.name == startNet.name and (netItem.nameStrength.value > 1):
                connectedSet.add(netItem)
        return connectedSet - {startNet}

    @staticmethod
    def checkPinNetConnect(pinItem: shp.schematicPin, netItem: net.schematicNet):
        """
        Determine if a pin is connected to a net.
        """
        return bool(pinItem.sceneBoundingRect().intersects(netItem.sceneBoundingRect()))

    @staticmethod
    def checkNetConnect(netItem, otherNetItem):
        """
        Determine if a net is connected to another one. One net should end on the other net.
        """

        if otherNetItem is not netItem:
            for netItemEnd, otherEnd in itt.product(
                netItem.sceneEndPoints, otherNetItem.sceneEndPoints
            ):
                # not a very elegant solution to mistakes in net end points.
                if (netItemEnd - otherEnd).manhattanLength() <= 1:
                    return True
        else:
            return False

    @lru_cache(maxsize=128)
    def generatePinNetMap(self, sceneSymbolSet: tuple[set[shp.schematicSymbol]]):
        """
        For symbols in sceneSymbolSet, find which pin is connected to which net. If a
        pin is not connected, assign to it a default net starting with d prefix.
        """
        netCounter = 0
        for symbolItem in sceneSymbolSet:
            for pinName, pinItem in symbolItem.pins.items():
                pinItem.connected = False  # clear connections

                pinConnectedNets = [
                    netItem
                    for netItem in self.items(
                        pinItem.sceneBoundingRect().adjusted(-2, -2, 2, 2)
                    )
                    if isinstance(netItem, net.schematicNet)
                ]
                # this will name the pin by first net it finds in the bounding rectangle of
                # the pin. If there are multiple nets in the bounding rectangle, the first
                # net in the list will be the one used.
                if pinConnectedNets:
                    symbolItem.pinNetMap[pinName] = pinConnectedNets[0].name
                    pinItem.connected = True

                if not pinItem.connected:
                    # assign a default net name prefixed with d(efault).
                    symbolItem.pinNetMap[pinName] = f"dnet{netCounter}"
                    self.logger.warning(
                        f"left unconnected:{symbolItem.pinNetMap[pinName]}"
                    )
                    netCounter += 1
            # now reorder pinNetMap according pinOrder attribute
            if symbolItem.symattrs.get("pinOrder"):
                pinOrderList = list()
                [
                    pinOrderList.append(item.strip())
                    for item in symbolItem.symattrs.get("pinOrder").split(",")
                ]
                symbolItem.pinNetMap = {
                    pinName: symbolItem.pinNetMap[pinName] for pinName in pinOrderList
                }

    @staticmethod
    def findSceneCells(symbolSet):
        """
        This function just goes through set of symbol items in the scene and
        checks if that symbol's cell is encountered first time. If so, it adds
        it to a dictionary   cell_name:symbol
        """
        symbolGroupDict = dict()
        for symbolItem in symbolSet:
            if symbolItem.cellName not in symbolGroupDict.keys():
                symbolGroupDict[symbolItem.cellName] = symbolItem
        return symbolGroupDict

    def findSceneSymbolSet(self) -> set[shp.schematicSymbol]:
        """
        Find all the symbols on the scene as a set.
        """
        return {item for item in self.items() if isinstance(item, shp.schematicSymbol)}

    def findSceneNetsSet(self) -> set[net.schematicNet]:
        return {item for item in self.items() if isinstance(item, net.schematicNet)}

    def findRectSymbolPin(self, rect: Union[QRect, QRectF]) -> set[shp.symbolPin]:
        pinsRectSet = {
            item for item in self.items(rect) if isinstance(item, shp.symbolPin)
        }
        return pinsRectSet

    def findSceneSchemPinsSet(self) -> set[shp.schematicPin]:
        pinsSceneSet = {
            item for item in self.items() if isinstance(item, shp.schematicPin)
        }
        if pinsSceneSet:  # check pinsSceneSet is empty
            return pinsSceneSet
        else:
            return set()

    def findSceneTextSet(self) -> set[shp.text]:
        if textSceneSet := {
            item for item in self.items() if isinstance(item, shp.text)
        }:
            return textSceneSet
        else:
            return set()

    def addStretchWires(self, start: QPoint, end: QPoint) -> list[net.schematicNet]:
        """
        Add a trio of wires between two points
        """
        try:
            if (
                start.y() == end.y() or start.x() == end.x()
            ):  # horizontal or verticalline
                lines = [net.schematicNet(start, end)]
            else:
                firstPointX = self.snapToBase(
                    (end.x() - start.x()) / 3 + start.x(), self.snapTuple[0]
                )
                firstPointY = start.y()
                firstPoint = QPoint(firstPointX, firstPointY)
                secondPoint = QPoint(firstPointX, end.y())
                lines = list()
                if start != firstPoint:
                    lines.append(net.schematicNet(start, firstPoint))
                if firstPoint != secondPoint:
                    lines.append(net.schematicNet(firstPoint, secondPoint))
                if secondPoint != end:
                    lines.append(net.schematicNet(secondPoint, end))
            return lines
        except Exception as e:
            self.logger.error(f"extend wires error{e}")
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
        text = shp.text(
            pos,
            self.noteText,
            self.noteFontFamily,
            self.noteFontStyle,
            self.noteFontSize,
            self.noteAlign,
            self.noteOrient,
        )
        self.addUndoStack(text)
        return text

    def drawInstance(self, pos: QPoint):
        """
        Add an instance of a symbol to the scene.
        """
        instance = self.instSymbol(pos)

        self.instanceCounter += 1
        self.addUndoStack(instance)
        self.instanceSymbolTuple = None
        return instance

    def instSymbol(self, pos: QPoint):
        itemShapes = []
        itemAttributes = {}
        try:
            with open(self.instanceSymbolTuple.viewItem.viewPath, "r") as temp:
                items = json.load(temp)
                if items[0]["cellView"] != "symbol":
                    self.logger.error("Not a symbol!")
                    return

                for item in items[2:]:
                    if item["type"] == "attr":
                        itemAttributes[item["nam"]] = item["def"]
                    else:
                        itemShapes.append(lj.symbolItems(self).create(item))
                symbolInstance = shp.schematicSymbol(itemShapes, itemAttributes)

                symbolInstance.setPos(pos)
                symbolInstance.counter = self.instanceCounter
                symbolInstance.instanceName = f"I{symbolInstance.counter}"
                symbolInstance.libraryName = (
                    self.instanceSymbolTuple.libraryItem.libraryName
                )
                symbolInstance.cellName = self.instanceSymbolTuple.cellItem.cellName
                symbolInstance.viewName = self.instanceSymbolTuple.viewItem.viewName
                for labelItem in symbolInstance.labels.values():
                    labelItem.labelDefs()

                return symbolInstance
        except Exception as e:
            self.logger.warning(f"instantiation error: {e}")

    def copySelectedItems(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                selectedItemJson = json.dumps(item, cls=schenc.schematicEncoder)
                itemCopyDict = json.loads(selectedItemJson)
                shape = lj.schematicItems(self).create(itemCopyDict)
                if shape is not None:
                    self.addUndoStack(shape)
                    # shift position by four grid units to right and down
                    shape.setPos(
                        QPoint(
                            item.pos().x() + 4 * self.snapTuple[0],
                            item.pos().y() + 4 * self.snapTuple[1],
                        )
                    )
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
            topLevelItems = []
            # Insert a cellview item at the beginning of the list
            topLevelItems.insert(0, {"cellView": "schematic"})
            topLevelItems.insert(1, {"snapGrid": self.snapTuple})
            topLevelItems.extend(
                [item for item in self.items() if item.parentItem() is None]
            )
            with file.open(mode="w") as f:
                json.dump(topLevelItems, f, cls=schenc.schematicEncoder, indent=4)
            # if there is a parent editor, to reload the changes.
            print(self.editorWindow.parentEditor)
            if self.editorWindow.parentEditor is not None:
                editorType = self.findEditorTypeString(self.editorWindow.parentEditor)
                if editorType == "schematicEditor":
                    self.editorWindow.parentEditor.loadSchematic()
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
        index = str(type(editorWindow)).rfind(".")
        if index == -1:
            return str(type(editorWindow))
        else:
            print(str(type(editorWindow))[index + 1 : -2])
            return str(type(editorWindow))[index + 1 : -2]

    def loadSchematicItems(self, itemsList: list[dict]) -> None:
        """
        load schematic from item list
        """
        snapGrid = itemsList[1].get("snapGrid")
        self.majorGrid = snapGrid[0]  # dot/line grid spacing
        self.snapTuple = (snapGrid[1], snapGrid[1])
        self.snapDistance = 2 * snapGrid[1]
        shapesList = list()
        for itemDict in itemsList[2:]:
            itemShape = lj.schematicItems(self).create(itemDict)
            if (
                isinstance(itemShape, shp.schematicSymbol)
                and itemShape.counter > self.instanceCounter
            ):
                self.instanceCounter = itemShape.counter
                # increment item counter for next symbol
                self.instanceCounter += 1
            shapesList.append(itemShape)
        self.undoStack.push(us.loadShapesUndo(self, shapesList))

    def reloadScene(self):
        topLevelItems = [item for item in self.items() if item.parentItem() is None]
        # Insert a layout item at the beginning of the list
        topLevelItems.insert(0, {"cellView": "schematic"})
        topLevelItems.insert(1, {"snapGrid": self.snapTuple})
        items = json.loads(json.dumps(topLevelItems, cls=schenc.schematicEncoder))
        self.clear()
        self.loadSchematicItems(items)

    def viewObjProperties(self):
        """
        Display the properties of the selected object.
        """
        try:
            if self.selectedItems() is not None:
                for item in self.selectedItems():
                    item.prepareGeometryChange()
                    if isinstance(item, shp.schematicSymbol):
                        self.setInstanceProperties(item)
                    elif isinstance(item, net.schematicNet):
                        self.setNetProperties(item)
                    elif isinstance(item, shp.text):
                        item = self.setTextProperties(item)
                    elif isinstance(item, shp.schematicPin):
                        self.setSchematicPinProperties(item)
        except Exception as e:
            self.logger.error(e)

    def setInstanceProperties(self, item):
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
                dlg.instanceLabelsLayout.addWidget(
                    edf.boldLabel(label.labelName[1:], dlg), row_index, 0
                )
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
        for counter, name in enumerate(item._symattrs.keys()):
            dlg.instanceAttributesLayout.addWidget(edf.boldLabel(name, dlg), counter, 0)
            labelType = edf.longLineEdit()
            labelType.setReadOnly(True)
            labelNameEdit = edf.longLineEdit()
            labelNameEdit.setText(item._symattrs.get(name))
            labelNameEdit.setToolTip(f"{name} attribute (Read Only)")
            dlg.instanceAttributesLayout.addWidget(labelNameEdit, counter, 1)
        if dlg.exec() == QDialog.Accepted:
            item.instanceName = dlg.instNameEdit.text().strip()
            item.angle = float(dlg.angleEdit.text().strip())
            location = QPoint(
                int(float(dlg.xLocationEdit.text().strip())),
                int(float(dlg.yLocationEdit.text().strip())),
            )
            item.setPos(self.snapToGrid(location - self.origin, self.snapTuple))
            tempDoc = QTextDocument()
            for i in range(dlg.instanceLabelsLayout.rowCount()):
                # first create label name document with HTML annotations
                tempDoc.setHtml(
                    dlg.instanceLabelsLayout.itemAtPosition(i, 0).widget().text()
                )
                # now strip html annotations
                tempLabelName = f"@{tempDoc.toPlainText().strip()}"
                # check if label name is in label dictionary of item.
                if item.labels.get(tempLabelName):
                    # this is where the label value is set.
                    item.labels[tempLabelName].labelValue = (
                        dlg.instanceLabelsLayout.itemAtPosition(i, 1).widget().text()
                    )
                    visible = (
                        dlg.instanceLabelsLayout.itemAtPosition(i, 2)
                        .widget()
                        .currentText()
                    )
                    if visible == "True":
                        item.labels[tempLabelName].labelVisible = True
                    else:
                        item.labels[tempLabelName].labelVisible = False
            [labelItem.labelDefs() for labelItem in item.labels.values()]

    def setNetProperties(self, netItem: net.schematicNet):
        dlg = pdlg.netProperties(self.editorWindow)
        dlg.netStartPointEditX.setText(
            str(round(netItem.mapToScene(netItem.draftLine.p1()).x()))
        )
        dlg.netStartPointEditY.setText(
            str(round(netItem.mapToScene(netItem.draftLine.p1()).y()))
        )
        dlg.netEndPointEditX.setText(
            str(round(netItem.mapToScene(netItem.draftLine.p2()).x()))
        )
        dlg.netEndPointEditY.setText(
            str(round(netItem.mapToScene(netItem.draftLine.p2()).y()))
        )
        dlg.netNameEdit.setText(netItem.name)

        if dlg.exec() == QDialog.Accepted:
            netItem.name = dlg.netNameEdit.text().strip()
            if netItem.name != "":
                netItem.nameStrength = net.netNameStrengthEnum.SET
                self.findConnectedNetSet(netItem)
                # for otherNet in findConnectedNets:
                #     otherNet.inherit(netItem)

    def setTextProperties(self, item):
        dlg = pdlg.noteTextEditProperties(self.editorWindow, item)
        if dlg.exec() == QDialog.Accepted:
            # item.prepareGeometryChange()
            start = item.start
            self.removeItem(item)
            item = shp.text(
                start,
                dlg.plainTextEdit.toPlainText(),
                dlg.familyCB.currentText(),
                dlg.fontStyleCB.currentText(),
                dlg.fontsizeCB.currentText(),
                dlg.textAlignmCB.currentText(),
                dlg.textOrientCB.currentText(),
            )
            self.rotateAnItem(start, item, float(item.textOrient[1:]))
            self.addItem(item)
        return item

    def setSchematicPinProperties(self, item):
        dlg = pdlg.schematicPinPropertiesDialog(self.editorWindow, item)
        dlg.pinName.setText(item.pinName)
        dlg.pinDir.setCurrentText(item.pinDir)
        dlg.pinType.setCurrentText(item.pinType)
        dlg.angleEdit.setText(str(item.angle))
        dlg.xlocationEdit.setText(str(item.mapToScene(item.start).x()))
        dlg.ylocationEdit.setText(str(item.mapToScene(item.start).y()))
        if dlg.exec() == QDialog.Accepted:
            item.pinName = dlg.pinName.text().strip()
            item.pinDir = dlg.pinDir.currentText()
            item.pinType = dlg.pinType.currentText()
            itemStartPos = QPoint(
                int(float(dlg.xlocationEdit.text().strip())),
                int(float(dlg.ylocationEdit.text().strip())),
            )
            item.start = self.snapToGrid(itemStartPos - self.origin, self.snapTuple)
            item.angle = float(dlg.angleEdit.text().strip())

    def hilightNets(self):
        """
        Show the connections the selected items.
        """
        try:
            self.highlightNets = bool(self.editorWindow.hilightNetAction.isChecked())
        except Exception as e:
            self.logger.error(e)

    def goDownHier(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                if isinstance(item, shp.schematicSymbol):
                    dlg = fd.goDownHierDialogue(self.editorWindow)
                    libItem = libm.getLibItem(
                        self.editorWindow.libraryView.libraryModel, item.libraryName
                    )
                    cellItem = libm.getCellItem(libItem, item.cellName)
                    viewNames = [
                        cellItem.child(i).text()
                        for i in range(cellItem.rowCount())
                        # if cellItem.child(i).text() != item.viewName
                        if "schematic" in cellItem.child(i).text()
                        or "symbol" in cellItem.child(i).text()
                    ]
                    dlg.viewListCB.addItems(viewNames)
                    if dlg.exec() == QDialog.Accepted:
                        libItem = libm.getLibItem(
                            self.editorWindow.libraryView.libraryModel, item.libraryName
                        )
                        cellItem = libm.getCellItem(libItem, item.cellName)
                        viewItem = libm.getViewItem(
                            cellItem, dlg.viewListCB.currentText()
                        )
                        openViewTuple = (
                            self.editorWindow.libraryView.libBrowsW.openCellView(
                                viewItem, cellItem, libItem
                            )
                        )

                        if self.editorWindow.appMainW.openViews[openViewTuple]:
                            childWindow = self.editorWindow.appMainW.openViews[
                                openViewTuple
                            ]
                            childWindow.parentEditor = self.editorWindow
                            childWindowType = self.findEditorTypeString(childWindow)

                            if childWindowType == "symbolEditor":
                                childWindow.symbolToolbar.addAction(
                                    childWindow.goUpAction
                                )
                            elif childWindowType == "schematicEditor":
                                childWindow.schematicToolbar.addAction(
                                    childWindow.goUpAction
                                )
                            if dlg.buttonId == 2:
                                childWindow.centralW.scene.readOnly = True

    def ignoreSymbol(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                if isinstance(item, shp.schematicSymbol):
                    item.netlistIgnore = not item.netlistIgnore
        else:
            self.logger.warning("No symbol selected")

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

    def selectInRectItems(self, selectionRect: QRect, partialSelection=False):
        """
        Select items in the scene.
        """

        mode = Qt.IntersectsItemShape if partialSelection else Qt.ContainsItemShape
        if self.selectModes.selectAll:
            [item.setSelected(True) for item in self.items(selectionRect, mode=mode)]
        elif self.selectModes.selectDevice:
            [
                item.setSelected(True)
                for item in self.items(selectionRect, mode=mode)
                if isinstance(item, shp.schematicSymbol)
            ]
        elif self.selectModes.selectNet:
            [
                item.setSelected(True)
                for item in self.items(selectionRect, mode=mode)
                if isinstance(item, net.schematicNet)
            ]
        elif self.selectModes.selectPin:
            [
                item.setSelected(True)
                for item in self.items(selectionRect, mode=mode)
                if isinstance(item, shp.schematicPin)
            ]

    def renumberInstances(self):
        symbolList = [
            item for item in self.items() if isinstance(item, shp.schematicSymbol)
        ]
        self.instanceCounter = 0
        for symbolInstance in symbolList:
            symbolInstance.counter = self.instanceCounter
            if symbolInstance.instanceName.startswith("I"):
                symbolInstance.instanceName = f"I{symbolInstance.counter}"
                self.instanceCounter += 1
        self.reloadScene()


class layoutScene(editorScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.selectEdLayer = laylyr.pdkAllLayers[0]
        self.layoutShapes = [
            "Inst",
            "Rect",
            "Path",
            "Label",
            "Via",
            "Pin",
            "Polygon",
            "Pcell",
            "Ruler",
        ]
        # draw modes
        self.editModes = ddef.layoutModes(
            selectItem=False,
            deleteItem=False,
            moveItem=False,
            copyItem=False,
            rotateItem=False,
            changeOrigin=False,
            panView=False,
            drawPath=False,
            drawPin=False,
            drawArc=False,
            drawPolygon=False,
            addLabel=False,
            addVia=False,
            drawRect=False,
            drawLine=False,
            drawCircle=False,
            drawRuler=False,
            stretchItem=False,
            addInstance=False,
        )
        self.editModes.setMode("selectItem")
        self.selectModes = ddef.layoutSelectModes(
            selectAll=True,
            selectPath=False,
            selectInstance=False,
            selectVia=False,
            selectPin=False,
            selectLabel=False,
            selectText=False,
        )
        self.newInstance = None
        self.layoutInstanceTuple = None
        self._scale = fabproc.dbu
        self.itemCounter = 0
        self._newPath = None
        self._stretchPath = None
        self.newPathTuple = None
        self.draftLine = None
        self.m45Rotate = QTransform()
        self.m45Rotate.rotate(-45)
        self.newPin = None
        self.newPinTuple = None
        self.newLabelTuple = None
        self.newLabel = None
        self._newRect = None
        self._newPolygon = None
        self.arrayViaTuple = None
        self.singleVia = None
        self._arrayVia = None
        self._polygonGuideLine = None
        self._newRuler = None
        self.rulersSet = set()
        # this needs move to configuration file...
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamily = [
            family for family in fontFamilies if QFontDatabase.isFixedPitch(family)
        ][0]
        fontStyle = QFontDatabase.styles(fixedFamily)[0]
        self.rulerFont = QFont(fixedFamily)
        self.rulerFont.setStyleName(fontStyle)
        fontSize = [size for size in QFontDatabase.pointSizes(fixedFamily, fontStyle)][
            1
        ]
        self.rulerFont.setPointSize(fontSize)
        self.rulerFont.setKerning(False)
        self.rulerTickGap = fabproc.dbu
        self.rulerTickLength = int(fabproc.dbu / 10)
        self.rulerWidth = 2

    @property
    def drawMode(self):
        return any(
            (
                self.editModes.drawPath,
                self.editModes.drawPin,
                self.editModes.drawArc,
                self.editModes.drawPolygon,
                self.editModes.drawRect,
                self.editModes.drawCircle,
                self.editModes.drawRuler,
            )
        )

    # Order of drawing
    # 1. Rect
    # 2. Path
    # 3. Pin
    # 4. Label
    # 5. Via/Contact
    # 6. Polygon
    # 7. Add instance
    # 8. select item/s
    # 9. rotate item/s

    @staticmethod
    def toLayoutCoord(point: Union[QPoint | QPointF]) -> QPoint | QPointF:
        """
        Converts a point in scene coordinates to layout coordinates by dividing it to
        fabproc.dbu.
        """
        point /= fabproc.dbu
        return point

    @staticmethod
    def toSceneCoord(point: Union[QPoint | QPointF]) -> QPoint | QPointF:
        """
        Converts a point in layout coordinates to scene coordinates by multiplying it with
        fabproc.dbu.
        """
        point *= fabproc.dbu
        return point

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        """
        Handle the mouse press event.

        Args:
            mouse_event: The mouse event object.

        Returns:
            None
        """
        # Store the mouse press location
        self.mousePressLoc = mouse_event.scenePos().toPoint()
        # Call the base class mouse press event
        super().mousePressEvent(mouse_event)
        try:
            # Get the keyboard modifiers
            modifiers = QGuiApplication.keyboardModifiers()
            # Get the bounding rectangle of the view
            self.viewRect = self.parent.view.mapToScene(
                self.parent.view.viewport().rect()
            ).boundingRect()

            if mouse_event.button() == Qt.LeftButton:
                if self.editModes.drawPath:
                    self.editorWindow.messageLine.setText("Wire mode")
                    if self._newPath:
                        if self._newPath.draftLine.isNull():
                            self.removeItem(self._newPath)
                            self.undoStack.removeLastCommand()
                        self._newPath = None
                    # Create a new path
                    self._newPath = lshp.layoutPath(
                        QLineF(self.mousePressLoc, self.mousePressLoc),
                        self.newPathTuple.layer,
                        self.newPathTuple.width,
                        self.newPathTuple.startExtend,
                        self.newPathTuple.endExtend,
                        self.newPathTuple.mode,
                    )
                    self._newPath.name = self.newPathTuple.name
                    # self._newPath.setSelected(True)

                elif self.editModes.drawRect and self._newRect is not None:
                    self._newRect.end = self.mousePressLoc
                    self._newRect.setSelected(False)
                    self._newRect = None
                elif self.editModes.drawRuler:
                    if self._newRuler is None:
                        self._newRuler = lshp.layoutRuler(
                            QLineF(self.mousePressLoc, self.mousePressLoc),
                            width=self.rulerWidth,
                            tickGap=self.rulerTickGap,
                            tickLength=self.rulerTickLength,
                            tickFont=self.rulerFont,
                        )
                        self.addUndoStack(self._newRuler)
                        self.rulersSet.add(self._newRuler)
                    else:
                        self._newRuler = None

                elif self.editModes.drawPin:
                    if self.newLabel is None:
                        if self.newPin is None:
                            # Create a new pin
                            self.newPin = lshp.layoutPin(
                                self.mousePressLoc,
                                self.mousePressLoc,
                                *self.newPinTuple,
                            )
                            self.addUndoStack(self.newPin)
                        else:
                            self.newLabel = lshp.layoutLabel(
                                self.mouseReleaseLoc,
                                *self.newLabelTuple,
                            )
                            self.addUndoStack(self.newLabel)
                            self.newPin.label = self.newLabel
                            self.newPin = None
                    else:
                        self.newLabel.start = self.mousePressLoc
                        self.newLabel = None

                elif self.editModes.addLabel and self.newLabel is not None:
                    self.newLabelTuple = None
                    self.newLabel = None
                    self.editModes.setMode("selectItem")
                elif self.editModes.addVia and self._arrayVia is not None:
                    self.arrayViaTuple = None
                    self._arrayVia = None
                    self.editModes.setMode("selectItem")
                elif self.editModes.selectItem:
                    # Select scene items
                    self.selectSceneItems(modifiers)
                elif self.editModes.rotateItem:
                    self.editorWindow.messageLine.setText("Rotate item")
                    if self.selectedItems():
                        # Rotate selected items
                        self.rotateSelectedItems(self.mousePressLoc)
                elif self.editModes.changeOrigin:
                    self.origin = self.mousePressLoc
                    self.editModes.setMode("selectItem")
        except Exception as e:
            self.logger.error(f"mouse press error: {e}")

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        """
        Handle the mouse move event.

        Args:
            mouse_event (QGraphicsSceneMouseEvent): The mouse event object.

        Returns:
            None
        """
        # Get the current mouse position
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        # Call the parent class's mouseMoveEvent method
        super().mouseMoveEvent(mouse_event)
        # Get the keyboard modifiers
        modifiers = QGuiApplication.keyboardModifiers()
        if mouse_event.buttons() == Qt.LeftButton:
            # Handle selecting item mode with shift modifier
            if self.editModes.selectItem and modifiers == Qt.ShiftModifier:
                self.selectionRectItem.setRect(
                    QRectF(self.mousePressLoc, self.mouseMoveLoc)
                )
        else:
            if self.editModes.drawRect and self._newRect:
                if self._newRect.scene() is None:
                    self.addUndoStack(self._newRect)
                self._newRect.end = self.mouseMoveLoc
            # Handle drawing pin mode with no new pin
            elif self.editModes.drawPin:
                if self.newPin is not None:
                    self.newPin.end = self.mouseMoveLoc
                else:
                    if self.newLabel is not None:
                        self.newLabel.start = self.mouseMoveLoc
            # Handle drawing path mode
            elif self.editModes.drawPath and self._newPath is not None:
                self._newPath.draftLine = QLineF(
                    self._newPath.draftLine.p1(), self.mouseMoveLoc
                )
                if self._newPath.scene() is None:
                    self.addUndoStack(self._newPath)
            elif self.editModes.drawRuler and self._newRuler is not None:
                self._newRuler.draftLine = QLineF(
                    self._newRuler.draftLine.p1(), self.mouseMoveLoc
                )
            # Handle adding label mode
            elif self.editModes.addLabel:
                if self.newLabel is not None:  # already defined a new label
                    self.newLabel.start = self.mouseMoveLoc
                # there is no new label but there is a new label tuple defined
                elif self.newLabelTuple is not None:
                    self.newLabel = lshp.layoutLabel(
                        self.mouseMoveLoc, *self.newLabelTuple
                    )
                    self.addUndoStack(self.newLabel)
            # Handle adding via mode with array via tuple
            elif self.editModes.addVia and self.arrayViaTuple is not None:
                if self._arrayVia is None:
                    singleVia = lshp.layoutVia(
                        QPoint(0, 0),
                        *self.arrayViaTuple.singleViaTuple,
                    )
                    self._arrayVia = lshp.layoutViaArray(
                        self.mouseMoveLoc,
                        singleVia,
                        self.arrayViaTuple.xs,
                        self.arrayViaTuple.ys,
                        self.arrayViaTuple.xnum,
                        self.arrayViaTuple.ynum,
                    )
                    self.addUndoStack(self._arrayVia)
                else:
                    self._arrayVia.setPos(self.mouseMoveLoc - self._arrayVia.start)
                    self._arrayVia.setSelected(True)
            # Handle drawing polygon mode
            elif self.editModes.drawPolygon and self._newPolygon is not None:
                self._polygonGuideLine.setLine(
                    QLineF(self._newPolygon.points[-1], self.mouseMoveLoc)
                )
            # Handle adding instance mode with layout instance tuple
            elif self.editModes.addInstance and self.layoutInstanceTuple is not None:
                if self.newInstance is None:
                    self.newInstance = self.instLayout()
                    # if new instance is a pcell, start a dialogue for pcell parameters
                    if isinstance(self.newInstance, pcells.baseCell):
                        dlg = ldlg.pcellInstanceDialog(self.editorWindow)
                        dlg.pcellLibName.setText(self.newInstance.libraryName)
                        dlg.pcellCellName.setText(self.newInstance.cellName)
                        dlg.pcellViewName.setText(self.newInstance.viewName)
                        initArgs = inspect.signature(
                            self.newInstance.__class__.__init__
                        ).parameters
                        argsUsed = [param for param in initArgs if (param != "self")]
                        argDict = {
                            arg: getattr(self.newInstance, arg) for arg in argsUsed
                        }
                        lineEditDict = {
                            key: edf.shortLineEdit(value)
                            for key, value in argDict.items()
                        }
                        for key, value in lineEditDict.items():
                            dlg.instanceParamsLayout.addRow(key, value)
                        if dlg.exec() == QDialog.Accepted:
                            instanceValuesDict = {}
                            for key, value in lineEditDict.items():
                                instanceValuesDict[key] = value.text()
                            self.newInstance(*instanceValuesDict.values())
                    self.addUndoStack(self.newInstance)
                self.newInstance.setPos(self.mouseMoveLoc - self.newInstance.start)
            elif self.editModes.stretchItem and self._stretchPath is not None:
                self._stretchPath.draftLine = QLineF(
                    self._stretchPath.draftLine.p1(), self.mouseMoveLoc
                )
        # Calculate the cursor position in layout units
        cursorPosition = self.toLayoutCoord(self.mouseMoveLoc - self.origin)

        # Show the cursor position in the status line
        self.statusLine.showMessage(
            f"Cursor Position: ({cursorPosition.x()}, {cursorPosition.y()})"
        )

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        try:
            if mouse_event.button() == Qt.LeftButton:
                if self.editModes.drawRect:
                    self.editorWindow.messageLine.setText("Rectangle mode.")
                    # Create a new rectangle
                    self._newRect = lshp.layoutRect(
                        self.mouseReleaseLoc,
                        self.mouseReleaseLoc,
                        self.selectEdLayer,
                    )

                elif self.editModes.drawPolygon:
                    if self._newPolygon is None:
                        # Create a new polygon
                        self._newPolygon = lshp.layoutPolygon(
                            [self.mouseReleaseLoc, self.mouseReleaseLoc],
                            self.selectEdLayer,
                        )
                        self.addUndoStack(self._newPolygon)
                        # Create a guide line for the polygon
                        self._polygonGuideLine = QGraphicsLineItem(
                            QLineF(
                                self._newPolygon.points[-2], self._newPolygon.points[-1]
                            )
                        )
                        self._polygonGuideLine.setPen(
                            QPen(QColor(255, 255, 0), 1, Qt.DashLine)
                        )
                        self.addUndoStack(self._polygonGuideLine)

                    else:
                        self._newPolygon.addPoint(self.mouseReleaseLoc)
                elif self.editModes.addInstance and self.newInstance is not None:
                    self.newInstance = None
                    self.layoutInstanceTuple = None
                    self.editModes.setMode("selectItem")
                elif self.editModes.selectItem and modifiers == Qt.ShiftModifier:
                    self.selectInRectItems(
                        self.selectionRectItem.rect(), self.partialSelection
                    )
                    self.removeItem(self.selectionRectItem)
                    self.selectionRectItem = None

        except Exception as e:
            self.logger.error(f"mouse release error: {e}")


    def instLayout(self):
        """
        Read a layout file and create layoutShape objects from it.
        """
        match self.layoutInstanceTuple.viewItem.viewType:
            case "layout":
                with self.layoutInstanceTuple.viewItem.viewPath.open("r") as temp:
                    try:
                        decodedData = json.load(temp)
                        if decodedData[0]["cellView"] != "layout":
                            self.logger.error("Not a layout cell")
                        else:
                            instanceShapes = [
                                lj.layoutItems(self).create(item)
                                for item in decodedData[2:]
                                if item.get("type") in self.layoutShapes
                            ]
                            layoutInstance = lshp.layoutInstance(instanceShapes)
                            layoutInstance.libraryName = (
                                self.layoutInstanceTuple.libraryItem.libraryName
                            )
                            layoutInstance.cellName = (
                                self.layoutInstanceTuple.cellItem.cellName
                            )
                            layoutInstance.viewName = (
                                self.layoutInstanceTuple.viewItem.viewName
                            )
                            self.itemCounter += 1
                            layoutInstance.counter = self.itemCounter
                            layoutInstance.instanceName = f"I{layoutInstance.counter}"
                            # For each instance assign a counter number from the scene
                            return layoutInstance
                    except json.JSONDecodeError:
                        self.logger.warning("Invalid JSON File")
            case "pcell":
                with open(self.layoutInstanceTuple.viewItem.viewPath, "r") as temp:
                    try:
                        pcellRefDict = json.load(temp)
                        if pcellRefDict[0]["cellView"] != "pcell":
                            self.logger.error("Not a pcell cell")
                        else:
                            # create a pcell instance with default parameters.
                            pcellInstance = eval(
                                f"pcells.{pcellRefDict[1]['reference']}()"
                            )
                            # now evaluate pcell

                            pcellInstance.libraryName = (
                                self.layoutInstanceTuple.libraryItem.libraryName
                            )
                            pcellInstance.cellName = (
                                self.layoutInstanceTuple.cellItem.cellName
                            )
                            pcellInstance.viewName = (
                                self.layoutInstanceTuple.viewItem.viewName
                            )
                            self.itemCounter += 1
                            pcellInstance.counter = self.itemCounter
                            # This needs to become more sophisticated.
                            pcellInstance.instanceName = f"I{pcellInstance.counter}"

                            return pcellInstance
                    except Exception as e:
                        self.logger.error(f"Cannot read pcell: {e}")

    def findScenelayoutCellSet(self) -> set[lshp.layoutInstance]:
        """
        Find all the symbols on the scene as a set.
        """
        return {item for item in self.items() if isinstance(item, lshp.layoutInstance)}

    def saveLayoutCell(self, filePathObj: pathlib.Path) -> None:
        """
        Save the layout cell items to a file.

        Args:
            filePathObj (pathlib.Path): filepath object for layout file.

        Returns:
            None
        """
        try:
            # Only save the top-level items

            topLevelItems = [item for item in self.items() if item.parentItem() is None]
            topLevelItems.insert(0, {"cellView": "layout"})
            topLevelItems.insert(1, {"snapGrid": self.snapTuple})
            with filePathObj.open("w") as file:
                # Serialize items to JSON using layoutEncoder class
                json.dump(topLevelItems, file, cls=layenc.layoutEncoder)
        except Exception as e:
            self.logger.error(f"Cannot save layout: {e}")

    def loadLayoutCell(self, filePathObj: pathlib.Path) -> None:
        """
        Load the layout cell from the given file path.

        Args:
            filePathObj (pathlib.Path): The file path object.

        Returns:
            None
        """
        try:
            with filePathObj.open("r") as file:
                decodedData = json.load(file)
            snapGrid = decodedData[1].get("snapGrid")
            self.majorGrid = snapGrid[0]  # dot/line grid spacing
            self.snapGrid = snapGrid[1]  # snapping grid size
            self.snapTuple = (self.snapGrid, self.snapGrid)
            self.snapDistance = 2 * self.snapGrid
            starttime = time.time()
            self.createLayoutItems(decodedData[2:])
            endtime = time.time()
            print(f"load time: {endtime-starttime}")
        except Exception as e:
            self.logger.error(f"Cannot load layout: {e}")

    def createLayoutItems(self, decodedData):
        if decodedData:
            loadedLayoutItems = [
                lj.layoutItems(self).create(item)
                for item in decodedData
                if item.get("type") in self.layoutShapes
            ]
            # A hack to get loading working. Otherwise, when it is saved the top-level items
            # get destroyed.
            undoCommand = us.loadShapesUndo(self, loadedLayoutItems)
            self.undoStack.push(undoCommand)

    def reloadScene(self):
        # Get the top level items from the scene
        topLevelItems = [item for item in self.items() if item.parentItem() is None]
        # Insert a layout item at the beginning of the list
        topLevelItems.insert(0, {"cellView": "layout"})
        # Convert the top level items to JSON string
        # Decode the JSON string back to Python objects
        decodedData = json.loads(json.dumps(topLevelItems, cls=layenc.layoutEncoder))
        # Clear the current scene
        self.clear()
        # Create layout items based on the decoded data
        self.createLayoutItems(decodedData)

    def deleteSelectedItems(self):
        for item in self.selectedItems():
            # if pin is to be deleted, the associated label should be also deleted.
            if isinstance(item, lshp.layoutPin) and item.label is not None:
                undoCommand = us.deleteShapeUndo(self, item.label)
                self.undoStack.push(undoCommand)
        super().deleteSelectedItems()

    def viewObjProperties(self):
        """
        Display the properties of the selected object.
        """
        try:
            if self.selectedItems() is not None:
                for item in self.selectedItems():
                    match type(item):
                        case lshp.layoutRect:
                            self.layoutRectProperties(item)
                        case lshp.layoutPin:
                            self.layoutPinProperties(item)
                        case lshp.layoutLabel:
                            self.layoutLabelProperties(item)
                        case lshp.layoutPath:
                            self.layoutPathProperties(item)
                        case lshp.layoutViaArray:
                            self.layoutViaProperties(item)
                        case lshp.layoutPolygon:
                            self.layoutPolygonProperties(item)
                        case lshp.layoutInstance:
                            self.layoutInstanceProperties(item)
                        case _:
                            if item.__class__.__bases__[0] == pcells.baseCell:
                                self.layoutPCellProperties(item)

        except Exception as e:
            self.logger.error(f"{type(item)} property editor error: {e}")

    def layoutPolygonProperties(self, item):
        pointsTupleList = [self.toLayoutCoord(point) for point in item.points]
        dlg = ldlg.layoutPolygonProperties(self.editorWindow, pointsTupleList)
        dlg.polygonLayerCB.addItems(
            [f"{item.name} [{item.purpose}]" for item in laylyr.pdkAllLayers]
        )
        dlg.polygonLayerCB.setCurrentText(
            f"{item.layer.name} [" f"{item.layer.purpose}]"
        )

        if dlg.exec() == QDialog.Accepted:
            item.layer = laylyr.pdkAllLayers[dlg.polygonLayerCB.currentIndex()]
            tempPoints = []
            for i in range(dlg.tableWidget.rowCount()):
                xcoor = dlg.tableWidget.item(i, 1).text()
                ycoor = dlg.tableWidget.item(i, 2).text()
                if xcoor != "" and ycoor != "":
                    tempPoints.append(
                        self.toSceneCoord(QPointF(float(xcoor), float(ycoor)))
                    )
            item.points = tempPoints

    def layoutRectProperties(self, item):
        dlg = ldlg.layoutRectProperties(self.editorWindow)
        dlg.rectLayerCB.addItems(
            [f"{item.name} [{item.purpose}]" for item in laylyr.pdkAllLayers]
        )
        dlg.rectLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.rectWidthEdit.setText(str(item.width / fabproc.dbu))
        dlg.rectHeightEdit.setText(str(item.height / fabproc.dbu))
        dlg.topLeftEditX.setText(str(item.rect.topLeft().x() / fabproc.dbu))
        dlg.topLeftEditY.setText(str(item.rect.topLeft().y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.layer = laylyr.pdkAllLayers[dlg.rectLayerCB.currentIndex()]
            item.width = float(dlg.rectWidthEdit.text()) * fabproc.dbu
            item.height = float(dlg.rectHeightEdit.text()) * fabproc.dbu

            item.rect = QRectF(
                float(dlg.topLeftEditX.text()) * fabproc.dbu,
                float(dlg.topLeftEditY.text()) * fabproc.dbu,
                float(dlg.rectWidthEdit.text()) * fabproc.dbu,
                float(dlg.rectHeightEdit.text()) * fabproc.dbu,
            )

    def layoutViaProperties(self, item):
        dlg = ldlg.layoutViaProperties(self.editorWindow)
        if item.xnum == 1 and item.ynum == 1:
            dlg.singleViaRB.setChecked(True)
            dlg.singleViaClicked()
            dlg.singleViaNamesCB.setCurrentText(item.via.viaDefTuple.name)
            dlg.singleViaWidthEdit.setText(str(item.width / fabproc.dbu))
            dlg.singleViaHeightEdit.setText(str(item.via.height / fabproc.dbu))
        else:
            dlg.arrayViaRB.setChecked(True)
            dlg.arrayViaClicked()
            dlg.arrayViaNamesCB.setCurrentText(item.via.viaDefTuple.name)
            dlg.arrayViaWidthEdit.setText(str(item.via.width / fabproc.dbu))
            dlg.arrayViaHeightEdit.setText(str(item.via.height / fabproc.dbu))
            dlg.arrayViaSpacingEdit.setText(str(item.spacing / fabproc.dbu))
            dlg.arrayXNumEdit.setText(str(item.xnum))
            dlg.arrayYNumEdit.setText(str(item.ynum))
        dlg.startXEdit.setText(str(item.mapToScene(item.start).x() / fabproc.dbu))
        dlg.startYEdit.setText(str(item.mapToScene(item.start).y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            if dlg.singleViaRB.isChecked():
                item.viaDefTuple = [
                    viaDefT
                    for viaDefT in fabproc.processVias
                    if viaDefT.name == dlg.singleViaNamesCB.currentText()
                ][0]
                item.width = float(dlg.singleViaWidthEdit.text()) * fabproc.dbu
                item.height = float(dlg.singleViaHeightEdit.text()) * fabproc.dbu
                item.start = item.mapFromScene(
                    self.toSceneCoord(
                        QPointF(
                            float(dlg.startXEdit.text()), float(dlg.startYEdit.text())
                        )
                    )
                )
                item.xnum = 1
                item.ynum = 1
                item.spacing = 0.0
            else:
                item.viaDefTuple = [
                    viaDefT
                    for viaDefT in fabproc.processVias
                    if viaDefT.name == dlg.arrayViaNamesCB.currentText()
                ][0]
                item.width = float(dlg.arrayViaWidthEdit.text()) * fabproc.dbu
                item.height = float(dlg.arrayViaHeightEdit.text()) * fabproc.dbu
                item.start = item.mapFromScene(
                    self.toLayoutCoord(
                        QPointF(
                            float(dlg.startXEdit.text()), float(dlg.startYEdit.text())
                        )
                    )
                )
                item.xnum = int(dlg.arrayXNumEdit.text())
                item.ynum = int(dlg.arrayYNumEdit.text())
                item.spacing = float(dlg.arrayViaSpacingEdit.text()) * fabproc.dbu

    def layoutPathProperties(self, item):
        dlg = ldlg.layoutPathPropertiesDialog(self.editorWindow)
        match item.mode:
            case 0:
                dlg.manhattanButton.setChecked(True)
            case 1:
                dlg.diagonalButton.setChecked(True)
            case 2:
                dlg.anyButton.setChecked(True)
            case 3:
                dlg.horizontalButton.setChecked(True)
            case 4:
                dlg.verticalButton.setChecked(True)
        dlg.pathLayerCB.addItems(
            [f"{item.name} [{item.purpose}]" for item in laylyr.pdkDrawingLayers]
        )
        dlg.pathLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.pathWidth.setText(str(item.width / fabproc.dbu))
        dlg.pathNameEdit.setText(item.name)
        roundingFactor = len(str(fabproc.dbu)) - 1
        dlg.startExtendEdit.setText(
            str(round(item.startExtend / fabproc.dbu, roundingFactor))
        )
        dlg.endExtendEdit.setText(
            str(round(item.endExtend / fabproc.dbu, roundingFactor))
        )
        dlg.p1PointEditX.setText(
            str(round(item.draftLine.p1().x() / fabproc.dbu, roundingFactor))
        )
        dlg.p1PointEditY.setText(
            str(round(item.draftLine.p1().y() / fabproc.dbu, roundingFactor))
        )
        dlg.p2PointEditX.setText(
            str(round(item.draftLine.p2().x() / fabproc.dbu, roundingFactor))
        )
        dlg.p2PointEditY.setText(
            str(round(item.draftLine.p2().y() / fabproc.dbu, roundingFactor))
        )
        angle = item.angle
        if dlg.exec() == QDialog.Accepted:
            item.name = dlg.pathNameEdit.text()
            item.layer = laylyr.pdkDrawingLayers[dlg.pathLayerCB.currentIndex()]
            item.width = fabproc.dbu * float(dlg.pathWidth.text())
            item.startExtend = fabproc.dbu * float(dlg.startExtendEdit.text())
            item.endExtend = fabproc.dbu * float(dlg.endExtendEdit.text())
            p1 = self.toSceneCoord(
                QPointF(
                    float(dlg.p1PointEditX.text()),
                    float(dlg.p1PointEditY.text()),
                )
            )
            p2 = self.toSceneCoord(
                QPointF(
                    float(dlg.p2PointEditX.text()),
                    float(dlg.p2PointEditY.text()),
                )
            )
            item.draftLine = QLineF(p1, p2)
            item.angle = angle

    def layoutLabelProperties(self, item):
        dlg = ldlg.layoutLabelProperties(self.editorWindow)
        dlg.labelName.setText(item.labelText)
        dlg.labelLayerCB.addItems(
            [f"{layer.name} [{layer.purpose}]" for layer in laylyr.pdkTextLayers]
        )
        dlg.labelLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.familyCB.setCurrentText(item.fontFamily)
        dlg.fontStyleCB.setCurrentText(item.fontStyle)
        dlg.labelHeightCB.setCurrentText(str(int(item.fontHeight)))
        dlg.labelAlignCB.setCurrentText(item.labelAlign)
        dlg.labelOrientCB.setCurrentText(item.labelOrient)
        dlg.labelTopLeftX.setText(str(item.mapToScene(item.start).x() / fabproc.dbu))
        dlg.labelTopLeftY.setText(str(item.mapToScene(item.start).y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.labelText = dlg.labelName.text()
            item.layer = laylyr.pdkTextLayers[dlg.labelLayerCB.currentIndex()]
            item.fontFamily = dlg.familyCB.currentText()
            item.fontStyle = dlg.fontStyleCB.currentText()
            item.fontHeight = int(float(dlg.labelHeightCB.currentText()))
            item.labelAlign = dlg.labelAlignCB.currentText()
            item.labelOrient = dlg.labelOrientCB.currentText()
            item.start = item.snapToGrid(
                item.mapFromScene(
                    self.toSceneCoord(
                        QPointF(
                            float(dlg.labelTopLeftX.text()),
                            float(dlg.labelTopLeftY.text()),
                        )
                    )
                ),
                self.snapTuple,
            )

    def layoutPinProperties(self, item):
        dlg = ldlg.layoutPinProperties(self.editorWindow)
        dlg.pinName.setText(item.pinName)
        dlg.pinDir.setCurrentText(item.pinDir)
        dlg.pinType.setCurrentText(item.pinType)

        dlg.pinLayerCB.addItems(
            [
                f"{pinLayer.name} [{pinLayer.purpose}]"
                for pinLayer in laylyr.pdkPinLayers
            ]
        )
        dlg.pinLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.pinBottomLeftX.setText(str(item.mapToScene(item.start).x() / fabproc.dbu))
        dlg.pinBottomLeftY.setText(str(item.mapToScene(item.start).y() / fabproc.dbu))
        dlg.pinTopRightX.setText(str(item.mapToScene(item.end).x() / fabproc.dbu))
        dlg.pinTopRightY.setText(str(item.mapToScene(item.end).y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.pinName = dlg.pinName.text()
            item.pinDir = dlg.pinDir.currentText()
            item.pinType = dlg.pinType.currentText()
            item.layer = laylyr.pdkPinLayers[dlg.pinLayerCB.currentIndex()]
            item.label.labelText = dlg.pinName.text()
            item.start = item.snapToGrid(
                item.mapFromScene(
                    self.toSceneCoord(
                        QPointF(
                            float(dlg.pinBottomLeftX.text()),
                            float(dlg.pinBottomLeftY.text()),
                        )
                    )
                ),
                self.snapTuple,
            )
            item.end = item.snapToGrid(
                item.mapFromScene(
                    self.toSceneCoord(
                        QPointF(
                            float(dlg.pinTopRightX.text()),
                            float(dlg.pinTopRightY.text()),
                        )
                    )
                ),
                self.snapTuple,
            )
            item.layer.name = dlg.pinLayerCB.currentText()

    def layoutInstanceProperties(self, item):
        dlg = ldlg.layoutInstancePropertiesDialog(self.editorWindow)
        dlg.instanceLibName.setText(item.libraryName)
        dlg.instanceCellName.setText(item.cellName)
        dlg.instanceViewName.setText(item.viewName)
        dlg.instanceNameEdit.setText(item.instanceName)
        dlg.xEdit.setText(str(item.scenePos().x() / fabproc.dbu))
        dlg.yEdit.setText(str(item.scenePos().y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.libraryName = dlg.instanceLibName.text().strip()
            item.cellName = dlg.instanceCellName.text().strip()
            item.viewName = dlg.instanceViewName.text().strip()
            item.instanceName = dlg.instanceNameEdit.text().strip()
            item.setPos(
                QPoint(
                    self.snapToBase(
                        float(dlg.xEdit.text()) * fabproc.dbu, self.snapTuple[0]
                    ),
                    self.snapToBase(
                        float(dlg.yEdit.text()) * fabproc.dbu, self.snapTuple[1]
                    ),
                )
            )

    def layoutPCellProperties(self, item: lshp.layoutPcell):
        dlg = ldlg.pcellInstancePropertiesDialog(self.editorWindow)
        dlg.pcellLibName.setText(item.libraryName)
        dlg.pcellCellName.setText(item.cellName)
        dlg.pcellViewName.setText(item.viewName)
        dlg.instanceNameEdit.setText(item.instanceName)
        lineEditDict = self.extractPcellInstanceParameters(item)
        for key, value in lineEditDict.items():
            dlg.instanceParamsLayout.addRow(key, value)
        dlg.xEdit.setText(str(item.scenePos().x() / fabproc.dbu))
        dlg.yEdit.setText(str(item.scenePos().y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.libraryName = dlg.pcellLibName.text()
            item.cellName = dlg.pcellCellName.text()
            item.viewName = dlg.pcellViewName.text()
            item.instanceName = dlg.instanceNameEdit.text()
            rowCount = dlg.instanceParamsLayout.rowCount()
            instParamDict = {}
            for row in range(4, rowCount):  # first 4 rows are already processed.
                labelText = (
                    dlg.instanceParamsLayout.itemAt(row, QFormLayout.LabelRole)
                    .widget()
                    .text()
                    .replace("&", "")
                ) 
                paramValue = (
                    dlg.instanceParamsLayout.itemAt(row, QFormLayout.FieldRole)
                    .widget()
                    .text()
                )
                instParamDict[labelText] = paramValue
            item(**instParamDict)

    def extractPcellInstanceParameters(self, instance: lshp.layoutPcell) -> dict:
        initArgs = inspect.signature(instance.__class__.__init__).parameters
        argsUsed = [param for param in initArgs if (param != "self")]
        argDict = {arg: getattr(instance, arg) for arg in argsUsed}
        lineEditDict = {key: edf.shortLineEdit(value) for key, value in argDict.items()}
        return lineEditDict

    def copySelectedItems(self):
        """
        Copy the selected items and create new instances with incremented names.
        """
        for item in self.selectedItems():
            # Create a deep copy of the item using JSON serialization
            itemCopyJson = json.dumps(item, cls=layenc.layoutEncoder)
            itemCopyDict = json.loads(itemCopyJson)
            shape = lj.layoutItems(self).create(itemCopyDict)
            match itemCopyDict["type"]:
                case "Inst" | "Pcell":
                    self.itemCounter += 1
                    shape.instanceName = f"I{self.itemCounter}"
                    shape.counter = self.itemCounter
            self.undoStack.push(us.addShapeUndo(self, shape))
            shape.setPos(
                QPoint(
                    item.pos().x() + 4 * self.snapTuple[0],
                    item.pos().y() + 4 * self.snapTuple[1],
                )
            )

    def moveBySelectedItems(self):
        if self.selectedItems():
            dlg = pdlg.moveByDialogue(self.editorWindow)
            dlg.xEdit.setText("0.0")
            dlg.yEdit.setText("0.0")
            if dlg.exec() == QDialog.Accepted:
                for item in self.selectedItems():
                    item.moveBy(
                        self.snapToBase(
                            float(dlg.xEdit.text()) * fabproc.dbu, self.snapTuple[0]
                        ),
                        self.snapToBase(
                            float(dlg.yEdit.text()) * fabproc.dbu, self.snapTuple[1]
                        ),
                    )
                self.editorWindow.messageLine.setText(
                    f"Moved items by {dlg.xEdit.text()} and {dlg.yEdit.text()}"
                )
                self.editModes.setMode("selectItem")

    def deleteAllRulers(self):
        for ruler in self.rulersSet:
            undoCommand = us.deleteShapeUndo(self, ruler)
            self.undoStack.push(undoCommand)

    def goDownHier(self):
        if self.selectedItems():
            for item in self.selectedItems():
                if isinstance(item, lshp.layoutInstance):
                    dlg = fd.goDownHierDialogue(self.editorWindow)
                    libItem = libm.getLibItem(
                        self.editorWindow.libraryView.libraryModel, item.libraryName
                    )
                    cellItem = libm.getCellItem(libItem, item.cellName)
                    viewNames = [
                        cellItem.child(i).text()
                        for i in range(cellItem.rowCount())
                        # if cellItem.child(i).text() != item.viewName
                        if "layout" in cellItem.child(i).text()
                    ]
                    dlg.viewListCB.addItems(viewNames)
                    if dlg.exec() == QDialog.Accepted:
                        libItem = libm.getLibItem(
                            self.editorWindow.libraryView.libraryModel, item.libraryName
                        )
                        cellItem = libm.getCellItem(libItem, item.cellName)
                        viewItem = libm.getViewItem(
                            cellItem, dlg.viewListCB.currentText()
                        )
                        openViewT = (
                            self.editorWindow.libraryView.libBrowsW.openCellView(
                                viewItem, cellItem, libItem
                            )
                        )
                        if self.editorWindow.appMainW.openViews[openViewT]:
                            childWindow = self.editorWindow.appMainW.openViews[
                                openViewT
                            ]
                            childWindow.parentEditor = self.editorWindow
                            childWindow.layoutToolbar.addAction(childWindow.goUpAction)
                            if dlg.buttonId == 2:
                                childWindow.centralW.scene.readOnly = True

    def stretchPath(self, pathItem: lshp.layoutPath, stretchEnd: str):
        match stretchEnd:
            case "p2":
                self._stretchPath = lshp.layoutPath(
                    QLineF(pathItem.sceneEndPoints[0], pathItem.sceneEndPoints[1]),
                    pathItem.layer,
                    pathItem.width,
                    pathItem.startExtend,
                    pathItem.endExtend,
                    pathItem.mode,
                )
            case "p1":
                self._stretchPath = lshp.layoutPath(
                    QLineF(pathItem.sceneEndPoints[1], pathItem.sceneEndPoints[0]),
                    pathItem.layer,
                    pathItem.width,
                    pathItem.startExtend,
                    pathItem.endExtend,
                    pathItem.mode,
                )
        self._stretchPath.stretch = True
        self._stretchPath.name = pathItem.name

        addDeleteStretchNetCommand = us.addDeleteShapeUndo(
            self, self._stretchPath, pathItem
        )
        self.undoStack.push(addDeleteStretchNetCommand)

    @staticmethod
    def rotateVector(mouseLoc: QPoint, vector: layp.layoutPath, transform: QTransform):
        """
        Rotate the vector based on the mouse location and transform.

        Args:
            mouseLoc (QPoint): The current mouse location.
            vector (layp.layoutPath): The vector to rotate.
            transform (QTransform): The transform to apply to the vector.
        """
        # start = vector.start
        # xmove = mouseLoc.x() - start.x()
        # ymove = mouseLoc.y() - start.y()

    #     # Determine the new end point of the vector based on the mouse movement
    #     if xmove >= 0 and ymove >= 0:
    #         vector.end = QPoint(start.x(), start.y() + ymove)
    #     elif xmove >= 0 and ymove < 0:
    #         vector.end = QPoint(start.x() + xmove, start.y())
    #     elif xmove < 0 and ymove < 0:
    #         vector.end = QPoint(start.x(), start.y() + ymove)
    #     elif xmove < 0 and ymove >= 0:
    #         vector.end = QPoint(start.x() + xmove, start.y())
    #
    #     vector.setTransform(transform)
