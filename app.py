#  “Commons Clause” License Condition v1.0
#
#  The Software is provided to you by the Licensor under the License, as defined
#  below, subject to the following condition.
#
#  Without limiting other conditions in the License, the grant of rights under the
#  License will not include, and the License does not grant to you, the right to
#  Sell the Software.
#
#  For purposes of the foregoing, “Sell” means practicing any or all of the rights
#  granted to you under the License to provide to third parties, for a fee or other
#  consideration (including without limitation fees for hosting or consulting/
#  support services related to the Software), a product or service whose value
#  derives, entirely or substantially, from the functionality of the Software. Any
#  license notice or attribution required by the License must also include this
#  Commons Clause License Condition notice.
#
#  Software: Revolution EDA
#  License: Mozilla Public License 2.0
#  Licensor: Revolution Semiconductor (Registered in the Netherlands)
#

import logging
import logging.config
import pathlib
import sys
from contextlib import redirect_stderr, redirect_stdout

import backend.schBackEnd as scb  # import the backend
import gui.editorWindows as edw
import gui.pythonConsole as pcon
import gui.fileDialogues as fd
import backend.hdlBackEnd as hdl
import api.ui as ui
import resources.resources
from PySide6.QtCore import (Qt, )
from PySide6.QtGui import (QAction, QFont, QIcon)
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QMenuBar,
                               QDialog)


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

        self.console.writeoutput("Welcome to RevEDA")
        self.console.writeoutput("Revolution Semiconductor (C) 2022.")
        self.console.setfont(QFont("Fira Mono Regular", 12))
        # layout statements, using a grid layout
        gLayout = QVBoxLayout()
        gLayout.setSpacing(10)
        gLayout.addWidget(self.console)
        self.setLayout(gLayout)


# main application window definition
class mainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        # revEDAPathObj = Path(__file__)
        revEDADirObj = pathlib.Path.cwd().parent
        # library definition file path
        libraryPathObj = revEDADirObj.joinpath("library.yaml")
        try:
            with libraryPathObj.open(mode="r") as f:
                # create a dictionary of library (directory) names and paths
                self.libraryDict = scb.readLibDefFile(f)
        except IOError:
            print(f"Cannot find {str(libraryPathObj)} file.")
            self.libraryDict = {}
        # this list is the list of usable cellviews.i
        self.cellViews = ["schematic", "symbol", "layout", "veriloga"]
        self.init_UI()
        # Create a custom logger
        self.logger = logging.getLogger(__name__)
        c_handler = logging.StreamHandler(stream=self.centralW.console)
        c_handler.setLevel(logging.WARNING)
        c_format = logging.Formatter('%(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        f_handler = logging.FileHandler('reveda.log')
        f_handler.setLevel(logging.DEBUG)
        f_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(f_format)
        self.logger.addHandler(c_handler)
        self.logger.addHandler(f_handler)

    def init_UI(self):
        self.resize(900, 300)
        self._createMenuBar()
        self._createActions()
        self._createTriggers()
        # create container to position all widgets
        self.centralW = mainwContainer(self)
        self.setCentralWidget(self.centralW)
        self.libraryBrowser = None

    def _createMenuBar(self):
        self.mainW_menubar = self.menuBar()
        self.mainW_menubar.setNativeMenuBar(False)
        # Returns QMenu object.
        self.menuFile = self.mainW_menubar.addMenu("&File")
        self.menuTools = self.mainW_menubar.addMenu("&Tools")
        self.importTools = self.menuTools.addMenu("&Import")
        self.menuOptions = self.mainW_menubar.addMenu("&Options")
        self.menuHelp = self.mainW_menubar.addMenu("&Help")

        self.mainW_statusbar = self.statusBar()
        self.mainW_statusbar.showMessage("Ready")

        # create actions

    def _createActions(self):
        exitIcon = QIcon(":/icons/external.png")
        self.exitAction = QAction(exitIcon, "Exit", self)
        self.exitAction.setShortcut("Ctrl+Q")

        self.menuFile.addAction(self.exitAction)

        openLibIcon = QIcon(":/icons/database--pencil.png")
        self.libraryBrowserAction = QAction(openLibIcon, "Library Browser", self)
        self.menuTools.addAction(self.libraryBrowserAction)
        importVerilogaIcon = QIcon(":/icons/document--plus.png")
        self.importVerilogaAction = QAction(importVerilogaIcon,
                                            'Import Verilog-a file...')
        self.importTools.addAction(self.importVerilogaAction)
        optionsIcon = QIcon(":/icons/resource-monitor.png")
        self.optionsAction = QAction(optionsIcon, "Options...", self)
        self.menuOptions.addAction(self.optionsAction)

    def _createTriggers(self):
        self.exitAction.triggered.connect(self.exitApp)  # type: ignore
        self.libraryBrowserAction.triggered.connect(self.libraryBrowserClick)
        self.importVerilogaAction.triggered.connect(self.importVerilogaClick)
        self.optionsAction.triggered.connect(self.optionsClick)
    # open library browser window
    def libraryBrowserClick(self):
        if self.libraryBrowser is None:
            self.libraryBrowser = edw.libraryBrowser(self)  # create the library browser
            self.libraryBrowser.show()  # update the main library dictionary if library path dialogue  # is OK'd.
        else:
            self.libraryBrowser.show()
            self.libraryBrowser.raise_()

    def importVerilogaClick(self):
        '''
        Import a verilog-a view and add it to a design library
        '''
        if self.libraryBrowser is None:
            # create libBrowser if it does not exist, but do not show it
            self.libraryBrowser = edw.libraryBrowser(self)
        libraryModel = self.libraryBrowser.libBrowserCont.designView.libraryModel
        dlg = fd.importCellDialogue(libraryModel, self)
        if dlg.exec() == QDialog.Accepted:
            self.importedFileObj = pathlib.Path(dlg.vaFileEdit.text())
            importedVaObj = hdl.verilogaC(self.importedFileObj)
            selectedLibName = dlg.libNamesCB.currentText()
            selectedLibItem = libraryModel.findItems(selectedLibName)[0]
            selectedLibItemRow = selectedLibItem.row()
            libCellNames = [libraryModel.item(selectedLibItemRow).child(i).cellName for i
                            in range(libraryModel.item(selectedLibItemRow).rowCount())]
            if dlg.cellNamesCB.currentText() not in libCellNames and \
                    dlg.cellNamesCB.currentText() !='':  # a new
                # cell
                scb.createCell(self,libraryModel, selectedLibItem,
                               dlg.cellNamesCB.currentText())
            i=0
            while i <= selectedLibItem.rowCount():
                if selectedLibItem.child(i).cellName == dlg.cellNamesCB.currentText():
                    cellItem = selectedLibItem.child(i)
                    break
                i += 1
            else:
                cellItem = None
            if cellItem is not None:
                viewItem = scb.createCellView(self,dlg.vaViewName.text(),cellItem.data(
                    Qt.UserRole+2))

    def optionsClick(self):
        pass

    def libDictUpdate(self):
        self.libraryDict = self.libraryBrowser.libraryDict

    def exitApp(self):
        self.app.closeAllWindows()

    def closeEvent(self, event):
        self.app.closeAllWindows()
        event.accept()


# Start Main application window
app = QApplication(sys.argv)
app.setStyle("Fusion")
# empty argument as there is no parent window.
mainW = mainWindow(app)
mainW.setWindowTitle("Revolution EDA")
redirect = pcon.Redirect(mainW.centralW.console.errorwrite)
with redirect_stdout(mainW.centralW.console), redirect_stderr(redirect):
    mainW.show()
    sys.exit(app.exec())
