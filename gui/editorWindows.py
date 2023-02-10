#   “Commons Clause” License Condition v1.0
#  #
#   The Software is provided to you by the Licensor under the License, as defined
#   below, subject to the following condition.
#  #
#   Without limiting other conditions in the License, the grant of rights under the
#   License will not include, and the License does not grant to you, the right to
#   Sell the Software.
#  #
#   For purposes of the foregoing, “Sell” means practicing any or all of the rights
#   granted to you under the License to provide to third parties, for a fee or other
#   consideration (including without limitation fees for hosting or consulting/
#   support services related to the Software), a product or service whose value
#   derives, entirely or substantially, from the functionality of the Software. Any
#   license notice or attribution required by the License must also include this
#   Commons Clause License Condition notice.
#  #
#   Software: Revolution EDA
#   License: Mozilla Public License 2.0
#   Licensor: Revolution Semiconductor (Registered in the Netherlands)

from copy import deepcopy
import datetime
import json
import math

# from hashlib import new
import pathlib
import shutil

# import numpy as np
from PySide6.QtCore import (QDir, Qt, QRect, QPoint, QMargins, QRectF, QProcess,
                            QRunnable, Signal, Slot)
from PySide6.QtGui import (QAction, QKeySequence, QColor, QIcon, QPainter, QPen,
                           QImage, QStandardItemModel, QCursor, QUndoStack,
                           QTextDocument, QGuiApplication, QCloseEvent, QFont,
                           QStandardItem)
from PySide6.QtPrintSupport import (QPrintDialog, )
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog,
                               QFormLayout, QGraphicsScene, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMenu, QMessageBox,
                               QToolBar, QTreeView, QVBoxLayout, QWidget,
                               QGraphicsRectItem, QGraphicsEllipseItem,
                               QGraphicsView, QGridLayout,
                               QGraphicsSceneMouseEvent, QAbstractItemView,
                               QTableView, QGroupBox, QComboBox)

import backend.schBackEnd as scb
import backend.undoStack as us
import backend.libraryMethods as libm
import common.layers as cel
import common.net as net
import common.pens as pens  # import pens
import common.shape as shp  # import the shapes
import fileio.loadJSON as lj
import fileio.symbolEncoder as se
import gui.fileDialogues as fd
import gui.propertyDialogues as pdlg
import gui.editFunctions as edf


class editorWindow(QMainWindow):
    """
    Base class for editor windows.
    """

    def __init__(self, viewItem: scb.viewItem, libraryDict: dict,
                 libraryView):  # file is a pathlib.Path object
        super().__init__()
        self.viewItem = viewItem
        self.file = self.viewItem.data(Qt.UserRole + 2)
        self.cellItem = self.viewItem.parent()
        self.cellName = self.cellItem.cellName
        self.libItem = self.cellItem.parent()
        self.libName = self.libItem.libraryName
        self.viewName = self.viewItem.viewName
        self.libraryDict = libraryDict
        self.libraryView = libraryView
        self.parentView = None
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
        self.majorGrid = 10  # snapping grid size
        self.gridTuple = (self.majorGrid, self.majorGrid)
        self.init_UI()

    def init_UI(self):
        """
        Placeholder for child classes init_UI function.
        """
        ...

    def _createMenuBar(self):
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

    def _createActions(self):
        checkCellIcon = QIcon(":/icons/document-task.png")
        self.checkCellAction = QAction(checkCellIcon, "Check-Save", self)

        self.readOnlyCellIcon = QIcon(":/icons/lock.png")
        self.readOnlyCellAction = QAction(self.readOnlyCellIcon, "Make Read Only",
                                          self)

        printIcon = QIcon(":/icons/printer--arrow.png")
        self.printAction = QAction(printIcon, "Print...", self)

        printPreviewIcon = QIcon(":/icons/printer--arrow.png")
        self.printPreviewAction = QAction(printPreviewIcon, "Print Preview...",
                                          self)

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
        self.selectConfigAction = QAction(selectConfigIcon, "Selection Config...",
                                          self)

        panZoomConfigIcon = QIcon(":/icons/selection-resize.png")
        self.panZoomConfigAction = QAction(panZoomConfigIcon,
                                           "Pan/Zoom Config...", self)

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
        self.viewPropAction = QAction(viewPropIcon, "Cellview Properties...",
                                      self)

        viewCheckIcon = QIcon(":/icons/ui-check-box.png")
        self.viewCheckAction = QAction(viewCheckIcon, "Check CellView", self)

        viewErrorsIcon = QIcon(":/icons/report--exclamation.png")
        self.viewErrorsAction = QAction(viewErrorsIcon, "View Errors...", self)

        deleteErrorsIcon = QIcon(":/icons/report--minus.png")
        self.deleteErrorsAction = QAction(deleteErrorsIcon, "Delete Errors...",
                                          self)

        netlistIcon = QIcon(":/icons/script-text.png")
        self.netlistAction = QAction(netlistIcon, "Create Netlist...", self)

        simulateIcon = QIcon(":/icons/application-wave.png")
        self.simulateAction = QAction(simulateIcon, "Run RevEDA Sim GUI", self)

        createLineIcon = QIcon(":/icons/layer-shape-line.png")
        self.createLineAction = QAction(createLineIcon, "Create Line...", self)

        createRectIcon = QIcon(":/icons/layer-shape.png")
        self.createRectAction = QAction(createRectIcon, "Create Rectangle...",
                                        self)

        createPolyIcon = QIcon(":/icons/layer-shape-polygon.png")
        self.createPolyAction = QAction(createPolyIcon, "Create Polygon...", self)

        createCircleIcon = QIcon(":/icons/layer-shape-ellipse.png")
        self.createCircleAction = QAction(createCircleIcon, "Create Circle...",
                                          self)

        createArcIcon = QIcon(":/icons/layer-shape-polyline.png")
        self.createArcAction = QAction(createArcIcon, "Create Arc...", self)

        createInstIcon = QIcon(":/icons/block--plus.png")
        self.createInstAction = QAction(createInstIcon, "Create Instance...",
                                        self)

        createWireIcon = QIcon(":/icons/node-insert.png")
        self.createWireAction = QAction(createWireIcon, "Create Wire...", self)

        createBusIcon = QIcon(":/icons/node-select-all.png")
        self.createBusAction = QAction(createBusIcon, "Create Bus...", self)

        createLabelIcon = QIcon(":/icons/tag-label-yellow.png")
        self.createLabelAction = QAction(createLabelIcon, "Create Label...", self)

        createPinIcon = QIcon(":/icons/pin--plus.png")
        self.createPinAction = QAction(createPinIcon, "Create Pin...", self)

        createSymbolIcon = QIcon(":/icons/application-block.png")
        self.createSymbolAction = QAction(createSymbolIcon, "Create Symbol...",
                                          self)

        createTextIcon = QIcon(":icons/sticky-note-text.png")
        self.createTextAction = QAction(createTextIcon, "Create Text...", self)

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
        self.menuFile.addAction(self.readOnlyCellAction)
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
        self.printAction.triggered.connect(self.printClick)
        # self.printPreviewAction.triggered.connect(self.printPreviewClick)
        self.exportImageAction.triggered.connect(self.imageExportClick)
        self.exitAction.triggered.connect(self.closeWindow)
        self.fitAction.triggered.connect(self.fitToWindow)
        self.zoomInAction.triggered.connect(self.zoomIn)
        self.zoomOutAction.triggered.connect(self.zoomOut)
        self.dispConfigAction.triggered.connect(self.dispConfDialog)
        self.moveOriginAction.triggered.connect(self.moveOrigin)

    def _createShortcuts(self):
        self.redoAction.setShortcut("Shift+U")
        self.undoAction.setShortcut(Qt.Key_U)
        self.objPropAction.setShortcut(Qt.Key_Q)
        self.copyAction.setShortcut("C")
        self.rotateAction.setShortcut("Ctrl+R")
        self.createTextAction.setShortcut("Shift+L")
        self.deleteAction.setShortcut(QKeySequence.Delete)

    def dispConfDialog(self):
        dcd = pdlg.displayConfigDialog(self)
        dlg.majorGridEntry.setText(str(self.majorGrid))
        if dcd.exec() == QDialog.Accepted:
            self.majorGrid = int(float(dcd.majorGridEntry.text()))

    def printClick(self):
        dlg = QPrintDialog(self)
        if dlg.exec() == QDialog.Accepted:
            printer = dlg.printer()
            self.centralW.view.printView(printer)

    # def printPreviewClick(self):
    #     # dlg = QPrintDialog(self)
    #     # if dlg.exec() == QDialog.Accepted:
    #     #     printer = dlg.printer()
    #     printer = QPrinter(QPrinter.ScreenResolution)
    #
    #     ppdlg = QPrintPreviewDialog(self)
    #     ppdlg.paintRequested.connect(self.centralW.scene.render(QPainter(printer)))
    #     ppdlg.exec()
    def imageExportClick(self):
        image = QImage(self.centralW.view.viewport().size(),
                       QImage.Format_ARGB32_Premultiplied)
        self.centralW.view.printView(image)
        fdlg = QFileDialog(self, caption="Select or create an image file")
        fdlg.setDefaultSuffix("png")
        fdlg.setFileMode(QFileDialog.AnyFile)
        fdlg.setViewMode(QFileDialog.Detail)
        fdlg.setNameFilter("Image Files (*.png *.jpg *.bmp *.gif *.jpeg")
        if fdlg.exec() == QDialog.Accepted:
            imageFile = fdlg.selectedFiles()[0]
        image.save(imageFile)

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

    def moveOrigin(self):
        self.centralW.scene.changeOrigin = True


class schematicEditor(editorWindow):
    def __init__(self, viewItem: scb.viewItem, libraryDict: dict,
                 libraryView) -> None:
        super().__init__(viewItem, libraryDict, libraryView)
        self.setWindowTitle(f"Schematic Editor - {self.cellName}")
        self.setWindowIcon(QIcon(":/icons/layer-shape.png"))
        self.configDict = dict()
        self.netlistedCells = list()
        self.symbolChooser = None
        self.cellViews = [
            "symbol"]  # only symbol can be instantiated in the schematic window.
        self._schematicActions()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = schematicContainer(self)
        self.setCentralWidget(self.centralW)

    def _createTriggers(self):
        super()._createTriggers()
        self.checkCellAction.triggered.connect(self.checkSaveCell)
        self.createWireAction.triggered.connect(self.createWireClick)
        self.createInstAction.triggered.connect(self.createInstClick)
        self.createPinAction.triggered.connect(self.createPinClick)
        self.createTextAction.triggered.connect(self.createNoteClick)
        self.createSymbolAction.triggered.connect(self.createSymbolClick)
        self.copyAction.triggered.connect(self.copyClick)
        self.deleteAction.triggered.connect(self.deleteClick)
        self.objPropAction.triggered.connect(self.objPropClick)
        self.undoAction.triggered.connect(self.undoClick)
        self.redoAction.triggered.connect(self.redoClick)
        self.netlistAction.triggered.connect(self.createNetlistClick)
        self.rotateAction.triggered.connect(self.rotateItemClick)
        self.simulateAction.triggered.connect(self.startSimClick)
        self.goDownAction.triggered.connect(self.goDownClick)
        self.goUpAction.triggered.connect(self.goUpClick)

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
        self.menuCreate.addAction(self.createTextAction)
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
        # self.schematicToolbar.addAction(self.createLabelAction)
        self.schematicToolbar.addAction(self.createSymbolAction)
        self.schematicToolbar.addSeparator()
        self.schematicToolbar.addAction(self.viewCheckAction)

    def _schematicActions(self):
        self.centralW.scene.itemContextMenu.addAction(self.copyAction)
        self.centralW.scene.itemContextMenu.addAction(self.moveAction)
        self.centralW.scene.itemContextMenu.addAction(self.rotateAction)
        self.centralW.scene.itemContextMenu.addAction(self.deleteAction)
        self.centralW.scene.itemContextMenu.addAction(self.objPropAction)
        self.centralW.scene.itemContextMenu.addAction(self.goDownAction)
        if self.parentView is not None:
            self.centralW.scene.itemContextMenu.addAction(self.goUpAction)

    def _createShortcuts(self):
        super()._createShortcuts()
        self.createInstAction.setShortcut(Qt.Key_I)
        self.createWireAction.setShortcut(Qt.Key_W)
        self.createPinAction.setShortcut(Qt.Key_P)

    def createWireClick(self, s):
        self.centralW.scene.drawWire = True

    def deleteClick(self, s):
        self.centralW.scene.deleteSelectedItems()

    def createInstClick(self, s):

        # create a designLibrariesView
        libraryModel = symbolViewsModel(self.libraryDict)
        if self.symbolChooser is None:
            self.symbolChooser = fd.selectCellViewDialog(self, libraryModel)
            self.symbolChooser.show()
        else:
            self.symbolChooser.raise_()
        if self.symbolChooser.exec() == QDialog.Accepted:
            self.centralW.scene.addInstance = True
            libItem = libm.getLibItem(libraryModel,
                                      self.symbolChooser.libNamesCB.currentText())
            cellItem = libm.getCellItem(libItem,
                                        self.symbolChooser.cellCB.currentText())
            viewItem = libm.getViewItem(cellItem,
                                        self.symbolChooser.viewCB.currentText())
            self.centralW.scene.instanceSymbolFile = viewItem.data(
                Qt.UserRole + 2)

    def createPinClick(self, s):
        createPinDlg = pdlg.createSchematicPinDialog(self)
        if createPinDlg.exec() == QDialog.Accepted:
            self.centralW.scene.pinName = createPinDlg.pinName.text()
            self.centralW.scene.pinType = createPinDlg.pinType.currentText()
            self.centralW.scene.pinDir = createPinDlg.pinDir.currentText()
            self.centralW.scene.drawPin = True

    def createNoteClick(self, s):
        textDlg = pdlg.noteTextEdit(self)
        if textDlg.exec() == QDialog.Accepted:
            self.centralW.scene.noteText = textDlg.plainTextEdit.toPlainText()
            self.centralW.scene.noteFontFamily = textDlg.familyCB.currentText()
            self.centralW.scene.noteFontSize = textDlg.fontsizeCB.currentText()
            self.centralW.scene.noteFontStyle = textDlg.fontStyleCB.currentText()
            self.centralW.scene.noteAlign = textDlg.textAlignmCB.currentText()
            self.centralW.scene.noteOrient = textDlg.textOrientCB.currentText()
            self.centralW.scene.drawText = True

    def createSymbolClick(self, s):
        self.centralW.scene.createSymbol()

    def undoClick(self, s):
        self.centralW.scene.undoStack.undo()

    def redoClick(self, s):
        self.centralW.scene.undoStack.redo()

    def objPropClick(self, s):
        self.centralW.scene.viewObjProperties()

    def copyClick(self, s):
        self.centralW.scene.copySelectedItems()

    def rotateItemClick(self, s):
        self.centralW.scene.rotateItem = True
        self.centralW.scene.itemSelect = False

    def startSimClick(self, s):
        simguiw = revedasim.simGUImainWindow(self)
        simguiw.show()

    def checkSaveCell(self):
        self.centralW.scene.saveSchematicCell(self.file)

    def loadSchematic(self):
        with open(self.file) as tempFile:
            items = json.load(tempFile)
        self.centralW.scene.loadSchematicCell(items)

    def createConfigView(self, configItem: scb.viewItem, configDict: dict,
                         newConfigDict: dict, netlistedCells: set):

        sceneSymbolSet = self.centralW.scene.findSceneSymbolSet()
        for item in sceneSymbolSet:
            libItem = libm.getLibItem(self.libraryView.libraryModel,
                                      item.libraryName)
            cellItem = libm.getCellItem(libItem, item.cellName)
            viewItems = [cellItem.child(row) for row in
                         range(cellItem.rowCount())]
            viewNames = [viewItem.viewName for viewItem in viewItems]
            netlistableViews = [viewItemName for viewItemName in
                                self.switchViewList if viewItemName in viewNames]
            itemSwitchViewList = deepcopy(netlistableViews)
            viewDict = dict(zip(viewNames, viewItems))
            if cellItem.cellName not in netlistedCells:
                cellLine = configDict.get(cellItem.cellName)
                if cellLine:
                    netlistableViews = [cellLine[1]]
                for viewName in netlistableViews:
                    match viewDict[viewName].viewType:
                        case "schematic":
                            newConfigDict.update({
                                cellItem.cellName: [libItem.libraryName, viewName,
                                                    itemSwitchViewList, ]})
                            schematicObj = schematicEditor(viewDict[viewName],
                                                           self.libraryDict,
                                                           self.libraryView, )
                            schematicObj.loadSchematic()
                            schematicObj.createConfigView(configItem, configDict,
                                                          newConfigDict,
                                                          netlistedCells)
                            break
                        case other:
                            newConfigDict.update({
                                cellItem.cellName: [libItem.libraryName, viewName,
                                                    itemSwitchViewList, ]})
                            break
                netlistedCells.append(cellItem.cellName)

    def closeEvent(self, event):
        self.centralW.scene.saveSchematicCell(self.file)
        self.libraryView.openViews.pop(
            f"{self.libName}_{self.cellName}_{self.viewName}")
        event.accept()

    def createNetlistClick(self, s):
        dlg = fd.netlistExportDialogue(self)
        dlg.libNameEdit.setText(self.libName)
        dlg.cellNameEdit.setText(self.cellName)
        configViewItems = [self.cellItem.child(row) for row in
                           range(self.cellItem.rowCount()) if
                           self.cellItem.child(row).viewType == 'config']
        netlistableViews = [self.viewItem.viewName]
        for item in configViewItems:
            # is there a better way of doing it?
            with item.data(Qt.UserRole + 2).open(mode='r') as f:
                configItems = json.load(f)
                if configItems[1]['reference'] == self.viewItem.viewName:
                    netlistableViews.append(item.viewName)
        dlg.viewNameCombo.addItems(netlistableViews)
        if hasattr(self.appMainW, "simulationPath"):
            dlg.netlistDirEdit.setText(str(self.appMainW.simulationPath))
        if dlg.exec() == QDialog.Accepted:
            self.netlistDir = dlg.netlistDirEdit.text()
            selectedViewName = dlg.viewNameCombo.currentText()
            self.switchViewList = [item.strip() for item in
                                   dlg.switchViewEdit.text().split(",")]
            self.stopViewList = [dlg.stopViewEdit.text().strip()]
            simDirPathObj = pathlib.Path(self.netlistDir)
            subDirPathObj = simDirPathObj.joinpath(self.cellName)
            subDirPathObj.mkdir(parents=True, exist_ok=True)
            netlistFilePathObj = subDirPathObj.joinpath(f'{self.cellName}_'
                                                        f'{selectedViewName}').with_suffix(
                '.cir')
            if 'schematic' in dlg.viewNameCombo.currentText():
                netlistObj = xyceNetlist(self, netlistFilePathObj)
            else:
                netlistObj = xyceNetlist(self, netlistFilePathObj, True)
                configItem = libm.findViewItem(self.libraryView.libraryModel,
                                               self.libName, self.cellName,
                                               dlg.viewNameCombo.currentText())
                with configItem.data(Qt.UserRole + 2).open(mode='r') as f:
                    netlistObj.configDict = json.load(f)[2]
            xyceNetlRunner = runXNetlistThread(netlistObj, self)
            self.logger.info('Writing netlist')
            self.appMainW.threadPool.start(xyceNetlRunner)

    def goDownClick(self, s):
        self.centralW.scene.goDownHier()

    def goUpClick(self, s):
        self.centralW.scene.goUpHier()


