# schematic editor backend
import pathlib

from PySide6.QtGui import (
    QStandardItem,
)
from PySide6.QtWidgets import (
    QMessageBox,
)
import shutil
from ruamel.yaml import YAML
import shape as shp
from pathlib import Path

from PySide6.QtCore import (
    Qt,
)


class libraryItem(QStandardItem):
    def __init__(
        self, libraryPath: pathlib.Path, libraryName: str
    ):  # path is a pathlib.Path object
        super().__init__(libraryName)
        self.libraryPath = libraryPath
        self.libraryName = libraryName
        self.setEditable(False)
        self.setData(libraryPath, Qt.UserRole + 2)
        self.setData("library", Qt.UserRole + 1)


class cellItem(QStandardItem):
    def __init__(self, libraryPath: pathlib.Path, cellName: str) -> None:
        super().__init__(cellName)
        self.cellName = cellName
        self.libraryPath = libraryPath
        self.setEditable(False)
        self.setData("cell", Qt.UserRole + 1)
        self.setData(libraryPath / cellName, Qt.UserRole + 2)

    def type(self):
        return QStandardItem.UserType + 1


class viewItem(QStandardItem):
    def __init__(self, libraryPath: pathlib.Path, cellName: str, viewName) -> None:
        super().__init__(viewName)
        self.name = viewName
        self.libraryPath = libraryPath
        self.cellName = cellName
        self.setEditable(False)
        self.setData("view", Qt.UserRole + 1)
        # set the data to the item to be the path to the view.
        self.setData(
            libraryPath.joinpath(cellName, viewName).with_suffix(".json"),
            Qt.UserRole + 2,
        )

    def type(self):
        return QStandardItem.UserType + 2


def createLibrary(parent, model, libraryDir, libraryName):
    if libraryName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a library name")
    else:
        libraryPath = Path(libraryDir).joinpath(libraryName)
        if libraryPath.exists():
            QMessageBox.warning(parent, "Error", "Library already exits.")
        else:
            libraryPath.mkdir()
            libraryItem = QStandardItem(libraryPath.name)
            libraryItem.setData(libraryPath, Qt.UserRole + 2)
            libraryItem.setData("library", Qt.UserRole + 1)
            model.appendRow(libraryItem)
            print(f"Created {libraryPath}")


def createCellView(parent, viewName, cellItem):
    if viewName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a view name")
    cellPath = cellItem.data(Qt.UserRole + 2)
    viewPath = cellPath.joinpath(viewName + ".json")
    viewPath.touch()  # create the view file
    viewItem = QStandardItem(viewName)
    viewItem.setData(viewPath, Qt.UserRole + 2)
    viewItem.setData("view", Qt.UserRole + 1)
    cellItem.appendRow(viewItem)
    # needs to decide on how to handle the view type
    print(f"Created {viewName} at {str(viewPath)}")
    with open(viewPath, "w") as f: # write an empty json file
        f.writelines('[')
        f.writelines({'type': 'view', 'name': viewName})
        f.writelines(']')
    return viewItem


# function for copying a cell
def copyCell(parent, model, cellItem, copyName, selectedLibPath):
    """
    parent: the parent widget
    model: the model
    cellItem: the cell item in the model
    copyName: the name of the new cell
    selectedLibPath: the path of the selected library
    """
    cellPath = cellItem.data(Qt.UserRole + 2)  # get the cell path from item user data
    if copyName == "":
        copyName = "newCell"
    copyPath = selectedLibPath.joinpath(copyName)
    if copyPath.exists():
        QMessageBox.warning(parent, "Error", "Cell already exits.")
    else:
        assert cellPath.exists()
        shutil.copytree(cellPath, copyPath)  # copied the cell
        libraryItem = model.findItems(selectedLibPath.cellName, flags=Qt.MatchExactly)[
            0
        ]  # find the library item
        # create new cell item
        cellItem = QStandardItem(copyPath.cellName)
        cellItem.setEditable(False)
        cellItem.setData("cell", Qt.UserRole + 1)
        cellItem.setData(copyPath, Qt.UserRole + 2)
        # go through view list and add to cell item
        viewList = [
            str(view.stem) for view in copyPath.iterdir() if view.suffix == ".json"
        ]

        for view in viewList:
            viewItem = QStandardItem(view)
            viewItem.setData("view", Qt.UserRole + 1)
            # set the data to the item to be the path to the view.
            viewItem.setData(
                copyPath.joinpath(view).with_suffix(".json"),
                Qt.UserRole + 2,
            )
            viewItem.setEditable(False)
            cellItem.appendRow(viewItem)
        libraryItem.appendRow(cellItem)


def renameCell(parent, cellItem, newName):
    cellPath = cellItem.data(Qt.UserRole + 2)
    if newName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a cell name")
    else:
        cellPath.rename(cellPath.parent / newName)
        cellItem.setText(newName)


def createCell(parent, model, selectedItem, cellName):
    if cellName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a cell name")
    else:
        if selectedItem.data(Qt.UserRole + 1) == "library":
            selectedLibPath = selectedItem.data(Qt.UserRole + 2)

            cellPath = selectedLibPath.joinpath(cellName)
            if cellPath.exists():
                QMessageBox.warning(parent, "Error", "Cell already exits.")
            else:
                cellPath.mkdir()
                libraryItem = model.findItems(
                    selectedLibPath.stem, flags=Qt.MatchExactly
                )[0]
        cellItem = QStandardItem(cellName)
        cellItem.setData(cellPath, Qt.UserRole + 2)
        cellItem.setData("cell", Qt.UserRole + 1)
        libraryItem.appendRow(cellItem)
        print(f"Created {cellName} at {str(cellPath)}")


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


def decodeSymbol(item):
    print(type(item))

def decodeLabel(label: shp.label):
    assert isinstance(label, shp.label)
    if label.labelType == "Normal":
        label.setText(label.labelDefinition)
    elif label.labelType == "NLPLabel":
        try:
            if label.labelDefinition == "[@cellName]":
                label.labelText=label.parentItem().cellName
                label.labelName = "cellName"
            elif label.labelDefinition == "[@instName]":
                label.labelText=f'I{label.parentItem().counter}'
                label.labelName = "instName"
            elif label.labelDefinition == "[@libName]":
                label.labelText=label.parentItem().libraryName
                label.labelName = "libName"
            elif label.labelDefinition == "[@viewName]":
                label.labelText=label.parentItem().viewName
                label.labelName = "viewName"
            elif label.labelDefinition == "[@modelName]":
                label.labelText=label.parentItem().attr["modelName"]
                label.labelName = "modelName"
            elif label.labelDefinition == "[@elementNum]":
                label.labelText=label.parentItem().counter
                label.labelName = "elementNum"
            else:
                if ':' in label.labelDefinition: # there is at least one colon
                    fieldsLength = len(label.labelDefinition.split(':'))
                    if fieldsLength == 1:
                        label.labelName = label.labelDefinition[1:-1]
                        label.labelText = f'{label.labelDefinition[1:-1]}=?'
                    elif len(label.labelDefinition.split(':')) == 2: # there is only one colon
                        label.labelName = label.labelDefinition.split(":")[0].split("@")[1]
                        label.labelText = f'{label.labelDefinition[1:-1]}=?'
                    elif len(label.labelDefinition.split(':')) == 3: # there are two colons
                        label.labelName = label.labelDefinition.split(":")[0].split("@")[1]
                        label.labelText = f'{label.labelDefinition.split(":")[2][:-1]}'
                    else:
                        print('label format error.')
        except Exception as e:
            print(e)
