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
#    consideration (including without limitation fees for hosting) a product or service whose value
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
import logging

# from hashlib import new
import pathlib

from copy import deepcopy


# import numpy as np
from PySide6.QtCore import (
    Qt,
)
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QActionGroup
from PySide6.QtWidgets import (
    QApplication,
    QDialogButtonBox,
    QDialog,
    QFileDialog,
    QMainWindow,
    QToolBar,
    QVBoxLayout,
    QFormLayout,
    QWidget,
    QListView,
    QMenu,
    QGroupBox,
    QComboBox,
)

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.libraryModelView as lmview
import revedaEditor.backend.libBackEnd as libb
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.layoutDialogues as ldlg
import revedaEditor.gui.textEditor as ted
import revedaEditor.gui.editFunctions as edf
from revedaEditor.gui.symbolEditor import symbolEditor
from revedaEditor.gui.schematicEditor import schematicEditor
from revedaEditor.gui.layoutEditor import layoutEditor
from revedaEditor.gui.configEditor import configViewEdit
from revedaEditor.gui.startThread import startThread


class libraryBrowser(QMainWindow):
    CELLVIEWS = [
        "schematic",
        "symbol",
        "layout",
        "veriloga",
        "config",
        "spice",
        "pcell",
        "revbench",
    ]

    def __init__(self, appMainW: QMainWindow) -> None:
        super().__init__()
        self.resize(600, 600)
        self.appMainW = appMainW
        self._app = QApplication.instance()
        self.libraryDict = appMainW.libraryDict
        self.cellViews = self.CELLVIEWS
        self.setWindowIcon(QIcon(":logo-color.png"))
        self.setWindowTitle("Library Browser")

        # Setup UI components
        self._createMenuBar()
        self._createActions()
        self._createToolBars()
        self._createTriggers()

        # Setup library components
        self.logger = appMainW.logger
        self.libFilePath = appMainW.libraryPathObj
        self.libBrowserCont = libraryBrowserContainer(self)
        self.setCentralWidget(self.libBrowserCont)
        self.designView = self.libBrowserCont.designView
        self.editProcess = None

    def _createMenuBar(self):
        self.browserMenubar = self.menuBar()
        self.browserMenubar.setNativeMenuBar(False)
        self.libraryMenu = self.browserMenubar.addMenu("&Library")
        self.cellMenu = self.browserMenubar.addMenu("&Cell")
        self.cellViewMenu = self.browserMenubar.addMenu("Cell &View")
        self.viewMenu: QMenu = self.browserMenubar.addMenu("&View")
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

        updateLibRefIcon = QIcon(":/icons/arrow-continue.png")
        self.updateLibRefAction = QAction(updateLibRefIcon, "Update Library Refs...", self)
        self.updateLibRefAction.setToolTip("Update Library References")
        self.libraryMenu.addAction(self.updateLibRefAction)

        newCellIcon = QIcon(":/icons/document--plus.png")
        self.newCellAction = QAction(newCellIcon, "New Cell...", self)
        self.newCellAction.setToolTip("Create New Cell")
        self.cellMenu.addAction(self.newCellAction)

        deleteCellIcon = QIcon(":/icons/node-delete.png")
        self.deleteCellAction = QAction(deleteCellIcon, "Delete Cell...", self)
        self.deleteCellAction.setToolTip("Delete Cell")
        self.cellMenu.addAction(self.deleteCellAction)

        newCellViewIcon = QIcon(":/icons/document--pencil.png")
        self.newCellViewAction = QAction(newCellViewIcon, "Create New CellView...", self)
        self.newCellViewAction.setToolTip("Create New Cellview")
        self.cellViewMenu.addAction(self.newCellViewAction)

        openCellViewIcon = QIcon(":/icons/document--pencil.png")
        self.openCellViewAction = QAction(openCellViewIcon, "Open CellView...", self)
        self.openCellViewAction.setToolTip("Open CellView")
        self.cellViewMenu.addAction(self.openCellViewAction)

        deleteCellViewIcon = QIcon(":/icons/node-delete.png")
        self.deleteCellViewAction = QAction(deleteCellViewIcon, "Delete CellView...", self)
        self.deleteCellViewAction.setToolTip("Delete Cellview")
        self.cellViewMenu.addAction(self.deleteCellViewAction)

        viewSelectGroup = QActionGroup(self)
        viewSelectGroup.setExclusive(True)

        self.selectColumnViewAction = QAction("Column View", self)
        self.selectColumnViewAction.setCheckable(True)
        viewSelectGroup.addAction(self.selectColumnViewAction)
        self.selectColumnViewAction.setChecked(True)
        self.selectTreeViewAction = QAction("Tree View", self)
        self.selectTreeViewAction.setCheckable(True)
        viewSelectGroup.addAction(self.selectTreeViewAction)
        self.viewMenu.addActions(viewSelectGroup.actions())

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
        self.updateLibRefAction.triggered.connect(self.updateLibRefClick)
        self.selectColumnViewAction.triggered.connect(self.selectColumnViewClick)
        self.selectTreeViewAction.triggered.connect(self.selectTreeViewClick)

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
        """Open a directory and designate it as a library."""
        libDialog = QFileDialog(self, "Create/Open Library", str(pathlib.Path.cwd()))
        libDialog.setFileMode(QFileDialog.Directory)

        if libDialog.exec() == QDialog.Accepted:
            libPathObj = pathlib.Path(libDialog.selectedFiles()[0])
            self.libraryDict[libPathObj.stem] = libPathObj
            libPathObj.joinpath("reveda.lib").touch(exist_ok=True)
            self.designView.libraryModel.populateLibrary(libPathObj)
            self.writeLibDefFile(self.designView.libraryModel.libraryDict, self.libFilePath)
            self.appMainW.libraryDict = self.designView.libraryModel.libraryDict
            self.designView.reworkDesignLibrariesView(self.appMainW.libraryDict)

    def closeLibClick(self):
        libCloseDialog = fd.closeLibDialog(self.libraryDict, self)
        if libCloseDialog.exec() == QDialog.Accepted:
            libName = libCloseDialog.libNamesCB.currentText()
            libItem = libm.getLibItem(self.designView.libraryModel, libName)
            self.libraryDict.pop(libName, None)
            self.designView.libraryModel.invisibleRootItem().removeRow(libItem.row())

    def libraryEditorClick(self, s):
        """
        Open library editor dialogue.
        """
        tempDict = deepcopy(self.libraryDict)
        pathEditDlg = fd.libraryPathEditorDialog(self, tempDict)
        libDefFilePathObj = pathlib.Path.cwd().joinpath("library.json")
        if pathEditDlg.exec() == QDialog.Accepted:
            self.libraryDict.clear()
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
        self.designView.reworkDesignLibrariesView(self.designView.libraryModel.libraryDict)

    def updateLibraryClick(self):
        self.designView.reworkDesignLibrariesView(self.designView.libraryModel.libraryDict)

    def updateLibRefClick(self):
        try:
            dlg = libraryListView(self, self.designView.libraryModel)
            dlg.show()
        except Exception as e:
            self.logger.error(f"Error updating library references: {e}")

    def newCellClick(self, s):
        try:
            self.designView.libraryModel = self.designView.libraryModel
            firstLibName = self.libraryDict.keys().__iter__().__next__()
            firstLibItem = libm.getLibItem(self.designView.libraryModel, firstLibName)
            self.libBrowserCont.designView.createCell(firstLibItem)
        except Exception as e:
            self.logger.error(f"Error in creating new cell: {e}")

    def deleteCellClick(self, s):
        dlg = fd.deleteCellDialog(self, self.designView.libraryModel)
        if dlg.exec() == QDialog.Accepted:
            libItem = libm.getLibItem(
                self.designView.libraryModel, dlg.libNamesCB.currentText()
            )
            if dlg.cellCB.currentText().strip() == "":
                self.logger.error("Please enter a cell name.")
            else:
                cellItem = libm.getCellItem(libItem, dlg.cellCB.currentText())
                self.designView.deleteCell(cellItem)

    def newCellViewClick(self, s):
        dlg = fd.newCellViewDialog(self, self.designView.libraryModel)
        dlg.viewType.addItems(self.cellViews)

        if dlg.exec() != QDialog.Accepted:
            return
        libItem = libm.getLibItem(
            self.designView.libraryModel, dlg.libNamesCB.currentText()
        )
        cellItem = libm.getCellItem(libItem, dlg.cellCB.currentText())
        self.designView.handleNewCellView(cellItem, dlg)

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
                    configWindow = self.createNewConfigView(cellItem, viewItem, dlg)
                    self.appMainW.openViews[viewTuple] = configWindow
                    configWindow.show()
            case "schematic":
                # libb.createCellView(self.appMainW, viewItem.viewName, cellItem)

                schematicWindow = schematicEditor(
                    viewItem, self.libraryDict, self.libBrowserCont.designView
                )
                self.appMainW.openViews[viewTuple] = schematicWindow
                schematicWindow.loadSchematic()
                schematicWindow.show()
            case "symbol":
                # libb.createCellView(self.appMainW, viewItem.viewName, cellItem)
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
            case "revbench":
                self.openRevbenchWindow(libItem, cellItem, viewItem)

    def createNewConfigView(
        self,
        cellItem: libb.cellItem,
        viewItem: libb.viewItem,
        dlg: fd.createConfigViewDialogue,
    ):
        selectedSchName = dlg.viewNameCB.currentText()
        selectedSchItem = libm.getViewItem(cellItem, selectedSchName)

        schematicWindow = schematicEditor(
            selectedSchItem,
            self.libraryDict,
            self.libBrowserCont.designView,
        )
        schematicWindow.loadSchematic()
        switchViewList = [
            viewName.strip() for viewName in dlg.switchViews.text().split(",")
        ]
        stopViewList = [viewName.strip() for viewName in dlg.stopViews.text().split(",")]
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
        return configWindow

    def openConfigEditWindow(self, configDict, schViewItem, viewItem):
        schematicName = schViewItem.viewName
        cellItem = schViewItem.parent()
        libItem = cellItem.parent()
        configWindow = configViewEdit(self.appMainW, schViewItem, configDict, viewItem)
        configWindow.centralWidget.libraryNameEdit.setText(libItem.libraryName)
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
        return configWindow

    def openRevbenchWindow(self, libItem, cellItem, viewItem):
        if self._app.plugins.get("plugins.revedasim"):
            simdlg = self._app.plugins["plugins.revedasim"].dialogueWindows
            # simdlg = importlib.import_module("revedasim.dialogueWindows",
            #     str(self._app.revedasim_pathObj), )
            revbenchdlg = simdlg.createRevbenchDialogue(
                self, self.designView.libraryModel, cellItem, viewItem
            )
            # hide view name dialog not to confuse the user.
            revbenchdlg.benchBox.setVisible(False)
            revbenchdlg.mainLayout.update()
            if revbenchdlg.exec() == QDialog.Accepted:
                items = []
                libraryName = libItem.data(Qt.UserRole + 2).name
                cellName = cellItem.data(Qt.UserRole + 2).name
                items.append({"viewType": "revbench"})
                items.append({"lib": libraryName})
                items.append({"cell": cellName})
                items.append({"view": revbenchdlg.viewCB.currentText()})
                items.append({"settings": []})
                with viewItem.data(Qt.UserRole + 2).open(mode="w") as benchFile:
                    json.dump(items, benchFile, indent=4)
                simmwModule = self._app.plugins["plugins.revedasim"]
                simmw = simmwModule.SimMainWindow(
                    viewItem, self.designView.libraryModel, self.designView
                )
                simmw.show()
        else:
            self.logger.error("Reveda SAE is not installed.")

    def selectCellView(self, libModel) -> libb.viewItem:
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
        viewItem = self.selectCellView(self.designView.libraryModel)
        cellItem = viewItem.parent()
        libItem = cellItem.parent()
        self.openCellView(viewItem, cellItem, libItem)

    def openCellView(
        self,
        viewItem: libb.viewItem,
        cellItem: libb.cellItem,
        libItem: libb.libraryItem,
    ):
        viewName = viewItem.viewName
        cellName = cellItem.cellName
        libName = libItem.libraryName
        openCellViewTuple = ddef.viewTuple(libName, cellName, viewName)
        if openCellViewTuple in self.appMainW.openViews.keys():
            self.appMainW.openViews[openCellViewTuple].show()
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
                        xyceEditor = ted.xyceEditor(self.appMainW, str(spicefilePathObj))
                        self.appMainW.openViews[openCellViewTuple] = xyceEditor
                        xyceEditor.cellViewTuple = openCellViewTuple
                        xyceEditor.closedSignal.connect(self.spiceEditFinished)
                        xyceEditor.show()

                case "pcell":
                    textEditor = ted.jsonEditor(self.appMainW, str(viewItem.viewPath))
                    textEditor.show()

                case "config":
                    with open(viewItem.viewPath) as tempFile:
                        items = json.load(tempFile)
                    schematicName = items[1]["reference"]
                    schViewItem = libm.getViewItem(cellItem, schematicName)
                    configDict = items[2]
                    configWindow = self.openConfigEditWindow(
                        configDict, schViewItem, viewItem
                    )
                    self.appMainW.openViews[openCellViewTuple] = configWindow
                    configWindow.show()
                case "revbench":
                    # if self._app.revedasim_pathObj:
                    #     try:
                    if self._app.plugins.get("plugins.revedasim"):
                        SimMainW = self._app.plugins["plugins.revedasim"].SimMainWindow
                        simmw = SimMainW(
                            viewItem, self.designView.libraryModel, self.designView
                        )
                        self.appMainW.openViews[openCellViewTuple] = simmw
                        simmw.show()
                    else:
                        self.logger.error("Reveda SAE is not installed.")

                case _:
                    pass
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
        viewItem = self.selectCellView(self.designView.libraryModel)
        try:
            self.designView.deleteView(viewItem)
        except Exception as e:
            self.logger.warning(f"Error:{e}")

    def selectColumnViewClick(self):
        self.libBrowserCont.switchToColumnView()

    def selectTreeViewClick(self):
        self.libBrowserCont.switchToTreeView()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()  # ignore the default close event
        self.hide()  # hide the window instead


