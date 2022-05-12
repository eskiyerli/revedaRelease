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
import json
import shutil

# import numpy as np
import copy

from PySide6.QtCore import (QRect, QTemporaryFile, QMargins, )
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QCursor,
    QFont,
    QFontMetrics,
    QIcon,
    QKeySequence,
    QPainter,
    QPen,
    QStandardItemModel,
    QTransform,
    QUndoCommand,
    QUndoStack,
    QTextDocument,
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
    QGraphicsEllipseItem,
    QGraphicsItemGroup,
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
    QGraphicsSceneMouseEvent,
    QWidget,
)

import circuitElements as cel
import libraryWindow as libw
import loadJSON as lj
import propertyDialogues as pdlg
import pythonConsole as pcon
import resources
import schBackEnd as scb  # import the backend
import shape as shp  # import the shapes
import net
import symbolEncoder as se
import undoStack as us
from Point import *
from Vector import *


class editorWindow(QMainWindow):
    def __init__(
            self, file: pathlib.Path, libraryDict: dict, libraryView
    ):  # file is a pathlib.Path object
        super().__init__()
        self.file = file
        self.libraryDict = libraryDict
        self.libraryView = libraryView
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
        self.readOnlyCellAction = QAction(
            self.readOnlyCellIcon, "Make Read Only", self
        )

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
        self.dispConfigAction = QAction(
            dispConfigIcon, "Display Config...", self
        )

        selectConfigIcon = QIcon(":/icons/zone-select.png")
        self.selectConfigAction = QAction(
            selectConfigIcon, "Selection Config...", self
        )

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
        self.createLabelAction = QAction(
            createLabelIcon, "Create Label...", self
        )

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
        self.viewPropAction = QAction(
            viewPropIcon, "Cellview Properties...", self
        )

        viewCheckIcon = QIcon(":/icons/ui-check-box.png")
        self.viewCheckAction = QAction(viewCheckIcon, "Check CellView", self)

        viewErrorsIcon = QIcon(":/icons/report--exclamation.png")
        self.viewErrorsAction = QAction(viewErrorsIcon, "View Errors...", self)

        deleteErrorsIcon = QIcon(":/icons/report--minus.png")
        self.deleteErrorsAction = QAction(
            deleteErrorsIcon, "Delete Errors...", self
        )

        netlistIcon = QIcon(":/icons/script-text.png")
        self.netlistAction = QAction(netlistIcon, "Create Netlist...", self)

        simulateIcon = QIcon(":/icons/application-wave.png")
        self.simulateAction = QAction(simulateIcon, "Run RevEDA Sim GUI", self)

        createLineIcon = QIcon(":/icons/layer-shape-line.png")
        self.createLineAction = QAction(createLineIcon, "Create Line...", self)

        createRectIcon = QIcon(":/icons/layer-shape.png")
        self.createRectAction = QAction(
            createRectIcon, "Create Rectangle...", self
        )

        createPolyIcon = QIcon(":/icons/layer-shape-polygon.png")
        self.createPolyAction = QAction(
            createPolyIcon, "Create Polygon...", self
        )

        createCircleIcon = QIcon(":/icons/layer-shape-ellipse.png")
        self.createCircleAction = QAction(
            createCircleIcon, "Create Circle...", self
        )

        createArcIcon = QIcon(":/icons/layer-shape-polyline.png")
        self.createArcAction = QAction(createArcIcon, "Create Arc...", self)

        createInstIcon = QIcon(":/icons/block--plus.png")
        self.createInstAction = QAction(
            createInstIcon, "Create Instance...", self
        )

        createWireIcon = QIcon(":/icons/node-insert.png")
        self.createWireAction = QAction(createWireIcon, "Create Wire...", self)

        createBusIcon = QIcon(":/icons/node-select-all.png")
        self.createBusAction = QAction(createBusIcon, "Create Bus...", self)

        createLabelIcon = QIcon(":/icons/tag-label-yellow.png")
        self.createLabelAction = QAction(
            createLabelIcon, "Create Label...", self
        )

        createPinIcon = QIcon(":/icons/pin--plus.png")
        self.createPinAction = QAction(createPinIcon, "Create Pin...", self)

        createSymbolIcon = QIcon(":/icons/application-block.png")
        self.createSymbolAction = QAction(
            createSymbolIcon, "Create Symbol...", self
        )

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
        self.undoAction.setShortcut(Qt.Key_U)
        self.objPropAction.setShortcut(Qt.Key_Q)
        self.copyAction.setShortcut("C")
        self.deleteAction.setShortcut(QKeySequence.Delete)

    def dispConfDialog(self):
        dcd = displayConfigDialog(self)
        if dcd.exec() == QDialog.Accepted:
            gridValue = int(float(dcd.majorGridEntry.text()))
            self.centralW.scene.gridMajor = gridValue
            self.centralW.view.gridMajor = gridValue
            self.centralW.scene.gridTuple = (gridValue, gridValue)
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
        self.centralW.scene.changeOrigin = True


