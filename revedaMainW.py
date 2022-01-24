import json
import math
import os
import shutil
import sys
from contextlib import redirect_stderr, redirect_stdout

# from hashlib import new
from pathlib import Path

# from threading import Thread

import json


import numpy as np
from numpy.lib.function_base import copy
from PySide6.QtCore import QDir, QLine, QModelIndex, QPoint, QPointF, QRect, QRectF, Qt
from PySide6.QtGui import (
    QAction,
    QColor,
    QCursor,  # QPalette,; QPixmap,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QStandardItem,
    QStandardItemModel,
    QTransform,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTabWidget,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from ruamel.yaml import YAML

import circuitElements as cel
import pythonConsole as pcon
import resources
import schBackEnd as scb  # import the backend
from Point import *
from Vector import *


class designLibrariesView(QTreeView):
    def __init__(self, parent=None, libraryDict={}):
        super().__init__(parent=parent)  # QTreeView
        self.parent = parent  # type: QMainWindow
        self.libraryDict = libraryDict  # type: dict
        self.cellViews = ["schematic", "symbol", "layout"]
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

    def addLibrary(self, designPath, parentItem):  # designPath: Path
        if designPath.is_dir():
            libraryEntry = scb.libraryItem(designPath, designPath.name)
            parentItem.appendRow(libraryEntry)

            cellList = [
                str(cell.name) for cell in designPath.iterdir() if cell.is_dir()
            ]
            for cell in cellList:  # type: str
                viewList = [
                    str(view.stem)
                    for view in designPath.joinpath(cell).iterdir()
                    if view.suffix == ".json" and str(view.stem) in self.cellViews
                ]
                if len(viewList) >= 0:
                    cellEntry = self.addCell(designPath, libraryEntry, cell)
                    for view in viewList:
                        self.addCellView(designPath, cell, cellEntry, view)

    def addCell(self, designPath, libraryNameItem, cell):
        cellEntry = scb.cellItem(designPath, cell)
        libraryNameItem.appendRow(cellEntry)
        # libraryNameItem.appendRow(cellItem)
        return cellEntry

    def addCellView(self, designPath, cell, cellItem, view):
        viewEntry = scb.viewItem(designPath, cell, view)
        cellItem.appendRow(viewEntry)
        return viewEntry

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
            menu.addAction("Remove Library", self.removeLibrary)
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

    def removeLibrary(self):
        shutil.rmtree(self.selectedItem.data(Qt.UserRole + 2))
        self.libraryModel.removeRow(self.selectedItem.row())

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
            scb.createCellView(self, dlg.nameEdit.text(), dlg.cellItem)
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
            print(f"Error:{e.strerror}")

    def openView(self):
        if self.selectedItem.text() == "schematic":
            print(self.selectedItem.type())
            schematicWindow = schematicEditor()
            schematicWindow.show()
        elif self.selectedItem.text() == "symbol":
            symbolWindow = symbolEditor(file=self.selectedItem.data(Qt.UserRole + 2))
            symbolWindow.show()
            symbolWindow.loadSymbol()

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
            print(f"Error:{e.strerror}")

    def reworkDesignLibrariesView(self):
        self.libraryModel.clear()
        self.initModel()
        self.setModel(self.libraryModel)
        for designPath in self.libraryDict.values():  # type: Path
            self.addLibrary(designPath, self.parentItem)


class libraryBrowser(QMainWindow):
    def __init__(self, libraryDict) -> None:
        super().__init__()
        self.libraryDict = libraryDict
        self.setWindowTitle("Library Browser")
        self._createMenuBar()
        self._createActions()

        self._createToolBars()

        self.initUI()

    def initUI(self):
        self.libBrowserCont = libraryBrowserContainer(self, self.libraryDict)
        self.setCentralWidget(self.libBrowserCont)

    def _createMenuBar(self):
        self.menuBar = self.menuBar()
        self.libraryMenu = self.menuBar.addMenu("&Library")

    def _createActions(self):
        openLibIcon = QIcon(":/icons/database--plus.png")
        self.openLibAction = QAction(openLibIcon, "Create/Open Lib...", self)
        self.libraryMenu.addAction(self.openLibAction)
        self.openLibAction.triggered.connect(self.openLibDialog)

        self.libraryEditorAction = QAction(openLibIcon, "Library Editor", self)
        self.libraryMenu.addAction(self.libraryEditorAction)
        self.libraryEditorAction.triggered.connect(self.libraryEditorClick)

        newLibIcon = QIcon(":/icons/database--plus.png")
        self.newLibAction = QAction(newLibIcon, "New Lib...", self)
        self.libraryMenu.addAction(self.newLibAction)

        saveLibIcon = QIcon(":/icons/database-import.png")
        self.saveLibAction = QAction(saveLibIcon, "Save Lib...", self)
        self.libraryMenu.addAction(self.saveLibAction)

        closeLibIcon = QIcon(":/icons/database-delete.png")
        self.closeLibAction = QAction(closeLibIcon, "Close Lib...", self)
        self.libraryMenu.addAction(self.closeLibAction)

        self.libraryMenu.addSeparator()
        newCellIcon = QIcon(":/icons/document--plus.png")
        self.newCellAction = QAction(newCellIcon, "New Cell...", self)
        self.libraryMenu.addAction(self.newCellAction)

        openCellIcon = QIcon(":/icons/document--pencil.png")
        self.openCellAction = QAction(openCellIcon, "Open Cell...", self)
        self.libraryMenu.addAction(self.openCellAction)

        saveCellIcon = QIcon(":/icons/document-import.png")
        self.saveCellAction = QAction(saveCellIcon, "Save Cell", self)
        self.libraryMenu.addAction(self.saveCellAction)

        closeCellIcon = QIcon(":/icons/document--minus.png")
        closeCellAction = QAction(closeCellIcon, "Close Cell", self)
        self.libraryMenu.addAction(closeCellAction)

        deleteIcon = QIcon(":/icons/node-delete.png")
        self.deleteCellAction = QAction(deleteIcon, "Delete", self)
        self.libraryMenu.addAction(self.deleteCellAction)

    def _createToolBars(self):
        # Create tools bar called "main toolbar"
        toolbar = QToolBar("Main Toolbar", self)
        # place toolbar at top
        self.addToolBar(toolbar)
        toolbar.addAction(self.newLibAction)
        toolbar.addAction(self.openLibAction)
        toolbar.addAction(self.saveLibAction)
        toolbar.addSeparator()
        toolbar.addAction(self.newCellAction)
        toolbar.addAction(self.openCellAction)
        toolbar.addAction(self.saveCellAction)

    def openLibDialog(self):
        home_dir = str(Path.cwd())
        libDialog = QFileDialog(self, "Create/Open Library", home_dir)
        libDialog.setFileMode(QFileDialog.Directory)
        # libDialog.Option(QFileDialog.ShowDirsOnly)
        if libDialog.exec() == QDialog.Accepted:
            self.libraryDict[libDialog.selectedFiles()[0]] = Path(
                libDialog.selectedFiles()[0]
            )
            self.libBrowserCont.designView.reworkDesignLibrariesView()

    def libraryEditorClick(self, s):
        dlg = libraryPathEditorDialog(self)
        dlg.exec()


class libraryBrowserContainer(QWidget):
    def __init__(self, parent, libraryDict) -> None:
        super().__init__(parent)
        self.libraryDict = libraryDict
        self.setWindowTitle("Library Browser")
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.designView = designLibrariesView(self, self.libraryDict)
        self.layout.addWidget(self.designView)
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


class editorWindow(QMainWindow):
    def __init__(self, file) -> None:  # file is a pathlib.Path object
        super().__init__()
        self.file = file
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("CellView Editor")
        self.resize(1600, 800)
        self._createMenuBar()
        self._createActions()
        self._createToolBars()
        # create container to position all widgets
        self.centralWidget = editorContainer(self)
        self.setCentralWidget(self.centralWidget)

    def _createMenuBar(self):
        self.menuBar = self.menuBar()
        # Returns QMenu object.
        self.menuFile = self.menuBar.addMenu("&File")
        self.menuView = self.menuBar.addMenu("&View")
        self.menuEdit = self.menuBar.addMenu("&Edit")
        self.menuCreate = self.menuBar.addMenu("C&reate")
        self.menuCheck = self.menuBar.addMenu("&Check")
        self.menuTools = self.menuBar.addMenu("&Tools")
        self.menuWindow = self.menuBar.addMenu("&Window")
        self.menuUtilities = self.menuBar.addMenu("&Utilities")
        self.menuSimulation = self.menuBar.addMenu("&Simulation")
        self.menuHelp = self.menuBar.addMenu("&Help")

        self.statusBar()

    def _createActions(self):
        checkCellIcon = QIcon(":/icons/document-task.png")
        self.checkCellAction = QAction(checkCellIcon, "Check-Save", self)
        self.menuFile.addAction(self.checkCellAction)

        self.menuFile.addSeparator()

        readOnlyCellIcon = QIcon(":/icons/lock.png")
        readOnlyCellAction = QAction(readOnlyCellIcon, "Make Read Only", self)
        self.menuFile.addAction(readOnlyCellAction)

        self.menuFile.addSeparator()

        printIcon = QIcon(":/icons/printer--arrow.png")
        self.printAction = QAction(printIcon, "Print...", self)
        self.menuFile.addAction(self.printAction)

        exportImageIcon = QIcon(":/icons/image-export.png")
        exportImageAction = QAction(exportImageIcon, "Export...", self)
        self.menuFile.addAction(exportImageAction)

        self.menuFile.addSeparator()

        exitIcon = QIcon(":/icons/external.png")
        self.exitAction = QAction(exitIcon, "Exit", self)
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.triggered.connect(self.close)
        self.menuFile.addAction(self.exitAction)

        fitIcon = QIcon(":/icons/zone.png")
        self.fitAction = QAction(fitIcon, "Fit to Window", self)
        self.menuView.addAction(self.fitAction)

        zoomInIcon = QIcon(":/icons/zone-resize.png")
        self.zoomInAction = QAction(zoomInIcon, "Zoom In", self)
        self.menuView.addAction(self.zoomInAction)

        zoomOutIcon = QIcon(":/icons/zone-resize-actual.png")
        self.zoomOutAction = QAction(zoomOutIcon, "Zoom Out", self)
        self.menuView.addAction(self.zoomOutAction)

        panIcon = QIcon(":/icons/zone--arrow.png")
        self.panAction = QAction(panIcon, "Pan View", self)
        self.menuView.addAction(self.panAction)

        redrawIcon = QIcon(":/icons/arrow-circle.png")
        self.redrawAction = QAction(redrawIcon, "Redraw", self)
        self.menuView.addAction(self.redrawAction)
        # rulerIcon = QIcon(":/icons/ruler.png")
        # self.rulerAction = QAction(rulerIcon, 'Ruler', self)
        # self.menuView.addAction(self.rulerAction)
        # delRulerIcon = QIcon.fromTheme('delete')
        # self.delRulerAction = QAction(delRulerIcon, 'Delete Rulers', self)
        # self.menuView.addAction(self.delRulerAction)
        self.menuView.addSeparator()
        # display options
        dispConfigIcon = QIcon(":/icons/resource-monitor.png")
        self.dispConfigAction = QAction(dispConfigIcon, "Display Config...", self)
        self.menuView.addAction(self.dispConfigAction)
        self.dispConfigAction.triggered.connect(self.dispConfDialog)

        selectConfigIcon = QIcon(":/icons/zone-select.png")
        self.selectConfigAction = QAction(selectConfigIcon, "Selection Config...", self)
        self.menuView.addAction(self.selectConfigAction)

        panZoomConfigIcon = QIcon(":/icons/selection-resize.png")
        self.panZoomConfigAction = QAction(
            panZoomConfigIcon, "Pan/Zoom Config...", self
        )
        self.menuView.addAction(self.panZoomConfigAction)

        undoIcon = QIcon(":/icons/arrow-circle-315-left.png")
        self.undoAction = QAction(undoIcon, "Undo", self)
        self.menuEdit.addAction(self.undoAction)

        redoIcon = QIcon(":/icons/arrow-circle-225.png")
        self.redoAction = QAction(redoIcon, "Redo", self)
        self.menuEdit.addAction(self.redoAction)

        yankIcon = QIcon(":/icons/node-insert.png")
        self.yankAction = QAction(yankIcon, "Yank", self)
        self.menuEdit.addAction(self.yankAction)

        pasteIcon = QIcon(":/icons/clipboard-paste.png")
        self.pasteAction = QAction(pasteIcon, "Paste", self)
        self.menuEdit.addAction(self.pasteAction)

        self.menuEdit.addSeparator()

        deleteIcon = QIcon(":/icons/node-delete.png")
        self.deleteAction = QAction(deleteIcon, "Delete", self)
        self.menuEdit.addAction(self.deleteAction)
        self.deleteAction.triggered.connect(self.deleteItemMethod)

        copyIcon = QIcon(":/icons/document-copy.png")
        self.copyAction = QAction(copyIcon, "Copy", self)
        self.menuEdit.addAction(self.copyAction)

        moveIcon = QIcon(":/icons/arrow-move.png")
        self.moveAction = QAction(moveIcon, "Move", self)
        self.menuEdit.addAction(self.moveAction)

        moveByIcon = QIcon(":/icons/arrow-transition.png")
        self.moveByAction = QAction(moveByIcon, "Move By ...", self)
        self.menuEdit.addAction(self.moveByAction)

        moveOriginIcon = QIcon(":/icons/arrow-skip.png")
        self.moveOriginAction = QAction(moveOriginIcon, "Move Origin", self)
        self.menuEdit.addAction(self.moveOriginAction)

        stretchIcon = QIcon(":/icons/fill.png")
        self.stretchAction = QAction(stretchIcon, "Stretch", self)
        self.menuEdit.addAction(self.stretchAction)

        rotateIcon = QIcon(":/icons/arrow-circle.png")
        self.rotateAction = QAction(rotateIcon, "Rotate...", self)
        self.menuEdit.addAction(self.rotateAction)

        scaleIcon = QIcon(":/icons/selection-resize.png")
        self.scaleAction = QAction(scaleIcon, "Scale...", self)
        self.menuEdit.addAction(self.scaleAction)
        self.menuEdit.addSeparator()

        netNameIcon = QIcon(":/icons/node-design.png")
        self.netNameAction = QAction(netNameIcon, "Net Name...", self)
        self.menuEdit.addAction(self.netNameAction)

        hierMenu = self.menuEdit.addMenu("Hierarchy")

        goUpIcon = QIcon(":/icons/arrow-step-out.png")
        self.goUpAction = QAction(goUpIcon, "Go Up   ↑", self)
        hierMenu.addAction(self.goUpAction)

        goDownIcon = QIcon(":/icons/arrow-step.png")
        self.goDownAction = QAction(goDownIcon, "Go Down ↓", self)
        hierMenu.addAction(self.goDownAction)

        selectMenu = self.menuEdit.addMenu("Select")
        self.selectAllIcon = QIcon(":/icons/node-select-all.png")
        self.selectAllAction = QAction(self.selectAllIcon, "Select All", self)
        selectMenu.addAction(self.selectAllAction)

        deselectAllIcon = QIcon(":/icons/node.png")
        self.deselectAllAction = QAction(deselectAllIcon, "Unselect All", self)
        selectMenu.addAction(self.deselectAllAction)

        propertyMenu = self.menuEdit.addMenu("Properties")

        objPropIcon = QIcon(":/icons/property-blue.png")
        self.objPropAction = QAction(objPropIcon, "Object Properties...", self)
        propertyMenu.addAction(self.objPropAction)

        viewPropIcon = QIcon(":/icons/property.png")
        self.viewPropAction = QAction(viewPropIcon, "Cellview Properties...", self)
        propertyMenu.addAction(self.viewPropAction)

        createInstIcon = QIcon(":/icons/block--plus.png")
        self.createInstAction = QAction(createInstIcon, "Create Instance...", self)
        self.menuCreate.addAction(self.createInstAction)

        createWireIcon = QIcon(":/icons/node-insert.png")
        self.createWireAction = QAction(createWireIcon, "Create Wire...", self)
        self.menuCreate.addAction(self.createWireAction)

        createBusIcon = QIcon(":/icons/node-select-all.png")
        self.createBusAction = QAction(createBusIcon, "Create Bus...", self)
        self.menuCreate.addAction(self.createBusAction)

        createLabelIcon = QIcon(":/icons/tag-label-yellow.png")
        self.createLabelAction = QAction(createLabelIcon, "Create Label...", self)
        self.menuCreate.addAction(self.createLabelAction)

        createPinIcon = QIcon(":/icons/pin--plus.png")
        self.createPinAction = QAction(createPinIcon, "Create Pin...", self)
        self.menuCreate.addAction(self.createPinAction)

        createSymbolIcon = QIcon(":/icons/application-block.png")
        self.createSymbolAction = QAction(createSymbolIcon, "Create Symbol...", self)
        self.menuCreate.addAction(self.createSymbolAction)

        viewCheckIcon = QIcon(":/icons/ui-check-box.png")
        self.viewCheckAction = QAction(viewCheckIcon, "Check CellView", self)
        self.menuCheck.addAction(self.viewCheckAction)

        viewErrorsIcon = QIcon(":/icons/report--exclamation.png")
        self.viewErrorsAction = QAction(viewErrorsIcon, "View Errors...", self)
        self.menuCheck.addAction(self.viewErrorsAction)

        deleteErrorsIcon = QIcon(":/icons/report--minus.png")
        self.deleteErrorsAction = QAction(deleteErrorsIcon, "Delete Errors...", self)
        self.menuCheck.addAction(self.deleteErrorsAction)

        netlistIcon = QIcon(":/icons/script-text.png")
        netlistAction = QAction(netlistIcon, "Create Netlist...", self)
        self.menuSimulation.addAction(netlistAction)

        simulateIcon = QIcon(":/icons/application-wave.png")
        self.simulateAction = QAction(simulateIcon, "Run RevEDA Sim GUI", self)
        self.menuSimulation.addAction(self.simulateAction)

        createLineIcon = QIcon(":/icons/layer-shape-line.png")
        self.createLineAction = QAction(createLineIcon, "Create Line...", self)

        createRectIcon = QIcon(":/icons/layer-shape.png")
        self.createRectAction = QAction(createRectIcon, "Create Rectangle...", self)

        createPolyIcon = QIcon(":/icons/layer-shape-polygon.png")
        self.createPolyAction = QAction(createPolyIcon, "Create Polygon...", self)

        createCircleIcon = QIcon(":/icons/layer-shape-ellipse.png")
        self.createCircleAction = QAction(createCircleIcon, "Create Circle...", self)

        createArcIcon = QIcon(":/icons/layer-shape-polyline.png")
        self.createArcAction = QAction(createArcIcon, "Create Arc...", self)

        createTextIcon = QIcon(":/icons/layer-shape-text.png")
        createLabelAction = QAction(createTextIcon, "Create Label...", self)

    def _createToolBars(self):
        # Create tools bar called "main toolbar"
        self.toolbar = QToolBar("Main Toolbar", self)
        # place toolbar at top
        self.addToolBar(self.toolbar)
        self.toolbar.addAction(self.printAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.undoAction)
        self.toolbar.addAction(self.redoAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.deleteAction)
        self.toolbar.addAction(self.moveAction)
        self.toolbar.addAction(self.copyAction)
        self.toolbar.addAction(self.stretchAction)
        # toolbar.addAction(self.rulerAction)
        # toolbar.addAction(self.delRulerAction)
        self.toolbar.addAction(self.objPropAction)
        self.toolbar.addAction(self.viewPropAction)
        self.toolbar.addSeparator()
        self.schematicToolbar = QToolBar("Schematic Toolbar", self)
        self.addToolBar(self.schematicToolbar)
        self.schematicToolbar.addAction(self.createInstAction)
        self.schematicToolbar.addAction(self.createWireAction)
        self.schematicToolbar.addAction(self.createBusAction)
        self.schematicToolbar.addAction(self.createPinAction)
        self.schematicToolbar.addAction(self.createLabelAction)
        self.schematicToolbar.addAction(self.createSymbolAction)
        self.schematicToolbar.addSeparator()
        self.schematicToolbar.addAction(self.viewCheckAction)

        self.symbolToolbar = QToolBar("Symbol Toolbar", self)
        self.addToolBar(self.symbolToolbar)
        self.symbolToolbar.addAction(self.createLineAction)
        self.symbolToolbar.addAction(self.createRectAction)
        self.symbolToolbar.addAction(self.createPolyAction)
        self.symbolToolbar.addAction(self.createCircleAction)
        self.symbolToolbar.addAction(self.createArcAction)
        self.symbolToolbar.addAction(self.createLabelAction)
        self.symbolToolbar.addAction(self.createPinAction)

    # self is the parent window, ie. the application
    def dispConfDialog(self):
        dcd = displayConfigDialog(self)

    def deleteItemMethod(self, s):
        self.centralWidget.scene.deleteItem = True


class schematicEditor(editorWindow):
    def __init__(self, file) -> None:
        super().__init__(file=file)
        self.setWindowTitle("Schematic Editor")
        self.symbolToolbar.setVisible(False)
        self.schematicToolbar.setVisible(True)
        self.createWireAction.triggered.connect(self.createWireClick)

    def createWireClick(self, s):
        self.centralWidget.scene.drawWire = True
        self.centralWidget.scene.selectItem = False
        if hasattr(self.centralWidget.scene, "start"):
            del self.centralWidget.scene.start


class symbolEditor(editorWindow):
    def __init__(self, file) -> None:
        super().__init__(file=file)
        self.setWindowTitle("Symbol Editor")
        self.schematicToolbar.setVisible(False)
        self.symbolToolbar.setVisible(True)
        self.checkCellAction.triggered.connect(self.checkSaveCell)
        self.createLineAction.triggered.connect(self.createLineClick)
        self.createRectAction.triggered.connect(self.createRectClick)
        self.createPolyAction.triggered.connect(self.createPolyClick)
        self.createArcAction.triggered.connect(self.createArcClick)
        self.createCircleAction.triggered.connect(self.createCircleClick)
        self.createLabelAction.triggered.connect(self.createLabelClick)
        self.createPinAction.triggered.connect(self.createPinClick)

    def checkSaveCell(self):
        self.centralWidget.scene.saveSymbolCell(self.file)

    def createRectClick(self, s):
        self.setDrawMode(False, False, False, True, False)

    def createLineClick(self, s):
        self.setDrawMode(False, False, False, False, True)

    def createPolyClick(self, s):
        pass

    def createArcClick(self, s):
        pass

    def createCircleClick(self, s):
        pass

    def createLabelClick(self, s):
        pass

    def createPinClick(self, s):
        print("Voila")
        createPinDlg = createPinDialog(self)
        if createPinDlg.exec() == QDialog.Accepted:
            self.centralWidget.scene.pinName = createPinDlg.pinName.text()
            self.setDrawMode(True, False, False, False, False)

    def setDrawMode(self, drawPin, selectItem, drawArc, drawRect, drawLine):
        self.centralWidget.scene.drawPin = drawPin
        self.centralWidget.scene.selectItem = selectItem
        self.centralWidget.scene.drawArc = drawArc  # draw arc
        self.centralWidget.scene.drawRect = drawRect
        self.centralWidget.scene.drawLine = drawLine
        if hasattr(self.centralWidget.scene, "start"):
            del self.centralWidget.scene.start

    def loadSymbol(self):
        self.centralWidget.scene.loadSymbol(self.file)


class createPinDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Pin")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.layout = QFormLayout()

        self.pinName = QLineEdit()
        self.pinName.setPlaceholderText("Pin Name")
        self.pinName.setToolTip("Enter pin name")
        self.layout.addRow(QLabel("Pin Name"), self.pinName)
        self.pinDir = QComboBox()
        self.pinDir.addItems(["Input", "Output", "Inout"])
        self.pinDir.setToolTip("Select pin direction")
        self.layout.addRow(QLabel("Pin Direction"), self.pinDir)
        self.pinType = QComboBox()
        self.pinType.addItems(
            ["Signal", "Ground", "Power", "Clock", "Digital", "Analog"]
        )
        self.pinType.setToolTip("Select pin type")
        self.layout.addRow(QLabel("Pin Type"), self.pinType)

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        self.show()


class displayConfigDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Display Options")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.layout = QVBoxLayout()
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        dispOptionsTabs = QTabWidget(self)
        # Grid Display Options tab
        displayTab = QWidget()
        # layout for displayTab
        vBox = QVBoxLayout()
        gridGrBox = QGroupBox("Display Grid")
        noGrid = QRadioButton("None")
        dotGrid = QRadioButton("Dots")
        dotGrid.setChecked(True)
        lineGrid = QRadioButton("Lines")
        gRLayout = QHBoxLayout()
        # create a logical group of grid option buttons
        gridButtonGroup = QButtonGroup()
        gridButtonGroup.addButton(noGrid)
        gridButtonGroup.addButton(dotGrid)
        gridButtonGroup.addButton(lineGrid)
        gRLayout.addWidget(noGrid)
        gRLayout.addWidget(dotGrid)
        gRLayout.addWidget(lineGrid)
        gRLayout.addStretch(1)
        gridGrBox.setLayout(gRLayout)
        #  gridGrBox.setLayout(gRLayout)
        # add to top row of display tab
        vBox.addWidget(gridGrBox)
        # create a form layout
        gridFormWidget = QWidget()
        fLayout = QFormLayout(self)
        self.majorGridEntry = QLineEdit()
        if self.parent.centralWidget.scene.gridMajor:
            self.majorGridEntry.setText(str(self.parent.centralWidget.scene.gridMajor))
        else:
            self.majorGridEntry.setText("10")
        self.minorGridEntry = QLineEdit()
        self.minorGridEntry.setText("5")
        fLayout.addRow("Major Grid:", self.majorGridEntry)
        fLayout.addRow("Minor Grid Spacing", self.minorGridEntry)
        gridFormWidget.setLayout(fLayout)
        vBox.addWidget(gridFormWidget)
        displayTab.setLayout(vBox)

        dispOptionsTabs.insertTab(0, displayTab, "Display Options")
        self.layout.addWidget(dispOptionsTabs)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        # need to change this later
        # self.setGeometry(300, 300, 300, 200)
        self.show()

    def accept(self):
        super().accept()
        self.parent.centralWidget.scene.gridMajor = int(self.majorGridEntry.text())
        self.parent.centralWidget.view.gridMajor = int(self.majorGridEntry.text())
        self.parent.centralWidget.scene.gridMinor = int(self.minorGridEntry.text())
        self.parent.centralWidget.scene.update()
        self.close()


class editorContainer(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.init_UI()

    def init_UI(self):
        self.scene = schematic_scene(self)
        self.view = schematic_view(self.scene, self)

        # layout statements, using a grid layout
        gLayout = QGridLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.view, 0, 0)
        # ratio of first column to second column is 5
        gLayout.setColumnStretch(0, 5)
        gLayout.setRowStretch(0, 6)
        self.setLayout(gLayout)


class schematic_scene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.gridMajor = 10
        self.drawWire = False  # flag to indicate if a wire is being drawn
        self.drawItem = False  # flag to indicate if an item is being drawn
        self.selectItem = True  # flag to indicate if an item is being selected
        self.drawLine = False
        self.drawArc = False  # flag to indicate if an arc is being drawn
        self.drawPin = False
        self.drawRect = False  # flag to indicate if a rectangle is being drawn
        self.objectStack = []  # stack of objects to be deleted

        self.wireLayer = cel.layer(
            name="wireLayer", color=QColor("aqua"), z=1, visible=True
        )
        self.symbolLayer = cel.layer(
            name="symbolLayer", color=QColor("green"), z=1, visible=True
        )
        self.guideLineLayer = cel.layer(
            name="guideLineLayer", color=QColor("white"), z=1, visible=True
        )
        self.selectedWireLayer = cel.layer(
            name="selectedWireLayer", color=QColor("red"), z=1, visible=True
        )
        self.pinLayer = cel.layer(
            name="pinLayer", color=QColor("darkRed"), z=2, visible=True
        )
        self.wirePen = QPen(self.wireLayer.color, 2)
        self.symbolPen = QPen(self.symbolLayer.color, 3)
        self.selectedWirePen = QPen(self.selectedWireLayer.color, 2)
        self.pinPen = QPen(self.pinLayer.color, 2)

    def mousePressEvent(self, mouse_event):
        super().mousePressEvent(mouse_event)
        if self.selectItem == True:
            self.selectedItem = self.itemAt(mouse_event.scenePos(), QTransform())
            if self.selectedItem != None:
                print("I found something")
        else:
            self.startPosition = mouse_event.scenePos().toPoint()
            if hasattr(self, "start") == False:
                self.start = QPoint(
                    self.snapGrid(self.startPosition.x(), self.gridMajor),
                    self.snapGrid(self.startPosition.y(), self.gridMajor),
                )

    def mouseMoveEvent(self, mouse_event):
        self.snap2Grid(mouse_event)

        pen = QPen(self.guideLineLayer.color, 1)
        pen.setStyle(Qt.DashLine)
        if hasattr(self, "draftItem"):
            self.removeItem(self.draftItem)  # remove old guide line
            del self.draftItem
        if self.drawWire == True and hasattr(self, "start") == True:
            self.draftItem = QGraphicsLineItem(QLine(self.start, self.current))
            self.draftItem.setPen(pen)
            self.addItem(self.draftItem)
        elif self.drawLine == True and hasattr(self, "start") == True:
            self.draftItem = QGraphicsLineItem(QLine(self.start, self.current))
            self.draftItem.setPen(pen)
            self.addItem(self.draftItem)
        elif self.drawRect == True and hasattr(self, "start") == True:
            self.draftItem = QGraphicsRectItem(QRectF(self.start, self.current))
            self.draftItem.setPen(pen)
            self.addItem(self.draftItem)
        elif self.drawPin == True and hasattr(self, "start") == True:
            self.draftItem = QGraphicsRectItem(
                QRectF(self.current.x() - 5, self.current.y() - 5, 10, 10)
            )
            self.draftItem.setPen(pen)
            self.addItem(self.draftItem)
        super().mouseMoveEvent(mouse_event)

    def snap2Grid(self, mouse_event):
        self.current = mouse_event.scenePos().toPoint()
        self.current /= self.gridMajor
        self.current *= self.gridMajor

    def mouseReleaseEvent(self, mouse_event):
        super().mouseReleaseEvent(mouse_event)
        if hasattr(self, "draftItem"):
            self.removeItem(self.draftItem)
            del self.draftItem
        if self.drawWire == True:
            self.lineDraw(self.wirePen)
            self.drawWire = False
        elif self.drawLine == True:
            self.lineDraw(self.symbolPen)
            self.drawLine = False
        elif self.drawRect == True:
            self.rectDraw()
        elif self.drawPin == True:
            self.pinDraw(self.pinPen)
            self.drawPin = False  # reset flag

        self.start = self.current  # reset start position

    def rectDraw(self):
        rect = rectItem(QRect(self.start, self.current), self.symbolPen)
        self.addItem(rect)
        self.drawRect = False
        self.objectStack.append(rect)

    def lineDraw(self, pen):
        line = lineItem(self.start, self.current, pen)
        self.addItem(line)
        self.objectStack.append(line)

    def pinDraw(self, pen):
        pin = pinItem(self.current, self.pinName, pen)
        self.addItem(pin)
        self.objectStack.append(pin)
        del self.pinName

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_Escape:
            self.drawWire = False  # turn off wire select mode
            self.drawItem = False  # turn off drawing mode when escape is pressed
            self.drawRect = False
            if hasattr(self, "draftItem"):
                self.removeItem(self.draftItem)
            self.selectItem = True
        elif key_event.key() == Qt.Key_Delete:
            if hasattr(self, "selectedItem"):
                self.removeItem(self.selectedItem)
                del self.selectedItem
                self.selectItem = True
        elif key_event.key() == Qt.Key_U:

            if type(self.objectStack[-1]) == list:
                for item in self.objectStack[-1]:
                    self.removeItem(item)
                    del item
            else:
                self.removeItem(self.objectStack[-1])
                del self.objectStack[-1]
            self.objectStack.pop()
        elif key_event.key() == Qt.Key_Delete:
            if hasattr(self, "selectedItem"):
                self.removeItem(self.selectedItem)
                del self.selectedItem
                self.selectItem = True
        super().keyPressEvent(key_event)

    def snapGrid(self, number, base):
        return base * int(round(number / base))

    def loadSymbol(self, file):
        pass
        with open(file, "r") as f:
            fsonLoad = f.read()
            items = json.loads(fsonLoad)
        for item in items:
            if item["type"] == "rect":
                rectPaint = QRect(
                        item["rect"][0],
                        item["rect"][1],
                        item["rect"][2],
                        item["rect"][3],
                    )
                rectPaint.setTopLeft(QPoint(item["loc"][0], item["loc"][1]))
                rect = rectItem(
                    rectPaint,
                    QPen(
                        QColor(
                            item["color"][0],
                            item["color"][1],
                            item["color"][2],
                            item["color"][3],
                        ),
                        item["width"],
                    ),
                )
                self.addItem(rect)
                self.objectStack.append(rect)
        # if item['type'] == 'line':
        #     line = lineItem(QPoint(item['start'][0],item['start'][1]),QPoint(item['end'][0],item['end'][1]),QPen(QColor(item['color']),item['width']))
        #     self.addItem(line)
        #     self.objectStack.append(line)
        # elif item['type'] == 'rect':
        #     rect = rectItem(QRect(item['start'][0],item['start'][1],item['end'][0],item['end'][1]),QPen(QColor(item['color']),item['width']))
        #     self.addItem(rect)
        #     self.objectStack.append(rect)
        # elif item['type'] == 'pin':
        #     pin = pinItem(QPoint(item['x'],item['y']),item['name'],QPen(QColor(item['color']),item['width']))
        #     self.addItem(pin)
        #     self.objectStack.append(pin)
        # elif item['type'] == 'wire':
        #     wire = wireItem(QPoint(item['start'][0],item['start'][1]),QPoint(item['end'][0],item['end'][1]),QPen(QColor(item['color']),item['width']))
        #     self.addItem(wire)
        #     self.objectStack.append(wire)

    def saveSymbolCell(self, fileName):

        self.sceneR = self.sceneRect()

        items = self.items(self.sceneR)
        with open(fileName, "w") as f:
            json.dump(items, f, cls=complexEncoder, indent=4)


class complexEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, rectItem):
            itemDict = {
                "type": "rect",
                "rect": item.__dict__["rect"].getRect(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "loc": item.__dict__["loc"].toTuple(),
            }
            return itemDict
        else:
            return super().default(item)


class rectItem(QGraphicsItem):
    def __init__(self, rect, pen):
        super().__init__()
        self.rect = rect
        self.pen = pen
        self.loc = self.rect.topLeft()
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)

    def boundingRect(self):
        return QRectF(self.rect)

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.drawRect(self.rect)

    def mouseMoveEvent(self, event) -> None:
        self.loc = self.rect.topLeft()
        super().mouseMoveEvent(event)


