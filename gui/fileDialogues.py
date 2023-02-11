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

import pathlib

from PySide6.QtCore import (Qt, QDir)
from PySide6.QtGui import (QStandardItemModel, QStandardItem, QCursor, QAction)
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                               QFormLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout,
                               QPushButton, QGroupBox, QTableView, QMenu, )

import backend.schBackEnd as scb
import common.shape as shp
import gui.editFunctions as edf
import backend.libraryMethods as libm


class createCellDialog(QDialog):
    def __init__(self, parent, model):
        super().__init__(parent=parent)
        self.parent = parent
        self.model = model
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Create Cell")
        self.layout = QFormLayout()
        self.layout.setSpacing(10)
        self.libNamesCB = QComboBox()
        self.libNamesCB.setModel(self.model)
        self.libNamesCB.setModelColumn(0)
        self.libNamesCB.setCurrentIndex(0)
        self.libNamesCB.currentTextChanged.connect(self.selectLibrary)
        self.layout.addRow(edf.boldLabel("Library:"), self.libNamesCB)
        self.cellCB = QComboBox()
        libItem = libm.getLibItem(self.model, self.libNamesCB.currentText())
        self.cellList = [libItem.child(i).cellName for i in range(libItem.rowCount())]
        self.cellCB.addItems(self.cellList)
        self.cellCB.setEditable(True)
        self.layout.addRow(edf.boldLabel("Cell Name:"), self.cellCB)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def selectLibrary(self):
        libItem = libm.getLibItem(self.model, self.libNamesCB.currentText())
        cellList = [libItem.child(i).cellName for i in range(libItem.rowCount())]
        self.cellCB.clear()
        self.cellCB.addItems(cellList)

    # @staticmethod
    # def getLibItem(libraryModel: QStandardItemModel, libName: str) -> scb.libraryItem:
    #     return libm.getLibItem(libraryModel, libName)
    #
    # @staticmethod
    # def getCellItem(libItem: scb.libraryItem, cellNameInp: str) -> scb.cellItem:
    #     return libm.getCellItem(libItem,cellNameInp)
    #
    # @staticmethod
    # def getViewItem(cellItem: scb.cellItem, viewNameInp: str) -> scb.viewItem:
    #     return libm.getViewItem(cellItem, viewNameInp)


class deleteCellDialog(createCellDialog):
    def __init__(self, parent, model):
        super().__init__(parent, model)
        self.cellCB.setEditable(False)
        self.setWindowTitle('Delete Cell')


class newCellViewDialog(createCellDialog):
    def __init__(self, parent, model):
        super().__init__(parent, model)
        self.cellCB.setEditable(False)
        self.setWindowTitle('Create Cell View')
        self.viewType = QComboBox()
        self.layout.addRow(edf.boldLabel("View Type:"), self.viewType)
        self.viewName = edf.longLineEdit()
        self.layout.addRow(edf.boldLabel('View Name:'), self.viewName)
        self.layout.setSpacing(10)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class selectCellViewDialog(deleteCellDialog):
    def __init__(self, parent, model):
        super().__init__(parent=parent, model=model)
        libItem = libm.getLibItem(self.model, self.libNamesCB.currentText())
        self.setWindowTitle("Select CellView")
        self.cellCB.currentTextChanged.connect(self.cellNameChanged)
        self.viewCB = QComboBox()
        cellItem = libm.getCellItem(libItem, self.cellCB.currentText())
        self.viewCB.addItems(
            [cellItem.child(i).text() for i in range(cellItem.rowCount())])

        self.layout.addRow(edf.boldLabel('View Name:'), self.viewCB)
        self.layout.setSpacing(10)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def cellNameChanged(self):
        libItem = libm.getLibItem(self.model, self.libNamesCB.currentText())
        cellItem = libm.getCellItem(libItem, self.cellCB.currentText())
        if cellItem is not None:
            viewList = [cellItem.child(i).text() for i in range(cellItem.rowCount())]
        else:
            viewList = []
        self.viewCB.clear()
        self.viewCB.addItems(viewList)


