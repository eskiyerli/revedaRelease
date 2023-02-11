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

# schematic editor backend
import pathlib
import shutil
from pathlib import Path

from PySide6.QtCore import (Qt, )
from PySide6.QtGui import (QStandardItem, )
from PySide6.QtWidgets import (QMessageBox, QGroupBox, QVBoxLayout, QDialog,
                               QDialogButtonBox, QFormLayout)
# from ruamel.yaml import YAML
import json
import fileio.symbolEncoder as se
import gui.editFunctions as edf


class libraryItem(QStandardItem):
    def __init__(self, libraryPath: pathlib.Path):  # path is a pathlib.Path object
        self._libraryPath = libraryPath
        self._libraryName = libraryPath.name
        super().__init__(self.libraryName)
        self.setEditable(False)
        self.setData(libraryPath, Qt.UserRole + 2)
        self.setData("library", Qt.UserRole + 1)

    def type(self):
        return Qt.StandardItem.UserType

    @property
    def libraryPath(self):
        return self._libraryPath

    @libraryPath.setter
    def libraryPath(self, value):
        if isinstance(value, pathlib.Path):
            self._libraryPath = value

    @property
    def libraryName(self):
        return self._libraryName


class cellItem(QStandardItem):
    def __init__(self, cellPath: pathlib.Path) -> None:
        self._cellName = cellPath.stem
        # self._libName = self.parent.libraryName
        super().__init__(self.cellName)
        self.setEditable(False)
        self.setData("cell", Qt.UserRole + 1)
        self.setData(cellPath, Qt.UserRole + 2)

    def type(self):
        return QStandardItem.UserType + 1

    @property
    def cellName(self):
        return self._cellName


class viewItem(QStandardItem):
    def __init__(self, viewPath: pathlib.Path) -> None:
        self.viewPath = viewPath
        super().__init__(self.viewPath.stem)
        self.setEditable(False)
        self.setData('view', Qt.UserRole + 1)
        # set the data to the item to be the path to the view.
        self.setData(viewPath, Qt.UserRole + 2)

    def type(self):
        return QStandardItem.UserType + 1

    def delete(self):
        '''
        delete the view file and remove the row.
        '''
        self.viewPath.unlink()
        viewRow = self.row()
        parent = self.parent()
        parent.removeRow(viewRow)

    @property
    def viewType(self):
        if 'schematic' in self.viewPath.stem:
            return 'schematic'
        elif 'symbol' in self.viewPath.stem:
            return 'symbol'
        elif 'veriloga' in self.viewPath.stem:
            return 'veriloga'
        elif 'config' in self.viewPath.stem:
            return 'config'
        elif 'xyce' in self.viewPath.stem:
            return 'xyce'
        elif 'spice' in self.viewPath.stem:
            return 'spice'
        else:
            return None

    @property
    def viewName(self):
        return self.viewPath.stem


def createLibrary(parent, model, libraryDir, libraryName) -> libraryItem:
    if libraryName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a library name")
    else:
        libraryPath = Path(libraryDir).joinpath(libraryName)
        if libraryPath.exists():
            QMessageBox.warning(parent, "Error", "Library already exits.")
        else:
            libraryPath.mkdir()
            newLibraryItem = libraryItem(libraryPath)
            newLibraryItem.setData(libraryPath, Qt.UserRole + 2)
            newLibraryItem.setData("library", Qt.UserRole + 1)
            model.appendRow(newLibraryItem)
            print(f"Created {libraryPath}")
    return newLibraryItem


def createCell(parent, model, selectedLib, cellName) -> cellItem:
    # assert isinstance(selectedLib, libraryItem)
    if selectedLib.data(Qt.UserRole + 1) == "library":
        selectedLibPath = selectedLib.data(Qt.UserRole + 2)
        cellPath = selectedLibPath.joinpath(cellName)
        if cellName.strip() == "":
            QMessageBox.warning(parent, "Error", "Please enter a cell name")
            return None
        elif cellPath.exists():
            QMessageBox.warning(parent, "Error", "Cell already exits. Delete cell first.")
            return None
        else:
            cellPath.mkdir()
            # parentLibrary = model.findItems(selectedLibPath.stem,
            #                                 flags=Qt.MatchExactly)[0]
            newCellItem = cellItem(cellPath)
            selectedLib.appendRow(newCellItem)
            parent.logger.warning(f"Created {cellName} cell at {str(cellPath)}")
            return newCellItem


def createCellView(parent, viewName, cellItem: cellItem) -> viewItem:
    if viewName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a view name")
        return None
    viewPath = cellItem.data(Qt.UserRole + 2).joinpath(f'{viewName}.json')
    if viewPath.exists():
        parent.logger.warning('Replacing the cell view.')
        oldView = [cellItem.child(row) for row in range(cellItem.rowCount()) if
                   cellItem.child(row).viewName == viewName][0]
        oldView.delete()
    newViewItem = viewItem(viewPath)
    viewPath.touch()  # create empty cell view
    items = list()
    if 'schematic' in viewName:
        items.insert(0, {'viewName': 'schematic'})
    elif 'symbol' in viewName:
        items.insert(0, {'viewName': 'symbol'})
    elif 'veriloga' in viewName:
        items.insert(0, {'viewName': 'veriloga'})
    elif 'config' in viewName:
        items.insert(0, {'viewName': 'config'})
    with viewPath.open(mode='w') as f:
        json.dump(items, f, indent=4)
    parent.logger.warning(f'Created {viewName} at {str(viewPath)}')
    cellItem.appendRow(newViewItem)

    return newViewItem


# function for copying a cell
def copyCell(parent, model, origCellItem: cellItem, copyName, selectedLibPath) -> bool:
    """
    parent: the parent widget
    model: the model
    cellItem: the cell item in the model
    copyName: the name of the new cell
    selectedLibPath: the path of the selected library
    """
    cellPath = origCellItem.data(Qt.UserRole + 2)  # get the cell path from item user data
    if copyName == "":  # assign a default name for the cell
        copyName = "newCell"
    copyPath = selectedLibPath.joinpath(copyName)
    if copyPath.exists():
        QMessageBox.warning(parent, "Error", "Cell already exits.")
        return False
    else:
        assert cellPath.exists()
        shutil.copytree(cellPath, copyPath)  # copied the cell
        libraryItem = model.findItems(selectedLibPath.cellName, flags=Qt.MatchExactly)[
            0]  # find the library item
        # create new cell item
        newCellItem = cellItem(copyPath.cellName)
        newCellItem.setEditable(False)
        newCellItem.setData("cell", Qt.UserRole + 1)
        newCellItem.setData(copyPath, Qt.UserRole + 2)
        # go through view list and add to cell item
        viewList = [str(view.stem) for view in copyPath.iterdir() if
                    view.suffix == ".json"]

        for view in viewList:
            addedView = viewItem(copyPath.joinpath(view).with_suffix(".json"))
            addedView.setData("view", Qt.UserRole + 1)
            # set the data to the item to be the path to the view.
            addedView.setData(copyPath.joinpath(view).with_suffix(".json"),
                              Qt.UserRole + 2, )
            addedView.setEditable(False)
            cellItem.appendRow(addedView)
        libraryItem.appendRow(cellItem)
        return True


def renameCell(parent, oldCell, newName) -> bool:
    cellPath = oldCell.data(Qt.UserRole + 2)
    if newName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a cell name")
        return False
    else:
        cellPath.rename(cellPath.parent / newName)
        oldCell.setText(newName)
        return True
