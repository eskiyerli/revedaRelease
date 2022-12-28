
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
from PySide6.QtWidgets import (QMessageBox, )
# from ruamel.yaml import YAML
import json
import fileio.symbolEncoder as se


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
        self.setData(viewPath, Qt.UserRole + 2 )

    def type(self):
        return QStandardItem.UserType + 1

    @property
    def viewType(self):
        if 'schematic' in self.viewPath.stem:
            return 'schematic'
        elif 'symbol' in self.viewPath.stem:
            return 'symbol'
        elif 'veriloga' in self.viewPath.stem:
            return 'veriloga'
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
            parentLibrary = model.findItems(selectedLibPath.stem,
                                            flags=Qt.MatchExactly)[0]
            newCellItem = cellItem(cellPath)
            selectedLib.appendRow(newCellItem)
            parent.logger.warning(f"Created {cellName} cell at {str(cellPath)}")
            return newCellItem


def createCellView(parent, viewName, cellItem:cellItem) -> viewItem:
    if viewName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a view name")
        return None
    elif cellItem.data(Qt.UserRole+2).joinpath(f'{viewName}.json').exists():
        QMessageBox.warning(parent, "Error", "View exists. Delete cellview first.")
        return None
    else:
        viewPath = cellItem.data(Qt.UserRole+2).joinpath(f'{viewName}.json')
        viewPath.touch()  # create the view file
        newViewItem = viewItem(viewPath)
        items = []
        if newViewItem.viewType == 'schematic':
            items.insert(0, {'cellView': 'schematic'})
            with open(viewPath, "w") as f:
                json.dump(items, f, cls=se.schematicEncoder, indent=4)
        elif newViewItem.viewType == 'symbol':
            items.insert(0, {'cellView': 'symbol'})
            with open(viewPath, "w") as f:
                json.dump(items, f, cls=se.symbolEncoder, indent=4)
        elif newViewItem.viewType == 'veriloga':
            items.insert(0, {'cellView': 'veriloga'})
            items.insert(1, {'filePath': str(parent.importedVaObj.pathObj)})
            items.insert(2, {'vaModule': parent.importedVaObj.vaModule})
            items.insert(3, {'netlistLine': parent.importedVaObj.netListLine})
            with open(viewPath, "w") as f:
                json.dump(items, f, cls=se.schematicEncoder, indent=4)
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


def writeLibDefFile(libPathDict:dict, libFilePath: pathlib.Path, logger) -> None:

    # yaml = YAML()
    # yaml.explicit_start = True
    # yaml.default_flow_style = False
    libTempDict = dict(zip(libPathDict.keys(),map(str,libPathDict.values())))
    try:
        with libFilePath.open(mode="w") as f:
            json.dump({'libdefs': libTempDict},f, indent=4)
    #         yaml.dump(libDefDict, libFilePath)
    #     logger.warning('writing library definition file.')
    except IOError:
        logger.error(f"Cannot save library definitions in {libFilePath}")


def readLibDefFile(libPath:Path, logger):
    libraryDict = dict()
    try:
        with libPath.open(mode='r') as f:
            data = json.load(f)
    except IOError:
        logger.warning(f'No {str(libPath)} is found.')
    if data.get('libdefs') is not None:
        for key, value in data['libdefs'].items():
            libraryDict[key] = Path(value)
    elif data.get('include') is not None:
        for item in data.get('include'):
            libraryDict.update(readLibDefFile(Path(item),logger))
    return libraryDict


