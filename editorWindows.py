"""
======================= START OF LICENSE NOTICE =======================
  Copyright (C) 2022 Murat Eskiyerli. All Rights Reserved

  NO WARRANTY. THE PRODUCT IS PROVIDED BY DEVELOPER "AS IS" AND ANY
  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL DEVELOPER BE LIABLE FOR
  ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
  GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
  IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
  OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THE PRODUCT, EVEN
  IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
======================== END OF LICENSE NOTICE ========================
  Primary Author: Murat Eskiyerli

"""

# from hashlib import new
import pathlib
import temppathlib
import json
import shutil
# import numpy as np
from PySide6.QtCore import QRect, QTemporaryFile
from PySide6.QtGui import (QAction, QBrush, QColor, QCursor, QFont,
                           QFontMetrics, QIcon, QKeySequence, QPainter, QPen,
                           QStandardItemModel, QTransform, QUndoCommand,
                           QUndoStack)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QComboBox, QDialog,
                               QDialogButtonBox, QFileDialog, QFormLayout,
                               QGraphicsItem, QGraphicsLineItem, QGraphicsItemGroup,
                               QGraphicsRectItem, QGraphicsScene,
                               QGraphicsView, QGridLayout, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QMenu, QMessageBox, QPushButton, QRadioButton,
                               QTabWidget, QToolBar, QTreeView, QVBoxLayout, QGraphicsSceneMouseEvent,
                               QWidget)

import circuitElements as cel
import libraryWindow as libw
import loadJSON as lj
import propertyDialogues as pdlg
import pythonConsole as pcon
import resources
import schBackEnd as scb  # import the backend
import shape as shp  # import the shapes
import symbolEncoder as se
import undoStack as us
from Point import *
from Vector import *


class editorWindow(QMainWindow):
    def __init__(self, file: pathlib.Path, libraryDict: dict):  # file is a pathlib.Path object
        super().__init__()
        self.file = file
        self.libraryDict = libraryDict
        self._createActions()
        self._createTriggers()
        self._createShortcuts()
        self.init_UI()

    def init_UI(self):
        pass

    def _createMenuBar(self):
        self.editorMenuBar = self.menuBar()
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
        self.moveOriginAction.triggered.connect(self.moveOrigin)

    def _createShortcuts(self):
        self.redoAction.setShortcut("Shift+U")
        self.undoAction.setShortcut("U")
        self.objPropAction.setShortcut(Qt.Key_Q)
        self.copyAction.setShortcut("C")
        self.deleteAction.setShortcut(QKeySequence.Delete)

    def dispConfDialog(self):
        dcd = displayConfigDialog(self)
        if dcd.exec() == QDialog.Accepted:
            self.centralW.scene.gridMajor = dcd.majorGridEntry.text()
            self.centralW.scene.update()
            self.centralW.view.update()


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

    def moveOrigin(self):
        # self.centralW.scene.moveOrigin()
        pass

class schematicEditor(editorWindow):
    def __init__(self, file: pathlib.Path, libraryDict: dict) -> None:
        super().__init__(file=file, libraryDict=libraryDict)
        self.setWindowTitle(f"Schematic Editor - {file.parent.stem}")
        self.setWindowIcon(QIcon(":/icons/layer-shape.png"))
        self.symbolChooser = None
        self.cellViews = ['symbol']  # only symbol can be instantiated in the schematic window.

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = schematicContainer(self)
        self.setCentralWidget(self.centralW)
        self.statusLine = self.statusBar()

    def _createTriggers(self):
        super()._createTriggers()
        self.createWireAction.triggered.connect(self.createWireClick)
        self.createInstAction.triggered.connect(self.createInstClick)

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

    def _createShortcuts(self):
        super()._createShortcuts()
        self.createInstAction.setShortcut(Qt.Key_I)
        self.createWireAction.setShortcut(Qt.Key_W)

    def createWireClick(self, s):
        pass

    def createInstClick(self, s):
        revEDAPathObj = pathlib.Path(__file__)
        revEDADirObj = revEDAPathObj.parent
        print(f'schematic scene: {self.centralW.scene}')
        if self.symbolChooser is None:
            self.symbolChooser = libw.symbolChooser(
                self.libraryDict, self.cellViews, self.centralW.scene
            )  # create the library browser
            self.symbolChooser.show()
        else:
            self.symbolChooser.show()


