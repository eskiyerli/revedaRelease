import json
import pathlib
import shutil
import sys
from contextlib import redirect_stderr, redirect_stdout

# from hashlib import new
from pathlib import Path

# import numpy as np
from PySide6.QtCore import (
    QDir,
    QLine,
    QRect,
    QRectF,
)
from PySide6.QtGui import (
    QAction,
    QKeySequence,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QBrush,
    QFontMetrics,
    QStandardItemModel,
    QTransform,
    QCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
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

import circuitElements as cel
import propertyDialogues as pdlg
import pythonConsole as pcon
import schBackEnd as scb  # import the backend
import shape as shp  # import the shapes
from Point import *
from Vector import *
import resources


# from threading import Thread


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
            self.schematicWindow = schematicEditor(
                file=self.selectedItem.data(Qt.UserRole + 2)
            )
            self.schematicWindow.show()
        elif self.selectedItem.text() == "symbol":
            self.symbolWindow = symbolEditor(
                file=self.selectedItem.data(Qt.UserRole + 2)
            )
            self.symbolWindow.loadSymbol()
            self.symbolWindow.show()

    def copyView(self):
        dlg = copyViewDialog(self, self.libraryModel, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            if self.selectedItem.data(Qt.UserRole + 1) == "view":
                viewPath = self.selectedItem.data(Qt.UserRole + 2)
                newViewPath = dlg.selectedLibPath.joinpath(
                    dlg.selectedCell, dlg.selectedView + ".json"
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
        self.browserMenubar = self.menuBar()
        self.libraryMenu = self.browserMenubar.addMenu("&Library")

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
            if view.suffix == ".json"
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
    def __init__(self, file: pathlib.Path):  # file is a pathlib.Path object
        super().__init__()
        self.file = file
        self._createActions()
        self._createTriggers()
        self._createShortcuts()
        self.init_UI()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = editorContainer(self)
        self.setCentralWidget(self.centralW)
        self.statusLine = self.statusBar()

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

    def _createActions(self):
        checkCellIcon = QIcon(":/icons/document-task.png")
        self.checkCellAction = QAction(checkCellIcon, "Check-Save", self)

        self.readOnlyCellIcon = QIcon(":/icons/lock.png")
        self.readOnlyCellAction = QAction(self.readOnlyCellIcon, "Make Read Only", self)

        printIcon = QIcon(":/icons/printer--arrow.png")
        self.printAction = QAction(printIcon, "Print...", self)

        exportImageIcon = QIcon(":/icons/image-export.png")
        self.exportImageAction = QAction(exportImageIcon, "Export...", self)

        exitIcon = QIcon(":/icons/external.png")
        self.exitAction = QAction(exitIcon, "Close Window", self)
        self.exitAction.setShortcut("Ctrl+Q")

        fitIcon = QIcon(":/icons/zone.png")
        self.fitAction = QAction(fitIcon, "Fit to Window", self)

        zoomInIcon = QIcon(":/icons/zone-resize.png")
        self.zoomInAction = QAction(zoomInIcon, "Zoom In", self)

        zoomOutIcon = QIcon(":/icons/zone-resize-actual.png")
        self.zoomOutAction = QAction(zoomOutIcon, "Zoom Out", self)

        panIcon = QIcon(":/icons/zone--arrow.png")
        self.panAction = QAction(panIcon, "Pan View", self)

        redrawIcon = QIcon(":/icons/arrow-circle.png")
        self.redrawAction = QAction(redrawIcon, "Redraw", self)

        # rulerIcon = QIcon(":/icons/ruler.png")
        # self.rulerAction = QAction(rulerIcon, 'Ruler', self)
        # self.menuView.addAction(self.rulerAction)
        # delRulerIcon = QIcon.fromTheme('delete')
        # self.delRulerAction = QAction(delRulerIcon, 'Delete Rulers', self)
        # self.menuView.addAction(self.delRulerAction)

        # display options
        dispConfigIcon = QIcon(":/icons/resource-monitor.png")
        self.dispConfigAction = QAction(dispConfigIcon, "Display Config...", self)

        selectConfigIcon = QIcon(":/icons/zone-select.png")
        self.selectConfigAction = QAction(selectConfigIcon, "Selection Config...", self)

        panZoomConfigIcon = QIcon(":/icons/selection-resize.png")
        self.panZoomConfigAction = QAction(
            panZoomConfigIcon, "Pan/Zoom Config...", self
        )

        undoIcon = QIcon(":/icons/arrow-circle-315-left.png")
        self.undoAction = QAction(undoIcon, "Undo", self)

        redoIcon = QIcon(":/icons/arrow-circle-225.png")
        self.redoAction = QAction(redoIcon, "Redo", self)

        yankIcon = QIcon(":/icons/node-insert.png")
        self.yankAction = QAction(yankIcon, "Yank", self)

        pasteIcon = QIcon(":/icons/clipboard-paste.png")
        self.pasteAction = QAction(pasteIcon, "Paste", self)

        deleteIcon = QIcon(":/icons/node-delete.png")
        self.deleteAction = QAction(deleteIcon, "Delete", self)

        copyIcon = QIcon(":/icons/document-copy.png")
        self.copyAction = QAction(copyIcon, "Copy", self)

        moveIcon = QIcon(":/icons/arrow-move.png")
        self.moveAction = QAction(moveIcon, "Move", self)

        moveByIcon = QIcon(":/icons/arrow-transition.png")
        self.moveByAction = QAction(moveByIcon, "Move By ...", self)

        moveOriginIcon = QIcon(":/icons/arrow-skip.png")
        self.moveOriginAction = QAction(moveOriginIcon, "Move Origin", self)

        stretchIcon = QIcon(":/icons/fill.png")
        self.stretchAction = QAction(stretchIcon, "Stretch", self)

        rotateIcon = QIcon(":/icons/arrow-circle.png")
        self.rotateAction = QAction(rotateIcon, "Rotate...", self)

        scaleIcon = QIcon(":/icons/selection-resize.png")
        self.scaleAction = QAction(scaleIcon, "Scale...", self)

        netNameIcon = QIcon(":/icons/node-design.png")
        self.netNameAction = QAction(netNameIcon, "Net Name...", self)

        # create label action but do not add to any menu.
        createLabelIcon = QIcon(":/icons/tag-label-yellow.png")
        self.createLabelAction = QAction(createLabelIcon, "Create Label...", self)

        createPinIcon = QIcon(":/icons/pin--plus.png")
        self.createPinAction = QAction(createPinIcon, "Create Pin...", self)

        goUpIcon = QIcon(":/icons/arrow-step-out.png")
        self.goUpAction = QAction(goUpIcon, "Go Up   ↑", self)

        goDownIcon = QIcon(":/icons/arrow-step.png")
        self.goDownAction = QAction(goDownIcon, "Go Down ↓", self)

        self.selectAllIcon = QIcon(":/icons/node-select-all.png")
        self.selectAllAction = QAction(self.selectAllIcon, "Select All", self)

        deselectAllIcon = QIcon(":/icons/node.png")
        self.deselectAllAction = QAction(deselectAllIcon, "Unselect All", self)

        objPropIcon = QIcon(":/icons/property-blue.png")
        self.objPropAction = QAction(objPropIcon, "Object Properties...", self)

        viewPropIcon = QIcon(":/icons/property.png")
        self.viewPropAction = QAction(viewPropIcon, "Cellview Properties...", self)

        viewCheckIcon = QIcon(":/icons/ui-check-box.png")
        self.viewCheckAction = QAction(viewCheckIcon, "Check CellView", self)

        viewErrorsIcon = QIcon(":/icons/report--exclamation.png")
        self.viewErrorsAction = QAction(viewErrorsIcon, "View Errors...", self)

        deleteErrorsIcon = QIcon(":/icons/report--minus.png")
        self.deleteErrorsAction = QAction(deleteErrorsIcon, "Delete Errors...", self)

        netlistIcon = QIcon(":/icons/script-text.png")
        self.netlistAction = QAction(netlistIcon, "Create Netlist...", self)

        simulateIcon = QIcon(":/icons/application-wave.png")
        self.simulateAction = QAction(simulateIcon, "Run RevEDA Sim GUI", self)

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

        createInstIcon = QIcon(":/icons/block--plus.png")
        self.createInstAction = QAction(createInstIcon, "Create Instance...", self)

        createWireIcon = QIcon(":/icons/node-insert.png")
        self.createWireAction = QAction(createWireIcon, "Create Wire...", self)

        createBusIcon = QIcon(":/icons/node-select-all.png")
        self.createBusAction = QAction(createBusIcon, "Create Bus...", self)

        createLabelIcon = QIcon(":/icons/tag-label-yellow.png")
        self.createLabelAction = QAction(createLabelIcon, "Create Label...", self)

        createPinIcon = QIcon(":/icons/pin--plus.png")
        self.createPinAction = QAction(createPinIcon, "Create Pin...", self)

        createSymbolIcon = QIcon(":/icons/application-block.png")
        self.createSymbolAction = QAction(createSymbolIcon, "Create Symbol...", self)

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
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.fitAction)
        self.toolbar.addAction(self.zoomInAction)
        self.toolbar.addAction(self.zoomOutAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.objPropAction)

    def _addActions(self):
        # file menu
        self.menuFile.addAction(self.checkCellAction)
        self.menuFile.addAction(self.readOnlyCellAction)
        self.menuFile.addAction(self.printAction)
        self.menuFile.addAction(self.exportImageAction)
        self.menuFile.addAction(self.exitAction)
        # view menu
        self.menuView.addAction(self.fitAction)
        self.menuView.addAction(self.zoomInAction)
        self.menuView.addAction(self.zoomOutAction)
        self.menuView.addAction(self.panAction)
        self.menuView.addAction(self.redrawAction)
        self.menuView.addAction(self.dispConfigAction)
        self.menuView.addAction(self.selectConfigAction)
        self.menuView.addAction(self.panZoomConfigAction)
        # edit menu
        self.menuEdit.addAction(self.undoAction)
        self.menuEdit.addAction(self.redoAction)
        self.menuEdit.addAction(self.yankAction)
        self.menuEdit.addAction(self.pasteAction)
        self.menuEdit.addAction(self.deleteAction)
        self.menuEdit.addAction(self.copyAction)
        self.menuEdit.addAction(self.moveAction)
        self.menuEdit.addAction(self.moveByAction)
        self.menuEdit.addAction(self.moveOriginAction)
        self.menuEdit.addAction(self.stretchAction)
        self.menuEdit.addAction(self.rotateAction)

        self.menuCheck.addAction(self.viewCheckAction)

    def _createTriggers(self):
        self.exitAction.triggered.connect(self.closeWindow)
        self.fitAction.triggered.connect(self.fitToWindow)
        self.zoomInAction.triggered.connect(self.zoomIn)
        self.zoomOutAction.triggered.connect(self.zoomOut)
        self.dispConfigAction.triggered.connect(self.dispConfDialog)

    def _createShortcuts(self):
        self.redoAction.setShortcut("Shift+U")
        self.undoAction.setShortcut("U")
        self.objPropAction.setShortcut(Qt.Key_Q)
        self.copyAction.setShortcut("C")
        self.deleteAction.setShortcut(QKeySequence.Delete)

    def dispConfDialog(self):
        dcd = displayConfigDialog(self)

    # def deleteItemMethod(self, s):
    #     self.centralW.scene.itemDelete = True

    def fitToWindow(self):
        self.centralW.view.fitToView()

    def zoomIn(self):
        self.centralW.view.scale(1.25, 1.25)

    def zoomOut(self):
        self.centralW.view.scale(0.8, 0.8)

    def closeWindow(self):
        self.close()

    def _createMenu(self):
        pass


class schematicEditor(editorWindow):
    def __init__(self, file) -> None:
        super().__init__(file=file)
        self.setWindowTitle("Schematic Editor")
        self.setWindowIcon(QIcon(":/icons/layer-shape.png"))

    def _createTriggers(self):
        super()._createTriggers()

        self.createWireAction.triggered.connect(self.createWireClick)

    def _createMenuBar(self):
        super()._createMenuBar()
        self.menuSimulation = self.menuBar.addMenu("&Simulation")
        self.menuHelp = self.menuBar.addMenu("&Help")
        self._addActions()

    def _addActions(self):
        super()._addActions()
        # edit menu

        self.menuEdit.addAction(self.netNameAction)

        self.propertyMenu = self.menuEdit.addMenu("Properties")
        self.propertyMenu.addAction(self.objPropAction)
        self.propertyMenu.addAction(self.viewPropAction)

        self.selectMenu = self.menuEdit.addMenu("Select")
        self.selectMenu.addAction(self.selectAllAction)
        self.selectMenu.addAction(self.deselectAllAction)

        # hierarchy submenu
        self.hierMenu = self.menuEdit.addMenu("Hierarchy")
        self.hierMenu.addAction(self.goUpAction)
        self.hierMenu.addAction(self.goDownAction)

        # create menu
        self.menuCreate.addAction(self.createInstAction)
        self.menuCreate.addAction(self.createWireAction)
        self.menuCreate.addAction(self.createBusAction)
        self.menuCreate.addAction(self.createLabelAction)
        self.menuCreate.addAction(self.createPinAction)
        self.menuCreate.addAction(self.createSymbolAction)

        # check menu
        self.menuCheck.addAction(self.viewErrorsAction)
        self.menuCheck.addAction(self.deleteErrorsAction)

        self.menuSimulation.addAction(self.netlistAction)
        self.menuSimulation.addAction(self.simulateAction)

    def _createToolBars(self):
        super()._createToolBars()
        # toolbar.addAction(self.rulerAction)
        # toolbar.addAction(self.delRulerAction)
        self.toolbar.addAction(self.objPropAction)
        self.toolbar.addAction(self.viewPropAction)

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

    def createWireClick(self, s):
        pass


class symbolEditor(editorWindow):
    def __init__(self, file):
        super().__init__(file=file)
        self.file = file
        self.setWindowTitle(f"Symbol Editor - {file.stem}")
        self._symbolActions()

    def init_UI(self):
        return super().init_UI()

    def _createActions(self):
        super()._createActions()

    def _createShortcuts(self):
        super()._createShortcuts()
        self.stretchAction.setShortcut("M")

    def _createMenuBar(self):
        super()._createMenuBar()
        self.menuHelp = self.menuBar.addMenu("&Help")
        self._addActions()

    def _createToolBars(self):  # redefine the toolbar in the editorWindow class
        super()._createToolBars()
        self.symbolToolbar = QToolBar("Symbol Toolbar", self)
        self.addToolBar(self.symbolToolbar)
        self.symbolToolbar.addAction(self.createLineAction)
        self.symbolToolbar.addAction(self.createRectAction)
        self.symbolToolbar.addAction(self.createPolyAction)
        self.symbolToolbar.addAction(self.createCircleAction)
        self.symbolToolbar.addAction(self.createArcAction)
        self.symbolToolbar.addAction(self.createLabelAction)
        self.symbolToolbar.addAction(self.createPinAction)

    def _addActions(self):
        super()._addActions()
        self.menuEdit.addAction(self.stretchAction)
        self.menuEdit.addAction(self.viewPropAction)
        self.menuCreate.addAction(self.createLineAction)
        self.menuCreate.addAction(self.createRectAction)
        self.menuCreate.addAction(self.createPolyAction)
        self.menuCreate.addAction(self.createCircleAction)
        self.menuCreate.addAction(self.createArcAction)
        self.menuCreate.addAction(self.createLabelAction)
        self.menuCreate.addAction(self.createPinAction)

    def _createTriggers(self):

        self.checkCellAction.triggered.connect(self.checkSaveCell)
        self.createLineAction.triggered.connect(self.createLineClick)
        self.createRectAction.triggered.connect(self.createRectClick)
        self.createPolyAction.triggered.connect(self.createPolyClick)
        self.createArcAction.triggered.connect(self.createArcClick)
        self.createCircleAction.triggered.connect(self.createCircleClick)
        self.createLabelAction.triggered.connect(self.createSymbolLabelDialogue)
        self.createPinAction.triggered.connect(self.createPinClick)
        self.objPropAction.triggered.connect(self.objPropClick)
        self.copyAction.triggered.connect(self.copyClick)
        self.redoAction.triggered.connect(self.redoClick)
        self.undoAction.triggered.connect(self.undoClick)
        self.deleteAction.triggered.connect(self.deleteClick)
        self.stretchAction.triggered.connect(self.stretchClick)
        self.viewPropAction.triggered.connect(self.viewPropClick)
        super()._createTriggers()

    def _symbolActions(self):
        self.centralW.scene.symbolContextMenu.addAction(self.copyAction)
        self.centralW.scene.symbolContextMenu.addAction(self.moveAction)
        self.centralW.scene.symbolContextMenu.addAction(self.stretchAction)
        self.centralW.scene.symbolContextMenu.addAction(self.deleteAction)
        self.centralW.scene.symbolContextMenu.addAction(self.objPropAction)

    def objPropClick(self):
        print("objPropClick")
        self.centralW.scene.itemProperties()

    def checkSaveCell(self):
        self.centralW.scene.saveSymbolCell(self.file)

    def createRectClick(self, s):
        self.setDrawMode(False, False, False, True, False, False)

    def createLineClick(self, s):
        self.setDrawMode(False, False, False, False, True, False)

    def createPolyClick(self, s):
        pass

    def createArcClick(self, s):
        pass

    def createCircleClick(self, s):
        pass

    def createPinClick(self, s):
        createPinDlg = pdlg.createPinDialog(self)
        if createPinDlg.exec() == QDialog.Accepted:
            self.centralW.scene.pinName = createPinDlg.pinName.text()
            self.centralW.scene.pinType = createPinDlg.pinType.currentText()
            self.centralW.scene.pinDir = createPinDlg.pinDir.currentText()
            self.setDrawMode(True, False, False, False, False, False)

    def undoClick(self, s):
        self.centralW.scene.undoLastItem()

    def redoClick(self, s):
        self.centralW.scene.redoLastItem()

    def deleteClick(self, s):
        self.centralW.scene.deleteSelectedItem()

    def copyClick(self, s):
        self.centralW.scene.copySelectedItem()

    def stretchClick(self, s):
        self.centralW.scene.stretchSelectedItem()

    def viewPropClick(self, s):
        self.centralW.scene.viewSymbolProperties()

    def setDrawMode(
        self,
        drawPin: bool,
        selectItem: bool,
        drawArc: bool,
        drawRect: bool,
        drawLine: bool,
        addLabel: bool,
    ):
        """
        Sets the drawing mode in the symbol editor.
        """
        self.centralW.scene.drawPin = drawPin
        self.centralW.scene.selectItem = selectItem
        self.centralW.scene.drawArc = drawArc  # draw arc
        self.centralW.scene.drawRect = drawRect
        self.centralW.scene.drawLine = drawLine
        self.centralW.scene.addLabel = addLabel
        if hasattr(self.centralW.scene, "start"):
            del self.centralW.scene.start

    def loadSymbol(self):
        """
        symbol is loaded to the scene.
        """
        self.centralW.scene.loadSymbol(self.file)

    def createSymbolLabelDialogue(self):
        createLabelDlg = pdlg.createSymbolLabelDialog(self)
        if createLabelDlg.exec() == QDialog.Accepted:
            self.setDrawMode(False, False, False, False, False, True)
            # directly setting scene class attributes here to pass the information.
            self.centralW.scene.labelName = createLabelDlg.labelNameEdit.text()
            self.centralW.scene.labelHeight = (
                createLabelDlg.labelHeightEdit.text().strip()
            )
            self.centralW.scene.labelAlignment = (
                createLabelDlg.labelAlignCombo.currentText()
            )
            self.centralW.scene.labelOrient = (
                createLabelDlg.labelOrientCombo.currentText()
            )
            self.centralW.scene.labelUse = createLabelDlg.labelUseCombo.currentText()
            self.centralW.scene.labelType = "Normal"  # default button
            if createLabelDlg.normalType.isChecked():
                self.centralW.scene.labelType = "Normal"
            elif createLabelDlg.NLPType.isChecked():
                self.centralW.scene.labelType = "NLPLabel"
            elif createLabelDlg.pyLType.isChecked():
                self.centralW.scene.labelType = "PyLabel"


class displayConfigDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Display Options")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.vBoxLayout = QVBoxLayout()
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
        self.setLayout(self.vBoxLayout)
        # need to change this later
        # self.setGeometry(300, 300, 300, 200)
        self.show()

    def accept(self):
        super().accept()
        self.parent.centralWidget.scene.gridMajor = int(self.majorGridEntry.text())
        self.parent.centralWidget.view.gridMajor = int(self.majorGridEntry.text())
        self.parent.centralWidget.scene.gridMinor = int(self.minorGridEntry.text())
        self.parent.centralWidget.view.gridMinor = int(self.minorGridEntry.text())
        self.parent.centralWidget.scene.update()
        self.close()


class editorContainer(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.init_UI()

    def init_UI(self):
        self.scene = editor_scene(self)
        self.view = editor_view(self.scene, self)

        # layout statements, using a grid layout
        gLayout = QGridLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.view, 0, 0)
        # ratio of first column to second column is 5
        gLayout.setColumnStretch(0, 5)
        gLayout.setRowStretch(0, 6)
        self.setLayout(gLayout)


class editor_scene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.gridMajor = 10
        self.gridTuple = (self.gridMajor, self.gridMajor)
        # drawing switches
        self.resetSceneMode()  # reset to select mode
        self.objectStack = []  # stack of objects
        self.undoStack = []  # stack of objects to be redone
        self.selectedItem = None  # selected item
        # items at mouse press point
        # layer infrastructure is ad-hoc. Needs rethink at some point.
        self.defineSceneLayers()
        # pen definitions
        self.setPens()
        self.symbolContextMenu = QMenu()

    def setPens(self):
        self.wirePen = QPen(self.wireLayer.color, 2)
        self.wirePen.setCosmetic(True)
        self.symbolPen = QPen(self.symbolLayer.color, 3)
        self.symbolPen.setCosmetic(True)
        self.selectedWirePen = QPen(self.selectedWireLayer.color, 2)
        self.pinPen = QPen(self.pinLayer.color, 2)
        self.labelPen = QPen(self.labelLayer.color, 1)

    def defineSceneLayers(self):
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
        self.labelLayer = cel.layer(
            name="labelLayer", color=QColor("yellow"), z=3, visible=True
        )

    def mousePressEvent(self, mouse_event):

        if self.selectItem and self.itemAt(mouse_event.scenePos(), QTransform()):
            self.itemsAtMousePress = self.items(mouse_event.scenePos())
            self.selectedItem = self.itemsAtMousePress[0]
        elif (
            hasattr(self, "start") == False
            and (
                self.drawWire
                or self.drawLine
                or self.drawPin
                or self.drawRect
                or self.addLabel
            )
            == True
        ):
            self.startPosition = mouse_event.scenePos().toPoint()
            self.start = QPoint(
                self.snapGrid(self.startPosition.x(), self.gridMajor),
                self.snapGrid(self.startPosition.y(), self.gridMajor),
            )
            self.selectedItem = None
        super().mousePressEvent(mouse_event)

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
        elif self.drawPin == True:
            self.draftItem = QGraphicsRectItem(
                QRect(self.current.x() - 5, self.current.y() - 5, 10, 10)
            )
            self.draftItem.setPen(pen)
            self.draftItem.setBrush(QBrush(QColor("white")))
            self.addItem(self.draftItem)
        elif self.addLabel == True:
            self.labelFont = QFont("Arial", 12)
            fm = QFontMetrics(self.labelFont)
            self.draftItem = QGraphicsRectItem(
                QRect(
                    self.current.x(),
                    self.current.y(),
                    fm.boundingRect(self.labelName).width(),
                    fm.boundingRect(self.labelName).height(),
                )
            )
            self.draftItem.setPen(pen)
            self.addItem(self.draftItem)
        self.parent.parent.statusLine.showMessage(
            "Cursor Position: " + str(self.current.toTuple())
        )
        super().mouseMoveEvent(mouse_event)

    def snap2Grid(self, mouse_event):
        self.current = mouse_event.scenePos().toPoint()
        self.current /= self.gridMajor
        self.current *= self.gridMajor

    def mouseReleaseEvent(self, mouse_event):

        if hasattr(self, "draftItem"):  # remove ghost item
            self.removeItem(self.draftItem)
            del self.draftItem
        if self.drawWire:
            self.lineDraw(self.wirePen)
            self.drawWire = False
        elif self.drawLine:
            self.lineDraw(self.symbolPen)
            self.drawLine = False
        elif self.drawRect:
            self.rectDraw(self.start, self.current, self.symbolPen)
        elif self.drawPin:
            self.pinDraw(self.pinPen)
            self.drawPin = False  # reset flag
        elif self.addLabel:
            self.labelDraw(self.labelPen)
            self.addLabel = False
        if hasattr(self, "start"):
            del self.start
        super().mouseReleaseEvent(mouse_event)

    def rectDraw(self, start: QPoint, end: QPoint, pen: QPen):
        """
        Draws a rectangle on the scene
        """
        rect = shp.rectangle(start, end, pen, self.gridTuple)
        self.addItem(rect)
        self.drawRect = False
        self.objectStack.append(rect)

    def lineDraw(self, pen: QPen):
        line = shp.line(self.start, self.current, pen, self.gridTuple)
        self.addItem(line)
        self.objectStack.append(line)

    def pinDraw(self, pen: QPen):
        pin = shp.pin(
            self.current, pen, self.pinName, self.pinDir, self.pinType, self.gridTuple
        )
        self.addItem(pin)
        self.objectStack.append(pin)

    def labelDraw(self, pen: QPen):
        label = shp.label(
            self.current,
            pen,
            self.labelName,
            self.gridTuple,
            self.labelType,
            self.labelHeight,
            self.labelAlignment,
            self.labelOrient,
            self.labelUse,
        )
        self.addItem(label)
        self.objectStack.append(label)

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_Escape:
            self.resetSceneMode()
        elif key_event.key() == Qt.Key_C:
            self.copyItem()
        elif key_event.key() == Qt.Key_Up:
            selectedItemsCount = len(self.itemsAtMousePress)
            if self.selectCount == selectedItemsCount:
                self.selectCount = 0
                self.changeSelection(self.selectCount)
                self.selectCount += 1
            elif self.selectCount < selectedItemsCount:
                self.changeSelection(self.selectCount)
                self.selectCount += 1

        super().keyPressEvent(key_event)

    def changeSelection(self, i):
        '''
        Change the selected item.
        '''
        self.selectedItem.setSelected(False)
        self.selectedItem = self.itemsAtMousePress[i]
        self.selectedItem.setSelected(True)

    def resetSceneMode(self):
        self.drawWire = False  # flag to indicate if a wire is being drawn
        self.drawItem = False  # flag to indicate if an item is being drawn
        self.selectItem = True  # flag to indicate if an item is being selected
        self.drawLine = False  # flag to indicate if a line is being drawn
        self.drawArc = False  # flag to indicate if an arc is being drawn
        self.drawPin = False  # flag to indicate if a pin is being drawn
        self.drawRect = False  # flag to indicate if a rectangle is being drawn
        self.addLabel = False  # flag to indicate if a label is being drawn
        self.selectCount = 0  # index of item selected
        self.itemsAtMousePress = []
        if hasattr(self, "draftItem"):
            self.removeItem(self.draftItem)
        self.selectItem = True
        self.selectedItem = None

    def deleteSelectedItem(self):
        if hasattr(self, "selectedItem"):
            self.removeItem(self.selectedItem)
            self.objectStack.remove(self.selectedItem)
            self.undoStack.append(self.selectedItem)
            del self.selectedItem
            self.update()
            self.selectItem = True

    def undoLastItem(self):
        if len(self.objectStack) > 0:
            lastItem = self.objectStack.pop()
            self.removeItem(lastItem)
            self.undoStack.append(lastItem)
            self.update()
        else:
            print("Nothing to undo")

    def redoLastItem(self):
        if len(self.undoStack) > 0:
            lastItem = self.undoStack.pop()
            self.addItem(lastItem)
            self.objectStack.append(lastItem)
            self.update()
        else:
            print("No item to redo")

    def copySelectedItem(self):
        if hasattr(self, "selectedItem"):
            selectedItemJson = json.dumps(self.selectedItem, cls=symbolEncoder)
            itemCopyDict = json.loads(selectedItemJson)
            shape = self.createSymbolItems(itemCopyDict)
            self.addItem(shape)
            shape.setPos(
                QPoint(
                    self.selectedItem.pos().x() + self.gridTuple[0],
                    self.selectedItem.pos().y() + self.gridTuple[1],
                )
            )
            self.objectStack.append(shape)

    def itemProperties(self):
        if self.selectedItem is not None:
            if isinstance(self.selectedItem, shp.rectangle):
                self.queryDlg = pdlg.rectPropertyDialog(
                    self.parent.parent, self.selectedItem
                )
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateRectangleShape()
            elif isinstance(self.selectedItem, shp.line):
                self.queryDlg = pdlg.linePropertyDialog(
                    self.parent.parent, self.selectedItem
                )
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateLineShape()

            elif isinstance(self.selectedItem, shp.pin):
                self.queryDlg = pdlg.pinPropertyDialog(
                    self.parent.parent, self.selectedItem
                )
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updatePinShape()
            elif isinstance(self.selectedItem, shp.label):
                self.queryDlg = pdlg.labelPropertyDialog(
                    self.parent.parent, self.selectedItem
                )
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateLabelShape()

            del self.queryDlg
        else:
            print("No item selected")

    def updateRectangleShape(self):
        location = self.selectedItem.scenePos().toTuple()
        newLeft = self.snapGrid(
            float(self.queryDlg.rectLeftLine.text()) - float(location[0]),
            self.gridTuple[0],
        )
        newTop = self.snapGrid(
            float(self.queryDlg.rectTopLine.text()) - float(location[1]),
            self.gridTuple[1],
        )
        newWidth = self.snapGrid(
            float(self.queryDlg.rectWidthLine.text()), self.gridTuple[0]
        )
        newHeight = self.snapGrid(
            float(self.queryDlg.rectHeightLine.text()), self.gridTuple[1]
        )
        self.selectedItem.start = QPoint(newLeft, newTop)
        self.selectedItem.end = QPoint(newLeft + newWidth, newTop + newHeight)
        self.selectedItem.setLeft(newLeft)
        self.selectedItem.setTop(newTop)
        self.selectedItem.setWidth(newWidth)
        self.selectedItem.setHeight(newHeight)
        self.selectedItem.update()

    def updateLineShape(self):
        location = self.selectedItem.scenePos().toTuple()
        newStartX = self.snapGrid(
            float(self.queryDlg.startXLine.text()) - float(location[0]),
            self.gridTuple[0],
        )
        newStartY = self.snapGrid(
            float(self.queryDlg.startYLine.text()) - float(location[1]),
            self.gridTuple[1],
        )
        newEndX = self.snapGrid(
            float(self.queryDlg.endXLine.text()) - float(location[0]),
            self.gridTuple[0],
        )
        newEndY = self.snapGrid(
            float(self.queryDlg.endYLine.text()) - float(location[1]),
            self.gridTuple[1],
        )
        self.selectedItem.start = QPoint(newStartX, newStartY)
        self.selectedItem.end = QPoint(newEndX, newEndY)
        self.selectedItem.update()

    def updatePinShape(self):
        location = self.selectedItem.scenePos().toTuple()
        newX = self.snapGrid(
            float(self.queryDlg.pinXLine.text()) - float(location[0]), self.gridTuple[0]
        )
        newY = self.snapGrid(
            float(self.queryDlg.pinYLine.text()) - float(location[1]), self.gridTuple[1]
        )
        self.selectedItem.start = QPoint(newX, newY)
        self.selectedItem.rect = QRect(newX - 5, newY - 5, 10, 10)
        self.selectedItem.pinName = self.queryDlg.pinName.text()
        self.selectedItem.pinType = self.queryDlg.pinType.currentText()
        self.selectedItem.pinDir = self.queryDlg.pinDir.currentText()
        self.selectedItem.update()

    def updateLabelShape(self):
        """
        update pin shape with new values.
        """
        location = self.selectedItem.scenePos().toTuple()
        newX = self.snapGrid(
            float(self.queryDlg.labelXLine.text()) - float(location[0]),
            self.gridTuple[0],
        )
        newY = self.snapGrid(
            float(self.queryDlg.labelYLine.text()) - float(location[1]),
            self.gridTuple[1],
        )
        self.selectedItem.start = QPoint(newX, newY)
        self.selectedItem.labelName = self.queryDlg.labelNameEdit.text()
        self.selectedItem.labelHeight = self.queryDlg.labelHeightEdit.text()
        self.selectedItem.labelAlign = self.queryDlg.labelAlignCombo.currentText()
        self.selectedItem.labelOrient = self.queryDlg.labelOrientation.currentText()
        self.selectedItem.labelUse = self.queryDlg.labelUse.currentText()
        if self.queryDlg.normalType.isChecked():
            self.selectedItem.labelType = shp.label.labelTypes[0]
        elif self.queryDlg.NLPType.isChecked():
            self.selectedItem.labelType = shp.label.labelTypes[1]
        elif self.queryDlg.pyLType.isChecked():
            self.selectedItem.labelType = shp.label.labelTypes[2]
        self.selectedItem.update()

    def snapGrid(self, number, base):
        return base * int(round(number / base))

    def loadSymbol(self, file):
        with open(file, "r") as f:
            fJsonLoad = f.read()
            try:
                items = json.loads(fJsonLoad)  # load json file
                for item in items:
                    symbolShape = self.createSymbolItems(item)
                    self.addItem(symbolShape)
                    self.objectStack.append(symbolShape)
            except json.decoder.JSONDecodeError:
                print("Invalid JSON file")

    def createSymbolItems(self, item):
        if item["type"] == "rect":
            start = QPoint(item["rect"][0], item["rect"][1])
            end = QPoint(item["rect"][2], item["rect"][3])
            penStyle = Qt.PenStyle.__dict__[
                item["lineStyle"].split(".")[-1]
            ]  # convert string to enum
            penWidth = item["width"]
            penColor = QColor(*item["color"])
            pen = QPen(penColor, penWidth, penStyle)
            pen.setCosmetic(item["cosmetic"])
            rect = shp.rectangle(
                start, end, pen, self.gridTuple
            )  # note that we are using grid values for scene
            rect.setPos(
                QPoint(item["location"][0], item["location"][1]),
            )
            return rect
        elif item["type"] == "line":
            start = QPoint(item["start"][0], item["start"][1])
            end = QPoint(item["end"][0], item["end"][1])
            penStyle = Qt.PenStyle.__dict__[item["lineStyle"].split(".")[-1]]
            penWidth = item["width"]
            penColor = QColor(*item["color"])
            pen = QPen(penColor, penWidth, penStyle)
            pen.setCosmetic(item["cosmetic"])
            line = shp.line(start, end, pen, self.gridTuple)
            line.setPos(QPoint(item["location"][0], item["location"][1]))
            return line
        elif item["type"] == "pin":
            start = QPoint(item["start"][0], item["start"][1])
            penStyle = Qt.PenStyle.__dict__[item["lineStyle"].split(".")[-1]]
            penWidth = item["width"]
            penColor = QColor(*item["color"])
            pen = QPen(penColor, penWidth, penStyle)
            pen.setCosmetic(item["cosmetic"])
            pin = shp.pin(
                start,
                pen,
                item["pinName"],
                item["pinDir"],
                item["pinType"],
                self.gridTuple,
            )
            pin.setPos(QPoint(item["location"][0], item["location"][1]))
            return pin
        elif item["type"] == "label":
            start = QPoint(item["start"][0], item["start"][1])
            penStyle = Qt.PenStyle.__dict__[item["lineStyle"].split(".")[-1]]
            penWidth = item["width"]
            penColor = QColor(*item["color"])
            pen = QPen(penColor, penWidth, penStyle)
            pen.setCosmetic(item["cosmetic"])
            label = shp.label(
                start,
                pen,
                item["labelName"],
                self.gridTuple,
                item["labelType"],
                item["labelHeight"],
                item["labelAlign"],
                item["labelOrient"],
                item["labelUse"],
            )
            label.setPos(QPoint(item["location"][0], item["location"][1]))
            return label

    def saveSymbolCell(self, fileName):
        self.sceneR = self.sceneRect()  # get scene rect
        items = self.items(self.sceneR)  # get items in scene rect
        with open(fileName, "w") as f:
            json.dump(items, f, cls=symbolEncoder, indent=4)

    def stretchSelectedItem(self):
        if self.selectedItem is not None:
            self.selectedItem.stretch = True

    def viewSymbolProperties(self):
        symbolPropDialogue = pdlg.symbolLabelsDialogue(self.parent.parent, self.items())
        if symbolPropDialogue.exec() == QDialog.Accepted:
            for i, item in enumerate(symbolPropDialogue.labelItemList):
                # label name is not changed.
                item.labelHeight = symbolPropDialogue.labelHeightList[i]
                item.labelAlign = symbolPropDialogue.labelAlignmentList[i]
                item.labelOrient = symbolPropDialogue.labelOrientationList[i]
                item.labelUse = symbolPropDialogue.labelUseList[i]
                item.labelType = symbolPropDialogue.labelTypeList[i]
                item.update()


class symbolEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, shp.rectangle):
            itemDict = {
                "type": "rect",
                "rect": item.__dict__["rect"].getCoords(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "location": item.scenePos().toTuple(),
            }
            return itemDict
        elif isinstance(item, shp.line):
            itemDict = {
                "type": "line",
                "start": item.__dict__["start"].toTuple(),
                "end": item.__dict__["end"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "location": item.scenePos().toTuple(),
            }
            return itemDict
        elif isinstance(item, shp.pin):
            itemDict = {
                "type": "pin",
                "start": item.__dict__["start"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "pinName": item.__dict__["pinName"],
                "pinDir": item.__dict__["pinDir"],
                "pinType": item.__dict__["pinType"],
                "location": item.scenePos().toTuple(),
            }
            return itemDict
        elif isinstance(item, shp.label):
            itemDict = {
                "type": "label",
                "start": item.__dict__["start"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "labelName": item.__dict__["labelName"],
                "labelType": item.__dict__["labelType"],
                "labelHeight": item.__dict__["labelHeight"],
                "labelAlign": item.__dict__["labelAlign"],
                "labelOrient": item.__dict__["labelOrient"],
                "labelUse": item.__dict__["labelUse"],
                "location": item.scenePos().toTuple(),
            }
            return itemDict

        else:
            return super().default(item)


class editor_view(QGraphicsView):
    """
    The qgraphicsview for qgraphicsscene. It is used for both schematic and layout editors.
    """

    def __init__(self, scene, parent):
        super().__init__(scene, parent)
        self.parent = parent
        self.scene = scene
        self.gridMajor = self.scene.gridMajor

        self.init_UI()

    def init_UI(self):
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.standardCursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.standardCursor)  # set cursor to standard arrow
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setMouseTracking(True)  # self.setDragMode(QGraphicsView.RubberBandDrag)

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

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_F:
            self.fitToView()
        super().keyPressEvent(key_event)

    def fitToView(self):
        viewRect = self.scene.itemsBoundingRect()
        self.fitInView(viewRect, Qt.AspectRatioMode.KeepAspectRatio)
        self.show()


# library path editor dialogue
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


class mainwContainer(QWidget):
    """
    Definition for the main app window layout.
    """

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


# main application window definition
class mainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        revEDAPathObj = Path(__file__)
        revEDADirObj = revEDAPathObj.parent
        self.cellViews = ["schematic", "symbol"]
        # library definition file path
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
        self.centralW = mainwContainer(self)
        self.setCentralWidget(self.centralW)
        self.libraryBrowser = None

    def _createMenuBar(self):
        self.mainW_menubar = self.menuBar()
        # Returns QMenu object.
        self.menuFile = self.mainW_menubar.addMenu("&File")
        self.menuTools = self.mainW_menubar.addMenu("&Tools")
        self.menuOptions = self.mainW_menubar.addMenu("&Options")
        self.menuHelp = self.mainW_menubar.addMenu("&Help")
        self.mainW_statusbar = self.statusBar()
        self.mainW_statusbar.showMessage("Ready")

        # create actions

    def _createActions(self):
        exitIcon = QIcon(":/icons/external.png")
        self.exitAction = QAction(exitIcon, "Exit", self)
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.triggered.connect(self.exitApp)
        self.menuFile.addAction(self.exitAction)

        openLibIcon = QIcon(":/icons/database--pencil.png")
        self.libraryBrowserAction = QAction(openLibIcon, "Library Browser", self)
        self.menuTools.addAction(self.libraryBrowserAction)
        self.libraryBrowserAction.triggered.connect(self.libraryBrowserClick)

    # open library browser window
    def libraryBrowserClick(self):
        if self.libraryBrowser is None:
            self.libraryBrowser = libraryBrowser(
                self.libraryDict
            )  # create the library browser
            self.libraryBrowser.show()
        else:
            self.libraryBrowser.show()

    def exitApp(self):
        self.app.closeAllWindows()


# Start Main application window
app = QApplication(sys.argv)
# app.setStyle('Fusion')
# empty argument as there is no parent window.
mainW = mainWindow(app)
mainW.setWindowTitle("Revolution EDA Main Window")
redirect = pcon.Redirect(mainW.centralW.console.errorwrite)
with redirect_stdout(mainW.centralW.console), redirect_stderr(redirect):
    mainW.show()
    sys.exit(app.exec())
