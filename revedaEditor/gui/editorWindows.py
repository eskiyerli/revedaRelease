#    “Commons Clause” License Condition v1.0
#   #
#    The Software is provided to you by the Licensor under the License, as defined
#    below, subject to the following condition.
#
#    Without limiting other conditions in the License, the grant of rights under the
#    License will not include, and the License does not grant to you, the right to
#    Sell the Software.
#
#    For purposes of the foregoing, “Sell” means practicing any or all of the rights
#    granted to you under the License to provide to third parties, for a fee or other
#    consideration (including without limitation fees for hosting or consulting/
#    support services related to the Software), a product or service whose value
#    derives, entirely or substantially, from the functionality of the Software. Any
#    license notice or attribution required by the License must also include this
#    Commons Clause License Condition notice.
#
#   Add-ons and extensions developed for this software may be distributed
#   under their own separate licenses.
#
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
#

import datetime
import json
# from hashlib import new
import pathlib
import shutil
import time
from copy import deepcopy
from functools import lru_cache

# import numpy as np
from PySide6.QtCore import (
    QRunnable,
    Qt,
    Slot,
    QPoint,
)
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QCursor,
    QIcon,
    QImage,
    QKeySequence,
    QStandardItem,
    QStandardItemModel,
)
from PySide6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QSplitter,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QTableView,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from quantiphy import Quantity

import pdk.layoutLayers
# import pdk.symLayers as symlyr
import pdk.layoutLayers as laylyr
import pdk.process as fabproc
import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.libraryModelView as lmview
import revedaEditor.backend.schBackEnd as scb
import revedaEditor.common.net as net
import revedaEditor.common.shapes as shp  # import the shapes
import revedaEditor.fileio.gdsExport as gdse
import revedaEditor.fileio.layoutEncoder as layenc
import revedaEditor.fileio.loadJSON as lj
import revedaEditor.fileio.symbolEncoder as symenc
import revedaEditor.gui.editFunctions as edf
import revedaEditor.gui.editorScenes as escn
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.helpBrowser as hlp
import revedaEditor.gui.layoutDialogues as ldlg
import revedaEditor.gui.lsw as lsw
import revedaEditor.gui.propertyDialogues as pdlg
import revedaEditor.gui.textEditor as ted
import revedaEditor.gui.editorViews as edv

import revedaEditor.resources.resources
import pdk.pcells as pcells


# import os
# if os.environ.get('REVEDASIM_PATH'):
#     import revedasim.simMainWindow as smw


class libraryBrowser(QMainWindow):
    def __init__(self, appMainW: QMainWindow) -> None:
        super().__init__()
        self.resize(300, 600)
        self.appMainW = appMainW
        self.libraryDict = self.appMainW.libraryDict
        self.cellViews = self.appMainW.cellViews
        self.setWindowTitle("Library Browser")
        self._createMenuBar()
        self._createActions()
        self._createToolBars()
        self._createTriggers()
        self.logger = self.appMainW.logger
        self.libFilePath = self.appMainW.libraryPathObj
        self.libBrowserCont = libraryBrowserContainer(self)
        self.setCentralWidget(self.libBrowserCont)
        self.designView = self.libBrowserCont.designView
        self.libraryModel = self.designView.libraryModel
        self.editProcess = None

    def _createMenuBar(self):
        self.browserMenubar = self.menuBar()
        self.browserMenubar.setNativeMenuBar(False)
        self.libraryMenu = self.browserMenubar.addMenu("&Library")
        self.cellMenu = self.browserMenubar.addMenu("&Cell")
        self.viewMenu = self.browserMenubar.addMenu("&View")
        self.helpMenu = self.browserMenubar.addMenu("&Help")

    def _createActions(self):
        openLibIcon = QIcon(":/icons/database--plus.png")
        self.openLibAction = QAction(openLibIcon, "Create/Open Lib...", self)
        self.openLibAction.setToolTip("Create/Open Lib...")
        self.libraryMenu.addAction(self.openLibAction)

        libraryEditIcon = QIcon(":/icons/application-dialog.png")
        self.libraryEditorAction = QAction(libraryEditIcon, "Library Editor", self)
        self.libraryMenu.addAction(self.libraryEditorAction)
        self.libraryEditorAction.setToolTip("Open Library Editor...")

        closeLibIcon = QIcon(":/icons/database-delete.png")
        self.closeLibAction = QAction(closeLibIcon, "Close Lib...", self)
        self.closeLibAction.setToolTip("Close Lib")
        self.libraryMenu.addAction(self.closeLibAction)

        self.libraryMenu.addSeparator()
        updateLibraryIcon = QIcon(":/icons/arrow-circle.png")
        self.updateLibraryAction = QAction(updateLibraryIcon, "Update Library...", self)
        self.updateLibraryAction.setToolTip("Update Library")
        self.libraryMenu.addAction(self.updateLibraryAction)

        newCellIcon = QIcon(":/icons/document--plus.png")
        self.newCellAction = QAction(newCellIcon, "New Cell...", self)
        self.newCellAction.setToolTip("Create New Cell")
        self.cellMenu.addAction(self.newCellAction)

        deleteCellIcon = QIcon(":/icons/node-delete.png")
        self.deleteCellAction = QAction(deleteCellIcon, "Delete Cell...", self)
        self.deleteCellAction.setToolTip("Delete Cell")
        self.cellMenu.addAction(self.deleteCellAction)

        newCellViewIcon = QIcon(":/icons/document--pencil.png")
        self.newCellViewAction = QAction(
            newCellViewIcon, "Create New CellView...", self
        )
        self.newCellViewAction.setToolTip("Create New Cellview")
        self.viewMenu.addAction(self.newCellViewAction)

        openCellViewIcon = QIcon(":/icons/document--pencil.png")
        self.openCellViewAction = QAction(openCellViewIcon, "Open CellView...", self)
        self.openCellViewAction.setToolTip("Open CellView")
        self.viewMenu.addAction(self.openCellViewAction)

        deleteCellViewIcon = QIcon(":/icons/node-delete.png")
        self.deleteCellViewAction = QAction(
            deleteCellViewIcon, "Delete CellView...", self
        )
        self.deleteCellViewAction.setToolTip("Delete Cellview")
        self.viewMenu.addAction(self.deleteCellViewAction)

    def _createTriggers(self):
        self.openLibAction.triggered.connect(self.openLibClick)
        self.libraryEditorAction.triggered.connect(self.libraryEditorClick)
        self.closeLibAction.triggered.connect(self.closeLibClick)
        self.newCellAction.triggered.connect(self.newCellClick)
        self.deleteCellAction.triggered.connect(self.deleteCellClick)
        self.newCellViewAction.triggered.connect(self.newCellViewClick)
        self.openCellViewAction.triggered.connect(self.openCellViewClick)
        self.deleteCellViewAction.triggered.connect(self.deleteCellViewClick)
        self.updateLibraryAction.triggered.connect(self.updateLibraryClick)

    def _createToolBars(self):
        # Create tools bar called "main toolbar"
        toolbar = QToolBar("Main Toolbar", self)
        # place toolbar at top
        self.addToolBar(toolbar)
        toolbar.addAction(self.openLibAction)
        toolbar.addAction(self.closeLibAction)
        toolbar.addSeparator()
        toolbar.addAction(self.newCellAction)
        toolbar.addAction(self.deleteCellAction)
        toolbar.addSeparator()
        toolbar.addAction(self.newCellViewAction)
        toolbar.addAction(self.openCellViewAction)
        toolbar.addAction(self.deleteCellViewAction)

    def writeLibDefFile(self, libPathDict: dict, libFilePath: pathlib.Path) -> None:
        libTempDict = dict(zip(libPathDict.keys(), map(str, libPathDict.values())))
        try:
            with libFilePath.open(mode="w") as f:
                json.dump({"libdefs": libTempDict}, f, indent=4)
            self.logger.info(f"Wrote library definition file in {libFilePath}")
        except IOError:
            self.logger.error(f"Cannot save library definitions in {libFilePath}")

    def openLibClick(self):
        """
        Open a directory and add a 'reveda.lib' file to designate it as a library.
        """
        home_dir = str(pathlib.Path.cwd())
        libDialog = QFileDialog(self, "Create/Open Library", home_dir)
        libDialog.setFileMode(QFileDialog.Directory)
        # libDialog.Option(QFileDialog.ShowDirsOnly)
        if libDialog.exec() == QDialog.Accepted:
            libPathObj = pathlib.Path(libDialog.selectedFiles()[0])
            self.libraryDict[libPathObj.stem] = libPathObj
            # create an empty file to denote it is a design library.
            libPathObj.joinpath("reveda.lib").touch(exist_ok=True)
            # self.designView.reworkDesignLibrariesView()
            self.libraryModel.populateLibrary(libPathObj)
            self.writeLibDefFile(self.libraryDict, self.libFilePath)

    def closeLibClick(self):
        libCloseDialog = fd.closeLibDialog(self.libraryDict, self)
        if libCloseDialog.exec() == QDialog.Accepted:
            libName = libCloseDialog.libNamesCB.currentText()
            libItem = libm.getLibItem(self.libraryModel, libName)
            self.libraryDict.pop(libName, None)
            self.libraryModel.rootItem.removeRow(libItem)

    def libraryEditorClick(self, s):
        """
        Open library editor dialogue.
        """
        tempDict = deepcopy(self.libraryDict)
        pathEditDlg = fd.libraryPathEditorDialog(self, tempDict)
        libDefFilePathObj = pathlib.Path.cwd().joinpath("library.json")
        self.libraryDict.clear()
        if pathEditDlg.exec() == QDialog.Accepted:
            model = pathEditDlg.pathsModel
            for row in range(model.rowCount()):
                if model.itemFromIndex(model.index(row, 1)).text().strip():
                    self.libraryDict[
                        model.itemFromIndex(model.index(row, 0)).text().strip()
                    ] = pathlib.Path(
                        model.itemFromIndex(model.index(row, 1)).text().strip()
                    )
        self.writeLibDefFile(self.libraryDict, libDefFilePathObj)
        self.appMainW.libraryDict = self.libraryDict
        self.designView.reworkDesignLibrariesView(self.appMainW.libraryDict)

    def updateLibraryClick(self):
        self.designView.reworkDesignLibrariesView(self.appMainW.libraryDict)

    def newCellClick(self, s):
        dlg = fd.createCellDialog(self, self.libraryModel)
        if dlg.exec() == QDialog.Accepted:
            libName = dlg.libNamesCB.currentText()
            cellName = dlg.cellCB.currentText()
            self.createNewCell(self, self.libraryModel, cellName, libName)

    def createNewCell(self, parent, libraryModel, cellName, libName):
        libItem = libm.getLibItem(self.libraryModel, libName)
        if cellName.strip() == "":
            self.logger.error("Please enter a cell name.")
        else:
            scb.createCell(parent, libraryModel, libItem, cellName)

    def deleteCellClick(self, s):
        dlg = fd.deleteCellDialog(self, self.libraryModel)
        if dlg.exec() == QDialog.Accepted:
            libItem = libm.getLibItem(self.libraryModel, dlg.libNamesCB.currentText())
            if dlg.cellCB.currentText().strip() == "":
                self.logger.error("Please enter a cell name.")
            else:
                # cellItemsLib = {libItem.child(i).cellName: libItem.child(i) for i in
                #                 range(libItem.rowCount())}
                # cellItem = cellItemsLib.get(dlg.cellCB.currentText())
                cellItem = libm.getCellItem(libItem, dlg.cellCB.currentText())
                # remove the directory
                shutil.rmtree(cellItem.data(Qt.UserRole + 2))
                cellItem.parent().removeRow(cellItem.row())

    def newCellViewClick(self, s):
        dlg = fd.newCellViewDialog(self, self.libraryModel)
        dlg.viewType.addItems(self.cellViews)
        if dlg.exec() == QDialog.Accepted:
            # cellPath = dlg.selectedLibPath.joinpath(dlg.cellCB.currentText())
            libItem = libm.getLibItem(self.libraryModel, dlg.libNamesCB.currentText())
            cellItem = libm.getCellItem(libItem, dlg.cellCB.currentText())
            viewItem = scb.createCellView(
                self.appMainW, dlg.viewName.text().strip(), cellItem
            )
            self.createNewCellView(libItem, cellItem, viewItem)

    def createNewCellView(self, libItem, cellItem, viewItem):
        viewTuple = ddef.viewTuple(
            libItem.libraryName, cellItem.cellName, viewItem.viewName
        )
        match viewItem.viewType:
            case "config":
                schViewsList = [
                    cellItem.child(row).viewName
                    for row in range(cellItem.rowCount())
                    if cellItem.child(row).viewType == "schematic"
                ]

                dlg = fd.createConfigViewDialogue(self.appMainW)
                dlg.libraryNameEdit.setText(libItem.libraryName)
                dlg.cellNameEdit.setText(cellItem.cellName)
                dlg.viewNameCB.addItems(schViewsList)
                dlg.switchViews.setText(", ".join(self.appMainW.switchViewList))
                dlg.stopViews.setText(", ".join(self.appMainW.stopViewList))
                # dlg.switchViews.setText(self.)
                if dlg.exec() == QDialog.Accepted:
                    selectedSchName = dlg.viewNameCB.currentText()
                    selectedSchItem = libm.getViewItem(cellItem, selectedSchName)
                    schematicWindow = schematicEditor(
                        selectedSchItem,
                        self.libraryDict,
                        self.libBrowserCont.designView,
                    )
                    schematicWindow.loadSchematic()
                    switchViewList = [
                        viewName.strip()
                        for viewName in dlg.switchViews.text().split(",")
                    ]
                    stopViewList = [
                        viewName.strip() for viewName in dlg.stopViews.text().split(",")
                    ]
                    schematicWindow.switchViewList = switchViewList
                    schematicWindow.stopViewList = stopViewList
                    schematicWindow.configDict = dict()  # clear config dictionary

                    # clear netlisted cells list
                    newConfigDict = dict()  # create an empty newconfig dict
                    schematicWindow.createConfigView(
                        viewItem,
                        schematicWindow.configDict,
                        newConfigDict,
                        schematicWindow.processedCells,
                    )
                    configFilePathObj = viewItem.data(Qt.UserRole + 2)
                    items = list()
                    items.insert(0, {"cellView": "config"})
                    items.insert(1, {"reference": selectedSchName})
                    items.insert(2, schematicWindow.configDict)
                    with configFilePathObj.open(mode="w+") as configFile:
                        json.dump(items, configFile, indent=4)

                    configWindow = self.openConfigEditWindow(
                        schematicWindow.configDict, selectedSchItem, viewItem
                    )
                    self.appMainW.openViews[viewTuple] = configWindow
            case "schematic":
                # scb.createCellView(self.appMainW, viewItem.viewName, cellItem)
                schematicWindow = schematicEditor(
                    viewItem, self.libraryDict, self.libBrowserCont.designView
                )
                self.appMainW.openViews[viewTuple] = schematicWindow
                schematicWindow.loadSchematic()
                schematicWindow.show()
            case "symbol":
                # scb.createCellView(self.appMainW, viewItem.viewName, cellItem)
                symbolWindow = symbolEditor(
                    viewItem, self.libraryDict, self.libBrowserCont.designView
                )
                self.appMainW.openViews[viewTuple] = symbolWindow
                symbolWindow.loadSymbol()
                symbolWindow.show()
            case "layout":
                layoutWindow = layoutEditor(
                    viewItem, self.libraryDict, self.libBrowserCont.designView
                )
                self.appMainW.openViews[viewTuple] = layoutWindow
                layoutWindow.loadLayout()
                layoutWindow.show()
            case "veriloga":
                verilogaEditor = ted.verilogaEditor(self.appMainW, "")
                verilogaEditor.cellViewTuple = viewTuple
                verilogaEditor.closedSignal.connect(self.verilogaCreateFinished)
                verilogaEditor.show()
            case "spice":
                xyceEditor = ted.xyceEditor(self.appMainW, "")
                xyceEditor.cellViewTuple = viewTuple
                xyceEditor.closedSignal.connect(self.spiceCreateFinished)
                xyceEditor.show()

            case "pcell":
                dlg = ldlg.pcellLinkDialogue(self.appMainW, viewItem)
                if dlg.exec() == QDialog.Accepted:
                    items = list()
                    items.insert(0, {"cellView": "pcell"})
                    items.insert(1, {"reference": dlg.pcellCB.currentText()})
                    with viewItem.data(Qt.UserRole + 2).open(mode="w+") as pcellFile:
                        json.dump(items, pcellFile, indent=4)
                else:
                    try:
                        viewItem.data(Qt.UserRole + 2).unlink()  # delete the file.
                        viewItem.parent().removeRow(viewItem.row())
                    except OSError as e:
                        self.logger.warning(f"Error:{e.strerror}")

    def openConfigEditWindow(self, configDict, schViewItem, viewItem):
        schematicName = schViewItem.viewName
        libItem = schViewItem.parent().parent()
        configWindow = configViewEdit(self.appMainW, schViewItem, configDict, viewItem)
        configWindow.centralWidget.libraryNameEdit.setText(libItem.libraryName)
        cellItem = viewItem.parent()
        configWindow.centralWidget.cellNameEdit.setText(cellItem.cellName)
        schViewsList = [
            cellItem.child(row).viewName
            for row in range(cellItem.rowCount())
            if cellItem.child(row).viewType == "schematic"
        ]
        configWindow.centralWidget.viewNameCB.addItems(schViewsList)
        configWindow.centralWidget.viewNameCB.setCurrentText(schematicName)
        configWindow.centralWidget.switchViewsEdit.setText(
            ", ".join(self.appMainW.switchViewList)
        )
        configWindow.centralWidget.stopViewsEdit.setText(
            ", ".join(self.appMainW.stopViewList)
        )
        configWindow.show()
        return configWindow

    def selectCellView(self, libModel) -> scb.viewItem:
        dlg = fd.selectCellViewDialog(self, libModel)
        if dlg.exec() == QDialog.Accepted:
            libItem = libm.getLibItem(libModel, dlg.libNamesCB.currentText())
            try:
                cellItem = libm.getCellItem(libItem, dlg.cellCB.currentText())
            except IndexError:
                cellItem = libItem.child(0)
            try:
                viewItem = libm.getViewItem(cellItem, dlg.viewCB.currentText())
                return viewItem
            except IndexError:
                viewItem = cellItem.child(0)
                return None

    def openCellViewClick(self):
        viewItem = self.selectCellView(self.libraryModel)
        cellItem = viewItem.parent()
        libItem = cellItem.parent()
        self.openCellView(viewItem, cellItem, libItem)

    def openCellView(
        self, viewItem: scb.viewItem, cellItem: scb.cellItem, libItem: scb.libraryItem
    ):
        viewName = viewItem.viewName
        cellName = cellItem.cellName
        libName = libItem.libraryName
        openCellViewTuple = ddef.viewTuple(libName, cellName, viewName)
        if openCellViewTuple in self.appMainW.openViews.keys():
            self.appMainW.openViews[openCellViewTuple].raise_()
        else:
            match viewItem.viewType:
                case "layout":
                    layoutWindow = layoutEditor(
                        viewItem, self.libraryDict, self.libBrowserCont.designView
                    )
                    layoutWindow.loadLayout()
                    layoutWindow.show()
                    layoutWindow.centralW.scene.fitItemsInView()
                    self.appMainW.openViews[openCellViewTuple] = layoutWindow

                case "schematic":
                    schematicWindow = schematicEditor(
                        viewItem, self.libraryDict, self.libBrowserCont.designView
                    )
                    schematicWindow.loadSchematic()
                    schematicWindow.show()
                    schematicWindow.centralW.scene.fitItemsInView()
                    self.appMainW.openViews[openCellViewTuple] = schematicWindow
                case "symbol":
                    symbolWindow = symbolEditor(
                        viewItem, self.libraryDict, self.libBrowserCont.designView
                    )
                    symbolWindow.loadSymbol()
                    symbolWindow.show()
                    symbolWindow.centralW.scene.fitItemsInView()
                    self.appMainW.openViews[openCellViewTuple] = symbolWindow
                case "veriloga":
                    with open(viewItem.viewPath) as tempFile:
                        items = json.load(tempFile)
                    if items[1]["filePath"]:
                        VerilogafilePathObj = (
                            viewItem.parent()
                            .data(Qt.UserRole + 2)
                            .joinpath(items[1]["filePath"])
                        )
                        verilogaEditor = ted.verilogaEditor(
                            self.appMainW, str(VerilogafilePathObj)
                        )
                        self.appMainW.openViews[openCellViewTuple] = verilogaEditor
                        verilogaEditor.cellViewTuple = openCellViewTuple
                        verilogaEditor.closedSignal.connect(self.verilogaEditFinished)
                        verilogaEditor.show()
                    else:
                        self.logger.warning("File path not defined.")
                case "spice":
                    with open(viewItem.viewPath) as tempFile:
                        items = json.load(tempFile)
                    if items[1]["filePath"]:
                        spicefilePathObj = (
                            viewItem.parent()
                            .data(Qt.UserRole + 2)
                            .joinpath(items[1]["filePath"])
                        )
                        xyceEditor = ted.xyceEditor(
                            self.appMainW, str(spicefilePathObj)
                        )
                        self.appMainW.openViews[openCellViewTuple] = xyceEditor
                        xyceEditor.cellViewTuple = openCellViewTuple
                        xyceEditor.closedSignal.connect(self.spiceEditFinished)
                        xyceEditor.show()

                case "pcell":
                    with open(viewItem.viewPath) as tempFile:
                        items = json.load(tempFile)

                case "config":
                    with open(viewItem.viewPath) as tempFile:
                        items = json.load(tempFile)
                    # viewName = items[0]["viewName"]
                    schematicName = items[1]["reference"]
                    schViewItem = libm.getViewItem(cellItem, schematicName)
                    configDict = items[2]
                    configWindow = self.openConfigEditWindow(
                        configDict, schViewItem, viewItem
                    )
                    self.appMainW.openViews[openCellViewTuple] = configWindow

        return openCellViewTuple

    def verilogaCreateFinished(self, editorViewTuple: ddef.viewTuple, fileName: str):
        self.appMainW.importVerilogaModule(editorViewTuple, fileName)

    def spiceCreateFinished(self, editorViewTuple: ddef.viewTuple, fileName: str):
        self.appMainW.importSpiceSubckt(editorViewTuple, fileName)

    def verilogaEditFinished(self, editorViewTuple: ddef.viewTuple, fileName: str):
        self.appMainW.importVerilogaModule(editorViewTuple, fileName)
        self.appMainW.openViews.pop(editorViewTuple)

    def spiceEditFinished(self, editorViewTuple: ddef.viewTuple, fileName: str):
        self.appMainW.importSpiceSubckt(editorViewTuple, fileName)
        self.appMainW.openViews.pop(editorViewTuple)

    def deleteCellViewClick(self, s):
        viewItem = self.selectCellView(self.libraryModel)
        try:
            viewItem.data(Qt.UserRole + 2).unlink()  # delete the file.
            viewItem.parent().removeRow(viewItem.row())
        except OSError as e:
            self.logger.warning(f"Error:{e.strerror}")

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()  # ignore the default close event
        self.hide()  # hide the window instead


