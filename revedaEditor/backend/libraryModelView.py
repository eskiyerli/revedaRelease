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


import shutil

from PySide6.QtCore import (
    Qt,
)
from PySide6.QtGui import (
    QAction,
    QStandardItemModel,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QMenu,
    QMessageBox,
    QTreeView,
)


import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.schBackEnd as scb
import revedaEditor.gui.fileDialogues as fd


class designLibrariesView(QTreeView):
    def __init__(self, parent):
        super().__init__(parent=parent)  # QTreeView
        self.parent = parent
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.viewCounter = 0
        self.libBrowsW = self.parent.parent
        self.appMainW = self.libBrowsW.appMainW
        self.libraryDict = self.appMainW.libraryDict  # type: dict
        self.cellViews = self.appMainW.cellViews  # type: list
        self.openViews = self.appMainW.openViews  # type: dict
        self.logger = self.appMainW.logger
        self.selectedItem = None
        # library model is based on qstandarditemmodel
        self.libraryModel = designLibrariesModel(self.libraryDict)
        self.setSortingEnabled(True)
        self.setUniformRowHeights(True)
        self.expandAll()
        self.setModel(self.libraryModel)

    def removeLibrary(self):
        button = QMessageBox.question(
            self,
            "Library Deletion",
            "Are you sure to delete " "this library? This action cannot be undone.",
        )
        if button == QMessageBox.Yes:
            shutil.rmtree(self.selectedItem.data(Qt.UserRole + 2))
            self.libraryModel.removeRow(self.selectedItem.row())

    def renameLib(self):
        oldLibraryName = self.selectedItem.libraryName
        dlg = fd.renameLibDialog(self, oldLibraryName)
        if dlg.exec() == QDialog.Accepted:
            newLibraryName = dlg.newLibraryName.text().strip()
            libraryItem = libm.getLibItem(self.libraryModel, oldLibraryName)
            libraryItem.setText(newLibraryName)
            oldLibraryPath = libraryItem.data(Qt.UserRole + 2)
            newLibraryPath = oldLibraryPath.parent.joinpath(newLibraryName)
            oldLibraryPath.rename(newLibraryPath)

    def createCell(self):
        dlg = fd.createCellDialog(self, self.libraryModel)
        assert isinstance(self.selectedItem, scb.libraryItem)
        dlg.libNamesCB.setCurrentText(self.selectedItem.libraryName)
        if dlg.exec() == QDialog.Accepted:
            cellName = dlg.cellCB.currentText()
            if cellName.strip() != "":
                scb.createCell(self, self.libraryModel, self.selectedItem, cellName)
            else:
                self.logger.error("Please enter a cell name.")

    def copyCell(self):
        dlg = fd.copyCellDialog(self, self.libraryModel, self.selectedItem)

        if dlg.exec() == QDialog.Accepted:
            scb.copyCell(
                self, dlg.model, dlg.cellItem, dlg.copyName.text(), dlg.selectedLibPath
            )

    def renameCell(self):
        dlg = fd.renameCellDialog(self, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            scb.renameCell(self, dlg.cellItem, dlg.nameEdit.text())

    def deleteCell(self):
        try:
            shutil.rmtree(self.selectedItem.data(Qt.UserRole + 2))
            self.selectedItem.parent().removeRow(self.selectedItem.row())
        except OSError as e:
            self.logger.warning(f"Error:{e}")

    def createCellView(self):
        dlg = fd.createCellViewDialog(self, self.libraryModel, self.selectedItem)
        if dlg.exec() == QDialog.Accepted:
            viewItem = scb.createCellView(
                self.appMainW, dlg.nameEdit.text(), self.selectedItem
            )
            self.libBrowsW.createNewCellView(
                self.selectedItem.parent(), self.selectedItem, viewItem
            )

    def openView(self):
        viewItem = self.selectedItem
        cellItem = viewItem.parent()
        libItem = cellItem.parent()
        self.libBrowsW.openCellView(viewItem, cellItem, libItem)

    def copyView(self):
        dlg = fd.copyViewDialog(self, self.libraryModel)
        dlg.libNamesCB.setCurrentText(self.selectedItem.parent().parent().libraryName)
        dlg.cellCB.setCurrentText(self.selectedItem.parent().cellName)
        if dlg.exec() == QDialog.Accepted:
            if self.selectedItem.data(Qt.UserRole + 1) == "view":
                viewPath = self.selectedItem.data(Qt.UserRole + 2)
                selectedLibItem = libm.getLibItem(
                    self.libraryModel, dlg.libNamesCB.currentText()
                )
                cellName = dlg.cellCB.currentText()
                libCellNames = [
                    selectedLibItem.child(row).cellName
                    for row in range(selectedLibItem.rowCount())
                ]
                if (
                    cellName in libCellNames
                ):  # check if there is the cell in the library
                    cellItem = libm.getCellItem(
                        selectedLibItem, dlg.cellCB.currentText()
                    )
                else:
                    cellItem = scb.createCell(
                        self.libBrowsW,
                        self.libraryModel,
                        selectedLibItem,
                        dlg.cellCB.currentText(),
                    )
                cellViewNames = [
                    cellItem.child(row).viewName for row in range(cellItem.rowCount())
                ]
                newViewName = dlg.viewName.text()
                if newViewName in cellViewNames:
                    self.logger.warning(
                        "View already exists. Delete cellview and try again."
                    )
                else:
                    newViewPath = cellItem.data(Qt.UserRole + 2).joinpath(
                        f"{newViewName}.json"
                    )
                    shutil.copy(viewPath, newViewPath)
                    cellItem.appendRow(scb.viewItem(newViewPath))

    def renameView(self):
        oldViewName = self.selectedItem.viewName
        dlg = fd.renameViewDialog(self.libBrowsW, oldViewName)
        if dlg.exec() == QDialog.Accepted:
            newName = dlg.newViewNameEdit.text()
            try:
                viewPathObj = self.selectedItem.data(Qt.UserRole + 2)
                newPathObj = self.selectedItem.data(Qt.UserRole + 2).rename(
                    viewPathObj.parent.joinpath(f"{newName}.json")
                )
                self.selectedItem.parent().appendRow(scb.viewItem(newPathObj))
                self.selectedItem.parent().removeRow(self.selectedItem.row())
            except FileExistsError:
                self.logger.error("Cellview exists.")

    def deleteView(self):
        try:
            self.selectedItem.data(Qt.UserRole + 2).unlink()
            itemRow = self.selectedItem.row()
            parent = self.selectedItem.parent()
            parent.removeRow(itemRow)
        except OSError as e:
            self.logger.warning(f"Error:{e.strerror}")

    def reworkDesignLibrariesView(self, libraryDict: dict):
        """
        Recreate library model from libraryDict.
        """
        self.libraryModel = designLibrariesModel(libraryDict)
        self.setModel(self.libraryModel)
        self.libBrowsW.libraryModel = self.libraryModel

    # context menu
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        try:
            index = self.selectedIndexes()[0]
        except IndexError:
            pass
        try:
            self.selectedItem = self.libraryModel.itemFromIndex(index)
            if self.selectedItem.data(Qt.UserRole + 1) == "library":
                menu.addAction("Rename Library", self.renameLib)
                menu.addAction("Remove Library", self.removeLibrary)
                menu.addAction("Create Cell", self.createCell)
            elif self.selectedItem.data(Qt.UserRole + 1) == "cell":
                menu.addAction(
                    QAction("Create CellView...", self, triggered=self.createCellView)
                )
                menu.addAction(QAction("Copy Cell...", self, triggered=self.copyCell))
                menu.addAction(
                    QAction("Rename Cell...", self, triggered=self.renameCell)
                )
                menu.addAction(
                    QAction("Delete Cell...", self, triggered=self.deleteCell)
                )
            elif self.selectedItem.data(Qt.UserRole + 1) == "view":
                menu.addAction(QAction("Open View", self, triggered=self.openView))
                menu.addAction(QAction("Copy View...", self, triggered=self.copyView))
                menu.addAction(
                    QAction("Rename View...", self, triggered=self.renameView)
                )
                menu.addAction(
                    QAction("Delete View...", self, triggered=self.deleteView)
                )
            menu.exec(event.globalPos())
        except UnboundLocalError:
            pass


class designLibrariesModel(QStandardItemModel):
    def __init__(self, libraryDict):
        self.libraryDict = libraryDict
        super().__init__()
        self.rootItem = self.invisibleRootItem()
        self.setHorizontalHeaderLabels(["Libraries"])
        self.initModel()

    def initModel(self):
        for designPath in self.libraryDict.values():
            self.populateLibrary(designPath)

    def populateLibrary(self, designPath):  # designPath: Path
        """
        Populate library view.
        """
        if designPath.joinpath("reveda.lib").exists():
            libraryItem = self.addLibraryToModel(designPath)
            cellList = [cell.name for cell in designPath.iterdir() if cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell), libraryItem)
                viewList = [
                    view.name
                    for view in designPath.joinpath(cell).iterdir()
                    if view.suffix == ".json"
                ]
                for view in viewList:
                    self.addViewToModel(designPath.joinpath(cell, view), cellItem)

    def addLibraryToModel(self, designPath):
        libraryEntry = scb.libraryItem(designPath)
        self.rootItem.appendRow(libraryEntry)
        return libraryEntry

    def addCellToModel(self, cellPath, parentItem):
        cellEntry = scb.cellItem(cellPath)
        parentItem.appendRow(cellEntry)
        return cellEntry

    def addViewToModel(self, viewPath, parentItem):
        viewEntry = scb.viewItem(viewPath)
        parentItem.appendRow(viewEntry)

