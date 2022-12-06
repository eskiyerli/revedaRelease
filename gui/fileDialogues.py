
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

from PySide6.QtCore import (Qt, QSize)

from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                               QFormLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout,
                               QPushButton)
from PySide6.QtGui import (QStandardItemModel)
import common.shape as shp
import gui.editorWindows as ed
import gui.editFunctions as edf
import pathlib


class createCellDialog(QDialog):
    def __init__(self, parent, libraryDict: [str, pathlib.Path]):
        super().__init__(parent)
        self.parent = parent
        self.libraryDict = libraryDict
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Create Cell")
        layout = QFormLayout()
        self.libNamesCB = QComboBox()
        self.libNamesCB.addItems(self.libraryDict.keys())
        layout.addRow('Library Name:', self.libNamesCB)
        self.nameEdit = edf.longLineEdit()
        self.nameEdit.setPlaceholderText("Enter Cell Name")
        layout.addRow("Cell Name:", self.nameEdit)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)


class deleteCellDialog(QDialog):
    def __init__(self, parent, libModel: QStandardItemModel):
        super().__init__(parent)
        self.parent = parent
        self.libModel = libModel
        self.setWindowTitle("Select Cell")
        self.setMinimumSize(QSize(320, 180))
        mainlayout = QVBoxLayout()
        self.layout = QFormLayout()
        self.layout.setVerticalSpacing(10)
        self.libNamesCB = QComboBox()
        self.libNamesCB.setModel(self.libModel)
        self.libNamesCB.currentTextChanged.connect(self.libNameChanged)
        self.layout.addRow('Library Name:', self.libNamesCB)
        self.cellNamesCB = QComboBox()
        self.initLibItem = self.libModel.item(0)
        self.cellNames = [self.initLibItem.child(i).cellName for i in
                          range(self.initLibItem.rowCount())]
        self.cellNamesCB.addItems(self.cellNames)
        self.layout.addRow('Cell Name:', self.cellNamesCB)
        mainlayout.addLayout(self.layout)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainlayout.setSpacing(20)
        mainlayout.addWidget(self.buttonBox)
        self.setLayout(mainlayout)

    def libNameChanged(self, libName):
        self.cellNamesCB.clear()
        libItem = self.libModel.findItems(libName)[0]
        cellNames = [libItem.child(i).cellName for i in range(libItem.rowCount())]
        self.cellNamesCB.addItems(cellNames)


class selectCellViewDialog(deleteCellDialog):
    def __init__(self, parent, libModel):
        super().__init__(parent=parent, libModel=libModel)
        self.setWindowTitle("Select CellView")
        self.setMinimumSize(QSize(320, 200))
        self.viewNamesCB = QComboBox()
        initCellItem = self.initLibItem.child(0)
        initViewNames = [initCellItem.child(i).viewName for i in
                         range(initCellItem.rowCount())]
        self.viewNamesCB.addItems(initViewNames)
        self.layout.addRow('View Name:', self.viewNamesCB)
        self.cellNamesCB.currentTextChanged.connect(self.cellNameChanged)

    def cellNameChanged(self, cellItemName):
        self.viewNamesCB.clear()
        libItem = self.libModel.findItems(self.libNamesCB.currentText())[0]
        try:
            cellItem = [libItem.child(i) for i in range(libItem.rowCount()) if
                        libItem.child(i).cellName == cellItemName][0]
        except IndexError:
            cellItem = libItem.child(0)
        finally:
            viewNames = [cellItem.child(i).viewName for i in range(cellItem.rowCount()) if
                         cellItem.child(i).viewName in self.parent.cellViews]
            self.viewNamesCB.addItems(viewNames)


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