class symbolEditor(editorWindow):
    def __init__(self, file, libraryDict):
        super().__init__(file=file, libraryDict=libraryDict)
        self.file = file
        self.setWindowTitle(f"Symbol Editor - {file.parent.stem}")
        self._symbolActions()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = symbolContainer(self)
        self.setCentralWidget(self.centralW)
        self.statusLine = self.statusBar()

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
        self.centralW.scene.undoStack.undo()

    def redoClick(self, s):
        self.centralW.scene.undoStack.redo()

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
        self.vLayout = QVBoxLayout()

        # dispOptionsTabs = QTabWidget(self)
        # # Grid Display Options tab
        # displayTab = QWidget()
        # # layout for displayTab
        # vBox = QVBoxLayout()
        # gridGrBox = QGroupBox("Display Grid")
        # noGrid = QRadioButton("None")
        # dotGrid = QRadioButton("Dots")
        # dotGrid.setChecked(True)
        # lineGrid = QRadioButton("Lines")
        # gRLayout = QHBoxLayout()
        # # create a logical group of grid option buttons
        # gridButtonGroup = QButtonGroup()
        # gridButtonGroup.addButton(noGrid)
        # gridButtonGroup.addButton(dotGrid)
        # gridButtonGroup.addButton(lineGrid)
        # gRLayout.addWidget(noGrid)
        # gRLayout.addWidget(dotGrid)
        # gRLayout.addWidget(lineGrid)
        # gRLayout.addStretch(1)
        # gridGrBox.setLayout(gRLayout)
        # #  gridGrBox.setLayout(gRLayout)
        # # add to top row of display tab
        # vBox.addWidget(gridGrBox)
        # # create a form layout
        # gridFormWidget = QWidget()
        fLayout = QFormLayout(self)
        self.majorGridEntry = QLineEdit()
        if self.parent.centralW.scene.gridMajor:
            self.majorGridEntry.setText(str(self.parent.centralW.scene.gridMajor))
        else:
            self.majorGridEntry.setText("10")
        # self.minorGridEntry = QLineEdit()
        # self.minorGridEntry.setText("5")
        fLayout.addRow("Major Grid:", self.majorGridEntry)
        self.vLayout.addLayout(fLayout, 1)
        # fLayout.addRow("Minor Grid Spacing", self.minorGridEntry)
        # gridFormWidget.setLayout(fLayout)
        # vBox.addWidget(gridFormWidget)
        # displayTab.setLayout(vBox)

        # dispOptionsTabs.insertTab(0, displayTab, "Display Options")
        # self.layout.addWidget(dispOptionsTabs)
        # self.layout.addWidget(self.buttonBox)
        # self.setLayout(self.vBoxLayout)
        # need to change this later
        # self.setGeometry(300, 300, 300, 200)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        # self.vBoxLayout = QVBoxLayout()
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.vLayout.addWidget(self.buttonBox)
        self.setLayout(self.vLayout)
        self.show()



class symbolContainer(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.init_UI()

    def init_UI(self):
        self.scene = symbol_scene(self)
        self.view = symbol_view(self.scene, self)

        # layout statements, using a grid layout
        gLayout = QGridLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.view, 0, 0)
        # ratio of first column to second column is 5
        gLayout.setColumnStretch(0, 5)
        gLayout.setRowStretch(0, 6)
        self.setLayout(gLayout)


class schematicContainer(QWidget):
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