class symbolViewsModel(designLibrariesModel):
    """
    Initializes the object with the given `libraryDict` and `symbolViews`.

    Parameters:
        libraryDict (dict): A dictionary containing the library information.
        symbolViews (list): A list of symbol views.

    Returns:
        None
    """

    def __init__(self, libraryDict: dict, symbolViews: list):
        self.symbolViews = symbolViews
        super().__init__(libraryDict)

    def populateLibrary(self, designPath):  # designPath: Path
        """
        Populate library view.
        """
        if designPath.joinpath("reveda.lib").exists():
            libraryItem = self.addLibraryToModel(designPath)
            cellList = [cell.name for cell in designPath.iterdir() if cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell), libraryItem)
                viewList = [
                    view.name
                    for view in designPath.joinpath(cell).iterdir()
                    if view.suffix == ".json"
                    and any(x in view.name for x in self.symbolViews)
                ]
                for view in viewList:
                    self.addViewToModel(designPath.joinpath(cell, view), cellItem)


class layoutViewsModel(designLibrariesModel):
    def __init__(self, libraryDict: dict, layoutViews: list):
        self.layoutViews = layoutViews
        super().__init__(libraryDict)

    def populateLibrary(self, designPath):  # designPath: Path
        """
        Populate library view.
        """
        if designPath.joinpath("reveda.lib").exists():
            libraryItem = self.addLibraryToModel(designPath)
            cellList = [cell.name for cell in designPath.iterdir() if cell.is_dir()]
            for cell in cellList:  # type: str
                cellItem = self.addCellToModel(designPath.joinpath(cell), libraryItem)
                viewList = [
                    view.name
                    for view in designPath.joinpath(cell).iterdir()
                    if view.suffix == ".json"
                    and any(x in view.name for x in self.layoutViews)
                ]
                for view in viewList:
                    self.addViewToModel(designPath.joinpath(cell, view), cellItem)