class libraryBrowserContainer(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.designView = lmview.designLibrariesView(self)
        self.layout.addWidget(self.designView)
        self.setLayout(self.layout)

class editorWindow(QMainWindow):
    """
    Base class for editor windows.
    """

    def __init__(
        self,
        viewItem: scb.viewItem,
        libraryDict: dict,
        libraryView: lmview.designLibrariesView,
    ):  # file is a pathlib.Path object
        super().__init__()
        self.centralW = None
        self.viewItem = viewItem
        self.file: pathlib.Path = self.viewItem.data(
            Qt.UserRole + 2
        )  # pathlib Path object
        self.cellItem = self.viewItem.parent()
        self.cellName = self.cellItem.cellName
        self.libItem = self.cellItem.parent()
        self.libName = self.libItem.libraryName
        self.viewName = self.viewItem.viewName
        self.libraryDict = libraryDict
        self.libraryView = libraryView
        self.parentEditor = None  # type: editorWindow
        self._app = QApplication.instance()  # main application pointer
        self.appMainW = self.libraryView.parent.parent.appMainW
        self.logger = self.appMainW.logger
        self.switchViewList = self.appMainW.switchViewList
        self.stopViewList = self.appMainW.stopViewList
        self.statusLine = self.statusBar()
        self.messageLine = QLabel()  # message line
        self.statusLine.addPermanentWidget(self.messageLine)
        self.majorGrid = 10  # dot/line grid spacing
        self.snapGrid = 5  # snapping grid size
        self.snapTuple = (self.snapGrid, self.snapGrid)
        self.snapDistance = 2 * self.snapGrid
        self.init_UI()

    def init_UI(self):
        self.resize(1600, 800)
        self._createActions()
        self._createMenuBar()
        self._createToolBars()
        self._addActions()
        self._createTriggers()
        self._createShortcuts()

    def _createMenuBar(self):
        """
        Creates the menu bar for the editor.

        """
        self.editorMenuBar = self.menuBar()
        self.editorMenuBar.setNativeMenuBar(False)
        # Returns QMenu object.
        self.menuFile = self.editorMenuBar.addMenu("&File")
        self.menuView = self.editorMenuBar.addMenu("&View")
        self.menuEdit = self.editorMenuBar.addMenu("&Edit")
        self.menuCreate = self.editorMenuBar.addMenu("C&reate")
        self.menuOptions = self.editorMenuBar.addMenu("&Options")
        # self.menuCheck = self.editorMenuBar.addMenu("&Check")
        self.menuTools = self.editorMenuBar.addMenu("&Tools")
        # self.menuWindow = self.editorMenuBar.addMenu("&Window")
        self.menuUtilities = self.editorMenuBar.addMenu("&Utilities")
        self.menuHelp = self.editorMenuBar.addMenu("&Help")

    def _createActions(self):
        checkCellIcon = QIcon(":/icons/document-task.png")
        self.checkCellAction = QAction(checkCellIcon, "Check-Save", self)

        saveCellIcon = QIcon(":/icons/document--plus.png")
        self.saveCellAction = QAction(saveCellIcon, "Save", self)

        self.readOnlyCellIcon = QIcon(":/icons/lock.png")
        self.readOnlyCellAction = QAction("Read Only", self)
        self.readOnlyCellAction.setCheckable(True)

        updateCellIcon = QIcon(":/icons/document-xaml.png")
        self.updateCellAction = QAction(updateCellIcon, "Update Design", self)
        self.updateCellAction.setToolTip("Reread all the cells in the design")

        printIcon = QIcon(":/icons/printer--arrow.png")
        self.printAction = QAction(printIcon, "Print...", self)
        self.printAction.setToolTip("Print the current design")

        printPreviewIcon = QIcon(":/icons/printer--arrow.png")
        self.printPreviewAction = QAction(printPreviewIcon, "Print Preview...", self)
        self.printPreviewAction.setToolTip("Preview the current design output")

        exportImageIcon = QIcon(":/icons/image-export.png")
        self.exportImageAction = QAction(exportImageIcon, "Export...", self)
        self.exportImageAction.setToolTip("Export the current design as an image")

        exitIcon = QIcon(":/icons/external.png")
        self.exitAction = QAction(exitIcon, "Close Window", self)
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.setToolTip("Close the current window")

        fitIcon = QIcon(":/icons/zone.png")
        self.fitAction = QAction(fitIcon, "Fit to Window", self)
        self.fitAction.setToolTip("Fit the design to the window")

        zoomInIcon = QIcon(":/icons/zone-resize.png")
        self.zoomInAction = QAction(zoomInIcon, "Zoom In", self)
        self.zoomInAction.setToolTip("Zoom in on the design")

        zoomOutIcon = QIcon(":/icons/zone-resize-actual.png")
        self.zoomOutAction = QAction(zoomOutIcon, "Zoom Out", self)
        self.zoomOutAction.setToolTip("Zoom out on the design")

        panIcon = QIcon(":/icons/zone--arrow.png")
        self.panAction = QAction(panIcon, "Pan View", self)
        self.panAction.setToolTip("Pan the design")

        redrawIcon = QIcon(":/icons/arrow-circle.png")
        self.redrawAction = QAction(redrawIcon, "Redraw", self)
        self.redrawAction.setToolTip("Redraw the design on the screen")

        rulerIcon = QIcon(":/icons/ruler.png")
        self.rulerAction = QAction(rulerIcon, "Add Ruler", self)
        self.rulerAction.setToolTip("Add a ruler to the layout")

        delRulerIcon = QIcon.fromTheme(":/icons/ruler--minus.png")
        self.delRulerAction = QAction(delRulerIcon, "Delete Rulers", self)
        self.delRulerAction.setToolTip("Delete all the rulers from the layout")

        # display options
        dispConfigIcon = QIcon(":/icons/grid-snap-dot.png")
        self.dispConfigAction = QAction(dispConfigIcon, "Display Config...", self)
        self.dispConfigAction.setToolTip("Configure the display options")

        selectConfigIcon = QIcon(":/icons/zone-select.png")
        self.selectConfigAction = QAction(selectConfigIcon, "Selection Config...", self)
        self.selectConfigAction.setToolTip("Configure the selection options")

        panZoomConfigIcon = QIcon(":/icons/selection-resize.png")
        self.panZoomConfigAction = QAction(
            panZoomConfigIcon, "Pan/Zoom Config...", self
        )
        self.panZoomConfigAction.setToolTip("Configure the pan/zoom options")

        undoIcon = QIcon(":/icons/arrow-circle-315-left.png")
        self.undoAction = QAction(undoIcon, "Undo", self)
        self.undoAction.setToolTip("Undo the last action")

        redoIcon = QIcon(":/icons/arrow-circle-225.png")
        self.redoAction = QAction(redoIcon, "Redo", self)
        self.redoAction.setToolTip("Redo the last undone action")

        yankIcon = QIcon(":/icons/node-insert.png")
        self.yankAction = QAction(yankIcon, "Yank", self)

        pasteIcon = QIcon(":/icons/clipboard-paste.png")
        self.pasteAction = QAction(pasteIcon, "Paste", self)
        self.pasteAction.setToolTip("Paste the contents of the clipboard")

        deleteIcon = QIcon(":/icons/node-delete.png")
        self.deleteAction = QAction(deleteIcon, "Delete", self)
        self.deleteAction.setToolTip("Delete selected items")

        copyIcon = QIcon(":/icons/document-copy.png")
        self.copyAction = QAction(copyIcon, "Copy", self)
        self.copyAction.setToolTip("Copy selected items")

        moveIcon = QIcon(":/icons/arrow-move.png")
        self.moveAction = QAction(moveIcon, "Move", self)
        self.moveAction.setToolTip("Move selected items")

        moveByIcon = QIcon(":/icons/arrow-transition.png")
        self.moveByAction = QAction(moveByIcon, "Move By ...", self)
        self.moveAction.setToolTip("Move selected items by an offset")

        moveOriginIcon = QIcon(":/icons/arrow-skip.png")
        self.moveOriginAction = QAction(moveOriginIcon, "Move Origin", self)
        self.moveOriginAction.setToolTip("Move the origin of the design")

        stretchIcon = QIcon(":/icons/fill.png")
        self.stretchAction = QAction(stretchIcon, "Stretch", self)
        self.stretchAction.setToolTip("Stretch item")

        rotateIcon = QIcon(":/icons/arrow-circle.png")
        self.rotateAction = QAction(rotateIcon, "Rotate...", self)
        self.rotateAction.setToolTip("Rotate item")

        scaleIcon = QIcon(":/icons/selection-resize.png")
        self.scaleAction = QAction(scaleIcon, "Scale...", self)
        self.scaleAction.setToolTip("Scale item")

        netNameIcon = QIcon(":/icons/node-design.png")
        self.netNameAction = QAction(netNameIcon, "Net Name...", self)
        self.netNameAction.setToolTip("Set net name")

        # create label action but do not add to any menu.
        createLabelIcon = QIcon(":/icons/tag-label-yellow.png")
        self.createLabelAction = QAction(createLabelIcon, "Create Label...", self)
        self.createLabelAction.setToolTip("Create Label")

        createPinIcon = QIcon(":/icons/pin.png")
        self.createPinAction = QAction(createPinIcon, "Create Pin...", self)
        self.createPinAction.setToolTip("Create Pin")

        goUpIcon = QIcon(":/icons/arrow-step-out.png")
        self.goUpAction = QAction(goUpIcon, "Go Up", self)
        self.goUpAction.setToolTip("Go up a level in design hierarchy")

        goDownIcon = QIcon(":/icons/arrow-step.png")
        self.goDownAction = QAction(goDownIcon, "Go Down", self)
        self.goDownAction.setToolTip("Go down a level in design hierarchy")

        self.selectAllIcon = QIcon(":/icons/node-select-all.png")
        self.selectAllAction = QAction(self.selectAllIcon, "Select All", self)
        self.selectAllAction.setToolTip("Select all items in the design")

        deselectAllIcon = QIcon(":/icons/node.png")
        self.deselectAllAction = QAction(deselectAllIcon, "Unselect All", self)
        self.deselectAllAction.setToolTip("Unselect all items in the design")

        objPropIcon = QIcon(":/icons/property-blue.png")
        self.objPropAction = QAction(objPropIcon, "Object Properties...", self)
        self.objPropAction.setToolTip("Configure object properties")

        viewPropIcon = QIcon(":/icons/property.png")
        self.viewPropAction = QAction(viewPropIcon, "Cellview Properties...", self)
        self.viewPropAction.setToolTip("Configure Cellview Properties")

        viewCheckIcon = QIcon(":/icons/ui-check-box.png")
        self.viewCheckAction = QAction(viewCheckIcon, "Check CellView", self)
        self.viewCheckAction.setToolTip("Check Cellview")

        viewErrorsIcon = QIcon(":/icons/report--exclamation.png")
        self.viewErrorsAction = QAction(viewErrorsIcon, "View Errors...", self)
        self.viewErrorsAction.setToolTip("View Errros")

        deleteErrorsIcon = QIcon(":/icons/report--minus.png")
        self.deleteErrorsAction = QAction(deleteErrorsIcon, "Delete Errors...", self)
        self.deleteErrorsAction.setToolTip("Delete Errros")

        netlistIcon = QIcon(":/icons/script-text.png")
        self.netlistAction = QAction(netlistIcon, "Create Netlist...", self)
        self.netlistAction.setToolTip("Create Netlist")

        createLineIcon = QIcon(":/icons/layer-shape-line.png")
        self.createLineAction = QAction(createLineIcon, "Create Line...", self)
        self.createLineAction.setToolTip("Create Line")

        createRectIcon = QIcon(":/icons/layer-shape.png")
        self.createRectAction = QAction(createRectIcon, "Create Rectangle...", self)
        self.createRectAction.setToolTip("Create Rectangle")

        createPolyIcon = QIcon(":/icons/layer-shape-polygon.png")
        self.createPolygonAction = QAction(createPolyIcon, "Create Polygon...", self)
        self.createPolygonAction.setToolTip("Create Polygon")

        createCircleIcon = QIcon(":/icons/layer-shape-ellipse.png")
        self.createCircleAction = QAction(createCircleIcon, "Create Circle...", self)
        self.createCircleAction.setToolTip("Create Circle")

        createArcIcon = QIcon(":/icons/layer-shape-polyline.png")
        self.createArcAction = QAction(createArcIcon, "Create Arc...", self)
        self.createArcAction.setToolTip("Create Arc")

        createViaIcon = QIcon(":/icons/layer-mask.png")
        self.createViaAction = QAction(createViaIcon, "Create Via...", self)
        self.createViaAction.setToolTip("Create Via")

        createInstIcon = QIcon(":/icons/block--plus.png")
        self.createInstAction = QAction(createInstIcon, "Create Instance...", self)
        self.createInstAction.setToolTip("Create Instance")

        self.createNetAction = QAction(createLineIcon, "Create Net...", self)
        self.createNetAction.setToolTip("Create Net")

        self.createPathAction = QAction(createLineIcon, "Create Path...", self)
        self.createPathAction.setToolTip("Create Path")

        createBusIcon = QIcon(":/icons/node-select-all.png")
        self.createBusAction = QAction(createBusIcon, "Create Bus...", self)
        self.createBusAction.setToolTip("Create Bus")

        createSymbolIcon = QIcon(":/icons/application-block.png")
        self.createSymbolAction = QAction(createSymbolIcon, "Create Symbol...", self)
        self.createSymbolAction.setToolTip("Create Symbol from Cellview")

        createTextIcon = QIcon(":icons/sticky-note-text.png")
        self.createTextAction = QAction(createTextIcon, "Create Text...", self)
        self.createTextAction.setToolTip("Create Text")

        # selection Actions
        selectDeviceIcon = QIcon(":icons/target.png")
        self.selectDeviceAction = QAction(selectDeviceIcon, "Select Devices", self)
        self.selectDeviceAction.setToolTip("Select Devices Only")

        selectNetIcon = QIcon(":icons/pencil--plus.png")
        self.selectNetAction = QAction(selectNetIcon, "Select Nets", self)
        self.selectNetAction.setToolTip("Select Nets Only")

        self.selectWireAction = QAction(selectNetIcon, "Select Wires", self)
        self.selectWireAction.setToolTip("Select Wires Only")

        selectPinIcon = QIcon(":/icons/pin--plus.png")
        self.selectPinAction = QAction(selectPinIcon, "Select Pins", self)
        self.selectPinAction.setToolTip("Select Pins Only")

        removeSelectFilterIcon = QIcon(":icons/eraser.png")
        self.removeSelectFilterAction = QAction(
            removeSelectFilterIcon, "Remove Select Filters", self
        )
        self.removeSelectFilterAction.setToolTip("Remove Selection Filters")

        ignoreIcon = QIcon(":/icons/minus-circle.png")
        self.ignoreAction = QAction(ignoreIcon, "Ignore", self)
        self.ignoreAction.setToolTip("Ignore selected cell")

        helpIcon = QIcon(":/icons/document-arrow.png")
        self.helpAction = QAction(helpIcon, "Help...", self)
        self.helpAction.setToolTip("Help")

        self.aboutIcon = QIcon(":/icons/information.png")
        self.aboutAction = QAction(self.aboutIcon, "About", self)
        self.aboutAction.setToolTip("About Revolution EDA")

    def _createToolBars(self):
        # Create tools bar called "main toolbar"
        self.toolbar = QToolBar("Main Toolbar", self)
        # place toolbar at top
        self.addToolBar(self.toolbar)
        self.toolbar.addAction(self.printAction)
        self.toolbar.addAction(self.exportImageAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.undoAction)
        self.toolbar.addAction(self.redoAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.deleteAction)
        self.toolbar.addAction(self.moveAction)
        self.toolbar.addAction(self.copyAction)
        self.toolbar.addAction(self.stretchAction)
        self.toolbar.addAction(self.rotateAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.fitAction)
        self.toolbar.addAction(self.zoomInAction)
        self.toolbar.addAction(self.zoomOutAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.objPropAction)

    def _addActions(self):
        # file menu
        self.menuFile.addAction(self.checkCellAction)
        self.menuFile.addAction(self.saveCellAction)
        self.menuFile.addAction(self.updateCellAction)
        self.menuFile.addAction(self.printAction)
        self.menuFile.addAction(self.printPreviewAction)
        self.menuFile.addAction(self.exportImageAction)
        self.menuFile.addAction(self.exitAction)
        # view menu
        self.menuView.addAction(self.fitAction)
        self.menuView.addAction(self.zoomInAction)
        self.menuView.addAction(self.zoomOutAction)
        self.menuView.addAction(self.panAction)
        self.menuView.addAction(self.redrawAction)
        self.menuView.addAction(self.panZoomConfigAction)
        # edit menu
        self.menuEdit.addAction(self.undoAction)
        self.menuEdit.addAction(self.redoAction)
        # self.menuEdit.addAction(self.yankAction)
        self.menuEdit.addAction(self.pasteAction)
        self.menuEdit.addAction(self.deleteAction)
        self.menuEdit.addAction(self.copyAction)
        self.menuEdit.addAction(self.moveAction)
        self.menuEdit.addAction(self.moveByAction)
        self.menuEdit.addAction(self.moveOriginAction)
        self.menuEdit.addAction(self.stretchAction)
        self.menuEdit.addAction(self.rotateAction)
        self.selectMenu = QMenu('Selection', self)
        self.selectMenu.setIcon(QIcon('icons/node-select.png'))
        self.menuEdit.addMenu(self.selectMenu)
        self.selectMenu.addAction(self.selectAllAction)
        self.selectMenu.addAction(self.deselectAllAction)
        self.menuTools.addAction(self.readOnlyCellAction)
        # self.menuCheck.addAction(self.viewCheckAction)
        self.menuOptions.addAction(self.dispConfigAction)
        self.menuOptions.addAction(self.selectConfigAction)
        self.menuHelp.addAction(self.helpAction)
        self.menuHelp.addAction(self.aboutAction)

    def helpClick(self):
        helpBrowser = hlp.helpBrowser(self)
        helpBrowser.show()

    def aboutClick(self):
        abtDlg = hlp.aboutDialog(self)
        abtDlg.show()

    def _createTriggers(self):
        self.checkCellAction.triggered.connect(self.checkSaveCell)
        self.saveCellAction.triggered.connect(self.saveCell)
        self.readOnlyCellAction.triggered.connect(self.readOnlyCellClick)
        self.updateCellAction.triggered.connect(self.updateDesignScene)
        self.printAction.triggered.connect(self.printClick)
        self.printPreviewAction.triggered.connect(self.printPreviewClick)
        self.exportImageAction.triggered.connect(self.imageExportClick)
        self.exitAction.triggered.connect(self.closeWindow)
        self.fitAction.triggered.connect(self.fitToWindow)
        self.redrawAction.triggered.connect(self.redraw)
        self.zoomInAction.triggered.connect(self.zoomIn)
        self.zoomOutAction.triggered.connect(self.zoomOut)
        self.panAction.triggered.connect(self.panView)
        self.dispConfigAction.triggered.connect(self.dispConfigEdit)
        self.selectConfigAction.triggered.connect(self.selectConfigEdit)
        self.stretchAction.triggered.connect(self.stretchClick)
        self.moveOriginAction.triggered.connect(self.moveOrigin)
        self.selectAllAction.triggered.connect(self.selectAllClick)
        self.deselectAllAction.triggered.connect(self.deselectAllClick)
        self.deleteAction.triggered.connect(self.deleteClick)
        self.copyAction.triggered.connect(self.copyClick)
        self.undoAction.triggered.connect(self.undoClick)
        self.redoAction.triggered.connect(self.redoClick)
        self.moveByAction.triggered.connect(self.moveByClick)
        self.rotateAction.triggered.connect(self.rotateItemClick)
        self.goUpAction.triggered.connect(self.goUpHierarchy)
        self.helpAction.triggered.connect(self.helpClick)
        self.aboutAction.triggered.connect(self.aboutClick)

    def _createShortcuts(self):
        self.redoAction.setShortcut("Shift+U")
        self.undoAction.setShortcut(Qt.Key_U)
        self.objPropAction.setShortcut(Qt.Key_Q)
        self.copyAction.setShortcut(Qt.Key_C)
        self.rotateAction.setShortcut("Ctrl+R")
        self.createTextAction.setShortcut("Shift+L")
        self.fitAction.setShortcut(Qt.Key_F)
        self.deleteAction.setShortcut(QKeySequence.Delete)
        self.selectAllAction.setShortcut("Ctrl+A")
        self.stretchAction.setShortcut(Qt.Key_S)

    def _editorContextMenu(self):
        self.centralW.scene.itemContextMenu.addAction(self.copyAction)
        self.centralW.scene.itemContextMenu.addAction(self.moveByAction)
        self.centralW.scene.itemContextMenu.addAction(self.rotateAction)
        self.centralW.scene.itemContextMenu.addAction(self.deleteAction)
        self.centralW.scene.itemContextMenu.addAction(self.objPropAction)
        self.centralW.scene.itemContextMenu.addAction(self.selectAllAction)
        self.centralW.scene.itemContextMenu.addAction(self.deselectAllAction)

    def dispConfigEdit(self):
        dcd = pdlg.displayConfigDialog(self)
        dcd.majorGridEntry.setText(str(self.majorGrid))
        dcd.snapGridEdit.setText(str(self.snapGrid))
        if dcd.exec() == QDialog.Accepted:
            self.majorGrid = int(float(dcd.majorGridEntry.text()))
            self.snapGrid = int(float(dcd.snapGridEdit.text()))
            self.snapTuple = (self.majorGrid, self.majorGrid)
            self.centralW.view.majorGrid = self.majorGrid
            self.centralW.view.snapGrid = self.snapGrid
            self.centralW.view.snapTuple = self.snapTuple
            self.centralW.scene.majorGrid = self.majorGrid
            self.centralW.scene.snapGrid = self.snapGrid
            self.centralW.scene.snapTuple = self.snapTuple

            if dcd.dotType.isChecked():
                self.centralW.view.gridbackg = True
                self.centralW.view.linebackg = False
            elif dcd.lineType.isChecked():
                self.centralW.view.gridbackg = False
                self.centralW.view.linebackg = True
            else:
                self.centralW.view.gridbackg = False
                self.centralW.view.linebackg = False
            self.centralW.view.resetCachedContent()

    def selectConfigEdit(self):
        scd = pdlg.selectConfigDialogue(self)
        if self.centralW.scene.partialSelection:
            scd.partialSelection.setChecked(True)
        else:
            scd.fullSelection.setChecked(True)
        scd.snapDistanceEntry.setText(str(self.snapDistance))
        if scd.exec() == QDialog.Accepted:
            self.centralW.scene.partialSelection = scd.partialSelection.isChecked()
            self.snapDistance = int(float(scd.snapDistanceEntry.text()))

    def checkSaveCell(self):
        pass

    def saveCell(self):
        pass

    def readOnlyCellClick(self):
        self.centralW.scene.readOnly = self.readOnlyCellAction.isChecked()

    def updateDesignScene(self):
        self.messageLine.setText("Reloading design.")
        self.centralW.scene.reloadScene()

    def printClick(self):
        dlg = QPrintDialog(self)
        if dlg.exec() == QDialog.Accepted:
            printer = dlg.printer()
            printRunner = startThread(self.centralW.view.printView(printer))
            self.appMainW.threadPool.start(printRunner)
            self.logger.info(
                "Printing started"
            )  # self.centralW.view.printView(printer)

    def printPreviewClick(self):
        printer = QPrinter(QPrinter.ScreenResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        ppdlg = QPrintPreviewDialog(self)
        ppdlg.paintRequested.connect(self.centralW.view.printView)
        ppdlg.exec()

    def imageExportClick(self):
        image = QImage(
            self.centralW.view.viewport().size(), QImage.Format_ARGB32_Premultiplied
        )
        self.centralW.view.printView(image)
        fdlg = QFileDialog(self, caption="Select or create an image file")
        fdlg.setDefaultSuffix("png")
        fdlg.setFileMode(QFileDialog.AnyFile)
        fdlg.setViewMode(QFileDialog.Detail)
        fdlg.setNameFilter("Image Files (*.png *.jpg *.bmp *.gif *.jpeg")
        if fdlg.exec() == QDialog.Accepted:
            imageFile = fdlg.selectedFiles()[0]
            image.save(imageFile)

    def deleteClick(self, s):
        self.centralW.scene.editModes.setMode("deleteItem")
        self.centralW.scene.deleteSelectedItems()

    def selectAllClick(self):
        self.centralW.scene.selectAll()

    def deselectAllClick(self):
        self.centralW.scene.deselectAll()

    def stretchClick(self, s):
        self.centralW.scene.editModes.setMode("stretchItem")
        self.centralW.scene.stretchSelectedItems()

    def moveClick(self):
        self.centralW.scene.editModes.setMode("moveItem")

    def moveByClick(self):
        self.centralW.scene.editModes.setMode("moveItem")
        self.centralW.scene.moveBySelectedItems()

    def rotateClick(self):
        self.centralW.scene.editModes.setMode("rotateItem")

    def panView(self):
        self.centralW.scene.editModes.setMode("panView")
        self.messageLine.setText("Click on the view to pan it")

    def goUpHierarchy(self):
        self.saveCell()
        if self.parentEditor is not None:
            self.parentEditor.updateDesignScene()
            self.parentEditor.raise_()
        self.close()

    def fitToWindow(self):
        self.centralW.scene.fitItemsInView()

    def copyClick(self, s):
        self.centralW.scene.editModes.setMode("copyItem")
        self.centralW.scene.copySelectedItems()

    def zoomIn(self):
        self.centralW.view.scale(1.25, 1.25)

    def zoomOut(self):
        self.centralW.view.scale(0.8, 0.8)

    def closeWindow(self):
        self.close()

    def closeEvent(self, event):
        cellViewTuple = ddef.viewTuple(self.libName, self.cellName, self.viewName)
        self.appMainW.openViews.pop(cellViewTuple)
        event.accept()
        super().closeEvent(event)

    def moveOrigin(self):
        self.centralW.scene.editModes.setMode("changeOrigin")

    def undoClick(self, s):
        self.centralW.scene.undoStack.undo()

    def redoClick(self, s):
        self.centralW.scene.undoStack.redo()

    def rotateItemClick(self, s):
        self.centralW.scene.editModes.setMode("rotateItem")

    def redraw(self):
        self.messageLine.setText("Redrawing...")
        self.centralW.view.update()


class layoutEditor(editorWindow):
    def __init__(self, viewItem: scb.viewItem, libraryDict: dict, libraryView) -> None:
        super().__init__(viewItem, libraryDict, libraryView)
        self.setWindowTitle(f"Layout Editor - {self.cellName} - {self.viewName}")
        self.setWindowIcon(QIcon(":/icons/edLayer-shape.png"))
        self.layoutViews = ["layout", "pcell"]
        self.dbu = fabproc.dbu
        self.layoutChooser = None
        self.gdsExportDir = pathlib.Path.cwd()
        self._layoutContextMenu()

    def init_UI(self):
        super().init_UI()
        # create container to position all widgets
        self.centralW = layoutContainer(self)
        self.setCentralWidget(self.centralW)

    def _createMenuBar(self):
        super()._createMenuBar()
        self.alignMenu = QMenu('Align', self)
        self.alignMenu.setIcon(QIcon('icons/layers-alignment-middle.png'))

        self.propertyMenu = self.menuEdit.addMenu("Properties")

    def _createActions(self):
        super()._createActions()
        self.exportGDSAction = QAction("Export GDS", self)
        self.exportGDSAction.setToolTip("Export GDS from Layout")

    def _addActions(self):
        super()._addActions()
        self.menuEdit.addMenu(self.alignMenu)
        # self.menuUtilities.addMenu(self.selectMenu)
        self.selectMenu.addAction(self.selectDeviceAction)
        self.selectMenu.addAction(self.selectWireAction)
        self.selectMenu.addSeparator()
        self.selectMenu.addAction(self.removeSelectFilterAction)

        self.propertyMenu.addAction(self.objPropAction)
        self.menuEdit.addAction(self.stretchAction)
        self.menuCreate.addAction(self.createInstAction)
        self.menuCreate.addAction(self.createRectAction)
        self.menuCreate.addAction(self.createPathAction)
        self.menuCreate.addAction(self.createPinAction)
        self.menuCreate.addAction(self.createLabelAction)
        self.menuCreate.addAction(self.createViaAction)
        self.menuCreate.addAction(self.createPolygonAction)
        self.menuCreate.addSeparator()
        self.menuCreate.addAction(self.rulerAction)
        self.menuCreate.addAction(self.delRulerAction)
        self.menuTools.addAction(self.exportGDSAction)
        # hierarchy submenu
        self.hierMenu = self.menuEdit.addMenu("Hierarchy")
        self.hierMenu.addAction(self.goUpAction)
        self.hierMenu.addAction(self.goDownAction)

    def _layoutContextMenu(self):
        super()._editorContextMenu()
        self.centralW.scene.itemContextMenu.addAction(self.goDownAction)

    def _createToolBars(self):
        super()._createToolBars()
        self.layoutToolbar = QToolBar("Layout Toolbar", self)
        self.addToolBar(self.layoutToolbar)
        self.layoutToolbar.addAction(self.createInstAction)
        self.layoutToolbar.addAction(self.createRectAction)
        self.layoutToolbar.addAction(self.createPathAction)
        self.layoutToolbar.addAction(self.createPinAction)
        self.layoutToolbar.addAction(self.createLabelAction)
        self.layoutToolbar.addAction(self.createViaAction)
        self.layoutToolbar.addAction(self.createPolygonAction)
        self.layoutToolbar.addSeparator()
        self.layoutToolbar.addAction(self.rulerAction)
        self.layoutToolbar.addAction(self.delRulerAction)
        self.layoutToolbar.addSeparator()
        self.layoutToolbar.addAction(self.goDownAction)
        self.layoutToolbar.addSeparator()
        self.layoutToolbar.addAction(self.removeSelectFilterAction)
        self.layoutToolbar.addAction(self.selectWireAction)
        self.layoutToolbar.addAction(self.selectDeviceAction)

    def _createTriggers(self):
        super()._createTriggers()

        self.createInstAction.triggered.connect(self.createInstClick)
        self.createRectAction.triggered.connect(self.createRectClick)
        self.exportGDSAction.triggered.connect(self.exportGDSClick)
        self.createPathAction.triggered.connect(self.createPathClick)
        self.createPinAction.triggered.connect(self.createPinClick)
        self.createLabelAction.triggered.connect(self.createLabelClick)
        self.createViaAction.triggered.connect(self.createViaClick)
        self.createPolygonAction.triggered.connect(self.createPolygonClick)
        self.rulerAction.triggered.connect(self.createRulerClick)
        self.delRulerAction.triggered.connect(self.delRulerClick)
        self.deleteAction.triggered.connect(self.deleteClick)
        self.objPropAction.triggered.connect(self.objPropClick)

        self.goDownAction.triggered.connect(self.goDownClick)

    def _createShortcuts(self):
        super()._createShortcuts()
        self.createRectAction.setShortcut(Qt.Key_R)
        self.createPathAction.setShortcut(Qt.Key_W)
        self.createInstAction.setShortcut(Qt.Key_I)
        self.createPinAction.setShortcut(Qt.Key_P)
        self.createLabelAction.setShortcut(Qt.Key_L)
        self.createViaAction.setShortcut(Qt.Key_V)
        self.createPolygonAction.setShortcut(Qt.Key_G)
        self.stretchAction.setShortcut(Qt.Key_S)
        self.rulerAction.setShortcut(Qt.Key_K)
        self.delRulerAction.setShortcut("Shift+K")

    def createRectClick(self, s):
        self.centralW.scene.editModes.setMode("drawRect")

    def createRulerClick(self, s):
        self.centralW.scene.editModes.setMode("drawRuler")
        self.messageLine.setText("Click on the first point of the ruler.")

    def delRulerClick(self, s):
        self.messageLine.setText("Deleting all rulers")
        self.centralW.scene.deleteAllRulers()
        self.centralW.scene.editModes.setMode("selectItem")

    def createPathClick(self, s):
        dlg = ldlg.createPathDialogue(self)
        # paths are created on drawing layers
        dlg.pathLayerCB.addItems(
            [f"{item.name} [{item.purpose}]" for item in laylyr.pdkDrawingLayers]
        )
        dlg.pathWidth.setText("1.0")
        dlg.startExtendEdit.setText("0.5")
        dlg.endExtendEdit.setText("0.5")

        if dlg.exec() == QDialog.Accepted:
            self.centralW.scene.editModes.setMode("drawPath")
            if dlg.manhattanButton.isChecked():
                pathMode = 0
            elif dlg.diagonalButton.isChecked():
                pathMode = 1
            elif dlg.anyButton.isChecked():
                pathMode = 2
            elif dlg.horizontalButton.isChecked():
                pathMode = 3
            elif dlg.verticalButton.isChecked():
                pathMode = 4
            else:
                pathMode = 0
            if dlg.pathWidth.text().strip():
                pathWidth = fabproc.dbu * float(dlg.pathWidth.text().strip())
            else:
                pathWidth = fabproc.dbu * 1.0
            pathName = dlg.pathNameEdit.text()
            pathLayerName = dlg.pathLayerCB.currentText().split()[0]
            pathLayer = [
                item for item in laylyr.pdkDrawingLayers if item.name == pathLayerName
            ][0]
            startExtend = float(dlg.startExtendEdit.text().strip()) * fabproc.dbu
            endExtend = float(dlg.endExtendEdit.text().strip()) * fabproc.dbu
            self.centralW.scene.newPathTuple = ddef.layoutPathTuple(
                pathLayer, pathName, pathMode, pathWidth, startExtend, endExtend
            )

    def createPinClick(self):
        dlg = ldlg.createLayoutPinDialog(self)
        pinLayersNames = [
            f"{item.name} [{item.purpose}]" for item in laylyr.pdkPinLayers
        ]
        textLayersNames = [
            f"{item.name} [{item.purpose}]" for item in laylyr.pdkTextLayers
        ]
        dlg.pinLayerCB.addItems(pinLayersNames)
        dlg.labelLayerCB.addItems(textLayersNames)

        if self.centralW.scene.newPinTuple is not None:
            dlg.pinLayerCB.setCurrentText(
                f"{self.centralW.scene.newPinTuple.pinLayer.name} "
                f"[{self.centralW.scene.newPinTuple.pinLayer.purpose}]"
            )
        if self.centralW.scene.newLabelTuple is not None:
            dlg.labelLayerCB.setCurrentText(
                f"{self.centralW.scene.newLabelTuple.labelLayer.name} ["
                f"{self.centralW.scene.newLabelTuple.labelLayer.purpose}]"
            )
            dlg.familyCB.setCurrentText(self.centralW.scene.newLabelTuple.fontFamily)
            dlg.fontStyleCB.setCurrentText(self.centralW.scene.newLabelTuple.fontStyle)
            dlg.labelHeightCB.setCurrentText(
                str(self.centralW.scene.newLabelTuple.fontHeight)
            )
            dlg.labelAlignCB.setCurrentText(
                self.centralW.scene.newLabelTuple.labelAlign
            )
            dlg.labelOrientCB.setCurrentText(
                self.centralW.scene.newLabelTuple.labelOrient
            )
        if dlg.exec() == QDialog.Accepted:
            self.centralW.scene.editModes.setMode("drawPin")
            pinName = dlg.pinName.text()
            pinDir = dlg.pinDir.currentText()
            pinType = dlg.pinType.currentText()
            pinLayerName = dlg.pinLayerCB.currentText().split()[0]
            pinLayer = [
                item for item in laylyr.pdkPinLayers if item.name == pinLayerName
            ][0]
            labelLayerName = dlg.labelLayerCB.currentText().split()[0]
            labelLayer = [
                item for item in laylyr.pdkTextLayers if item.name == labelLayerName
            ][0]
            fontFamily = dlg.familyCB.currentText()
            fontStyle = dlg.fontStyleCB.currentText()
            labelHeight = float(dlg.labelHeightCB.currentText())
            labelAlign = dlg.labelAlignCB.currentText()
            labelOrient = dlg.labelOrientCB.currentText()
            self.centralW.scene.newPinTuple = ddef.layoutPinTuple(
                pinName, pinDir, pinType, pinLayer
            )
            self.centralW.scene.newLabelTuple = ddef.layoutLabelTuple(
                pinName,
                fontFamily,
                fontStyle,
                labelHeight,
                labelAlign,
                labelOrient,
                labelLayer,
            )

    def createLabelClick(self):
        dlg = ldlg.createLayoutLabelDialog(self)
        textLayersNames = [
            f"{item.name} [{item.purpose}]" for item in laylyr.pdkTextLayers
        ]
        dlg.labelLayerCB.addItems(textLayersNames)
        if dlg.exec() == QDialog.Accepted:
            self.centralW.scene.editModes.setMode("addLabel")
            labelName = dlg.labelName.text()
            labelLayerName = dlg.labelLayerCB.currentText().split()[0]
            labelLayer = [
                item for item in laylyr.pdkTextLayers if item.name == labelLayerName
            ][0]
            fontFamily = dlg.familyCB.currentText()
            fontStyle = dlg.fontStyleCB.currentText()
            fontHeight = float(dlg.labelHeightCB.currentText())
            labelAlign = dlg.labelAlignCB.currentText()
            labelOrient = dlg.labelOrientCB.currentText()
            self.centralW.scene.newLabelTuple = ddef.layoutLabelTuple(
                labelName,
                fontFamily,
                fontStyle,
                fontHeight,
                labelAlign,
                labelOrient,
                labelLayer,
            )

    def createViaClick(self):
        dlg = ldlg.createLayoutViaDialog(self)

        if dlg.exec() == QDialog.Accepted:
            self.centralW.scene.editModes.setMode("addVia")
            self.centralW.scene.addVia = True
            if dlg.singleViaRB.isChecked():
                # selViaDefTuple = [
                #     viaDefTuple
                #     for viaDefTuple in fabproc.processVias
                #     if viaDefTuple.name == dlg.singleViaNamesCB.currentText()
                # ][0]
                selViaDefTuple = fabproc.processVias[
                    fabproc.processViaNames.index(dlg.singleViaNamesCB.currentText())
                ]

                singleViaTuple = ddef.singleViaTuple(
                    selViaDefTuple,
                    fabproc.dbu * float(dlg.singleViaWidthEdit.text().strip()),
                    fabproc.dbu * float(dlg.singleViaHeightEdit.text().strip()),
                )
                self.centralW.scene.arrayViaTuple = ddef.arrayViaTuple(
                    singleViaTuple, fabproc.dbu * float(selViaDefTuple.minSpacing),
                    fabproc.dbu * float(selViaDefTuple.minSpacing), 1, 1
                )
            else:
                selViaDefTuple = [
                    viaDefTuple
                    for viaDefTuple in fabproc.processVias
                    if viaDefTuple.name == dlg.arrayViaNamesCB.currentText()
                ][0]

                singleViaTuple = ddef.singleViaTuple(
                    selViaDefTuple,
                    fabproc.dbu * float(dlg.arrayViaWidthEdit.text().strip()),
                    fabproc.dbu * float(dlg.arrayViaHeightEdit.text().strip()),
                )
                self.centralW.scene.arrayViaTuple = ddef.arrayViaTuple(
                    singleViaTuple,
                    fabproc.dbu * float(dlg.arrayViaSpacingEdit.text().strip()),
                    fabproc.dbu * float(dlg.arrayViaSpacingEdit.text().strip()),
                    int(float(dlg.arrayXNumEdit.text().strip())),
                    int(float(dlg.arrayYNumEdit.text().strip())),
                )
        else:
            self.centralW.scene.editModes.setMode("selectItem")

    def createPolygonClick(self):
        self.centralW.scene.editModes.setMode("drawPolygon")

    def objPropClick(self, s):
        self.centralW.scene.viewObjProperties()

    def goDownClick(self):
        self.centralW.scene.goDownHier()

    def checkSaveCell(self):
        self.centralW.scene.saveLayoutCell(self.file)

    def saveCell(self):
        self.centralW.scene.saveLayoutCell(self.file)

    def loadLayout(self):
        self.centralW.scene.loadLayoutCell(self.file)


    def createInstClick(self, s):
        # create a designLibrariesView
        libraryModel = lmview.layoutViewsModel(self.libraryDict, self.layoutViews)
        if self.layoutChooser is None:
            self.layoutChooser = fd.selectCellViewDialog(self, libraryModel)
            self.layoutChooser.show()
        else:
            self.layoutChooser.raise_()
        if self.layoutChooser.exec() == QDialog.Accepted:
            self.centralW.scene.editModes.setMode("addInstance")
            libItem = libm.getLibItem(
                libraryModel, self.layoutChooser.libNamesCB.currentText()
            )
            cellItem = libm.getCellItem(
                libItem, self.layoutChooser.cellCB.currentText()
            )
            viewItem = libm.getViewItem(
                cellItem, self.layoutChooser.viewCB.currentText()
            )
            self.centralW.scene.layoutInstanceTuple = ddef.viewItemTuple(
                libItem, cellItem, viewItem
            )

    def exportGDSClick(self):
        dlg = fd.gdsExportDialogue(self)
        dlg.unitEdit.setText("1 um")
        dlg.precisionEdit.setText("1 nm")
        dlg.exportPathEdit.setText(str(self.gdsExportDir))

        if dlg.exec() == QDialog.Accepted:
            self.gdsExportDir = pathlib.Path(dlg.exportPathEdit.text().strip())
            gdsExportPath = self.gdsExportDir / f"{self.cellName}.gds"
            # reprocess the layout to get the layout positions right.
            topLevelItems = [
                item
                for item in self.centralW.scene.items()
                if item.parentItem() is None
            ]
            decodedData = json.loads(
                json.dumps(topLevelItems, cls=layenc.layoutEncoder)
            )
            layoutItems = [
                lj.layoutItems(self.centralW.scene).create(item)
                for item in decodedData
                if item.get("type") in self.centralW.scene.layoutShapes
            ]

            gdsExportObj = gdse.gdsExporter(self.cellName, layoutItems, gdsExportPath)
            gdsExportObj.unit = Quantity(dlg.unitEdit.text().strip()).real
            gdsExportObj.precision = Quantity(dlg.precisionEdit.text().strip()).real
            if gdsExportObj:
                gdsExportRunner = startThread(gdsExportObj.gds_export())
                self.appMainW.threadPool.start(gdsExportRunner)
                # netlistObj.writeNetlist()
                self.logger.info("GDS Export is finished.")


class schematicEditor(editorWindow):
    def __init__(self, viewItem: scb.viewItem, libraryDict: dict, libraryView) -> None:
        super().__init__(viewItem, libraryDict, libraryView)
        self.setWindowTitle(f"Schematic Editor - {self.cellName} - {self.viewName}")
        self.setWindowIcon(QIcon(":/icons/edLayer-shape.png"))
        self.configDict = dict()
        self.processedCells = set()  # cells included in config view
        self.symbolChooser = None
        self.symbolViews = [
            "symbol"
        ]  # only symbol can be instantiated in the schematic window.
        self._schematicContextMenu()

    def init_UI(self):
        super().init_UI()
        self.resize(1600, 800)
        # create container to position all widgets
        self.centralW = schematicContainer(self)
        self.setCentralWidget(self.centralW)


    def _createActions(self):
        super()._createActions()
        self.netNameAction = QAction("Net Name", self)
        self.netNameAction.setToolTip("Set Net Name")
        self.netNameAction.setShortcut(Qt.Key_L)
        self.hilightNetAction = QAction("Highlight Net", self)
        self.hilightNetAction.setToolTip("Highlight Selected Net Connections")
        self.hilightNetAction.setCheckable(True)
        self.renumberInstanceAction = QAction("Renumber Instances", self)
        self.renumberInstanceAction.setToolTip("Renumber Instances")
        simulationIcon = QIcon("icons/application-run.png")
        self.simulateAction = QAction(simulationIcon, "Simulaiton GUI...", self)


    def _createTriggers(self):
        super()._createTriggers()

        self.createNetAction.triggered.connect(self.createNetClick)
        self.createInstAction.triggered.connect(self.createInstClick)
        self.createPinAction.triggered.connect(self.createPinClick)
        self.createTextAction.triggered.connect(self.createNoteClick)
        self.createSymbolAction.triggered.connect(self.createSymbolClick)

        self.objPropAction.triggered.connect(self.objPropClick)
        self.netlistAction.triggered.connect(self.createNetlistClick)
        self.simulateAction.triggered.connect(self.startSimClick)
        self.ignoreAction.triggered.connect(self.ignoreClick)
        self.goDownAction.triggered.connect(self.goDownClick)

        self.hilightNetAction.triggered.connect(self.hilightNetClick)
        self.netNameAction.triggered.connect(self.netNameClick)
        self.selectDeviceAction.triggered.connect(self.selectDeviceClick)
        self.selectNetAction.triggered.connect(self.selectNetClick)
        self.selectPinAction.triggered.connect(self.selectPinClick)
        self.removeSelectFilterAction.triggered.connect(self.removeSelectFilterClick)
        self.renumberInstanceAction.triggered.connect(self.renumberInstanceClick)


    def _addActions(self):
        super()._addActions()
        # edit menu
        self.menuEdit.addAction(self.netNameAction)

        self.propertyMenu = self.menuEdit.addMenu("Properties")
        self.propertyMenu.addAction(self.objPropAction)

        # hierarchy submenu
        self.hierMenu = self.menuEdit.addMenu("Hierarchy")
        self.hierMenu.addAction(self.goUpAction)
        self.hierMenu.addAction(self.goDownAction)

        # create menu
        self.menuCreate.addAction(self.createInstAction)
        self.menuCreate.addAction(self.createNetAction)
        # self.menuCreate.addAction(self.createBusAction)
        self.menuCreate.addAction(self.createPinAction)
        self.menuCreate.addAction(self.createTextAction)
        self.menuCreate.addAction(self.createSymbolAction)

        # check menu
        # self.menuCheck.addAction(self.viewErrorsAction)
        # self.menuCheck.addAction(self.deleteErrorsAction)

        # tools menu
        self.menuTools.addAction(self.hilightNetAction)
        self.menuTools.addAction(self.renumberInstanceAction)
        # utilities Menu
        self.selectMenu = self.menuUtilities.addMenu("Selection")
        self.selectMenu.addAction(self.selectDeviceAction)
        self.selectMenu.addAction(self.selectNetAction)
        self.selectMenu.addAction(self.selectPinAction)
        self.selectMenu.addSeparator()
        self.selectMenu.addAction(self.removeSelectFilterAction)
        self.simulationMenu = QMenu("&Simulation")
        # help menu
        self.simulationMenu.addAction(self.netlistAction)
        self.editorMenuBar.insertMenu(
            self.menuHelp.menuAction(), self.simulationMenu)
        # self.menuHelp = self.editorMenuBar.addMenu("&Help")
        if self._app.revedasim_path:
            self.simulationMenu.addAction(self.simulateAction)

    def _createToolBars(self):
        super()._createToolBars()
        # toolbar.addAction(self.rulerAction)
        # toolbar.addAction(self.delRulerAction)
        self.toolbar.addAction(self.objPropAction)
        self.toolbar.addAction(self.viewPropAction)

        self.schematicToolbar = QToolBar("Schematic Toolbar", self)
        self.addToolBar(self.schematicToolbar)
        self.schematicToolbar.addAction(self.createInstAction)
        self.schematicToolbar.addAction(self.createNetAction)
        self.schematicToolbar.addAction(self.createBusAction)
        self.schematicToolbar.addAction(self.createPinAction)
        # self.schematicToolbar.addAction(self.createLabelAction)
        self.schematicToolbar.addAction(self.createSymbolAction)
        self.schematicToolbar.addSeparator()
        self.schematicToolbar.addAction(self.viewCheckAction)
        self.schematicToolbar.addSeparator()
        self.schematicToolbar.addAction(self.goDownAction)
        self.schematicToolbar.addSeparator()
        self.schematicToolbar.addAction(self.selectDeviceAction)
        self.schematicToolbar.addAction(self.selectNetAction)
        self.schematicToolbar.addAction(self.selectPinAction)
        self.schematicToolbar.addAction(self.removeSelectFilterAction)

    def _schematicContextMenu(self):
        super()._editorContextMenu()
        self.centralW.scene.itemContextMenu.addAction(self.ignoreAction)
        self.centralW.scene.itemContextMenu.addAction(self.goDownAction)

    def _createShortcuts(self):
        super()._createShortcuts()
        self.createInstAction.setShortcut(Qt.Key_I)
        self.createNetAction.setShortcut(Qt.Key_W)
        self.createPinAction.setShortcut(Qt.Key_P)
        self.goDownAction.setShortcut("Shift+E")

    def createNetClick(self, s):
        self.centralW.scene.editModes.setMode("drawWire")

    def createInstClick(self, s):
        # create a designLibrariesView
        libraryModel = lmview.symbolViewsModel(self.libraryDict, self.symbolViews)
        if self.symbolChooser is None:
            self.symbolChooser = fd.selectCellViewDialog(self, libraryModel)
            self.symbolChooser.show()
        else:
            self.symbolChooser.raise_()
        if self.symbolChooser.exec() == QDialog.Accepted:
            libItem = libm.getLibItem(
                libraryModel, self.symbolChooser.libNamesCB.currentText()
            )
            cellItem = libm.getCellItem(
                libItem, self.symbolChooser.cellCB.currentText()
            )
            viewItem = libm.getViewItem(
                cellItem, self.symbolChooser.viewCB.currentText()
            )
            self.centralW.scene.instanceSymbolTuple = ddef.viewItemTuple(
                libItem, cellItem, viewItem
            )
            self.centralW.scene.editModes.setMode("addInstance")

    def createPinClick(self, s):
        createPinDlg = pdlg.createSchematicPinDialog(self)
        if createPinDlg.exec() == QDialog.Accepted:
            self.centralW.scene.pinName = createPinDlg.pinName.text()
            self.centralW.scene.pinType = createPinDlg.pinType.currentText()
            self.centralW.scene.pinDir = createPinDlg.pinDir.currentText()
            self.centralW.scene.editModes.setMode("drawPin")

    def createNoteClick(self, s):
        textDlg = pdlg.noteTextEdit(self)
        if textDlg.exec() == QDialog.Accepted:
            self.centralW.scene.noteText = textDlg.plainTextEdit.toPlainText()
            self.centralW.scene.noteFontFamily = textDlg.familyCB.currentText()
            self.centralW.scene.noteFontSize = textDlg.fontsizeCB.currentText()
            self.centralW.scene.noteFontStyle = textDlg.fontStyleCB.currentText()
            self.centralW.scene.noteAlign = textDlg.textAlignmCB.currentText()
            self.centralW.scene.noteOrient = textDlg.textOrientCB.currentText()
            self.centralW.scene.editModes.setMode("drawText")

    def createSymbolClick(self, s):
        self.createSymbol()

    def objPropClick(self, s):
        self.centralW.scene.editModes.setMode("selectItem")
        self.centralW.scene.viewObjProperties()

    def startSimClick(self, s):
        import revedasim.simMainWindow as smw

        simguiw = smw.simMainWindow(self)
        simguiw.show()

    def renumberInstanceClick(self, s):
        self.centralW.scene.renumberInstances()

    def checkSaveCell(self):
        schematicNets = self.centralW.scene.findSceneNetsSet()
        self.centralW.scene.groupAllNets(schematicNets)
        self.centralW.scene.saveSchematic(self.file)

    def saveCell(self):
        self.centralW.scene.saveSchematic(self.file)

    def loadSchematic(self):
        with open(self.file) as tempFile:
            items = json.load(tempFile)
        self.centralW.scene.loadSchematicItems(items)

        # because we do not save dot points, it is necessary to recreate them.

    def createConfigView(
        self,
        configItem: scb.viewItem,
        configDict: dict,
        newConfigDict: dict,
        processedCells: set,
    ):
        sceneSymbolSet = self.centralW.scene.findSceneSymbolSet()
        for item in sceneSymbolSet:
            libItem = libm.getLibItem(self.libraryView.libraryModel, item.libraryName)
            cellItem = libm.getCellItem(libItem, item.cellName)
            viewItems = [cellItem.child(row) for row in range(cellItem.rowCount())]
            viewNames = [viewItem.viewName for viewItem in viewItems]
            netlistableViews = [
                viewItemName
                for viewItemName in self.switchViewList
                if viewItemName in viewNames
            ]
            itemSwitchViewList = deepcopy(netlistableViews)
            viewDict = dict(zip(viewNames, viewItems))
            itemCellTuple = ddef.cellTuple(libItem.libraryName, cellItem.cellName)
            if itemCellTuple not in processedCells:
                if cellLine := configDict.get(cellItem.cellName):
                    netlistableViews = [cellLine[1]]
                for viewName in netlistableViews:
                    match viewDict[viewName].viewType:
                        case "schematic":
                            newConfigDict[cellItem.cellName] = [
                                libItem.libraryName,
                                viewName,
                                itemSwitchViewList,
                            ]
                            schematicObj = schematicEditor(
                                viewDict[viewName],
                                self.libraryDict,
                                self.libraryView,
                            )
                            schematicObj.loadSchematic()
                            schematicObj.createConfigView(
                                configItem,
                                configDict,
                                newConfigDict,
                                processedCells,
                            )
                            break
                        case _:
                            newConfigDict[cellItem.cellName] = [
                                libItem.libraryName,
                                viewName,
                                itemSwitchViewList,
                            ]
                            break
                processedCells.add(itemCellTuple)

    def closeEvent(self, event):
        self.centralW.scene.saveSchematic(self.file)
        event.accept()
        super().closeEvent(event)

    def createNetlistClick(self, s):
        dlg = fd.netlistExportDialogue(self)
        dlg.libNameEdit.setText(self.libName)
        dlg.cellNameEdit.setText(self.cellName)
        configViewItems = [
            self.cellItem.child(row)
            for row in range(self.cellItem.rowCount())
            if self.cellItem.child(row).viewType == "config"
        ]
        netlistableViews = [self.viewItem.viewName]
        for item in configViewItems:
            # is there a better way of doing it?
            with item.data(Qt.UserRole + 2).open(mode="r") as f:
                configItems = json.load(f)
                if configItems[1]["reference"] == self.viewItem.viewName:
                    netlistableViews.append(item.viewName)
        dlg.viewNameCombo.addItems(netlistableViews)
        if hasattr(self.appMainW, "simulationPath"):
            dlg.netlistDirEdit.setText(str(self.appMainW.simulationPath))
        if dlg.exec() == QDialog.Accepted:
            netlistObj = None
            try:
                self._startNetlisting(dlg, netlistObj)
            except Exception as e:
                self.logger.error(f"Error in creating netlist: {e}")

    def _startNetlisting(self, dlg, netlistObj):
        self.appMainW.simulationPath = pathlib.Path(dlg.netlistDirEdit.text())
        selectedViewName = dlg.viewNameCombo.currentText()
        self.switchViewList = [
            item.strip() for item in dlg.switchViewEdit.text().split(",")
        ]
        self.stopViewList = [dlg.stopViewEdit.text().strip()]
        subDirPathObj = self.appMainW.simulationPath.joinpath(self.cellName).joinpath(
            self.viewName
        )
        subDirPathObj.mkdir(parents=True, exist_ok=True)
        netlistFilePathObj = subDirPathObj.joinpath(
            f"{self.cellName}_{selectedViewName}"
        ).with_suffix(".cir")
        simViewName = dlg.viewNameCombo.currentText()
        if "schematic" in simViewName:
            netlistObj = xyceNetlist(self, netlistFilePathObj)
        elif "config" in simViewName:
            netlistObj = xyceNetlist(self, netlistFilePathObj, True)
            configItem = libm.findViewItem(
                self.libraryView.libraryModel,
                self.libName,
                self.cellName,
                dlg.viewNameCombo.currentText(),
            )
            with configItem.data(Qt.UserRole + 2).open(mode="r") as f:
                netlistObj.configDict = json.load(f)[2]

        if netlistObj:
            startTime = time.perf_counter()
            xyceNetlRunner = startThread(netlistObj.writeNetlist())
            self.appMainW.threadPool.start(xyceNetlRunner)
            # netlistObj.writeNetlist()
            endTime = time.perf_counter()
            self.logger.info(f"Netlisting time: {endTime - startTime}")
            print("Netlisting finished.")

    def goDownClick(self, s):
        self.centralW.scene.goDownHier()

    def ignoreClick(self, s):
        self.centralW.scene.ignoreSymbol()

    def netNameClick(self, s):
        # self.centralW.scene.netNameEdit()
        if self.centralW.scene.selectedItems() is not None:
            for item in self.centralW.scene.selectedItems():
                if isinstance(item, net.schematicNet):
                    self.centralW.scene.setNetProperties(item)
    def hilightNetClick(self, s):
        self.centralW.scene.hilightNets()

    def selectDeviceClick(self):
        self.centralW.scene.selectModes.setMode("selectDevice")
        self.messageLine.setText("Select Only Instances")

    def selectNetClick(self):
        self.centralW.scene.selectModes.setMode("selectNet")
        self.messageLine.setText("Select Only Nets")


    def selectPinClick(self):
        self.centralW.scene.selectModes.setMode("selectPin")
        self.messageLine.setText("Select Only Pins")

    def removeSelectFilterClick(self):
        self.centralW.scene.selectModes.setMode("selectAll")
        self.messageLine.setText("Select All Objects")

    def createSymbol(self) -> None:
        """
        Create a symbol view for a schematic.
        """
        oldSymbolItem = False

        askViewNameDlg = pdlg.symbolNameDialog(
            self.file.parent,
            self.cellName,
            self,
        )
        if askViewNameDlg.exec() == QDialog.Accepted:
            symbolViewName = askViewNameDlg.symbolViewsCB.currentText()
            if symbolViewName in askViewNameDlg.symbolViewNames:
                oldSymbolItem = True
            if oldSymbolItem:
                deleteSymViewDlg = fd.deleteSymbolDialog(
                    self.cellName, symbolViewName, self
                )
                if deleteSymViewDlg.exec() == QDialog.Accepted:
                    self.generateSymbol(symbolViewName)
            else:
                self.generateSymbol(symbolViewName)

    def generateSymbol(self, symbolViewName: str) -> None:
        symbolWindow = None
        libName = self.libName
        cellName = self.cellName
        libItem = libm.getLibItem(
            self.libraryView.libraryModel, libName
        )
        cellItem = libm.getCellItem(libItem, cellName)
        # libraryView = self.libraryView
        schematicPins: list[shp.schematicPin] = list(
            self.centralW.scene.findSceneSchemPinsSet())
        schematicPinNames: list[str] = [pinItem.pinName for pinItem in schematicPins]
        rectXDim: int = 0
        rectYDim: int = 0

        inputPins = [
            pinItem.pinName
            for pinItem in schematicPins
            if pinItem.pinDir == shp.schematicPin.pinDirs[0]
        ]

        outputPins = [
            pinItem.pinName
            for pinItem in schematicPins
            if pinItem.pinDir == shp.schematicPin.pinDirs[1]
        ]

        inoutPins = [
            pinItem.pinName
            for pinItem in schematicPins
            if pinItem.pinDir == shp.schematicPin.pinDirs[2]
        ]

        dlg = pdlg.symbolCreateDialog(self)
        dlg.leftPinsEdit.setText(", ".join(inputPins))
        dlg.rightPinsEdit.setText(", ".join(outputPins))
        dlg.topPinsEdit.setText(", ".join(inoutPins))
        if dlg.exec() == QDialog.Accepted:
            symbolViewItem = scb.createCellView(
                self, symbolViewName, cellItem
            )
            libraryDict = self.libraryDict
            # create symbol editor window with an empty items list
            symbolWindow = symbolEditor(symbolViewItem, libraryDict, self.libraryView)
            try:
                leftPinNames = list(
                    filter(
                        None,
                        [
                            pinName.strip()
                            for pinName in dlg.leftPinsEdit.text().split(",")
                        ],
                    )
                )
                rightPinNames = list(
                    filter(
                        None,
                        [
                            pinName.strip()
                            for pinName in dlg.rightPinsEdit.text().split(",")
                        ],
                    )
                )
                topPinNames = list(
                    filter(
                        None,
                        [
                            pinName.strip()
                            for pinName in dlg.topPinsEdit.text().split(",")
                        ],
                    )
                )
                bottomPinNames = list(
                    filter(
                        None,
                        [
                            pinName.strip()
                            for pinName in dlg.bottomPinsEdit.text().split(",")
                        ],
                    )
                )
                stubLength = int(float(dlg.stubLengthEdit.text().strip()))
                pinDistance = int(float(dlg.pinDistanceEdit.text().strip()))
                rectXDim = (
                    max(len(topPinNames), len(bottomPinNames)) + 1
                ) * pinDistance
                rectYDim = (
                    max(len(leftPinNames), len(rightPinNames)) + 1
                ) * pinDistance
            except ValueError:
                self.logger.error("Enter valid value")

        # add window to open windows list
        # libraryView.openViews[f"{libName}_{cellName}_{symbolViewName}"] = symbolWindow
        if symbolWindow is not None:
            symbolScene = symbolWindow.centralW.scene
            symbolScene.rectDraw(QPoint(0, 0), QPoint(rectXDim, rectYDim))
            symbolScene.labelDraw(
                QPoint(int(0.25 * rectXDim), int(0.4 * rectYDim)),
                "[@cellName]",
                "NLPLabel",
                "12",
                "Center",
                "R0",
                "Instance",
            )
            symbolScene.labelDraw(
                QPoint(int(rectXDim), int(-0.2 * rectYDim)),
                "[@instName]",
                "NLPLabel",
                "12",
                "Center",
                "R0",
                "Instance",
            )
            leftPinLocs = [
                QPoint(-stubLength, (i + 1) * pinDistance)
                for i in range(len(leftPinNames))
            ]
            rightPinLocs = [
                QPoint(rectXDim + stubLength, (i + 1) * pinDistance)
                for i in range(len(rightPinNames))
            ]
            bottomPinLocs = [
                QPoint((i + 1) * pinDistance, rectYDim + stubLength)
                for i in range(len(bottomPinNames))
            ]
            topPinLocs = [
                QPoint((i + 1) * pinDistance, -stubLength)
                for i in range(len(topPinNames))
            ]
            for i in range(len(leftPinNames)):
                symbolScene.lineDraw(
                    leftPinLocs[i], leftPinLocs[i] + QPoint(stubLength, 0)
                )
                symbolScene.addItem(
                    schematicPins[schematicPinNames.index(leftPinNames[i])].toSymbolPin(
                        leftPinLocs[i]
                    )
                )
            for i in range(len(rightPinNames)):
                symbolScene.lineDraw(
                    rightPinLocs[i], rightPinLocs[i] + QPoint(-stubLength, 0)
                )
                symbolScene.addItem(
                    schematicPins[
                        schematicPinNames.index(rightPinNames[i])
                    ].toSymbolPin(rightPinLocs[i])
                )
            for i in range(len(topPinNames)):
                symbolScene.lineDraw(
                    topPinLocs[i], topPinLocs[i] + QPoint(0, stubLength)
                )
                symbolScene.addItem(
                    schematicPins[schematicPinNames.index(topPinNames[i])].toSymbolPin(
                        topPinLocs[i]
                    )
                )
            for i in range(len(bottomPinNames)):
                symbolScene.lineDraw(
                    bottomPinLocs[i], bottomPinLocs[i] + QPoint(0, -stubLength)
                )
                symbolScene.addItem(
                    schematicPins[
                        schematicPinNames.index(bottomPinNames[i])
                    ].toSymbolPin(bottomPinLocs[i])
                )  # symbol attribute generation for netlisting.
            symbolScene.attributeList = list()  # empty attribute list

            symbolScene.attributeList.append(
                symenc.symbolAttribute(
                    "XyceSymbolNetlistLine", "X@instName @cellName @pinList"
                )
            )
            symbolScene.attributeList.append(
                symenc.symbolAttribute("pinOrder", ", ".join(schematicPinNames))
            )

            symbolWindow.checkSaveCell()
            self.libraryView.reworkDesignLibrariesView(self.appMainW.libraryDict)

            openCellViewTuple = ddef.viewTuple(libName, cellName, symbolViewName)
            self.appMainW.openViews[openCellViewTuple] = symbolWindow
            symbolWindow.show()


class symbolEditor(editorWindow):
    def __init__(
        self,
        viewItem: scb.viewItem,
        libraryDict: dict,
        libraryView: lmview.designLibrariesView,
    ):
        super().__init__(viewItem, libraryDict, libraryView)
        self.setWindowTitle(f"Symbol Editor - {self.cellName} - {self.viewName}")
        self._symbolContextMenu()

    def init_UI(self):
        super().init_UI()
        # create container to position all widgets
        self.centralW = symbolContainer(self)
        self.setCentralWidget(self.centralW)

    # def _createActions(self):
    #     super()._createActions()

    def _createShortcuts(self):
        super()._createShortcuts()
        self.stretchAction.setShortcut(Qt.Key_S)
        self.createRectAction.setShortcut(Qt.Key_R)
        self.createLineAction.setShortcut(Qt.Key_W)
        self.createLabelAction.setShortcut(Qt.Key_L)
        self.createPinAction.setShortcut(Qt.Key_P)


    def _createToolBars(self):  # redefine the toolbar in the editorWindow class
        super()._createToolBars()
        self.symbolToolbar = QToolBar("Symbol Toolbar", self)
        self.addToolBar(self.symbolToolbar)
        self.symbolToolbar.addAction(self.createLineAction)
        self.symbolToolbar.addAction(self.createRectAction)
        self.symbolToolbar.addAction(self.createPolygonAction)
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
        self.menuCreate.addAction(self.createPolygonAction)
        self.menuCreate.addAction(self.createCircleAction)
        self.menuCreate.addAction(self.createArcAction)
        self.menuCreate.addAction(self.createLabelAction)
        self.menuCreate.addAction(self.createPinAction)

    def _createTriggers(self):
        super()._createTriggers()
        self.createLineAction.triggered.connect(self.createLineClick)
        self.createRectAction.triggered.connect(self.createRectClick)
        self.createPolygonAction.triggered.connect(self.createPolyClick)
        self.createArcAction.triggered.connect(self.createArcClick)
        self.createCircleAction.triggered.connect(self.createCircleClick)
        self.createLabelAction.triggered.connect(self.createLabelClick)
        self.createPinAction.triggered.connect(self.createPinClick)
        self.objPropAction.triggered.connect(self.objPropClick)
        self.deleteAction.triggered.connect(self.deleteClick)
        self.viewPropAction.triggered.connect(self.viewPropClick)

    def _symbolContextMenu(self):
        super()._editorContextMenu()
        self.centralW.scene.itemContextMenu.addAction(self.stretchAction)

    def objPropClick(self):
        self.centralW.scene.itemProperties()

    def checkSaveCell(self):
        self.centralW.scene.saveSymbolCell(self.file)

    def saveCell(self):
        self.centralW.scene.saveSymbolCell(self.file)

    def createRectClick(self, s):
        self.centralW.scene.editModes.setMode("drawRect")
        self.messageLine.setText("Press left mouse button for the first point.")

    def createLineClick(self, s):
        self.centralW.scene.editModes.setMode("drawLine")
        self.messageLine.setText("Press left mouse button for the first point.")

    def createPolyClick(self, s):
        self.centralW.scene.editModes.setMode("drawPolygon")

    def createArcClick(self, s):
        self.centralW.scene.editModes.setMode("drawArc")
        self.messageLine.setText("Press left mouse button for the first point.")

    def createCircleClick(self, s):
        self.centralW.scene.editModes.setMode("drawCircle")
        self.messageLine.setText("Press left mouse button for the centre point.")

    def createPinClick(self, s):
        createPinDlg = pdlg.createPinDialog(self)
        if createPinDlg.exec() == QDialog.Accepted:
            modeList = [False for _ in range(8)]
            modeList[0] = True
            self.centralW.scene.pinName = createPinDlg.pinName.text()
            self.centralW.scene.pinType = createPinDlg.pinType.currentText()
            self.centralW.scene.pinDir = createPinDlg.pinDir.currentText()
            self.centralW.scene.editModes.setMode("drawPin")
            self.messageLine.setText("Place pin on the symbol.")

    def rotateItemClick(self, s):
        self.centralW.scene.editModes.setMode("rotateItem")
        self.messageLine.setText("Click on an item to rotate CW 90 degrees.")

    def copyClick(self, s):
        self.centralW.scene.editModes.setMode("copyItem")
        self.centralW.scene.copySelectedItems()
        self.messageLine.setText("Copying selected items")

    def viewPropClick(self, s):
        self.centralW.scene.editModes.setMode("selectItem")
        self.centralW.scene.viewSymbolProperties()

    def loadSymbol(self):
        """
        symbol is loaded to the scene.
        """
        with open(self.file) as tempFile:
            try:
                items = json.load(tempFile)
            except json.decoder.JSONDecodeError:
                self.logger.error("Cannot load symbol. JSON Decode Error")
        self.centralW.scene.loadSymbol(items)

    def createLabelClick(self):
        createLabelDlg = pdlg.createSymbolLabelDialog(self)
        self.messageLine.setText("Place a label")
        createLabelDlg.labelHeightEdit.setText("12")
        if createLabelDlg.exec() == QDialog.Accepted:
            self.centralW.scene.editModes.setMode("addLabel")
            # directly setting scene class attributes here to pass the information.
            self.centralW.scene.labelDefinition = createLabelDlg.labelDefinition.text()
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
            self.centralW.scene.labelOpaque = (
                createLabelDlg.labelVisiCombo.currentText() == "Yes"
            )
            self.centralW.scene.labelType = "Normal"  # default button
            if createLabelDlg.normalType.isChecked():
                self.centralW.scene.labelType = "Normal"
            elif createLabelDlg.NLPType.isChecked():
                self.centralW.scene.labelType = "NLPLabel"
            elif createLabelDlg.pyLType.isChecked():
                self.centralW.scene.labelType = "PyLabel"



    def closeEvent(self, event):
        """
        Closes the application.
        """
        self.centralW.scene.saveSymbolCell(self.file)
        event.accept()
        super().closeEvent(event)


class symbolContainer(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.scene = escn.symbolScene(self)
        self.view = edv.symbolView(self.scene, self)
        self.init_UI()

    def init_UI(self):
        # layout statements, using a grid layout
        gLayout = QGridLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.view, 0, 0)
        # ratio of first column to second column is 5
        gLayout.setColumnStretch(0, 5)
        gLayout.setRowStretch(0, 6)
        self.setLayout(gLayout)


class schematicContainer(QWidget):
    def __init__(self, parent: schematicEditor):
        super().__init__(parent=parent)
        assert isinstance(parent, schematicEditor)
        self.parent = parent
        self.scene = escn.schematicScene(self)
        self.view = edv.schematicView(self.scene, self)

        self.init_UI()

    def init_UI(self):
        # layout statements, using a grid layout
        gLayout = QGridLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.view, 0, 0)
        # ratio of first column to second column is 5
        gLayout.setColumnStretch(0, 5)
        gLayout.setRowStretch(0, 6)
        self.setLayout(gLayout)


class layoutContainer(QWidget):
    def __init__(self, parent: layoutEditor):
        super().__init__(parent=parent)
        self.parent = parent
        self.scene = escn.layoutScene(self)
        self.view = edv.layoutView(self.scene, self)
        self.lswModel = lsw.layerDataModel(laylyr.pdkAllLayers)
        layerViewTable = lsw.layerViewTable(self, self.lswModel)
        self.lswWidget = lswWindow(layerViewTable)
        self.lswWidget.setMinimumWidth(300)
        self.lswWidget.lswTable.dataSelected.connect(self.selectLayer)
        self.lswWidget.lswTable.layerSelectable.connect(self.layerSelectableChange)
        self.lswWidget.lswTable.layerVisible.connect(self.layerVisibleChange)

        self.init_UI()

    def init_UI(self):
        # there could be other widgets in the grid layout, such as edLayer
        # viewer/editor.
        vLayout = QVBoxLayout(self)
        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        splitter.insertWidget(0, self.lswWidget)
        splitter.insertWidget(1, self.view)
        # ratio of first column to second column is 5
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 5)
        vLayout.addWidget(splitter)

        self.setLayout(vLayout)

    def selectLayer(self, layerName: str, layerPurpose: str):
        self.scene.selectEdLayer = self.findSelectedLayer(layerName, layerPurpose)

    def findSelectedLayer(self, layerName: str, layerPurpose: str):
        for layer in pdk.layoutLayers.pdkAllLayers:
            if layer.name == layerName and layer.purpose == layerPurpose:
                return layer
        return pdk.layoutLayers.pdkAllLayers[0]

    def layerSelectableChange(
        self, layerName: str, layerPurpose: str, layerSelectable: bool
    ):
        selectedLayer = self.findSelectedLayer(layerName, layerPurpose)
        if selectedLayer:
            selectedLayer.selectable = layerSelectable

        for item in self.scene.items():
            if (hasattr(item, 'layer') and item.layer == selectedLayer and item.parentItem()
                    is None):
                item.setEnabled(layerSelectable)
                item.update()

    def layerVisibleChange(self, layerName: str, layerPurpose: str, layerVisible: bool):
        selectedLayer = self.findSelectedLayer(layerName, layerPurpose)
        if selectedLayer:
            selectedLayer.visible = layerVisible

            for item in self.scene.items():
                if hasattr(item, "layer") and item.layer == selectedLayer:
                    item.setVisible(layerVisible)
                    item.update()