class lineItem(QGraphicsItem):
    def __init__(self, start, current, pen):
        super().__init__()
        self.current = current
        self.start = start
        self.pen = pen
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)

    def boundingRect(self):
        return QRectF(
            self.start.x(), self.start.y(), self.current.x(), self.current.y()
        )

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        if self.start.x() != self.current.x():
            if self.start.y() != self.current.y():
                midPoint = QPoint(self.current.x(), self.start.y())
                painter.drawLine(self.start, midPoint)
                painter.drawLine(midPoint, self.current)
            else:
                painter.drawLine(self.start, self.current)
        else:
            if self.start.y() != self.current.y():
                painter.drawLine(self.start, self.current)
            else:
                painter.drawPoint(self.start)

    def pos(self):
        return self.start


class pinItem(QGraphicsItem):
    def __init__(self, pos, name, pen):
        super().__init__()
        self.pos = pos
        self.pen = pen
        self.name = name
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.rect = QRectF(self.pos.x() - 5, self.pos.y() - 5, 10, 10)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.setBrush(self.pen.color())
        painter.drawRect(self.rect)
        painter.setFont(QFont("Arial", 10))
        textLoc = QPoint(self.pos.x() - 2.5, self.pos.y() - 10)
        painter.drawText(textLoc, self.name)

    def pos(self):
        return self.pos