class createCellViewDialog(QDialog):
    def __init__(self, parent, model, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.model = model
        self.cellItem = cellItem
        self.cellPath = self.cellItem.data(Qt.UserRole + 2)
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Create CellView")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.viewComboBox = QComboBox()
        self.viewComboBox.addItems(self.parent.cellViews)
        layout.addRow("Select View:", self.viewComboBox)
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("CellView Name")
        self.nameEdit.setFixedWidth(200)
        layout.addRow(QLabel("View Name:"), self.nameEdit)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)


class renameCellDialog(QDialog):
    def __init__(self, parent, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.cellItem = cellItem

        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Rename Cell")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("Cell Name")
        self.nameEdit.setFixedWidth(200)
        layout.addRow(QLabel("Cell Name:"), self.nameEdit)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)


class copyCellDialog(QDialog):
    def __init__(self, parent, model, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.model = model
        self.cellItem = cellItem

        # self.index = 0
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Copy Cell")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.libraryComboBox = QComboBox()
        self.libraryComboBox.setModel(self.model)
        self.libraryComboBox.setModelColumn(0)
        self.libraryComboBox.setCurrentIndex(0)
        self.selectedLibPath = self.libraryComboBox.itemData(0, Qt.UserRole + 2)
        self.libraryComboBox.currentTextChanged.connect(self.selectLibrary)
        layout.addRow(QLabel("Library:"), self.libraryComboBox)
        self.copyName = QLineEdit()
        self.copyName.setPlaceholderText("Enter Cell Name")
        self.copyName.setFixedWidth(130)
        layout.addRow(QLabel("Cell Name:"), self.copyName)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)

    def selectLibrary(self):
        self.selectedLibPath = self.libraryComboBox.itemData(
            self.libraryComboBox.currentIndex(), Qt.UserRole + 2)


class copyViewDialog(createCellDialog):
    def __init__(self, parent, model):
        super().__init__(parent=parent, model=model)
        self.setWindowTitle('Copy View')
        self.cellCB.setEditable(True)
        self.cellCB.InsertPolicy = QComboBox.InsertAfterCurrent
        self.viewName = edf.longLineEdit()
        self.layout.addRow(edf.boldLabel('View Name:'), self.viewName)
        self.layout.setSpacing(10)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class closeLibDialog(QDialog):
    def __init__(self, libraryDict, parent, *args):
        super().__init__(parent, *args)
        self.libraryDict = libraryDict
        self.setWindowTitle('Select Library to close')
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        formLayout = QFormLayout()
        self.libNamesCB = QComboBox()
        self.libNamesCB.addItems(self.libraryDict.keys())
        formLayout.addRow(edf.boldLabel('Select Library', self), self.libNamesCB)
        layout.addLayout(formLayout)
        layout.addSpacing(40)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)


class renameLibDialog(QDialog):
    def __init__(self, parent, oldLibraryName, *args):
        super().__init__(parent, *args)
        self.oldLibraryName = oldLibraryName
        self.setWindowTitle(f'Change {oldLibraryName} to:')
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        formBox = QGroupBox('Rename Library')
        layout = QVBoxLayout()
        formLayout = QFormLayout()
        self.newLibraryName = edf.longLineEdit()
        formLayout.addRow(edf.boldLabel('New Library Name:', self), self.newLibraryName)
        formBox.setLayout(formLayout)
        layout.addWidget(formBox)
        layout.addSpacing(40)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)


