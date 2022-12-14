
#   “Commons Clause” License Condition v1.0
#  #
#   The Software is provided to you by the Licensor under the License, as defined
#   below, subject to the following condition.
#  #
#   Without limiting other conditions in the License, the grant of rights under the
#   License will not include, and the License does not grant to you, the right to
#   Sell the Software.
#  #
#   For purposes of the foregoing, “Sell” means practicing any or all of the rights
#   granted to you under the License to provide to third parties, for a fee or other
#   consideration (including without limitation fees for hosting or consulting/
#   support services related to the Software), a product or service whose value
#   derives, entirely or substantially, from the functionality of the Software. Any
#   license notice or attribution required by the License must also include this
#   Commons Clause License Condition notice.
#  #
#   Software: Revolution EDA
#   License: Mozilla Public License 2.0
#   Licensor: Revolution Semiconductor (Registered in the Netherlands)

import json

import fileio.loadJSON as lj
import fileio.symbolEncoder as se
from PySide6.QtGui import (QUndoCommand)


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
        self.scene.removeItem(self.shape)

    def redo(self):
        self.scene.addItem(self.shape)


class undoRotateShape(QUndoCommand):
    def __init__(self,scene,shape, angle, parent=None):
        super().__init__()
        self.scene = scene
        self.shape = shape
        self.angle = angle
        self.setText("Undo Shape rotation")

    def undo(self) -> None:
        self.shape.setRotation(self.angle-90)

    def redo(self) -> None:
        # self.angle += 90
        self.shape.setRotation(self.angle)