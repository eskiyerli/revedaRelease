import os
import sys
from pathlib import Path
from threading import Thread
import shutil


from PySide6.QtGui import (
    QAction,
    QColor,
    QIcon,
    QPalette,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
    QPen,
    QTransform,
    QCursor,
    QPainter,
    QFont,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QFileDialog,
    QComboBox,
    QFormLayout,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QRadioButton,
    QTabWidget,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
    QGraphicsLineItem,
    QGraphicsItem,
    QDialogButtonBox,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTabWidget,
)
from PySide6.QtCore import (
    QModelIndex,
    Qt,
    QPoint,
    QLine,
    QDir,
)
from numpy.lib.function_base import copy

import resources
import numpy as np
import math
import circuitElements as cel
from Point import *
from Vector import *
from ruamel.yaml import YAML
import pythonConsole as pcon
from contextlib import redirect_stdout, redirect_stderr
import schBackEnd as scb  # import the backend


class designLibrariesView(QTreeView):
    def __init__(self, parent=None, libraryDict={}):
        super().__init__(parent=parent)  # QTreeView
        self.parent = parent  # type: QMainWindow
        self.libraryDict = libraryDict  # type: dict
        self.cellViews = ['schematic', 'symbol', 'layout']
        self.init_UI()

    def init_UI(self):
        self.setSortingEnabled(True)
        self.initModel()
        # iterate design library directories
        for designPath in self.libraryDict.values():  # type: Path
            self.addLibrary(designPath, self.parentItem)

        self.setModel(self.libraryModel)

    def initModel(self):
        self.libraryModel = QStandardItemModel()
        self.libraryModel.setHorizontalHeaderLabels(["Libraries"])
        self.parentItem = self.libraryModel.invisibleRootItem()

    def addLibrary(self, designPath, parentItem):  # type: Path, QStandardItem
        libraryName = (
            designPath.name
        )  # name of the directory is the name of the library
        # create a standard Item
        libraryNameItem = QStandardItem(libraryName)
        libraryNameItem.setEditable(False)
        libraryNameItem.setData("library", Qt.UserRole + 1)
        libraryNameItem.setData(designPath, Qt.UserRole + 2)
        cellList = [str(cell.name) for cell in designPath.iterdir() if cell.is_dir()]
        for cell in cellList:  # type: str
            viewList = [
                str(view.stem)
                for view in designPath.joinpath(cell).iterdir()
                if view.suffix == ".py"
            ]
            if len(viewList) >= 0:
                cellItem = self.addCell(designPath, libraryNameItem, cell)
                for view in viewList:
                    self.addCellView(designPath, cell, cellItem, view)
        parentItem.appendRow(libraryNameItem)

    def addCell(self, designPath, libraryNameItem, cell):
        cellItem = QStandardItem(cell)
        cellItem.setEditable(False)
        cellItem.setData("cell", Qt.UserRole + 1)
        cellItem.setData(designPath / cell, Qt.UserRole + 2)

        libraryNameItem.appendRow(cellItem)
        return cellItem

    def addCellView(self, designPath, cell, cellItem, view):
        viewItem = QStandardItem(view)
        viewItem.setData("view", Qt.UserRole + 1)
        # set the data to the item to be the path to the view.
        viewItem.setData(
            designPath.joinpath(cell, view).with_suffix(".py"),
            Qt.UserRole + 2,
        )
        viewItem.setEditable(False)
        cellItem.appendRow(viewItem)

    def removeLibrary(self):
        pass

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        try:
            index = self.selectedIndexes()[0]
        except IndexError:
            pass
        self.selectedItem = self.libraryModel.itemFromIndex(index)
        if self.selectedItem.data(Qt.UserRole + 1) == "library":
            menu.addAction("Save Library As...", self.saveLibAs)
            menu.addAction("Rename Library", self.renameLib)
            menu.addAction("Create Cell", self.createCell)
        elif self.selectedItem.data(Qt.UserRole + 1) == "cell":
            menu.addAction(
                QAction("Create CellView...", self, triggered=self.createCellView)
            )
            menu.addAction(QAction("Copy Cell...", self, triggered=self.copyCell))
            menu.addAction(QAction("Rename Cell...", self, triggered=self.renameCell))
            menu.addAction(QAction("Delete Cell...", self, triggered=self.deleteCell))
        elif self.selectedItem.data(Qt.UserRole + 1) == "view":
            menu.addAction(QAction("Open View", self, triggered=self.openView))
            menu.addAction(QAction("Copy View...", self, triggered=self.copyView))
            menu.addAction(QAction("Rename View...", self, triggered=self.renameView))
            menu.addAction(QAction("Delete View...", self, triggered=self.deleteView))
        menu.exec(event.globalPos())

    def saveLibAs(self):
        pass

    def renameLib(self):
        pass

    def createCell(self):
        dlg = createCellDialog(self, self.libraryModel, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            scb.createCell(
                self, self.libraryModel, self.selectedItem, dlg.nameEdit.text()
            )
            self.reworkDesignLibrariesView()

    def createCellView(self):
        dlg = createCellViewDialog(
            self, self.libraryModel, self.selectedItem
        )  # type: createCellViewDialog
        if dlg.exec() == QDialog.Accepted:
            viewItem = scb.createCellView(self, dlg.nameEdit.text(), dlg.cellItem)
            self.reworkDesignLibrariesView()

    def copyCell(self):
        dlg = copyCellDialog(self, self.libraryModel, self.selectedItem)

        if dlg.exec() == QDialog.Accepted:
            scb.copyCell(
                self, dlg.model, dlg.cellItem, dlg.copyName.text(), dlg.selectedLibPath
            )

    def renameCell(self):
        dlg = renameCellDialog(self, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            scb.renameCell(self, dlg.model, dlg.cellItem, dlg.nameEdit.text())

    def deleteCell(self):
        try:
            shutil.rmtree(self.selectedItem.data(Qt.UserRole + 2))
            self.selectedItem.parent().removeRow(self.selectedItem.row())
        except OSError as e:
            print(f"Error:{ e.strerror}")

    def openView(self):
        if self.selectedItem.text() == "schematic":
            print(self.selectedItem.data(Qt.UserRole + 2).read_text())

    def copyView(self):
        dlg = copyViewDialog(self, self.libraryModel, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            if self.selectedItem.data(Qt.UserRole + 1) == "view":
                viewPath = self.selectedItem.data(Qt.UserRole + 2)
                newViewPath = dlg.selectedLibPath.joinpath(
                    dlg.selectedCell, dlg.selectedView + ".py"
                )
                if not newViewPath.exists():
                    try:
                        newViewPath.parent.mkdir(parents=True)
                    except FileExistsError:
                        pass
                    shutil.copy(viewPath, newViewPath)
                else:
                    QMessageBox.warning(self, "Error", "View already exits.")
                    self.copyView()  # try again

    def renameView(self):
        pass

    def deleteView(self):
        try:
            self.selectedItem.data(Qt.UserRole + 2).unlink()
            self.selectedItem.parent().removeRow(self.selectedItem.row())
        except OSError as e:
            print(f"Error:{ e.strerror}")

    def reworkDesignLibrariesView(self):
        self.libraryModel.clear()
        self.initModel()
        self.setModel(self.libraryModel)
        for designPath in self.libraryDict.values():  # type: Path
            print(designPath)
            self.addLibrary(designPath, self.parentItem)


class libraryBrowser(QMainWindow):
    def __init__(self, libraryDict) -> None:
        super().__init__()
        self.libraryDict = libraryDict
        self.setWindowTitle("Library Browser")
        self._createMenuBar()
        self._createActions()
        self.initUI()

    def initUI(self):

        self.setCentralWidget(libraryBrowserContainer(self, self.libraryDict))

    def _createMenuBar(self):
        self.menuBar = self.menuBar()
        self.libraryMenu=self.menuBar.addMenu("&Library")

    def _createActions(self):
        newLibIcon = QIcon(":/icons/database--plus.png")
        self.newLibAction = QAction(newLibIcon, "New Lib...", self)
        self.libraryMenu.addAction(self.newLibAction)        
        self.newLibAction.triggered.connect(self.newLibrary)

    def newLibrary(self):
        pass 
    
    def openLibDialog(self):
        home_dir = str(Path.home())
        fname = QFileDialog.getOpenFileName(self, "Open file", home_dir)  

class libraryBrowserContainer(QWidget):
    def __init__(self, parent, libraryDict) -> None:
        super().__init__(parent)
        self.libraryDict = libraryDict
        self.setWindowTitle("Library Browser")
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.layout.addWidget(designLibrariesView(self, self.libraryDict))
        self.setLayout(self.layout)


class container(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.init_UI()

    def init_UI(self):

        # treeView = designLibrariesView(self)
        self.console = pcon.pythonConsole(globals())
        self.console.writeoutput("Welcome to RevEDA")
        self.console.writeoutput("Revolution Semiconductor (C) 2021.")
        self.console.setfont(QFont("Fira Mono Regular", 12))
        # layout statements, using a grid layout
        gLayout = QVBoxLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.console)
        self.setLayout(gLayout)


class createCellDialog(QDialog):
    def __init__(self, parent, libraryModel, selectedItem):
        super().__init__(parent)
        self.parent = parent
        self.libraryModel = libraryModel
        self.selectedItem = selectedItem
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Create Cell")
        layout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("Enter Cell Name")
        layout.addRow("Cell Name:", self.nameEdit)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)


class createCellViewDialog(QDialog):
    def __init__(self, parent, model, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.model = model
        self.cellItem = cellItem
        self.cellPath = self.cellItem.data(Qt.UserRole + 2)
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Create CellView")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.viewComboBox = QComboBox()
        self.viewComboBox.addItems(self.parent.cellViews)
        layout.addRow("Select View:", self.viewComboBox)
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("CellView Name")
        self.nameEdit.setFixedWidth(200)
        layout.addRow(QLabel("View Name:"), self.nameEdit)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)


class renameCellDialog(QDialog):
    def __init__(self, parent, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.cellItem = cellItem

        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Rename Cell")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("Cell Name")
        self.nameEdit.setFixedWidth(200)
        layout.addRow(QLabel("Cell Name:"), self.nameEdit)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)


class copyCellDialog(QDialog):
    def __init__(self, parent, model, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.model = model
        self.cellItem = cellItem

        # self.index = 0
        self.init_UI()

    def init_UI(self):

        self.setWindowTitle("Copy Cell")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.libraryComboBox = QComboBox()
        self.libraryComboBox.setModel(self.model)
        self.libraryComboBox.setModelColumn(0)
        self.libraryComboBox.setCurrentIndex(0)
        self.selectedLibPath = self.libraryComboBox.itemData(0, Qt.UserRole + 2)
        self.libraryComboBox.currentTextChanged.connect(self.selectLibrary)
        layout.addRow(QLabel("Library:"), self.libraryComboBox)
        self.copyName = QLineEdit()
        self.copyName.setPlaceholderText("Enter Cell Name")
        self.copyName.setFixedWidth(130)
        layout.addRow(QLabel("Cell Name:"), self.copyName)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)

    def selectLibrary(self):
        self.selectedLibPath = self.libraryComboBox.itemData(
            self.libraryComboBox.currentIndex(), Qt.UserRole + 2
        )


class copyViewDialog(QDialog):
    def __init__(self, parent, model, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.model = model
        self.cellItem = cellItem

        # self.index = 0
        self.init_UI()

    def init_UI(self):

        self.setWindowTitle("Copy CellView")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.libraryComboBox = QComboBox()
        self.libraryComboBox.setModel(self.model)
        self.libraryComboBox.setModelColumn(0)
        self.libraryComboBox.setCurrentIndex(0)
        self.selectedLibPath = self.libraryComboBox.itemData(0, Qt.UserRole + 2)
        self.libraryComboBox.currentTextChanged.connect(self.selectLibrary)
        layout.addRow(QLabel("Library:"), self.libraryComboBox)
        self.cellComboBox = QComboBox()
        cellList = [
            str(cell.name) for cell in self.selectedLibPath.iterdir() if cell.is_dir()
        ]
        self.cellComboBox.addItems(cellList)
        self.cellComboBox.setEditable(True)
        self.cellComboBox.InsertPolicy = QComboBox.InsertAfterCurrent
        layout.addRow(QLabel("Cell Name:"), self.cellComboBox)
        self.selectedCell = self.cellComboBox.currentText()
        self.cellComboBox.currentTextChanged.connect(self.selectCell)
        self.viewComboBox = QComboBox()
        self.viewComboBox.setEditable(True)
        self.viewComboBox.InsertPolicy = QComboBox.InsertAfterCurrent
        self.viewComboBox.addItems(self.viewList())
        self.selectedView = self.viewComboBox.currentText()
        self.viewComboBox.currentTextChanged.connect(self.selectView)
        layout.addRow(QLabel("View Name:"), self.viewComboBox)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)

    def viewList(self):
        viewList = [
            str(view.stem)
            for view in self.selectedLibPath.joinpath(self.selectedCell).iterdir()
            if view.suffix == ".py"
        ]
        return viewList

    def selectLibrary(self):
        self.selectedLibPath = self.libraryComboBox.itemData(
            self.libraryComboBox.currentIndex(), Qt.UserRole + 2
        )
        cellList = [
            str(cell.name) for cell in self.selectedLibPath.iterdir() if cell.is_dir()
        ]
        self.cellComboBox.clear()
        self.cellComboBox.addItems(cellList)

    def selectCell(self):
        self.selectedCell = self.cellComboBox.currentText()
        self.viewComboBox.clear()
        self.viewComboBox.addItems(self.viewList())

    def selectView(self):
        self.selectedView = self.viewComboBox.currentText()


class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        revEDAPathObj = Path(__file__)
        revEDADirObj = revEDAPathObj.parent
        self.cellViews = ["schematic", "symbol"]
        libraryPathObj = Path.cwd().joinpath("library.yaml")
        try:
            with libraryPathObj.open(mode="r") as f:
                self.libraryDict = scb.readLibDefFile(f)
        except IOError:
            print(f"Cannot find {str(libraryPathObj)} file.")
            self.libraryDict = {}
        self.init_UI()

    def init_UI(self):
        self.resize(900, 300)
        self._createMenuBar()
        self._createActions()
        # create container to position all widgets
        self.centralWidget = container(self)
        self.setCentralWidget(self.centralWidget)
        self.libraryBrowser = None

    def _createMenuBar(self):
        self.menuBar = self.menuBar()
        # Returns QMenu object.
        self.menuFile = self.menuBar.addMenu("&File")
        self.menuTools = self.menuBar.addMenu("&Tools")
        self.menuOptions = self.menuBar.addMenu("&Options")

        self.menuHelp = self.menuBar.addMenu("&Help")

        self.statusBar()

        # create actions

    def _createActions(self):
        openLibIcon = QIcon(":/icons/database--pencil.png")
        self.libraryBrowserAction = QAction(openLibIcon, "Library Browser", self)
        self.menuTools.addAction(self.libraryBrowserAction)
        self.libraryBrowserAction.triggered.connect(self.libraryBrowserClick)

    def libraryBrowserClick(self):
        if self.libraryBrowser is None:
            self.libraryBrowser = libraryBrowser(
                self.libraryDict
            )  # create the library browser
            self.libraryBrowser.show()
        else:
            self.libraryBrowser.show()


app = QApplication(sys.argv)
# app.setStyle('Fusion')
# empty argument as there is no parent window.
mainW = mainWindow()
mainW.setWindowTitle("Revolution EDA Main Window")
redirect = pcon.Redirect(mainW.centralWidget.console.errorwrite)
with redirect_stdout(mainW.centralWidget.console), redirect_stderr(redirect):
    mainW.show()
    sys.exit(app.exec())
