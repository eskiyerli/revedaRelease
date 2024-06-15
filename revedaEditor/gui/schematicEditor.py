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
import time
from copy import deepcopy
from functools import lru_cache

# import numpy as np
from PySide6.QtCore import (
    Qt,
    QPoint,
)
from PySide6.QtGui import (
    QAction,
    QIcon,
)
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QMenu,
    QToolBar,
    QWidget,
)

# import pdk.symLayers as symlyr
import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.libraryModelView as lmview
import revedaEditor.backend.schBackEnd as scb
import revedaEditor.common.net as net
import revedaEditor.common.shapes as shp  # import the shapes
import revedaEditor.fileio.symbolEncoder as symenc
import revedaEditor.gui.editorScenes as escn
import revedaEditor.gui.editorViews as edv
import revedaEditor.gui.editorWindow as edw
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.propertyDialogues as pdlg
import revedaEditor.resources.resources
from revedaEditor.gui.startThread import startThread


class schematicEditor(edw.editorWindow):
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
            from revedaEditor.gui.symbolEditor import symbolEditor
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

