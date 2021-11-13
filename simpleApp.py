import os
import sys
from pathlib import Path
from threading import Thread

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
)
from PySide6.QtCore import Qt, QPoint, QLine

import resources
import numpy as np
import math
import circuitElements as cel
from Point import *
from Vector import *

import pythonConsole as pcon
from contextlib import redirect_stdout, redirect_stderr

class designLibrariesView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setSelectionMode(QTreeView.ExtendedSelection)
        self.setDragEnabled(True)

# class designLibrariesView(QTreeView):
#     def __init__(self, parent=None, libraryDict={}):
#         super().__init__(parent=parent)
#         self.libraryDict = libraryDict
#         self.init_UI()

#     def init_UI(self):
#         model = QStandardItemModel()
#         model.setHorizontalHeaderLabels(["Libraries"])
#         # iterate design library directories
#         for designPath in self.libraryDict.values():
#             parentItem = model.invisibleRootItem()
#             libraryName = designPath.name
#             # create a standard Item
#             libraryNameItem = QStandardItem(libraryName)
#             libraryNameItem.setEditable(False)
#             parentItem.appendRow(libraryNameItem)
#             cellList = [
#                 str(cell.name) for cell in designPath.iterdir() if cell.is_dir()
#             ]
#             for cell in cellList:
#                 cellItem = QStandardItem(cell)
#                 cellItem.setEditable(False)
#                 libraryNameItem.appendRow(cellItem)
#                 viewList = [
#                     str(view.name)
#                     for view in designPath.joinpath(cell).iterdir()
#                     if view.is_dir()
#                 ]
#                 #                viewList = os.listdir(os.path.join(designPath, cell))
#                 for view in viewList:
#                     viewItem = QStandardItem(view)
#                     viewItem.setEditable(False)
#                     cellItem.appendRow(viewItem)

#         self.setModel(model)


