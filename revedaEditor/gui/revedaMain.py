#
#    “Commons Clause” License Condition v1.0
#   #
#    The Software is provided to you by the Licensor under the License, as defined
#    below, subject to the following condition.
#   #
#    Without limiting other conditions in the License, the grant of rights under the
#    License will not include, and the License does not grant to you, the right to
#    Sell the Software.
#   #
#    For purposes of the foregoing, “Sell” means practicing any or all of the rights
#    granted to you under the License to provide to third parties, for a fee or other
#    consideration (including without limitation fees for hosting or consulting/
#    support services related to the Software), a product or service whose value
#    derives, entirely or substantially, from the functionality of the Software. Any
#    license notice or attribution required by the License must also include this
#    Commons Clause License Condition notice.
#   #
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)


import json
import logging
import logging.config
import pathlib

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWidgets import (QApplication, QDialog, QMainWindow, QVBoxLayout,
                               QWidget, QMessageBox)
from ruamel.yaml import YAML

import revedaEditor.backend.hdlBackEnd as hdl
import revedaEditor.backend.importViews as imv
import revedaEditor.gui.editorWindows as edw
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.pythonConsole as pcon
import revedaEditor.resources.resources
import revedaEditor.revinit as revinit
import revinit


class mainwContainer(QWidget):
    """
    Definition for the main app window layout.
    """

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.console = pcon.pythonConsole(globals())
        self.init_UI()

    def init_UI(self):
        # treeView = designLibrariesView(self)
        self.console.setfont(QFont("Fira Mono Regular", 12))
        self.console.writeoutput(
            f"Welcome to Revolution EDA version" f" {revinit.__version__}"
        )
        self.console.writeoutput("Revolution Semiconductor (C) 2023.")
        # layout statements, using a grid layout
        gLayout = QVBoxLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.console)
        self.setLayout(gLayout)

