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

# schematic editor backend
import pathlib
import shutil
from pathlib import Path

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtGui import (
    QStandardItem,
)
from PySide6.QtWidgets import QMessageBox


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

    def __str__(self):
        return f"library item path: {self.libraryPath}, library item name: {self.libraryName}"

    def __repr__(self):
        return f"{type(self).__name__}({self.libraryPath})"

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
        self.cellPath = cellPath
        self._cellName = cellPath.stem
        super().__init__(self.cellName)
        self.setEditable(False)
        self.setData("cell", Qt.UserRole + 1)
        self.setData(cellPath, Qt.UserRole + 2)

    def type(self):
        return QStandardItem.UserType + 1

    def __str__(self):
        return f"cell item path: {self.cellPath}, \ncell item name: {self.cellName}"

    def __repr__(self):
        return f"{type(self).__name__}({self.cellPath})"

    @property
    def cellName(self):
        return self._cellName


class viewItem(QStandardItem):
    def __init__(self, viewPath: pathlib.Path) -> None:
        self.viewPath = viewPath
        super().__init__(self.viewPath.stem)
        self.setEditable(False)
        self.setData("view", Qt.UserRole + 1)
        # set the data to the item to be the path to the view.
        self.setData(viewPath, Qt.UserRole + 2)

    def type(self):
        return QStandardItem.UserType + 1

    def __str__(self):
        return f"view item path: {self.viewPath}, view item name: {self.viewName}"

    def __repr__(self):
        return f"{type(self).__name__}(pathlib.Path({self.viewPath}))"

    def delete(self):
        """
        delete the view file and remove the row.
        """
        self.viewPath.unlink()
        viewRow = self.row()
        self.parent().removeRow(viewRow)

    @property
    def viewType(self):
        if "schematic" in self.viewPath.stem:
            return "schematic"
        elif "symbol" in self.viewPath.stem:
            return "symbol"
        elif "veriloga" in self.viewPath.stem:
            return "veriloga"
        elif "config" in self.viewPath.stem:
            return "config"
        elif "xyce" in self.viewPath.stem:
            return "xyce"
        elif "spice" in self.viewPath.stem:
            return "spice"
        elif "myhdl" in self.viewPath.stem:
            return "myhdl"
        elif "layout" in self.viewPath.stem:
            return "layout"
        elif "pcell" in self.viewPath.stem:
            return "pcell"
        else:
            return None

    @property
    def viewName(self):
        return str(self.viewPath.stem)


def createLibrary(parent, model, libraryDir, libraryName) -> libraryItem:
    """
    Create a library item with the given parameters and add it to the model.
    If the library name is empty, show a warning message.
    If the library already exists, show a warning message.
    Log the creation of the library item.
    Return the newly created library item.
    """
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
            parent.logger.info(f"Created {libraryPath}")
    return newLibraryItem


def createCell(parent, model, selectedLib, cellName):
    if selectedLib.data(Qt.UserRole + 1) == "library":
        selectedLibPath = selectedLib.data(Qt.UserRole + 2)
        cellPath = selectedLibPath.joinpath(cellName)
        if cellName.strip() == "":
            QMessageBox.warning(parent, "Error", "Please enter a cell name")
            return None
        elif cellPath.exists():
            QMessageBox.warning(
                parent, "Error", "Cell already exits. Delete cell first."
            )
            return None
        else:
            cellPath.mkdir()
            newCellItem = cellItem(cellPath)
            selectedLib.appendRow(newCellItem)
            parent.logger.info(f"Created {cellName} cell at {str(cellPath)}")
            return newCellItem


def createCellView(parent, viewName, cellItem: cellItem):
    """
    Create a cell view with the given view name and cell item.
    If the view name is empty, show a warning message.
    If the view path exists, replace the cell view and show a warning message.
    Create an empty cell view path and append the new view item to the cell item.
    Return the new view item.
    """
    if viewName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a view name")
        return None
    viewPath = cellItem.data(Qt.UserRole + 2).joinpath(f"{viewName}.json")
    if viewPath.exists():
        parent.logger.warning("Replacing the cell view.")
        oldView = [
            cellItem.child(row)
            for row in range(cellItem.rowCount())
            if cellItem.child(row).viewName == viewName
        ][0]
        oldView.delete()
    newViewItem = viewItem(viewPath)
    viewPath.touch()  # create empty cell view path
    items = list()
    if "schematic" in viewName:
        items.insert(0, {"viewName": "schematic"})
        items.insert(1, {"snapGrid": (10, 5)})
    elif "symbol" in viewName:
        items.insert(0, {"viewName": "symbol"})
        items.insert(1, {"snapGrid": (10, 5)})
    elif "layout" in viewName:
        items.insert(0, {"viewName": "layout"})
        items.insert(1, {"snapGrid": (10, 5)})
    elif "pcell" in viewName:
        items.insert(0, {"viewName": "pcell"})
    elif "spice" in viewName:
        items.insert(0, {"viewName": "spice"})
    elif "veriloga" in viewName:
        items.insert(0, {"viewName": "veriloga"})
    elif "config" in viewName:
        items.insert(0, {"viewName": "config"})
    with viewPath.open(mode="w") as f:
        json.dump(items, f, indent=4)
    parent.logger.warning(f"Created {viewName} at {str(viewPath)}")
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
    cellPath = origCellItem.data(
        Qt.UserRole + 2
    )  # get the cell path from item user data
    if copyName == "":  # assign a default name for the cell
        copyName = "newCell"
    copyPath = selectedLibPath.joinpath(copyName)
    if copyPath.exists():
        QMessageBox.warning(parent, "Error", "Cell already exits.")
        return False
    else:
        assert cellPath.exists()
        shutil.copytree(cellPath, copyPath)  # copied the cell
        libraryItem = model.findItems(selectedLibPath.name, flags=Qt.MatchExactly)[
            0
        ]  # find the library item
        # create new cell item
        newCellItem = cellItem(copyPath)
        newCellItem.setEditable(False)
        newCellItem.setData("cell", Qt.UserRole + 1)
        newCellItem.setData(copyPath, Qt.UserRole + 2)
        # go through view list and add to cell item
        addedViewList = [
            viewItem(viewPath)
            for viewPath in copyPath.iterdir()
            if viewPath.suffix == ".json"
        ]
        [addedView.setEditable(False) for addedView in addedViewList]

        newCellItem.appendRows(addedViewList)
        # add the new cell item to the library item
        libraryItem.appendRow(newCellItem)
        return True


def renameCell(parent, oldCell, newName) -> bool:
    """
    Function to rename a cell in the parent with a new name.
    Parameters:
    - parent: the parent of the cell
    - oldCell: the cell to be renamed
    - newName: the new name for the cell
    Returns:
    - bool: True if the cell is successfully renamed, False otherwise
    """
    cellPath = oldCell.data(Qt.UserRole + 2)
    if newName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a cell name")
        return False
    else:
        cellPath.rename(cellPath.parent / newName)
        oldCell.setText(newName)
        return True