class symbolEditor(editorWindow):
    def __init__(self, viewItem: scb.viewItem, libraryDict: dict, libraryView):
        super().__init__(viewItem, libraryDict, libraryView)
        self.setWindowTitle(f"Symbol Editor - {self.cellName}")
        self._symbolActions()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = symbolContainer(self)
        self.setCentralWidget(self.centralW)

    def _createActions(self):
        super()._createActions()

    def _createShortcuts(self):
        super()._createShortcuts()
        self.stretchAction.setShortcut(Qt.Key_M)
        self.createRectAction.setShortcut(Qt.Key_R)
        self.createLineAction.setShortcut(Qt.Key_W)
        self.createLabelAction.setShortcut(Qt.Key_L)

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
        self.rotateAction.triggered.connect(self.rotateItemClick)
        self.deleteAction.triggered.connect(self.deleteClick)
        self.stretchAction.triggered.connect(self.stretchClick)
        self.viewPropAction.triggered.connect(self.viewPropClick)
        super()._createTriggers()

    def _symbolActions(self):
        self.centralW.scene.itemContextMenu.addAction(self.copyAction)
        self.centralW.scene.itemContextMenu.addAction(self.moveAction)
        self.centralW.scene.itemContextMenu.addAction(self.rotateAction)
        self.centralW.scene.itemContextMenu.addAction(self.stretchAction)
        self.centralW.scene.itemContextMenu.addAction(self.deleteAction)
        self.centralW.scene.itemContextMenu.addAction(self.objPropAction)

    def objPropClick(self):
        self.centralW.scene.itemProperties()

    def checkSaveCell(self):
        self.centralW.scene.saveSymbolCell(self.file)

    def createRectClick(self, s):
        self.setDrawMode(False, False, False, True, False, False, False)

    def createLineClick(self, s):
        self.setDrawMode(False, False, False, False, True, False, False)

    def createPolyClick(self, s):
        pass

    def createArcClick(self, s):
        self.setDrawMode(False, False, True, False, False, False, False)

    def createCircleClick(self, s):
        self.setDrawMode(False, False, False, False, False, False, True)

    def createPinClick(self, s):
        createPinDlg = pdlg.createPinDialog(self)
        if createPinDlg.exec() == QDialog.Accepted:
            self.centralW.scene.pinName = createPinDlg.pinName.text()
            self.centralW.scene.pinType = createPinDlg.pinType.currentText()
            self.centralW.scene.pinDir = createPinDlg.pinDir.currentText()
            self.setDrawMode(True, False, False, False, False, False, False)

    def rotateItemClick(self, s):
        self.centralW.scene.rotateItem = True
        self.centralW.scene.selectItem = False
        self.messageLine.setText("Click on an item to rotate CW 90 degrees.")

    def undoClick(self, s):
        self.centralW.scene.undoStack.undo()

    def redoClick(self, s):
        self.centralW.scene.undoStack.redo()

    def deleteClick(self, s):
        self.centralW.scene.deleteSelectedItems()

    def copyClick(self, s):
        self.centralW.scene.copySelectedItems()

    def stretchClick(self, s):
        self.centralW.scene.stretchSelectedItem()

    def viewPropClick(self, s):
        self.centralW.scene.viewSymbolProperties()

    def setDrawMode(self, *args):
        """
        Sets the drawing mode in the symbol editor.
        """
        self.centralW.scene.drawPin = args[0]
        self.centralW.scene.selectItem = args[1]
        self.centralW.scene.drawArc = args[2]  # draw arc
        self.centralW.scene.drawRect = args[3]  # draw rect
        self.centralW.scene.drawLine = args[4]  # draw line
        self.centralW.scene.addLabel = args[5]
        self.centralW.scene.drawCircle = args[6]
        if hasattr(self.centralW.scene, "start"):
            del self.centralW.scene.start

    def loadSymbol(self):
        """
        symbol is loaded to the scene.
        """
        with open(self.file) as tempFile:
            items = json.load(tempFile)
        self.centralW.scene.loadSymbol(items)

    def createSymbolLabelDialogue(self):
        createLabelDlg = pdlg.createSymbolLabelDialog(self)
        if createLabelDlg.exec() == QDialog.Accepted:
            self.setDrawMode(False, False, False, False, False, True, False)
            # directly setting scene class attributes here to pass the information.
            self.centralW.scene.labelDefinition = createLabelDlg.labelDefinition.text()
            self.centralW.scene.labelHeight = (
                createLabelDlg.labelHeightEdit.text().strip())
            self.centralW.scene.labelAlignment = (
                createLabelDlg.labelAlignCombo.currentText())
            self.centralW.scene.labelOrient = (
                createLabelDlg.labelOrientCombo.currentText())
            self.centralW.scene.labelUse = createLabelDlg.labelUseCombo.currentText()
            if createLabelDlg.labelVisiCombo.currentText() == "Yes":
                self.centralW.scene.labelOpaque = True
            else:
                self.centralW.scene.labelOpaque = False
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
        self.appMainW.openViews.pop(
            f"{self.libName}_{self.cellName}_{self.viewName}")
        event.accept()


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