class renameViewDialog(QDialog):
    def __init__(self, parent, oldViewName):
        super().__init__(parent)
        self.oldViewName = oldViewName
        self.setWindowTitle(f'Rename {oldViewName} ')
        self.layout = QVBoxLayout()
        formLayout = QFormLayout()
        oldViewNameEdit = edf.longLineEdit()
        oldViewNameEdit.setText(self.oldViewName)
        oldViewNameEdit.setEnabled(False)
        formLayout.addRow(edf.boldLabel('Old View Name:'), oldViewNameEdit)
        self.newViewNameEdit = edf.longLineEdit()
        formLayout.addRow(edf.boldLabel('New View Name:'), self.newViewNameEdit)
        self.layout.addLayout(formLayout)
        self.layout.setSpacing(10)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class deleteSymbolDialog(QDialog):
    def __init__(self, cellName, viewName, *args):
        super().__init__(*args)
        self.setWindowTitle(f'Delete {cellName}-{viewName} CellView?')
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel(f"{cellName}-{viewName} will be recreated!")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class netlistExportDialogue(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(f'Export Netlist?')
        self.setMinimumSize(500, 100)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addStretch(2)
        viewBox = QGroupBox('Select a view to Netlist')
        viewBoxLayout = QFormLayout()
        self.libNameEdit = edf.longLineEdit()
        self.libNameEdit.setDisabled(True)
        viewBoxLayout.addRow(edf.boldLabel('Library:'),self.libNameEdit)
        self.cellNameEdit = edf.longLineEdit()
        self.cellNameEdit.setDisabled(True)
        viewBoxLayout.addRow(edf.boldLabel('Cell:'), self.cellNameEdit)
        self.viewNameCombo = QComboBox()
        viewBoxLayout.addRow(edf.boldLabel('View:'),self.viewNameCombo)
        viewBox.setLayout(viewBoxLayout)
        self.mainLayout.addWidget(viewBox)
        switchBox = QGroupBox('Switch and Stop View Lists')
        self.formLayout = QFormLayout()
        self.switchViewEdit = edf.longLineEdit()
        self.switchViewEdit.setText((', ').join(self.parent.switchViewList))
        self.formLayout.addRow(edf.boldLabel('Switch View List:'), self.switchViewEdit)
        self.stopViewEdit = edf.longLineEdit()
        self.stopViewEdit.setText((', ').join(self.parent.stopViewList))
        self.formLayout.addRow((edf.boldLabel('Stop View: ')), self.stopViewEdit)
        switchBox.setLayout(self.formLayout)
        self.mainLayout.addWidget(switchBox)
        fileBox = QGroupBox('Select Simulation Directory')
        fileDialogLayout = QHBoxLayout()
        fileDialogLayout.addWidget(edf.boldLabel('Export Directory:'))
        self.netlistDirEdit = edf.longLineEdit()
        fileDialogLayout.addWidget(self.netlistDirEdit)
        self.netListDirButton = QPushButton('...')
        self.netListDirButton.clicked.connect(self.onDirButtonClicked)
        fileDialogLayout.addWidget(self.netListDirButton)
        fileBox.setLayout(fileDialogLayout)
        self.mainLayout.addWidget(fileBox)
        self.mainLayout.addStretch(2)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)

    def onDirButtonClicked(self):
        self.dirName = QFileDialog.getExistingDirectory()
        if self.dirName:
            self.netlistDirEdit.setText(self.dirName)


class goDownHierDialogue(QDialog):
    def __init__(self, symbolShape: shp.symbolShape, libraryDict: dict[str, pathlib.Path],
                 *args):
        self.symbolShape = symbolShape
        self.libraryDict = libraryDict
        super().__init__(*args)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        cellPropLayout = QFormLayout()
        libraryNameEdit = edf.shortLineEdit()
        libraryNameEdit.setText(self.symbolShape.libraryName)
        libraryNameEdit.setReadOnly(True)
        cellPropLayout.addRow(edf.boldLabel("Library Name:", self), libraryNameEdit)
        cellNameEdit = edf.shortLineEdit()
        cellNameEdit.setText(self.symbolShape.cellName)
        cellNameEdit.setReadOnly(True)
        cellPropLayout.addRow(edf.boldLabel("Cell Name:", self), cellNameEdit)
        cellPath = pathlib.Path(
            self.libraryDict.get(self.symbolShape.libraryName).joinpath(
                self.symbolShape.cellName))
        viewList = [str(view.stem) for view in cellPath.iterdir() if
                    view.suffix == ".json"]
        self.viewNameCB = QComboBox()
        self.viewNameCB.addItems(viewList)
        cellPropLayout.addRow(edf.boldLabel("Select View:", self), self.viewNameCB)
        mainLayout.addLayout(cellPropLayout)
        mainLayout.addStretch(2)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.show()


