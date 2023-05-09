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
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
#
#  properties dialogues for various symbol items
from pathlib import Path
from PySide6.QtCore import (Qt,)
from PySide6.QtGui import (QIcon, QAction)
from PySide6.QtWidgets import (QMainWindow, QLabel, QGroupBox, QVBoxLayout,
                               QWidget, QGridLayout, QToolBar)

import revedasim.fileOps as fops
import revedasim.analysisPanel as ap
import revedasim.variablesPanel as vp
import revedasim.outputsPanel as op
class simMainWindow(QMainWindow):
    def __init__(self, app, editorWindow):
        self._app = app
        self._editorWindow = editorWindow
        super().__init__()
        self.setWindowTitle("Revolution EDA Simulation Dashboard")
        self.setMinimumSize(800, 600)
        # self.setWindowIcon(QIcon("icons/logo.png"))
        self._createActions()
        self._createMenuBar()
        self._createToolBars()
        self._createTriggers()
        self._initializeValues()
        self.logger = self._editorWindow.logger
        self.statusLine = self.statusBar()
        self.messageLine = QLabel()  # message line
        self.statusLine.addPermanentWidget(self.messageLine)
        self.statusLine.showMessage("Ready")
        self.mainContainer = simContainer(self)
        self.setCentralWidget(self.mainContainer)

    def _initializeValues(self):
        self.libraryDict = self._editorWindow.libraryDict
        self.libraryView = self._editorWindow.libraryView
        self.libraryItem = self._editorWindow.libItem
        self.libraryName = self.libraryItem.libraryName
        self.cellItem = self._editorWindow.cellItem
        self.cellName = self.cellItem.cellName
        self.viewItem = self._editorWindow.viewItem
        self.viewName = self.viewItem.viewName

        self.selectedDesign = {
            "libName": self.libraryName,
            "cellName": self.viewName,
            "viewName": self.viewName,
        }
        self.modelLib = []
        self.modelSec = []
        self.libraryPath = self.libraryItem.data(Qt.UserRole+2)
        simulationPathPrefix = self.libraryPath.parent
        self.simulatorSetupDict = {
            "simulatorName": "Xyce",
            "simPathPrefix": simulationPathPrefix,
            "simPath": simulationPathPrefix.joinpath(self.libraryName,self.cellName),
            "textEditorPath": ".",
            "simulatorPath": ".",
            "includeFilePath": ".",
        }
        self.simDeckRootObj = self.simulatorSetupDict["simPath"].joinpath(
            f'{self.cellName}_{self.viewName}')
        self.netlistNameObj = self.simDeckRootObj.with_suffix(".cir")
        self.simulatorPathObj = Path(self.simulatorSetupDict["simulatorPath"])
        self.variableCount = 0
        self.variablesDict = {'temp': '27'}
        self.expressionDict = dict()
        self.outputsDict = dict()  # list of dictionaries to hold outputs
        self.analysisChoices = ["TRAN", "AC", "NOISE", "DC", "HB"]
        self.analysesDict = {  # 'selectedAnal': 'TRAN',
            "tran": {
                "tInitStep": "1u",
                "tstop": "1m",
                "tstart": "0",
                "tMaxStep": "",
                "tSchedule": "",
                "uiuc": 0,
            },
            "ac": {
                "linlog": 2,
                "fstart": "1k",
                "fstop": "100k",
                "fstep": "100",
            },
            "noise": {
                "outnode": "",
                "refnode": "0",
                "inputSource": "",
                "sourceResistance": "",
                "linlog": 0,
                "fstart": "1k",
                "fstop": "1Meg",
                "fstep": "100 ",
            },
            "dc": {
                "sweepType": 0,  # 0: selected source, 1: variable
                "inputSource": "",  # name of input source or variable
                "linlog": 0,
                "start": "0",
                "stop": "1",
                "step": "10",
            },
            "hb": {
                "frequency": ["1e9"],
                "numfreq": ["10"],
                "intmodmax": "3",
                "tahb": False,
                "startupperiods": "2",
                "numpts": "101",
                "voltlim": True,
                "saveicdata": False,
            },
        }
        self.selectedAnalyses = list()
        # self.tempAnalysisDict = {}
        self.saveOptionsDict = {"saveNodes": 1, "saveCurrents": 1, "saveExpressions": 1}
        self.simTextDict = {0: "TRAN", 1: "AC", 2: "NOISE", 3: "DC", 4: "HB"}
        self.tranOptions = {
            "method": 7,
            "newlte": 2,
            "abstol": "1e-12",
            "reltol": "1e-3",
        }
        self.temperOptions = {"temp": "25", "tnom": "25"}
        self.deviceOptions = {"gmin": "1e-12", "voltlim": 1, "lambertw": 0}
        self.parserOptions = {"model_binning": 1}
        self.simOptions = {
            "tranOptions": self.tranOptions,
            "temperOptions": self.temperOptions,
            "deviceOptions": self.deviceOptions,
            "parserOptions": self.parserOptions,
        }
        #        self.selectedNetNames = {}
        self.initCondDict = dict()
        self.nodeSetDict = dict()
        self.vaFileSet = set()
        self.vaModelSet = set()
        self.instNamePrefix = ""
        self.tranLabels = list()

    def _createMenuBar(self):
        self._editorMenuBar = self.menuBar()
        self._editorMenuBar.setNativeMenuBar(False)
        # Returns QMenu object.
        self.menuSession = self._editorMenuBar.addMenu("&Session")
        self.menuSetup = self._editorMenuBar.addMenu("S&etup")
        self.menuAnalyses = self._editorMenuBar.addMenu("&Analysis")
        self.menuVariables = self._editorMenuBar.addMenu("&Variables")
        self.menuOutputs = self._editorMenuBar.addMenu("&Outputs")
        self.menuSimulation = self._editorMenuBar.addMenu("S&imulation")
        self.menuResults = self._editorMenuBar.addMenu("&Results")
        self.menuTools = self._editorMenuBar.addMenu("&Tools")
        self.menuHelp = self._editorMenuBar.addMenu("&Help")


        # add actions to menus
        # self.menuSession.addAction(self.selectSchematicAction)
        self.menuSession.addAction(self.saveStateAction)
        self.menuSession.addAction(self.loadStateAction)
        self.menuSetup.addAction(self.openDesignAction)
        self.menuSetup.addAction(self.simSetupAction)
        self.menuSetup.addSeparator()
        self.menuSetup.addAction(self.modelLibAction)
        self.menuAnalyses.addAction(self.analysesAction)
        self.menuAnalyses.addAction(self.simOptionsAction)
        self.menuVariables.addAction(self.varEditAction)
        self.menuOutputs.addAction(self.saveOptionsAction)
        self.menuOutputs.addAction(self.selectOutputAction)
        self.menuOutputs.addSeparator()
        self.menuOutputs.addAction(self.expressionEditAction)
        self.menuSimulation.addAction(self.netlRunAction)
        self.menuSimulation.addAction(self.runAction)
        self.menuSimulation.addAction(self.stopAction)
        self.menuSimOptions = self.menuSimulation.addMenu("Options")
        self.menuSimOptions.addAction(self.analogOptionsAction)
        self.menuNetlist = self.menuSimulation.addMenu("Netl&ist")
        self.menuNetlist.addAction(self.createNetlistAction)
        self.menuNetlist.addAction(self.displayNetlistAction)
        self.menuSimulation.addAction(self.outputLogAction)



    def _createActions(self):
        # selectSchematicIcon = QIcon(":/icons/blue-document-attribute-s.png")
        # self.selectSchematicAction = QAction(selectSchematicIcon, "Select "
        #                                                      "Schematic", self)
        saveStateIcon = QIcon(":icons/blue-document-import.png")
        self.saveStateAction = QAction(saveStateIcon, 'Save State...', self)
        loadStateIcon = QIcon(":icons/blue-document-export.png")
        self.loadStateAction = QAction(loadStateIcon, "Load State...", self)
        openDesignIcon = QIcon(":/icons/blue-document-node.png")
        self.openDesignAction = QAction(openDesignIcon, "&Design...", self)
        simSetupIcon = QIcon(":/icons/screwdriver.png")
        self.simSetupAction = QAction(simSetupIcon, "Simulator/Directory...",
                                      self)
        modelLibIcon = QIcon(":/icons/books-stack.png")
        self.modelLibAction = QAction(modelLibIcon, "Model libraries...", self)
        analysesIcon = QIcon(":/icons/calculator-scientific.png")
        self.analysesAction = QAction(analysesIcon, "Analyses...", self)
        simOptionsIcon = QIcon(":/icons/gear--pencil.png")
        self.simOptionsAction = QAction(simOptionsIcon, "Analyses Options...")
        varEditIcon = QIcon(":/icons/table.png")
        self.varEditAction = QAction(varEditIcon, "Set Variables...")
        saveOptionsIcon = QIcon(":/icons/node-select.png")
        self.saveOptionsAction = QAction(saveOptionsIcon, 'Save Options...')
        selectOutputIcon = QIcon(":/icons/toggle-expand.png")
        self.selectOutputAction = QAction(selectOutputIcon, "Select On "
                                                            "Schematic", self)
        expressionEditIcon = QIcon(":/icons/regular-expression.png")
        self.expressionEditAction = QAction(expressionEditIcon, "Expression "
                                                                "Editor...", self)
        netlRunIcon = QIcon(":/icons/control-double.png")
        self.netlRunAction = QAction(netlRunIcon, "Netlist and Run", self)
        runIcon = QIcon(":/icons/control.png")
        self.runAction = QAction(runIcon, "Run",self)
        stopIcon = QIcon(":/icons/control-stop-square.png")
        self.stopAction = QAction(stopIcon, "Stop",self)
        analogOptionsIcon = QIcon(":/icons/ui-check-boxes-list.png")
        self.analogOptionsAction = QAction(analogOptionsIcon, "Analog...",self)
        self.analogOptionsAction.setToolTip('Analog Options')
        createNetlistIcon = QIcon(":/icons/scripts-text.png")
        self.createNetlistAction = QAction(createNetlistIcon, "Create" )
        displayNetlistIcon = QIcon(":/icons/script-text.png")
        self.displayNetlistAction = QAction(displayNetlistIcon, "Display" )
        outputLogIcon = QIcon(":/icons/clipboard-text.png")
        self.outputLogAction = QAction(outputLogIcon, "Show Simulation Log...",
                                       self)

    def _createToolBars(self):
        # Create tools bar called "main toolbar"
        self.toolbar = QToolBar("Main Toolbar", self)
        # place toolbar at top
        self.addToolBar(self.toolbar)
        self.toolbar.addAction(self.openDesignAction)
        self.toolbar.addAction(self.simSetupAction)
        self.toolbar.addAction(self.modelLibAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.analysesAction)
        self.toolbar.addAction(self.simOptionsAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.varEditAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.saveOptionsAction)
        self.toolbar.addAction(self.selectOutputAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.netlRunAction)
        self.toolbar.addAction(self.runAction)
        self.toolbar.addAction(self.stopAction)
        self.toolbar.addAction(self.analogOptionsAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.createNetlistAction)
        self.toolbar.addAction(self.displayNetlistAction)

    def _createTriggers(self):
        # self.selectSchematicAction.triggered.connect(self.selectSchematicEvent)
        self.saveStateAction.triggered.connect(self.saveStateEvent)
        self.loadStateAction.triggered.connect(self.loadStateEvent)
        self.openDesignAction.triggered.connect(self.openDesignEvent)
        self.simSetupAction.triggered.connect(self.simSetupEvent)
        self.modelLibAction.triggered.connect(self.modelLibEvent)
        self.analysesAction.triggered.connect(self.analysesEvent)
        self.simOptionsAction.triggered.connect(self.simOptionsEvent)
        self.varEditAction.triggered.connect(self.varEditEvent)
        self.saveOptionsAction.triggered.connect(self.saveOptionsEvent)
        self.selectOutputAction.triggered.connect(self.selectOutputEvent)
        self.expressionEditAction.triggered.connect(self.expressionEditEvent)
        self.netlRunAction.triggered.connect(self.netlRunEvent)
        self.runAction.triggered.connect(self.runEvent)
        self.stopAction.triggered.connect(self.stopEvent)
        self.analogOptionsAction.triggered.connect(self.analogOptionsEvent)
        self.createNetlistAction.triggered.connect(self.createNetlistEvent)
        self.displayNetlistAction.triggered.connect(self.displayNetlistEvent)
        self.outputLogAction.triggered.connect(self.outputLogEvent)


    def saveStateEvent(self):
        pass

    def loadStateEvent(self):
        pass

    def openDesignEvent(self):
        pass

    def simSetupEvent(self):
        pass

    def modelLibEvent(self):
        pass

    def analysesEvent(self):
        pass

    def simOptionsEvent(self):
        pass

    def varEditEvent(self):
        pass

    def saveOptionsEvent(self):
        pass

    def selectOutputEvent(self):
        pass

    def expressionEditEvent(self):
        pass

    def netlRunEvent(self):
        pass

    def runEvent(self):
        pass

    def stopEvent(self):
        pass

    def analogOptionsEvent(self):
        pass

    def createNetlistEvent(self):
        pass

    def displayNetlistEvent(self):
        pass

    def outputLogEvent(self):
        pass