class schematic_view(QGraphicsView):
    def __init__(self, scene, parent):
        super().__init__(scene, parent)
        self.parent = parent
        self.scene = scene
        self.gridMajor = self.scene.gridMajor

        self.init_UI()

    def init_UI(self):
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.CacheBackground = True
        self.standardCursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.standardCursor)  # set cursor to standard arrow
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setMouseTracking(True)
        # self.setDragMode(QGraphicsView.RubberBandDrag)

    def wheelEvent(self, mouse_event):
        factor = 1.1
        if mouse_event.angleDelta().y() < 0:
            factor = 0.9
        view_pos = QPoint(
            int(mouse_event.globalPosition().x()), int(mouse_event.globalPosition().y())
        )
        scene_pos = self.mapToScene(view_pos)
        self.centerOn(scene_pos)
        self.scale(factor, factor)
        delta = self.mapToScene(view_pos) - self.mapToScene(
            self.viewport().rect().center()
        )
        self.centerOn(scene_pos - delta)
        super().wheelEvent(mouse_event)

    def snapGrid(self, number, base):
        return base * int(math.floor(number / base))

    def drawBackground(self, painter, rect):
        rectCoord = rect.getRect()
        painter.fillRect(rect, QColor("black"))
        painter.setPen(QColor("white"))
        grid_x_start = math.ceil(rectCoord[0] / self.gridMajor) * self.gridMajor
        grid_y_start = math.ceil(rectCoord[1] / self.gridMajor) * self.gridMajor
        num_x_points = math.floor(rectCoord[2] / self.gridMajor)
        num_y_points = math.floor(rectCoord[3] / self.gridMajor)
        for i in range(int(num_x_points)):  # rect width
            for j in range(int(num_y_points)):  # rect length
                painter.drawPoint(
                    grid_x_start + i * self.gridMajor, grid_y_start + j * self.gridMajor
                )
        super().drawBackground(painter, rect)


class libraryPathEditorDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.libraryEditRowList = []
        self.libraryDict = self.parent.libraryDict
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Library Path Editor")
        mainLayout = QVBoxLayout()
        mainLayout.setSpacing(10)
        self.entriesLayout = QVBoxLayout()  # layout for all the entries
        labelLayout = QHBoxLayout()
        labelLayout.addWidget(QLabel("Library Name"))
        labelLayout.addWidget(QLabel("Library Path"))
        mainLayout.addLayout(labelLayout)  # add label layout to main layout
        for key in self.libraryDict.keys():
            self.libraryEditRowList.append(libraryEditRow(self))
            self.entriesLayout.addWidget(self.libraryEditRowList[-1])
            self.libraryEditRowList[-1].libraryNameEdit.setText(key)
            self.libraryEditRowList[-1].libraryPathEdit.setText(
                str(self.libraryDict[key])
            )
            self.libraryEditRowList[-1].libraryPathEdit.textChanged.connect(self.addRow)
        mainLayout.addLayout(self.entriesLayout)
        self.libraryEditRowList.append(libraryEditRow(self))
        self.entriesLayout.addWidget(self.libraryEditRowList[-1])
        self.libraryEditRowList[-1].libraryPathEdit.textChanged.connect(self.addRow)
        mainLayout.addLayout(self.entriesLayout)
        applyButton = QPushButton("Apply")
        applyButton.clicked.connect(self.apply)
        applyButton.setDefault(False)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.cancel)
        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(applyButton, QDialogButtonBox.ActionRole)
        buttonBox.addButton(cancelButton, QDialogButtonBox.ActionRole)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    def apply(self):
        self.reworkLibraryModel()

        self.close()

    def reworkLibraryModel(self):
        libPath = Path.cwd().joinpath("library.yaml")
        tempLibDict = {}
        for item in self.libraryEditRowList:
            if item.libraryNameEdit.text() != "":  # check if the key is empty
                tempLibDict[item.libraryNameEdit.text()] = item.libraryPathEdit.text()
        try:
            with libPath.open(mode="w") as f:
                scb.writeLibDefFile(tempLibDict, libPath)
        except IOError:
            print(f"Cannot save library definitions in {libPath}")
        # self.parent.centralWidget.treeView.addLibrary()
        self.libraryDict = {}  # now empty the library dict
        for key, value in tempLibDict.items():
            self.libraryDict[key] = Path(
                value
            )  # redefine  libraryDict with pathlib paths.
        self.parent.libraryDict = self.libraryDict  # propogate changes up to mainWindow
        self.parent.libBrowserCont.designView.libraryModel.clear()
        self.parent.libBrowserCont.designView.initModel()
        self.parent.libBrowserCont.designView.setModel(
            self.parent.libBrowserCont.designView.libraryModel
        )
        for designPath in self.libraryDict.values():  # type: Path
            self.parent.libBrowserCont.designView.addLibrary(
                designPath, self.parent.libBrowserCont.designView.parentItem
            )

    def cancel(self):
        self.close()

    def addRow(self):
        if self.libraryEditRowList[-1].libraryPathEdit.text() != "":
            self.libraryEditRowList.append(libraryEditRow(self))
            self.entriesLayout.addWidget(self.libraryEditRowList[-1])
            self.libraryEditRowList[-1].libraryPathEdit.textChanged.connect(self.addRow)