class editor_scene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.gridMajor = 10
        self.gridTuple = (self.gridMajor, self.gridMajor)
        self.selectedItem = None  # selected item
        self.defineSceneLayers()
        self.setPens()
        self.undoStack = QUndoStack()

    def setPens(self):
        self.wirePen = QPen(self.wireLayer.color, 2)
        self.wirePen.setCosmetic(True)
        self.symbolPen = QPen(self.symbolLayer.color, 3)
        self.symbolPen.setCosmetic(True)
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

    def snapGrid(self, number, base):
        return base * int(math.floor(number / base))

    def snap2Grid(self, point: QPoint, gridTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(
            gridTuple[0] * int(round(point.x() / gridTuple[0])),
            gridTuple[1] * int(round(point.y() / gridTuple[1])),
        )

class symbol_scene(editor_scene):
    '''
    Scene for Symbol editor.
    '''

    def __init__(self, parent):
        super().__init__(parent)
        # drawing switches
        self.resetSceneMode()  # reset to select mode
        # pen definitions
        self.setPens()
        self.symbolContextMenu = QMenu()

    def mousePressEvent(self, mouse_event):
        snapped_pos = self.snap2Grid(mouse_event.scenePos(), self.gridTuple)
        if self.selectItem and self.items(snapped_pos):
            self.itemsAtMousePress = self.items(snapped_pos)
            self.selectedItem = self.itemsAtMousePress[0]
            self.selectedItem.setSelected(True)
        elif not (self.selectItem or hasattr(self, "start")):
            self.start = snapped_pos
            self.selectedItem = None
        super().mousePressEvent(mouse_event)

    def mouseMoveEvent(self, mouse_event):
        self.current = self.snap2Grid(mouse_event.scenePos(), self.gridTuple)
        pen = QPen(self.guideLineLayer.color, 1)
        pen.setStyle(Qt.DashLine)
        if hasattr(self, "draftItem"):
            self.removeItem(self.draftItem)  # remove ghost item
            del self.draftItem
        elif self.drawLine and hasattr(self, "start") == True:
            self.draftItem = shp.line(self.start, self.current, pen, self.gridTuple)
            self.addItem(self.draftItem)
        elif self.drawRect and hasattr(self, "start") == True:
            self.draftItem = shp.rectangle(
                self.start, self.current, pen, self.gridTuple
            )
            self.addItem(self.draftItem)
        elif self.drawPin:  # draw pin
            self.draftItem = shp.pin(
                self.current,
                pen,
                self.pinName,
                self.pinDir,
                self.pinType,
                self.gridTuple,
            )  # draw pin
            self.addItem(self.draftItem)
        elif self.addLabel:  # draw label
            self.draftItem = shp.label(
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
            self.addItem(self.draftItem)
        self.parent.parent.statusLine.showMessage(
            "Cursor Position: " + str(self.current.toTuple())
        )

        super().mouseMoveEvent(mouse_event)

    def mouseReleaseEvent(self, mouse_event):
        if hasattr(self, "draftItem"):  # remove ghost item
            self.removeItem(self.draftItem)
            del self.draftItem
            if self.drawLine:
                self.lineDraw(self.start, self.current, self.symbolPen, self.gridTuple)
            elif self.drawRect:
                self.rectDraw(self.start, self.current, self.symbolPen, self.gridTuple)
            elif self.drawPin:
                self.pinDraw(
                    self.current,
                    self.pinPen,
                    self.pinName,
                    self.pinDir,
                    self.pinType,
                    self.gridTuple,
                )  # draw pin
            elif self.addLabel:
                self.labelDraw(self.labelPen)
        if hasattr(self, "start"):
            del self.start
        super().mouseReleaseEvent(mouse_event)

    def lineDraw(self, start: QPoint, current: QPoint, pen: QPen, gridTuple: tuple):
        line = shp.line(
            start, current - QPoint(pen.width() / 2, pen.width() / 2), pen, gridTuple
        )
        self.addItem(line)
        undoCommand = us.addShapeUndo(self, line)
        self.undoStack.push(undoCommand)
        self.drawLine = False

    def rectDraw(self, start: QPoint, end: QPoint, pen: QPen, gridTuple: tuple):
        """
        Draws a rectangle on the scene
        """
        rect = shp.rectangle(
            start, end - QPoint(pen.width() / 2, pen.width() / 2), pen, gridTuple
        )
        self.addItem(rect)
        undoCommand = us.addShapeUndo(self, rect)
        self.undoStack.push(undoCommand)
        self.drawRect = False

    def pinDraw(
            self, current, pen: QPen, pinName: str, pinDir, pinType, gridTuple: tuple
    ):
        pin = shp.pin(current, pen, pinName, pinDir, pinType, gridTuple)
        self.addItem(pin)
        undoCommand = us.addShapeUndo(self, pin)
        self.undoStack.push(undoCommand)
        self.drawPin = False

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
        undoCommand = us.addShapeUndo(self, label)
        self.undoStack.push(undoCommand)
        self.addLabel = False

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
        """
        Change the selected item.
        """
        self.selectedItem.setSelected(False)
        self.selectedItem = self.itemsAtMousePress[i]
        self.selectedItem.setSelected(True)

    def resetSceneMode(self):
        """
        Reset the scene mode to default. Select mode is set to True.
        """
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
            del self.selectedItem
            self.update()
            self.selectItem = True

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
        undoUpdateRectangle = us.updateShapeUndo()
        us.keepOriginalShape(
            self, self.selectedItem, self.gridTuple, parent=undoUpdateRectangle
        )
        self.selectedItem.start = QPoint(newLeft, newTop)
        self.selectedItem.end = QPoint(newLeft + newWidth, newTop + newHeight)
        self.selectedItem.setLeft(newLeft)
        self.selectedItem.setTop(newTop)
        self.selectedItem.setWidth(newWidth)
        self.selectedItem.setHeight(newHeight)
        us.changeOriginalShape(self, self.selectedItem, parent=undoUpdateRectangle)
        self.undoStack.push(undoUpdateRectangle)
        self.selectedItem.update()

    def updateLineShape(self):
        location = self.selectedItem.scenePos().toTuple()
        self.selectedItem.start = self.snap2Grid(
            QPoint(
                float(self.queryDlg.startXLine.text()) - float(location[0]),
                float(self.queryDlg.startYLine.text()) - float(location[1]),
            ),
            self.gridTuple,
        )
        self.selectedItem.end = self.snap2Grid(
            QPoint(
                float(self.queryDlg.endXLine.text()) - float(location[0]),
                float(self.queryDlg.endYLine.text()) - float(location[1]),
            ),
            self.gridTuple,
        )

        self.selectedItem.update()

    def updatePinShape(self):
        location = self.selectedItem.scenePos().toTuple()
        self.selectedItem.start = self.snap2Grid(
            QPoint(
                float(self.queryDlg.pinXLine.text()) - float(location[0]),
                float(self.queryDlg.pinYLine.text()) - float(location[1]),
            ),
            self.gridTuple,
        )
        self.selectedItem.rect = QRect(
            self.selectedItem.start.x() - 5, self.selectedItem.start.y() - 5, 10, 10
        )
        self.selectedItem.pinName = self.queryDlg.pinName.text()
        self.selectedItem.pinType = self.queryDlg.pinType.currentText()
        self.selectedItem.pinDir = self.queryDlg.pinDir.currentText()
        self.selectedItem.update()

    def updateLabelShape(self):
        """
        update pin shape with new values.
        """
        location = self.selectedItem.scenePos().toTuple()
        self.selectedItem.start = self.snap2Grid(
            QPoint(
                float(self.queryDlg.labelXLine.text()) - float(location[0]),
                float(self.queryDlg.labelYLine.text()) - float(location[1]),
            ),
            self.gridTuple,
        )
        self.selectedItem.labelName = self.queryDlg.labelNameEdit.text()
        self.selectedItem.labelHeight = self.queryDlg.labelHeightEdit.text()
        self.selectedItem.labelAlign = self.queryDlg.labelAlignCombo.currentText()
        self.selectedItem.labelOrient = self.queryDlg.labelOrientCombo.currentText()
        self.selectedItem.labelUse = self.queryDlg.labelUseCombo.currentText()
        if self.queryDlg.normalType.isChecked():
            self.selectedItem.labelType = shp.label.labelTypes[0]
        elif self.queryDlg.NLPType.isChecked():
            self.selectedItem.labelType = shp.label.labelTypes[1]
        elif self.queryDlg.pyLType.isChecked():
            self.selectedItem.labelType = shp.label.labelTypes[2]
        self.selectedItem.update()

    def loadSymbol(self, file):
        self.attributeList = []
        with temppathlib.NamedTemporaryFile() as temp:
            shutil.copy(file, temp.path.name)
            try:
                items = json.load(open(temp.path.name))
                for item in items:
                    if (
                            item["type"] == "rect"
                            or item["type"] == "line"
                            or item["type"] == "pin"
                            or item["type"] == "label"
                    ):
                        itemShape = lj.createSymbolItems(item, self.gridTuple)
                        self.addItem(itemShape)
                    elif item["type"] == "attribute":
                        attr = lj.createSymbolAttribute(item)
                        self.attributeList.append(attr)

            except json.decoder.JSONDecodeError:
                print("Invalid JSON file")

    def saveSymbolCell(self, fileName):
        self.sceneR = self.sceneRect()  # get scene rect
        items = self.items(self.sceneR)  # get items in scene rect
        items.extend(self.attributeList)  # add attribute list to list
        with open(fileName, "w") as f:
            json.dump(items, f, cls=se.symbolEncoder, indent=4)

    def stretchSelectedItem(self):
        if self.selectedItem is not None:
            self.selectedItem.stretch = True

    def viewSymbolProperties(self):
        symbolPropDialogue = pdlg.symbolLabelsDialogue(
            self.parent.parent, self.items(), self.attributeList
        )
        self.attributeList = []
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
            for i, item in enumerate(symbolPropDialogue.attributeNameList):
                if item.text().strip() != "":
                    self.attributeList.append(
                        se.symbolAttribute(
                            item.text(),
                            symbolPropDialogue.attributeTypeList[i].currentText(),
                            symbolPropDialogue.attributeDefList[i].text(),
                        )
                    )


class schematic_scene(editor_scene):
    def __init__(self, parent):
        super().__init__(parent)
        self.instCounter = 0
        self.current = QPoint(0, 0)
        self.itemsAtMousePress = []

    def mousePressEvent(self, mouse_event:QGraphicsSceneMouseEvent) -> None:
        snapped_pos = self.snap2Grid(mouse_event.scenePos(), self.gridTuple)
        if mouse_event.button() == Qt.LeftButton:
            if self.items(snapped_pos):
                self.itemsAtMousePress = self.items(snapped_pos)
                self.selectedItem = self.itemsAtMousePress[0]
                self.selectedItem.setSelected(True)
                self.selectedItem.setFocus()
        super().mousePressEvent(mouse_event)

    def mouseMoveEvent(self, event:QGraphicsSceneMouseEvent) -> None:
        self.current = self.snap2Grid(event.scenePos(), self.gridTuple)
        self.parent.parent.statusLine.showMessage(
            "Cursor Position: " + str(self.current.toTuple())
        )
        super().mouseMoveEvent(event)

    def instSymbol(self, file: pathlib.Path):
        symbolInstance = shp.symbolInst(self)  # create symbol instance        with temppathlib.NamedTemporaryFile() as temp:
        with temppathlib.NamedTemporaryFile() as temp:
            shutil.copy(file, temp.path.name)
            try:
                items = json.load(open(temp.path.name))
                for item in items:
                    if (
                            item["type"] == "rect"
                            or item["type"] == "line"
                            or item["type"] == "pin"
                            or item["type"] == "label"
                    ):
                        itemShape = lj.createSymbolItems(item, self.gridTuple)
                        symbolInstance.addToGroup(itemShape)
                symbolInstance.setData(0, self.instCounter)
                symbolInstance.setPos(300,300)
                self.addItem(symbolInstance)  # add symbol instance to scene
                symbolInstance.setPos(self.current)
                print(f'scene position: {symbolInstance.scenePos().toTuple()}')
                self.instCounter += 1

            except json.decoder.JSONDecodeError:
                print("Invalid JSON file")


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


class symbol_view(editor_view):
    def __int__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)


class schematic_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