class editor_scene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.editor = self.parent.parent
        self.majorGrid = self.editor.majorGrid
        self.gridTuple = self.editor.gridTuple
        self.selectedItems = None  # selected item
        self.defineSceneLayers()
        self.setPens()
        self.undoStack = QUndoStack()
        self.changeOrigin = False
        self.origin = QPoint(0, 0)
        self.cellName = self.editor.file.parent.stem
        self.libraryDict = self.editor.libraryDict
        self.rotateItem = False
        self.itemContextMenu = QMenu()
        self.appMainW = self.editor.appMainW
        self.logger = self.appMainW.logger
        self.messageLine = self.editor.messageLine
        self.statusLine = self.editor.statusLine

    def setPens(self):
        self.wirePen = pens.pen.returnPen("wirePen")
        self.symbolPen = pens.pen.returnPen("symbolPen")
        self.selectedWirePen = pens.pen.returnPen("selectedWirePen")
        self.pinPen = pens.pen.returnPen("pinPen")
        self.labelPen = pens.pen.returnPen("labelPen")
        self.textPen = pens.pen.returnPen("textPen")

    def defineSceneLayers(self):
        self.wireLayer = cel.wireLayer
        self.symbolLayer = cel.symbolLayer
        self.guideLineLayer = cel.guideLineLayer
        self.selectedWireLayer = cel.selectedWireLayer
        self.pinLayer = cel.pinLayer
        self.labelLayer = cel.labelLayer
        self.textLayer = cel.textLayer

    def snapToBase(self, number, base):
        '''
        Restrict a number to the multiples of base
        '''
        return int(base * int(round(number / base)))

    def snapToGrid(self, point: QPoint, gridTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(int(gridTuple[0] * int(round(point.x() / gridTuple[0]))),
                      int(gridTuple[1] * int(round(point.y() / gridTuple[1]))))

    def rotateSelectedItems(self, point: QPoint):
        """
        Rotate selected items by 90 degree.
        """
        for item in self.selectedItems:
            self.rotateAnItem(point, item, 90)
        self.rotateItem = False
        self.itemSelect = True

    def rotateAnItem(self, point: QPoint, item, angle):
        rotationOriginPoint = item.mapFromScene(point)
        item.setTransformOriginPoint(rotationOriginPoint)
        item.angle += angle
        item.setRotation(item.angle)
        undoCommand = us.undoRotateShape(self, item, item.angle)
        self.undoStack.push(undoCommand)


class symbol_scene(editor_scene):
    """
    Scene for Symbol editor.
    """

    def __init__(self, parent):
        super().__init__(parent)
        # drawing switches
        self.resetSceneMode()  # reset to select mode
        # pen definitions
        self.setPens()
        self.draftPen = QPen(self.guideLineLayer.color, 1)
        self.drawPin = False
        self.itemSelect = True
        self.drawArc = False  # draw arc
        self.drawRect = False
        self.drawLine = False
        self.addLabel = False
        self.drawCircle = False
        self.drawMode = (
                self.drawLine or self.drawArc or self.drawRect or self.drawCircle)
        self.symbolShapes = ["line", "arc", "rect", "circle", "pin", "label"]
        self.changeOrigin = False
        self.origin = QPoint(0, 0)
        # some default attributes
        self.pinName = ""
        self.pinType = shp.pin.pinTypes[0]
        self.pinDir = shp.pin.pinDirs[0]
        self.labelDefinition = ""
        self.labelType = shp.label.labelTypes[0]
        self.labelOrient = shp.label.labelOrients[0]
        self.labelAlignment = shp.label.labelAlignments[0]
        self.labelUse = shp.label.labelUses[0]
        self.labelVisible = False
        self.labelHeight = "12"
        self.labelOpaque = True

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(mouse_event)
        if mouse_event.button() == Qt.LeftButton:
            eventScenePos = mouse_event.scenePos()
            self.start = self.snapToGrid(eventScenePos.toPoint(), self.gridTuple)
            if self.changeOrigin:  # change origin of the symbol
                self.origin = self.start
            if self.itemSelect:
                self.messageLine.setText("Select an item")
                #     # find the view rectangle every time mouse is pressed.
                self.viewRect = self.parent.view.mapToScene(
                    self.parent.view.viewport().rect()).boundingRect()
                itemsAtMousePress = self.items(eventScenePos)
                if itemsAtMousePress:
                    self.selectedItems = [item for item in itemsAtMousePress if
                                          item.isSelected()]
                    self.messageLine.setText("Item selected")
                else:
                    self.selectedItems = None
                    self.parent.parent.messageLine.setText("Nothing selected")
            if self.drawPin:
                if hasattr(self, "draftPin"):
                    self.removeItem(self.draftPin)
                self.draftPin = shp.pin(self.start, self.draftPen, "", "Input",
                                        "Signal", self.gridTuple, )
                self.addItem(self.draftPin)
                self.draftPin.setSelected(True)
            if self.addLabel:
                if hasattr(self, "draftLabel"):
                    self.removeItem(self.draftLabel)
                self.draftLabel = shp.label(self.start, self.draftPen, "12",
                                            self.gridTuple, )
                self.addItem(self.draftLabel)
                self.draftLabel.setSelected(True)
            if self.rotateItem:
                if self.selectedItems:
                    self.rotateSelectedItems(self.start)

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(mouse_event)
        eventScenePos = mouse_event.scenePos()
        self.current = self.snapToGrid(eventScenePos.toPoint(), self.gridTuple)
        modifiers = QGuiApplication.keyboardModifiers()
        if mouse_event.buttons() == Qt.LeftButton:
            if hasattr(self, "draftItem"):
                self.removeItem(self.draftItem)
                del self.draftItem
            # if hasattr(self, "draftRect"):
            #     self.removeItem(self.draftRect)
            if self.drawLine and hasattr(self, "start"):
                self.parent.parent.messageLine.setText("Line Mode")
                self.draftItem = shp.line(self.start, self.current, self.draftPen,
                                          self.gridTuple)
                self.addItem(self.draftItem)
            if self.drawRect and hasattr(self, "start"):
                self.draftItem = shp.rectangle(self.start, self.current,
                                               self.draftPen, self.gridTuple)
                self.addItem(self.draftItem)
            if self.drawCircle and hasattr(self, "start"):
                xlen = abs(self.current.x() - self.start.x())
                ylen = abs(self.current.y() - self.start.y())
                length = math.sqrt(xlen ** 2 + ylen ** 2)
                self.draftItem = QGraphicsEllipseItem(
                    QRectF(self.start - QPoint(int(length), int(length)),
                           self.start + QPoint(int(length), int(length)), ))
                self.draftItem.setPen(self.draftPen)
                self.addItem(self.draftItem)
            if self.drawArc and hasattr(self, "start"):
                self.draftItem = shp.arc(self.start, self.current, self.draftPen,
                                         self.gridTuple)
                # self.draftRect = shp.rectangle(self.start,self.current, self.draftPen,
                #                                self.gridTuple)
                self.addItem(self.draftItem)  # self.addItem(self.draftRect)
            if self.itemSelect:
                if modifiers == Qt.ShiftModifier:
                    self.draftItem = QGraphicsRectItem(
                        QRect.span(self.start, self.current))
                    self.draftItem.setPen(self.draftPen)
                    self.addItem(self.draftItem)
                    self.messageLine.setText("Select an Area")

        self.statusLine.showMessage(
            "Cursor Position: " + str((self.current - self.origin).toTuple()))

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        eventScenePos = mouse_event.scenePos()
        self.current = self.snapToGrid(eventScenePos.toPoint(), self.gridTuple)
        if mouse_event.button() == Qt.LeftButton:
            if (self.itemSelect and hasattr(self, "draftItem") and isinstance(
                    self.draftItem, QGraphicsRectItem)):
                self.selectedItems = [item for item in
                                      self.items(self.draftItem.rect(),
                                                 mode=Qt.IntersectsItemBoundingRect)]
                for item in self.selectedItems:
                    item.setSelected(True)
            if self.drawLine and hasattr(self, "start"):
                self.lineDraw(self.start, self.current, self.symbolPen,
                              self.gridTuple)

            if self.drawRect and hasattr(self, "start"):
                self.rectDraw(self.start, self.current, self.symbolPen,
                              self.gridTuple)

            if self.drawCircle and hasattr(self, "start"):
                self.circleDraw(self.start, self.current, self.symbolPen,
                                self.gridTuple)

            if self.drawArc and hasattr(self, 'start'):
                self.arcDraw(self.start, self.current, self.symbolPen,
                             self.gridTuple)
            if self.drawPin and hasattr(self, "draftPin"):
                self.pinDraw(self.current, self.pinPen, self.pinName, self.pinDir,
                             self.pinType, self.gridTuple, )  # draw pin

            if self.addLabel and hasattr(self, "draftLabel"):
                self.labelDraw(self.current, self.labelPen, self.labelDefinition,
                               self.gridTuple, self.labelType, self.labelHeight,
                               self.labelAlignment, self.labelOrient,
                               self.labelUse, )  # draw label

            if hasattr(self, "draftItem"):
                self.removeItem(self.draftItem)
                del self.draftItem
            elif hasattr(self, "draftPin"):
                self.removeItem(self.draftPin)
                del self.draftPin
            elif hasattr(self, "draftLabel"):
                self.removeItem(self.draftLabel)
                del self.draftLabel  # if hasattr(self,"draftRect"):  #     self.removeItem(self.draftRect)  # del self.draftRect
            if self.changeOrigin:
                self.changeOrigin = False
            self.itemSelect = True

    def lineDraw(self, start: QPoint, current: QPoint, pen: QPen,
                 gridTuple: tuple):
        line = shp.line(start, current, pen, gridTuple)
        self.addItem(line)
        undoCommand = us.addShapeUndo(self, line)
        self.undoStack.push(undoCommand)
        self.drawLine = False
        return line

    def rectDraw(self, start: QPoint, end: QPoint, pen: QPen, gridTuple: tuple):
        """
        Draws a rectangle on the scene
        """
        rect = shp.rectangle(start,
                             end - QPoint(pen.width() / 2, pen.width() / 2), pen,
                             gridTuple)
        self.addItem(rect)
        undoCommand = us.addShapeUndo(self, rect)
        self.undoStack.push(undoCommand)
        self.drawRect = False
        return rect

    def circleDraw(self, start: QPoint, end: QPoint, pen: QPen,
                   gridTuple: tuple[int, int]):
        """
        Draws a circle on the scene
        """
        snappedEnd = self.snapToGrid(end, gridTuple)
        circle = shp.circle(start, snappedEnd, pen, gridTuple)
        self.addItem(circle)
        undoCommand = us.addShapeUndo(self, circle)
        self.undoStack.push(undoCommand)
        self.drawCircle = False
        return circle

    def arcDraw(self, start: QPoint, end: QPoint, pen: QPen,
                gridTuple: tuple[int, int]):
        '''
        Draws an arc inside the rectangle defined by start and end points.
        '''
        arc = shp.arc(start, end, pen, gridTuple)
        self.addItem(arc)
        undoCommand = us.addShapeUndo(self, arc)
        self.undoStack.push(undoCommand)
        self.drawArc = False
        return arc

    def pinDraw(self, current, pen: QPen, pinName: str, pinDir, pinType,
                gridTuple: tuple):
        pin = shp.pin(current, pen, pinName, pinDir, pinType, gridTuple)
        self.addItem(pin)
        undoCommand = us.addShapeUndo(self, pin)
        self.undoStack.push(undoCommand)
        self.drawPin = False
        return pin

    def labelDraw(self, current, pen: QPen, labelDefinition, gridTuple, labelType,
                  labelHeight, labelAlignment, labelOrient, labelUse, ):
        label = shp.label(current, pen, labelDefinition, gridTuple, labelType,
                          labelHeight, labelAlignment, labelOrient, labelUse, )
        label.labelVisible = self.labelOpaque
        label.setLabelName()  # set the name
        label.setOpacity(1)
        self.addItem(label)
        undoCommand = us.addShapeUndo(self, label)
        self.undoStack.push(undoCommand)
        self.addLabel = False
        return label

    def keyPressEvent(self, key_event):
        super().keyPressEvent(key_event)
        if key_event.key() == Qt.Key_Escape:
            self.resetSceneMode()
        elif key_event.key() == Qt.Key_C:
            self.copySelectedItems()
        elif key_event.key() == Qt.Key_M:
            self.stretchSelectedItem()  # elif key_event.key() == Qt.Key_Up:  #     selectedItemsCount = len(self.itemsAtMousePress)  #     if self.selectCount == selectedItemsCount:  #         self.selectCount = 0  #         self.changeSelection(self.selectCount)  #         self.selectCount += 1  #     elif self.selectCount < selectedItemsCount:  #         self.changeSelection(self.selectCount)  #         self.selectCount += 1

    # def changeSelection(self, i):
    #     """
    #     Change the selected item.
    #     """
    #     self.selectedItem.setSelected(False)
    #     self.selectedItem = self.itemsAtMousePress[i]
    #     self.selectedItem.setSelected(True)

    def resetSceneMode(self):
        """
        Reset the scene mode to default. Select mode is set to True.
        """
        self.drawItem = False  # flag to indicate if an item is being drawn
        self.drawLine = False  # flag to indicate if a line is being drawn
        self.drawArc = False  # flag to indicate if an arc is being drawn
        self.drawPin = False  # flag to indicate if a pin is being drawn
        self.drawRect = False  # flag to indicate if a rectangle is being drawn
        self.addLabel = False  # flag to indicate if a label is being drawn
        self.selectCount = 0  # index of item selected
        self.selectedItems = None
        if hasattr(self, "draftItem"):
            self.removeItem(self.draftItem)
        self.itemSelect = True

    def deleteSelectedItems(self):
        if self.selectedItems:
            for item in self.selectedItems:
                self.removeItem(item)
            del self.selectedItems
            self.update()
            self.itemSelect = True

    def copySelectedItems(self):
        if hasattr(self, "selectedItems"):
            for item in self.selectedItems:
                selectedItemJson = json.dumps(item, cls=se.symbolEncoder)
                itemCopyDict = json.loads(selectedItemJson)
                shape = lj.createSymbolItems(itemCopyDict, self.gridTuple)
                self.addItem(shape)
                undoCommand = us.addShapeUndo(self, shape)
                self.undoStack.push(undoCommand)
                # shift position by one grid unit to right and down
                shape.setPos(QPoint(item.pos().x() + 2 * self.gridTuple[0],
                                    item.pos().y() + 2 * self.gridTuple[1], ))

    def itemProperties(self):
        """
        When item properties is queried.
        """
        if self.selectedItems:
            for item in self.selectedItems:
                if isinstance(item, shp.rectangle):
                    self.queryDlg = pdlg.rectPropertyDialog(self.editor, item)
                    if self.queryDlg.exec() == QDialog.Accepted:
                        self.updateRectangleShape(item)
                if isinstance(item, shp.circle):
                    self.queryDlg = pdlg.circlePropertyDialog(self.editor, item)
                    if self.queryDlg.exec() == QDialog.Accepted:
                        self.updateCircleShape(item)
                if isinstance(item, shp.arc):
                    self.queryDlg = pdlg.arcPropertyDialog(self.editor, item)
                    if self.queryDlg.exec() == QDialog.Accepted:
                        self.updateArcShape(item)
                elif isinstance(item, shp.line):
                    self.queryDlg = pdlg.linePropertyDialog(self.editor, item)
                    if self.queryDlg.exec() == QDialog.Accepted:
                        self.updateLineShape(item)
                elif isinstance(item, shp.pin):
                    self.queryDlg = pdlg.pinPropertyDialog(self.editor, item)
                    if self.queryDlg.exec() == QDialog.Accepted:
                        self.updatePinShape(item)
                elif isinstance(item, shp.label):
                    self.queryDlg = pdlg.labelPropertyDialog(self.editor, item)
                    if self.queryDlg.exec() == QDialog.Accepted:
                        self.updateLabelShape(item)

    def updateRectangleShape(self, item: shp.rectangle):
        left = self.snapToBase(float(self.queryDlg.rectLeftLine.text()),
                               self.gridTuple[0])
        top = self.snapToBase(float(self.queryDlg.rectTopLine.text()),
                              self.gridTuple[1])
        width = self.snapToBase(float(self.queryDlg.rectWidthLine.text()),
                                self.gridTuple[0])
        height = self.snapToBase(float(self.queryDlg.rectHeightLine.text()),
                                 self.gridTuple[1])
        topLeft = item.mapFromScene(QPoint(left, top))
        # undoUpdateRectangle = us.updateShapeUndo()
        # us.keepOriginalShape(self, item, self.gridTuple, parent=undoUpdateRectangle)
        item.rect = QRect(topLeft.x(), topLeft.y(), width, height)

        # us.changeOriginalShape(self, item, parent=undoUpdateRectangle)
        # self.undoStack.push(undoUpdateRectangle)
        # self.selectedItem.update()

    def updateCircleShape(self, item: shp.circle):

        centerX = self.snapToBase(float(self.queryDlg.centerXEdit.text()),
                                  self.gridTuple[0])
        centerY = self.snapToBase(float(self.queryDlg.centerYEdit.text()),
                                  self.gridTuple[1])
        radius = self.snapToBase(float(self.queryDlg.radiusEdit.text()),
                                 self.gridTuple[0])
        centerPoint = self.snapToGrid(QPoint(centerX, centerY), self.gridTuple)
        item.centre(self.selectedItem.mapFromScene(centerPoint))
        item.radius(radius)

    def updateArcShape(self, item: shp.arc):

        startX = self.snapToBase(float(self.queryDlg.startXEdit.text()),
                                 self.gridTuple[0])
        startY = self.snapToBase(float(self.queryDlg.startYEdit.text()),
                                 self.gridTuple[1])
        item.start = item.mapFromScene(QPoint(startX, startY)).toPoint()
        item.width = self.snapToBase(float(self.queryDlg.widthEdit.text()),
                                     self.gridTuple[0])
        item.height = self.snapToBase(float(self.queryDlg.heightEdit.text()),
                                      self.gridTuple[1])

    def updateLineShape(self, item: shp.line):
        """
        Updates line shape from dialogue entries.
        """
        startEntry = QPoint(int(float(self.queryDlg.startXLine.text())),
                            int(float(self.queryDlg.startYLine.text())), )
        item.start = item.mapFromScene(startEntry).toPoint()
        endEntry = QPoint(int(float(self.queryDlg.endXLine.text())),
                          int(float(self.queryDlg.endYLine.text())), )
        item.end = item.mapFromScene(endEntry).toPoint()

    def updatePinShape(self, item: shp.pin):
        location = item.scenePos().toTuple()
        item.start = self.snapToGrid(
            QPoint(int(float(self.queryDlg.pinXLine.text()) - float(location[0])),
                   int(float(self.queryDlg.pinYLine.text()) - float(
                       location[1])), ), self.gridTuple, )
        item.rect = QRect(self.selectedItem.start.x() - 5,
                          self.selectedItem.start.y() - 5, 10, 10)
        item.pinName = self.queryDlg.pinName.text()
        item.pinType = self.queryDlg.pinType.currentText()
        item.pinDir = self.queryDlg.pinDir.currentText()
        item.update()

    def updateLabelShape(self, item: shp.label):
        """
        update pin shape with new values.
        """
        location = item.scenePos().toTuple()
        item.start = self.snapToGrid(
            QPoint(int(float(self.queryDlg.labelXLine.text()) - float(location[0])),
                   int(float(self.queryDlg.labelYLine.text()) - float(
                       location[1])), ), self.gridTuple, )
        item.labelDefinition = self.queryDlg.labelDefinition.text()
        item.labelHeight = self.queryDlg.labelHeightEdit.text()
        item.labelAlign = self.queryDlg.labelAlignCombo.currentText()
        item.labelOrient = self.queryDlg.labelOrientCombo.currentText()
        item.labelUse = self.queryDlg.labelUseCombo.currentText()
        if self.queryDlg.labelVisiCombo.currentText() == "Yes":
            item.labelVisible = True
        else:
            item.labelVisible = False
        if self.queryDlg.normalType.isChecked():
            item.labelType = shp.label.labelTypes[0]
        elif self.queryDlg.NLPType.isChecked():
            item.labelType = shp.label.labelTypes[1]
        elif self.queryDlg.pyLType.isChecked():
            item.labelType = shp.label.labelTypes[2]
        # set opacity to 1 so that the label is still visible on symbol editor
        item.setOpacity(1)
        item.setLabelName()
        item.update()

    def loadSymbol(self, itemsList: list):
        self.attributeList = []
        for item in itemsList[1:]:
            if item is not None:
                if item["type"] in self.symbolShapes:
                    itemShape = lj.createSymbolItems(item, self.gridTuple)
                    # items should be always visible in symbol view
                    if isinstance(itemShape, shp.label):
                        itemShape.setOpacity(1)
                    print(item['type'])
                    self.addItem(itemShape)
                elif item["type"] == "attr":
                    attr = lj.createSymbolAttribute(item)
                    self.attributeList.append(attr)

    def saveSymbolCell(self, fileName):
        # items = self.items(self.sceneRect())  # get items in scene rect
        items = self.items()
        items.insert(0, {"cellView": "symbol"})
        if hasattr(self, "attributeList"):
            items.extend(self.attributeList)  # add attribute list to list
        with open(fileName, "w") as f:
            try:
                json.dump(items, f, cls=se.symbolEncoder, indent=4)
            except Exception as e:
                self.logger.error(e)

    def stretchSelectedItem(self):
        if self.selectedItems is not None:
            try:
                for item in self.selectedItems:
                    if hasattr(item, 'stretch'):
                        item.stretch = True

            except AttributeError:
                self.messageLine.setText("Nothing selected")

    def viewSymbolProperties(self):
        """
        View symbol properties dialog.
        """
        # copy symbol attribute list to another list by deepcopy to be safe
        attributeListCopy = deepcopy(self.attributeList)
        symbolPropDialogue = pdlg.symbolLabelsDialogue(self.parent.parent,
                                                       self.items(),
                                                       attributeListCopy)
        if symbolPropDialogue.exec() == QDialog.Accepted:
            for i, item in enumerate(symbolPropDialogue.labelItemList):
                # label name is not changed.
                item.labelHeight = symbolPropDialogue.labelHeightList[i].text()
                item.labelAlign = symbolPropDialogue.labelAlignmentList[
                    i].currentText()
                item.labelOrient = symbolPropDialogue.labelOrientationList[
                    i].currentText()
                item.labelUse = symbolPropDialogue.labelUseList[i].currentText()
                item.labelType = symbolPropDialogue.labelTypeList[i].currentText()
                item.update(item.boundingRect())
            # create an empty attribute list. If the dialog is OK, the local attribute list
            # will be copied to the symbol attribute list.
            localAttributeList = []
            for i, item in enumerate(symbolPropDialogue.attributeNameList):
                if item.text().strip() != "":
                    localAttributeList.append(se.symbolAttribute(item.text(),
                                                                 symbolPropDialogue.attributeDefList[
                                                                     i].text()))
                self.attributeList = deepcopy(localAttributeList)


class schematic_scene(editor_scene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.schematicWindow = self.parent.parent
        self.instCounter = 0
        self.mousePressLoc = QPoint(0, 0)
        self.mouseMoveLoc = QPoint(0, 0)
        self.mouseReleaseLoc = QPoint(0, 0)
        self.start = QPoint(0, 0)
        self.current = QPoint(0, 0)
        self.selectedItems = None
        self.itemsAtMousePress = list()
        self.itemContextMenu = QMenu()
        self.drawWire = False  # flag to add wire
        self.drawPin = False  # flag to add pin
        self.drawText = False  # flat to add text
        self.itemSelect = True  # flag to select item
        self.drawMode = self.drawWire or self.drawPin
        self.draftPen = QPen(self.guideLineLayer.color, 1)
        self.draftPen.setStyle(Qt.DashLine)
        self.draftPin = None
        self.draftText = None
        self.itemCounter = 0
        self.netCounter = 0
        # self.pinLocations = self.pinLocs()  # dictionary to store pin locations
        self.schematicNets = {}  # netName: list of nets with the same name
        self.crossDots = set()  # list of cross dots
        self.draftItem = None
        self.viewRect = QRect(0, 0, 0, 0)
        self.viewportCrossDots = (
            set())  # an empty set of crossing points in the viewport
        self.sceneCrossDots = set()  # an empty set of all crossing points in the scene
        self.crossDotsMousePress = (
            set())  # a temporary set to hold the crossdots locations
        # add instance attributes
        self.addInstance = False
        self.instanceSymbolFile = None
        # pin attribute defaults
        self.pinName = ""
        self.pinType = "Signal"
        self.pinDir = "Input"
        self.parentView = None

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(mouse_event)
        if mouse_event.button() == Qt.LeftButton:
            self.mousePressLoc = mouse_event.scenePos().toPoint()
            self.start = self.snapToGrid(self.mousePressLoc, self.gridTuple)
            if self.changeOrigin:  # change origin of the symbol
                self.origin = self.start
            elif self.itemSelect:
                self.parent.parent.messageLine.setText("Select an item")
                #     # find the view rectangle every time mouse is pressed.
                self.viewRect = self.parent.view.mapToScene(
                    self.parent.view.viewport().rect()).boundingRect()
                itemsAtMousePress = self.items(mouse_event.scenePos())
                if itemsAtMousePress:
                    # normally only one item is selected
                    self.selectedItems = [item for item in itemsAtMousePress if
                                          item.isSelected()]
                    self.parent.parent.messageLine.setText("Item selected")
                else:
                    self.selectedItems = None
                    self.parent.parent.messageLine.setText("Nothing selected")
            elif self.drawPin:
                self.draftPin = shp.schematicPin(self.start, self.draftPen,
                                                 self.pinName, self.pinDir,
                                                 self.pinType, self.gridTuple, )
                self.addItem(self.draftPin)
            elif self.drawText:
                self.draftText = shp.text(self.start, self.draftPen,
                                          self.noteText, self.gridTuple,
                                          self.noteFontFamily, self.noteFontStyle,
                                          self.noteFontSize, self.noteAlign,
                                          self.noteOrient, )
                self.rotateAnItem(self.start, self.draftText,
                                  float(self.noteOrient[1:]))
                self.addItem(self.draftText)
            elif self.rotateItem:
                if self.selectedItems:
                    self.rotateSelectedItems(self.start)

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseMoveEvent(mouse_event)
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        self.current = self.snapToGrid(self.mouseMoveLoc, self.gridTuple)
        modifiers = QGuiApplication.keyboardModifiers()
        if mouse_event.buttons() == Qt.LeftButton:
            if hasattr(self, "draftItem"):
                self.removeItem(self.draftItem)
                del self.draftItem
            if self.drawWire and hasattr(self, "start"):
                self.parent.parent.messageLine.setText("Wire Mode")
                self.draftItem = net.schematicNet(self.start, self.current,
                                                  self.draftPen)
                self.addItem(self.draftItem)
            elif self.itemSelect:
                if modifiers == Qt.ShiftModifier:
                    self.draftItem = QGraphicsRectItem(
                        QRect.span(self.start, self.current))
                    self.draftItem.setPen(self.draftPen)
                    self.addItem(self.draftItem)
                    self.parent.parent.messageLine.setText("Select an Area")
            elif self.drawPin:
                self.draftPin.setPos(
                    self.snapToGrid(self.mouseMoveLoc - self.mousePressLoc,
                                    self.gridTuple))
            elif self.drawText:
                self.draftText.setPos(
                    self.snapToGrid(self.mouseMoveLoc - self.mousePressLoc,
                                    self.gridTuple))
        self.parent.parent.statusLine.showMessage(
            "Cursor Position: " + str(self.current.toTuple()))

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
        self.current = self.snapToGrid(self.mouseReleaseLoc, self.gridTuple)

        if mouse_event.button() == Qt.LeftButton:
            if self.addInstance:
                instance = self.drawInstance(self.current)
                instance.setSelected(True)
                self.itemSelect = False
                self.addInstance = False
            elif self.drawText:
                self.removeItem(self.draftText)
                note = self.addNote(
                    self.snapToGrid(self.mouseReleaseLoc, self.gridTuple))
                self.rotateAnItem(self.current, note, float(self.noteOrient[1:]))
                self.addItem(note)
                note.setSelected(True)
                self.parent.parent.messageLine.setText("Note added.")
                self.drawText = False
            elif self.drawPin:
                self.removeItem(self.draftPin)
                pin = self.addPin(
                    self.snapToGrid(self.mouseReleaseLoc, self.gridTuple))
                self.addItem(pin)
                pin.setSelected(True)
                self.parent.parent.messageLine.setText("Pin added")
                self.drawPin = False
            elif hasattr(self, "draftItem") and hasattr(self, "start"):
                if self.itemSelect and isinstance(self.draftItem,
                                                  QGraphicsRectItem):
                    self.selectedItems = [item for item in
                                          self.items(self.draftItem.rect(),
                                                     mode=Qt.IntersectsItemBoundingRect)
                                          if (item.childItems() or isinstance(
                            item, net.schematicNet))]
                    for item in self.selectedItems:
                        item.setSelected(True)
                if self.drawWire:
                    drawnNet = self.netDraw(self.start, self.current,
                                            self.wirePen)
                    self.removeDotsInView(self.viewRect)
                    self.mergeNets(drawnNet, self.viewRect)
                    self.splitNets(self.viewRect)
                    self.findDotPoints(self.viewRect)
                    self.drawWire = False
                self.removeItem(self.draftItem)
                del self.draftItem
                del self.start

    def removeDotsInView(self, viewRect: QRect) -> None:
        dotsInView = {item for item in self.items(viewRect) if
                      isinstance(item, net.crossingDot)}
        for dot in dotsInView:
            self.removeItem(dot)
            del dot
        self.viewportCrossDots = set()

    def findDotPoints(self, viewRect: QRect) -> None:
        self.viewportCrossDots = set()  # empty the set.
        netsInView = {item for item in self.items(viewRect) if
                      isinstance(item, net.schematicNet)}
        for netItem in netsInView:
            netItemEnd = netItem.mapToScene(netItem.end)
            for netItem2 in netsInView.difference({netItem, }):
                netItem2Start = netItem.mapToScene(netItem2.start)
                if ((netItem.horizontal and netItem2.horizontal) and (
                        netItemEnd == netItem2Start) or (
                        not (netItem.horizontal or netItem2.horizontal) and (
                        netItemEnd == netItem2Start))):
                    for netItem3 in netsInView.difference({netItem, }).difference(
                            {netItem2, }):
                        netItem3End = netItem3.mapToScene(netItem3.end)
                        netItem3Start = netItem3.mapToScene(netItem3.start)
                        if (netItemEnd == netItem3End) or (
                                netItemEnd == netItem3Start):
                            cornerPoint = netItemEnd.toPoint()
                            self.viewportCrossDots.add(cornerPoint)

        for cornerPoint in self.viewportCrossDots:
            self.createCrossDot(cornerPoint, 3)

    def mergeNets(self, drawnNet, viewRect: QRect) -> None:
        # check any overlapping nets in the view
        # editing is done in the view and thus there is no need to check all nets in the scene
        horizontalNetsInView = {item for item in self.items(viewRect) if (
                isinstance(item, net.schematicNet) and item.horizontal)}
        verticalNetsInView = {item for item in self.items(viewRect) if (
                isinstance(item, net.schematicNet) and not item.horizontal)}
        dBNetRect = drawnNet.sceneBoundingRect()
        if len(horizontalNetsInView) > 1 and drawnNet.horizontal:
            for netItem in horizontalNetsInView - {drawnNet, }:
                netItemBRect = netItem.sceneBoundingRect()
                if dBNetRect.intersects(netItemBRect):
                    mergedRect = dBNetRect.united(netItemBRect).toRect()
                    self.removeItem(netItem)  # remove the old net from the scene
                    self.removeItem(
                        drawnNet)  # remove the drawn net from the scene
                    mergedNet = self.netDraw(
                        self.snapToGrid(mergedRect.bottomLeft(), self.gridTuple),
                        self.snapToGrid(mergedRect.bottomRight(), self.gridTuple),
                        self.wirePen, )
                    horizontalNetsInView.discard(netItem)
                    self.mergeNets(mergedNet, viewRect)
                    self.parent.parent.messageLine.setText("Merged Nets")
        elif len(verticalNetsInView) > 1 and not drawnNet.horizontal:
            for netItem in verticalNetsInView - {drawnNet, }:
                netItemBRect = netItem.sceneBoundingRect()
                if dBNetRect.intersects(netItemBRect):
                    mergedRect = dBNetRect.united(netItemBRect).toRect()
                    self.removeItem(netItem)  # remove the old net from the scene
                    self.removeItem(
                        drawnNet)  # remove the drawn net from the scene
                    mergedNet = self.netDraw(
                        self.snapToGrid(mergedRect.bottomRight(), self.gridTuple),
                        self.snapToGrid(mergedRect.topRight(), self.gridTuple),
                        self.wirePen, )  # create a new net with the merged rectangle
                    verticalNetsInView.discard(netItem)
                    self.mergeNets(mergedNet, viewRect)
                    self.parent.parent.messageLine.setText("Net merged")

    def splitNets(self, viewRect: QRect) -> None:
        horizontalNetsInView = {item for item in self.items(viewRect) if (
                isinstance(item, net.schematicNet) and item.horizontal)}
        verticalNetsInView = {item for item in self.items(viewRect) if (
                isinstance(item, net.schematicNet) and not item.horizontal)}
        addedNets = set()
        for hNetItem in horizontalNetsInView:
            verticalNetsInView = {item for item in self.items(viewRect) if (
                    isinstance(item, net.schematicNet) and not item.horizontal)}
            hNetBRect = hNetItem.sceneBoundingRect().toRect()
            for vNetItem in verticalNetsInView:
                vNetBRect = vNetItem.sceneBoundingRect().toRect()
                if vNetBRect.intersects(hNetBRect):
                    crossPoint = self.snapToGrid(
                        vNetBRect.intersected(hNetBRect).center(), self.gridTuple)
                    if crossPoint != vNetItem.end and crossPoint != vNetItem.start:
                        addedNets.add((
                            vNetItem.mapToScene(vNetItem.start).toPoint(),
                            crossPoint))
                        addedNets.add((crossPoint, vNetItem.mapToScene(
                            vNetItem.end).toPoint()))
                        self.removeItem(vNetItem)
                        del vNetItem
                        break
        for vNetItem in verticalNetsInView:
            horizontalNetsInView = {item for item in self.items(viewRect) if (
                    isinstance(item, net.schematicNet) and item.horizontal)}
            vNetBRect = vNetItem.sceneBoundingRect().toRect()
            for hNetItem in horizontalNetsInView:
                hNetBRect = hNetItem.sceneBoundingRect().toRect()
                if hNetBRect.intersects(vNetBRect):
                    crossPoint = self.snapToGrid(
                        hNetBRect.intersected(vNetBRect).center(), self.gridTuple)
                    if crossPoint != hNetItem.end and crossPoint != hNetItem.start:
                        addedNets.add((
                            hNetItem.mapToScene(hNetItem.start).toPoint(),
                            crossPoint))
                        addedNets.add((crossPoint, hNetItem.mapToScene(
                            hNetItem.end).toPoint()))
                        self.removeItem(hNetItem)
                        del hNetItem
                        break
        for addedNet in addedNets:
            self.netDraw(addedNet[0], addedNet[1], self.wirePen)

    def createNetlist(self, netlistFile, writeNetlist: bool) -> None:
        """
        Creates a netlist from the schematic.
        """
        pass

    def groupAllNets(self) -> None:
        """
        This method starting from nets connected to pins, then named nets and unnamed
        nets, groups all the nets in the schematic.
        """
        # all the nets in the schematic in a set to remove duplicates
        netsSceneSet = self.findSceneNetsSet()
        # create a separate set of named nets.
        # namedNetsSet = set()
        # nets connected to pins. Netlisting will start from those nets
        pinConNetsSet = set()
        # first start from schematic pins
        scenePinsSet = self.findScenePinsSet()

        for scenePin in scenePinsSet:
            for sceneNet in netsSceneSet:
                if self.checkPinNetConnect(scenePin, sceneNet):
                    if sceneNet.nameSet:
                        if sceneNet.name == scenePin.pinName:
                            pinConNetsSet.add(sceneNet)
                        else:
                            sceneNet.nameConflict = True
                            self.parent.parent.logger.error(
                                f"Net name conflict at {scenePin.pinName} of "
                                f"{scenePin.parent.instanceName}.")
                    else:
                        pinConNetsSet.add(sceneNet)
                        sceneNet.name = scenePin.pinName
                    sceneNet.update()

        # first propagate the net names to the nets connected to pins.
        # first net set is left over nets.
        notPinConnNets = self.groupNamedNets(pinConNetsSet,
                                             netsSceneSet - pinConNetsSet)

        # find all nets with nets set through net dialogue.
        namedNetsSet = set([netItem for netItem in netsSceneSet - pinConNetsSet if
                            netItem.nameSet])
        # now remove already named net set from firstNetSet
        unnamedNets = self.groupNamedNets(namedNetsSet,
                                          notPinConnNets - namedNetsSet)
        # for netItem in unnamedNets:
        #     if not netItem.nameSet:
        #         netItem.name = None  # empty all net names not set by the user
        # now start netlisting from the unnamed nets
        self.groupUnnamedNets(unnamedNets, self.netCounter)

    def generatePinNetMap(self, sceneSymbolSet):
        """
        For symbols in sceneSymbolSet, find which pin is connected to which net. If a
        pin is not connected, assign to it a default net starting with d prefix.
        """
        netCounter = 0
        for symbolItem in sceneSymbolSet:
            for pinName, pinItem in symbolItem.pins.items():
                pinItem.connected = False  # clear connections
                # find each symbol its pin locations and save it in pinLocations
                # directory.
                # symbolItem.pinLocations[pinName] = pinItem.sceneBoundingRect()
                for netName, netItemSet in self.schematicNets.items():
                    for netItem in netItemSet:
                        if self.checkPinNetConnect(pinItem, netItem):
                            symbolItem.pinNetMap[pinName] = netName
                            pinItem.connected = True  # print(f'{symbolItem.instanceName}, {pinItem.pinName}')
                if not pinItem.connected:
                    # assign a default net name prefixed with d(efault).
                    symbolItem.pinNetMap[pinName] = f"dnet{netCounter}"
                    self.logger.error(
                        f"left unconnected:{symbolItem.pinNetMap[pinName]}")
                    netCounter += 1

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

    def findSceneSymbolSet(self) -> set[shp.symbolShape]:
        """
        Find all the symbols on the scene as a set.
        """
        symbolSceneSet = {item for item in self.items() if
                          isinstance(item, shp.symbolShape)}
        return symbolSceneSet

    def findSceneNetsSet(self) -> set[net.schematicNet]:
        netsSceneSet = {item for item in self.items() if
                        isinstance(item, net.schematicNet)}
        return netsSceneSet

    def findScenePinsSet(self) -> set[shp.schematicPin]:
        pinsSceneSet = {item for item in self.items() if
                        isinstance(item, shp.schematicPin)}
        if pinsSceneSet:  # check pinsSceneSet is empty
            return pinsSceneSet
        else:
            return set()

    def findSceneTextSet(self) -> set[shp.text]:
        textSceneSet = {item for item in self.items() if
                        isinstance(item, shp.text)}
        if textSceneSet:  # check textSceneSet is empty
            return textSceneSet
        else:
            return set()

    def groupNamedNets(self, namedNetsSet, unnamedNetsSet):
        """
        Groups nets with the same name.
        """
        for netItem in namedNetsSet:
            if self.schematicNets.get(netItem.name) is None:
                self.schematicNets[netItem.name] = set()
            connectedNets, unnamedNetsSet = self.traverseNets({netItem, },
                                                              unnamedNetsSet, )
            self.schematicNets[netItem.name] |= connectedNets
        # These are the nets not connected to any named net
        return unnamedNetsSet

    def groupUnnamedNets(self, unnamedNetsSet: set[net.schematicNet],
                         nameCounter: int):
        """
        Groups nets together if they are connected and assign them default names
        if they don't have a name assigned.
        """
        # select a net from the set and remove it from the set
        try:
            initialNet = (
                unnamedNetsSet.pop())  # assign it a name, net0, net1, net2, etc.
        except KeyError:  # initialNet set is empty
            pass
        else:
            initialNet.name = "net" + str(nameCounter)
            # now go through the set and see if any of the
            # nets are connected to the initial net
            # remove them from the set and add them to the initial net's set
            self.schematicNets[
                initialNet.name], unnamedNetsSet = self.traverseNets(
                {initialNet, }, unnamedNetsSet, )
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
                if self.checkConnect(netItem, netItem2):
                    if (
                            netItem2.nameSet and netItem.nameSet and netItem.name != netItem2.name):
                        self.parent.parent.messageLine.setText(
                            "Error: multiple names assigned to same net")
                        netItem2.nameConflict = True
                        netItem.nameConflict = True
                        break
                    else:
                        netItem2.name = netItem.name
                        netItem.nameConflict = False
                        netItem2.nameConflict = False
                    newFoundConnectedSet.add(netItem2)
        # keep searching if you already found a net connected to the initial net
        if len(newFoundConnectedSet) > 0:
            connectedSet.update(newFoundConnectedSet)
            otherNetsSet -= newFoundConnectedSet
            self.traverseNets(connectedSet, otherNetsSet)
        return connectedSet, otherNetsSet

    def checkPinNetConnect(self, pinItem: shp.pin, netItem: net.schematicNet):
        if pinItem.sceneBoundingRect().intersects(netItem.sceneBoundingRect()):
            return True
        else:
            return False

    def checkConnect(self, netItem, otherNetItem):
        """
        Determine if a net is connected to netItem.
        """
        netBRect = netItem.sceneBoundingRect()
        if otherNetItem is not netItem:
            otherBRect = otherNetItem.sceneBoundingRect()
            if otherBRect.contains(
                    netItem.mapToScene(netItem.start)) or otherBRect.contains(
                netItem.mapToScene(netItem.end)):
                return True
            elif netBRect.contains(otherNetItem.mapToScene(
                    otherNetItem.start)) or netBRect.contains(
                otherNetItem.mapToScene(otherNetItem.end)):
                return True
            else:
                return False

    def createCrossDot(self, center: QPoint, radius: int):
        crossDot = net.crossingDot(center, radius, self.wirePen)
        self.addItem(crossDot)
        return crossDot

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_Escape:
            self.resetSceneMode()
        super().keyPressEvent(key_event)

    def resetSceneMode(self):
        self.itemSelect = True
        self.drawWire = False
        self.drawPin = False
        self.selectedItems = []
        self.parent.parent.messageLine.setText("Select Mode")

    def netDraw(self, start: QPoint, current: QPoint,
                pen: QPen) -> net.schematicNet:
        line = net.schematicNet(start, current, pen)
        self.addItem(line)
        undoCommand = us.addShapeUndo(self, line)
        self.undoStack.push(undoCommand)
        return line

    def addPin(self, pos: QPoint):
        pin = shp.schematicPin(pos, self.pinPen, self.pinName, self.pinDir,
                               self.pinType, self.gridTuple)
        undoCommand = us.addShapeUndo(self, pin)
        self.undoStack.push(undoCommand)
        return pin

    def addNote(self, pos: QPoint):
        """
        Changed the method name not to clash with qgraphicsscene addText method.
        """
        text = shp.text(pos, self.textPen, self.noteText, self.gridTuple,
                        self.noteFontFamily, self.noteFontStyle,
                        self.noteFontSize, self.noteAlign, self.noteOrient, )
        undoCommand = us.addShapeUndo(self, text)
        self.undoStack.push(undoCommand)
        return text

    def drawInstance(self, pos: QPoint):
        """
        Add an instance of a symbol to the scene.
        """
        instance = self.instSymbol(self.instanceSymbolFile, pos)
        self.addItem(instance)
        undoCommand = us.addShapeUndo(self, instance)
        self.undoStack.push(undoCommand)
        return instance

    def instSymbol(self, file: pathlib.Path, pos: QPoint):
        """
        Read a symbol file and create symbolShape objects from it.
        """
        assert isinstance(file, pathlib.Path)
        itemShapes = []
        itemAttributes = {}
        draftPen = QPen(self.guideLineLayer.color, 1)
        with open(file, "r") as temp:
            try:
                items = json.load(temp)
                if items[0]["cellView"] == "symbol":
                    for item in items[1:]:
                        if item["type"] == 'attr':
                            itemAttributes[item["nam"]] = item["def"]
                        else:
                            itemShapes.append(lj.createSymbolItems(item,
                                                               self.gridTuple))
                        # if (item["type"] == "rect" or item["type"] == "line" or
                        #         item["type"] == "pin" or item[
                        #             "type"] == "label" or item[
                        #             "type"] == "circle" or item["type"] == "arc"):
                        #     # append recreated shapes to shapes list
                        #     itemShapes.append(
                        #         lj.createSymbolItems(item, self.gridTuple))
                        # elif item["type"] == "attr":
                        #     itemAttributes[item["nam"]] = item["def"]
                else:
                    self.logger.error("Not a symbol!")

                # create a symbol instance passing item shapes and attributes as
                # arguments
                symbolInstance = shp.symbolShape(draftPen, self.gridTuple,
                                                 itemShapes, itemAttributes)
                symbolInstance.setPos(pos)
                # For each instance assign a counter number from the scene
                symbolInstance.counter = self.itemCounter
                symbolInstance.instanceName = f"I{symbolInstance.counter}"
                symbolInstance.libraryName = file.parent.parent.stem
                symbolInstance.cellName = file.parent.stem
                symbolInstance.viewName = "symbol"
                for item in symbolInstance.labels.values():
                    item.labelDefs()
                return symbolInstance
            except json.JSONDecodeError:
                # print("Invalid JSON file")
                self.logger.warning("Invalid JSON File")

    def deleteSelectedItems(self):
        try:
            for item in self.selectedItems:
                self.removeItem(item)
            del self.selectedItems
            self.update()
            self.itemSelect = True
        except TypeError:
            pass

    def copySelectedItems(self):
        if self.selectedItems is not None:
            for item in self.selectedItems:
                selectedItemJson = json.dumps(item, cls=se.schematicEncoder)
                itemCopyDict = json.loads(selectedItemJson)
                print(itemCopyDict)
                if isinstance(item, shp.symbolShape):
                    self.itemCounter += 1
                    itemCopyDict["name"] = f"I{self.itemCounter}"
                    itemCopyDict["labelDict"]["instName"] = ["@instName",
                                                             f"I{self.itemCounter}", ]
                    shape = lj.createSchematicItems(itemCopyDict,
                                                    self.libraryDict,
                                                    item.viewName, self.gridTuple)

                elif isinstance(item, net.schematicNet):
                    shape = lj.createSchematicNets(itemCopyDict)
                elif isinstance(item, shp.schematicPin):
                    shape = lj.createSchematicPins(itemCopyDict, self.gridTuple)
                self.addItem(shape)
                # shift position by one grid unit to right and down
                shape.setPos(QPoint(item.pos().x() + 4 * self.gridTuple[0],
                                    item.pos().y() + 4 * self.gridTuple[1], ))
                undoCommand = us.addShapeUndo(self, shape)
                self.undoStack.push(undoCommand)

    def saveSchematicCell(self, file: pathlib.Path):
        self.sceneR = self.sceneRect()  # get scene rect
        # items = self.items(self.sceneR)  # get items in scene rect
        # only save symbol shapes
        symbolItems = self.findSceneSymbolSet()
        netItems = self.findSceneNetsSet()
        pinItems = self.findScenePinsSet()
        textItems = self.findSceneTextSet()
        items = list(symbolItems | netItems | pinItems | textItems)
        items.insert(0, {"cellView": "schematic"})
        with open(file, "w") as f:
            json.dump(items, f, cls=se.schematicEncoder, indent=4)
        if self.parent.parent.parentView is not None:
            if type(self.parentView) == schematicEditor:
                self.parent.parent.parentView.loadSchematic()
            elif type(self.parentView) == symbolEditor:
                self.parent.parent.parentView.loadSymbol()

    def loadSchematicCell(self, itemsList):
        """
        load schematic from item list
        """
        for item in itemsList[1:]:
            if item is not None:
                if item["type"] == "symbolShape":
                    itemShape = lj.createSchematicItems(item, self.libraryDict,
                                                        "symbol", self.gridTuple)
                    self.addItem(itemShape)
                    if itemShape.counter > self.itemCounter:
                        self.itemCounter = itemShape.counter
                elif item["type"] == "schematicNet":
                    netShape = lj.createSchematicNets(item)
                    self.addItem(netShape)
                elif item["type"] == "schematicPin":
                    pinShape = lj.createSchematicPins(item, self.gridTuple)
                    self.addItem(pinShape)
                elif item["type"] == "text":
                    text = lj.createTextItem(item, self.gridTuple)
                    self.addItem(text)

        # increment item counter for next symbol
        self.itemCounter += 1
        self.findDotPoints(self.sceneRect())
        # self.addItem(shp.text(QPoint(0, 200), self.textPen, 'Revolution EDA'))
        self.update()

    def viewObjProperties(self):
        """
        Display the properties of the selected object.
        """

        if self.selectedItems is not None:
            for item in self.selectedItems:
                if isinstance(item, shp.symbolShape):
                    dlg = pdlg.instanceProperties(self.parent.parent, item)
                    if dlg.exec() == QDialog.Accepted:
                        item.libraryName = dlg.libNameEdit.text().strip()
                        item.cellName = dlg.cellNameEdit.text().strip()
                        item.viewName = dlg.viewNameEdit.text().strip()
                        filePath = pathlib.Path(
                            self.libraryDict[item.libraryName].joinpath(
                                item.cellName, item.viewName + ".json"))
                        item.instanceName = dlg.instNameEdit.text().strip()
                        item.angle = float(dlg.angleEdit.text().strip())
                        for label in item.labels.values():
                            if label.labelDefinition == "[@instName]":
                                label.labelValue = item.instanceName
                            elif label.labelDefinition == "[@cellName]":
                                label.labelValue = item.cellName
                        location = self.snapToGrid(
                            QPoint(float(dlg.xLocationEdit.text().strip()),
                                   float(dlg.yLocationEdit.text().strip()), ),
                            self.gridTuple, )
                        item.setPos(location)
                        tempDoc = QTextDocument()
                        for i in range(dlg.instanceLabelsLayout.rowCount()):
                            # first create label name document with HTML annotations
                            tempDoc.setHtml(
                                dlg.instanceLabelsLayout.itemAtPosition(i,
                                                                        0).widget().text())
                            # now strip html annotations
                            tempLabelName = tempDoc.toPlainText().strip()
                            # check if label name is in label dictionary of item.
                            if tempLabelName in item.labels.keys():
                                item.labels[tempLabelName].labelValue = (
                                    dlg.instanceLabelsLayout.itemAtPosition(i,
                                                                            1).widget().text())
                                item.labels[tempLabelName].labelValueSet = True
                                visible = (
                                    dlg.instanceLabelsLayout.itemAtPosition(i,
                                                                            2).widget().currentText())
                                if visible == "True":
                                    item.labels[tempLabelName].labelVisible = True
                                else:
                                    item.labels[
                                        tempLabelName].labelVisible = False
                                item.labels[tempLabelName].labelDefs()
                        item.update()
                elif isinstance(item, net.schematicNet):
                    dlg = pdlg.netProperties(self.parent.parent, item)
                    if dlg.exec() == QDialog.Accepted:
                        item.name = dlg.netNameEdit.text().strip()
                        if item.name == "":
                            item.nameSet = False
                        else:
                            item.nameSet = True  # self.createNetlist()
                        item.update()
                elif isinstance(item, shp.text):
                    dlg = pdlg.noteTextEditProperties(self.parent.parent, item)
                    if dlg.exec() == QDialog.Accepted:
                        # item.prepareGeometryChange()
                        start = item.start
                        self.removeItem(item)
                        item = shp.text(start, self.textPen,
                                        dlg.plainTextEdit.toPlainText(),
                                        self.gridTuple,
                                        dlg.familyCB.currentText(),
                                        dlg.fontStyleCB.currentText(),
                                        dlg.fontsizeCB.currentText(),
                                        dlg.textAlignmCB.currentText(),
                                        dlg.textOrientCB.currentText(), )
                        self.rotateAnItem(start, item, float(item.textOrient[1:]))
                        self.addItem(item)

    def createSymbol(self):
        """
        Create a symbol view for a schematic.
        """
        oldSymbolItem = False

        askViewNameDlg = pdlg.symbolNameDialog(self.parent.parent.file.parent,
                                               self.parent.parent.cellName,
                                               self.parent.parent, )
        if askViewNameDlg.exec() == QDialog.Accepted:
            symbolViewName = askViewNameDlg.symbolViewsCB.currentText()
            if symbolViewName in askViewNameDlg.symbolViewNames:
                oldSymbolItem = True

        if oldSymbolItem:
            deleteSymViewDlg = fd.deleteSymbolDialog(self.parent.parent.cellName,
                                                     symbolViewName,
                                                     self.parent.parent)
            if deleteSymViewDlg.exec() == QDialog.Accepted:
                self.generateSymbol(symbolViewName)
        else:
            self.generateSymbol(symbolViewName)

    def generateSymbol(self, symbolViewName: str):
        # openPath = pathlib.Path(cellItem.data(Qt.UserRole + 2))
        cellPath = self.schematicWindow.file.parent
        libName = self.schematicWindow.libName
        cellName = self.schematicWindow.cellName
        libItem = libm.getLibItem(self.schematicWindow.libraryView.libraryModel,
                                  libName)
        cellItem = libm.getCellItem(libItem, cellName)
        libraryView = self.schematicWindow.libraryView
        schematicPins = list(self.findScenePinsSet())

        schematicPinNames = [pinItem.pinName for pinItem in schematicPins]

        inputPins = [pinItem.pinName for pinItem in schematicPins if
                     pinItem.pinDir == shp.schematicPin.pinDirs[0]]

        outputPins = [pinItem.pinName for pinItem in schematicPins if
                      pinItem.pinDir == shp.schematicPin.pinDirs[1]]

        inoutPins = [pinItem.pinName for pinItem in schematicPins if
                     pinItem.pinDir == shp.schematicPin.pinDirs[2]]

        dlg = pdlg.symbolCreateDialog(self.parent.parent, inputPins, outputPins,
                                      inoutPins)
        if dlg.exec() == QDialog.Accepted:
            symbolViewItem = scb.createCellView(self.parent.parent,
                                                symbolViewName, cellItem)
            libraryDict = self.parent.parent.libraryDict
            # create symbol editor window with an empty items list
            symbolWindow = symbolEditor(symbolViewItem, libraryDict, libraryView)
            try:
                leftPinNames = list(filter(None, [pinName.strip() for pinName in
                                                  dlg.leftPinsEdit.text().split(
                                                      ",")], ))
                rightPinNames = list(filter(None, [pinName.strip() for pinName in
                                                   dlg.rightPinsEdit.text().split(
                                                       ",")], ))
                topPinNames = list(filter(None, [pinName.strip() for pinName in
                                                 dlg.topPinsEdit.text().split(
                                                     ",")], ))
                bottomPinNames = list(filter(None, [pinName.strip() for pinName in
                                                    dlg.bottomPinsEdit.text().split(
                                                        ",")], ))
                stubLength = int(float(dlg.stubLengthEdit.text().strip()))
                pinDistance = int(float(dlg.pinDistanceEdit.text().strip()))
                rectXDim = (max(len(topPinNames),
                                len(bottomPinNames)) + 1) * pinDistance
                rectYDim = (max(len(leftPinNames),
                                len(rightPinNames)) + 1) * pinDistance
            except ValueError:
                print("Enter valid value")

        # add window to open windows list
        libraryView.openViews[
            f"{libName}_{cellName}_{symbolViewName}"] = symbolWindow
        symbolScene = symbolWindow.centralW.scene
        symbolScene.rectDraw(QPoint(0, 0), QPoint(rectXDim, rectYDim),
                             self.symbolPen, self.gridTuple)
        symbolScene.labelDraw(QPoint(int(0.25 * rectXDim), int(0.4 * rectYDim)),
                              self.labelPen, "[@cellName]", self.gridTuple,
                              "NLPLabel", "12", "Center", "R0", "Instance", )
        symbolScene.labelDraw(QPoint(int(rectXDim), int(-0.2 * rectYDim)),
                              self.labelPen, "[@instName]", self.gridTuple,
                              "NLPLabel", "12", "Center", "R0", "Instance", )
        leftPinLocs = [QPoint(-stubLength, (i + 1) * pinDistance) for i in
                       range(len(leftPinNames))]
        rightPinLocs = [QPoint(rectXDim + stubLength, (i + 1) * pinDistance) for i
                        in range(len(rightPinNames))]
        bottomPinLocs = [QPoint((i + 1) * pinDistance, rectYDim + stubLength) for
                         i in range(len(bottomPinNames))]
        topPinLocs = [QPoint((i + 1) * pinDistance, -stubLength) for i in
                      range(len(topPinNames))]
        for i in range(len(leftPinNames)):
            symbolScene.lineDraw(leftPinLocs[i],
                                 leftPinLocs[i] + QPoint(stubLength, 0),
                                 symbolScene.symbolPen, symbolScene.gridTuple, )
            symbolScene.addItem(schematicPins[
                schematicPinNames.index(leftPinNames[i])].toSymbolPin(
                leftPinLocs[i], symbolScene.pinPen, symbolScene.gridTuple))
        for i in range(len(rightPinNames)):
            symbolScene.lineDraw(rightPinLocs[i],
                                 rightPinLocs[i] + QPoint(-stubLength, 0),
                                 symbolScene.symbolPen, symbolScene.gridTuple, )
            symbolScene.addItem(schematicPins[
                schematicPinNames.index(rightPinNames[i])].toSymbolPin(
                rightPinLocs[i], symbolScene.pinPen, symbolScene.gridTuple))
        for i in range(len(topPinNames)):
            symbolScene.lineDraw(topPinLocs[i],
                                 topPinLocs[i] + QPoint(0, stubLength),
                                 symbolScene.symbolPen, symbolScene.gridTuple, )
            symbolScene.addItem(schematicPins[
                schematicPinNames.index(topPinNames[i])].toSymbolPin(
                topPinLocs[i], symbolScene.pinPen, symbolScene.gridTuple))
        for i in range(len(bottomPinNames)):
            symbolScene.lineDraw(bottomPinLocs[i],
                                 bottomPinLocs[i] + QPoint(0, -stubLength),
                                 symbolScene.symbolPen, symbolScene.gridTuple, )
            symbolScene.addItem(schematicPins[
                schematicPinNames.index(bottomPinNames[i])].toSymbolPin(
                bottomPinLocs[i], symbolScene.pinPen,
                symbolScene.gridTuple))  # symbol attribute generation for netlisting.
        symbolScene.attributeList = list()  # empty attribute list
        nlpPinNames = ""
        for pinName in schematicPinNames:
            nlpPinNames += f" [|{pinName}:%]"
        symbolScene.attributeList.append(se.symbolAttribute("NLPDeviceFormat",
                                                            f"X[@instName] {nlpPinNames} [@cellName]"))
        symbolWindow.show()
        libraryView.reworkDesignLibrariesView()
        return symbolViewItem

    def goDownHier(self):
        if self.selectedItems is not None:
            for item in self.selectedItems:
                if isinstance(item, shp.symbolShape):
                    dlg = fd.goDownHierDialogue(item,
                                                self.parent.parent.libraryDict, )
                    if dlg.exec() == QDialog.Accepted:
                        selectedView = dlg.viewNameCB.currentText()
                        libName = item.libraryName
                        cellName = item.cellName
                        libraryView = self.parent.parent.libraryView
                        libraryModel = libraryView.libraryModel
                        libraryDict = libraryView.libraryDict
                        viewItem = libm.findViewItem(libraryModel, libName,
                                                     cellName, selectedView)

                        if "symbol" in selectedView:
                            symbolWindow = symbolEditor(viewItem, libraryDict,
                                                        libraryView, )
                            symbolWindow.loadSymbol()
                            symbolWindow.parentView = self.parent.parent
                            symbolWindow.show()
                            libraryView.openViews[
                                f"{libName}_{cellName}_{selectedView}"] = symbolWindow
                        elif "schematic" in selectedView:
                            schematicWindow = schematicEditor(viewItem,
                                                              libraryDict,
                                                              libraryView, )
                            schematicWindow.loadSchematic()
                            schematicWindow.parentView = self.parent.parent
                            schematicWindow.show()
                            libraryView.openViews[
                                f"{libName}_{cellName}_{selectedView}"] = schematicWindow

    def goUpHier(self):
        print("Up baby up")


class editor_view(QGraphicsView):
    """
    The qgraphicsview for qgraphicsscene. It is used for both schematic and layout editors.
    """

    def __init__(self, scene, parent):
        super().__init__(scene, parent)
        self.parent = parent
        self.editor = self.parent.parent
        self.scene = scene
        self.majorGrid = self.editor.majorGrid
        self.gridTuple = self.editor.gridTuple
        self.gridbackg = True
        self.init_UI()

    def init_UI(self):
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # self.setCacheMode(QGraphicsView.CacheBackground)
        self.standardCursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.standardCursor)  # set cursor to standard arrow
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setMouseTracking(True)

    def wheelEvent(self, mouse_event):
        factor = 1.1
        if mouse_event.angleDelta().y() < 0:
            factor = 0.9
        view_pos = QPoint(int(mouse_event.globalPosition().x()),
                          int(mouse_event.globalPosition().y()))
        scene_pos = self.mapToScene(view_pos)
        self.centerOn(scene_pos)
        self.scale(factor, factor)
        delta = self.mapToScene(view_pos) - self.mapToScene(
            self.viewport().rect().center())
        self.centerOn(scene_pos - delta)
        super().wheelEvent(mouse_event)

    def snapToBase(self, number, base):
        return base * int(math.floor(number / base))

    def drawBackground(self, painter, rect):

        if self.gridbackg:
            rectCoord = rect.getRect()
            painter.fillRect(rect, QColor("black"))
            painter.setPen(QColor("gray"))
            grid_x_start = math.ceil(
                rectCoord[0] / self.majorGrid) * self.majorGrid
            grid_y_start = math.ceil(
                rectCoord[1] / self.majorGrid) * self.majorGrid
            num_x_points = math.floor(rectCoord[2] / self.majorGrid)
            num_y_points = math.floor(rectCoord[3] / self.majorGrid)
            for i in range(int(num_x_points)):  # rect width
                for j in range(int(num_y_points)):  # rect length
                    painter.drawPoint(grid_x_start + i * self.majorGrid,
                                      grid_y_start + j * self.majorGrid, )
        else:
            super().drawBackground(painter, rect)

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_F:
            self.fitToView()
        super().keyPressEvent(key_event)

    def fitToView(self):
        viewRect = self.scene.itemsBoundingRect().marginsAdded(
            QMargins(40, 40, 40, 40))
        self.fitInView(viewRect, Qt.AspectRatioMode.KeepAspectRatio)
        self.show()

    def printView(self, printer):
        """
        Print view using selected Printer.
        """
        painter = QPainter(printer)
        painter.setFont(QFont("Helvetica"))
        self.gridbackg = False
        self.drawBackground(painter, self.viewport().geometry())
        painter.drawText(self.viewport().geometry(), "Revolution EDA")
        self.render(painter)
        self.gridbackg = True
        painter.end()


class symbol_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self.visibleRect = QRect(0, 0, 0, 0)  # initialize to an empty rectangle


class schematic_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self.visibleRect = QRect(0, 0, 0, 0)  # initialize to an empty rectangle
        self.viewItems = []
        self.netItems = []

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        if mouse_event.button() == Qt.LeftButton:
            if self.scene.drawWire:
                self.visibleRect = self.viewport().geometry()
                self.viewItems = [item for item in self.items(self.visibleRect,
                                                              mode=Qt.IntersectsItemShape)
                                  if isinstance(item, shp.symbolShape)]
                self.netItems = [item for item in self.items(self.visibleRect,
                                                             mode=Qt.IntersectsItemShape)
                                 if isinstance(item, net.schematicNet)]
        super().mouseReleaseEvent(mouse_event)


class libraryBrowser(QMainWindow):
    def __init__(self, appMainW: QMainWindow) -> None:
        super().__init__()
        self.appMainW = appMainW
        self.libraryDict = self.appMainW.libraryDict
        self.cellViews = self.appMainW.cellViews
        self.setWindowTitle("Library Browser")
        self._createMenuBar()
        self._createActions()
        self._createToolBars()
        self.logger = self.appMainW.logger
        self.libFilePath = self.appMainW.libraryPathObj
        self.libBrowserCont = libraryBrowserContainer(self)
        self.setCentralWidget(self.libBrowserCont)
        self.designView = self.libBrowserCont.designView
        self.libraryModel = self.designView.libraryModel

    def _createMenuBar(self):
        self.browserMenubar = self.menuBar()
        self.browserMenubar.setNativeMenuBar(False)
        self.libraryMenu = self.browserMenubar.addMenu("&Library")

    def _createActions(self):
        openLibIcon = QIcon(":/icons/database--plus.png")
        self.openLibAction = QAction(openLibIcon, "Create/Open Lib...", self)
        self.openLibAction.setToolTip("Create/Open Lib...")
        self.libraryMenu.addAction(self.openLibAction)
        self.openLibAction.triggered.connect(self.openLibClick)

        libraryEditIcon = QIcon(":/icons/application-dialog.png")
        self.libraryEditorAction = QAction(libraryEditIcon, "Library Editor",
                                           self)
        self.libraryMenu.addAction(self.libraryEditorAction)
        self.libraryEditorAction.setToolTip("Open Library Editor...")
        self.libraryEditorAction.triggered.connect(self.libraryEditorClick)

        closeLibIcon = QIcon(":/icons/database-delete.png")
        self.closeLibAction = QAction(closeLibIcon, "Close Lib...", self)
        self.closeLibAction.setToolTip("Close Lib")
        self.libraryMenu.addAction(self.closeLibAction)
        self.closeLibAction.triggered.connect(self.closeLibClick)

        self.libraryMenu.addSeparator()

        newCellIcon = QIcon(":/icons/document--plus.png")
        self.newCellAction = QAction(newCellIcon, "New Cell...", self)
        self.newCellAction.setToolTip("Create New Cell")
        self.libraryMenu.addAction(self.newCellAction)
        self.newCellAction.triggered.connect(self.newCellClick)

        deleteCellIcon = QIcon(":/icons/node-delete.png")
        self.deleteCellAction = QAction(deleteCellIcon, "Delete Cell...", self)
        self.deleteCellAction.setToolTip("Delete Cell")
        self.libraryMenu.addAction(self.deleteCellAction)
        self.deleteCellAction.triggered.connect(self.deleteCellClick)

        self.libraryMenu.addSeparator()

        newCellViewIcon = QIcon(":/icons/document--pencil.png")
        self.newCellViewAction = QAction(newCellViewIcon,
                                         "Create New CellView...", self)
        self.newCellViewAction.setToolTip("Create New Cellview")
        self.libraryMenu.addAction(self.newCellViewAction)
        self.newCellViewAction.triggered.connect(self.newCellViewClick)

        openCellViewIcon = QIcon(":/icons/document--pencil.png")
        self.openCellViewAction = QAction(openCellViewIcon, "Open CellView...",
                                          self)
        self.openCellViewAction.setToolTip("Open CellView")
        self.libraryMenu.addAction(self.openCellViewAction)
        self.openCellViewAction.triggered.connect(self.openCellViewClick)

        deleteCellViewIcon = QIcon(":/icons/node-delete.png")
        self.deleteCellViewAction = QAction(deleteCellViewIcon,
                                            "Delete CellView...", self)
        self.deleteCellViewAction.setToolTip("Delete Cellview")
        self.libraryMenu.addAction(self.deleteCellViewAction)
        self.deleteCellViewAction.triggered.connect(self.deleteCellViewClick)

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

    def writeLibDefFile(self, libPathDict: dict,
                        libFilePath: pathlib.Path) -> None:

        libTempDict = dict(
            zip(libPathDict.keys(), map(str, libPathDict.values())))
        try:
            with libFilePath.open(mode="w") as f:
                json.dump({"libdefs": libTempDict}, f, indent=4)
            self.logger.info(f'Wrote library definition file in {libFilePath}')
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
            # TODO: add some library information to this file.
            libPathObj.joinpath("reveda.lib").touch(exist_ok=True)
            # self.designView.reworkDesignLibrariesView()
            self.libraryModel.populateLibrary(libPathObj)
            self.writeLibDefFile(self.libraryDict, self.libFilePath)

    def closeLibClick(self):
        libCloseDialog = fd.closeLibDialog(self.libraryDict, self)
        if libCloseDialog.exec() == QDialog.Accepted:
            libName = libCloseDialog.libNamesCB.currentText()
            libItem = libm.getLibItem(self.libraryModel, libName)
            try:
                self.libraryDict.pop(libName)
            except KeyError:
                self.logger.error(f"{libName} not found.")
            finally:
                self.libraryModel.rootItem.removeRow(
                    libItem)  # self.designView.reworkDesignLibrariesView()

    def libraryEditorClick(self, s):
        """
        Open library editor dialogue.
        """
        tempDict = deepcopy(self.libraryDict)
        pathEditDlg = fd.libraryPathEditorDialog(self, tempDict)
        self.libraryDict.clear()
        if pathEditDlg.exec() == QDialog.Accepted:
            model = pathEditDlg.pathsModel
            for row in range(model.rowCount()):

                if model.itemFromIndex(model.index(row, 1)).text().strip():
                    self.libraryDict[model.itemFromIndex(
                        model.index(row, 0)).text().strip()] = pathlib.Path(
                        model.itemFromIndex(model.index(row, 1)).text().strip())
        self.writeLibDefFile(self.libraryDict,
                             pathlib.Path.cwd().joinpath('library.json'))
        self.designView.reworkDesignLibrariesView()

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
            libItem = libm.getLibItem(self.libraryModel,
                                      dlg.libNamesCB.currentText())
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
            libItem = libm.getLibItem(self.libraryModel,
                                      dlg.libNamesCB.currentText())
            cellItem = libm.getCellItem(libItem, dlg.cellCB.currentText())
            viewItem = scb.createCellView(self.appMainW,
                                          dlg.viewName.text().strip(), cellItem)
            self.createNewCellView(libItem, cellItem, viewItem)

    def createNewCellView(self, libItem, cellItem, viewItem):
        match viewItem.viewType:
            case "config":
                schViewsList = [cellItem.child(row).viewName for row in
                                range(cellItem.rowCount()) if
                                cellItem.child(row).viewType == "schematic"]

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
                    schematicWindow = schematicEditor(selectedSchItem,
                                                      self.libraryDict,
                                                      self.libBrowserCont.designView, )
                    schematicWindow.loadSchematic()
                    switchViewList = [viewName.strip() for viewName in
                                      dlg.switchViews.text().split(",")]
                    stopViewList = [viewName.strip() for viewName in
                                    dlg.stopViews.text().split(",")]
                    schematicWindow.switchViewList = switchViewList
                    schematicWindow.stopViewList = stopViewList
                    schematicWindow.configDict = dict()  # clear config dictionary
                    schematicWindow.netlistedCells = list()
                    # clear netlisted cells list
                    newConfigDict = dict()  # create an empty newconfig dict
                    schematicWindow.createConfigView(viewItem,
                                                     schematicWindow.configDict,
                                                     newConfigDict,
                                                     schematicWindow.netlistedCells, )
                    configFilePathObj = viewItem.data(Qt.UserRole + 2)
                    items = list()
                    items.insert(0, {"cellView": "config"})
                    items.insert(1, {"reference": selectedSchName})
                    items.insert(2, schematicWindow.configDict)
                    with configFilePathObj.open(mode="w+") as configFile:
                        json.dump(items, configFile, indent=4)

                    self.openConfigEditWindow(schematicWindow.configDict,
                                              selectedSchItem, viewItem)
            case "schematic":
                # scb.createCellView(self.appMainW, viewItem.viewName, cellItem)
                schematicWindow = schematicEditor(viewItem, self.libraryDict,
                                                  self.libBrowserCont.designView)
                schematicWindow.loadSchematic()
                schematicWindow.show()
            case "symbol":
                # scb.createCellView(self.appMainW, viewItem.viewName, cellItem)
                symbolWindow = symbolEditor(viewItem, self.libraryDict,
                                            self.libBrowserCont.designView)
                symbolWindow.loadSymbol()
                symbolWindow.show()
            case "veriloga":
                # scb.createCellView(self.appMainW, viewItem.viewName, cellItem)
                p = QProcess(self.appMainW)
                p.finished.connect(self.appMainW.importVerilogaClick)
                p.start(str(self.appMainW.textEditorPath), [])

    def openConfigEditWindow(self, configDict, schViewItem, viewItem):
        schematicName = schViewItem.viewName
        libItem = schViewItem.parent().parent()
        configWindow = configViewEdit(self.appMainW, schViewItem, configDict,
                                      viewItem)
        configWindow.centralWidget.libraryNameEdit.setText(libItem.libraryName)
        cellItem = viewItem.parent()
        configWindow.centralWidget.cellNameEdit.setText(cellItem.cellName)
        schViewsList = [cellItem.child(row).viewName for row in
                        range(cellItem.rowCount()) if
                        cellItem.child(row).viewType == "schematic"]
        configWindow.centralWidget.viewNameCB.addItems(schViewsList)
        configWindow.centralWidget.viewNameCB.setCurrentText(schematicName)
        configWindow.centralWidget.switchViewsEdit.setText(
            ", ".join(self.appMainW.switchViewList))
        configWindow.centralWidget.stopViewsEdit.setText(
            ", ".join(self.appMainW.stopViewList))
        configWindow.show()

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

    def openCellView(self, viewItem, cellItem, libItem):
        viewName = viewItem.viewName
        cellName = cellItem.cellName
        libName = libItem.libraryName

        if f"{libName}_{cellName}_{viewName}" in self.appMainW.openViews.keys():
            self.appMainW.openViews[
                f"{libName}_{cellName}_" f"{viewName}"].raise_()
        else:
            if viewItem.viewType == "schematic":
                schematicWindow = schematicEditor(viewItem, self.libraryDict,
                                                  self.libBrowserCont.designView)
                schematicWindow.loadSchematic()
                schematicWindow.show()
                self.appMainW.openViews[
                    f"{libName}_{cellName}_" f"{viewName}"] = schematicWindow
            elif viewItem.viewType == "symbol":
                symbolWindow = symbolEditor(viewItem, self.libraryDict,
                                            self.libBrowserCont.designView)
                symbolWindow.loadSymbol()
                symbolWindow.show()
                self.appMainW.openViews[
                    f"{libName}_{cellName}_" f"{viewName}"] = symbolWindow
            elif viewItem.viewType == "veriloga":
                with open(viewItem.viewPath) as tempFile:
                    items = json.load(tempFile)
                if items[1]["filePath"]:
                    p = QProcess(self.appMainW)
                    p.finished.connect(self.appMainW.importVerilogaClick)
                    p.start(str(self.appMainW.textEditorPath), [
                        str(viewItem.viewPath.parent.joinpath(
                            items[1]["filePath"]))])

                else:
                    self.logger.warning("File path not defined.")
            elif viewItem.viewType == "config":
                with open(viewItem.viewPath) as tempFile:
                    items = json.load(tempFile)
                viewName = items[0]["viewName"]
                schematicName = items[1]["reference"]
                schViewItem = libm.getViewItem(cellItem, schematicName)
                configDict = items[2]
                self.openConfigEditWindow(configDict, schViewItem, viewItem)

    def deleteCellViewClick(self, s):
        viewItem = self.selectCellView(self.libraryModel)
        try:
            viewItem.data(Qt.UserRole + 2).unlink()  # delete the file.
            viewItem.parent().removeRow(viewItem.row())
        except OSError as e:
            # print(f"Error:{e.strerror}")
            self.logger.warning(f"Error:{e.strerror}")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.appMainW.libraryBrowser = None
        event.accept()


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
        self.parent = parent  # type: QMainWindow
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
        # iterate design library directories. Designpath is the path of library
        # obtained from libraryDict
        # for designPath in self.libraryDict.values():  # type: Path
        #     self.populateLibrary(designPath)
        self.setModel(self.libraryModel)

    def removeLibrary(self):
        button = QMessageBox.question(self, "Library Deletion",
                                      "Are you sure to delete " "this library? This action cannot be undone.", )
        if button == QMessageBox.Yes:
            shutil.rmtree(self.selectedItem.data(Qt.UserRole + 2))
            self.libraryModel.removeRow(self.selectedItem.row())

    def saveLibAs(self):
        pass

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
            if cellName.strip() != '':
                scb.createCell(self, self.libraryModel, self.selectedItem,
                               cellName)
            else:
                self.logger.error("Please enter a cell name.")

    def copyCell(self):
        dlg = fd.copyCellDialog(self, self.libraryModel, self.selectedItem)

        if dlg.exec() == QDialog.Accepted:
            scb.copyCell(self, dlg.model, dlg.cellItem, dlg.copyName.text(),
                         dlg.selectedLibPath)

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
            viewItem = scb.createCellView(self.appMainW, dlg.nameEdit.text(),
                                          self.selectedItem)
            self.libBrowsW.createNewCellView(self.selectedItem.parent(),
                                             self.selectedItem, viewItem)

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
                selectedLibItem = libm.getLibItem(self.libraryModel,
                                                  dlg.libNamesCB.currentText())
                selectedLibPath = selectedLibItem.libraryPath
                cellName = dlg.cellCB.currentText()
                libCellNames = [selectedLibItem.child(row).cellName for row in
                                range(selectedLibItem.rowCount())]
                if (
                        cellName in libCellNames):  # check if there is the cell in the library
                    cellItem = libm.getCellItem(selectedLibItem,
                                                dlg.cellCB.currentText())
                else:
                    cellItem = scb.createCell(self.libBrowsW, self.libraryModel,
                                              selectedLibItem,
                                              dlg.cellCB.currentText(), )
                cellViewNames = [cellItem.child(row).viewName for row in
                                 range(cellItem.rowCount())]
                newViewName = dlg.viewName.text()
                if newViewName in cellViewNames:
                    self.logger.warning(
                        "View already exists. Delete cellview and try " "again.")
                else:
                    newViewPath = cellItem.data(Qt.UserRole + 2).joinpath(
                        f"{newViewName}.json")
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
                    viewPathObj.parent.joinpath(f"{newName}.json"))
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

    def reworkDesignLibrariesView(self):
        """
        Recreate library model from libraryDict.
        """
        self.libraryModel.clear()
        self.libraryModel = designLibrariesModel(self.appMainW.libraryDict)
        self.setModel(self.libraryModel)

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
                menu.addAction(QAction("Create CellView...", self,
                                       triggered=self.createCellView))
                menu.addAction(
                    QAction("Copy Cell...", self, triggered=self.copyCell))
                menu.addAction(
                    QAction("Rename Cell...", self, triggered=self.renameCell))
                menu.addAction(
                    QAction("Delete Cell...", self, triggered=self.deleteCell))
            elif self.selectedItem.data(Qt.UserRole + 1) == "view":
                menu.addAction(
                    QAction("Open View", self, triggered=self.openView))
                menu.addAction(
                    QAction("Copy View...", self, triggered=self.copyView))
                menu.addAction(
                    QAction("Rename View...", self, triggered=self.renameView))
                menu.addAction(
                    QAction("Delete View...", self, triggered=self.deleteView))
            menu.exec(event.globalPos())
        except UnboundLocalError:
            pass


