# schematic editor backend
import pathlib
import shutil
from pathlib import Path

from PySide6.QtCore import (Qt, )
from PySide6.QtGui import (QStandardItem, )
from PySide6.QtWidgets import (QMessageBox, )
from ruamel.yaml import YAML

import revedaeditor.common.shape as shp


class libraryItem(QStandardItem):
    def __init__(self, libraryPath: pathlib.Path
                 ):  # path is a pathlib.Path object
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
    def libraryPath(self,value):
        if isinstance(value, pathlib.Path):
            self._libraryPath = value

    @property
    def libraryName(self):
        return self._libraryName

class cellItem(QStandardItem):
    def __init__(self, cellPath: pathlib.Path) -> None:
        self.cellName = cellPath.stem
        super().__init__(self.cellName)
        self.setEditable(False)
        self.setData("cell", Qt.UserRole + 1)
        self.setData(cellPath, Qt.UserRole + 2)

    def type(self):
        return QStandardItem.UserType + 1


class viewItem(QStandardItem):
    def __init__(self, viewPath: pathlib.Path) -> None:
        self.viewName = viewPath.stem
        super().__init__(self.viewName)
        self.setEditable(False)
        self.setData("view", Qt.UserRole + 1)
        # set the data to the item to be the path to the view.
        self.setData(
            viewPath, Qt.UserRole + 2, )
        self.setData(self.viewName, Qt.UserRole + 3)

    def type(self):
        return QStandardItem.UserType + 2


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


def createCellView(parent, viewName, cellPath) -> viewItem:
    if viewName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a view name")
    viewPath = cellPath.joinpath(viewName + ".json")
    viewPath.touch()  # create the view file
    newViewItem = viewItem(viewPath)
    newViewItem.setData("view", Qt.UserRole + 1)
    newViewItem.setData(viewPath, Qt.UserRole + 2)
    newViewItem.setData(viewName, Qt.UserRole + 3)
    # cellItem.appendRow(newViewItem)
    # needs to decide on how to handle the view type
    print(f"Created {viewName} at {str(viewPath)}")
    # with open(viewPath, "w") as f: # write an empty json file
    #     f.writelines('[')
    #     f.writelines({'type': 'view', 'name': viewName})
    #     f.writelines(']')
    return newViewItem


# function for copying a cell
def copyCell(parent, model, origCellItem: cellItem, copyName, selectedLibPath
             ) -> bool:
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
    else:
        assert cellPath.exists()
        shutil.copytree(cellPath, copyPath)  # copied the cell
        libraryItem = \
            model.findItems(selectedLibPath.cellName, flags=Qt.MatchExactly)[
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
            addedView.setData(
                copyPath.joinpath(view).with_suffix(".json"), Qt.UserRole + 2, )
            addedView.setEditable(False)
            cellItem.appendRow(addedView)
        libraryItem.appendRow(cellItem)


def renameCell(parent, oldCell, newName) -> bool:
    cellPath = oldCell.data(Qt.UserRole + 2)
    if newName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a cell name")
        return False
    else:
        cellPath.rename(cellPath.parent / newName)
        oldCell.setText(newName)
        return True


def createCell(parent, model, selectedLib, cellName) -> bool:
    assert isinstance(selectedLib, libraryItem)
    if cellName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a cell name")
        return False
    else:
        if selectedLib.data(Qt.UserRole + 1) == "library":
            selectedLibPath = selectedLib.data(Qt.UserRole + 2)
            cellPath = selectedLibPath.joinpath(cellName)
            if cellPath.exists():
                QMessageBox.warning(parent, "Error", "Cell already exits.")
            else:
                cellPath.mkdir()
                parentLibrary = model.findItems(
                    selectedLibPath.stem, flags=Qt.MatchExactly
                    )[0]
        newCellItem = cellItem(cellPath)
        selectedLib.appendRow(newCellItem)
        print(f"Created {cellName} cell at {str(cellPath)}")
        return True


def writeLibDefFile(libPathDict, libPath):
    yaml = YAML()
    yaml.explicit_start = True
    yaml.default_flow_style = False
    libDefDict = {}
    for key, value in libPathDict.items():
        libDefDict[key] = str(value)
    yaml.dump(libDefDict, libPath)


def readLibDefFile(libPath):
    yaml = YAML()
    yaml.explicit_start = True
    yaml.default_flow_style = False
    data = list(yaml.load_all(libPath))
    libraryDict = {}  # empty dictionary
    for key, value in data[0].items():
        libraryDict[key] = Path(value)
    return libraryDict

# def decodeSymbol(item):
#     print(type(item))
#
#
# def decodeLabel(label: shp.label):
#     assert isinstance(label, shp.label)
#     label.labelDefs()

# def createNetlistLine(symbolItem: shp.symbolShape):
#     """
#     Create a netlist line from a nlp device format line.
#     """
#     nlpDeviceFormatLine = symbolItem.attr["NLPDeviceFormat"].strip()
#     # nlpDeviceFormatLine.replace("[@instName]", f'{symbolItem.instanceName}')
#     for labelItem in symbolItem.labels.values():
#         if labelItem.labelDefinition in nlpDeviceFormatLine:
#             nlpDeviceFormatLine = nlpDeviceFormatLine.replace(
#                 labelItem.labelDefinition, labelItem.labelText
#                 )
#     for pinName, netName in symbolItem.pinNetMap.items():
#         if pinName in nlpDeviceFormatLine:
#             nlpDeviceFormatLine = nlpDeviceFormatLine.replace(
#                 f'[|{pinName}:%]', netName
#                 )
    return nlpDeviceFormatLine  # #     return ""

# def createSubcktHeaderLine(symbolItem: shp.symbolShape):
#     """
#     create the subckt definition line
#     """
#     nlpDeviceFormatLine = symbolItem.attr["NLPDeviceFormat"][1].strip()
