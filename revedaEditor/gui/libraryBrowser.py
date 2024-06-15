
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

import json
# from hashlib import new
import pathlib
import shutil
from copy import deepcopy

# import numpy as np
from PySide6.QtCore import (
    Qt,
)
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QIcon,
)
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QMainWindow,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.libraryModelView as lmview
import revedaEditor.backend.schBackEnd as scb
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.layoutDialogues as ldlg
import revedaEditor.gui.textEditor as ted
from revedaEditor.gui.symbolEditor import symbolEditor
from revedaEditor.gui.schematicEditor import schematicEditor
from revedaEditor.gui.layoutEditor import layoutEditor
from revedaEditor.gui.configEditor import configViewEdit
import revedaEditor.resources.resources

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