class lswWindow(QWidget):
    def __init__(self, lswTable: lsw.layerViewTable):
        super().__init__()
        self.lswTable = lswTable
        layout = QVBoxLayout()
        toolBar = QToolBar()
        avIcon = QIcon('icons/eye.png')
        nvIcon = QIcon('icons/eye-close.png')
        avAction = QAction(avIcon, 'All Visible', self)
        avAction.setToolTip('All layers visible')
        avAction.triggered.connect(self.lswTable.allLayersVisible)
        nvAction = QAction(nvIcon, 'None Visible', self)
        nvAction.setToolTip('No layer visible')
        nvAction.triggered.connect(self.lswTable.noLayersVisible)
        asIcon = QIcon('icons/pencil.png')
        nsIcon = QIcon('icons/pencil-prohibition.png')
        nsAction = QAction(nsIcon, 'All Selectable', self)
        nsAction.setToolTip('No layers selectable')
        nsAction.triggered.connect(self.lswTable.noLayersSelectable)
        asAction = QAction(asIcon, 'None Selectable', self)
        asAction.setToolTip('All layers selectable')
        asAction.triggered.connect(self.lswTable.allLayersSelectable)

        toolBar.addAction(avAction)
        toolBar.addAction(nvAction)
        toolBar.addAction(asAction)
        toolBar.addAction(nsAction)
        layout.addWidget(toolBar)
        layout.addWidget(self.lswTable)
        self.setLayout(layout)