#
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(900, 300)
        self._createActions()
        self._createMenuBar()
        self._createTriggers()
        self.cellViews = [
            "schematic",
            "symbol",
            "layout",
            "veriloga",
            "config",
            "spice",
        ]
        self.switchViewList = ["schematic", "veriloga", "spice", "symbol"]
        self.stopViewList = ["symbol"]
        self.simulationPath = pathlib.Path.cwd().parent
        self.openViews = dict()
        # create container to position all widgets
        self.centralW = mainwContainer(self)
        self.setCentralWidget(self.centralW)
        self.mainW_statusbar = self.statusBar()
        self.mainW_statusbar.showMessage("Ready")
        self.app = QApplication.instance()
        # logger name is 'reveda'
        self.logger = logging.getLogger("reveda")
        # library definition file path
        self.runPath = pathlib.Path.cwd()
        # look for library.json file where the script is invoked
        self.libraryPathObj = self.runPath.joinpath("library.json")
        self.libraryDict = self.readLibDefFile(self.libraryPathObj)
        self.libraryBrowser = edw.libraryBrowser(self)

        self.logger_def()
        # revEDAPathObj = Path(__file__)
        # library definition file path
        self.runPath = pathlib.Path.cwd()
        # look for library.json file where the script is invoked
        self.libraryPathObj = self.runPath.joinpath("library.json")
        self.libraryDict = self.readLibDefFile(self.libraryPathObj)
        self.textEditorPath = self.runPath
        self.threadPool = QThreadPool.globalInstance()
        self.confFilePath = self.runPath.joinpath("reveda.conf")
        self.loadState()

    def _createMenuBar(self):
        self.mainW_menubar = self.menuBar()
        self.mainW_menubar.setNativeMenuBar(False)
        # Returns QMenu object.
        self.menuFile = self.mainW_menubar.addMenu("&File")
        self.menuTools = self.mainW_menubar.addMenu("&Tools")
        self.importTools = self.menuTools.addMenu("&Import")
        self.menuOptions = self.mainW_menubar.addMenu("&Options")
        self.menuHelp = self.mainW_menubar.addMenu("&Help")
        self.menuFile.addAction(self.exitAction)
        self.menuTools.addAction(self.libraryBrowserAction)
        self.importTools.addAction(self.importVerilogaAction)
        self.menuOptions.addAction(self.optionsAction)
        # self.menuHelp.addAction(self.helpAction)
        # self.menuHelp.addAction(self.aboutAction)
        self.menuOptions.addAction(self.optionsAction)

    def _createActions(self):
        exitIcon = QIcon(":/icons/external.png")
        self.exitAction = QAction(exitIcon, "Exit", self)
        self.exitAction.setShortcut("Ctrl+Q")
        importVerilogaIcon = QIcon(":/icons/document-import.png")
        self.importVerilogaAction = QAction(
            importVerilogaIcon, "Import Verilog-a file..."
        )
        openLibIcon = QIcon(":/icons/database--pencil.png")
        self.libraryBrowserAction = QAction(openLibIcon, "Library Browser", self)
        optionsIcon = QIcon(":/icons/resource-monitor.png")
        self.optionsAction = QAction(optionsIcon, "Options...", self)

    def _createTriggers(self):
        self.exitAction.triggered.connect(self.exitApp)  # type: ignore
        self.libraryBrowserAction.triggered.connect(self.libraryBrowserClick)
        self.importVerilogaAction.triggered.connect(self.importVerilogaClick)
        self.optionsAction.triggered.connect(self.optionsClick)

    def readLibDefFile(self, libPath: pathlib.Path):
        libraryDict = dict()
        data = dict()
        if libPath.exists():
            with libPath.open(mode="r") as f:
                data = json.load(f)
            if data.get("libdefs") is not None:
                for key, value in data["libdefs"].items():
                    libraryDict[key] = pathlib.Path(value)
            elif data.get("include") is not None:
                for item in data.get("include"):
                    libraryDict.update(self.readLibDefFile(pathlib.Path(item)))
        return libraryDict

    # open library browser window
    def libraryBrowserClick(self):
        self.libraryBrowser.show()
        self.libraryBrowser.raise_()

    def logger_def(self):
        logging.basicConfig(level=logging.INFO)

        c_handler = logging.StreamHandler(stream=self.centralW.console)
        c_handler.setLevel(logging.INFO)
        c_format = logging.Formatter("%(levelname)s - %(message)s")
        c_handler.setFormatter(c_format)
        f_handler = logging.FileHandler("reveda.log")
        f_handler.setLevel(logging.INFO)
        f_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        f_handler.setFormatter(f_format)
        self.logger.addHandler(c_handler)
        self.logger.addHandler(f_handler)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirm Exit',
                                     'Are you sure you want to exit?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.app.closeAllWindows()
        else:
            event.ignore()

    def optionsClick(self):
        dlg = fd.appProperties(self)
        dlg.editorPathEdit.setText(str(self.textEditorPath))
        dlg.simPathEdit.setText(str(self.simulationPath))
        dlg.switchViewsEdit.setText(", ".join(self.switchViewList))
        dlg.stopViewsEdit.setText(", ".join(self.stopViewList))

        if dlg.exec() == QDialog.Accepted:
            self.textEditorPath = pathlib.Path(dlg.editorPathEdit.text())
            self.simulationPath = pathlib.Path(dlg.simPathEdit.text())
            self.switchViewList = [
                switchView.strip()
                for switchView in dlg.switchViewsEdit.text().split(",")
            ]
            self.stopViewList = [
                stopView.strip() for stopView in
                dlg.stopViewsEdit.text().split(",")
            ]
            if dlg.optionSaveBox.isChecked():
                self.saveState()

    def importVerilogaClick(self):
        """
        Import a verilog-a view and add it to a design library
        """
        libraryModel = self.libraryBrowser.libraryModel
        importDlg = fd.importVerilogaCellDialogue(libraryModel, self)
        importDlg.vaViewName.setText("veriloga")
        if importDlg.exec() == QDialog.Accepted:
            importedVaObj = hdl.verilogaC(
                pathlib.Path(importDlg.vaFileEdit.text()))
            vaViewItemTuple = imv.createVaView(self, importDlg, libraryModel,
                                               importedVaObj)
            if importDlg.symbolCheckBox.isChecked():
                imv.createVaSymbol(self, vaViewItemTuple, self.libraryDict,
                                   self.libraryBrowser, importedVaObj)

    def loadState(self):

        if self.confFilePath.exists():
            self.logger.info(f'Configuration file: {self.confFilePath} exists')
            with self.confFilePath.open(mode="r") as f:
                items = json.load(f)

            self.textEditorPath = pathlib.Path(items.get("textEditorPath"))
            self.simulationPath = pathlib.Path(items.get("simulationPath"))
            if items.get("switchViewList")[0] != '':
                self.switchViewList = items.get("switchViewList")
            if items.get("stopViewList")[0] != '':
                self.stopViewList = items.get("stopViewList")

    def saveState(self):
        items = {
            "textEditorPath": str(self.textEditorPath),
            "simulationPath": str(self.simulationPath),
            "switchViewList": self.switchViewList,
            "stopViewList": self.stopViewList,
        }
        with self.confFilePath.open(mode="w", encoding="utf") as f:
            json.dump(items, f, indent=4)


    def exitApp(self):
        self.app.closeAllWindows()
