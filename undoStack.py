import json
from PySide6.QtGui import (QUndoCommand)
import loadJSON as lj
import symbolEncoder as se


class addShapeUndo(QUndoCommand):
    def __init__(self, scene, shape):
        super().__init__()
        self.scene = scene
        self.shape = shape
        self.setText("Draw Shape")

    def undo(self):
        self.scene.removeItem(self.shape)

    def redo(self):
        self.scene.addItem(self.shape)

class updateShapeUndo(QUndoCommand):
    def __init__(self):
        super().__init__()
        self.setText("Move Shape")

class keepOriginalShape(QUndoCommand):
    def __init__(self,scene,shape,gridTuple,parent=None):
        super().__init__(parent=parent)
        self.scene = scene
        self.gridTuple = gridTuple
        self.setText("Keep Original Shape")
        # recreate the original shape as Qt cannot create deepcopy of an item.
        dump=json.dumps(shape,cls=se.symbolEncoder, indent=4)
        item = json.loads(dump)
        self.originalShape = lj.createSymbolItems(item, self.gridTuple)

    def undo(self):
        print(self.originalShape)
        self.scene.addItem(self.originalShape)

    def redo(self):
        self.scene.removeItem(self.originalShape)

class changeOriginalShape(QUndoCommand):
    def __init__(self,scene,shape,parent=None):
        super().__init__(parent=parent)
        self.scene = scene
        self.shape = shape
        self.setText("Change Original Shape")

    def undo(self):
        print(self.shape)
        self.scene.removeItem(self.shape)

    def redo(self):
        self.scene.addItem(self.shape)