class container(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.init_UI()

    def init_UI(self):

        self.scene = schematic_scene(self)

        self.view = schematic_view(self.scene, self)

        libraryDict = {
            "design": Path.home().joinpath(
                "OneDrive", "Documents", "Projects", "RevEDA", "revedaWork"
            )
        }
        # treeView = designLibrariesView(self, libraryDict)
        treeView = designLibrariesView(self)
        self.console = pcon.pythonConsole(globals())
        self.console.writeoutput("Welcome to RevEDA")
        self.console.setfont(QFont("Fira Mono Regular", 10))
        # layout statements, using a grid layout
        gLayout = QGridLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(treeView, 0, 0)
        gLayout.addWidget(self.view, 0, 1)
        # ratio of first column to second column is 5
        gLayout.setColumnStretch(1, 5)
        gLayout.setRowStretch(0, 6)
        gLayout.addWidget(self.console, 1, 0, 1, 2)
        gLayout.setRowStretch(1, 1)
        self.setLayout(gLayout)


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
        self.parent.centralWidget.scene.gridMajor = int(self.majorGridEntry.text())
        self.parent.centralWidget.view.gridMajor = int(self.majorGridEntry.text())
        self.parent.centralWidget.scene.gridMinor = int(self.minorGridEntry.text())
        self.parent.centralWidget.scene.update()
        self.close()

    def reject(self):
        self.close()


class schematic_scene(QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.gridMajor = 10
        self.drawWire = False
        self.drawItem = False
        self.selectItem = True
        self.wireLayer = cel.layer(
            name="wireLayer", color=QColor("green"), z=1, visible=True
        )
        self.guideLineLayer = cel.layer(
            name="guideLineLayer", color=QColor("white"), z=2, visible=True
        )
        self.selectedWireLayer = cel.layer(
            name="selectedWireLayer", color=QColor("red"), z=3, visible=True
        )
        self.wirePen = QPen(self.wireLayer.color, 2)
        self.selectedWirePen = QPen(self.selectedWireLayer.color, 2)
        self.init_UI()

    def init_UI(self):
        pass

    def mousePressEvent(self, mouse_event):
        self.startPosition = mouse_event.scenePos()
        if hasattr(self, "start") == False:
            self.start = QPoint(
                self.snapGrid(self.startPosition.x(), self.gridMajor),
                self.snapGrid(self.startPosition.y(), self.gridMajor),
            )
        # vectorObj = Vector(0,0,self.start.x(), self.start.y())
        # print(vectorObj)

        if self.selectItem == True:
            self.selectedItem = self.itemAt(
                self.startPosition.x(), self.startPosition.y(), QTransform()
            )
            if self.selectedItem != None:
                self.selectedItem.setSelected(True)
                self.selectedItem.setZValue(1)
                self.selectedItem.setPen(self.selectedWirePen)  # set pen to red
                self.selectedItem.show()
                self.selectedItem.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mousePressEvent(mouse_event)

    def mouseMoveEvent(self, mouse_event):
        self.currentPosition = mouse_event.scenePos()
        self.current = QPoint(
            self.snapGrid(self.currentPosition.x(), self.gridMajor),
            self.snapGrid(self.currentPosition.y(), self.gridMajor),
        )
        if self.drawWire == True and hasattr(self, "start") == True:
            if hasattr(self, "linkLine"):
                self.removeItem(self.linkLine)  # remove old guide line
            pen = QPen(self.guideLineLayer.color, 1)
            pen.setStyle(Qt.DashLine)

            self.linkLine = QGraphicsLineItem(QLine(self.start, self.current))

            self.linkLine.setPen(pen)
            self.addItem(self.linkLine)
        super().mouseMoveEvent(mouse_event)

    def mouseReleaseEvent(self, mouse_event):
        if hasattr(self, "linkLine"):
            self.removeItem(self.linkLine)
        if self.drawWire == True:
            midPoint = QPoint(self.current.x(), self.start.y())
            horizLine = QGraphicsLineItem(QLine(self.start, midPoint))
            horizLine.setPen(self.wirePen)
            self.addItem(horizLine)
            vertLine = QGraphicsLineItem(QLine(midPoint, self.current))
            vertLine.setPen(self.wirePen)
            self.addItem(vertLine)
            self.start = self.current  # reset start position

        super().mouseReleaseEvent(mouse_event)

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_Escape:
            self.drawWire = False  # turn off wire select mode
            self.drawItem = False  # turn off drawing mode when escape is pressed
            if hasattr(self, "linkLine"):
                self.removeItem(self.linkLine)
            self.selectItem = True
        elif key_event.key() == Qt.Key_Delete:
            if hasattr(self, "selectedItem"):
                self.removeItem(self.selectedItem)
                del self.selectedItem
                self.selectItem = True

    def snapGrid(self, number, base):
        return base * int(math.floor(number / base))


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

    # def mouseMoveEvent(self, mouse_event):

    #     super().mouseMoveEvent(mouse_event)

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


class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        revEDAPathObj = Path(__file__)
        revEDADirObj = revEDAPathObj.parent
        self.init_UI()

    def init_UI(self):
        self.resize(1600, 800)
        self._createMenuBar()
        self._createActions()
        self._createToolBars()
        # create container to position all widgets
        self.centralWidget = container(self)
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

        newLibIcon = QIcon(":/icons/database--plus.png")
        self.newLibAction = QAction(newLibIcon, "New Lib...", self)
        self.menuFile.addAction(self.newLibAction)

        openLibIcon = QIcon(":/icons/database--pencil.png")
        self.openLibAction = QAction(openLibIcon, "Open Lib...", self)
        self.openLibAction.setShortcut("Ctrl+O")
        self.openLibAction.triggered.connect(self.openLibDialog)
        self.menuFile.addAction(self.openLibAction)

        saveLibIcon = QIcon(":/icons/database-import.png")
        self.saveLibAction = QAction(saveLibIcon, "Save Lib...", self)
        self.menuFile.addAction(self.saveLibAction)

        closeLibIcon = QIcon(":/icons/database-delete.png")
        self.closeLibAction = QAction(closeLibIcon, "Close Lib...", self)
        self.menuFile.addAction(self.closeLibAction)

        self.menuFile.addSeparator()
        newCellIcon = QIcon(":/icons/document--plus.png")
        self.newCellAction = QAction(newCellIcon, "New Cell...", self)
        self.menuFile.addAction(self.newCellAction)

        openCellIcon = QIcon(":/icons/document--pencil.png")
        self.openCellAction = QAction(openCellIcon, "Open Cell...", self)
        self.menuFile.addAction(self.openCellAction)

        saveCellIcon = QIcon(":/icons/document-import.png")
        self.saveCellAction = QAction(saveCellIcon, "Save Cell", self)
        self.menuFile.addAction(self.saveCellAction)

        closeCellIcon = QIcon(":/icons/document--minus.png")
        closeCellAction = QAction(closeCellIcon, "Close Cell", self)
        self.menuFile.addAction(closeCellAction)

        checkCellIcon = QIcon(":/icons/document-task.png")
        checkCellAction = QAction(checkCellIcon, "Check-Save", self)
        self.menuFile.addAction(checkCellAction)

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
        self.createWireAction.triggered.connect(self.createWireClick)

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
        # Main toolbar

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
        toolbar.addSeparator()
        toolbar.addAction(self.printAction)
        toolbar.addSeparator()
        toolbar.addAction(self.undoAction)
        toolbar.addAction(self.redoAction)
        toolbar.addSeparator()
        toolbar.addAction(self.deleteAction)
        toolbar.addAction(self.moveAction)
        toolbar.addAction(self.copyAction)
        toolbar.addAction(self.stretchAction)
        # toolbar.addAction(self.rulerAction)
        # toolbar.addAction(self.delRulerAction)
        toolbar.addAction(self.objPropAction)
        toolbar.addAction(self.viewPropAction)
        toolbar.addSeparator()
        toolbar.addAction(self.createInstAction)
        toolbar.addAction(self.createWireAction)
        toolbar.addAction(self.createBusAction)
        toolbar.addAction(self.createPinAction)
        toolbar.addAction(self.createLabelAction)
        toolbar.addAction(self.createSymbolAction)
        toolbar.addSeparator()
        toolbar.addAction(self.viewCheckAction)

    def openLibDialog(self):
        home_dir = str(Path.home())
        fname = QFileDialog.getOpenFileName(self, "Open file", home_dir)

    # self is the parent window, ie. the application
    def dispConfDialog(self):
        dcd = displayConfigDialog(self)

    def createWireClick(self, s):
        self.centralWidget.scene.drawWire = True
        self.centralWidget.scene.selectItem = False
        if hasattr(self.centralWidget.scene, "start"):
            del self.centralWidget.scene.start

    def deleteItemMethod(self, s):
        self.centralWidget.scene.deleteItem = True


app = QApplication(sys.argv)
# app.setStyle('Fusion')
# empty argument as there is no parent window.
mainW = mainWindow()
redirect = pcon.Redirect(mainW.centralWidget.console.errorwrite)
with redirect_stdout(mainW.centralWidget.console), redirect_stderr(redirect):

    mainW.show()
    sys.exit(app.exec())
mainW.show()
app.exec()
