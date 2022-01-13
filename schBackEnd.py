# schematic editor backend
from PySide6.QtGui import (
    QStandardItem,

)
from PySide6.QtWidgets import (
    QMessageBox,
)
import shutil
from ruamel.yaml import YAML
from pathlib import Path

from PySide6.QtCore import (
    Qt,

)

def createLibrary(parent,model,libraryDir,libraryName):
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

def createCellView(parent,viewName, cellItem):
    if viewName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a view name")
    cellPath = cellItem.data(Qt.UserRole+2)
    viewPath = cellPath.joinpath(viewName+'.py')
    viewPath.touch()  # create the view file
    viewItem = QStandardItem(viewName)
    viewItem.setData(viewPath, Qt.UserRole + 2)
    viewItem.setData("view", Qt.UserRole + 1)
    cellItem.appendRow(viewItem)
    # needs to decide on how to handle the view type
    print(f"Created {viewName} at {str(viewPath)}")
    return viewItem

# function for copying a cell
def copyCell(parent,model,cellItem,copyName, selectedLibPath):
    '''
    parent: the parent widget
    model: the model
    cellItem: the cell item in the model
    copyName: the name of the new cell
    selectedLibPath: the path of the selected library
    '''
    cellPath = cellItem.data(Qt.UserRole + 2)    # get the cell path from item user data
    if copyName == "":
        copyName = "newCell"
    copyPath = selectedLibPath.joinpath(copyName)
    if copyPath.exists():
        QMessageBox.warning(parent, "Error", "Cell already exits.")
    else:
        assert cellPath.exists()
        shutil.copytree(cellPath, copyPath)  # copied the cell
        libraryItem = model.findItems(
            selectedLibPath.name, flags=Qt.MatchExactly
        )[
            0
        ]  # find the library item
        # create new cell item
        cellItem = QStandardItem(copyPath.name)
        cellItem.setEditable(False)
        cellItem.setData("cell", Qt.UserRole + 1)
        cellItem.setData(copyPath, Qt.UserRole + 2)
        # go through view list and add to cell item
        viewList = [
            str(view.stem)
            for view in copyPath.iterdir()
            if view.suffix == ".py"
        ]

        for view in viewList:
            viewItem = QStandardItem(view)
            viewItem.setData("view", Qt.UserRole + 1)
            # set the data to the item to be the path to the view.
            viewItem.setData(
                copyPath.joinpath(view).with_suffix(".py"),
                Qt.UserRole + 2,
            )
            viewItem.setEditable(False)
            cellItem.appendRow(viewItem)
        libraryItem.appendRow(cellItem)

def renameCell(parent,cellItem,newName):
    cellPath = cellItem.data(Qt.UserRole + 2)
    if newName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a cell name")
    else:
        cellPath.rename(cellPath.parent/newName)
        cellItem.setText(newName)

def createCell(parent,model,selectedItem,cellName):
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
                    selectedLibPath.name, flags=Qt.MatchExactly
                )[
                    0
                ]
        cellItem = QStandardItem(cellName)
        cellItem.setData(cellPath, Qt.UserRole + 2)
        cellItem.setData("cell", Qt.UserRole + 1)
        libraryItem.appendRow(cellItem)
        print(f"Created {cellName} at {str(cellPath)}")

def writeLibDefFile(libPathDict, libPath):
        yaml = YAML()
        yaml.explicit_start = True
        yaml.default_flow_style = False
        libDefDict ={}
        for key,value in libPathDict.items():
            libDefDict[key]=str(value)
        yaml.dump(libDefDict,libPath)

def readLibDefFile(libPath):
    yaml = YAML()
    yaml.explicit_start = True
    yaml.default_flow_style = False
    data = list(yaml.load_all(libPath)) 
    libraryDict={} # empty dictionary
    for key,value in data[0].items():
        libraryDict[key]= Path(value)
    return libraryDict