class designLibrariesModel(QStandardItemModel):
    def __init__(self, libraryDict):
        self.libraryDict = libraryDict
        super().__init__()
        self.rootItem = self.invisibleRootItem()
        self.setHorizontalHeaderLabels(["Libraries"])
        for designPath in self.libraryDict.values():
            self.populateLibrary(designPath)

    def populateLibrary(self, designPath):  # designPath: Path
        """
        Populate library view.
        """
        if designPath.joinpath("reveda.lib").exists():
            libraryItem = self.addLibraryToModel(designPath)
            cellList = [cell.name for cell in designPath.iterdir() if
                        cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell),
                                               libraryItem)
                viewList = [view.name for view in
                            designPath.joinpath(cell).iterdir() if
                            view.suffix == ".json"]
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
        parentItem.appendRow(viewEntry)  # return viewEntry


class libraryPathsModel(QStandardItemModel):
    def __init__(self, libraryDict):
        super().__init__()
        self.libraryDict = libraryDict
        self.setHorizontalHeaderLabels(['Library Name', 'Library Path'])
        for key, value in self.libraryDict.items():
            libName = QStandardItem(key)
            libPath = QStandardItem(str(value))
            self.appendRow(libName, libPath)
        self.appendRow(QStandardItem('Click here...'), QStandardItem(''))