class copyViewDialog(QDialog):
    def __init__(self, parent, model, cellItem):
        super().__init__(parent=parent)
        self.parent = parent
        self.model = model
        self.cellItem = cellItem
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Copy CellView")
        layout = QFormLayout()
        layout.setSpacing(10)
        self.libraryComboBox = QComboBox()
        self.libraryComboBox.setModel(self.model)
        self.libraryComboBox.setModelColumn(0)
        self.libraryComboBox.setCurrentIndex(0)
        self.selectedLibPath = self.libraryComboBox.itemData(0, Qt.UserRole + 2)
        self.libraryComboBox.currentTextChanged.connect(self.selectLibrary)
        layout.addRow(QLabel("Library:"), self.libraryComboBox)
        self.cellComboBox = QComboBox()
        cellList = [str(cell.cellName) for cell in self.selectedLibPath.iterdir() if
                    cell.is_dir()]
        self.cellComboBox.addItems(cellList)
        self.cellComboBox.setEditable(True)
        self.cellComboBox.InsertPolicy = QComboBox.InsertAfterCurrent
        layout.addRow(QLabel("Cell Name:"), self.cellComboBox)
        self.selectedCell = self.cellComboBox.currentText()
        self.cellComboBox.currentTextChanged.connect(self.selectCell)
        self.viewComboBox = QComboBox()
        self.viewComboBox.setEditable(True)
        self.viewComboBox.InsertPolicy = QComboBox.InsertAfterCurrent
        self.viewComboBox.addItems(self.viewList())
        self.selectedView = self.viewComboBox.currentText()
        self.viewComboBox.currentTextChanged.connect(self.selectView)
        layout.addRow(QLabel("View Name:"), self.viewComboBox)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addRow(self.buttonBox)
        self.setLayout(layout)

    def viewList(self):
        viewList = [str(view.stem) for view in
                    self.selectedLibPath.joinpath(self.selectedCell).iterdir() if
                    view.suffix == ".json"]
        return viewList

    def selectLibrary(self):
        self.selectedLibPath = self.libraryComboBox.itemData(
            self.libraryComboBox.currentIndex(), Qt.UserRole + 2)
        cellList = [str(cell.cellName) for cell in self.selectedLibPath.iterdir() if
                    cell.is_dir()]
        self.cellComboBox.clear()
        self.cellComboBox.addItems(cellList)

    def selectCell(self):
        self.selectedCell = self.cellComboBox.currentText()
        self.viewComboBox.clear()
        self.viewComboBox.addItems(self.viewList())

    def selectView(self):
        self.selectedView = self.viewComboBox.currentText()


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
    def __init__(self,model,parent):
        super().__init__(parent)
        self._parent = parent
        self.setWindowTitle('Import a Verilog-a File')
        self._model = model
        self.setMinimumSize(500, 200)
        mainLayout = QVBoxLayout()
        fileDialogLayout = QHBoxLayout()
        fileDialogLayout.addWidget(edf.boldLabel('Select Verilog-A file:'),1)
        self.vaFileEdit = edf.longLineEdit()
        fileDialogLayout.addWidget(self.vaFileEdit,4)
        self.vaFileButton = QPushButton('...')
        self.vaFileButton.clicked.connect(self.onFileButtonClicked)
        fileDialogLayout.addWidget(self.vaFileButton,1)
        mainLayout.addLayout(fileDialogLayout)
        mainLayout.addSpacing(20)
        layout = QFormLayout()
        layout.setSpacing(10)
        self.libNamesCB = QComboBox()
        self.libNamesCB.setModel(self._model)
        self.libNamesCB.currentTextChanged.connect(self.changeCells)
        layout.addRow(edf.boldLabel('Library:'),self.libNamesCB)
        self.cellNamesCB = QComboBox()
        self.cellNamesCB.setEditable(True)
        initialCellNames = [self._model.item(0).child(i).cellName for i in range(
            self._model.item(0).rowCount())]
        self.cellNamesCB.addItems(initialCellNames)
        layout.addRow(edf.boldLabel('Cell:'),  self.cellNamesCB)
        self.vaViewName = edf.longLineEdit()
        layout.addRow(edf.boldLabel('Verilog-A view:'),self.vaViewName)
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
        libCellNames = [self._model.item(selectedLibItemRow).child(i).cellName for i in range(
            self._model.item(selectedLibItemRow).rowCount())]
        self.cellNamesCB.clear()
        self.cellNamesCB.addItems(libCellNames)

    def onFileButtonClicked(self):
        self.vaFileName = QFileDialog.getOpenFileName(self, caption='Select Verilog-A '
                                                                    'file.')[0]
        if self.vaFileName:
            self.vaFileEdit.setText(self.vaFileName)