class xyceNetlist:
    def __init__(
        self,
        schematic: schematicEditor,
        filePathObj: pathlib.Path,
        use_config: bool = False,
    ):
        self.filePathObj = filePathObj
        self.schematic = schematic
        self._use_config = use_config
        self._scene = self.schematic.centralW.scene
        self.libraryDict = self.schematic.libraryDict
        self.libraryView = self.schematic.libraryView
        self._configDict = None
        self.libItem = libm.getLibItem(
            self.schematic.libraryView.libraryModel,
            self.schematic.libName,
        )
        self.cellItem = libm.getCellItem(self.libItem, self.schematic.cellName)

        self.switchViewList = schematic.switchViewList
        self.stopViewList = schematic.stopViewList
        self.netlistedViewsSet = set()  # keeps track of netlisted views.
        self.includeLines = set()  # keeps track of include lines.
        self.vamodelLines = set()  # keeps track of vamodel lines.
        self.vahdlLines = set()  # keeps track of *.HDL lines.

    def writeNetlist(self):
        with self.filePathObj.open(mode="w") as cirFile:
            cirFile.write(
                "*".join(
                    [
                        "\n",
                        80 * "*",
                        "\n",
                        "* Revolution EDA CDL Netlist\n",
                        f"* Library: {self.schematic.libName}\n",
                        f"* Top Cell Name: {self.schematic.cellName}\n",
                        f"* View Name: {self.schematic.viewName}\n",
                        f"* Date: {datetime.datetime.now()}\n",
                        80 * "*",
                        "\n",
                        ".GLOBAL gnd!\n\n",
                    ]
                )
            )

            # now go down the rabbit hole to track all circuit elements.
            self.recursiveNetlisting(self.schematic, cirFile)

            cirFile.write(".END\n")
            for line in self.includeLines:
                cirFile.write(f"{line}\n")
            for line in self.vamodelLines:
                cirFile.write(f"{line}\n")
            for line in self.vahdlLines:
                cirFile.write(f"{line}\n")

    @property
    def configDict(self):
        return self._configDict

    @configDict.setter
    def configDict(self, value: dict):
        assert isinstance(value, dict)
        self._configDict = value


    # def recursiveNetlisting(self, schematic: schematicEditor, cirFile):
    #     """
    #     Recursively traverse all sub-circuits and netlist them.
    #     """
    #     try:
    #         schematicScene = schematic.centralW.scene
    #         schematicNets = schematicScene.findSceneNetsSet()
    #         schematicScene.groupAllNets(schematicNets)  # name all nets in the
    #         # schematic
    #         sceneSymbolSet = schematicScene.findSceneSymbolSet()
    #         schematicScene.generatePinNetMap(tuple(sceneSymbolSet))
    #         for elementSymbol in sceneSymbolSet:
    #             if elementSymbol.symattrs.get("XyceNetlistPass") != "1" and (
    #                 not elementSymbol.netlistIgnore
    #             ):
    #                 libItem = libm.getLibItem(
    #                     schematic.libraryView.libraryModel, elementSymbol.libraryName
    #                 )
    #                 cellItem = libm.getCellItem(libItem, elementSymbol.cellName)
    #                 viewItems = [
    #                     cellItem.child(row) for row in range(cellItem.rowCount())
    #                 ]
    #                 viewNames = [view.viewName for view in viewItems]
    #
    #                 netlistView = "symbol"
    #                 if self._use_config:
    #                     netlistView = self.configDict.get(elementSymbol.cellName)[1]
    #                 else:
    #                     for viewName in self.switchViewList:
    #                         if viewName in viewNames:
    #                             netlistView = viewName
    #                             break
    #                 # these are qstandarditem in library browser.
    #                 # viewItem = libm.getViewItem(cellItem, netlistView)
    #
    #                 # now create the netlist line for that item.
    #                 self.createItemLine(cirFile, elementSymbol, cellItem, netlistView)
    #             elif elementSymbol.netlistIgnore:
    #                 cirFile.write(
    #                     f"*{elementSymbol.instanceName} is marked to be ignored\n"
    #                 )
    #             elif not elementSymbol.symattrs.get("XyceNetlistPass", False):
    #                 cirFile.write(
    #                     f"*{elementSymbol.instanceName} has no XyceNetlistLine attribute\n"
    #                 )
    #
    #     except Exception as e:
    #         self.schematic.logger.error(f"Netlisting error: {e}")
    @lru_cache(maxsize=16)
    def recursiveNetlisting(self, schematic: schematicEditor, cirFile):
        """
        Recursively traverse all sub-circuits and netlist them.
        """
        try:
            schematicScene = schematic.centralW.scene
            schematicNets = schematicScene.findSceneNetsSet()
            schematicScene.groupAllNets(schematicNets)  # name all nets in the schematic

            sceneSymbolSet = schematicScene.findSceneSymbolSet()
            schematicScene.generatePinNetMap(tuple(sceneSymbolSet))

            for elementSymbol in sceneSymbolSet:
                self.processElementSymbol(elementSymbol, schematic, cirFile)
        except Exception as e:
            self.schematic.logger.error(f"Netlisting error: {e}")

    @lru_cache(maxsize=16)
    def processElementSymbol(self, elementSymbol, schematic, cirFile):
        if elementSymbol.symattrs.get("XyceNetlistPass") != "1" and (
            not elementSymbol.netlistIgnore):
            libItem = libm.getLibItem(schematic.libraryView.libraryModel,
                                      elementSymbol.libraryName)
            cellItem = libm.getCellItem(libItem, elementSymbol.cellName)
            netlistView = self.determineNetlistView(elementSymbol, cellItem)

            # Create the netlist line for the item.
            self.createItemLine(cirFile, elementSymbol, cellItem, netlistView)
        elif elementSymbol.netlistIgnore:
            cirFile.write(f"*{elementSymbol.instanceName} is marked to be ignored\n")
        elif not elementSymbol.symattrs.get("XyceNetlistPass", False):
            cirFile.write(f"*{elementSymbol.instanceName} has no XyceNetlistLine attribute\n")

    def determineNetlistView(self, elementSymbol, cellItem):
        viewItems = [cellItem.child(row) for row in range(cellItem.rowCount())]
        viewNames = [view.viewName for view in viewItems]

        if self._use_config:
            return self.configDict.get(elementSymbol.cellName)[1]
        else:
            for viewName in self.switchViewList:
                if viewName in viewNames:
                    return viewName
            return "symbol"

    def createItemLine(
        self,
        cirFile,
        elementSymbol: shp.schematicSymbol,
        cellItem: scb.cellItem,
        netlistView: str,
    ):
        if "schematic" in netlistView:
            # First write subckt call in the netlist.
            cirFile.write(self.createXyceSymbolLine(elementSymbol))
            schematicItem = libm.getViewItem(cellItem, netlistView)
            if netlistView not in self.stopViewList:
                # now load the schematic
                schematicObj = schematicEditor(
                    schematicItem, self.libraryDict, self.libraryView
                )
                schematicObj.loadSchematic()

                viewTuple = ddef.viewTuple(
                    schematicObj.libName, schematicObj.cellName, schematicObj.viewName
                )

                if viewTuple not in self.netlistedViewsSet:
                    self.netlistedViewsSet.add(viewTuple)
                    pinList = elementSymbol.symattrs.get("pinOrder", ", ").replace(
                        ",", " "
                    )
                    cirFile.write(f".SUBCKT {schematicObj.cellName} {pinList}\n")
                    self.recursiveNetlisting(schematicObj, cirFile)
                    cirFile.write(".ENDS\n")
        elif "symbol" in netlistView:
            cirFile.write(self.createXyceSymbolLine(elementSymbol))
        elif "spice" in netlistView:
            cirFile.write(self.createSpiceLine(elementSymbol))
        elif "veriloga" in netlistView:
            cirFile.write(self.createVerilogaLine(elementSymbol))

    def createXyceSymbolLine(self, elementSymbol: shp.schematicSymbol):
        """
        Create a netlist line from a nlp device format line.
        """
        try:
            xyceNetlistFormatLine = elementSymbol.symattrs[
                "XyceSymbolNetlistLine"
            ].strip()
            for labelItem in elementSymbol.labels.values():
                if labelItem.labelName in xyceNetlistFormatLine:
                    xyceNetlistFormatLine = xyceNetlistFormatLine.replace(
                        labelItem.labelName, labelItem.labelValue
                    )

            for attrb, value in elementSymbol.symattrs.items():
                if f"%{attrb}" in xyceNetlistFormatLine:
                    xyceNetlistFormatLine = xyceNetlistFormatLine.replace(
                        f"%{attrb}", value
                    )

            pinList = " ".join(elementSymbol.pinNetMap.values())
            xyceNetlistFormatLine = (
                xyceNetlistFormatLine.replace("@pinList", pinList) + "\n"
            )
            return xyceNetlistFormatLine
        except Exception as e:
            self._scene.logger.error(e)
            self._scene.logger.error(
                f"Netlist line is not defined for {elementSymbol.instanceName}"
            )
            # if there is no NLPDeviceFormat line, create a warning line
            return f"*Netlist line is not defined for symbol of {elementSymbol.instanceName}\n"

    def createSpiceLine(self, elementSymbol: shp.schematicSymbol):
        """
        Create a netlist line from a nlp device format line.
        """
        try:
            spiceNetlistFormatLine = elementSymbol.symattrs[
                "XyceSpiceNetlistLine"
            ].strip()
            for labelItem in elementSymbol.labels.values():
                if labelItem.labelName in spiceNetlistFormatLine:
                    spiceNetlistFormatLine = spiceNetlistFormatLine.replace(
                        labelItem.labelName, labelItem.labelValue
                    )

            for attrb, value in elementSymbol.symattrs.items():
                if f"%{attrb}" in spiceNetlistFormatLine:
                    spiceNetlistFormatLine = spiceNetlistFormatLine.replace(
                        f"%{attrb}", value
                    )
            pinList = elementSymbol.symattrs.get("pinOrder", ", ").replace(",", " ")
            spiceNetlistFormatLine = (
                spiceNetlistFormatLine.replace("@pinList", pinList) + "\n"
            )
            self.includeLines.add(
                elementSymbol.symattrs.get(
                    "incLine", "* no include line is found for {item.cellName}"
                ).strip()
            )
            return spiceNetlistFormatLine
        except Exception as e:
            self._scene.logger.error(f"Spice subckt netlist error: {e}")
            self._scene.logger.error(
                f"Netlist line is not defined for {elementSymbol.instanceName}"
            )
            # if there is no NLPDeviceFormat line, create a warning line
            return f"*Netlist line is not defined for symbol of {elementSymbol.instanceName}\n"

    def createVerilogaLine(self, elementSymbol):
        """
        Create a netlist line from a nlp device format line.
        """
        try:
            verilogaNetlistFormatLine = elementSymbol.symattrs[
                "XyceVerilogaNetlistLine"
            ].strip()
            for labelItem in elementSymbol.labels.values():
                if labelItem.labelName in verilogaNetlistFormatLine:
                    verilogaNetlistFormatLine = verilogaNetlistFormatLine.replace(
                        labelItem.labelName, labelItem.labelValue
                    )

            for attrb, value in elementSymbol.symattrs.items():
                if f"%{attrb}" in verilogaNetlistFormatLine:
                    verilogaNetlistFormatLine = verilogaNetlistFormatLine.replace(
                        f"%{attrb}", value
                    )
            pinList = " ".join(elementSymbol.pinNetMap.values())
            verilogaNetlistFormatLine = (
                verilogaNetlistFormatLine.replace("@pinList", pinList) + "\n"
            )
            self.vamodelLines.add(
                elementSymbol.symattrs.get(
                    "vaModelLine", "* no model line is found for {item.cellName}"
                ).strip()
            )
            self.vahdlLines.add(
                elementSymbol.symattrs.get(
                    "vaHDLLine", "* no hdl line is found for {item.cellName}"
                ).strip()
            )
            return verilogaNetlistFormatLine
        except Exception as e:
            self._scene.logger.error(e)
            self._scene.logger.error(
                f"Netlist line is not defined for {elementSymbol.instanceName}"
            )
            # if there is no NLPDeviceFormat line, create a warning line
            return f"*Netlist line is not defined for symbol of {elementSymbol.instanceName}\n"



