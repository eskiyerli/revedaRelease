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

import os
from typing import List, Sequence

# import numpy as np
from PySide6.QtCore import (QEvent, QPoint, QRectF, Qt, Signal)
from PySide6.QtGui import (QGuiApplication, QColor, QPen, QPainterPath, )
from PySide6.QtWidgets import (QGraphicsRectItem, QGraphicsScene, QMenu, QGraphicsItem,
                               QDialog,
                               QCompleter)
from dotenv import load_dotenv

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.undoStack as us
import revedaEditor.gui.propertyDialogues as pdlg

load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):
    pass
else:
    pass


class editorScene(QGraphicsScene):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.editorWindow = self.parent.parent
        self.majorGrid = self.editorWindow.majorGrid
        self.snapTuple = self.editorWindow.snapTuple
        self._snapDistance = int(self.majorGrid * 0.5)
        self.mousePressLoc = None
        self.mouseMoveLoc = None
        self.mouseReleaseLoc = None
        # common edit modes
        self.editModes = ddef.editModes(selectItem=True, deleteItem=False, moveItem=False,
                                        copyItem=False, rotateItem=False,
                                        changeOrigin=False,
                                        panView=False, stretchItem=False, )
        self.readOnly = False  # if the scene is not editable
        self.undoStack = us.undoStack()
        self.undoStack.setUndoLimit(99)
        self.origin = QPoint(0, 0)
        self.cellName = self.editorWindow.file.parent.stem
        self.partialSelection = True
        self._selectionRectItem = None
        self._items = []
        self._itemsOffset = []
        self.libraryDict = self.editorWindow.libraryDict
        self.itemContextMenu = QMenu()
        self.appMainW = self.editorWindow.appMainW
        self.logger = self.appMainW.logger
        self.messageLine = self.editorWindow.messageLine
        self.statusLine = self.editorWindow.statusLine
        self.installEventFilter(self)
        self.setMinimumRenderSize(2)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.mousePressLoc = event.scenePos().toPoint()
            self._items = [item for item in self.selectedItems() if
                           item.parentItem() is None]
            if self.editModes.selectItem:
                if not self.selectedItems():
                    # Start a new selection rectangle
                    self._startNewSelectionRectangle()
            elif self.editModes.moveItem:
                self._itemsOffset = [item.scenePos().toPoint() - self.mousePressLoc for item
                                     in
                                     self._items]
            elif self.editModes.panView:
                self.centerViewOnPoint(self.mousePressLoc)
                self.messageLine.setText("Pan View at mouse press position")

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouseReleaseLoc = event.scenePos().toPoint()
            modifiers = QGuiApplication.keyboardModifiers()

            if self.editModes.moveItem and self._items:
                if self.mouseReleaseLoc != self.mousePressLoc:
                    self.moveShapesUndoStack(self._items, self._itemsOffset,
                                             self.mousePressLoc,
                                             self.mouseReleaseLoc)
            elif self.editModes.selectItem:
                self._handleSelection(modifiers)

            self._cleanupAfterMouseRelease(modifiers)

    def _handleSelection(self, modifiers):
        if modifiers == Qt.KeyboardModifier.ShiftModifier:
            self._handleShiftSelection()
        elif modifiers == Qt.KeyboardModifier.ControlModifier:
            self._handleControlSelection()
        elif modifiers == Qt.KeyboardModifier.AltModifier:
            self._handleAltSelection()
        else:
            self._handleDefaultSelection()

    def _cleanupAfterMouseRelease(self, modifiers):
        if self._selectionRectItem and modifiers != Qt.KeyboardModifier.ShiftModifier:
            self.removeItem(self._selectionRectItem)
            self._selectionRectItem = None

        self._items = self.selectedItems()
        self.messageLine.setText("Item selected" if self._items else "Nothing selected")

    def _handleShiftSelection(self):
        if self._selectionRectItem:
            self._processExistingSelectionRectangle()
        else:
            self._startNewSelectionRectangle()

    def _processExistingSelectionRectangle(self):
        selectionMode = Qt.ItemSelectionMode.IntersectsItemShape if self.partialSelection else Qt.ItemSelectionMode.ContainsItemShape
        selectionPath = QPainterPath()
        selectionPath.addRect(self._selectionRectItem.sceneBoundingRect())
        self.setSelectionArea(selectionPath, mode=selectionMode)

        self.removeItem(self._selectionRectItem)
        self._selectionRectItem = None
        self.messageLine.setText("Selection complete")

    def _startNewSelectionRectangle(self):
        self._selectionRectItem = QGraphicsRectItem(
            QRectF(self.mousePressLoc, self.mousePressLoc))
        selectionRectPen = QPen(QColor("yellow"), 2, Qt.PenStyle.DashLine)
        selectionRectPen.setCosmetic(True)
        self._selectionRectItem.setPen(selectionRectPen)
        self.addItem(self._selectionRectItem)

    def _updateSelectionRectangle(self, currentPos):
        if self._selectionRectItem:
            rect = QRectF(self.mousePressLoc, currentPos).normalized()
            self._selectionRectItem.setRect(rect)

    def _handleControlSelection(self):
        for item in self._getClickedItems():
            item.setSelected(not item.isSelected())

    def _handleAltSelection(self):
        self.clearSelection()
        clicked_items = self._getClickedItems()
        if clicked_items:
            clicked_items[0].setSelected(True)

    def _handleDefaultSelection(self):
        self.clearSelection()
        for item in self._getClickedItems():
            item.setSelected(True)

    def _getClickedItems(self):
        return [item for item in self.items(self.mouseReleaseLoc) if
                item.parentItem() is None]

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if event.buttons() == Qt.MouseButton.LeftButton:
            currentPos = event.scenePos().toPoint()
            if self.editModes.moveItem and self._items:
                for item, offset in zip(self._items, self._itemsOffset):
                    item.setPos(currentPos + offset)
            elif self.editModes.selectItem and self._selectionRectItem:
                self._updateSelectionRectangle(currentPos)

    def snapToBase(self, number, base):
        """
        Restrict a number to the multiples of base
        """
        return int(round(number / base)) * base

    def snapToGrid(self, point: QPoint, snapTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(self.snapToBase(point.x(), snapTuple[0]),
                      self.snapToBase(point.y(), snapTuple[1]), )

    def rotateSelectedItems(self, point: QPoint):
        """
        Rotate selected items by 90 degree.
        """
        for item in self.selectedItems():
            self.rotateAnItem(point, item, 90)
        self.editModes.setMode("selectItem")

    def rotateAnItem(self, point: QPoint, item: QGraphicsItem, angle: int):
        undoCommand = us.undoRotateShape(self, item, point, angle)
        self.undoStack.push(undoCommand)

    def eventFilter(self, source, event):
        """
        Mouse events should snap to background grid points.
        """
        if self.readOnly:  # if read only do not propagate any mouse events
            return True
        elif event.type() in [QEvent.GraphicsSceneMouseMove, QEvent.GraphicsSceneMousePress,
                              QEvent.GraphicsSceneMouseRelease, ]:
            event.setScenePos(self.snapToGrid(event.scenePos(), self.snapTuple).toPointF())
            return False
        else:
            return super().eventFilter(source, event)

    def copySelectedItems(self):
        pass

    def flipHorizontal(self):
        for item in self.selectedItems():
            item.flipTuple = (-1, 1)

    def flipVertical(self):
        for item in self.selectedItems():
            item.flipTuple = (1, -1)

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
        newSceneRect = QRectF(currentSceneRect.left() - halfWidth, currentSceneRect.top(),
                              currentSceneRect.width(), currentSceneRect.height(), )
        self.setSceneRect(newSceneRect)

    def moveSceneRight(self) -> None:
        currentSceneRect = self.sceneRect()
        halfWidth = currentSceneRect.width() / 2.0
        newSceneRect = QRectF(currentSceneRect.left() + halfWidth, currentSceneRect.top(),
                              currentSceneRect.width(), currentSceneRect.height(), )
        self.setSceneRect(newSceneRect)

    def moveSceneUp(self) -> None:
        currentSceneRect = self.sceneRect()
        halfWidth = currentSceneRect.width() / 2.0
        newSceneRect = QRectF(currentSceneRect.left(), currentSceneRect.top() - halfWidth,
                              currentSceneRect.width(), currentSceneRect.height(), )
        self.setSceneRect(newSceneRect)

    def moveSceneDown(self) -> None:
        currentSceneRect = self.sceneRect()
        halfWidth = currentSceneRect.width() / 2.0
        newSceneRect = QRectF(currentSceneRect.left(), currentSceneRect.top() + halfWidth,
                              currentSceneRect.width(), currentSceneRect.height(), )
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

    def addListUndoStack(self, itemList: List) -> None:
        undoCommand = us.addShapesUndo(self, itemList)
        self.undoStack.push(undoCommand)

    def moveShapesUndoStack(self, items: Sequence[QGraphicsItem],
                            itemsOffsetList: Sequence[QPoint], start: QPoint,
                            end: QPoint) -> None:
        undoCommand = us.undoMoveShapesCommand(items, itemsOffsetList, start, end)
        self.undoStack.push(undoCommand)

    def addUndoMacroStack(self, undoCommands: list, macroName: str = "Macro"):
        self.undoStack.beginMacro(macroName)
        for command in undoCommands:
            self.undoStack.push(command)
        self.undoStack.endMacro()

    def moveBySelectedItems(self):
        if self.selectedItems():
            dlg = pdlg.moveByDialogue(self.editorWindow)
            dlg.xEdit.setText("0")
            dlg.yEdit.setText("0")
            if dlg.exec() == QDialog.Accepted:
                dx = self.snapToBase(float(dlg.xEdit.text()), self.snapTuple[0])
                dy = self.snapToBase(float(dlg.yEdit.text()), self.snapTuple[1])
                moveCommand = us.undoMoveByCommand(self, self.selectedItems(), dx, dy)
                self.undoStack.push(moveCommand)
                self.editorWindow.messageLine.setText(
                    f"Moved items by {dlg.xEdit.text()} and {dlg.yEdit.text()}")
                self.editModes.setMode("selectItem")

    def cellNameComplete(self, dlg: QDialog, cellNameList: List[str]):
        cellNameCompleter = QCompleter(cellNameList)
        cellNameCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        dlg.instanceCellName.setCompleter(cellNameCompleter)

    def viewNameComplete(self, dlg: QDialog, viewNameList: List[str]):
        viewNameCompleter = QCompleter(viewNameList)
        viewNameCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        dlg.instanceViewName.setCompleter(viewNameCompleter)
        dlg.instanceViewName.setText(viewNameList[0])
