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

from typing import List, Sequence
from PySide6.QtCore import (QEvent, QPoint, QRectF, Qt)
from PySide6.QtGui import (QGuiApplication)
from PySide6.QtWidgets import (QQGraphicsScene, QMenu, QGraphicsItem,
                               QDialog,
                               QCompleter)
from contextlib import contextmanager
import time
import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.undoStack as us
import revedaEditor.gui.propertyDialogues as pdlg


class editorScene(QGraphicsScene):
    # Class-level constants for quick access
    DEFAULT_GRID = (10, 10)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.editorWindow = self.parent.parent
        self.majorGrid = self.editorWindow.majorGrid
        self.snapTuple = self.editorWindow.snapTuple
        self._snapDistance = int(self.majorGrid * 0.5)
        self.snapGrid = None
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
        self.partialSelection = False
        self._selectionRectItem = None
        self._selectedItems = []
        self._selectedItemGroup = None
        self._groupItems = []
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
        modifiers = QGuiApplication.keyboardModifiers()
        if event.button() == Qt.MouseButton.LeftButton:
            self.mousePressLoc = event.scenePos().toPoint()
            selectedItems = self.selectedItems()
            if self.editModes.moveItem and selectedItems:
                self._selectedItemGroup = self.createItemGroup(selectedItems)
                self._selectedItemGroup.setFlag(QGraphicsItem.ItemIsMovable)
                self.messageLine.setText("Move Item(s)")
            elif self.editModes.panView:
                self.centerViewOnPoint(self.mousePressLoc)
                self.messageLine.setText("Pan View at mouse press position")

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouseReleaseLoc = event.scenePos().toPoint()
            # modifiers = QGuiApplication.keyboardModifiers()
            if self.editModes.moveItem and self._selectedItemGroup:
                self._groupItems = self._selectedItemGroup.childItems()
                self.destroyItemGroup(self._selectedItemGroup)
                self._selectedItemGroup = None


    def snapToBase(self, number, base):
        """
        Restrict a number to the multiples of base
        """
        return int(round(float(number) / base)) * base

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
        """
        Rotate a graphics item around a point by a specified angle with undo support.

        Args:
            point (QPoint): The pivot point for rotation
            item (QGraphicsItem): The item to be rotated
            angle (int): The rotation angle in degrees

        Returns:
            None
        """
        undoCommand = us.undoRotateShape(self, item, point, angle)
        self.undoStack.push(undoCommand)

    def eventFilter(self, source, event):
        """
        Filter mouse events to snap them to background grid points.

        Args:
            source: The object that triggered the event
            event: The event to be filtered

        Returns:
            bool: True if event should be filtered out, False if it should be processed
        """
        if self.readOnly:
            return True

        MOUSE_EVENTS = {
            QEvent.GraphicsSceneMouseMove,
            QEvent.GraphicsSceneMousePress,
            QEvent.GraphicsSceneMouseRelease
        }

        if event.type() in MOUSE_EVENTS:
            snappedPos = self.snapToGrid(event.scenePos(), self.snapTuple)
            event.setScenePos(snappedPos.toPointF())
            return False

        return super().eventFilter(source, event)

    def copySelectedItems(self):
        '''
        Will be implemented in the subclasses.
        '''

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


    def reloadScene(self):
        # Disable updates temporarily for better performance
        for view in self.views():
            view.setUpdatesEnabled(False)

        try:
            # Block signals during reload to prevent unnecessary updates
            self.blockSignals(True)

            # Clear existing items
            self.clear()

            # Reload layout
            self.loadDesign(self.editorWindow.file)

            # Optional: Update scene rect to fit content
            self.setSceneRect(self.itemsBoundingRect())

        finally:
            # Re-enable updates and signals
            self.blockSignals(False)
            for view in self.views():
                view.setUpdatesEnabled(True)
                view.viewport().update()

    def loadDesign(self, file):
        """
        implement in subclasses
        """
        pass


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
                         start: QPoint,
                            end: QPoint) -> None:
        undoCommand = us.undoMoveShapesCommand(items,  start, end)
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

    @contextmanager
    def measureDuration(self):
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            self.logger.info(f"Total processing time: {end_time - start_time:.3f} seconds")
