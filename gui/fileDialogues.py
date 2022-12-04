import pathlib

from PySide6.QtCore import (Qt)
from PySide6.QtGui import (QStandardItemModel)
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                               QFormLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout,
                               QPushButton)

import backend.schBackEnd as scb
import common.shape as shp
import gui.editFunctions as edf


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
        self.selectedLibPath = self.libNamesCB.itemData(0, Qt.UserRole + 2)
        self.libNamesCB.currentTextChanged.connect(self.selectLibrary)
        self.layout.addRow(edf.boldLabel("Library:"), self.libNamesCB)
        self.cellCB = QComboBox()
        libItem = self.getLibItem(self.model, self.libNamesCB.currentText())
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
        libItem = self.getLibItem(self.model, self.libNamesCB.currentText())
        cellList = [libItem.child(i).cellName for i in range(libItem.rowCount())]
        self.cellCB.clear()
        self.cellCB.addItems(cellList)

    @staticmethod
    def getLibItem(libraryModel: QStandardItemModel, libName: str) -> scb.libraryItem:
        libItem = [item for item in libraryModel.findItems(libName) if
                   item.data(Qt.UserRole + 1) == 'library'][0]
        return libItem

    @staticmethod
    def getCellItem(libItem: scb.libraryItem, cellNameInp: str) -> scb.cellItem:
        cellItem = [libItem.child(i) for i in range(libItem.rowCount()) if
                    libItem.child(i).cellName == cellNameInp][0]
        return cellItem

    @staticmethod
    def getViewItem(cellItem: scb.cellItem, viewNameInp: str) -> scb.viewItem:
        viewItem = [cellItem.child(i) for i in range(cellItem.rowCount()) if
                    cellItem.child(i).viewName == viewNameInp][0]
        return viewItem


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
        self.viewType.addItems(self.parent.cellViews)
        self.layout.addRow(edf.boldLabel("View Type:"), self.viewType)
        self.viewName = edf.longLineEdit()
        self.layout.addRow(edf.boldLabel('View Name:'), self.viewName)
        self.layout.setSpacing(10)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class selectCellViewDialog(deleteCellDialog):
    def __init__(self, parent, model):
        super().__init__(parent=parent, model=model)
        libItem = self.getLibItem(self.model, self.libNamesCB.currentText())
        self.setWindowTitle("Select CellView")
        self.cellCB.currentTextChanged.connect(self.cellNameChanged)
        self.viewCB = QComboBox()
        cellItem = self.getCellItem(libItem, self.cellCB.currentText())
        self.viewCB.addItems([cellItem.child(i).text() for i in range(
            cellItem.rowCount())])
        self.viewCB.setCurrentIndex(0)
        self.layout.addRow(edf.boldLabel('View Name:'), self.viewCB)
        self.layout.setSpacing(10)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def cellNameChanged(self):
        libItem = self.getLibItem(self.model, self.libNamesCB.currentText())
        cellItem = self.getCellItem(libItem, self.cellCB.currentText())
        viewList = [cellItem.child(i).text() for i in range(cellItem.rowCount())]
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


class copyViewDialog(newCellViewDialog):
    def __init__(self, parent, model):
        super().__init__(parent=parent, model=model)
        self.cellComboBox.setEditable(True)
        self.cellComboBox.InsertPolicy = QComboBox.InsertAfterCurrent
        self.viewComboBox.setEditable(True)
        self.viewComboBox.InsertPolicy = QComboBox.InsertAfterCurrent


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
        formLayout.addRow(QLabel('Select Library', self), self.libNamesCB)
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

        layout = QVBoxLayout()
        formLayout = QFormLayout()
        self.newLibraryName = edf.longLineEdit()
        formLayout.addRow(edf.boldLabel('New Library Name:', self), self.newLibraryName)
        layout.addLayout(formLayout)
        layout.addSpacing(40)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)


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
    def __init__(self, *args):
        super().__init__(*args)
        self.setWindowTitle(f'Export Netlist?')
        self.setMinimumSize(500, 100)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.mainLayout = QVBoxLayout()
        fileDialogLayout = QHBoxLayout()
        fileDialogLayout.addWidget(edf.boldLabel('Export Directory:'))
        self.netlistDirEdit = edf.longLineEdit()
        fileDialogLayout.addWidget(self.netlistDirEdit)
        self.netListDirButton = QPushButton('...')
        self.netListDirButton.clicked.connect(self.onDirButtonClicked)
        fileDialogLayout.addWidget(self.netListDirButton)

        self.mainLayout.addLayout(fileDialogLayout)
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


class importCellDialogue(QDialog):
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
        initialCellNames = [self._model.item(0).child(i).cellName for i in range(
            self._model.item(0).rowCount())]
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
                        range(
                            self._model.item(selectedLibItemRow).rowCount())]
        self.cellNamesCB.clear()
        self.cellNamesCB.addItems(libCellNames)

    def onFileButtonClicked(self):
        self.vaFileName = QFileDialog.getOpenFileName(self, caption='Select Verilog-A '
                                                                    'file.')[0]
        if self.vaFileName:
            self.vaFileEdit.setText(self.vaFileName)


class appProperties(QDialog):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setMinimumSize(500, 200)
        self.setWindowTitle('Revolution EDA Options')
        mainLayout = QVBoxLayout()
        fileDialogLayout = QHBoxLayout()
        fileDialogLayout.addWidget(edf.boldLabel('Select Editor Path:'), 1)
        self.editorPathEdit = edf.longLineEdit()
        fileDialogLayout.addWidget(self.editorPathEdit, 4)
        self.editFileButton = QPushButton('...')
        self.editFileButton.clicked.connect(self.onFileButtonClicked)
        fileDialogLayout.addWidget(self.editFileButton, 1)
        mainLayout.addLayout(fileDialogLayout)
        mainLayout.addSpacing(20)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)

    def onFileButtonClicked(self):
        self.editorPath = QFileDialog.getOpenFileName(self, caption='Select a text '
                                                                    'editor.')[0]
        if self.editorPath:
            self.editorPathEdit.setText(self.editorPath)