class configViewEdit(QMainWindow):
    def __init__(self, appMainW, schViewItem, configDict, viewItem):
        super().__init__(parent=appMainW)
        self.appMainW = appMainW  # app mainwindow
        self.schViewItem = schViewItem
        self.configDict = configDict
        self.viewItem = viewItem
        self.setWindowTitle("Edit Config View")
        self.setMinimumSize(500, 600)
        self._createMenuBar()
        self._createActions()
        self._addActions()
        self._createTriggers()
        self.centralWidget = configViewEditContainer(self)
        self.setCentralWidget(self.centralWidget)

    def _createMenuBar(self):
        self.mainMenu = self.menuBar()
        self.mainMenu.setNativeMenuBar(False)  # for mac
        self.fileMenu = self.mainMenu.addMenu("&File")
        self.editMenu = self.mainMenu.addMenu("&Edit")
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def _createActions(self):
        updateIcon = QIcon(":/icons/arrow-circle.png")
        self.updateAction = QAction(updateIcon, "Update", self)
        saveIcon = QIcon(":/icons/database--plus.png")
        self.saveAction = QAction(saveIcon, "Save", self)

    def _addActions(self):
        self.fileMenu.addAction(self.updateAction)
        self.fileMenu.addAction(self.saveAction)

    def _createTriggers(self):
        self.updateAction.triggered.connect(self.updateClick)
        self.saveAction.triggered.connect(self.saveClick)

    def updateClick(self):
        newConfigDict = self.updateConfigDict()
        if self.appMainW.libraryBrowser is None:
            self.appMainW.createLibraryBrowser()
        topSchematicWindow = schematicEditor(
            self.schViewItem,
            self.appMainW.libraryDict,
            self.appMainW.libraryBrowser.libBrowserCont.designView,
        )
        topSchematicWindow.loadSchematic()
        topSchematicWindow.createConfigView(
            self.viewItem,
            self.configDict,
            newConfigDict,
            topSchematicWindow.processedCells,
        )
        self.configDict = newConfigDict

        self.centralWidget.confModel = configModel(self.configDict)
        # self.centralWidget.configDictGroup.setVisible(False)
        self.centralWidget.configDictLayout.removeWidget(
            self.centralWidget.configViewTable
        )
        self.centralWidget.configViewTable = configTable(self.centralWidget.confModel)
        self.centralWidget.configDictLayout.addWidget(
            self.centralWidget.configViewTable
        )  # self.centralWidget.configDictGroup.setVisible(True)

    def updateConfigDict(self):
        self.centralWidget.configViewTable.updateModel()
        self.configDict = dict()
        newConfigDict = dict()
        model = self.centralWidget.confModel
        for i in range(model.rowCount()):
            viewList = [
                item.strip()
                for item in model.itemFromIndex(model.index(i, 3)).text().split(",")
            ]
            self.configDict[model.item(i, 1).text()] = [
                model.item(i, 0).text(),
                model.item(i, 2).text(),
                viewList,
            ]
        return newConfigDict

    def saveClick(self):
        configFilePathObj = self.viewItem.data(Qt.UserRole + 2)
        self.updateConfigDict()
        items = list()
        items.insert(0, {"viewName": "config"})
        items.insert(1, {"reference": self.schViewItem.viewName})
        items.insert(2, self.configDict)
        with configFilePathObj.open(mode="w+") as configFile:
            json.dump(items, configFile, indent=4)

    def closeEvent(self, event):
        cellViewTuple = ddef.viewTuple(
            self.viewItem.parent().parent().libraryName,
            self.viewItem.parent().cellName,
            self.viewItem.viewName,
        )
        self.appMainW.openViews.pop(cellViewTuple)
        event.accept()
        super().closeEvent(event)