class importVerilogaCellDialogue(QDialog):
    def __init__(self, model, parent):
        super().__init__(parent)
        self._parent = parent
        self.setWindowTitle('Import a Verilog-a File')
        self._model = model
        self.setMinimumSize(500, 200)
        mainLayout = QVBoxLayout()
        fileDialogLayout = QHBoxLayout()
        fileDialogLayout.addWidget(edf.boldLabel('Select Verilog-A file:'), 1)
        self.vaFileEdit = edf.longLineEdit()
        fileDialogLayout.addWidget(self.vaFileEdit, 4)
        self.vaFileButton = QPushButton('...')
        self.vaFileButton.clicked.connect(self.onFileButtonClicked)
        fileDialogLayout.addWidget(self.vaFileButton, 1)
        mainLayout.addLayout(fileDialogLayout)
        mainLayout.addSpacing(20)
        layout = QFormLayout()
        layout.setSpacing(10)
        self.libNamesCB = QComboBox()
        self.libNamesCB.setModel(self._model)
        self.libNamesCB.currentTextChanged.connect(self.changeCells)
        layout.addRow(edf.boldLabel('Library:'), self.libNamesCB)
        self.cellNamesCB = QComboBox()
        self.cellNamesCB.setEditable(True)
        initialCellNames = [self._model.item(0).child(i).cellName for i in
                            range(self._model.item(0).rowCount())]
        self.cellNamesCB.addItems(initialCellNames)
        layout.addRow(edf.boldLabel('Cell:'), self.cellNamesCB)
        self.vaViewName = edf.longLineEdit()
        layout.addRow(edf.boldLabel('Verilog-A view:'), self.vaViewName)
        mainLayout.addLayout(layout)
        mainLayout.addSpacing(20)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.show()

    def changeCells(self):
        selectedLibItemRow = self._model.findItems(self.libNamesCB.currentText())[0].row()
        libCellNames = [self._model.item(selectedLibItemRow).child(i).cellName for i in
                        range(self._model.item(selectedLibItemRow).rowCount())]
        self.cellNamesCB.clear()
        self.cellNamesCB.addItems(libCellNames)

    def onFileButtonClicked(self):
        self.vaFileName = QFileDialog.getOpenFileName(self, caption='Select Verilog-A '
                                                                    'file.')[0]
        if self.vaFileName:
            self.vaFileEdit.setText(self.vaFileName)


class createConfigViewDialogue(QDialog):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        self.mainLayout = QVBoxLayout()
        self.setWindowTitle("Create New Config View")
        self.setMinimumSize(360, 400)
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
        self.switchViews = edf.longLineEdit()
        viewGroupLayout.addRow(edf.boldLabel('View List:'), self.switchViews)
        self.stopViews = edf.longLineEdit()
        viewGroupLayout.addRow(edf.boldLabel('Stop List:'), self.stopViews)
        self.mainLayout.addWidget(viewGroup)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)


class appProperties(QDialog):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setMinimumSize(550, 200)
        self.setWindowTitle('Revolution EDA Options')
        mainLayout = QVBoxLayout()
        filePathsGroup = QGroupBox('Paths')
        filePathsLayout = QVBoxLayout()
        fileDialogLayout = QHBoxLayout()
        fileDialogLayout.addWidget(edf.boldLabel('Text Editor Path:'), 2)
        self.editorPathEdit = edf.longLineEdit()
        fileDialogLayout.addWidget(self.editorPathEdit, 5)
        self.editFileButton = QPushButton('...')
        self.editFileButton.clicked.connect(self.onFileButtonClicked)
        fileDialogLayout.addWidget(self.editFileButton, 1)
        filePathsLayout.addLayout(fileDialogLayout)
        simPathDialogLayout = QHBoxLayout()
        simPathDialogLayout.addWidget(edf.boldLabel('Simulation Path:'),2)
        self.simPathEdit = edf.longLineEdit()
        simPathDialogLayout.addWidget(self.simPathEdit,5)
        self.simPathButton = QPushButton('...')
        self.simPathButton.clicked.connect(self.onSimPathButtonClicked)
        simPathDialogLayout.addWidget(self.simPathButton,1)
        filePathsLayout.addLayout(simPathDialogLayout)
        filePathsGroup.setLayout(filePathsLayout)
        mainLayout.addWidget(filePathsGroup)
        switchViewsGroup = QGroupBox('Switch and Stop Views')
        switchViewsLayout = QFormLayout()
        self.switchViewsEdit = edf.longLineEdit()
        switchViewsLayout.addRow(edf.boldLabel('Switch Views:'), self.switchViewsEdit)
        self.stopViewsEdit = edf.longLineEdit()
        switchViewsLayout.addRow(edf.boldLabel('Stop Views:'), self.stopViewsEdit)
        switchViewsGroup.setLayout(switchViewsLayout)
        mainLayout.addWidget(switchViewsGroup)
        mainLayout.addSpacing(20)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)

    def onFileButtonClicked(self):
       self.editorPathEdit.setText(QFileDialog.getOpenFileName(self, caption='Select text '
                                                                    'editor path.')[0])

    def onSimPathButtonClicked(self):
        self.simPathEdit.setText(QFileDialog.getExistingDirectory(self, caption =
        'Simulation path:'))