class libraryPathsTableView(QTableView):
    def __init__(self, model):
        self.model = model
        self.setModel(self.model)
        self.setShowGrid(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def contextMenuEvent(self, event) -> None:
        self.menu = QMenu(self)
        removePathAction = QAction('Remove Library Path...', self.menu)
        removePathAction.triggered.connect(lambda: self.removeLibraryPath(event))
        self.menu.addAction(removePathAction)
        self.menu.popup(QCursor.pos())

    def removeLibraryPath(self, event):
        print('remove library path')


class symbolViewsModel(designLibrariesModel):
    def __init__(self, libraryDict):
        super().__init__(libraryDict)

    def populateLibrary(self, designPath):  # designPath: Path
        """
        Populate library view.
        """
        if designPath.joinpath("reveda.lib").exists():
            libraryItem = self.addLibraryToModel(designPath)
            cellList = [cell.name for cell in designPath.iterdir() if
                        cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell),
                                               libraryItem)
                viewList = [view.name for view in
                            designPath.joinpath(cell).iterdir() if
                            view.suffix == ".json" and "symbol" in view.name]
                for view in viewList:
                    self.addViewToModel(designPath.joinpath(cell, view), cellItem)


class xyceNetlist:
    def __init__(self, schematic: schematicEditor, filePathObj: pathlib.Path,
                 use_config: bool = False):
        self.filePathObj = filePathObj
        self.schematic = schematic
        self.scene = self.schematic.centralW.scene
        self.libraryDict = self.schematic.libraryDict
        self.libraryView = self.schematic.libraryView
        self._configDict = None
        self.libItem = libm.getLibItem(self.schematic.libraryView.libraryModel,
                                       self.schematic.libName, )
        self.cellItem = libm.getCellItem(self.libItem, self.schematic.cellName)
        self.use_config = use_config
        self.switchViewList = schematic.switchViewList
        self.netlistedViews = dict()

    def writeNetlist(self):
        with self.filePathObj.open(mode="w") as cirFile:
            cirFile.write(f'{80 * "*"}\n')
            cirFile.write("* Revolution EDA CDL Netlist\n")
            cirFile.write(f"* Library: {self.schematic.libName}\n")
            cirFile.write(f"* Top Cell Name: {self.schematic.cellName}\n")
            cirFile.write(f"* View Name: {self.schematic.viewName}\n")
            cirFile.write(f"* Date: {datetime.datetime.now()}\n")
            cirFile.write(f'{80 * "*"}\n')
            cirFile.write(".GLOBAL gnd!\n")
            cirFile.write("\n")
            self.recursiveNetlisting(self.schematic, cirFile, self.use_config)
            cirFile.write(".END\n")

    @property
    def configDict(self):
        return self._configDict

    @configDict.setter
    def configDict(self, value: dict):
        if value:
            self._configDict = value

    def recursiveNetlisting(self, schematic: schematicEditor, cirFile,
                            use_config: bool = False):
        """
        Recursively traverse all sub-circuits and netlist them.
        """
        # self.analyseSchematic(self.schematic)
        scene = schematic.centralW.scene
        scene.groupAllNets()  # name all nets in the schematic
        sceneSymbolSet = scene.findSceneSymbolSet()
        scene.generatePinNetMap(sceneSymbolSet)
        for item in sceneSymbolSet:
            libItem = libm.getLibItem(schematic.libraryView.libraryModel,
                                      item.libraryName)
            cellItem = libm.getCellItem(libItem, item.cellName)
            viewItems = [cellItem.child(row) for row in
                         range(cellItem.rowCount())]
            viewNames = [view.viewName for view in viewItems]

            viewDict = dict(zip(viewNames, viewItems))
            if use_config:
                netlistableViews = [self.configDict.get(item.cellName)[1]]
            else:
                netlistableViews = [viewItemName for viewItemName in
                                    self.switchViewList if
                                    viewItemName in viewNames]
            self.createItemLine(cirFile, item, libItem, netlistableViews,
                                viewDict)

    def createItemLine(self, cirFile, item, libItem, netlistableViews, viewDict):
        for view in netlistableViews:
            if view in viewDict.keys():
                if viewDict[view].viewType == "schematic":
                    schematicObj = schematicEditor(viewDict[view],
                                                   self.libraryDict,
                                                   self.libraryView, )
                    schematicObj.loadSchematic()
                    pins = " ".join(list(item.pinNetMap.keys()))
                    nets = " ".join(list(item.pinNetMap.values()))
                    cirFile.write(
                        f"X{item.instanceName} {nets} {item.cellName}\n")
                    if item.cellName not in self.netlistedViews.keys():
                        self.netlistedViews[item.cellName] = [libItem.libraryName,
                                                              view, ]
                        cirFile.write(f".SUBCKT {item.cellName} {pins}\n")
                        self.recursiveNetlisting(schematicObj, cirFile)
                        cirFile.write(".ENDS\n")
                elif viewDict[view].viewType == "veriloga":
                    with viewDict[view].data(Qt.UserRole + 2).open(
                            mode="r") as vaview:
                        items = json.load(vaview)
                    netlistLine = items[3]['netlistLine']
                    netlistLine = netlistLine.replace("[@instName]",
                                                      f"{item.instanceName}")
                    for pinName, netName in item.pinNetMap.items():
                        netlistLine = netlistLine.replace(f"[|{pinName}:%]",
                                                          f"{netName}")
                    for labelItem in item.labels.values():
                        if labelItem.labelDefinition in netlistLine:
                            netlistLine = netlistLine.replace(
                                labelItem.labelDefinition, labelItem.labelText)
                    cirFile.write(f"{netlistLine}\n")
                    modelParamsLine = ', '.join(
                        ' = '.join((key, val)) for (key, val) in
                        item.attr.items())
                    modelLine = f'.MODEL {item.labels["vaModel"].labelValue} ' \
                                f'{item.labels["vaModule"].labelValue} {modelParamsLine}'
                    cirFile.write(f'{modelLine}\n')
                    self.netlistedViews[item.cellName] = [libItem.libraryName,
                                                          "veriloga", ]
                elif viewDict[view].viewType == "symbol":
                    cirFile.write(f"{item.createNetlistLine()}\n")
                    self.netlistedViews[item.cellName] = [libItem.libraryName,
                                                          "symbol", ]
                break