class libraryEditRow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_UI()

    def init_UI(self):
        self.layout = QHBoxLayout()
        self.layout.setSpacing(10)
        self.libraryNameEdit = libraryNameEditC(self)
        self.libraryPathEdit = libraryPathEditC(self)
        self.layout.addWidget(self.libraryNameEdit)
        self.layout.addWidget(self.libraryPathEdit)
        self.setLayout(self.layout)


class libraryNameEditC(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.fileDialog = QFileDialog()
        self.fileDialog.setFileMode(QFileDialog.Directory)
        self.init_UI()

    def init_UI(self):
        self.setPlaceholderText("Library Name")
        self.setMaximumWidth(250)
        self.setFixedWidth(200)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction("Remove", self.removeRow)
        menu.addAction("Add Library...", self.addLibrary)
        menu.addAction("Library Info...", self.libInfo)
        menu.exec(event.globalPos())

    def addLibrary(self):
        self.fileDialog.exec()
        if self.fileDialog.selectedFiles():
            self.selectedDirectory = QDir(self.fileDialog.selectedFiles()[0])
            self.setText(self.selectedDirectory.dirName())
            self.parent.libraryPathEdit.setText(self.selectedDirectory.absolutePath())

    def removeRow(self):
        self.parent.deleteLater()
        self.parent.parent.libraryEditRowList.remove(self.parent)

    def libInfo(self):
        pass


class libraryPathEditC(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_UI()

    def init_UI(self):
        self.setPlaceholderText("Library Path                ")
        self.setMaximumWidth(600)
        self.setFixedWidth(500)


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
