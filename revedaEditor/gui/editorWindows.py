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
from copy import deepcopy
import inspect
from quantiphy import Quantity
import itertools as itt
from typing import Union, Optional, NamedTuple

# import os
# if os.environ.get('REVEDASIM_PATH'):
#     import revedasim.simMainWindow as smw

# import numpy as np
from PySide6.QtCore import (
    QEvent,
    QPoint,
    QPointF,
    QProcess,
    QRect,
    QRectF,
    QRunnable,
    Qt,
    Slot,
    QLineF,
)
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QCursor,
    QGuiApplication,
    QIcon,
    QImage,
    QKeySequence,
    QKeyEvent,
    QPainter,
    QStandardItem,
    QStandardItemModel,
    QTextDocument,
    QTransform,
    QWheelEvent,
    QPen,
    QFontDatabase,
    QFont,
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
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
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
    QGraphicsLineItem,
)
import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.schBackEnd as scb
import revedaEditor.backend.undoStack as us
import revedaEditor.common.net as net
import revedaEditor.common.layoutShapes as layp

# import pdk.symLayers as symlyr
import pdk.schLayers as schlyr
import pdk.layoutLayers as laylyr
import pdk.process as fabproc
import pdk.pcells as pcells
import revedaEditor.common.shapes as shp  # import the shapes
import revedaEditor.common.layoutShapes as lshp  # import layout shapes
import revedaEditor.fileio.loadJSON as lj
import revedaEditor.fileio.symbolEncoder as symenc
import revedaEditor.fileio.layoutEncoder as layenc
import revedaEditor.fileio.schematicEncoder as schenc
import revedaEditor.gui.editFunctions as edf
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.propertyDialogues as pdlg
import revedaEditor.gui.layoutDialogues as ldlg
import revedaEditor.gui.lsw as lsw
import revedaEditor.fileio.gdsExport as gdse
import revedaEditor.gui.helpBrowser as hlp
import revedaEditor.resources.resources
import revedaEditor.common.labels as lbl


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
            case "veriloga":
                # scb.createCellView(self.appMainW, viewItem.viewName, cellItem)
                if self.editProcess is None:
                    self.editProcess = QProcess()
                    self.editProcess.finished.connect(self.editProcessFinished)
                    self.editProcess.start(str(self.appMainW.textEditorPath), [])
            case "layout":
                layoutWindow = layoutEditor(
                    viewItem, self.libraryDict, self.libBrowserCont.designView
                )
                self.appMainW.openViews[viewTuple] = layoutWindow
                layoutWindow.loadLayout()
                layoutWindow.show()
            case "pcell":
                dlg = ldlg.pcellSettingDialogue(self.appMainW, viewItem, "pdk.pcells")
                if dlg.exec() == QDialog.Accepted:
                    items = list()
                    items.insert(0, {"cellView": "pcell"})
                    items.insert(1, {"reference": dlg.pcellCB.currentText()})
                    with viewItem.data(Qt.UserRole + 2).open(mode="w+") as pcellFile:
                        json.dump(items, pcellFile, indent=4)

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
                    self.appMainW.openViews[openCellViewTuple] = layoutWindow

                case "schematic":
                    schematicWindow = schematicEditor(
                        viewItem, self.libraryDict, self.libBrowserCont.designView
                    )
                    schematicWindow.loadSchematic()
                    schematicWindow.show()
                    self.appMainW.openViews[openCellViewTuple] = schematicWindow
                case "symbol":
                    symbolWindow = symbolEditor(
                        viewItem, self.libraryDict, self.libBrowserCont.designView
                    )
                    symbolWindow.loadSymbol()
                    symbolWindow.show()
                    self.appMainW.openViews[openCellViewTuple] = symbolWindow
                case "veriloga":
                    with open(viewItem.viewPath) as tempFile:
                        items = json.load(tempFile)
                    if items[1]["filePath"]:
                        if self.editProcess is None:
                            self.editProcess = QProcess()
                            VerilogafilePathObj = (
                                viewItem.parent()
                                .data(Qt.UserRole + 2)
                                .joinpath(items[1]["filePath"])
                            )
                            self.editProcess.finished.connect(self.editProcessFinished)
                            self.editProcess.start(
                                str(self.appMainW.textEditorPath), [str(VerilogafilePathObj)]
                            )
                    else:
                        self.logger.warning("File path not defined.")
                case "pcell":
                    with open(viewItem.viewPath) as tempFile:
                        items = json.load(tempFile)

                case "config":
                    with open(viewItem.viewPath) as tempFile:
                        items = json.load(tempFile)
                    viewName = items[0]["viewName"]
                    schematicName = items[1]["reference"]
                    schViewItem = libm.getViewItem(cellItem, schematicName)
                    configDict = items[2]
                    configWindow = self.openConfigEditWindow(
                        configDict, schViewItem, viewItem
                    )
                    self.appMainW.openViews[openCellViewTuple] = configWindow

        return openCellViewTuple

    def editProcessFinished(self):
        self.appMainW.importVerilogaClick()
        self.editProcess = None

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
        self.designView = designLibrariesView(self)
        self.layout.addWidget(self.designView)
        self.setLayout(self.layout)


class designLibrariesView(QTreeView):
    def __init__(self, parent):
        super().__init__(parent=parent)  # QTreeView
        self.parent = parent
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.viewCounter = 0
        self.libBrowsW = self.parent.parent
        self.appMainW = self.libBrowsW.appMainW
        self.libraryDict = self.appMainW.libraryDict  # type: dict
        self.cellViews = self.appMainW.cellViews  # type: list
        self.openViews = self.appMainW.openViews  # type: dict
        self.logger = self.appMainW.logger
        self.selectedItem = None
        # library model is based on qstandarditemmodel
        self.libraryModel = designLibrariesModel(self.libraryDict)
        self.setSortingEnabled(True)
        self.setUniformRowHeights(True)
        self.expandAll()
        self.setModel(self.libraryModel)

    def removeLibrary(self):
        button = QMessageBox.question(
            self,
            "Library Deletion",
            "Are you sure to delete " "this library? This action cannot be undone.",
        )
        if button == QMessageBox.Yes:
            shutil.rmtree(self.selectedItem.data(Qt.UserRole + 2))
            self.libraryModel.removeRow(self.selectedItem.row())

    def renameLib(self):
        oldLibraryName = self.selectedItem.libraryName
        dlg = fd.renameLibDialog(self, oldLibraryName)
        if dlg.exec() == QDialog.Accepted:
            newLibraryName = dlg.newLibraryName.text().strip()
            libraryItem = libm.getLibItem(self.libraryModel, oldLibraryName)
            libraryItem.setText(newLibraryName)
            oldLibraryPath = libraryItem.data(Qt.UserRole + 2)
            newLibraryPath = oldLibraryPath.parent.joinpath(newLibraryName)
            oldLibraryPath.rename(newLibraryPath)

    def createCell(self):
        dlg = fd.createCellDialog(self, self.libraryModel)
        assert isinstance(self.selectedItem, scb.libraryItem)
        dlg.libNamesCB.setCurrentText(self.selectedItem.libraryName)
        if dlg.exec() == QDialog.Accepted:
            cellName = dlg.cellCB.currentText()
            if cellName.strip() != "":
                scb.createCell(self, self.libraryModel, self.selectedItem, cellName)
            else:
                self.logger.error("Please enter a cell name.")

    def copyCell(self):
        dlg = fd.copyCellDialog(self, self.libraryModel, self.selectedItem)

        if dlg.exec() == QDialog.Accepted:
            scb.copyCell(
                self, dlg.model, dlg.cellItem, dlg.copyName.text(), dlg.selectedLibPath
            )

    def renameCell(self):
        dlg = fd.renameCellDialog(self, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            scb.renameCell(self, dlg.cellItem, dlg.nameEdit.text())

    def deleteCell(self):
        try:
            shutil.rmtree(self.selectedItem.data(Qt.UserRole + 2))
            self.selectedItem.parent().removeRow(self.selectedItem.row())
        except OSError as e:
            # print(f"Error:{e.strerror}")
            self.logger.warning(f"Error:{e}")

    def createCellView(self):
        dlg = fd.createCellViewDialog(self, self.libraryModel, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            viewItem = scb.createCellView(
                self.appMainW, dlg.nameEdit.text(), self.selectedItem
            )
            self.libBrowsW.createNewCellView(
                self.selectedItem.parent(), self.selectedItem, viewItem
            )

    def openView(self):
        viewItem = self.selectedItem
        cellItem = viewItem.parent()
        libItem = cellItem.parent()
        self.libBrowsW.openCellView(viewItem, cellItem, libItem)

    def copyView(self):
        dlg = fd.copyViewDialog(self, self.libraryModel)
        if dlg.exec() == QDialog.Accepted:
            if self.selectedItem.data(Qt.UserRole + 1) == "view":
                viewPath = self.selectedItem.data(Qt.UserRole + 2)
                selectedLibItem = libm.getLibItem(
                    self.libraryModel, dlg.libNamesCB.currentText()
                )
                cellName = dlg.cellCB.currentText()
                libCellNames = [
                    selectedLibItem.child(row).cellName
                    for row in range(selectedLibItem.rowCount())
                ]
                if (
                    cellName in libCellNames
                ):  # check if there is the cell in the library
                    cellItem = libm.getCellItem(
                        selectedLibItem, dlg.cellCB.currentText()
                    )
                else:
                    cellItem = scb.createCell(
                        self.libBrowsW,
                        self.libraryModel,
                        selectedLibItem,
                        dlg.cellCB.currentText(),
                    )
                cellViewNames = [
                    cellItem.child(row).viewName for row in range(cellItem.rowCount())
                ]
                newViewName = dlg.viewName.text()
                if newViewName in cellViewNames:
                    self.logger.warning(
                        "View already exists. Delete cellview and try again."
                    )
                else:
                    newViewPath = cellItem.data(Qt.UserRole + 2).joinpath(
                        f"{newViewName}.json"
                    )
                    shutil.copy(viewPath, newViewPath)
                    cellItem.appendRow(scb.viewItem(newViewPath))

    def renameView(self):
        oldViewName = self.selectedItem.viewName
        dlg = fd.renameViewDialog(self.libBrowsW, oldViewName)
        if dlg.exec() == QDialog.Accepted:
            newName = dlg.newViewNameEdit.text()
            try:
                viewPathObj = self.selectedItem.data(Qt.UserRole + 2)
                newPathObj = self.selectedItem.data(Qt.UserRole + 2).rename(
                    viewPathObj.parent.joinpath(f"{newName}.json")
                )
                self.selectedItem.parent().appendRow(scb.viewItem(newPathObj))
                self.selectedItem.parent().removeRow(self.selectedItem.row())
            except FileExistsError:
                self.logger.error("Cellview exists.")

    def deleteView(self):
        try:
            self.selectedItem.data(Qt.UserRole + 2).unlink()
            itemRow = self.selectedItem.row()
            parent = self.selectedItem.parent()
            parent.removeRow(itemRow)
        except OSError as e:
            # print(f"Error:{e.strerror}")
            self.logger.warning(f"Error:{e.strerror}")

    def reworkDesignLibrariesView(self, libraryDict: dict):
        """
        Recreate library model from libraryDict.
        """
        self.libraryModel = designLibrariesModel(libraryDict)
        self.setModel(self.libraryModel)
        self.libBrowsW.libraryModel = self.libraryModel

    # context menu
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        try:
            index = self.selectedIndexes()[0]
        except IndexError:
            pass
        try:
            self.selectedItem = self.libraryModel.itemFromIndex(index)
            if self.selectedItem.data(Qt.UserRole + 1) == "library":
                menu.addAction("Rename Library", self.renameLib)
                menu.addAction("Remove Library", self.removeLibrary)
                menu.addAction("Create Cell", self.createCell)
            elif self.selectedItem.data(Qt.UserRole + 1) == "cell":
                menu.addAction(
                    QAction("Create CellView...", self, triggered=self.createCellView)
                )
                menu.addAction(QAction("Copy Cell...", self, triggered=self.copyCell))
                menu.addAction(
                    QAction("Rename Cell...", self, triggered=self.renameCell)
                )
                menu.addAction(
                    QAction("Delete Cell...", self, triggered=self.deleteCell)
                )
            elif self.selectedItem.data(Qt.UserRole + 1) == "view":
                menu.addAction(QAction("Open View", self, triggered=self.openView))
                menu.addAction(QAction("Copy View...", self, triggered=self.copyView))
                menu.addAction(
                    QAction("Rename View...", self, triggered=self.renameView)
                )
                menu.addAction(
                    QAction("Delete View...", self, triggered=self.deleteView)
                )
            menu.exec(event.globalPos())
        except UnboundLocalError:
            pass


class designLibrariesModel(QStandardItemModel):
    def __init__(self, libraryDict):
        self.libraryDict = libraryDict
        super().__init__()
        self.rootItem = self.invisibleRootItem()
        self.setHorizontalHeaderLabels(["Libraries"])
        self.initModel()

    def initModel(self):
        for designPath in self.libraryDict.values():
            self.populateLibrary(designPath)

    def populateLibrary(self, designPath):  # designPath: Path
        """
        Populate library view.
        """
        if designPath.joinpath("reveda.lib").exists():
            libraryItem = self.addLibraryToModel(designPath)
            cellList = [cell.name for cell in designPath.iterdir() if cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell), libraryItem)
                viewList = [
                    view.name
                    for view in designPath.joinpath(cell).iterdir()
                    if view.suffix == ".json"
                ]
                for view in viewList:
                    self.addViewToModel(designPath.joinpath(cell, view), cellItem)

    def addLibraryToModel(self, designPath):
        libraryEntry = scb.libraryItem(designPath)
        self.rootItem.appendRow(libraryEntry)
        return libraryEntry

    def addCellToModel(self, cellPath, parentItem):
        cellEntry = scb.cellItem(cellPath)
        parentItem.appendRow(cellEntry)
        return cellEntry

    def addViewToModel(self, viewPath, parentItem):
        viewEntry = scb.viewItem(viewPath)
        parentItem.appendRow(viewEntry)


class libraryPathsModel(QStandardItemModel):
    def __init__(self, libraryDict):
        super().__init__()
        self.libraryDict = libraryDict
        self.setHorizontalHeaderLabels(["Library Name", "Library Path"])
        for key, value in self.libraryDict.items():
            libName = QStandardItem(key)
            libPath = QStandardItem(str(value))
            self.appendRow(libName, libPath)
        self.appendRow(QStandardItem("Click here..."), QStandardItem(""))


class libraryPathsTableView(QTableView):
    def __init__(self, model):
        self.model = model
        self.setModel(self.model)
        self.setShowGrid(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def contextMenuEvent(self, event) -> None:
        self.menu = QMenu(self)
        removePathAction = QAction("Remove Library Path...", self.menu)
        removePathAction.triggered.connect(lambda: self.removeLibraryPath(event))
        self.menu.addAction(removePathAction)
        self.menu.popup(QCursor.pos())

    def removeLibraryPath(self, event):
        print("remove library path")


class symbolViewsModel(designLibrariesModel):
    """
    Initializes the object with the given `libraryDict` and `symbolViews`.

    Parameters:
        libraryDict (dict): A dictionary containing the library information.
        symbolViews (list): A list of symbol views.

    Returns:
        None
    """

    def __init__(self, libraryDict: dict, symbolViews: list):
        self.symbolViews = symbolViews
        super().__init__(libraryDict)

    def populateLibrary(self, designPath):  # designPath: Path
        """
        Populate library view.
        """
        if designPath.joinpath("reveda.lib").exists():
            libraryItem = self.addLibraryToModel(designPath)
            cellList = [cell.name for cell in designPath.iterdir() if cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell), libraryItem)
                viewList = [
                    view.name
                    for view in designPath.joinpath(cell).iterdir()
                    if view.suffix == ".json"
                    and any(x in view.name for x in self.symbolViews)
                ]
                for view in viewList:
                    self.addViewToModel(designPath.joinpath(cell, view), cellItem)


class layoutViewsModel(designLibrariesModel):
    def __init__(self, libraryDict: dict, layoutViews: list):
        self.layoutViews = layoutViews
        super().__init__(libraryDict)

    def populateLibrary(self, designPath):  # designPath: Path
        """
        Populate library view.
        """
        if designPath.joinpath("reveda.lib").exists():
            libraryItem = self.addLibraryToModel(designPath)
            cellList = [cell.name for cell in designPath.iterdir() if cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell), libraryItem)
                viewList = [
                    view.name
                    for view in designPath.joinpath(cell).iterdir()
                    if view.suffix == ".json"
                    and any(x in view.name for x in self.layoutViews)
                ]
                for view in viewList:
                    self.addViewToModel(designPath.joinpath(cell, view), cellItem)


