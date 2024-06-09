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


from PySide6.QtCore import QPoint
from PySide6.QtGui import QUndoCommand, QUndoStack
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem


class undoStack(QUndoStack):
    def __init__(self):
        super().__init__()

    def removeLastCommand(self):
        # Remove the last command without undoing it
        if self.canUndo():
            self.setIndex(self.index() - 1)


class addShapeUndo(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, shape: QGraphicsItem):
        super().__init__()
        self._scene = scene
        self._shape = shape
        self.setText("Draw Shape")

    def undo(self):
        self._scene.removeItem(self._shape)

    def redo(self):
        self._scene.addItem(self._shape)


class addShapesUndo(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, shapes: list[QGraphicsItem]):
        super().__init__()
        self._scene = scene
        self._shapes = shapes
        self.setText("Add Shapes")

    def undo(self):
        [self._scene.removeItem(item) for item in self._shapes]

    def redo(self):
        [self._scene.addItem(item) for item in self._shapes]


class loadShapesUndo(addShapesUndo):
    """
    A hack to load the file but disallow the undo
    """

    def __init__(self, scene: QGraphicsScene, shapes: list[QGraphicsItem]):
        super().__init__(scene, shapes)

    def undo(self):
        pass


class deleteShapeUndo(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, shape: QGraphicsItem):
        super().__init__()
        self._scene = scene
        self._shape = shape
        self.setText("Delete Shape")

    def undo(self):
        self._scene.addItem(self._shape)

    def redo(self):
        self._scene.removeItem(self._shape)

class deleteShapesUndo(QUndoCommand):
    def __init__(self, scene: QGraphicsScene, shapes: list[QGraphicsItem]):
        super().__init__()
        self._scene = scene
        self._shapes = shapes
        self.setText("Delete Shapes")

    def undo(self):
        [self._scene.addItem(item) for item in self._shapes]

    def redo(self):
        [self._scene.removeItem(item) for item in self._shapes]

class addDeleteShapeUndo(QUndoCommand):
    def __init__(
        self, scene: QGraphicsScene, addShape: QGraphicsItem, deleteShape: QGraphicsItem
    ):
        super().__init__()
        self._scene = scene
        self._addshape = addShape
        self._deleteShape = deleteShape
        self.setText("Add/Delete Shape")

    def undo(self):
        self._scene.removeItem(self._addshape)
        self._scene.addItem(self._deleteShape)

    def redo(self):
        self._scene.addItem(self._addshape)
        self._scene.removeItem(self._deleteShape)


class updateSymUndo(QUndoCommand):
    def __init__(self, item: QGraphicsItem, oldItemList: list, newItemList: list):
        super().__init__()
        self._item = item
        self._oldItemList = oldItemList
        self._newItemList = newItemList

    def undo(self):
        pass

    def redo(self):
        pass


class updateSymRectUndo(updateSymUndo):
    def __init__(self, item: QGraphicsItem, oldItemList: list, newItemList: list):
        super().__init__(item, oldItemList, newItemList)

    def undo(self):
        self._item.prepareGeometryChange()
        self._item.rect.setRect(*self._oldItemList)

    def redo(self):
        self._item.prepareGeometryChange()
        self._item.rect.setRect(*self._newItemList)


class updateSymCircleUndo(updateSymUndo):
    def __init__(self, item: QGraphicsItem, oldItemList: list, newItemList: list):
        super().__init__(item, oldItemList, newItemList)

    def undo(self):
        self._item.centre = QPoint(self._oldItemList[0], self._oldItemList[1])
        self._item.radius = self._oldItemList[2]

    def redo(self):
        self._item.centre = QPoint(self._newItemList[0], self._newItemList[1])
        self._item.radius = self._newItemList[2]


class updateSymArcUndo(updateSymUndo):
    def __init__(self, item: QGraphicsItem, oldItemList: list, newItemList: list):
        super().__init__(item, oldItemList, newItemList)

    def undo(self):
        self._item.start = QPoint(self._oldItemList[0], self._oldItemList[1])
        self._item.width = self._oldItemList[2]
        self._item.height = self._oldItemList[3]

    def redo(self):
        self._item.start = QPoint(self._newItemList[0], self._newItemList[1])
        self._item.width = self._newItemList[2]
        self._item.height = self._newItemList[3]