class configViewEdit(QMainWindow):
    def __init__(self, appmainW, schViewItem, configDict, viewItem):
        super().__init__(parent=appmainW)
        self.appmainW = appmainW  # app mainwindow
        self.schViewItem = schViewItem
        self.configDict = configDict
        self.viewItem = viewItem
        self.setWindowTitle('Edit Config View')
        self.setMinimumSize(500, 600)
        self._createMenuBar()
        self._createActions()
        self._addActions()
        self._createTriggers()
        self.centralWidget = configViewEditContainer(self)
        self.setCentralWidget(self.centralWidget)

    def _createMenuBar(self):
        self.mainMenu = self.menuBar()
        self.fileMenu = self.mainMenu.addMenu("&File")
        self.editMenu = self.mainMenu.addMenu("&Edit")
        self.status_bar = self.statusBar()
        self.status_bar.showMessage('Ready')

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
            viewList = [item.strip() for item in
                        model.itemFromIndex(model.index(i, 3)).text().split(',')]
            self.configDict[model.item(i, 1).text()] = [model.item(i, 0).text(),
                                                        model.item(i, 2).text(),
                                                        viewList]
        if self.appmainW.libraryBrowser is None:
            self.appmainW.createLibraryBrowser()
        topSchematicWindow = schematicEditor(self.schViewItem,
                                             self.appmainW.libraryDict,
                                             self.appmainW.libraryBrowser.libBrowserCont.designView)
        topSchematicWindow.loadSchematic()
        topSchematicWindow.createConfigView(self.viewItem, self.configDict,
                                            newConfigDict, [])
        self.configDict = newConfigDict

        self.centralWidget.confModel = configModel(self.configDict)
        # self.centralWidget.configDictGroup.setVisible(False)
        self.centralWidget.configDictLayout.removeWidget(
            self.centralWidget.configViewTable)
        self.centralWidget.configViewTable = configTable(
            self.centralWidget.confModel)
        self.centralWidget.configDictLayout.addWidget(
            self.centralWidget.configViewTable)  # self.centralWidget.configDictGroup.setVisible(True)

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
        topCellGroup = QGroupBox('Top Cell')
        topCellLayout = QFormLayout()
        self.libraryNameEdit = edf.longLineEdit()
        topCellLayout.addRow(edf.boldLabel('Library:'), self.libraryNameEdit)
        self.cellNameEdit = edf.longLineEdit()
        topCellLayout.addRow(edf.boldLabel('Cell:'), self.cellNameEdit)
        self.viewNameCB = QComboBox()
        topCellLayout.addRow(edf.boldLabel('View:'), self.viewNameCB)
        topCellGroup.setLayout(topCellLayout)
        self.mainLayout.addWidget(topCellGroup)
        viewGroup = QGroupBox('Switch/Stop Views')
        viewGroupLayout = QFormLayout()
        viewGroup.setLayout(viewGroupLayout)
        self.switchViewsEdit = edf.longLineEdit()
        viewGroupLayout.addRow(edf.boldLabel('View List:'), self.switchViewsEdit)
        self.stopViewsEdit = edf.longLineEdit()
        viewGroupLayout.addRow(edf.boldLabel('Stop List:'), self.stopViewsEdit)
        self.mainLayout.addWidget(viewGroup)
        self.configDictGroup = QGroupBox('Cell View Configuration')
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
            ['Library', 'Cell Name', 'View Found', 'View To '
                                                   'Use'])
        for i, (k, v) in enumerate(configDict.items()):
            item = QStandardItem(v[0])
            self.setItem(i, 0, item)
            item = QStandardItem(k)
            self.setItem(i, 1, item)
            item = QStandardItem(v[1])
            self.setItem(i, 2, item)
            item = QStandardItem(', '.join(v[2]))
            self.setItem(i, 3, item)


class configTable(QTableView):
    def __init__(self, model: configModel):
        super().__init__()
        self.model = model
        self.setModel(self.model)
        self.combos = list()
        for row in range(self.model.rowCount()):
            self.combos.append(QComboBox())
            items = [item.strip() for item in self.model.itemFromIndex(
                self.model.index(row, 3)).text().split(',')]
            self.combos[-1].addItems(items)
            self.combos[-1].setCurrentText(
                self.model.itemFromIndex(self.model.index(row, 2)).text())
            self.setIndexWidget(self.model.index(row, 3), self.combos[-1])

    def updateModel(self):
        for row in range(self.model.rowCount()):
            item = QStandardItem(self.combos[row].currentText())
            self.model.setItem(row, 2, item)


class runXNetlistThread(QRunnable):
    def __init__(self, netlistObj: xyceNetlist, parent):
        super().__init__()
        self.netlistObj = netlistObj
        self.parent = parent

    def run(self) -> None:
        self.netlistObj.writeNetlist()
        self.parent.logger.info('Netlisting finished')