class libraryPathsModel(QStandardItemModel):
    def __init__(self, libraryDict):
        super().__init__()
        self.libraryDict = libraryDict
        self.setHorizontalHeaderLabels(['Library Name', 'Library Path'])
        for key, value in self.libraryDict.items():
            libName = QStandardItem(key)
            libPath = QStandardItem(str(value))
            self.appendRow([libName, libPath])
        self.appendRow([QStandardItem('Right click here...'), QStandardItem('')])


class libraryPathsTableView(QTableView):
    def __init__(self, model,logger):
        super().__init__()
        self.model = model
        self.logger = logger
        self.setModel(self.model)
        self.setShowGrid(True)
        self.setColumnWidth(0,200)
        self.setColumnWidth(1,400)
        self.fileDialog = QFileDialog()
        self.fileDialog.setFileMode(QFileDialog.Directory)
        self.libNameEditList = list()
        self.libPathEditList = list()
        for row in range(self.model.rowCount()):
            self.libPathEditList.append(edf.longLineEdit())
            self.setIndexWidget(self.model.index(row,1),self.libPathEditList[-1])
            self.libPathEditList[-1].setText(self.model.item(row,1).text())


    def contextMenuEvent(self, event) -> None:
        self.menu = QMenu(self)
        try:
            selectedIndex = self.selectedIndexes()[0]
        except IndexError:
            self.model.appendRow([QStandardItem('Click here...'), QStandardItem('')])
            selectedIndex = self.model.index(0,0)
        removePathAction = self.menu.addAction('Remove Path')
        removePathAction.triggered.connect(lambda : self.removeLibraryPath(selectedIndex))
        addPathAction = self.menu.addAction('Add Library Path')
        addPathAction.triggered.connect(lambda : self.addLibraryPath(selectedIndex))
        self.menu.exec(event.globalPos())

    def removeLibraryPath(self,index):
        self.model.takeRow(index.row())
        self.logger.info('Removed Library Path.')

    def addLibraryPath(self,index):
        row = index.row()
        self.selectRow(row)
        self.fileDialog.exec()
        if self.fileDialog.selectedFiles():
            self.selectedDirectory = QDir(self.fileDialog.selectedFiles()[0])
        self.model.insertRow(row,[QStandardItem(self.selectedDirectory.dirName()),
                                  QStandardItem(self.selectedDirectory.absolutePath())])


class libraryPathEditorDialog(QDialog):
    def __init__(self, parent, libraryDict: dict):
        super().__init__(parent)
        self.parent = parent
        self.logger = self.parent.logger
        self.libraryDict = libraryDict
        self.setWindowTitle('Library Paths Dialogue')
        self.setMinimumSize(700,300)
        self.mainLayout = QVBoxLayout()
        self.pathsBox = QGroupBox()
        self.boxLayout = QVBoxLayout()
        self.pathsBox.setLayout(self.boxLayout)
        self.pathsModel = libraryPathsModel(self.libraryDict)
        self.tableView = libraryPathsTableView(self.pathsModel,self.logger)
        self.boxLayout.addWidget(self.tableView)
        self.mainLayout.addWidget(self.pathsBox)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)