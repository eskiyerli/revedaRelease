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

#
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
#
import json
import logging
import logging.config
import pathlib

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QAction, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.hdlBackEnd as hdl
import revedaEditor.backend.importViews as imv
import revedaEditor.fileio.importLayp as imlyp
import revedaEditor.fileio.importXschemSym as impxsym
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.helpBrowser as hlp
import revedaEditor.gui.libraryBrowser as libw
import revedaEditor.gui.pythonConsole as pcon
import revedaEditor.gui.revinit as revinit
import revedaEditor.gui.stippleEditor as stip
import revedaEditor.resources.resources


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
        self.console.setfont(QFont("Fira Mono Regular", 12))
        self.console.writeoutput(
            f"Welcome to Revolution EDA version {revinit.__version__}"
        )
        self.console.writeoutput("Revolution Semiconductor (C) 2024.")
        self.console.writeoutput(
            "Mozilla Public License v2.0 modified with Commons Clause"
        )
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
            "pcell",
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
        # print(self.app.reveda_runpathObj)
        # logger name is 'reveda'
        self.logger = logging.getLogger("reveda")
        # library definition file path
        self.runPath = pathlib.Path.cwd()
        # look for library.json file where the script is invoked
        self.libraryPathObj = self.runPath.joinpath("library.json")
        self.libraryDict = self.readLibDefFile(self.libraryPathObj)
        self.libraryBrowser = libw.libraryBrowser(self)
        self.logger_def()
        # revEDAPathObj = Path(__file__)
        # library definition file path
        self.runPath = pathlib.Path.cwd()
        # look for library.json file where the script is invoked
        self.libraryPathObj = self.runPath.joinpath("library.json")
        self.libraryDict = self.readLibDefFile(self.libraryPathObj)
        self.textEditorPath: pathlib.Path = self.runPath
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
        self.menuTools.addAction(self.createStippleAction)
        self.importTools.addAction(self.importVerilogaAction)
        self.importTools.addAction(self.importSpiceAction)
        self.importTools.addAction(self.importLaypFileAction)
        self.importTools.addAction((self.importXschSymAction))
        self.menuOptions.addAction(self.optionsAction)
        self.menuHelp.addAction(self.helpAction)
        self.menuHelp.addAction(self.aboutAction)
        self.menuOptions.addAction(self.optionsAction)

    def _createActions(self):
        exitIcon = QIcon(":/icons/external.png")
        self.exitAction = QAction(exitIcon, "Exit", self)
        self.exitAction.setShortcut("Ctrl+Q")
        importVerilogaIcon = QIcon(":/icons/document-import.png")
        self.importVerilogaAction = QAction(
            importVerilogaIcon, "Import Verilog-a file..."
        )
        self.importSpiceAction = QAction(
            importVerilogaIcon, "Import Spice file...", self
        )
        self.importLaypFileAction = QAction(
            importVerilogaIcon, "Import KLayout Layer Prop. " "File...", self
        )
        self.importXschSymAction = QAction(
            importVerilogaIcon, "Import Xschem Symbols...", self
        )
        openLibIcon = QIcon(":/icons/database--pencil.png")
        self.libraryBrowserAction = QAction(openLibIcon, "Library Browser", self)
        optionsIcon = QIcon(":/icons/resource-monitor.png")
        self.optionsAction = QAction(optionsIcon, "Options...", self)
        self.createStippleAction = QAction("Create Stipple...", self)
        helpIcon = QIcon(":/icons/document-arrow.png")
        self.helpAction = QAction(helpIcon, "Help...", self)
        self.aboutIcon = QIcon(":/icons/information.png")
        self.aboutAction = QAction(self.aboutIcon, "About", self)

    def _createTriggers(self):
        self.exitAction.triggered.connect(self.exitApp)  # type: ignore
        self.libraryBrowserAction.triggered.connect(self.libraryBrowserClick)
        self.importVerilogaAction.triggered.connect(self.importVerilogaClick)
        self.importSpiceAction.triggered.connect(self.importSpiceClick)
        self.importLaypFileAction.triggered.connect(self.importLaypClick)
        self.importXschSymAction.triggered.connect(self.importXschSymClick)
        self.optionsAction.triggered.connect(self.optionsClick)
        self.createStippleAction.triggered.connect(self.createStippleClick)
        self.helpAction.triggered.connect(self.helpClick)
        self.aboutAction.triggered.connect(self.aboutClick)

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
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            for item in self.app.topLevelWidgets():
                item.close()
            # self.app.closeAllWindows()
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
                stopView.strip() for stopView in dlg.stopViewsEdit.text().split(",")
            ]
            if dlg.optionSaveBox.isChecked():
                self.saveState()

    def importVerilogaClick(self):
        """
        Import a Verilog-A view and add it to a design library.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        self.importVerilogaModule(ddef.viewTuple("", "", ""), "")

    def importVerilogaModule(self, viewT: ddef.viewTuple, filePath: str):
        """

        @param filePath:
        """
        library_model = self.libraryBrowser.libraryModel
        # Open the import dialog
        importDlg = fd.importVerilogaCellDialogue(library_model, self)
        importDlg.vaFileEdit.setText(filePath)
        if viewT.libraryName:
            importDlg.libNamesCB.setCurrentText(viewT.libraryName)
        if viewT.cellName:
            importDlg.cellNamesCB.setCurrentText(viewT.cellName)
        if viewT.viewName:
            importDlg.vaViewName.setText(viewT.viewName)
        else:
            # Set the default view name in the dialog
            importDlg.vaViewName.setText("veriloga")
        # Execute the import dialog and check if it was accepted
        if importDlg.exec() == QDialog.Accepted:
            # Create the Verilog-A object from the file path
            imported_va_obj = hdl.verilogaC(pathlib.Path(importDlg.vaFileEdit.text()))

            # Create the Verilog-A view item tuple
            vaViewItemTuple = imv.createVaView(
                self, importDlg, library_model, imported_va_obj
            )

            # Check if the symbol checkbox is checked
            if importDlg.symbolCheckBox.isChecked():
                # Create the Verilog-A symbol
                imv.createVaSymbol(
                    self,
                    vaViewItemTuple,
                    self.libraryDict,
                    self.libraryBrowser,
                    imported_va_obj,
                )

    def importSpiceClick(self):
        """
        Import a Spice view and add it to a design library.

        Args:
            self: The instance of the class.

        Returns:
            None
        """
        self.importSpiceSubckt("", ddef.viewTuple("", "", ""))

    def importLaypClick(self):

        importDlg = fd.klayoutLaypImportDialogue(self)
        if importDlg.exec() == QDialog.Accepted:
            imlyp.parseLyp(importDlg.laypFileEdit.text())

    def importXschSymClick(self):
        importDlg = fd.xschemSymIimportDialogue(self, self.libraryBrowser.libraryModel)

        if importDlg.exec() == QDialog.Accepted:
            symbolFiles = importDlg.symFileEdit.text().split(",")
            importLibraryName = importDlg.libNamesCB.currentText()
            scaleFactor = float(importDlg.scaleEdit.text().strip())
            symbolFileObjList = []
            for symbolFile in symbolFiles:
                symbolFileObjList.append(pathlib.Path(symbolFile.strip()))
            for symbolFileObj in symbolFileObjList:
                importObj = impxsym.importXschemSym(
                    self,
                    symbolFileObj,
                    self.libraryBrowser.designView,
                    importLibraryName,
                )
                importObj.scaleFactor = scaleFactor
                importObj.importSymFile()

    def importSpiceSubckt(self, viewT: ddef.viewTuple, filePath: str):
        # Get the library model
        library_model = self.libraryBrowser.libraryModel
        # Open the import dialog
        importDlg = fd.importSpiceCellDialogue(library_model, self)
        importDlg.spiceFileEdit.setText(filePath)
        # Set the default view name in the dialog
        if viewT.libraryName:
            importDlg.libNamesCB.setCurrentText(viewT.libraryName)
        if viewT.cellName:
            importDlg.cellNamesCB.setCurrentText(viewT.cellName)
        if viewT.viewName:
            importDlg.spiceViewName.setText(viewT.viewName)
        else:
            importDlg.spiceViewName.setText("spice")
        # Execute the import dialog and check if it was accepted
        if importDlg.exec() == QDialog.Accepted:
            # Create the Verilog-A object from the file path
            importedSpiceObj = hdl.spiceC(pathlib.Path(importDlg.spiceFileEdit.text()))

            # Create the Verilog-A view item tuple
            spiceViewItemTuple = imv.createSpiceView(
                self, importDlg, library_model, importedSpiceObj
            )

            # Check if the symbol checkbox is checked
            if importDlg.symbolCheckBox.isChecked():
                # Create the spice symbol
                imv.createSpiceSymbol(
                    self,
                    spiceViewItemTuple,
                    self.libraryDict,
                    self.libraryBrowser,
                    importedSpiceObj,
                )

    def createStippleClick(self):
        stippleWindow = stip.stippleEditor(self)
        stippleWindow.show()

    def helpClick(self):
        helpBrowser = hlp.helpBrowser(self)
        helpBrowser.show()

    def aboutClick(self):
        abtDlg = hlp.aboutDialog(self)
        abtDlg.show()

    def loadState(self):
        """
        Load the state of the object from a configuration file.

        This function reads the contents of the configuration file and updates the
         state of the object based on the values found in the file.
        It checks if the configuration file exists and then opens it for reading.
        If the file exists, it loads the contents of the file as a
        JSON object and assigns the values to the corresponding attributes of the
        object. The attributes updated include `textEditorPath`,
        `simulationPath`, `switchViewList`, and `stopViewList`. If the `switchViewList`
        or `stopViewList` in the configuration file is not
        empty, it updates the corresponding attributes with the values from the file.
        """

        if self.confFilePath.exists():
            self.logger.info(f"Configuration file: {self.confFilePath} exists")
            with self.confFilePath.open(mode="r") as f:
                items = json.load(f)
            self.textEditorPath = pathlib.Path(items.get("textEditorPath"))
            self.simulationPath = pathlib.Path(items.get("simulationPath"))
            if items.get("switchViewList")[0] != "":
                self.switchViewList = items.get("switchViewList")
            if items.get("stopViewList")[0] != "":
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