class configViewEditContainer(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.mainLayout = QVBoxLayout()
        topCellGroup = QGroupBox("Top Cell")
        topCellLayout = QFormLayout()
        self.libraryNameEdit = edf.longLineEdit()
        topCellLayout.addRow(edf.boldLabel("Library:"), self.libraryNameEdit)
        self.cellNameEdit = edf.longLineEdit()
        topCellLayout.addRow(edf.boldLabel("Cell:"), self.cellNameEdit)
        self.viewNameCB = QComboBox()
        topCellLayout.addRow(edf.boldLabel("View:"), self.viewNameCB)
        topCellGroup.setLayout(topCellLayout)
        self.mainLayout.addWidget(topCellGroup)
        viewGroup = QGroupBox("Switch/Stop Views")
        viewGroupLayout = QFormLayout()
        viewGroup.setLayout(viewGroupLayout)
        self.switchViewsEdit = edf.longLineEdit()
        viewGroupLayout.addRow(edf.boldLabel("View List:"), self.switchViewsEdit)
        self.stopViewsEdit = edf.longLineEdit()
        viewGroupLayout.addRow(edf.boldLabel("Stop List:"), self.stopViewsEdit)
        self.mainLayout.addWidget(viewGroup)
        self.configDictGroup = QGroupBox("Cell View Configuration")
        self.confModel = configModel(self.parent.configDict)
        self.configDictLayout = QVBoxLayout()
        self.configViewTable = configTable(self.confModel)
        self.configDictLayout.addWidget(self.configViewTable)
        self.configDictGroup.setLayout(self.configDictLayout)
        self.mainLayout.addWidget(self.configDictGroup)
        self.setLayout(self.mainLayout)


class configModel(QStandardItemModel):
    def __init__(self, configDict: dict):
        row = len(configDict.keys())
        column = 4
        super().__init__(row, column)
        self.setHorizontalHeaderLabels(
            ["Library", "Cell Name", "View Found", "View To ", "Use"]
        )
        for i, (k, v) in enumerate(configDict.items()):
            item = QStandardItem(v[0])
            self.setItem(i, 0, item)
            item = QStandardItem(k)
            self.setItem(i, 1, item)
            item = QStandardItem(v[1])
            self.setItem(i, 2, item)
            item = QStandardItem(", ".join(v[2]))
            self.setItem(i, 3, item)


class configTable(QTableView):
    def __init__(self, model: configModel):
        super().__init__()
        self.model = model
        self.setModel(self.model)
        self.combos = list()
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setEditTriggers(QTableView.NoEditTriggers)
        for row in range(self.model.rowCount()):
            self.combos.append(QComboBox())
            items = [
                item.strip()
                for item in self.model.itemFromIndex(self.model.index(row, 3))
                .text()
                .split(",")
            ]
            self.combos[-1].addItems(items)
            self.combos[-1].setCurrentText(
                self.model.itemFromIndex(self.model.index(row, 2)).text()
            )
            self.setIndexWidget(self.model.index(row, 3), self.combos[-1])

    def updateModel(self):
        for row in range(self.model.rowCount()):
            item = QStandardItem(self.combos[row].currentText())
            self.model.setItem(row, 2, item)


class startThread(QRunnable):
    __slots__ = ("fn",)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    @Slot()
    def run(self) -> None:
        try:
            self.fn
        except Exception as e:
            print(e)