class simContainer(QWidget):
    def __init__(self, parent):
        super(simContainer, self).__init__(parent)
        self.parent = parent
        self.mainLayout = QGridLayout(self)
        self.mainLayout.setSpacing(20)
        self.setLayout(self.mainLayout)
        self.outputsGroup = QGroupBox("Outputs")
        self.analysesGroup = QGroupBox("Analyses")
        self.variablesGroup = QGroupBox("Simulation Variables")
        self.mainLayout.addWidget(self.outputsGroup, 0, 0, 2,1)
        self.mainLayout.addWidget(self.analysesGroup, 0, 1)
        self.mainLayout.addWidget(self.variablesGroup, 1, 1)
        self.outputsLayout = QVBoxLayout()
        self.analysesLayout = QVBoxLayout()
        self.variablesLayout = QVBoxLayout()
        self.outputsGroup.setLayout(self.outputsLayout)
        self.analysesGroup.setLayout(self.analysesLayout)
        self.variablesGroup.setLayout(self.variablesLayout)
        self.outputsLayout.setSpacing(20)
        self.analysesLayout.setSpacing(20)
        self.variablesLayout.setSpacing(20)
        self.analysesModel = ap.analysesModel(self.parent.analysesDict)
        self.analysesView = ap.analysisTableView(self.parent, self.analysesModel)
        self.analysesLayout.addWidget(self.analysesView)
        self.variablesModel = vp.variablesModel(self.parent.variablesDict)
        self.variablesView = vp.variablesTableView(self.parent, self.variablesModel)
        self.variablesLayout.addWidget(self.variablesView)
        self.outputsModel = op.outputsModel(self.parent.outputsDict,
                                            self.parent.expressionDict)
        self.outputsView = op.outputsTableView(self.parent, self.outputsModel)
        self.outputsLayout.addWidget(self.outputsView)