class libraryBrowserContainer(QWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        self.logger = logging.getLogger("reveda")

    def initUI(self):
        self.layout = QVBoxLayout()
        self.designView = lmview.designLibrariesColumnView(self)
        self.layout.addWidget(self.designView)
        self.setLayout(self.layout)

    # def switchToTreeView(self):
    #     old_widget = self.layout.itemAt(0).widget()
    #     self.designView = lmview.designLibrariesTreeView(self)
    #     self.layout.replaceWidget(old_widget, self.designView)
    #     old_widget.deleteLater()  # Properly delete the old widget
    #     self.update()
    def switchToTreeView(self):
        try:
            # Check if layout exists and has items
            if not self.layout or self.layout.count() == 0:
                return

            # Get the old widget safely
            item = self.layout.itemAt(0)
            if not item:
                return

            old_widget = item.widget()
            if not old_widget:
                return

            # Create new view before removing old one to prevent blank screen
            self.designView = lmview.designLibrariesTreeView(self)

            # Block signals temporarily during widget replacement to prevent unnecessary updates
            old_widget.blockSignals(True)
            self.blockSignals(True)

            # Replace widget and ensure proper cleanup
            if self.layout.replaceWidget(old_widget, self.designView):
                old_widget.hide()  # Hide before deletion to prevent visual artifacts
                old_widget.setParent(None)  # Detach from parent
                old_widget.deleteLater()
                self.parent.designView = self.designView
                # Restore signal handling
                self.blockSignals(False)

            # Use update() only if needed, or consider using more specific update methods
            self.designView.show()

        except Exception as e:
            self.logger.error(f"Error switching to tree view: {str(e)}")
            # You might want to add proper error handling/logging here

    # def switchToColumnView(self):
    #     old_widget = self.layout.itemAt(0).widget()
    #     self.designView = lmview.designLibrariesColumnView(self)
    #     self.layout.replaceWidget(old_widget, self.designView)
    #     old_widget.deleteLater()  # Properly delete the old widget
    #     self.update()

    def switchToColumnView(self):
        """
        Switches the current view to a column view.
        Returns: bool indicating success/failure of the operation
        """
        try:
            # Validate layout existence and content
            if not self.layout or self.layout.count() == 0:
                return False

            # Safely get the old widget
            item = self.layout.itemAt(0)
            if not item:
                return False

            old_widget = item.widget()
            if not old_widget:
                return False

            self.designView = lmview.designLibrariesColumnView(self)

            # Block signals during widget replacement to prevent unnecessary updates
            old_widget.blockSignals(True)
            self.blockSignals(True)

            if self.layout.replaceWidget(old_widget, self.designView):
                old_widget.hide()  # Prevent flickering
                old_widget.setParent(None)  # Detach from parent
                old_widget.deleteLater()
                self.parent.designView = self.designView
                self.blockSignals(False)

            # Show new widget and ensure it's properly displayed
            self.designView.show()

            # Use a more specific update if possible instead of full update
            self.designView.update()  # Or self.update() if needed

            return True

        except Exception as e:
            logging.error(f"Error switching to column view: {str(e)}")
            return False


class libraryListView(QDialog):
    def __init__(self, parent, libraryModel: lmview.designLibrariesModel):
        super().__init__(parent)
        self.appMainW = QApplication.instance().mainW
        self.model = libraryModel
        self.setWindowTitle("Library List View")
        self.setGeometry(100, 100, 300, 400)
        librariesGroupBox = QGroupBox("Libraries")
        layout = QVBoxLayout()
        self.libraryListView = lmview.libraryCheckListView(self, libraryModel)
        self.libraryListView.setSelectionMode(QListView.MultiSelection)
        listViewLayout = QVBoxLayout()
        listViewLayout.addWidget(self.libraryListView)
        librariesGroupBox.setLayout(listViewLayout)
        layout.addWidget(librariesGroupBox)
        librariesGroupBox = QGroupBox("Libraries")
        librariesLayout = QFormLayout()
        self.origLibNameLineEdit = edf.longLineEdit()
        librariesLayout.addRow("Original Library Name", self.origLibNameLineEdit)
        self.newLibNameCB = QComboBox()
        self.newLibNameCB.setModel(libraryModel)
        self.newLibNameCB.setEditable(True)
        self.newLibNameCB.setInsertPolicy(QComboBox.InsertAtTop)
        self.newLibNameCB.setMinimumContentsLength(20)
        librariesLayout.addRow("New Library Name", self.newLibNameCB)
        librariesGroupBox.setLayout(librariesLayout)
        layout.addWidget(librariesGroupBox)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def accept(self):
        changedLibraries = self.libraryListView.getCheckedLibraries()
        if changedLibraries:
            for libName in changedLibraries:
                updateLibraryRunner = startThread(  
                lmview.updateJSONFieldInLibrary(
                    self.model,
                    libName,
                    "lib",
                    self.origLibNameLineEdit.text().strip(),
                    self.newLibNameCB.currentText(),
                ))
                updateLibraryRunner.signals.finished.connect(
                    lambda: self.appMainW.logger.info(
                        f"Updated library {libName} successfully."
                    )
                )
                updateLibraryRunner.signals.error.connect(
                    lambda e: self.appMainW.logger.error(
                        f"Error updating library {libName}: {e}"
                    )
                )
                self.appMainW.threadPool.start(updateLibraryRunner)
        return super().accept()
