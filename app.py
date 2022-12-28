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

import logging
import logging.config
import pathlib
import sys
from contextlib import redirect_stderr, redirect_stdout

from PySide6.QtCore import (Qt, QPoint)
from PySide6.QtGui import (QAction, QFont, QIcon)
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QDialog)
import resources.resources
import backend.hdlBackEnd as hdl
import backend.schBackEnd as scb  # import the backend
import fileio.symbolEncoder as se
import common.pens as pens
import common.shape as shp
import gui.editorWindows as edw
import gui.fileDialogues as fd
import gui.propertyDialogues as pdlg
import gui.pythonConsole as pcon


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

        self.textEditorPath = None
        # this list is the list of usable cellviews.i
        self.cellViews = ["schematic", "symbol", "layout", "veriloga", "spice"]
        self.init_UI()
        # logger definition
        self.logger_def()
        # revEDAPathObj = Path(__file__)
        # library definition file path
        self.libraryPathObj = pathlib.Path.cwd().joinpath('library.json')
        self.libraryDict = scb.readLibDefFile(self.libraryPathObj,self.logger)

    def logger_def(self):
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
        importDlg = fd.importCellDialogue(libraryModel, self)
        importDlg.vaViewName.setText('veriloga')
        if importDlg.exec() == QDialog.Accepted:
            self.importedVaObj = hdl.verilogaC(pathlib.Path(importDlg.vaFileEdit.text()))
            libItem = fd.createCellDialog.getLibItem(libraryModel,
                                                     importDlg.libNamesCB.currentText())

            # selectedLibName = dlg.libNamesCB.currentText()
            # selectedLibItem = libraryModel.findItems(selectedLibName)[0]
            libItemRow = libItem.row()
            libCellNames = [libraryModel.item(libItemRow).child(i).cellName for i in
                            range(libraryModel.item(libItemRow).rowCount())]
            cellName = importDlg.cellNamesCB.currentText().strip()
            if cellName not in libCellNames and cellName != '':
                scb.createCell(self, libraryModel, libItem, cellName)
            cellItem = fd.createCellDialog.getCellItem(libItem, cellName)

            symbolViewItem = scb.createCellView(self, 'symbol', cellItem)
            symbolWindow = edw.symbolEditor(symbolViewItem.data(Qt.UserRole + 2),
                                            self.libraryDict,
                                            self.libraryBrowser.libBrowserCont.designView)

            dlg = pdlg.symbolCreateDialog(self, self.importedVaObj.inPins,
                                          self.importedVaObj.outPins, self.importedVaObj.inoutPins)
            dlg.leftPinsEdit.setText(','.join(self.importedVaObj.inPins))
            dlg.rightPinsEdit.setText(','.join(self.importedVaObj.outPins))
            dlg.topPinsEdit.setText(','.join(self.importedVaObj.inoutPins))
            symbolPen = pens.pen.returnPen('symbolPen')
            labelPen = pens.pen.returnPen('labelPen')
            pinPen = pens.pen.returnPen(('pinPen'))

            if dlg.exec() == QDialog.Accepted:
                try:
                    leftPinNames = list(filter(None, [pinName.strip() for pinName in
                                                      dlg.leftPinsEdit.text().split(
                                                          ',')]))
                    rightPinNames = list(filter(None, [pinName.strip() for pinName in
                                                       dlg.rightPinsEdit.text().split(
                                                           ',')]))
                    topPinNames = list(filter(None, [pinName.strip() for pinName in
                                                     dlg.topPinsEdit.text().split(',')]))
                    bottomPinNames = list(filter(None, [pinName.strip() for pinName in
                                                        dlg.bottomPinsEdit.text().split(
                                                            ',')]))
                    stubLength = int(float(dlg.stubLengthEdit.text().strip()))
                    pinDistance = int(float(dlg.pinDistanceEdit.text().strip()))
                    rectXDim = (max(len(topPinNames),
                                    len(bottomPinNames)) + 1) * pinDistance
                    rectYDim = (max(len(leftPinNames),
                                    len(rightPinNames)) + 1) * pinDistance
                except ValueError:
                    self.logger.error("Enter valid value")
                symbolScene = symbolWindow.centralW.scene
                symbolScene.rectDraw(QPoint(0, 0), QPoint(rectXDim, rectYDim), symbolPen,
                                     symbolScene.gridTuple)
                symbolScene.labelDraw(QPoint(int(0.25 * rectXDim), int(0.4 * rectYDim)),
                                      labelPen, '[@cellName]', symbolScene.gridTuple,
                                      "NLPLabel", "12", "Center", "R0", "Instance")
                symbolScene.labelDraw(QPoint(int(rectXDim), int(-0.2 * rectYDim)),
                                      labelPen, '[@instName]', symbolScene.gridTuple,
                                      "NLPLabel", "12", "Center", "R0", "Instance")
                vaFileLabel = symbolScene.labelDraw(
                    QPoint(int(0.25 * rectXDim), int(0.6 * rectYDim)), labelPen,
                    f'[@vaFile:vaFile=%:vaFile={str(self.importedVaObj.pathObj)}]',
                    symbolScene.gridTuple, "NLPLabel", "12", "Center", "R0", "Instance")
                vaFileLabel.labelVisible = False
                vaModuleLabel = symbolScene.labelDraw(
                    QPoint(int(0.25 * rectXDim), int(0.8 * rectYDim)), labelPen,
                    f'[@vaModule:vaModule=%:vaModule={self.importedVaObj.vaModule}]',
                    symbolScene.gridTuple, "NLPLabel", "12", "Center", "R0", "Instance")
                vaModuleLabel.labelVisible = False
                vaModelLabel = symbolScene.labelDraw(
                    QPoint(int(0.25 * rectXDim), int(1 * rectYDim)), labelPen,
                    f'[@vaModel:vaModel=%:vaModel={self.importedVaObj.vaModule}Model]',
                    symbolScene.gridTuple, "NLPLabel", "12", "Center", "R0", "Instance")
                vaModelLabel.labelVisible = False
                i = 0
                instParamNum = len(self.importedVaObj.instanceParams)
                for key, value in self.importedVaObj.instanceParams.items():
                    symbolScene.labelDraw(
                        QPoint(int(rectXDim), int(i * 0.2 * rectYDim / instParamNum)),
                        labelPen, f'[@{key}:{key}=%:{key}={value}]',
                        symbolScene.gridTuple, "NLPLabel", "12", "Center", "R0",
                        "Instance")

                leftPinLocs = [QPoint(-stubLength, (i + 1) * pinDistance) for i in
                               range(len(leftPinNames))]
                rightPinLocs = [QPoint(rectXDim + stubLength, (i + 1) * pinDistance) for i
                                in range(len(rightPinNames))]
                bottomPinLocs = [QPoint((i + 1) * pinDistance, rectYDim + stubLength) for
                                 i in range(len(bottomPinNames))]
                topPinLocs = [QPoint((i + 1) * pinDistance, - stubLength) for i in
                              range(len(topPinNames))]
                for i, pinName in enumerate(leftPinNames):
                    symbolScene.lineDraw(leftPinLocs[i],
                                         leftPinLocs[i] + QPoint(stubLength, 0),
                                         symbolScene.symbolPen, symbolScene.gridTuple)
                    symbolScene.addItem(shp.pin(leftPinLocs[i], pinPen, pinName))
                for i, pinName in enumerate(rightPinNames):
                    symbolScene.lineDraw(rightPinLocs[i],
                                         rightPinLocs[i] + QPoint(-stubLength, 0),
                                         symbolScene.symbolPen, symbolScene.gridTuple)
                    symbolScene.addItem(shp.pin(rightPinLocs[i], pinPen, pinName))
                for i, pinName in enumerate(topPinNames):
                    symbolScene.lineDraw(topPinLocs[i],
                                         topPinLocs[i] + QPoint(0, stubLength),
                                         symbolScene.symbolPen, symbolScene.gridTuple)
                    symbolScene.addItem(shp.pin(topPinLocs[i], pinPen, pinName))
                for i, pinName in enumerate(bottomPinNames):
                    symbolScene.lineDraw(bottomPinLocs[i],
                                         bottomPinLocs[i] + QPoint(0, -stubLength),
                                         symbolScene.symbolPen, symbolScene.gridTuple)
                    symbolScene.addItem(shp.pin(bottomPinLocs[i], pinPen, pinName))
                symbolScene.attributeList = list()  # empty attribute list
                for key, value in self.importedVaObj.modelParams.items():
                    symbolScene.attributeList.append(se.symbolAttribute(key, value))
                # pinsString = ' '.join([f'[|{pin}:%]' for pin in self.importedVaObj.pins])
                # instParamString = ' '.join(
                #     [f'[@{key}:{key}=%:{key}={item}]' for key, item in
                #      self.importedVaObj.instanceParams.items()])
                # symbolScene.attributeList.append(se.symbolAttribute('NLPDeviceFormat',
                #                 f'Y{self.importedVaObj.vaModule} [@instName] {pinsString} '
                #                 f'{vaModelLabel.labelDefinition} {instParamString}'))
                symbolWindow.show()
                symbolWindow.libraryView.openViews[f'{libItem.libraryName}_{cellName}_' \
                                                   f'{symbolViewItem.viewName}'] = symbolWindow

                scb.createCellView(self, importDlg.vaViewName.text(), cellItem)
    def optionsClick(self):
        dlg = fd.appProperties(self)
        if self.textEditorPath:
            dlg.editorPathEdit.setText(self.textEditorPath)
        if dlg.exec() == QDialog.Accepted:
            self.textEditorPath = pathlib.Path(dlg.editorPathEdit.text())

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