class editorWindow(QMainWindow):
    """
    Base class for editor windows.
    """

    def __init__(
        self,
        viewItem: scb.viewItem,
        libraryDict: dict,
        libraryView: designLibrariesView,
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
        self._app = QApplication.instance()
        self._createActions()
        self._createTriggers()
        self._createShortcuts()
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
        # if self._app.revedasim_path:
        #     pass
        self.init_UI()

    def init_UI(self):
        """
        Placeholder for child classes init_UI function.
        """
        ...

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
        self.menuCheck = self.editorMenuBar.addMenu("&Check")
        self.menuTools = self.editorMenuBar.addMenu("&Tools")
        self.menuWindow = self.editorMenuBar.addMenu("&Window")
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

        printIcon = QIcon(":/icons/printer--arrow.png")
        self.printAction = QAction(printIcon, "Print...", self)

        printPreviewIcon = QIcon(":/icons/printer--arrow.png")
        self.printPreviewAction = QAction(printPreviewIcon, "Print Preview...", self)

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

        rulerIcon = QIcon(":/icons/ruler.png")
        self.rulerAction = QAction(rulerIcon, "Add Ruler", self)

        delRulerIcon = QIcon.fromTheme(":/icons/ruler--minus.png")
        self.delRulerAction = QAction(delRulerIcon, "Delete Rulers", self)

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
        self.goUpAction = QAction(goUpIcon, "Go Up", self)

        goDownIcon = QIcon(":/icons/arrow-step.png")
        self.goDownAction = QAction(goDownIcon, "Go Down", self)

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
        self.createPolygonAction = QAction(createPolyIcon, "Create Polygon...", self)

        createCircleIcon = QIcon(":/icons/layer-shape-ellipse.png")
        self.createCircleAction = QAction(createCircleIcon, "Create Circle...", self)

        createArcIcon = QIcon(":/icons/layer-shape-polyline.png")
        self.createArcAction = QAction(createArcIcon, "Create Arc...", self)

        createViaIcon = QIcon(":/icons/layer-mask.png")
        self.createViaAction = QAction(createViaIcon, "Create Via...", self)

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

        createTextIcon = QIcon(":icons/sticky-note-text.png")
        self.createTextAction = QAction(createTextIcon, "Create Text...", self)

        ignoreIcon = QIcon(":/icons/minus-circle.png")
        self.ignoreAction = QAction(ignoreIcon, "Ignore", self)

        helpIcon = QIcon(":/icons/document-arrow.png")
        self.helpAction = QAction(helpIcon, "Help...", self)

        self.aboutIcon = QIcon(":/icons/information.png")
        self.aboutAction = QAction(self.aboutIcon, "About", self)

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
        self.menuView.addAction(self.dispConfigAction)
        self.menuView.addAction(self.selectConfigAction)
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
        self.selectMenu = self.menuEdit.addMenu("Select")
        self.selectMenu.addAction(self.selectAllAction)
        self.selectMenu.addAction(self.deselectAllAction)
        self.menuTools.addAction(self.readOnlyCellAction)
        self.menuCheck.addAction(self.viewCheckAction)
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
        if self.parentEditor is not None:
            self.parentEditor.raise_()
            # magic happens in close event.
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
        self.saveCell()
        if self.parentEditor is not None:
            self.parentEditor.updateDesignScene()
            self.parentEditor.raise_()
        event.accept()
        super().closeEvent(event)

    def _createMenu(self):
        pass

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
        self._addActions()
        self._layoutContextMenu()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = layoutContainer(self)
        self.setCentralWidget(self.centralW)

    def _createActions(self):
        super()._createActions()
        self.exportGDSAction = QAction("Export GDS", self)

    def _addActions(self):
        super()._addActions()
        self.menuEdit.addAction(self.stretchAction)
        self.menuCreate.addAction(self.createInstAction)
        self.menuCreate.addAction(self.createRectAction)
        self.menuCreate.addAction(self.createWireAction)
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
        self.layoutToolbar.addAction(self.createWireAction)
        self.layoutToolbar.addAction(self.createPinAction)
        self.layoutToolbar.addAction(self.createLabelAction)
        self.layoutToolbar.addAction(self.createViaAction)
        self.layoutToolbar.addAction(self.createPolygonAction)
        self.layoutToolbar.addSeparator()
        self.layoutToolbar.addAction(self.rulerAction)
        self.layoutToolbar.addAction(self.delRulerAction)
        self.layoutToolbar.addSeparator()
        self.layoutToolbar.addAction(self.goDownAction)

    def _createTriggers(self):
        super()._createTriggers()

        self.createInstAction.triggered.connect(self.createInstClick)
        self.createRectAction.triggered.connect(self.createRectClick)
        self.exportGDSAction.triggered.connect(self.exportGDSClick)
        self.createWireAction.triggered.connect(self.createPathClick)
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
        self.createWireAction.setShortcut(Qt.Key_W)
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
                    singleViaTuple, fabproc.dbu * float(selViaDefTuple.minSpacing), 1, 1
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
        libraryModel = layoutViewsModel(self.libraryDict, self.layoutViews)
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
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = schematicContainer(self)
        self.setCentralWidget(self.centralW)

    def _createActions(self):
        super()._createActions()
        self.netNameAction = QAction("Net Name", self)
        self.netNameAction.setShortcut(Qt.Key_L)
        self.hilightNetAction = QAction("Highlight Net", self)
        self.hilightNetAction.setCheckable(True)

    def _createTriggers(self):
        super()._createTriggers()

        self.createWireAction.triggered.connect(self.createWireClick)
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

    def _createMenuBar(self):
        super()._createMenuBar()
        self.menuSimulation = self.editorMenuBar.addMenu("&Simulation")
        self.menuHelp = self.editorMenuBar.addMenu("&Help")
        self._addActions()

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
        self.menuCreate.addAction(self.createWireAction)
        self.menuCreate.addAction(self.createBusAction)
        self.menuCreate.addAction(self.createLabelAction)
        self.menuCreate.addAction(self.createPinAction)
        self.menuCreate.addAction(self.createTextAction)
        self.menuCreate.addAction(self.createSymbolAction)

        # check menu
        self.menuCheck.addAction(self.viewErrorsAction)
        self.menuCheck.addAction(self.deleteErrorsAction)

        # tools menu
        self.menuTools.addAction(self.hilightNetAction)
        self.menuTools.addAction(self.netNameAction)

        # help menu

        self.menuSimulation.addAction(self.netlistAction)
        if self._app.revedasim_path:
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
        # self.schematicToolbar.addAction(self.createLabelAction)
        self.schematicToolbar.addAction(self.createSymbolAction)
        self.schematicToolbar.addSeparator()
        self.schematicToolbar.addAction(self.viewCheckAction)
        self.schematicToolbar.addSeparator()
        self.schematicToolbar.addAction(self.goDownAction)

    def _schematicContextMenu(self):
        super()._editorContextMenu()
        self.centralW.scene.itemContextMenu.addAction(self.ignoreAction)
        self.centralW.scene.itemContextMenu.addAction(self.goDownAction)

    def _createShortcuts(self):
        super()._createShortcuts()
        self.createInstAction.setShortcut(Qt.Key_I)
        self.createWireAction.setShortcut(Qt.Key_W)
        self.createPinAction.setShortcut(Qt.Key_P)
        self.goDownAction.setShortcut("Shift+E")

    def createWireClick(self, s):
        self.centralW.scene.editModes.setMode("drawWire")

    def createInstClick(self, s):
        # create a designLibrariesView
        libraryModel = symbolViewsModel(self.libraryDict, self.symbolViews)
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
        self.centralW.scene.createSymbol()

    def objPropClick(self, s):
        self.centralW.scene.editModes.setMode("selectItem")
        self.centralW.scene.viewObjProperties()

    def startSimClick(self, s):
        import revedasim.simMainWindow as smw

        simguiw = smw.simMainWindow(self)
        simguiw.show()

    def checkSaveCell(self):
        self.centralW.scene.groupAllNets()
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
        subDirPathObj = self.appMainW.simulationPath.joinpath(self.cellName)
        subDirPathObj.mkdir(parents=True, exist_ok=True)
        netlistFilePathObj = subDirPathObj.joinpath(
            f"{self.cellName}_" f"{selectedViewName}"
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
            xyceNetlRunner = startThread(netlistObj.writeNetlist())
            self.appMainW.threadPool.start(xyceNetlRunner)
            # netlistObj.writeNetlist()
            self.logger.info("Netlisting finished.")

    def goDownClick(self, s):
        self.centralW.scene.goDownHier()

    def ignoreClick(self, s):
        self.centralW.scene.ignoreSymbol()

    def netNameClick(self, s):
        self.centralW.scene.netNameEdit()

    def hilightNetClick(self, s):
        self.centralW.scene.hilightNets()


class symbolEditor(editorWindow):
    def __init__(
        self,
        viewItem: scb.viewItem,
        libraryDict: dict,
        libraryView: designLibrariesView,
    ):
        super().__init__(viewItem, libraryDict, libraryView)
        self.setWindowTitle(f"Symbol Editor - {self.cellName} - {self.viewName}")
        self._symbolContextMenu()
        # self._createActions()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
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

    def _createMenuBar(self):
        super()._createMenuBar()
        self.menuHelp = self.editorMenuBar.addMenu("&Help")
        self._addActions()

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
        self.scene = symbol_scene(self)
        self.view = symbol_view(self.scene, self)
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
        self.scene = schematic_scene(self)
        self.view = schematic_view(self.scene, self)
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
        assert isinstance(parent, layoutEditor)
        self.parent = parent
        self.lswModel = lsw.layerDataModel(laylyr.pdkAllLayers)
        self.lswWidget = lsw.layerViewTable(self, self.lswModel)
        self.lswWidget.dataSelected.connect(self.layerSelected)
        self.scene = layout_scene(self)
        self.view = layout_view(self.scene, self)
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

    def layerSelected(self, layerName):
        self.scene.selectEdLayer = [
            item for item in laylyr.pdkDrawingLayers if item.name == layerName
        ][0]


class editor_scene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.editorWindow = self.parent.parent
        self.majorGrid = self.editorWindow.majorGrid
        self.snapTuple = self.editorWindow.snapTuple
        self.mousePressLoc = None
        self.mouseMoveLoc = None
        self.mouseReleaseLoc = None
        # common edit modes
        self.editModes = ddef.editModes(
            selectItem=True,
            deleteItem=False,
            moveItem=False,
            copyItem=False,
            rotateItem=False,
            changeOrigin=False,
            panView=False,
        )
        self.readOnly = False  # if the scene is not editable
        self.undoStack = us.undoStack()

        self.origin = QPoint(0, 0)
        self.snapDistance = self.editorWindow.snapDistance
        self.cellName = self.editorWindow.file.parent.stem
        self.partialSelection = True
        self.selectionRectItem = None
        self.libraryDict = self.editorWindow.libraryDict
        self.editModes.rotateItem = False
        self.itemContextMenu = QMenu()
        self.appMainW = self.editorWindow.appMainW
        self.logger = self.appMainW.logger
        self.messageLine = self.editorWindow.messageLine
        self.statusLine = self.editorWindow.statusLine
        self.installEventFilter(self)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.mousePressLoc = event.scenePos().toPoint()
            if self.editModes.panView:
                self.centerViewOnPoint(self.mousePressLoc)

    def snapToBase(self, number, base):
        """
        Restrict a number to the multiples of base
        """
        return int(round(number / base)) * base

    def snapToGrid(self, point: QPoint, snapTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(
            self.snapToBase(point.x(), snapTuple[0]),
            self.snapToBase(point.y(), snapTuple[1]),
        )

    def rotateSelectedItems(self, point: QPoint):
        """
        Rotate selected items by 90 degree.
        """
        for item in self.selectedItems():
            self.rotateAnItem(point, item, 90)
        self.editModes.setMode("selectItem")

    def rotateAnItem(self, point: QPoint, item, angle):
        rotationOriginPoint = item.mapFromScene(point)
        item.setTransformOriginPoint(rotationOriginPoint)
        item.angle += angle
        item.setRotation(item.angle)
        undoCommand = us.undoRotateShape(self, item, item.angle)
        self.undoStack.push(undoCommand)

    def eventFilter(self, source, event):
        """
        Mouse events should snap to background grid points.
        """
        if self.readOnly:  # if read only do not propagate any mouse events
            return True
        elif event.type() in [
            QEvent.GraphicsSceneMouseMove,
            QEvent.GraphicsSceneMousePress,
            QEvent.GraphicsSceneMouseRelease,
        ]:
            event.setScenePos(
                self.snapToGrid(event.scenePos(), self.snapTuple).toPointF()
            )
            return False
        else:
            return super().eventFilter(source, event)

    def copySelectedItems(self):
        pass

    def selectSceneItems(self, modifiers):
        """
        Selects scene items based on the given modifiers.
        A selection rectangle is drawn if ShiftModifier is pressed,
        else a single item is selected. The function does not return anything.

        :param modifiers: The keyboard modifiers that determine the selection type.
        :type modifiers: Qt.KeyboardModifiers
        """
        if modifiers == Qt.ShiftModifier:
            self.editorWindow.messageLine.setText("Draw Selection Rectangle")
            self.selectionRectItem = QGraphicsRectItem(
                QRectF(self.mousePressLoc, self.mousePressLoc)
            )
            self.selectionRectItem.setPen(schlyr.draftPen)
            self.undoStack.push(us.addShapeUndo(self, self.selectionRectItem))
            # self.addItem(self.selectionRectItem)
        else:
            self.editorWindow.messageLine.setText("Select an item")
            itemsAtMousePress = self.items(self.mousePressLoc)
            if itemsAtMousePress:
                [item.setSelected(True) for item in itemsAtMousePress]
        self.editorWindow.messageLine.setText(
            "Item selected" if self.selectedItems() else "Nothing selected"
        )

    def selectInRectItems(self, selectionRect: QRect, partialSelection=False):
        """
        Select items in the scene.
        """

        mode = Qt.IntersectsItemShape if partialSelection else Qt.ContainsItemShape
        [item.setSelected(True) for item in self.items(selectionRect, mode=mode)]

    def selectAll(self):
        """
        Select all items in the scene.
        """
        [item.setSelected(True) for item in self.items()]

    def deselectAll(self):
        """
        Deselect all items in the scene.
        """
        [item.setSelected(False) for item in self.selectedItems()]

    def deleteSelectedItems(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                # self.removeItem(item)
                undoCommand = us.deleteShapeUndo(self, item)
                self.undoStack.push(undoCommand)
            self.update()  # update the scene

    def stretchSelectedItems(self):
        if self.selectedItems() is not None:
            try:
                for item in self.selectedItems():
                    if hasattr(item, "stretch"):
                        item.stretch = True
            except AttributeError:
                self.messageLine.setText("Nothing selected")

    def fitItemsInView(self) -> None:
        self.setSceneRect(self.itemsBoundingRect().adjusted(-40, -40, 40, 40))
        self.views()[0].fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        self.views()[0].viewport().update()

    def moveSceneLeft(self) -> None:
        currentSceneRect = self.sceneRect()
        halfWidth = currentSceneRect.width() / 2.0
        newSceneRect = QRectF(
            currentSceneRect.left() - halfWidth,
            currentSceneRect.top(),
            currentSceneRect.width(),
            currentSceneRect.height(),
        )
        self.setSceneRect(newSceneRect)

    def moveSceneRight(self) -> None:
        currentSceneRect = self.sceneRect()
        halfWidth = currentSceneRect.width() / 2.0
        newSceneRect = QRectF(
            currentSceneRect.left() + halfWidth,
            currentSceneRect.top(),
            currentSceneRect.width(),
            currentSceneRect.height(),
        )
        self.setSceneRect(newSceneRect)

    def moveSceneUp(self) -> None:
        currentSceneRect = self.sceneRect()
        halfWidth = currentSceneRect.width() / 2.0
        newSceneRect = QRectF(
            currentSceneRect.left(),
            currentSceneRect.top() - halfWidth,
            currentSceneRect.width(),
            currentSceneRect.height(),
        )
        self.setSceneRect(newSceneRect)

    def moveSceneDown(self) -> None:
        currentSceneRect = self.sceneRect()
        halfWidth = currentSceneRect.width() / 2.0
        newSceneRect = QRectF(
            currentSceneRect.left(),
            currentSceneRect.top() + halfWidth,
            currentSceneRect.width(),
            currentSceneRect.height(),
        )
        self.setSceneRect(newSceneRect)

    def centerViewOnPoint(self, point: QPoint) -> None:
        view = self.views()[0]
        view_widget = view.viewport()
        width = view_widget.width()
        height = view_widget.height()
        self.setSceneRect(point.x() - width / 2, point.y() - height / 2, width, height)

    def addUndoStack(self, item):
        undoCommand = us.addShapeUndo(self, item)
        self.undoStack.push(undoCommand)

    def addListUndoStack(self, itemList: list):
        undoCommand = us.addShapesUndo(self, itemList)
        self.undoStack.push(undoCommand)


class symbol_scene(editor_scene):
    """
    Scene for Symbol editor.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        # drawing modes
        self.editModes = ddef.symbolModes(
            selectItem=True,
            deleteItem=False,
            moveItem=False,
            copyItem=False,
            rotateItem=False,
            changeOrigin=False,
            panView=False,
            drawPin=False,
            drawArc=False,
            drawRect=False,
            drawLine=False,
            addLabel=False,
            drawCircle=False,
            drawPolygon=False,
            stretchItem=False,
        )

        self.symbolShapes = ["line", "arc", "rect", "circle", "pin", "label", "polygon"]

        self.origin = QPoint(0, 0)
        # some default attributes
        self.newPin = None
        self.pinName = ""
        self.pinType = shp.symbolPin.pinTypes[0]
        self.pinDir = shp.symbolPin.pinDirs[0]
        self.labelDefinition = ""
        self.labelType = lbl.symbolLabel.labelTypes[0]
        self.labelOrient = lbl.symbolLabel.labelOrients[0]
        self.labelAlignment = lbl.symbolLabel.labelAlignments[0]
        self.labelUse = lbl.symbolLabel.labelUses[0]
        self.labelVisible = False
        self.labelHeight = "12"
        self.labelOpaque = True
        self.newLine = None
        self.newRect = None
        self.newCirc = None
        self.newArc = None
        self.newPolygon = None
        self.polygonGuideLine = None

    @property
    def drawMode(self):
        return any(
            (
                self.editModes.drawPin,
                self.editModes.drawArc,
                self.editModes.drawLine,
                self.editModes.drawRect,
                self.editModes.drawCircle,
                self.editModes.drawPolygon,
            )
        )

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(mouse_event)
        try:
            modifiers = QGuiApplication.keyboardModifiers()
            self.viewRect = self.parent.view.mapToScene(
                self.parent.view.viewport().rect()
            ).boundingRect()
            if mouse_event.button() == Qt.LeftButton:
                self.mousePressLoc = self.snapToGrid(
                    mouse_event.scenePos().toPoint(), self.snapTuple
                )
                if self.editModes.changeOrigin:  # change origin of the symbol
                    self.origin = self.mousePressLoc
                    self.editModes.changeOrigin = False
                if self.editModes.selectItem:
                    self.selectSceneItems(modifiers)
                if self.editModes.drawPin:
                    self.editorWindow.messageLine.setText("Add Symbol Pin")
                    self.newPin = self.pinDraw(self.mousePressLoc)
                    self.newPin.setSelected(True)
                elif self.editModes.drawLine:
                    self.newLine.setSelected(False)
                    self.newLine = None
                elif self.editModes.addLabel:
                    self.newLabel = self.labelDraw(
                        self.mousePressLoc,
                        self.labelDefinition,
                        self.labelType,
                        self.labelHeight,
                        self.labelAlignment,
                        self.labelOrient,
                        self.labelUse,
                    )
                    self.newLabel.setSelected(True)
                elif self.editModes.drawRect:
                    self.newRect = self.rectDraw(self.mousePressLoc, self.mousePressLoc)
                elif self.editModes.drawCircle:
                    self.editorWindow.messageLine.setText(
                        "Click on the center of the circle"
                    )
                    self.newCircle = self.circleDraw(
                        self.mousePressLoc, self.mousePressLoc
                    )
                elif self.editModes.drawPolygon:
                    if self.newPolygon is None:
                        # Create a new polygon
                        self.newPolygon = shp.symbolPolygon(
                            [self.mousePressLoc, self.mousePressLoc],
                        )
                        self.addUndoStack(self.newPolygon)
                        # Create a guide line for the polygon
                        self.polygonGuideLine = QGraphicsLineItem(
                            QLineF(
                                self.newPolygon.points[-2], self.newPolygon.points[-1]
                            )
                        )
                        self.polygonGuideLine.setPen(
                            QPen(QColor(255, 255, 0), 1, Qt.DashLine)
                        )
                        self.addUndoStack(self.polygonGuideLine)

                    else:
                        self.newPolygon.addPoint(self.mousePressLoc)
                elif self.editModes.drawArc:
                    self.editorWindow.messageLine.setText("Start drawing an arc")
                    self.newArc = self.arcDraw(self.mousePressLoc, self.mousePressLoc)
                if self.editModes.rotateItem:
                    self.editorWindow.messageLine.setText("Rotate item")
                    if self.selectedItems():
                        self.rotateSelectedItems(self.mousePressLoc)
        except Exception as e:
            self.logger.error(f"Error in mousePressEvent: {e}")

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(mouse_event)
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        if mouse_event.buttons() == Qt.LeftButton:
            if self.editModes.drawPin and self.newPin.isSelected():
                self.newPin.setPos(self.mouseMoveLoc - self.mousePressLoc)
            elif self.editModes.drawRect:
                self.editorWindow.messageLine.setText(
                    "Release mouse on the bottom left point"
                )
                self.newRect.end = self.mouseMoveLoc
            elif self.editModes.drawCircle:
                self.editorWindow.messageLine.setText("Extend Circle")
                radius = (
                    (self.mouseMoveLoc.x() - self.mousePressLoc.x()) ** 2
                    + (self.mouseMoveLoc.y() - self.mousePressLoc.y()) ** 2
                ) ** 0.5
                self.newCircle.radius = radius
            elif self.editModes.drawArc:
                self.editorWindow.messageLine.setText("Extend Arc")
                self.newArc.end = self.mouseMoveLoc
            elif self.editModes.selectItem and modifiers == Qt.ShiftModifier:
                self.selectionRectItem.setRect(
                    QRectF(self.mousePressLoc, self.mouseMoveLoc)
                )
        else:
            if self.editModes.drawPolygon and self.newPolygon is not None:
                self.polygonGuideLine.setLine(
                    QLineF(self.newPolygon.points[-1], self.mouseMoveLoc)
                )
            elif self.editModes.drawLine and self.newLine is not None:
                self.editorWindow.messageLine.setText("Release mouse on the end point")
                self.newLine.end = self.mouseMoveLoc
        self.statusLine.showMessage(
            f"Cursor Position: {(self.mouseMoveLoc - self.origin).toTuple()}")

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        try:
            self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
            modifiers = QGuiApplication.keyboardModifiers()
            if mouse_event.button() == Qt.LeftButton:
                if self.editModes.drawLine:
                    self.editorWindow.messageLine.setText("Drawing a Line")
                    self.newLine = self.lineDraw(self.mousePressLoc, self.mousePressLoc)
                    self.newLine.setSelected(True)

                elif self.editModes.drawCircle:
                    self.newCircle.setSelected(False)
                    self.newCircle.update()
                elif self.editModes.drawPin:
                    self.newPin.setSelected(False)
                    self.newPin = None
                elif self.editModes.drawRect:
                    self.newRect.setSelected(False)
                elif self.editModes.drawArc:
                    self.newArc.setSelected(False)
                elif self.editModes.addLabel:
                    self.newLabel.setSelected(False)
                    self.editModes.addLabel = False
                elif self.editModes.selectItem and modifiers == Qt.ShiftModifier:
                    self.selectInRectItems(
                        self.selectionRectItem.rect(), self.partialSelection
                    )
                    self.removeItem(self.selectionRectItem)
                    self.selectionRectItem = None
        except Exception as e:
            self.logger.error(f"Error in Mouse Press Event: {e} ")

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseDoubleClickEvent(event)
        self.mouseDoubleClickLoc = event.scenePos().toPoint()
        try:
            if event.button() == Qt.LeftButton and self.editModes.drawPolygon:
                self.newPolygon.polygon.remove(0)
                self.newPolygon.points.pop(0)
                self.editModes.setMode("selectItem")
                self.newPolygon = None
                self.removeItem(self.polygonGuideLine)
                self.polygonGuideLine = None
        except Exception as e:
            self.logger.error(f"Error in mouse Double Click Event: {e}")

    def lineDraw(self, start: QPoint, current: QPoint):
        line = shp.symbolLine(start, current)
        # self.addItem(line)
        undoCommand = us.addShapeUndo(self, line)
        self.undoStack.push(undoCommand)
        return line

    def rectDraw(self, start: QPoint, end: QPoint):
        """
        Draws a rectangle on the scene
        """
        rect = shp.symbolRectangle(start, end)
        # self.addItem(rect)
        undoCommand = us.addShapeUndo(self, rect)
        self.undoStack.push(undoCommand)
        return rect

    def circleDraw(self, start: QPoint, end: QPoint):
        """
        Draws a circle on the scene
        """
        circle = shp.symbolCircle(start, end)
        # self.addItem(circle)
        undoCommand = us.addShapeUndo(self, circle)
        self.undoStack.push(undoCommand)
        return circle

    def arcDraw(self, start: QPoint, end: QPoint):
        """
        Draws an arc inside the rectangle defined by start and end points.
        """
        arc = shp.symbolArc(start, end)
        # self.addItem(arc)
        undoCommand = us.addShapeUndo(self, arc)
        self.undoStack.push(undoCommand)
        return arc

    def pinDraw(self, current):
        pin = shp.symbolPin(current, self.pinName, self.pinDir, self.pinType)
        # self.addItem(pin)
        undoCommand = us.addShapeUndo(self, pin)
        self.undoStack.push(undoCommand)
        return pin

    def labelDraw(
        self,
        current,
        labelDefinition,
        labelType,
        labelHeight,
        labelAlignment,
        labelOrient,
        labelUse,
    ):
        label = lbl.symbolLabel(
            current,
            labelDefinition,
            labelType,
            labelHeight,
            labelAlignment,
            labelOrient,
            labelUse,
        )
        label.labelVisible = self.labelOpaque
        label.labelDefs()
        label.setOpacity(1)
        undoCommand = us.addShapeUndo(self, label)
        self.undoStack.push(undoCommand)
        return label

    def copySelectedItems(self):
        """
        Copies the selected items in the scene, creates a duplicate of each item,
        and adds them to the scene with a slight shift in position.
        """
        for item in self.selectedItems():
            # Serialize the item to JSON
            selectedItemJson = json.dumps(item, cls=symenc.symbolEncoder)

            # Deserialize the JSON back to a dictionary
            itemCopyDict = json.loads(selectedItemJson)

            # Create a new shape based on the item dictionary and the snap tuple
            shape = lj.symbolItems(self).create(itemCopyDict)

            # Create an undo command for adding the shape
            undo_command = us.addShapeUndo(self, shape)

            # Push the undo command to the undo stack
            self.undoStack.push(undo_command)

            # Shift the position of the shape by one grid unit to the right and down
            shape.setPos(
                QPoint(
                    item.pos().x() + 4 * self.snapTuple[0],
                    item.pos().y() + 4 * self.snapTuple[1],
                )
            )

    def moveBySelectedItems(self):
        if self.selectedItems():
            dlg = pdlg.moveByDialogue(self.editorWindow)
            dlg.xEdit.setText("0")
            dlg.yEdit.setText("0")
            if dlg.exec() == QDialog.Accepted:
                for item in self.selectedItems():
                    item.moveBy(
                        self.snapToBase(float(dlg.xEdit.text()), self.snapTuple[0]),
                        self.snapToBase(float(dlg.yEdit.text()), self.snapTuple[1]),
                    )
            self.editorWindow.messageLine.setText(
                f"Moved items by {dlg.xEdit.text()} and {dlg.yEdit.text()}"
            )
            self.editModes.setMode("selectItem")

    def itemProperties(self):
        """
        When item properties is queried.
        """
        if not self.selectedItems():
            return
        for item in self.selectedItems():
            if isinstance(item, shp.symbolRectangle):
                self.queryDlg = pdlg.rectPropertyDialog(self.editorWindow)
                [left, top, width, height] = item.rect.getRect()
                sceneTopLeftPoint = item.mapToScene(QPoint(left, top))
                self.queryDlg.rectLeftLine.setText(str(sceneTopLeftPoint.x()))
                self.queryDlg.rectTopLine.setText(str(sceneTopLeftPoint.y()))
                self.queryDlg.rectWidthLine.setText(str(width))  # str(width))
                self.queryDlg.rectHeightLine.setText(str(height))  # str(height))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateRectangleShape(item)
            if isinstance(item, shp.symbolCircle):
                self.queryDlg = pdlg.circlePropertyDialog(self.editorWindow)
                centre = item.mapToScene(item.centre).toTuple()
                radius = item.radius
                self.queryDlg.centerXEdit.setText(str(centre[0]))
                self.queryDlg.centerYEdit.setText(str(centre[1]))
                self.queryDlg.radiusEdit.setText(str(radius))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateCircleShape(item)
            if isinstance(item, shp.symbolArc):
                self.queryDlg = pdlg.arcPropertyDialog(self.editorWindow)
                sceneStartPoint = item.mapToScene(item.start)
                self.queryDlg.startXEdit.setText(str(sceneStartPoint.x()))
                self.queryDlg.startYEdit.setText(str(sceneStartPoint.y()))
                self.queryDlg.widthEdit.setText(str(item.width))
                self.queryDlg.heightEdit.setText(str(item.height))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateArcShape(item)
            elif isinstance(item, shp.symbolLine):
                self.queryDlg = pdlg.linePropertyDialog(self.editorWindow)
                sceneLineStartPoint = item.mapToScene(item.start).toPoint()
                sceneLineEndPoint = item.mapToScene(item.end).toPoint()
                self.queryDlg.startXLine.setText(str(sceneLineStartPoint.x()))
                self.queryDlg.startYLine.setText(str(sceneLineStartPoint.y()))
                self.queryDlg.endXLine.setText(str(sceneLineEndPoint.x()))
                self.queryDlg.endYLine.setText(str(sceneLineEndPoint.y()))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateLineShape(item)
            elif isinstance(item, shp.symbolPin):
                self.queryDlg = pdlg.pinPropertyDialog(self.editorWindow)
                self.queryDlg.pinName.setText(str(item.pinName))
                self.queryDlg.pinType.setCurrentText(item.pinType)
                self.queryDlg.pinDir.setCurrentText(item.pinDir)
                sceneStartPoint = item.mapToScene(item.start).toPoint()
                self.queryDlg.pinXLine.setText(str(sceneStartPoint.x()))
                self.queryDlg.pinYLine.setText(str(sceneStartPoint.y()))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updatePinShape(item)
            elif isinstance(item, lbl.symbolLabel):
                self.queryDlg = pdlg.labelPropertyDialog(self.editorWindow)
                self.queryDlg.labelDefinition.setText(str(item.labelDefinition))
                self.queryDlg.labelHeightEdit.setText(str(item.labelHeight))
                self.queryDlg.labelAlignCombo.setCurrentText(item.labelAlign)
                self.queryDlg.labelOrientCombo.setCurrentText(item.labelOrient)
                self.queryDlg.labelUseCombo.setCurrentText(item.labelUse)
                if item.labelVisible:
                    self.queryDlg.labelVisiCombo.setCurrentText("Yes")
                else:
                    self.queryDlg.labelVisiCombo.setCurrentText("No")
                if item.labelType == "Normal":
                    self.queryDlg.normalType.setChecked(True)
                elif item.labelType == "NLPLabel":
                    self.queryDlg.NLPType.setChecked(True)
                elif item.labelType == "PyLabel":
                    self.queryDlg.pyLType.setChecked(True)
                sceneStartPoint = item.mapToScene(item.start)
                self.queryDlg.labelXLine.setText(str(sceneStartPoint.x()))
                self.queryDlg.labelYLine.setText(str(sceneStartPoint.y()))
                if self.queryDlg.exec() == QDialog.Accepted:
                    self.updateLabelShape(item)

    def updateRectangleShape(self, item: shp.symbolRectangle):
        """
        Both dictionaries have the topleft corner of rectangle in scene coordinates.
        """
        origItemList = item.rect.getRect()  # in item coordinates
        left = self.snapToBase(
            float(self.queryDlg.rectLeftLine.text()), self.snapTuple[0]
        )
        top = self.snapToBase(
            float(self.queryDlg.rectTopLine.text()), self.snapTuple[1]
        )
        width = self.snapToBase(
            float(self.queryDlg.rectWidthLine.text()), self.snapTuple[0]
        )
        height = self.snapToBase(
            float(self.queryDlg.rectHeightLine.text()), self.snapTuple[1]
        )
        topLeftPoint = item.mapFromScene(QPoint(left, top))
        newItemList = [topLeftPoint.x(), topLeftPoint.y(), width, height]
        undoCommand = us.updateSymRectUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updateCircleShape(self, item: shp.symbolCircle):
        origItemList = [item.centre.x(), item.centre.y(), item.radius]
        centerX = self.snapToBase(
            float(self.queryDlg.centerXEdit.text()), self.snapTuple[0]
        )
        centerY = self.snapToBase(
            float(self.queryDlg.centerYEdit.text()), self.snapTuple[1]
        )
        radius = self.snapToBase(
            float(self.queryDlg.radiusEdit.text()), self.snapTuple[0]
        )
        centrePoint = item.mapFromScene(
            self.snapToGrid(QPoint(centerX, centerY), self.snapTuple)
        )
        newItemList = [centrePoint.x(), centrePoint.y(), radius]
        undoCommand = us.updateSymCircleUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updateArcShape(self, item: shp.symbolArc):
        origItemList = [item.start.x(), item.start.y(), item.width, item.height]
        startX = self.snapToBase(
            float(self.queryDlg.startXEdit.text()), self.snapTuple[0]
        )
        startY = self.snapToBase(
            float(self.queryDlg.startYEdit.text()), self.snapTuple[1]
        )
        start = item.mapFromScene(QPoint(startX, startY)).toPoint()
        width = self.snapToBase(
            float(self.queryDlg.widthEdit.text()), self.snapTuple[0]
        )
        height = self.snapToBase(
            float(self.queryDlg.heightEdit.text()), self.snapTuple[1]
        )
        newItemList = [start.x(), start.y(), width, height]
        undoCommand = us.updateSymArcUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updateLineShape(self, item: shp.symbolLine):
        """
        Updates line shape from dialogue entries.
        """
        origItemList = [item.start.x(), item.start.y(), item.end.x(), item.end.y()]
        startX = self.snapToBase(
            float(self.queryDlg.startXLine.text()), self.snapTuple[0]
        )
        startY = self.snapToBase(
            float(self.queryDlg.startYLine.text()), self.snapTuple[1]
        )
        endX = self.snapToBase(float(self.queryDlg.endXLine.text()), self.snapTuple[0])
        endY = self.snapToBase(float(self.queryDlg.endYLine.text()), self.snapTuple[1])
        start = item.mapFromScene(QPoint(startX, startY)).toPoint()
        end = item.mapFromScene(QPoint(endX, endY)).toPoint()
        newItemList = [start.x(), start.y(), end.x(), end.y()]
        undoCommand = us.updateSymLineUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updatePinShape(self, item: shp.symbolPin):
        origItemList = [
            item.start.x(),
            item.start.y(),
            item.pinName,
            item.pinDir,
            item.pinType,
        ]
        sceneStartX = self.snapToBase(
            float(self.queryDlg.pinXLine.text()), self.snapTuple[0]
        )
        sceneStartY = self.snapToBase(
            float(self.queryDlg.pinYLine.text()), self.snapTuple[1]
        )

        start = item.mapFromScene(QPoint(sceneStartX, sceneStartY)).toPoint()
        pinName = self.queryDlg.pinName.text()
        pinType = self.queryDlg.pinType.currentText()
        pinDir = self.queryDlg.pinDir.currentText()
        newItemList = [start.x(), start.y(), pinName, pinDir, pinType]
        undoCommand = us.updateSymPinUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def updateLabelShape(self, item: lbl.symbolLabel):
        """
        update label with new values.
        """
        origItemList = [
            item.start.x(),
            item.start.y(),
            item.labelDefinition,
            item.labelType,
            item.labelHeight,
            item.labelAlign,
            item.labelOrient,
            item.labelUse,
        ]
        sceneStartX = self.snapToBase(
            float(self.queryDlg.labelXLine.text()), self.snapTuple[0]
        )
        sceneStartY = self.snapToBase(
            float(self.queryDlg.labelYLine.text()), self.snapTuple[1]
        )
        start = item.mapFromScene(QPoint(sceneStartX, sceneStartY))
        labelDefinition = self.queryDlg.labelDefinition.text()
        labelHeight = self.queryDlg.labelHeightEdit.text()
        labelAlign = self.queryDlg.labelAlignCombo.currentText()
        labelOrient = self.queryDlg.labelOrientCombo.currentText()
        labelUse = self.queryDlg.labelUseCombo.currentText()
        labelVisible = self.queryDlg.labelVisiCombo.currentText() == "Yes"
        if self.queryDlg.normalType.isChecked():
            labelType = lbl.symbolLabel.labelTypes[0]
        elif self.queryDlg.NLPType.isChecked():
            labelType = lbl.symbolLabel.labelTypes[1]
        elif self.queryDlg.pyLType.isChecked():
            labelType = lbl.symbolLabel.labelTypes[2]
        # set opacity to 1 so that the label is still visible on symbol editor
        item.setOpacity(1)
        newItemList = [
            start.x(),
            start.y(),
            labelDefinition,
            labelType,
            labelHeight,
            labelAlign,
            labelOrient,
            labelUse,
        ]
        undoCommand = us.updateSymLabelUndo(item, origItemList, newItemList)
        self.undoStack.push(undoCommand)

    def loadSymbol(self, itemsList: list):
        snapGrid = itemsList[1].get("snapGrid")
        self.majorGrid = snapGrid[0]  # dot/line grid spacing
        self.snapGrid = snapGrid[1]  # snapping grid size
        self.snapTuple = (self.snapGrid, self.snapGrid)
        self.snapDistance = 2 * self.snapGrid
        self.parent.view.snapTuple = self.snapTuple
        self.editorWindow.snapTuple = self.snapTuple
        self.attributeList = []
        for item in itemsList[2:]:
            if item is not None:
                if item["type"] in self.symbolShapes:
                    itemShape = lj.symbolItems(self).create(item)
                    # items should be always visible in symbol view
                    if isinstance(itemShape, lbl.symbolLabel):
                        itemShape.setOpacity(1)
                    self.addItem(itemShape)
                elif item["type"] == "attr":
                    attr = lj.symbolItems(self).createSymbolAttribute(item)
                    self.attributeList.append(attr)

    def saveSymbolCell(self, fileName: pathlib.Path):
        # items = self.items(self.sceneRect())  # get items in scene rect
        items = self.items()
        items.insert(0, {"cellView": "symbol"})
        items.insert(1, {"snapGrid": self.snapTuple})
        if hasattr(self, "attributeList"):
            items.extend(self.attributeList)  # add attribute list to list
        with fileName.open(mode="w") as f:
            try:
                json.dump(items, f, cls=symenc.symbolEncoder, indent=4)
            except Exception as e:
                self.logger.error(f"Symbol save error: {e}")

    def reloadScene(self):
        items = self.items()
        if hasattr(self, "attributeList"):
            items.extend(self.attributeList)
        items = json.loads(json.dumps(items, cls=symenc.symbolEncoder))
        self.clear()
        self.loadSymbol(items)

    def viewSymbolProperties(self):
        """
        View symbol properties dialog.
        """
        # copy symbol attribute list to another list by deepcopy to be safe
        attributeListCopy = deepcopy(self.attributeList)
        symbolPropDialogue = pdlg.symbolLabelsDialogue(
            self.editorWindow, self.items(), attributeListCopy
        )
        if symbolPropDialogue.exec() == QDialog.Accepted:
            for i, item in enumerate(symbolPropDialogue.labelItemList):
                # label name is not changed.
                item.labelHeight = symbolPropDialogue.labelHeightList[i].text()
                item.labelAlign = symbolPropDialogue.labelAlignmentList[i].currentText()
                item.labelOrient = symbolPropDialogue.labelOrientationList[
                    i
                ].currentText()
                item.labelUse = symbolPropDialogue.labelUseList[i].currentText()
                item.labelType = symbolPropDialogue.labelTypeList[i].currentText()
                item.update(item.boundingRect())
            # create an empty attribute list. If the dialog is OK, the local attribute list
            # will be copied to the symbol attribute list.
            localAttributeList = []
            for i, item in enumerate(symbolPropDialogue.attributeNameList):
                if item.text().strip() != "":
                    localAttributeList.append(
                        symenc.symbolAttribute(
                            item.text(), symbolPropDialogue.attributeDefList[i].text()
                        )
                    )
                self.attributeList = deepcopy(localAttributeList)


class schematic_scene(editor_scene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.instCounter = 0
        self.start = QPoint(0, 0)
        self.current = QPoint(0, 0)
        self.editModes = ddef.schematicModes(
            selectItem=True,
            deleteItem=False,
            moveItem=False,
            copyItem=False,
            rotateItem=False,
            changeOrigin=False,
            panView=False,
            drawPin=False,
            drawWire=False,
            drawText=False,
            addInstance=False,
        )
        self.itemCounter = 0
        self.netCounter = 0
        self.schematicNets = {}  # netName: list of nets with the same name
        self._crossDotPoints = {}  # locations of cross dots
        self.crossDots = set()  # list of cross dots
        self.viewRect = None
        self.instanceSymbolTuple = None
        # pin attribute defaults
        self.pinName = ""
        self.pinType = "Signal"
        self.pinDir = "Input"
        self.parentView = None
        # self.wires = None
        self._newNet = None
        self.newInstance = None
        self.newPin = None
        self.newText = None
        self._snapPointRect = None
        self.highlightNets = False
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamily = [
            family for family in fontFamilies if QFontDatabase.isFixedPitch(family)
        ][0]
        fontStyle = QFontDatabase.styles(fixedFamily)[1]
        self.fixedFont = QFont(fixedFamily)
        self.fixedFont.setStyleName(fontStyle)
        fontSize = [size for size in QFontDatabase.pointSizes(fixedFamily, fontStyle)][
            3
        ]
        self.fixedFont.setPointSize(fontSize)
        self.fixedFont.setKerning(False)

    @property
    def drawMode(self):
        return any(
            (self.editModes.drawPin, self.editModes.drawWire, self.editModes.drawText)
        )

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(mouse_event)
        try:
            modifiers = QGuiApplication.keyboardModifiers()
            self.viewRect = self.parent.view.mapToScene(
                self.parent.view.viewport().rect()
            ).boundingRect()

            if mouse_event.button() == Qt.LeftButton:
                self.mousePressLoc = mouse_event.scenePos().toPoint()

                if self.editModes.addInstance:
                    self.newInstance = self.drawInstance(self.mousePressLoc)
                    self.newInstance.setSelected(True)
                elif self.editModes.drawWire and self._newNet is not None:
                    self.checkNewNet(self._newNet)
                    self._newNet = None
                elif self.editModes.changeOrigin:  # change origin of the symbol
                    self.origin = self.mousePressLoc
                    self.editModes.changeOrigin = False

                elif self.editModes.drawPin:
                    self.editorWindow.messageLine.setText("Add a pin")
                    self.newPin = self.addPin(self.mousePressLoc)
                    self.newPin.setSelected(True)

                elif self.editModes.drawText:
                    self.editorWindow.messageLine.setText("Add a text note")
                    self.newText = self.addNote(self.mousePressLoc)
                    # TODO: What is wrong here?
                    self.rotateAnItem(
                        self.mousePressLoc, self.newText, float(self.noteOrient[1:])
                    )
                    self.newText.setSelected(True)
                elif self.editModes.rotateItem:
                    self.editorWindow.messageLine.setText("Rotate item")
                    if self.selectedItems():
                        self.rotateSelectedItems(self.mousePressLoc)

                elif self.editModes.selectItem:
                    self.selectSceneItems(modifiers)

        except Exception as e:
            self.logger.error(f"mouse press error: {e}")

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(mouse_event)
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        try:
            if mouse_event.buttons() == Qt.LeftButton:
                if self.editModes.addInstance:
                    # TODO: think how to do it with mapFromScene
                    self.newInstance.setPos(self.mouseMoveLoc - self.mousePressLoc)

                elif self.editModes.drawPin and self.newPin.isSelected():
                    self.newPin.setPos(self.mouseMoveLoc - self.mousePressLoc)

                elif self.editModes.drawText and self.newText.isSelected():
                    self.newText.setPos(self.mouseMoveLoc - self.mousePressLoc)

                elif self.editModes.selectItem and modifiers == Qt.ShiftModifier:
                    self.selectionRectItem.setRect(
                        QRectF(self.mousePressLoc, self.mouseMoveLoc)
                    )
            else:
                if self.editModes.drawWire and self._newNet is not None:
                    self.mouseMoveLoc = self.findSnapPoint(
                        self.mouseMoveLoc, self.snapDistance, {self._newNet}
                    )
                    if self._snapPointRect is None:
                        rect = QRectF(QPointF(-5, -5), QPointF(5, 5))
                        self._snapPointRect = QGraphicsRectItem(rect)
                        self._snapPointRect.setPen(schlyr.draftPen)
                        self.addItem(self._snapPointRect)
                    self._snapPointRect.setPos(self.mouseMoveLoc)
                    self._newNet.draftLine = QLineF(
                        self.mouseReleaseLoc, self.mouseMoveLoc
                    )
                    if self._newNet.scene() is None:
                        self.addUndoStack(self._newNet)
            self.editorWindow.statusLine.showMessage(
                f"Cursor Position: {str((self.mouseMoveLoc - self.origin).toTuple())}"
            )
        except Exception as e:
            self.logger.error(f"mouse move error: {e}")

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        try:
            self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
            modifiers = QGuiApplication.keyboardModifiers()
            if mouse_event.button() == Qt.LeftButton:
                if self.editModes.addInstance:
                    self.editModes.addInstance = False

                elif self.editModes.drawWire and self._newNet is None:
                    self.editorWindow.messageLine.setText("Wire Mode")
                    self._newNet = net.schematicNet(
                        self.mouseReleaseLoc, self.mouseReleaseLoc
                    )
                    self._newNet.setSelected(True)
                elif self.editModes.drawText:
                    self.parent.parent.messageLine.setText("Note added.")
                    self.editModes.drawText = False
                    self.newText = None
                elif self.editModes.drawPin:
                    self.parent.parent.messageLine.setText("Pin added")
                    self.editModes.drawPin = False
                    self.newPin = None
                elif self.editModes.selectItem:
                    if modifiers == Qt.ShiftModifier:
                        self.selectInRectItems(
                            self.selectionRectItem.rect(), self.partialSelection
                        )
                        self.removeItem(self.selectionRectItem)
                        self.selectionRectItem = None
                    selectedNets = [
                        netItem
                        for netItem in self.selectedItems()
                        if isinstance(netItem, net.schematicNet)
                    ]
                    if selectedNets:
                        for netItem in selectedNets:
                            if netItem.scene():
                                self.mergeSplitNets(netItem)

        except Exception as e:
            self.logger.error(f"mouse release error: {e}")

    def checkNewNet(self, newNet):
        if newNet.draftLine.isNull():
            self.removeItem(newNet)
            self.undoStack.removeLastCommand()
        else:
            self.mergeSplitNets(newNet)

    def mergeSplitNets(self, inputNet: net.schematicNet):
        mergedNet = self.mergeNets(inputNet)
        mergedNet.clearDots()
        mergedNet.createDots()
        # first find the nets mergedNet can split.
        self.splitCrossingNet(mergedNet)
        overlapNets = list(mergedNet.findOverlapNets())
        if overlapNets:
            for netItem in overlapNets:
                self.splitCrossingNet(netItem)

    def mergeNets(self, inputNet):
        (origNet, mergedNet) = inputNet.mergeNets()
        if origNet.sceneShapeRect != mergedNet.sceneShapeRect:
            self.removeItem(origNet)
            self.addItem(mergedNet)
            return self.mergeNets(mergedNet)
        else:
            return origNet

    def splitCrossingNet(self, splittingNet):
        outputNets = set()
        crossingNetsDict = splittingNet.findCrossingNets(splittingNet.findOverlapNets())
        if crossingNetsDict:
            splitNetTuples = splittingNet.createSplitNets(crossingNetsDict)
            if splitNetTuples:  # mergedNet split some nets
                for netTuple in splitNetTuples:
                    self.addItem(netTuple.net)
                    netTuple.net.clearDots()
                    netTuple.net.createDots()
                    outputNets.add(netTuple.net)
        return outputNets

    def removeSnapRect(self):
        if self._snapPointRect:
            self.removeItem(self._snapPointRect)
            self._snapPointRect = None

    def findSnapPoint(self, eventLoc: QPoint, snapDistance: int, ignoredNetSet: set):
        # sourcery skip: simplify-len-comparison
        snapRect = QRect(
            eventLoc.x() - snapDistance,
            eventLoc.y() - snapDistance,
            2 * snapDistance,
            2 * snapDistance,
        )
        snapItems = {
            item
            for item in self.items(snapRect)
            if isinstance(item, (shp.symbolPin, net.schematicNet))
        }
        try:
            snapItems -= ignoredNetSet
            lengths = list()
            points = list()
            items = list()
            if len(snapItems) > 0:
                for item in snapItems:
                    if isinstance(item, shp.symbolPin):
                        items.append(item)
                        points.append(item.mapToScene(item.start))
                        lengths.append(
                            (item.mapToScene(item.start) - eventLoc).manhattanLength()
                        )
                    elif isinstance(item, net.schematicNet):
                        if snapRect.contains(item.draftLine.p1().toPoint()):
                            items.append(item)

                            points.append(item.draftLine.p1().toPoint())
                            lengths.append(
                                (
                                    item.mapToScene(item.draftLine.p1()) - eventLoc
                                ).manhattanLength()
                            )
                        elif snapRect.contains(item.draftLine.p2().toPoint()):
                            items.append(item)
                            points.append(item.draftLine.p2().toPoint())
                            # print(f'net end:{item.end}')
                            lengths.append(
                                (
                                    item.mapToScene(item.draftLine.p2()) - eventLoc
                                ).manhattanLength()
                            )
                if len(lengths) > 0:
                    indexClosestPoint = lengths.index(min(lengths))
                    eventLoc = points[indexClosestPoint]

            return eventLoc
        except Exception as e:
            self.logger.error(e)  # no items found
            return eventLoc

    def clearNetStatus(self, netsSet: set):
        """
        Clear all assigned net names
        """
        for netItem in netsSet:
            netItem.nameAdded = False
            netItem.nameConflict = False

    def groupAllNets(self) -> None:
        # sourcery skip: collection-builtin-to-comprehension, comprehension-to-generator
        """
        This method starting from nets connected to pins, then named nets and unnamed
        nets, groups all the nets in the schematic.
        """
        try:
            # all the nets in the schematic in a set to remove duplicates
            sceneNetsSet = self.findSceneNetsSet()
            self.clearNetStatus(sceneNetsSet)
            # first find nets connected to pins designating global nets.
            globalNetsSet = self.findGlobalNets()
            sceneNetsSet -= globalNetsSet  # remove these nets from all nets set.
            # now remove nets connected to global nets from this set.
            sceneNetsSet = self.groupNamedNets(globalNetsSet, sceneNetsSet)
            # now find nets connected to schematic pins
            schemPinConNetsSet = self.findSchPinNets()
            sceneNetsSet -= schemPinConNetsSet
            # use these nets as starting nets to find other nets connected to them
            sceneNetsSet = self.groupNamedNets(schemPinConNetsSet, sceneNetsSet)
            # now find the set of nets whose name is set by the user
            namedNetsSet = set([netItem for netItem in sceneNetsSet if netItem.nameSet])
            sceneNetsSet -= namedNetsSet
            # now remove already named net set from firstNetSet
            unnamedNets = self.groupNamedNets(namedNetsSet, sceneNetsSet)
            # now start netlisting from the unnamed nets
            self.groupUnnamedNets(unnamedNets, self.netCounter)
        except Exception as e:
            self.logger.error(e)

    def findGlobalNets(self) -> set:
        """
        This method finds all nets connected to global pins.
        """
        try:
            globalPinsSet = set()
            globalNetsSet = set()
            for symbolItem in self.findSceneSymbolSet():
                for pinName, pinItem in symbolItem.pins.items():
                    if pinName[-1] == "!":
                        globalPinsSet.add(pinItem)
            # self.logger.warning(f'global pins:{globalPinsSet}')
            for pinItem in globalPinsSet:
                pinNetSet = {
                    netItem
                    for netItem in self.items(pinItem.sceneBoundingRect())
                    if isinstance(netItem, net.schematicNet)
                }
                for netItem in pinNetSet:
                    if netItem.nameSet or netItem.nameAdded:
                        # check if net is already named explicitly
                        if netItem.name != pinItem.pinName:
                            netItem.nameConflict = True
                            self.logger.error(
                                f"Net name conflict at {pinItem.pinName} of "
                                f"{pinItem.parent.instanceName}."
                            )
                        else:
                            globalNetsSet.add(netItem)
                    else:
                        globalNetsSet.add(netItem)
                        netItem.name = pinItem.pinName
                        netItem.nameAdded = True
            return globalNetsSet
        except Exception as e:
            self.logger.error(e)

    def findSchPinNets(self):
        # nets connected to schematic pins.
        schemPinConNetsSet = set()
        # first start from schematic pins
        sceneSchemPinsSet = self.findSceneSchemPinsSet()
        for sceneSchemPin in sceneSchemPinsSet:
            pinNetSet = {
                netItem
                for netItem in self.items(sceneSchemPin.sceneBoundingRect())
                if isinstance(netItem, net.schematicNet)
            }
            for netItem in pinNetSet:
                if netItem.nameSet or netItem.nameAdded:  # check if net is named
                    if netItem.name == sceneSchemPin.pinName:
                        schemPinConNetsSet.add(netItem)
                    else:
                        netItem.nameConflict = True
                        self.parent.parent.logger.error(
                            f"Net name conflict at {sceneSchemPin.pinName} of "
                            f"{sceneSchemPin.parent().instanceName}."
                        )
                else:
                    schemPinConNetsSet.add(netItem)
                    netItem.name = sceneSchemPin.pinName
                    netItem.nameAdded = True
                netItem.update()
            schemPinConNetsSet.update(pinNetSet)
        return schemPinConNetsSet

    def groupNamedNets(self, namedNetsSet, unnamedNetsSet):
        """
        Groups nets with the same name using namedNetsSet members as seeds and going
        through connections. Returns the set of still unnamed nets.
        """
        for netItem in namedNetsSet:
            if self.schematicNets.get(netItem.name) is None:
                self.schematicNets[netItem.name] = set()
            connectedNets, unnamedNetsSet = self.traverseNets(
                {
                    netItem,
                },
                unnamedNetsSet,
            )
            self.schematicNets[netItem.name] |= connectedNets
        # These are the nets not connected to any named net
        return unnamedNetsSet

    def groupUnnamedNets(self, unnamedNetsSet: set[net.schematicNet], nameCounter: int):
        """
        Groups nets together if they are connected and assign them default names
        if they don't have a name assigned.
        """
        # select a net from the set and remove it from the set
        try:
            initialNet = (
                unnamedNetsSet.pop()
            )  # assign it a name, net0, net1, net2, etc.
        except KeyError:  # initialNet set is empty
            pass
        else:
            initialNet.name = "net" + str(nameCounter)
            # now go through the set and see if any of the
            # nets are connected to the initial net
            # remove them from the set and add them to the initial net's set
            self.schematicNets[initialNet.name], unnamedNetsSet = self.traverseNets(
                {
                    initialNet,
                },
                unnamedNetsSet,
            )
            nameCounter += 1
            if len(unnamedNetsSet) > 1:
                self.groupUnnamedNets(unnamedNetsSet, nameCounter)
            elif len(unnamedNetsSet) == 1:
                lastNet = unnamedNetsSet.pop()
                lastNet.name = "net" + str(nameCounter)
                self.schematicNets[lastNet.name] = {lastNet}

    def traverseNets(self, connectedSet, otherNetsSet):
        """
        Start from a net and traverse the schematic to find all connected nets. If the connected net search
        is exhausted, remove those nets from the scene nets set and start again in another net until all
        the nets in the scene are exhausted.
        """
        newFoundConnectedSet = set()
        for netItem in connectedSet:
            for netItem2 in otherNetsSet:
                if self.checkNetConnect(netItem, netItem2):
                    if (
                        (netItem2.nameSet or netItem2.nameAdded)
                        and (netItem.nameSet or netItem.nameAdded)
                        and (netItem.name != netItem2.name)
                    ):
                        self.editorWindow.messageLine.setText(
                            "Error: multiple names assigned to same net"
                        )
                        netItem2.nameConflict = True
                        netItem.nameConflict = True
                        break
                    else:
                        netItem2.name = netItem.name
                        netItem2.nameAdded = True
                    newFoundConnectedSet.add(netItem2)
        # keep searching if you already found a net connected to the initial net
        if len(newFoundConnectedSet) > 0:
            connectedSet.update(newFoundConnectedSet)
            otherNetsSet -= newFoundConnectedSet
            self.traverseNets(connectedSet, otherNetsSet)
        return connectedSet, otherNetsSet

    def checkPinNetConnect(self, pinItem: shp.schematicPin, netItem: net.schematicNet):
        """
        Determine if a pin is connected to a net.
        """
        return bool(pinItem.sceneBoundingRect().intersects(netItem.sceneBoundingRect()))

    def checkNetConnect(self, netItem, otherNetItem):
        """
        Determine if a net is connected to another one. One net should end on the other net.
        """

        if otherNetItem is not netItem:
            for netItemEnd, otherEnd in itt.product(
                netItem.sceneEndPoints, otherNetItem.sceneEndPoints
            ):
                # not a very elegant solution to mistakes in net end points.
                if (netItemEnd - otherEnd).manhattanLength() <= 1:
                    return True
        else:
            return False

    def generatePinNetMap(self, sceneSymbolSet: set):
        """
        For symbols in sceneSymbolSet, find which pin is connected to which net. If a
        pin is not connected, assign to it a default net starting with d prefix.
        """
        netCounter = 0
        for symbolItem in sceneSymbolSet:
            for pinName, pinItem in symbolItem.pins.items():
                pinItem.connected = False  # clear connections

                pinConnectedNets = [
                    netItem
                    for netItem in self.items(
                        pinItem.sceneBoundingRect().adjusted(-2, -2, 2, 2)
                    )
                    if isinstance(netItem, net.schematicNet)
                ]
                # this will name the pin by first net it finds in the bounding rectangle of
                # the pin. If there are multiple nets in the bounding rectangle, the first
                # net in the list will be the one used.
                if pinConnectedNets:
                    symbolItem.pinNetMap[pinName] = pinConnectedNets[0].name
                    pinItem.connected = True

                if not pinItem.connected:
                    # assign a default net name prefixed with d(efault).
                    symbolItem.pinNetMap[pinName] = f"dnet{netCounter}"
                    self.logger.warning(
                        f"left unconnected:{symbolItem.pinNetMap[pinName]}"
                    )
                    netCounter += 1
            # now reorder pinNetMap according pinOrder attribute
            if symbolItem.symattrs.get("pinOrder"):
                pinOrderList = list()
                [
                    pinOrderList.append(item.strip())
                    for item in symbolItem.symattrs.get("pinOrder").split(",")
                ]
                symbolItem.pinNetMap = {
                    pinName: symbolItem.pinNetMap[pinName] for pinName in pinOrderList
                }

    def findSceneCells(self, symbolSet):
        """
        This function just goes through set of symbol items in the scene and
        checks if that symbol's cell is encountered first time. If so, it adds
        it to a dictionary   cell_name:symbol
        """
        symbolGroupDict = dict()
        for symbolItem in symbolSet:
            if symbolItem.cellName not in symbolGroupDict.keys():
                symbolGroupDict[symbolItem.cellName] = symbolItem
        return symbolGroupDict

    def findSceneSymbolSet(self) -> set[shp.schematicSymbol]:
        """
        Find all the symbols on the scene as a set.
        """
        return {item for item in self.items() if isinstance(item, shp.schematicSymbol)}

    def findSceneNetsSet(self) -> set[net.schematicNet]:
        return {item for item in self.items() if isinstance(item, net.schematicNet)}

    def findRectSymbolPin(self, rect: Union[QRect, QRectF]) -> set[shp.symbolPin]:
        pinsRectSet = {
            item for item in self.items(rect) if isinstance(item, shp.symbolPin)
        }
        return pinsRectSet

    def findSceneSchemPinsSet(self) -> set[shp.schematicPin]:
        pinsSceneSet = {
            item for item in self.items() if isinstance(item, shp.schematicPin)
        }
        if pinsSceneSet:  # check pinsSceneSet is empty
            return pinsSceneSet
        else:
            return set()

    def findSceneTextSet(self) -> set[shp.text]:
        if textSceneSet := {
            item for item in self.items() if isinstance(item, shp.text)
        }:
            return textSceneSet
        else:
            return set()

    def addStretchWires(self, start: QPoint, end: QPoint) -> list[net.schematicNet]:
        """
        Add a trio of wires between two points
        """
        try:
            if (
                start.y() == end.y() or start.x() == end.x()
            ):  # horizontal or verticalline
                lines = [net.schematicNet(start, end)]
            else:
                firstPointX = self.snapToBase(
                    (end.x() - start.x()) / 3 + start.x(), self.snapTuple[0]
                )
                firstPointY = start.y()
                firstPoint = QPoint(firstPointX, firstPointY)
                secondPoint = QPoint(firstPointX, end.y())
                lines = list()
                if start != firstPoint:
                    lines.append(net.schematicNet(start, firstPoint))
                if firstPoint != secondPoint:
                    lines.append(net.schematicNet(firstPoint, secondPoint))
                if secondPoint != end:
                    lines.append(net.schematicNet(secondPoint, end))
            return lines
        except Exception as e:
            self.logger.error(f"extend wires error{e}")
            return []

    def addPin(self, pos: QPoint):
        try:
            pin = shp.schematicPin(pos, self.pinName, self.pinDir, self.pinType)
            self.addUndoStack(pin)
            return pin
        except Exception as e:
            self.logger.error(f"Pin add error: {e}")

    def addNote(self, pos: QPoint):
        """
        Changed the method name not to clash with qgraphicsscene addText method.
        """
        text = shp.text(
            pos,
            self.noteText,
            self.noteFontFamily,
            self.noteFontStyle,
            self.noteFontSize,
            self.noteAlign,
            self.noteOrient,
        )
        self.addUndoStack(text)
        return text

    def drawInstance(self, pos: QPoint):
        """
        Add an instance of a symbol to the scene.
        """
        instance = self.instSymbol(pos)

        self.itemCounter += 1
        self.addUndoStack(instance)
        self.instanceSymbolTuple = None
        return instance

    def instSymbol(self, pos: QPoint):
        itemShapes = []
        itemAttributes = {}
        try:
            with open(self.instanceSymbolTuple.viewItem.viewPath, "r") as temp:
                items = json.load(temp)
                if items[0]["cellView"] != "symbol":
                    self.logger.error("Not a symbol!")
                    return

                for item in items[2:]:
                    if item["type"] == "attr":
                        itemAttributes[item["nam"]] = item["def"]
                    else:
                        itemShapes.append(lj.symbolItems(self).create(item))

                symbolInstance = shp.schematicSymbol(itemShapes, itemAttributes)
                symbolInstance.setPos(pos)
                symbolInstance.counter = self.itemCounter
                symbolInstance.instanceName = f"I{symbolInstance.counter}"
                symbolInstance.libraryName = (
                    self.instanceSymbolTuple.libraryItem.libraryName
                )
                symbolInstance.cellName = self.instanceSymbolTuple.cellItem.cellName
                symbolInstance.viewName = self.instanceSymbolTuple.viewItem.viewName
                for item in symbolInstance.labels.values():
                    item.labelDefs()
                return symbolInstance
        except Exception as e:
            self.logger.warning(f"instantiation error: {e}")

    def copySelectedItems(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                selectedItemJson = json.dumps(item, cls=schenc.schematicEncoder)
                itemCopyDict = json.loads(selectedItemJson)
                shape = lj.schematicItems(self).create(itemCopyDict)
                if shape is not None:
                    self.addUndoStack(shape)
                    # shift position by four grid units to right and down
                    shape.setPos(
                        QPoint(
                            item.pos().x() + 4 * self.snapTuple[0],
                            item.pos().y() + 4 * self.snapTuple[1],
                        )
                    )
                    if isinstance(shape, shp.schematicSymbol):
                        self.itemCounter += 1
                        shape.instanceName = f"I{self.itemCounter}"
                        shape.counter = int(self.itemCounter)
                        [label.labelDefs() for label in shape.labels.values()]

    def saveSchematic(self, file: pathlib.Path):
        try:
            topLevelItems = [item for item in self.items() if item.parentItem() is None]
            # Insert a cellview item at the beginning of the list
            topLevelItems.insert(0, {"cellView": "schematic"})
            topLevelItems.insert(1, {"snapGrid": self.snapTuple})
            with file.open(mode="w") as f:
                json.dump(topLevelItems, f, cls=schenc.schematicEncoder, indent=4)
            # if there is a parent editor, to reload the changes.
            if self.editorWindow.parentEditor is not None:
                if isinstance(self.editorWindow.parentEditor, schematicEditor):
                    self.editorWindow.parentEditor.loadSchematic()
                elif isinstance(self.editorWindow.parentEditor, symbolEditor):
                    self.editorWindow.parentEditor.loadSymbol()
        except Exception as e:
            self.logger.error(e)

    def loadSchematicItems(self, itemsList: list[dict]) -> None:
        """
        load schematic from item list
        """
        snapGrid = itemsList[1].get("snapGrid")
        self.majorGrid = snapGrid[0]  # dot/line grid spacing
        self.snapGrid = snapGrid[1]  # snapping grid size
        self.snapTuple = (self.snapGrid, self.snapGrid)
        self.snapDistance = 2 * self.snapGrid
        shapesList = list()
        for item in itemsList[2:]:
            itemShape = lj.schematicItems(self).create(item)
            if (
                type(itemShape) == shp.schematicSymbol
                and itemShape.counter > self.itemCounter
            ):
                self.itemCounter = itemShape.counter
                # increment item counter for next symbol
                self.itemCounter += 1
            shapesList.append(itemShape)

        self.undoStack.push(us.loadShapesUndo(self, shapesList))
        print(f"snap tuple: {self.snapTuple}")

    def reloadScene(self):
        topLevelItems = [item for item in self.items() if item.parentItem() is None]
        # Insert a layout item at the beginning of the list
        topLevelItems.insert(0, {"cellView": "schematic"})
        topLevelItems.insert(1, {"snapGrid": self.snapTuple})
        items = json.loads(json.dumps(topLevelItems, cls=schenc.schematicEncoder))
        self.clear()
        self.loadSchematicItems(items)

    def viewObjProperties(self):
        """
        Display the properties of the selected object.
        """
        try:
            if self.selectedItems() is not None:
                for item in self.selectedItems():
                    item.prepareGeometryChange()
                    if isinstance(item, shp.schematicSymbol):
                        self.setInstanceProperties(item)

                    elif isinstance(item, net.schematicNet):
                        self.setNetProperties(item)

                    elif isinstance(item, shp.text):
                        item = self.setTextProperties(item)
                    elif isinstance(item, shp.schematicPin):
                        self.setSchematicPinProperties(item)
        except Exception as e:
            self.logger.error(e)

    def setInstanceProperties(self, item):
        dlg = pdlg.instanceProperties(self.editorWindow)
        dlg.libNameEdit.setText(item.libraryName)
        dlg.cellNameEdit.setText(item.cellName)
        dlg.viewNameEdit.setText(item.viewName)
        dlg.instNameEdit.setText(item.instanceName)
        location = (item.scenePos() - self.origin).toTuple()
        dlg.xLocationEdit.setText(str(location[0]))
        dlg.yLocationEdit.setText(str(location[1]))
        dlg.angleEdit.setText(str(item.angle))
        row_index = 0
        # iterate through the item labels.
        for label in item.labels.values():
            if label.labelDefinition not in lbl.symbolLabel.predefinedLabels:
                dlg.instanceLabelsLayout.addWidget(
                    edf.boldLabel(label.labelName, dlg), row_index, 0
                )
                labelValueEdit = edf.longLineEdit()
                labelValueEdit.setText(str(label.labelValue))
                dlg.instanceLabelsLayout.addWidget(labelValueEdit, row_index, 1)
                visibleCombo = QComboBox(dlg)
                visibleCombo.setInsertPolicy(QComboBox.NoInsert)
                visibleCombo.addItems(["True", "False"])
                if label.labelVisible:
                    visibleCombo.setCurrentIndex(0)
                else:
                    visibleCombo.setCurrentIndex(1)
                dlg.instanceLabelsLayout.addWidget(visibleCombo, row_index, 2)
                row_index += 1
        # now list instance attributes
        for counter, name in enumerate(item._symattrs.keys()):
            dlg.instanceAttributesLayout.addWidget(edf.boldLabel(name, dlg), counter, 0)
            labelType = edf.longLineEdit()
            labelType.setReadOnly(True)
            labelNameEdit = edf.longLineEdit()
            labelNameEdit.setText(item._symattrs.get(name))
            labelNameEdit.setToolTip(f"{name} attribute (Read Only)")
            dlg.instanceAttributesLayout.addWidget(labelNameEdit, counter, 1)
        if dlg.exec() == QDialog.Accepted:
            item.instanceName = dlg.instNameEdit.text().strip()
            item.angle = float(dlg.angleEdit.text().strip())

            location = QPoint(
                float(dlg.xLocationEdit.text().strip()),
                float(dlg.yLocationEdit.text().strip()),
            )
            item.setPos(self.snapToGrid(location - self.origin, self.snapTuple))
            tempDoc = QTextDocument()
            for i in range(dlg.instanceLabelsLayout.rowCount()):
                # first create label name document with HTML annotations
                tempDoc.setHtml(
                    dlg.instanceLabelsLayout.itemAtPosition(i, 0).widget().text()
                )
                # now strip html annotations
                tempLabelName = tempDoc.toPlainText().strip()
                # check if label name is in label dictionary of item.
                if item.labels.get(tempLabelName):
                    # this is where the label value is set.
                    item.labels[tempLabelName].labelValue = (
                        dlg.instanceLabelsLayout.itemAtPosition(i, 1).widget().text()
                    )
                    visible = (
                        dlg.instanceLabelsLayout.itemAtPosition(i, 2)
                        .widget()
                        .currentText()
                    )
                    if visible == "True":
                        item.labels[tempLabelName].labelVisible = True
                    else:
                        item.labels[tempLabelName].labelVisible = False
            [labelItem.labelDefs() for labelItem in item.labels.values()]

    def setNetProperties(self, item):
        dlg = pdlg.netProperties(self.editorWindow)
        dlg.netStartPointEditX.setText(
            str(round(item.mapToScene(item.draftLine.p1()).x()))
        )
        dlg.netStartPointEditY.setText(
            str(round(item.mapToScene(item.draftLine.p1()).y()))
        )
        dlg.netEndPointEditX.setText(
            str(round(item.mapToScene(item.draftLine.p2()).x()))
        )
        dlg.netEndPointEditY.setText(
            str(round(item.mapToScene(item.draftLine.p2()).y()))
        )
        if item.nameSet or item.nameAdded:
            dlg.netNameEdit.setText(item.name)
        if dlg.exec() == QDialog.Accepted:
            item.name = dlg.netNameEdit.text().strip()
            if item.name != "":
                item.nameSet = True

    def setTextProperties(self, item):
        dlg = pdlg.noteTextEditProperties(self.editorWindow, item)
        if dlg.exec() == QDialog.Accepted:
            # item.prepareGeometryChange()
            start = item.start
            self.removeItem(item)
            item = shp.text(
                start,
                dlg.plainTextEdit.toPlainText(),
                dlg.familyCB.currentText(),
                dlg.fontStyleCB.currentText(),
                dlg.fontsizeCB.currentText(),
                dlg.textAlignmCB.currentText(),
                dlg.textOrientCB.currentText(),
            )
            self.rotateAnItem(start, item, float(item.textOrient[1:]))
            self.addItem(item)
        return item

    def setSchematicPinProperties(self, item):
        dlg = pdlg.schematicPinPropertiesDialog(self.editorWindow, item)
        dlg.pinName.setText(item.pinName)
        dlg.pinDir.setCurrentText(item.pinDir)
        dlg.pinType.setCurrentText(item.pinType)
        dlg.angleEdit.setText(str(item.angle))
        dlg.xlocationEdit.setText(str(item.mapToScene(item.start).x()))
        dlg.ylocationEdit.setText(str(item.mapToScene(item.start).y()))
        if dlg.exec() == QDialog.Accepted:
            item.pinName = dlg.pinName.text().strip()
            item.pinDir = dlg.pinDir.currentText()
            item.pinType = dlg.pinType.currentText()
            itemStartPos = QPoint(
                int(float(dlg.xlocationEdit.text().strip())),
                int(float(dlg.ylocationEdit.text().strip())),
            )
            item.start = self.snapToGrid(itemStartPos - self.origin, self.snapTuple)
            item.angle = float(dlg.angleEdit.text().strip())

    def netNameEdit(self):
        """
        Edit the name of the selected net.
        """
        try:
            if self.selectedItems() is not None:
                for item in self.selectedItems():
                    if isinstance(item, net.schematicNet):
                        dlg = pdlg.netProperties(self.editorWindow, item)
                        if dlg.exec() == QDialog.Accepted:
                            item.name = dlg.netNameEdit.text().strip()
                            if item.name != "":
                                item.nameSet = True
                            item.update()
        except Exception as e:
            self.logger.error(e)

    def hilightNets(self):
        """
        Show the connections the selected items.
        """
        try:
            self.highlightNets = bool(self.editorWindow.hilightNetAction.isChecked())
        except Exception as e:
            self.logger.error(e)

    def createSymbol(self):
        """
        Create a symbol view for a schematic.
        """
        oldSymbolItem = False

        askViewNameDlg = pdlg.symbolNameDialog(
            self.editorWindow.file.parent,
            self.editorWindow.cellName,
            self.editorWindow,
        )
        if askViewNameDlg.exec() == QDialog.Accepted:
            symbolViewName = askViewNameDlg.symbolViewsCB.currentText()
            if symbolViewName in askViewNameDlg.symbolViewNames:
                oldSymbolItem = True
            if oldSymbolItem:
                deleteSymViewDlg = fd.deleteSymbolDialog(
                    self.editorWindow.cellName, symbolViewName, self.editorWindow
                )
                if deleteSymViewDlg.exec() == QDialog.Accepted:
                    self.createSymbolViewItem(symbolViewName)
            else:
                self.createSymbolViewItem(symbolViewName)

    def createSymbolViewItem(self, symbolViewName: str):
        self.generateSymbol(symbolViewName)
        self.editorWindow.libraryView.reworkDesignLibrariesView(
            self.editorWindow.appMainW.libraryDict
        )
        viewItem = libm.getViewItem(self.editorWindow.cellItem, symbolViewName)
        self.editorWindow.libraryView.libBrowsW.openCellView(
            viewItem, self.editorWindow.cellItem, self.editorWindow.libItem
        )

    def generateSymbol(self, symbolViewName: str):
        libName = self.editorWindow.libName
        cellName = self.editorWindow.cellName
        libItem = libm.getLibItem(self.editorWindow.libraryView.libraryModel, libName)
        cellItem = libm.getCellItem(libItem, cellName)
        libraryView = self.editorWindow.libraryView
        schematicPins = list(self.findSceneSchemPinsSet())

        schematicPinNames = [pinItem.pinName for pinItem in schematicPins]

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

        dlg = pdlg.symbolCreateDialog(self.parent.parent)
        dlg.leftPinsEdit.setText(", ".join(inputPins))
        dlg.rightPinsEdit.setText(", ".join(outputPins))
        dlg.topPinsEdit.setText(", ".join(inoutPins))
        if dlg.exec() == QDialog.Accepted:
            symbolViewItem = scb.createCellView(
                self.editorWindow, symbolViewName, cellItem
            )
            libraryDict = self.editorWindow.libraryDict
            # create symbol editor window with an empty items list
            symbolWindow = symbolEditor(symbolViewItem, libraryDict, libraryView)
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
        libraryView.openViews[f"{libName}_{cellName}_{symbolViewName}"] = symbolWindow
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
            QPoint(-stubLength, (i + 1) * pinDistance) for i in range(len(leftPinNames))
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
            QPoint((i + 1) * pinDistance, -stubLength) for i in range(len(topPinNames))
        ]
        for i in range(len(leftPinNames)):
            symbolScene.lineDraw(leftPinLocs[i], leftPinLocs[i] + QPoint(stubLength, 0))
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
                schematicPins[schematicPinNames.index(rightPinNames[i])].toSymbolPin(
                    rightPinLocs[i]
                )
            )
        for i in range(len(topPinNames)):
            symbolScene.lineDraw(topPinLocs[i], topPinLocs[i] + QPoint(0, stubLength))
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
                schematicPins[schematicPinNames.index(bottomPinNames[i])].toSymbolPin(
                    bottomPinLocs[i]
                )
            )  # symbol attribute generation for netlisting.
        symbolScene.attributeList = list()  # empty attribute list

        symbolScene.attributeList.append(
            symenc.symbolAttribute(
                "XyceSymbolNetlistLine", "X[@instName] [@cellName] [@pinList]"
            )
        )
        symbolScene.attributeList.append(
            symenc.symbolAttribute("pinOrder", ", ".join(schematicPinNames))
        )

        symbolWindow.checkSaveCell()
        libraryView.reworkDesignLibrariesView(self.appMainW.libraryDict)
        # symbolWindow.show()

    def goDownHier(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                if isinstance(item, shp.schematicSymbol):
                    dlg = fd.goDownHierDialogue(self.editorWindow)
                    libItem = libm.getLibItem(
                        self.editorWindow.libraryView.libraryModel, item.libraryName
                    )
                    cellItem = libm.getCellItem(libItem, item.cellName)
                    viewNames = [
                        cellItem.child(i).text()
                        for i in range(cellItem.rowCount())
                        # if cellItem.child(i).text() != item.viewName
                        if "schematic" in cellItem.child(i).text()
                        or "symbol" in cellItem.child(i).text()
                    ]
                    dlg.viewListCB.addItems(viewNames)
                    if dlg.exec() == QDialog.Accepted:
                        libItem = libm.getLibItem(
                            self.editorWindow.libraryView.libraryModel, item.libraryName
                        )
                        cellItem = libm.getCellItem(libItem, item.cellName)
                        viewItem = libm.getViewItem(
                            cellItem, dlg.viewListCB.currentText()
                        )
                        openViewTuple = (
                            self.editorWindow.libraryView.libBrowsW.openCellView(
                                viewItem, cellItem, libItem
                            )
                        )
                        if self.editorWindow.appMainW.openViews[openViewTuple]:
                            childWindow = self.editorWindow.appMainW.openViews[
                                openViewTuple
                            ]
                            childWindow.parentEditor = self.editorWindow
                            childWindow.symbolToolbar.addAction(childWindow.goUpAction)
                            if dlg.buttonId == 2:
                                childWindow.centralW.scene.readOnly = True

    def ignoreSymbol(self):
        if self.selectedItems() is not None:
            for item in self.selectedItems():
                if isinstance(item, shp.schematicSymbol):
                    item.netlistIgnore = not item.netlistIgnore
        else:
            self.logger.warning("No symbol selected")

    def moveBySelectedItems(self):
        if self.selectedItems():
            dlg = pdlg.moveByDialogue(self.editorWindow)
            dlg.xEdit.setText("0")
            dlg.yEdit.setText("0")
            if dlg.exec() == QDialog.Accepted:
                for item in self.selectedItems():
                    item.moveBy(
                        self.snapToBase(float(dlg.xEdit.text()), self.snapTuple[0]),
                        self.snapToBase(float(dlg.yEdit.text()), self.snapTuple[1]),
                    )
                self.editorWindow.messageLine.setText(
                    f"Moved items by {dlg.xEdit.text()} and {dlg.yEdit.text()}"
                )
                self.editModes.setMode("selectItem")


class layout_scene(editor_scene):
    def __init__(self, parent):
        super().__init__(parent)
        self.selectEdLayer = laylyr.pdkDrawingLayers[0]
        self.layoutShapes = [
            "Inst",
            "Rect",
            "Path",
            "Label",
            "Via",
            "Pin",
            "Polygon",
            "Pcell",
            "Ruler",
        ]
        # draw modes
        self.editModes = ddef.layoutModes(
            selectItem=False,
            deleteItem=False,
            moveItem=False,
            copyItem=False,
            rotateItem=False,
            changeOrigin=False,
            panView=False,
            drawPath=False,
            drawPin=False,
            drawArc=False,
            drawPolygon=False,
            addLabel=False,
            addVia=False,
            drawRect=False,
            drawLine=False,
            drawCircle=False,
            drawRuler=False,
            stretchItem=False,
            addInstance=False,
        )
        self.editModes.setMode("selectItem")
        self.newInstance = None
        self.layoutInstanceTuple = None

        self.itemCounter = 0
        self._newPath = None
        self.newPathTuple = None
        self.draftLine = None
        self.m45Rotate = QTransform()
        self.m45Rotate.rotate(-45)
        self.newPin = None
        self.newPinTuple = None
        self.newLabelTuple = None
        self.newLabel = None
        self._newPolygon = None
        self.arrayViaTuple = None
        self.singleVia = None
        self._arrayVia = None
        self._polygonGuideLine = None
        self._newRuler = None
        self.rulersSet = set()
        # this needs move to configuration file...
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamily = [
            family for family in fontFamilies if QFontDatabase.isFixedPitch(family)
        ][0]
        fontStyle = QFontDatabase.styles(fixedFamily)[0]
        self.rulerFont = QFont(fixedFamily)
        self.rulerFont.setStyleName(fontStyle)
        fontSize = [size for size in QFontDatabase.pointSizes(fixedFamily, fontStyle)][
            1
        ]
        self.rulerFont.setPointSize(fontSize)
        self.rulerFont.setKerning(False)
        self.rulerTickGap = fabproc.dbu
        self.rulerTickLength = int(fabproc.dbu / 10)
        self.rulerWidth = 2

    @property
    def drawMode(self):
        return any(
            (
                self.editModes.drawPath,
                self.editModes.drawPin,
                self.editModes.drawArc,
                self.editModes.drawPolygon,
                self.editModes.drawRect,
                self.editModes.drawCircle,
                self.editModes.drawRuler,
            )
        )

    # Order of drawing
    # 1. Rect
    # 2. Path
    # 3. Pin
    # 4. Label
    # 5. Via/Contact
    # 6. Polygon
    # 7. Add instance
    # 8. select item/s
    # 9. rotate item/s
    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        """
        Handle the mouse press event.

        Args:
            mouse_event: The mouse event object.

        Returns:
            None
        """
        # Store the mouse press location
        self.mousePressLoc = mouse_event.scenePos().toPoint()
        # Call the base class mouse press event
        super().mousePressEvent(mouse_event)
        try:
            # Get the keyboard modifiers
            modifiers = QGuiApplication.keyboardModifiers()

            # Get the bounding rectangle of the view
            self.viewRect = self.parent.view.mapToScene(
                self.parent.view.viewport().rect()
            ).boundingRect()

            if mouse_event.button() == Qt.LeftButton:
                if self.editModes.drawPath and self._newPath is not None:
                    if self._newPath.draftLine.isNull():
                        self.removeItem(self._newPath)
                        self.undoStack.removeLastCommand()
                    else:
                        self._newPath = None
                elif self.editModes.drawRect and self._newRect is not None:
                    self._newRect.end = self.mousePressLoc
                    self._newRect.setSelected(False)
                    self._newRect = None

                elif self.editModes.drawRuler:
                    if self._newRuler is None:
                        self._newRuler = lshp.layoutRuler(
                            QLineF(self.mousePressLoc, self.mousePressLoc),
                            width=self.rulerWidth,
                            tickGap=self.rulerTickGap,
                            tickLength=self.rulerTickLength,
                            tickFont=self.rulerFont,
                        )
                        self.addUndoStack(self._newRuler)
                    else:
                        self._newRuler = None

                elif self.editModes.drawPin and self.newLabel is None:
                    # Create a new pin
                    self.newPin = lshp.layoutPin(
                        self.mousePressLoc,
                        self.mousePressLoc,
                        *self.newPinTuple,
                    )
                    self.addUndoStack(self.newPin)
                elif self.editModes.addLabel and self.newLabel is not None:
                    self.newLabelTuple = None
                    self.newLabel = None
                    self.editModes.setMode("selectItem")
                elif self.editModes.addVia and self._arrayVia is not None:
                    self.arrayViaTuple = None
                    self._arrayVia = None
                    self.editModes.setMode("selectItem")

                elif self.editModes.selectItem:
                    # Select scene items
                    self.selectSceneItems(modifiers)
                elif self.editModes.rotateItem:
                    self.editorWindow.messageLine.setText("Rotate item")
                    if self.selectedItems():
                        # Rotate selected items
                        self.rotateSelectedItems(self.mousePressLoc)
                elif self.editModes.changeOrigin:
                    self.origin = self.mousePressLoc
                    self.editModes.setMode("selectItem")
        except Exception as e:
            self.logger.error(f"mouse press error: {e}")

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        """
        Handle the mouse move event.

        Args:
            mouse_event (QGraphicsSceneMouseEvent): The mouse event object.

        Returns:
            None
        """

        # Get the current mouse position
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        # Call the parent class's mouseMoveEvent method
        super().mouseMoveEvent(mouse_event)
        # Get the keyboard modifiers
        modifiers = QGuiApplication.keyboardModifiers()
        if mouse_event.buttons() == Qt.LeftButton:
            # Handle drawing rectangle mode

            # Handle drawing pin mode
            if self.editModes.drawPin and self.newPin is not None:
                self.newPin.end = self.mouseMoveLoc
            # Handle selecting item mode with shift modifier
            elif self.editModes.selectItem and modifiers == Qt.ShiftModifier:
                self.selectionRectItem.setRect(
                    QRectF(self.mousePressLoc, self.mouseMoveLoc)
                )
        else:
            if self.editModes.drawRect:
                if self._newRect.scene() is None:
                    self.addUndoStack(self._newRect)
                self._newRect.end = self.mouseMoveLoc
            # Handle drawing pin mode with no new pin
            elif self.editModes.drawPin and self.newPin is None:
                if self.newLabel is not None:
                    self.newLabel.start = self.mouseMoveLoc
            # Handle drawing path mode
            elif self.editModes.drawPath and self._newPath is not None:
                self._newPath.draftLine = QLineF(
                    self._newPath.draftLine.p1(), self.mouseMoveLoc
                )
                if self._newPath.scene() is None:
                    self.addUndoStack(self._newPath)
            elif self.editModes.drawRuler and self._newRuler is not None:
                self._newRuler.draftLine = QLineF(
                    self._newRuler.draftLine.p1(), self.mouseMoveLoc
                )
            # Handle adding label mode
            elif self.editModes.addLabel:
                if self.newLabel is not None:  # already defined a new label
                    self.newLabel.start = self.mouseMoveLoc
                # there is no new label but there is a new label tuple defined
                elif self.newLabelTuple is not None:
                    self.newLabel = lshp.layoutLabel(
                        self.mouseMoveLoc, *self.newLabelTuple
                    )
                    self.addUndoStack(self.newLabel)
            # Handle adding via mode with array via tuple
            elif self.editModes.addVia and self.arrayViaTuple is not None:
                if self._arrayVia is None:
                    singleVia = lshp.layoutVia(
                        QPoint(0, 0),
                        *self.arrayViaTuple.singleViaTuple,
                    )
                    self._arrayVia = lshp.layoutViaArray(
                        self.mouseMoveLoc,
                        singleVia,
                        self.arrayViaTuple.spacing,
                        self.arrayViaTuple.xnum,
                        self.arrayViaTuple.ynum,
                    )
                    self.addUndoStack(self._arrayVia)
                else:
                    self._arrayVia.setPos(self.mouseMoveLoc - self._arrayVia.start)
                    self._arrayVia.setSelected(True)
            # Handle drawing polygon mode
            elif self.editModes.drawPolygon and self._newPolygon is not None:
                self._polygonGuideLine.setLine(
                    QLineF(self._newPolygon.points[-1], self.mouseMoveLoc)
                )
            # Handle adding instance mode with layout instance tuple
            elif self.editModes.addInstance and self.layoutInstanceTuple is not None:
                if self.newInstance is None:
                    self.newInstance = self.instLayout()
                    # if new instance is a pcell, start a dialogue for pcell parameters
                    if isinstance(self.newInstance, lshp.layoutPcell):
                        dlg = ldlg.pcellInstanceDialog(self.editorWindow)
                        dlg.pcellLibName.setText(self.newInstance.libraryName)
                        dlg.pcellCellName.setText(self.newInstance.cellName)
                        dlg.pcellViewName.setText(self.newInstance.viewName)
                        initArgs = inspect.signature(
                            self.newInstance.__class__.__init__
                        ).parameters
                        argsUsed = [param for param in initArgs if (param != "self")]
                        argDict = {
                            arg: getattr(self.newInstance, arg) for arg in argsUsed
                        }
                        lineEditDict = {
                            key: edf.shortLineEdit(value)
                            for key, value in argDict.items()
                        }
                        for key, value in lineEditDict.items():
                            dlg.instanceParamsLayout.addRow(key, value)
                        if dlg.exec() == QDialog.Accepted:
                            instanceValuesDict = {}
                            for key, value in lineEditDict.items():
                                instanceValuesDict[key] = value.text()
                            self.newInstance(*instanceValuesDict.values())
                    self.addUndoStack(self.newInstance)
                self.newInstance.setPos(self.mouseMoveLoc - self.newInstance.start)

        # Calculate the cursor position in real units
        cursorPositionX = (self.mouseMoveLoc - self.origin).x() / fabproc.dbu
        cursorPositionY = (self.mouseMoveLoc - self.origin).y() / fabproc.dbu

        # Show the cursor position in the status line
        self.statusLine.showMessage(
            f"Cursor Position: ({cursorPositionX}, {cursorPositionY})"
        )

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
        modifiers = QGuiApplication.keyboardModifiers()
        try:
            if mouse_event.button() == Qt.LeftButton:
                if self.editModes.drawPath:
                    self.editorWindow.messageLine.setText("Wire mode")
                    # Create a new path
                    self._newPath = lshp.layoutPath(
                        QLineF(self.mouseReleaseLoc, self.mouseReleaseLoc),
                        self.newPathTuple.layer,
                        self.newPathTuple.width,
                        self.newPathTuple.startExtend,
                        self.newPathTuple.endExtend,
                        self.newPathTuple.mode,
                    )
                    self._newPath.name = self.newPathTuple.name
                    self._newPath.setSelected(True)
                elif self.editModes.drawRect:
                    self.editorWindow.messageLine.setText("Rectangle mode.")
                    # Create a new rectangle
                    self._newRect = lshp.layoutRect(
                        self.mouseReleaseLoc,
                        self.mouseReleaseLoc,
                        self.selectEdLayer,
                    )

                elif (
                    self.editModes.drawPin
                ):  # finish pin editing and start label editing
                    if self.newPin is not None and self.newLabel is None:
                        self.newLabel = lshp.layoutLabel(
                            self.mouseReleaseLoc,
                            *self.newLabelTuple,
                        )
                        self.addUndoStack(self.newLabel)
                        self.newPin.label = self.newLabel
                        self.newPin = None
                    elif self.newPin is None and self.newLabel is not None:
                        # finish label editing
                        self.newLabel = None

                elif self.editModes.drawPolygon:
                    if self._newPolygon is None:
                        # Create a new polygon
                        self._newPolygon = lshp.layoutPolygon(
                            [self.mouseReleaseLoc, self.mouseReleaseLoc],
                            self.selectEdLayer,
                        )
                        self.addUndoStack(self._newPolygon)
                        # Create a guide line for the polygon
                        self._polygonGuideLine = QGraphicsLineItem(
                            QLineF(
                                self._newPolygon.points[-2], self._newPolygon.points[-1]
                            )
                        )
                        self._polygonGuideLine.setPen(
                            QPen(QColor(255, 255, 0), 1, Qt.DashLine)
                        )
                        self.addUndoStack(self._polygonGuideLine)

                    else:
                        self._newPolygon.addPoint(self.mouseReleaseLoc)
                elif self.editModes.addInstance and self.newInstance is not None:
                    self.newInstance = None
                    self.layoutInstanceTuple = None
                    self.editModes.setMode("selectItem")
                elif self.editModes.selectItem and modifiers == Qt.ShiftModifier:
                    self.selectInRectItems(
                        self.selectionRectItem.rect(), self.partialSelection
                    )
                    self.removeItem(self.selectionRectItem)
                    self.selectionRectItem = None

        except Exception as e:
            self.logger.error(f"mouse release error: {e}")

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseDoubleClickEvent(event)
        self.mouseDoubleClickLoc = event.scenePos().toPoint()
        try:
            if event.button() == Qt.LeftButton:
                if self.editModes.drawPolygon:
                    self._newPolygon.polygon.remove(0)
                    self._newPolygon.points.pop(0)
                    self.editModes.setMode("selectItem")
                    self._newPolygon = None
                    self.removeItem(self._polygonGuideLine)
                    self._polygonGuideLine = None

        except Exception as e:
            self.logger.error(f"mouse double click error: {e}")

    def drawInstance(self, pos: QPoint):
        """
        Add an instance of a symbol to the scene.
        """
        try:
            instance = self.instLayout()
            self.itemCounter += 1
            undoCommand = us.addShapeUndo(self, instance)
            self.undoStack.push(undoCommand)
            return instance
        except Exception as e:
            self.logger.error(f"Cannot draw instance: {e}")

    def instLayout(self):
        """
        Read a layout file and create layoutShape objects from it.
        """
        match self.layoutInstanceTuple.viewItem.viewType:
            case "layout":
                with self.layoutInstanceTuple.viewItem.viewPath.open("r") as temp:
                    try:
                        decodedData = json.load(temp)
                        if decodedData[0]["cellView"] != "layout":
                            self.logger.error("Not a layout cell")
                        else:
                            instanceShapes = [
                                lj.layoutItems(self).create(decodedData)
                                for item in decodedData[2:]
                                if item.get("type") in self.layoutShapes
                            ]
                            layoutInstance = lshp.layoutInstance(instanceShapes)
                            layoutInstance.libraryName = (
                                self.layoutInstanceTuple.libraryItem.libraryName
                            )
                            layoutInstance.cellName = (
                                self.layoutInstanceTuple.cellItem.cellName
                            )
                            layoutInstance.viewName = (
                                self.layoutInstanceTuple.viewItem.viewName
                            )
                            self.itemCounter += 1
                            layoutInstance.counter = self.itemCounter
                            layoutInstance.instanceName = f"I{layoutInstance.counter}"
                            # For each instance assign a counter number from the scene
                            return layoutInstance
                    except json.JSONDecodeError:
                        # print("Invalid JSON file")
                        self.logger.warning("Invalid JSON File")
            case "pcell":
                with open(self.layoutInstanceTuple.viewItem.viewPath, "r") as temp:
                    try:
                        pcellRefDict = json.load(temp)
                        if pcellRefDict[0]["cellView"] != "pcell":
                            self.logger.error("Not a pcell cell")
                        else:
                            # create a pcell instance with default parameters.
                            pcellInstance = eval(
                                f"pcells.{pcellRefDict[1]['reference']}()"
                            )
                            # now evaluate pcell

                            pcellInstance.libraryName = (
                                self.layoutInstanceTuple.libraryItem.libraryName
                            )
                            pcellInstance.cellName = (
                                self.layoutInstanceTuple.cellItem.cellName
                            )
                            pcellInstance.viewName = (
                                self.layoutInstanceTuple.viewItem.viewName
                            )
                            self.itemCounter += 1
                            pcellInstance.counter = self.itemCounter
                            # This needs to become more sophisticated.
                            pcellInstance.instanceName = f"I{pcellInstance.counter}"

                            return pcellInstance
                    except Exception as e:
                        self.logger.error(f"Cannot read pcell: {e}")

    def findScenelayoutCellSet(self) -> set[lshp.layoutInstance]:
        """
        Find all the symbols on the scene as a set.
        """
        return {item for item in self.items() if isinstance(item, lshp.layoutInstance)}

    def saveLayoutCell(self, filePathObj: pathlib.Path) -> None:
        """
        Save the layout cell items to a file.

        Args:
            fileName (pathlib.Path): filepath object for layout file.

        Returns:
            None
        """
        try:
            # Only save the top-level items

            topLevelItems = [item for item in self.items() if item.parentItem() is None]
            topLevelItems.insert(0, {"cellView": "layout"})
            topLevelItems.insert(1, {"snapGrid": self.snapTuple})
            with filePathObj.open("w") as file:
                # Serialize items to JSON using layoutEncoder class
                json.dump(topLevelItems, file, cls=layenc.layoutEncoder, indent=4)
        except Exception as e:
            self.logger.error(f"Cannot save layout: {e}")

    def loadLayoutCell(self, filePathObj: pathlib.Path) -> None:
        """
        Load the layout cell from the given file path.

        Args:
            filePathObj (pathlib.Path): The file path object.

        Returns:
            None
        """
        try:
            with filePathObj.open("r") as file:
                decodedData = json.load(file)
            snapGrid = decodedData[1].get("snapGrid")
            self.majorGrid = snapGrid[0]  # dot/line grid spacing
            self.snapGrid = snapGrid[1]  # snapping grid size
            self.snapTuple = (self.snapGrid, self.snapGrid)
            self.snapDistance = 2 * self.snapGrid
            self.createLayoutItems(decodedData[2:])
        except Exception as e:
            self.logger.error(f"Cannot load layout: {e}")

    def createLayoutItems(self, decodedData):
        if decodedData:
            loadedLayoutItems = [
                lj.layoutItems(self).create(item)
                for item in decodedData
                if item.get("type") in self.layoutShapes
            ]
            # A hack to get loading working. Otherwise, when it is saved the top-level items
            # get destroyed.
            undoCommand = us.loadShapesUndo(self, loadedLayoutItems)
            self.undoStack.push(undoCommand)

    def reloadScene(self):
        # Get the top level items from the scene
        topLevelItems = [item for item in self.items() if item.parentItem() is None]
        # Insert a layout item at the beginning of the list
        topLevelItems.insert(0, {"cellView": "layout"})
        # Convert the top level items to JSON string
        # Decode the JSON string back to Python objects
        decodedData = json.loads(json.dumps(topLevelItems, cls=layenc.layoutEncoder))
        # Clear the current scene
        self.clear()
        # Create layout items based on the decoded data
        self.createLayoutItems(decodedData)

    def deleteSelectedItems(self):
        for item in self.selectedItems():
            # if pin is to be deleted, the associated label should be also deleted.
            if isinstance(item, lshp.layoutPin) and item.label is not None:
                undoCommand = us.deleteShapeUndo(self, item.label)
                self.undoStack.push(undoCommand)
        super().deleteSelectedItems()

    def viewObjProperties(self):
        """
        Display the properties of the selected object.
        """
        try:
            if self.selectedItems() is not None:
                for item in self.selectedItems():
                    match type(item):
                        case lshp.layoutRect:
                            self.layoutRectProperties(item)
                        case lshp.layoutPin:
                            self.layoutPinProperties(item)
                        case lshp.layoutLabel:
                            self.layoutLabelProperties(item)
                        case lshp.layoutPath:
                            self.layoutPathProperties(item)
                        case lshp.layoutViaArray:
                            self.layoutViaProperties(item)
                        case lshp.layoutPolygon:
                            self.layoutPolygonProperties(item)
                        case lshp.layoutInstance:
                            self.layoutInstanceProperties(item)
                        case _:
                            if item.__class__.__bases__[0] == lshp.layoutPcell:
                                self.layoutPCellProperties(item)

        except Exception as e:
            self.logger.error(f"{type(item)} property editor error: {e}")

    def layoutPolygonProperties(self, item):
        dlg = ldlg.layoutPolygonProperties(self.editorWindow, len(item.points))
        dlg.polygonLayerCB.addItems(
            [f"{item.name} [{item.purpose}]" for item in laylyr.pdkAllLayers]
        )
        dlg.polygonLayerCB.setCurrentText(
            f"{item.layer.name} [" f"{item.layer.purpose}]"
        )
        for i, point in enumerate(item.points):
            dlg.pointXEdits[i].setText(str(point.x() / fabproc.dbu))
            dlg.pointYEdits[i].setText(str(point.y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.layer = laylyr.pdkAllLayers[dlg.polygonLayerCB.currentIndex()]
            tempPoints = []
            for i in range(dlg.polygonGroupLayout.rowCount() - 2):
                xedit = dlg.polygonGroupLayout.itemAtPosition(i + 2, 1).widget().text()
                yedit = dlg.polygonGroupLayout.itemAtPosition(i + 2, 2).widget().text()
                if xedit != "" and yedit != "":
                    tempPoints.append(
                        QPointF(float(xedit) * fabproc.dbu, float(yedit) * fabproc.dbu)
                    )
            item.points = tempPoints

    def layoutRectProperties(self, item):
        dlg = ldlg.layoutRectProperties(self.editorWindow)
        dlg.rectLayerCB.addItems(
            [f"{item.name} [{item.purpose}]" for item in laylyr.pdkAllLayers]
        )
        dlg.rectLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.rectWidthEdit.setText(str(item.width / fabproc.dbu))
        dlg.rectHeightEdit.setText(str(item.height / fabproc.dbu))
        dlg.topLeftEditX.setText(str(item.rect.topLeft().x() / fabproc.dbu))
        dlg.topLeftEditY.setText(str(item.rect.topLeft().y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.layer = laylyr.pdkAllLayers[dlg.rectLayerCB.currentIndex()]
            item.width = float(dlg.rectWidthEdit.text()) * fabproc.dbu
            item.height = float(dlg.rectHeightEdit.text()) * fabproc.dbu

            item.rect = QRectF(
                float(dlg.topLeftEditX.text()) * fabproc.dbu,
                float(dlg.topLeftEditY.text()) * fabproc.dbu,
                float(dlg.rectWidthEdit.text()) * fabproc.dbu,
                float(dlg.rectHeightEdit.text()) * fabproc.dbu,
            )

    def layoutViaProperties(self, item):
        dlg = ldlg.layoutViaProperties(self.editorWindow)
        if item.xnum == 1 and item.ynum == 1:
            dlg.singleViaRB.setChecked(True)
            dlg.singleViaClicked()
            dlg.singleViaNamesCB.setCurrentText(item.via.viaDefTuple.name)
            dlg.singleViaWidthEdit.setText(str(item.width / fabproc.dbu))
            dlg.singleViaHeightEdit.setText(str(item.via.height / fabproc.dbu))
        else:
            dlg.arrayViaRB.setChecked(True)
            dlg.arrayViaClicked()
            dlg.arrayViaNamesCB.setCurrentText(item.via.viaDefTuple.name)
            dlg.arrayViaWidthEdit.setText(str(item.via.width / fabproc.dbu))
            dlg.arrayViaHeightEdit.setText(str(item.via.height / fabproc.dbu))
            dlg.arrayViaSpacingEdit.setText(str(item.spacing / fabproc.dbu))
            dlg.arrayXNumEdit.setText(str(item.xnum))
            dlg.arrayYNumEdit.setText(str(item.ynum))
        dlg.startXEdit.setText(str(item.mapToScene(item.start).x() / fabproc.dbu))
        dlg.startYEdit.setText(str(item.mapToScene(item.start).y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            if dlg.singleViaRB.isChecked():
                item.viaDefTuple = [
                    viaDefT
                    for viaDefT in fabproc.processVias
                    if viaDefT.name == dlg.singleViaNamesCB.currentText()
                ][0]
                item.width = float(dlg.singleViaWidthEdit.text()) * fabproc.dbu
                item.height = float(dlg.singleViaHeightEdit.text()) * fabproc.dbu
                item.start = item.mapFromScene(
                    QPointF(
                        float(dlg.startXEdit.text()) * fabproc.dbu,
                        float(dlg.startYEdit.text()) * fabproc.dbu,
                    )
                )
                item.xnum = 1
                item.ynum = 1
                item.spacing = 0.0
            else:
                item.viaDefTuple = [
                    viaDefT
                    for viaDefT in fabproc.processVias
                    if viaDefT.name == dlg.arrayViaNamesCB.currentText()
                ][0]
                item.width = float(dlg.arrayViaWidthEdit.text()) * fabproc.dbu
                item.height = float(dlg.arrayViaHeightEdit.text()) * fabproc.dbu
                item.start = item.mapFromScene(
                    QPointF(
                        float(dlg.startXEdit.text()) * fabproc.dbu,
                        float(dlg.startYEdit.text()) * fabproc.dbu,
                    )
                )
                item.xnum = int(dlg.arrayXNumEdit.text())
                item.ynum = int(dlg.arrayYNumEdit.text())
                item.spacing = float(dlg.arrayViaSpacingEdit.text()) * fabproc.dbu

    def layoutPathProperties(self, item):
        dlg = ldlg.layoutPathPropertiesDialog(self.editorWindow)
        match item.mode:
            case 0:
                dlg.manhattanButton.setChecked(True)
            case 1:
                dlg.diagonalButton.setChecked(True)
            case 2:
                dlg.anyButton.setChecked(True)
            case 3:
                dlg.horizontalButton.setChecked(True)
            case 4:
                dlg.verticalButton.setChecked(True)
        dlg.pathLayerCB.addItems(
            [f"{item.name} [{item.purpose}]" for item in laylyr.pdkDrawingLayers]
        )
        dlg.pathLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.pathWidth.setText(str(item.width / fabproc.dbu))
        dlg.pathNameEdit.setText(item.name)
        roundingFactor = len(str(fabproc.dbu)) - 1
        dlg.startExtendEdit.setText(
            str(round((item.startExtend) / fabproc.dbu, roundingFactor))
        )
        dlg.endExtendEdit.setText(
            str(round((item.endExtend) / fabproc.dbu, roundingFactor))
        )
        dlg.p1PointEditX.setText(
            str(round((item.draftLine.p1().x()) / fabproc.dbu, roundingFactor))
        )
        dlg.p1PointEditY.setText(
            str(round((item.draftLine.p1().y()) / fabproc.dbu, roundingFactor))
        )
        dlg.p2PointEditX.setText(
            str(round((item.draftLine.p2().x()) / fabproc.dbu, roundingFactor))
        )
        dlg.p2PointEditY.setText(
            str(round((item.draftLine.p2().y()) / fabproc.dbu, roundingFactor))
        )
        angle = item.angle
        if dlg.exec() == QDialog.Accepted:
            item.name = dlg.pathNameEdit.text()
            item.layer = laylyr.pdkDrawingLayers[dlg.pathLayerCB.currentIndex()]
            item.width = fabproc.dbu * float(dlg.pathWidth.text())
            item.startExtend = fabproc.dbu * float(dlg.startExtendEdit.text())
            item.endExtend = fabproc.dbu * float(dlg.endExtendEdit.text())
            p1 = QPointF(
                fabproc.dbu * float(dlg.p1PointEditX.text()),
                fabproc.dbu * float(dlg.p1PointEditY.text()),
            )
            p2 = QPointF(
                fabproc.dbu * float(dlg.p2PointEditX.text()),
                fabproc.dbu * float(dlg.p2PointEditY.text()),
            )
            item.draftLine = QLineF(p1, p2)
            item.angle = angle

    def layoutLabelProperties(self, item):
        dlg = ldlg.layoutLabelProperties(self.editorWindow)
        dlg.labelName.setText(item.labelText)
        dlg.labelLayerCB.addItems(
            [f"{layer.name} [{layer.purpose}]" for layer in laylyr.pdkTextLayers]
        )
        dlg.labelLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.familyCB.setCurrentText(item.fontFamily)
        dlg.fontStyleCB.setCurrentText(item.fontStyle)
        dlg.labelHeightCB.setCurrentText(str(int(item.fontHeight)))
        dlg.labelAlignCB.setCurrentText(item.labelAlign)
        dlg.labelOrientCB.setCurrentText(item.labelOrient)
        dlg.labelTopLeftX.setText(str(item.mapToScene(item.start).x() / fabproc.dbu))
        dlg.labelTopLeftY.setText(str(item.mapToScene(item.start).y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.labelText = dlg.labelName.text()
            item.layer = laylyr.pdkTextLayers[dlg.labelLayerCB.currentIndex()]
            item.fontFamily = dlg.familyCB.currentText()
            item.fontStyle = dlg.fontStyleCB.currentText()
            item.fontHeight = int(float(dlg.labelHeightCB.currentText()))
            item.labelAlign = dlg.labelAlignCB.currentText()
            item.labelOrient = dlg.labelOrientCB.currentText()
            item.start = item.snapToGrid(
                item.mapFromScene(
                    QPointF(
                        float(dlg.labelTopLeftX.text()) * fabproc.dbu,
                        float(dlg.labelTopLeftY.text()) * fabproc.dbu,
                    )
                ),
                self.snapTuple,
            )

    def layoutPinProperties(self, item):
        dlg = ldlg.layoutPinProperties(self.editorWindow)
        dlg.pinName.setText(item.pinName)
        dlg.pinDir.setCurrentText(item.pinDir)
        dlg.pinType.setCurrentText(item.pinType)
        dlg.pinLayerCB.addItems(
            [f"{item.name} [{item.layer.purpose}]" for item in laylyr.pdkPinLayers]
        )
        dlg.pinLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.pinBottomLeftX.setText(str(item.mapToScene(item.start).x() / fabproc.dbu))
        dlg.pinBottomLeftY.setText(str(item.mapToScene(item.start).y() / fabproc.dbu))
        dlg.pinTopRightX.setText(str(item.mapToScene(item.end).x() / fabproc.dbu))
        dlg.pinTopRightY.setText(str(item.mapToScene(item.end).y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.pinName = dlg.pinName.text()
            item.pinDir = dlg.pinDir.currentText()
            item.pinType = dlg.pinType.currentText()
            item.layer = laylyr.pdkPinLayers[dlg.pinLayerCB.currentIndex()]
            item.label.labelText = dlg.pinName.text()
            item.start = item.snapToGrid(
                item.mapFromScene(
                    QPointF(
                        float(dlg.pinBottomLeftX.text()) * fabproc.dbu,
                        float(dlg.pinBottomLeftY.text()) * fabproc.dbu,
                    )
                ),
                self.snapTuple,
            )
            item.end = item.snapToGrid(
                item.mapFromScene(
                    QPointF(
                        float(dlg.pinTopRightX.text()) * fabproc.dbu,
                        float(dlg.pinTopRightY.text()) * fabproc.dbu,
                    )
                ),
                self.snapTuple,
            )
            item.layer.name = dlg.pinLayerCB.currentText()

    def layoutInstanceProperties(self, item):
        dlg = ldlg.layoutInstancePropertiesDialog(self.editorWindow)
        dlg.instanceLibName.setText(item.libraryName)
        dlg.instanceCellName.setText(item.cellName)
        dlg.instanceViewName.setText(item.viewName)
        dlg.instanceNameEdit.setText(item.instanceName)
        dlg.xEdit.setText(str(item.scenePos().x() / fabproc.dbu))
        dlg.yEdit.setText(str(item.scenePos().y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.libraryName = dlg.instanceLibName.text().strip()
            item.cellName = dlg.instanceCellName.text().strip()
            item.viewName = dlg.instanceViewName.text().strip()
            item.instanceName = dlg.instanceNameEdit.text().strip()
            item.setPos(
                QPoint(
                    self.snapToBase(
                        float(dlg.xEdit.text()) * fabproc.dbu, self.snapTuple[0]
                    ),
                    self.snapToBase(
                        float(dlg.yEdit.text()) * fabproc.dbu, self.snapTuple[1]
                    ),
                )
            )

    def layoutPCellProperties(self, item: lshp.layoutPcell):
        dlg = ldlg.pcellInstancePropertiesDialog(self.editorWindow)
        dlg.pcellLibName.setText(item.libraryName)
        dlg.pcellCellName.setText(item.cellName)
        dlg.pcellViewName.setText(item.viewName)
        dlg.instanceNameEdit.setText(item.instanceName)
        lineEditDict = self.extractPcellInstanceParameters(item)
        for key, value in lineEditDict.items():
            dlg.instanceParamsLayout.addRow(key, value)
        dlg.xEdit.setText(str(item.scenePos().x() / fabproc.dbu))
        dlg.yEdit.setText(str(item.scenePos().y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            item.libraryName = dlg.pcellLibName.text()
            item.cellName = dlg.pcellCellName.text()
            item.viewName = dlg.pcellViewName.text()
            item.instanceName = dlg.instanceNameEdit.text()
            rowCount = dlg.instanceParamsLayout.rowCount()
            instParamDict = {}
            for row in range(4, rowCount):  # first 4 rows are already processed.
                labelText = (
                    dlg.instanceParamsLayout.itemAt(row, QFormLayout.LabelRole)
                    .widget()
                    .text()
                )
                paramValue = (
                    dlg.instanceParamsLayout.itemAt(row, QFormLayout.FieldRole)
                    .widget()
                    .text()
                )
                instParamDict[labelText] = paramValue

            item(**instParamDict)

    def extractPcellInstanceParameters(self, instance: lshp.layoutPcell) -> dict:
        initArgs = inspect.signature(instance.__class__.__init__).parameters
        argsUsed = [param for param in initArgs if (param != "self")]
        argDict = {arg: getattr(instance, arg) for arg in argsUsed}
        lineEditDict = {key: edf.shortLineEdit(value) for key, value in argDict.items()}
        return lineEditDict

    def copySelectedItems(self):
        """
        Copy the selected items and create new instances with incremented names.
        """
        for item in self.selectedItems():
            # Create a deep copy of the item using JSON serialization
            itemCopyJson = json.dumps(item, cls=layenc.layoutEncoder)
            itemCopyDict = json.loads(itemCopyJson)
            shape = lj.layoutItems(self).create(itemCopyDict)
            match itemCopyDict["type"]:
                case "Inst" | "Pcell":
                    self.itemCounter += 1
                    shape.instanceName = f"I{self.itemCounter}"
                    shape.counter = self.itemCounter
            self.undoStack.push(us.addShapeUndo(self, shape))
            shape.setPos(
                QPoint(
                    item.pos().x() + 4 * self.snapTuple[0],
                    item.pos().y() + 4 * self.snapTuple[1],
                )
            )

    def moveBySelectedItems(self):
        if self.selectedItems():
            dlg = pdlg.moveByDialogue(self.editorWindow)
            dlg.xEdit.setText("0.0")
            dlg.yEdit.setText("0.0")
            if dlg.exec() == QDialog.Accepted:
                for item in self.selectedItems():
                    item.moveBy(
                        self.snapToBase(
                            float(dlg.xEdit.text()) * fabproc.dbu, self.snapTuple[0]
                        ),
                        self.snapToBase(
                            float(dlg.yEdit.text()) * fabproc.dbu, self.snapTuple[1]
                        ),
                    )
                self.editorWindow.messageLine.setText(
                    f"Moved items by {dlg.xEdit.text()} and {dlg.yEdit.text()}"
                )
                self.editModes.setMode("selectItem")

    def deleteAllRulers(self):
        for ruler in self.rulersSet:
            undoCommand = us.deleteShapeUndo(self, ruler)
            self.undoStack.push(undoCommand)

    def goDownHier(self):
        if self.selectedItems():
            for item in self.selectedItems():
                if isinstance(item, lshp.layoutInstance):
                    dlg = fd.goDownHierDialogue(self.editorWindow)
                    libItem = libm.getLibItem(
                        self.editorWindow.libraryView.libraryModel, item.libraryName
                    )
                    cellItem = libm.getCellItem(libItem, item.cellName)
                    viewNames = [
                        cellItem.child(i).text()
                        for i in range(cellItem.rowCount())
                        # if cellItem.child(i).text() != item.viewName
                        if "layout" in cellItem.child(i).text()
                    ]
                    dlg.viewListCB.addItems(viewNames)
                    if dlg.exec() == QDialog.Accepted:
                        libItem = libm.getLibItem(
                            self.editorWindow.libraryView.libraryModel, item.libraryName
                        )
                        cellItem = libm.getCellItem(libItem, item.cellName)
                        viewItem = libm.getViewItem(
                            cellItem, dlg.viewListCB.currentText()
                        )
                        openViewT = (
                            self.editorWindow.libraryView.libBrowsW.openCellView(
                                viewItem, cellItem, libItem
                            )
                        )
                        if self.editorWindow.appMainW.openViews[openViewT]:
                            childWindow = self.editorWindow.appMainW.openViews[
                                openViewT
                            ]
                            childWindow.parentEditor = self.editorWindow
                            childWindow.layoutToolbar.addAction(childWindow.goUpAction)
                            if dlg.buttonId == 2:
                                childWindow.centralW.scene.readOnly = True

    @staticmethod
    def rotateVector(mouseLoc: QPoint, vector: layp.layoutPath, transform: QTransform):
        """
        Rotate the vector based on the mouse location and transform.

        Args:
            mouseLoc (QPoint): The current mouse location.
            vector (layp.layoutPath): The vector to rotate.
            transform (QTransform): The transform to apply to the vector.
        """
        start = vector.start
        xmove = mouseLoc.x() - start.x()
        ymove = mouseLoc.y() - start.y()

        # Determine the new end point of the vector based on the mouse movement
        if xmove >= 0 and ymove >= 0:
            vector.end = QPoint(start.x(), start.y() + ymove)
        elif xmove >= 0 and ymove < 0:
            vector.end = QPoint(start.x() + xmove, start.y())
        elif xmove < 0 and ymove < 0:
            vector.end = QPoint(start.x(), start.y() + ymove)
        elif xmove < 0 and ymove >= 0:
            vector.end = QPoint(start.x() + xmove, start.y())

        vector.setTransform(transform)


class editor_view(QGraphicsView):
    """
    The qgraphicsview for qgraphicsscene. It is used for both schematic and layout editors.
    """

    def __init__(self, scene, parent):
        super().__init__(scene, parent)
        self.parent = parent
        self.editor = self.parent.parent
        self.scene = scene
        self.logger = self.scene.logger
        self.majorGrid = self.editor.majorGrid
        self.snapGrid = self.editor.snapGrid
        self.snapTuple = self.editor.snapTuple
        self.gridbackg = True
        self.linebackg = False

        self.init_UI()

    def init_UI(self):
        """
        Initializes the user interface.

        This function sets up various properties of the QGraphicsView object, such as rendering hints,
        mouse tracking, transformation anchors, and cursor shape.

        Returns:
            None
        """
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # self.setCacheMode(QGraphicsView.CacheBackground)
        self.setMouseTracking(True)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setInteractive(True)
        self.setCursor(Qt.CrossCursor)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle the wheel event for zooming in and out of the view.

        Args:
            event (QWheelEvent): The wheel event to handle.
        """
        # Get the current center point of the view
        oldPos = self.mapToScene(self.viewport().rect().center())

        # Perform the zoom
        zoomFactor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        self.scale(zoomFactor, zoomFactor)

        # Get the new center point of the view
        newPos = self.mapToScene(self.viewport().rect().center())

        # Calculate the delta and adjust the scene position
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())

    def snapToBase(self, number, base):
        """
        Restrict a number to the multiples of base
        """
        return int(base * int(round(number / base)))

    def snapToGrid(self, point: QPoint, snapTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(
            self.snapToBase(point.x(), snapTuple[0]),
            self.snapToBase(point.y(), snapTuple[1]),
        )

    def drawBackground(self, painter, rect):
        """
        Draws the background of the painter within the given rectangle.

        Args:
            painter (QPainter): The painter object to draw on.
            rect (QRect): The rectangle to draw the background within.
        """

        # Fill the rectangle with black color
        painter.fillRect(rect, QColor("black"))

        # Calculate the coordinates of the left, top, bottom, and right edges of the rectangle
        left = int(rect.left()) - (int(rect.left()) % self.majorGrid)
        top = int(rect.top()) - (int(rect.top()) % self.majorGrid)
        bottom = int(rect.bottom())
        right = int(rect.right())

        if self.gridbackg:
            # Set the pen color to gray
            painter.setPen(QColor("white"))

            # Create a range of x and y coordinates for drawing the grids
            x_coords, y_coords = self.findCoords(left, top, bottom, right)

            for x_coord in x_coords:
                for y_coord in y_coords:
                    painter.drawPoint(x_coord, y_coord)

        elif self.linebackg:
            # Set the pen color to gray
            painter.setPen(QColor("gray"))

            # Create a range of x and y coordinates for drawing the lines
            x_coords, y_coords = self.findCoords(left, top, bottom, right)

            # Draw vertical lines
            for x in x_coords:
                painter.drawLine(x, top, x, bottom)

            # Draw horizontal lines
            for y in y_coords:
                painter.drawLine(left, y, right, y)

        else:
            # Call the base class method to draw the background
            super().drawBackground(painter, rect)

    def findCoords(self, left, top, bottom, right):
        """
        Calculate the coordinates for drawing lines or points on a grid.

        Parameters:
            left (int): The leftmost coordinate of the grid.
            top (int): The topmost coordinate of the grid.
            bottom (int): The bottommost coordinate of the grid.
            right (int): The rightmost coordinate of the grid.

        Returns:
            tuple: A tuple containing the x and y coordinates for drawing the lines or points.
        """
        x_coords = range(left, right, self.majorGrid)
        y_coords = range(top, bottom, self.majorGrid)

        if 160 <= len(x_coords) < 320:
            # Create a range of x and y coordinates for drawing the lines
            x_coords = range(left, right, self.majorGrid * 2)
            y_coords = range(top, bottom, self.majorGrid * 2)
        elif 320 <= len(x_coords) < 640:
            x_coords = range(left, right, self.majorGrid * 4)
            y_coords = range(top, bottom, self.majorGrid * 4)
        elif 640 <= len(x_coords) < 1280:
            x_coords = range(left, right, self.majorGrid * 8)
            y_coords = range(top, bottom, self.majorGrid * 8)
        elif 1280 <= len(x_coords) < 2560:
            x_coords = range(left, right, self.majorGrid * 16)
            y_coords = range(top, bottom, self.majorGrid * 16)
        elif len(x_coords) >= 2560:  # grid dots are too small to see
            x_coords = range(left, right, self.majorGrid * 1000)
            y_coords = range(top, bottom, self.majorGrid * 1000)

        return x_coords, y_coords

    def keyPressEvent(self, event: QKeyEvent):
        match event.key():
            case Qt.Key_F:
                self.scene.fitItemsInView()
            case Qt.Key_Left:
                self.scene.moveSceneLeft()
            case Qt.Key_Right:
                self.scene.moveSceneRight()
            case Qt.Key_Up:
                self.scene.moveSceneUp()
            case Qt.Key_Down:
                self.scene.moveSceneDown()
            case Qt.Key_Escape:
                self.scene.editModes.setMode("selectItem")
                self.editor.messageLine.setText("Select Item")
            case _:
                super().keyPressEvent(event)

    def printView(self, printer):
        """
        Print view using selected Printer.
        """
        painter = QPainter(printer)

        if self.gridbackg:
            self.gridbackg = False
        else:
            self.linebackg = False

        self.revedaPrint(painter)

        self.gridbackg = not self.gridbackg
        self.linebackg = not self.linebackg

    def revedaPrint(self, painter):
        viewport_geom = self.viewport().geometry()
        self.drawBackground(painter, viewport_geom)
        painter.drawText(viewport_geom, "Revolution EDA")
        self.render(painter)
        painter.end()


class symbol_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self.visibleRect = None


class schematic_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self.visibleRect = None  # initialize to an empty rectangle

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.scene.removeSnapRect()
            if self.scene._newNet:
                self.scene.checkNewNet(self.scene._newNet)
                self.scene._newNet = None
                self.scene.editModes.setMode("selectItem")
        super().keyPressEvent(event)


class layout_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self.visibleRect = None

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            if self.scene.editModes.drawPath and self.scene._newPath:
                self.scene._newNet = None

            elif self.scene.editModes.drawRect and self.scene._newRect:
                self.scene._newRect = None
            self.scene.editModes.setMode("selectItem")
        super().keyPressEvent(event)


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
                cirFile.write(f'{line}\n')
            for line in self.vamodelLines:
                cirFile.write(f'{line}\n')
            for line in self.vahdlLines:
                cirFile.write(f'{line}\n')

    @property
    def configDict(self):
        return self._configDict

    @configDict.setter
    def configDict(self, value: dict):
        assert isinstance(value, dict)
        self._configDict = value

    def recursiveNetlisting(self, schematic: schematicEditor, cirFile):
        """
        Recursively traverse all sub-circuits and netlist them.
        """
        try:
            schematicScene = schematic.centralW.scene
            schematicScene.groupAllNets()  # name all nets in the
            # schematic
            sceneSymbolSet = schematicScene.findSceneSymbolSet()
            schematicScene.generatePinNetMap(sceneSymbolSet)
            for elementSymbol in sceneSymbolSet:
                if (
                    elementSymbol.symattrs.get("XyceNetlistPass") != "1"
                    and (not elementSymbol.netlistIgnore)
                ):
                    libItem = libm.getLibItem(
                        schematic.libraryView.libraryModel, elementSymbol.libraryName
                    )
                    cellItem = libm.getCellItem(libItem, elementSymbol.cellName)
                    viewItems = [
                        cellItem.child(row) for row in range(cellItem.rowCount())
                    ]
                    viewNames = [view.viewName for view in viewItems]

                    netlistView = "symbol"
                    if self._use_config:
                        netlistView = self.configDict.get(elementSymbol.cellName)[1]
                    else:
                        for viewName in self.switchViewList:
                            if viewName in viewNames:
                                netlistView = viewName
                                break
                    # these are qstandarditem in library browser.
                    viewItem = libm.getViewItem(cellItem, netlistView)


                    # now create the netlist line for that item.
                    print(f"{elementSymbol.cellName}, {netlistView}")
                    self.createItemLine(cirFile, elementSymbol, cellItem, netlistView)
                elif elementSymbol.netlistIgnore:
                    cirFile.write(
                        f"*{elementSymbol.instanceName} is marked to be ignored\n"
                    )
                elif not elementSymbol.symattrs.get("XyceNetlistPass", False):
                    cirFile.write(
                        f"*{elementSymbol.instanceName} has no XyceNetlistLine attribute\n"
                    )

        except Exception as e:
            self.schematic.logger.error(f'Netlisting error: {e}')

    def createItemLine(
        self,
        cirFile,
        elementSymbol: shp.schematicSymbol,
        cellItem: scb.cellItem,
        netlistView: str,
    ):
        pass
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
            xyceNetlistFormatLine = elementSymbol.symattrs["XyceSymbolNetlistLine"].strip()
            for labelItem in elementSymbol.labels.values():
                if labelItem.labelDefinition in xyceNetlistFormatLine:
                    xyceNetlistFormatLine = xyceNetlistFormatLine.replace(
                        labelItem.labelDefinition, labelItem.labelText
                    )

            for attrb, value in elementSymbol.symattrs.items():
                if f"[%{attrb}]" in xyceNetlistFormatLine:
                    xyceNetlistFormatLine = xyceNetlistFormatLine.replace(
                        f"[%{attrb}]", value
                    )
            pinList = " ".join(elementSymbol.pinNetMap.values())
            xyceNetlistFormatLine = (
                xyceNetlistFormatLine.replace("[@pinList]", pinList) + "\n"
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
            spiceNetlistFormatLine = elementSymbol.symattrs["XyceSpiceNetlistLine"].strip()
            for labelItem in elementSymbol.labels.values():
                if labelItem.labelDefinition in spiceNetlistFormatLine:
                    spiceNetlistFormatLine = spiceNetlistFormatLine.replace(
                        labelItem.labelDefinition, labelItem.labelText
                    )

            for attrb, value in elementSymbol.symattrs.items():
                if f"[%{attrb}]" in spiceNetlistFormatLine:
                    spiceNetlistFormatLine = spiceNetlistFormatLine.replace(
                        f"[%{attrb}]", value
                    )
            pinList = elementSymbol.symattrs.get("pinOrder", ", ").replace(",", " ")
            spiceNetlistFormatLine = (
                spiceNetlistFormatLine.replace("[@pinList]", pinList) + "\n"
            )
            self.includeLines.add(
                elementSymbol.symattrs.get(
                    "incLine", "* no include line is found for {item.cellName}"
                ).strip()
            )
            return spiceNetlistFormatLine
        except Exception as e:
            self._scene.logger.error(f'Spice subckt netlist error: {e}')
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
                if labelItem.labelDefinition in verilogaNetlistFormatLine:
                    verilogaNetlistFormatLine = verilogaNetlistFormatLine.replace(
                        labelItem.labelDefinition, labelItem.labelText
                    )

            for attrb, value in elementSymbol.symattrs.items():
                if f"[%{attrb}]" in verilogaNetlistFormatLine:
                    verilogaNetlistFormatLine = verilogaNetlistFormatLine.replace(
                        f"[%{attrb}]", value
                    )
            pinList = " ".join(elementSymbol.pinNetMap.values())
            verilogaNetlistFormatLine = (
                verilogaNetlistFormatLine.replace("[@pinList]", pinList) + "\n"
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
    def __init__(self, appmainW, schViewItem, configDict, viewItem):
        super().__init__(parent=appmainW)
        self.appmainW = appmainW  # app mainwindow
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
        if self.appmainW.libraryBrowser is None:
            self.appmainW.createLibraryBrowser()
        topSchematicWindow = schematicEditor(
            self.schViewItem,
            self.appmainW.libraryDict,
            self.appmainW.libraryBrowser.libBrowserCont.designView,
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

    def saveClick(self):
        configFilePathObj = self.viewItem.data(Qt.UserRole + 2)
        items = list()
        items.insert(0, {"viewName": "config"})
        items.insert(1, {"reference": self.schViewItem.viewName})
        items.insert(2, self.configDict)
        with configFilePathObj.open(mode="w+") as configFile:
            json.dump(items, configFile, indent=4)


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