class updateSymLineUndo(updateSymUndo):
    def __init__(self, item: QGraphicsItem, oldItemList: list, newItemList: list):
        super().__init__(item, oldItemList, newItemList)

    def undo(self):
        self._item.start = QPoint(self._oldItemList[0], self._oldItemList[1])
        self._item.end = QPoint(self._oldItemList[2], self._oldItemList[3])

    def redo(self):
        self._item.start = QPoint(self._newItemList[0], self._newItemList[1])
        self._item.end = QPoint(self._newItemList[2], self._newItemList[3])


class updateSymPinUndo(updateSymUndo):
    def __init__(self, item: QGraphicsItem, oldItemList: list, newItemList: list):
        super().__init__(item, oldItemList, newItemList)

    def undo(self):
        self._item.start = QPoint(self._oldItemList[0], self._oldItemList[1])
        self._item.pinName = self._oldItemList[2]
        self._item.pinType = self._oldItemList[3]
        self._item.pinDir = self._oldItemList[4]

    def redo(self):
        self._item.pinName = self._newItemList[2]
        self._item.pinType = self._newItemList[3]
        self._item.pinDir = self._newItemList[4]
        self._item.start = QPoint(self._newItemList[0], self._newItemList[1])


class updateSymLabelUndo(updateSymUndo):
    def __init__(self, item: QGraphicsItem, oldItemList: list, newItemList: list):
        super().__init__(item, oldItemList, newItemList)

    def undo(self):
        self._item.start = QPoint(self._oldItemList[0], self._oldItemList[1])
        self._item.labelDefinition = self._oldItemList[2]
        self._item.labelType = self._oldItemList[3]
        self._item.labelHeight = self._oldItemList[4]
        self._item.labelAlign = self._oldItemList[5]
        self._item.labelOrient = self._oldItemList[6]
        self._item.labelUse = self._oldItemList[7]
        self._item.labelVisible = self._oldItemList[8]
        self._item.labelDefs()

    def redo(self):
        self._item.start = QPoint(self._newItemList[0], self._newItemList[1])
        self._item.labelDefinition = self._newItemList[2]
        self._item.labelType = self._newItemList[3]
        self._item.labelHeight = self._newItemList[4]
        self._item.labelAlign = self._newItemList[5]
        self._item.labelOrient = self._newItemList[6]
        self._item.labelUse = self._newItemList[7]
        self._item.labelVisible = self._newItemList[8]
        self._item.labelDefs()


class moveShapeUndo(QUndoCommand):
    def __init__(
        self,
        scene,
        item: QGraphicsItem,
        attribute: str,
        oldPosition: QPoint,
        newPosition: QPoint,
    ):
        self._scene = scene
        self._item = item
        self._attribute = attribute
        self._oldPosition = oldPosition
        self._newPosition = newPosition

    def undo(self):
        setattr(self._item, self._attribute, self._oldPosition)

    def redo(self):
        setattr(self._item, self._attribute, self._newPosition)


class undoRotateShape(QUndoCommand):
    def __init__(self, scene, shape, angle, parent=None):
        super().__init__()
        self._scene = scene
        self._shape = shape
        self._angle = angle
        self.setText("Undo Shape rotation")

    def undo(self) -> None:
        self._shape.setRotation(self._angle - 90)

    def redo(self) -> None:
        # self.angle += 90
        self._shape.setRotation(self._angle)


class undoMoveShapesCommand(QUndoCommand):
    def __init__(self, shapes: list[QGraphicsItem], shapesOffsetList: list[int], startPos, endPos):
        super().__init__()
        self._shapes = shapes
        self._shapesOffsetList = shapesOffsetList
        self._startPos = startPos
        self._endPos = endPos


    def undo(self):
        for index, item in enumerate(self._shapes):
            item.setPos(self._startPos + self._shapesOffsetList[index])

    def redo(self):
        for index, item in enumerate(self._shapes):
            item.setPos(self._endPos + self._shapesOffsetList[index])