class schematicEditor(editorWindow):
    def __init__(self, file: pathlib.Path, libraryDict: dict, libraryView
                 ) -> None:
        super().__init__(
            file=file, libraryDict=libraryDict, libraryView=libraryView
        )
        self.setWindowTitle(f"Schematic Editor - {file.parent.stem}")
        self.setWindowIcon(QIcon(":/icons/layer-shape.png"))
        self.symbolChooser = None
        self.cellViews = [
            "symbol"
        ]  # only symbol can be instantiated in the schematic window.
        self._schematicActions()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createToolBars()
        # create container to position all widgets
        self.centralW = schematicContainer(self)
        self.setCentralWidget(self.centralW)
        self.statusLine = self.statusBar()
        self.messageLine = QLabel()  # message line
        self.statusLine.addPermanentWidget(self.messageLine)

    def _createTriggers(self):
        super()._createTriggers()
        self.checkCellAction.triggered.connect(self.checkSaveCell)
        self.createWireAction.triggered.connect(self.createWireClick)
        self.createInstAction.triggered.connect(self.createInstClick)
        self.copyAction.triggered.connect(self.copyClick)
        self.deleteAction.triggered.connect(self.deleteClick)
        self.objPropAction.triggered.connect(self.objPropClick)

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

    def _schematicActions(self):
        self.centralW.scene.itemContextMenu.addAction(self.copyAction)
        self.centralW.scene.itemContextMenu.addAction(self.moveAction)
        self.centralW.scene.itemContextMenu.addAction(self.deleteAction)
        self.centralW.scene.itemContextMenu.addAction(self.objPropAction)

    def _createShortcuts(self):
        super()._createShortcuts()
        self.createInstAction.setShortcut(Qt.Key_I)
        self.createWireAction.setShortcut(Qt.Key_W)

    def createWireClick(self, s):
        self.centralW.scene.drawWire = True

    def deleteClick(self, s):
        self.centralW.scene.deleteSelectedItem()

    def createInstClick(self, s):
        revEDAPathObj = pathlib.Path(__file__)
        revEDADirObj = revEDAPathObj.parent
        if self.symbolChooser is None:
            self.symbolChooser = libw.symbolChooser(
                self.libraryDict, self.cellViews, self.centralW.scene
            )  # create the library browser
            self.symbolChooser.show()
        else:
            self.symbolChooser.show()

    def objPropClick(self, s):
        self.centralW.scene.viewObjProperties()

    def copyClick(self, s):
        pass

    def checkSaveCell(self):
        self.centralW.scene.saveSchematicCell(self.file)

    def loadSchematic(self):
        self.centralW.scene.loadSchematicCell(self.file)

    def closeEvent(self, event):
        self.centralW.scene.saveSchematicCell(self.file)
        self.libraryView.openViews.pop(
            f"{self.file.parent.parent.stem}_{self.file.parent.stem}_schematic"
        )
        event.accept()


class symbolEditor(editorWindow):
    def __init__(self, file: pathlib.Path, libraryDict: dict, libraryView):
        super().__init__(
            file=file, libraryDict=libraryDict, libraryView=libraryView
        )
        # self.file = file
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
        self.centralW.scene.itemContextMenu.addAction(self.copyAction)
        self.centralW.scene.itemContextMenu.addAction(self.moveAction)
        self.centralW.scene.itemContextMenu.addAction(self.stretchAction)
        self.centralW.scene.itemContextMenu.addAction(self.deleteAction)
        self.centralW.scene.itemContextMenu.addAction(self.objPropAction)

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
        self.libraryView.openViews.pop(
            f"{self.file.parent.parent.stem}_{self.file.parent.stem}_symbol"
        )
        event.accept()


class displayConfigDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Display Options")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.vLayout = QVBoxLayout()
        fLayout = QFormLayout()
        self.majorGridEntry = QLineEdit()
        fLayout.addRow("Major Grid:", self.majorGridEntry)
        if self.parent.centralW.scene.gridMajor:
            self.majorGridEntry.setText(
                str(self.parent.centralW.scene.gridMajor)
            )
        else:
            self.majorGridEntry.setText("10")
        self.vLayout.addLayout(fLayout)
        self.vLayout.addStretch(1)
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
        self.gridMajor = 10
        self.gridTuple = (self.gridMajor, self.gridMajor)
        self.selectedItem = None  # selected item
        self.defineSceneLayers()
        self.setPens()
        self.undoStack = QUndoStack()
        self.changeOrigin = False
        self.origin = QPoint(0, 0)
        self.cellName = self.parent.parent.file.parent.stem
        self.libraryDict = self.parent.parent.libraryDict

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
            name="wireLayer", color=QColor("cyan"), z=1, visible=True
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
        return base * int(round(number / base))

    def snap2Grid(self, point: QPoint, gridTuple: tuple[int, int]):
        """
        snap point to grid. Divides and multiplies by grid size.
        """
        return QPoint(
            gridTuple[0] * int(round(point.x() / gridTuple[0])),
            gridTuple[1] * int(round(point.y() / gridTuple[1])),
        )


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
        self.itemContextMenu = QMenu()
        self.draftPen = QPen(self.guideLineLayer.color, 1)

    def mousePressEvent(self, mouse_event):

        if mouse_event.button() == Qt.LeftButton:
            self.start = self.snap2Grid(mouse_event.scenePos(), self.gridTuple)
            if self.changeOrigin:  # change origin of the symbol
                self.origin = self.start
                self.changeOrigin = False
            elif self.selectItem and self.items(
                    self.start
            ):  # item select mode True
                self.itemsAtMousePress = self.items(self.start)
                self.selectedItem = self.itemsAtMousePress[0]
                self.selectedItem.setSelected(True)
            elif self.drawPin:
                if hasattr(self, "draftPin"):
                    self.removeItem(self.draftPin)
                self.draftPin = shp.pin(
                    self.start,
                    self.draftPen,
                    self.pinName,
                    self.pinDir,
                    self.pinType,
                    self.gridTuple,
                )
                self.addItem(self.draftPin)
            elif self.addLabel:
                if hasattr(self, "draftLabel"):
                    self.removeItem(self.draftLabel)
                self.draftLabel = shp.label(
                    self.start,
                    self.draftPen,
                    self.labelDefinition,
                    self.gridTuple,
                    self.labelType,
                    self.labelHeight,
                    self.labelAlignment,
                    self.labelOrient,
                    self.labelUse,
                )

                self.addItem(self.draftLabel)
        super().mousePressEvent(mouse_event)

    def mouseMoveEvent(self, mouse_event):
        self.current = self.snap2Grid(mouse_event.scenePos(), self.gridTuple)
        if mouse_event.buttons() == Qt.LeftButton:
            if hasattr(self, "draftItem"):
                self.removeItem(self.draftItem)
            if self.drawLine and hasattr(self, "start"):
                self.draftItem = shp.line(
                    self.start, self.current, self.draftPen, self.gridTuple
                )
                self.addItem(self.draftItem)
            elif self.drawRect and hasattr(self, "start"):
                self.draftItem = shp.rectangle(
                    self.start, self.current, self.draftPen, self.gridTuple
                )
                self.addItem(self.draftItem)
            elif self.drawPin and hasattr(
                    self, "draftPin"
            ):  # there is a pin draft
                self.draftPin.setSelected(True)
            elif self.addLabel and hasattr(self, "draftLabel"):
                self.draftLabel.setSelected(True)
        self.parent.parent.statusLine.showMessage(
            "Cursor Position: " + str((self.current - self.origin).toTuple())
        )

        super().mouseMoveEvent(mouse_event)

    def mouseReleaseEvent(self, mouse_event):
        print('scene event')
        self.current = self.snap2Grid(mouse_event.scenePos(), self.gridTuple)
        if mouse_event.button() == Qt.LeftButton:
            if self.drawLine and hasattr(self, "start"):
                self.lineDraw(
                    self.start, self.current, self.symbolPen, self.gridTuple
                )
            elif self.drawRect and hasattr(self, "start"):
                self.rectDraw(
                    self.start, self.current, self.symbolPen, self.gridTuple
                )
            elif self.drawPin and hasattr(self, "draftPin"):
                self.pinDraw(
                    self.current,
                    self.pinPen,
                    self.pinName,
                    self.pinDir,
                    self.pinType,
                    self.gridTuple,
                )  # draw pin
            elif self.addLabel and hasattr(self, "draftLabel"):
                self.labelDraw(
                    self.current,
                    self.labelPen,
                    self.labelDefinition,
                    self.gridTuple,
                    self.labelType,
                    self.labelHeight,
                    self.labelAlignment,
                    self.labelOrient,
                    self.labelUse,
                )  # draw label
            if hasattr(self, "draftItem"):
                self.removeItem(self.draftItem)
                del self.draftItem
            elif hasattr(self, "draftPin"):
                self.removeItem(self.draftPin)
                del self.draftPin
            elif hasattr(self, "draftLabel"):
                self.removeItem(self.draftLabel)
                del self.draftLabel

        super().mouseReleaseEvent(mouse_event)

    def lineDraw(self, start: QPoint, current: QPoint, pen: QPen,
                 gridTuple: tuple
                 ):
        line = shp.line(
            start, current, pen,
            gridTuple
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
            start, end - QPoint(pen.width() / 2, pen.width() / 2), pen,
            gridTuple
        )
        self.addItem(rect)
        undoCommand = us.addShapeUndo(self, rect)
        self.undoStack.push(undoCommand)
        self.drawRect = False

    def pinDraw(
            self, current, pen: QPen, pinName: str, pinDir, pinType,
            gridTuple: tuple
    ):
        pin = shp.pin(current, pen, pinName, pinDir, pinType, gridTuple)
        self.addItem(pin)
        undoCommand = us.addShapeUndo(self, pin)
        self.undoStack.push(undoCommand)
        self.drawPin = False

    def labelDraw(
            self,
            current,
            pen: QPen,
            labelDefinition,
            gridTuple,
            labelType,
            labelHeight,
            labelAlignment,
            labelOrient,
            labelUse,
    ):
        label = shp.label(
            current,
            pen,
            labelDefinition,
            gridTuple,
            labelType,
            labelHeight,
            labelAlignment,
            labelOrient,
            labelUse,
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
            selectedItemJson = json.dumps(
                self.selectedItem, cls=se.symbolEncoder
            )
            itemCopyDict = json.loads(selectedItemJson)
            shape = lj.createSymbolItems(itemCopyDict, self.gridTuple)
            self.addItem(shape)
            # shift position by one grid unit to right and down
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
        us.changeOriginalShape(
            self, self.selectedItem, parent=undoUpdateRectangle
        )
        self.undoStack.push(undoUpdateRectangle)
        self.selectedItem.update()

    def updateLineShape(self):
        location = self.selectedItem.scenePos().toTuple()
        self.selectedItem.start = self.snap2Grid(
            QPoint(
                int(
                    float(self.queryDlg.startXLine.text()) - float(location[0])
                ),
                int(
                    float(self.queryDlg.startYLine.text()) - float(location[1])
                ),
            ),
            self.gridTuple,
        )
        self.selectedItem.end = self.snap2Grid(
            QPoint(
                int(float(self.queryDlg.endXLine.text()) - float(location[0])),
                int(float(self.queryDlg.endYLine.text()) - float(location[1])),
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
            self.selectedItem.start.x() - 5, self.selectedItem.start.y() - 5,
            10, 10
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
        self.selectedItem.labelDefinition = self.queryDlg.labelDefinition.text()
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
        with open(file, "r") as temp:
            try:
                items = json.load(temp)
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
        if self.selectedItems is not None:
            self.selectedItem.stretch = True

    def viewSymbolProperties(self):
        """
        View symbol properties dialog.
        """
        # copy symbol attribute list to another list by deepcopy to be safe
        attributeListCopy = copy.deepcopy(self.attributeList)
        symbolPropDialogue = pdlg.symbolLabelsDialogue(
            self.parent.parent, self.items(), attributeListCopy
        )
        if symbolPropDialogue.exec() == QDialog.Accepted:
            for i, item in enumerate(symbolPropDialogue.labelItemList):
                # label name is not changed.
                item.labelHeight = symbolPropDialogue.labelHeightList[i].text()
                item.labelAlign = symbolPropDialogue.labelAlignmentList[
                    i].currentText()
                item.labelOrient = symbolPropDialogue.labelOrientationList[
                    i
                ].currentText()
                item.labelUse = symbolPropDialogue.labelUseList[i].currentText()
                item.labelType = symbolPropDialogue.labelTypeList[
                    i].currentText()
                item.update(item.boundingRect())
            # create an empty attribute list. If the dialog is OK, the local attribute list
            # will be copied to the symbol attribute list.
            localAttributeList = []
            for i, item in enumerate(symbolPropDialogue.attributeNameList):
                if item.text().strip() != "":
                    localAttributeList.append(
                        se.symbolAttribute(
                            item.text(),
                            symbolPropDialogue.attributeTypeList[
                                i].currentText(),
                            symbolPropDialogue.attributeDefList[i].text(),
                        )
                    )
                self.attributeList = copy.deepcopy(localAttributeList)


class schematic_scene(editor_scene):
    def __init__(self, parent):
        super().__init__(parent)
        self.instCounter = 0
        self.current = QPoint(0, 0)
        self.itemsAtMousePress = []
        self.itemContextMenu = QMenu()
        self.drawWire = False  # flag to add wire
        self.itemSelect = True  # flag to select item
        self.draftPen = QPen(self.guideLineLayer.color, 1)
        self.draftPen.setStyle(Qt.DashLine)
        self.itemCounter = 0
        self.netCounter = 0
        self.pinLocations = self.pinLocs()  # dictionary to store pin locations
        self.schematicNets = {}  # netName: list of nets with the same name
        self.draftItem = None

    def symbolItems(self):
        '''
        Return a list of all symbol items in the view
        '''
        return {item.instanceName: item for item in self.items() if
                isinstance(item, shp.symbolShape)}

    def pinLocs(self):
        symbolsDict = self.symbolItems()
        return {item.instanceName: item.pinLocations for item in
                symbolsDict.values()}

    def viewportItemPinLocs(self):
        # create a dictionary of items and their pin locations that are visible
        return {item.instanceName: item.pinLocations for item in
                self.parent.view.viewItems}

    def mousePressEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        if mouse_event.button() == Qt.LeftButton:
            self.start = self.snap2Grid(mouse_event.scenePos(), self.gridTuple)
            if self.itemSelect:
                self.itemsAtMousePress = self.items(self.start)
                if len(self.itemsAtMousePress) == 0:
                    self.parent.parent.messageLine.setText("No item selected")
                elif len(self.itemsAtMousePress) != 0:
                    self.parent.parent.messageLine.setText("Item selected")
                    if self.itemsAtMousePress[0].parentItem() is not None:
                        self.selectedItem = self.itemsAtMousePress[0].parentItem()
                    else:
                        self.selectedItem = self.itemsAtMousePress[0]
                    try:
                        self.selectedItem.setSelected(True)
                    except AttributeError:
                        pass

        super().mousePressEvent(mouse_event)

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:

        self.current = self.snap2Grid(mouse_event.scenePos(), self.gridTuple)
        if mouse_event.buttons() == Qt.LeftButton:
            if hasattr(self, "draftItem"):
                self.removeItem(self.draftItem)
            if self.drawWire and hasattr(self, "start"):
                self.parent.parent.messageLine.setText("Wire Mode")
                self.draftItem = net.schematicNet(
                    self.start, self.current, self.draftPen, ''
                )
                self.addItem(self.draftItem)
        self.parent.parent.statusLine.showMessage(
            "Cursor Position: " + str(self.current.toTuple())
        )
        super().mouseMoveEvent(mouse_event)

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        self.current = self.snap2Grid(mouse_event.scenePos(), self.gridTuple)
        if mouse_event.button() == Qt.LeftButton:
            if self.drawWire and hasattr(self, "start"):
                if hasattr(self, "draftItem"):
                    self.removeItem(self.draftItem)
                    del self.draftItem
                    drawnNet = self.netDraw(
                        self.start, self.current, self.wirePen,
                        f'net{self.netCounter}'
                    )
                    netMergedFlag = False
                    netAddedFlag = False
                    del self.start
                    del self.current
                    dnetBRect = drawnNet.boundingRect()
                    # check if it intersects another net and merge them.
                    for name, netItemList in self.schematicNets.items():
                        for netItem in netItemList:
                            if dnetBRect.intersects(netItem.boundingRect()):
                                if drawnNet.horizontal and netItem.horizontal:
                                    netMergedFlag = self.mergeHorizontalNets(dnetBRect, drawnNet, netItem)
                                elif not (drawnNet.horizontal or netItem.horizontal):
                                    netMergedFlag = self.mergeVerticalNets(dnetBRect, drawnNet, netItem)
                                elif drawnNet.horizontal and not netItem.horizontal:
                                    # print('cross net')
                                    crossRect = dnetBRect.intersected(netItem.boundingRect()).normalized().marginsAdded(
                                        QMargins(2, 2, 2, 2))
                                    crossRectCenter = crossRect.center()
                                    # check if drawn net is starts or ends in the existing net.

                                    if not (drawnNet.start.x() < crossRectCenter.x() < drawnNet.end.x()):
                                        if ((netItem.start.y() != crossRectCenter.y()) and (
                                                netItem.end.y() != crossRectCenter.y())):
                                            self.createCrossDot(crossRect, drawnNet)
                                        drawnNet.name = netItem.name  # get the net name from the connected net
                                        netAddedFlag = True
                                elif not drawnNet.horizontal and netItem.horizontal:
                                    crossRect = dnetBRect.intersected(netItem.boundingRect()).normalized().marginsAdded(
                                        QMargins(2, 2, 2, 2))
                                    crossRectCenter = crossRect.center()
                                    # check if drawn net is starts or ends in the existing net.

                                    if not (drawnNet.start.y() < crossRectCenter.y() < drawnNet.end.y()):
                                        if ((netItem.start.x() != crossRectCenter.x()) and (
                                                netItem.end.x() != crossRectCenter.x())):
                                            self.createCrossDot(crossRect, drawnNet)
                                        drawnNet.name = netItem.name  # get the net name from the connected net
                                        netAddedFlag = True
                    if not (netMergedFlag or netAddedFlag):
                        self.schematicNets[drawnNet.name] = [drawnNet]
                        self.netCounter += 1
                    elif netAddedFlag:  # a new net is added but shares a name with another net.
                        self.schematicNets[drawnNet.name] += [drawnNet]
            # elif hasattr(self, "selectedItem"):
            #     if isinstance(self.selectedItem, shp.symbolShape):
            #         for item in self.selectedItem.childItems():
            #             if type(item) is shp.pin:
            #                 self.selectedItem.pinLocations[
            #                     item.pinName] = (item.start + item.scenePos().toPoint()).toTuple()

                    self.selectedItem = None


        super().mouseReleaseEvent(mouse_event)

    def createCrossDot(self, crossRect, drawnNet):
        crossDot = QGraphicsEllipseItem(
            crossRect)  # create a dot to mark the cross net
        crossDot.setPen(self.wirePen)
        crossDot.setBrush(self.wirePen.color())
        crossDot.setParentItem(drawnNet)  # its parent is the drawn net
        self.addItem(crossDot)

    def mergeHorizontalNets(self, dnetBRect, drawnNet, netItem):
        mergedRect = dnetBRect.united(
            netItem.boundingRect()).toRect()  # create a merged horizontal rectangle
        self.schematicNets[netItem.name].remove(netItem)  # remove the old net from the list
        netItem = self.netDraw(mergedRect.bottomLeft(), mergedRect.bottomRight(),
                               self.wirePen, netItem.name)  # create a new net with the merged rectangle
        self.schematicNets[netItem.name].append(netItem)  # add the new net to the list
        self.removeItem(drawnNet)  # remove the drawn net from the scene
        self.parent.parent.messageLine.setText("Net merged")
        return True

    def mergeVerticalNets(self, dnetBRect, drawnNet, netItem):
        mergedRect = dnetBRect.united(
            netItem.boundingRect()).toRect()  # create a merged horizontal rectangle
        self.schematicNets[netItem.name].remove(netItem)  # remove the old net from the list
        netItem = self.netDraw(mergedRect.bottomRight(), mergedRect.topLeft(),
                               self.wirePen, netItem.name)  # create a new net with the merged rectangle
        self.schematicNets[netItem.name].append(netItem)  # add the new net to the list
        self.removeItem(drawnNet)  # remove the drawn net from the scene
        self.parent.parent.messageLine.setText("Net merged")
        return True

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_Escape:
            self.resetSceneMode()
        super().keyPressEvent(key_event)

    def resetSceneMode(self):
        self.itemSelect = True
        self.drawWire = False
        self.selectedItem = None
        self.parent.parent.messageLine.setText("Select Mode")

    def netDraw(self, start: QPoint, current: QPoint, pen: QPen,
                name: str
                ) -> net.schematicNet:
        line = net.schematicNet(start, current, pen, name)
        self.addItem(line)
        undoCommand = us.addShapeUndo(self, line)
        self.undoStack.push(undoCommand)
        return line

    def instSymbol(self, file: pathlib.Path, cellName: str, libraryName: str):
        '''
        Read a symbol file and create symbolShape objects from it.
        '''
        assert isinstance(file, pathlib.Path)
        assert isinstance(cellName, str)
        assert isinstance(libraryName, str)
        itemShapes = []
        itemAttributes = {}
        draftPen = QPen(self.guideLineLayer.color, 1)
        with open(file, "r") as temp:
            try:
                items = json.load(temp)
                for item in items:
                    if (
                            item["type"] == "rect"
                            or item["type"] == "line"
                            or item["type"] == "pin"
                            or item["type"] == "label"
                    ):
                        # append recreated shapes to shapes list
                        itemShapes.append(
                            lj.createSymbolItems(item, self.gridTuple)
                        )

                    elif item["type"] == "attribute":
                        itemAttributes[item["name"]] = [
                            item["attributeType"],
                            item["definition"],
                        ]

                # create a symbol instance passing item shapes and attributes as
                # arguments
                symbolInstance = shp.symbolShape(
                    draftPen, self.gridTuple, itemShapes, itemAttributes
                )
                self.addItem(symbolInstance)  # add symbol instance to scene
                symbolInstance.setPos(QPoint(0, 0))
                # For each instance assign a counter number from the scene
                symbolInstance.counter = self.itemCounter
                symbolInstance.instanceName = f'I{symbolInstance.counter}'
                symbolInstance.libraryName = libraryName
                symbolInstance.cellName = cellName
                symbolInstance.viewName = "symbol"
                for item in symbolInstance.labels:
                    item.labelDefs()  # assign label name and text
                    symbolInstance.labelDict[
                        item.labelName] = item  # labelName: label object
                # for pin in symbolInstance.pins:
                #     symbolInstance.pinLocations[pin.pinName] = (
                #             pin.start + pin.scenePos().toPoint()
                #     ).toTuple()
                print(symbolInstance.pinLocations)
                undoCommand = us.addShapeUndo(self, symbolInstance)
                self.undoStack.push(undoCommand)
                return symbolInstance
            except json.decoder.JSONDecodeError:
                print("Invalid JSON file")

    def deleteSelectedItem(self):
        if hasattr(self, "selectedItem"):
            self.removeItem(self.selectedItem)
            del self.selectedItem
            self.update()
            self.selectItem = True

    def saveSchematicCell(self, file: pathlib.Path):
        self.sceneR = self.sceneRect()  # get scene rect
        items = self.items(self.sceneR)  # get items in scene rect
        # only save symbol shapes
        symbolItems = [item for item in items if type(item) is shp.symbolShape]
        with open(file, "w") as f:
            json.dump(symbolItems, f, cls=se.schematicEncoder, indent=4)

    def loadSchematicCell(self, file: pathlib.Path):
        with open(file, "r") as temp:
            try:
                items = json.load(temp)
                for item in items:
                    if item is not None and item["type"] == "symbolShape":
                        itemShape = lj.createSchematicItems(
                            item, self.libraryDict, "symbol", self.gridTuple
                        )
                        self.addItem(itemShape)
                        if itemShape.counter > self.itemCounter:
                            self.itemCounter = itemShape.counter

            except json.decoder.JSONDecodeError:
                print("Invalid JSON file")
        # increment item counter for next symbol
        self.itemCounter += 1
        self.pinLocations = self.pinLocs()
        print(self.pinLocations)

    def viewObjProperties(self):
        if hasattr(self, "selectedItem") and self.selectedItem is not None:
            # assert isinstance(self.selectedItem, shp.symbolShape)

            dlg = pdlg.instanceProperties(
                self.parent.parent, self.selectedItem
            )
            if dlg.exec() == QDialog.Accepted:
                libraryName = dlg.libName.text().strip()
                cellName = dlg.cellName.text().strip()
                viewName = "symbol"  # prepare for the time there could be other view names
                filePath = pathlib.Path(
                    self.libraryDict[libraryName].joinpath(
                        cellName, viewName + ".json"
                    )
                )
                self.removeItem(self.selectedItem)
                del self.selectedItem
                self.selectedItem = self.instSymbol(
                    filePath, cellName, libraryName
                )
                self.selectedItem.setSelected(True)
                self.selectedItem.setPos(
                    int(float(dlg.xLocation.text())),
                    int(float(dlg.yLocation.text()))
                )
                self.addItem(self.selectedItem)
                self.selectedItem.instanceName = dlg.instName.text().strip()
                for label in self.selectedItem.labels:
                    if label.labelDefinition == '[@instName]':
                        label.setText(self.selectedItem.instanceName)
                    elif label.labelDefinition == '[@cellName]':
                        label.setText(self.selectedItem.cellName)
                tempDoc = QTextDocument()
                for i in range(dlg.instanceLabelsLayout.rowCount()):
                    tempDoc.setHtml(
                        dlg.instanceLabelsLayout.itemAtPosition(
                            i, 0
                        ).widget().text()
                    )
                    tempLabelName = tempDoc.toPlainText().strip()
                    if tempLabelName in self.selectedItem.labelDict.keys():
                        self.selectedItem.labelDict[tempLabelName].setText(
                            f'{tempLabelName} = {dlg.instanceLabelsLayout.itemAtPosition(i, 1).widget().text().strip()}'
                        )
                self.selectedItem.update()


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
        # self.setCacheMode(QGraphicsView.CacheBackground)
        self.standardCursor = QCursor(Qt.CrossCursor)
        self.setCursor(self.standardCursor)  # set cursor to standard arrow
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setMouseTracking(
            True
        )  # self.setDragMode(QGraphicsView.RubberBandDrag)

    def wheelEvent(self, mouse_event):
        factor = 1.1
        if mouse_event.angleDelta().y() < 0:
            factor = 0.9
        view_pos = QPoint(
            int(mouse_event.globalPosition().x()),
            int(mouse_event.globalPosition().y())
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
                    grid_x_start + i * self.gridMajor,
                    grid_y_start + j * self.gridMajor
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
        self.visibleRect = QRect(0, 0, 0, 0)  # initialize to an empty rectangle


class schematic_view(editor_view):
    def __init__(self, scene, parent):
        self.scene = scene
        self.parent = parent
        super().__init__(self.scene, self.parent)
        self.visibleRect = QRect(0, 0, 0, 0)  # initialize to an empty rectangle
        self.viewItems = []

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        if mouse_event.button() == Qt.MouseButton.LeftButton:
            if self.scene.drawWire:
                self.visibleRect = self.viewport().geometry()
                self.viewItems = [item for item in self.items(
                    self.visibleRect, mode=Qt.IntersectsItemShape
                ) if isinstance(item, shp.symbolShape)]
        super().mouseReleaseEvent(mouse_event)
