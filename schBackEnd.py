# schematic editor backend
from PySide6.QtGui import (
    QAction,
    QColor,
    QIcon,
    QPalette,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
    QPen,
    QTransform,
    QCursor,
    QPainter,
    QFont,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QFileDialog,
    QComboBox,
    QFormLayout,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QRadioButton,
    QTabWidget,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
    QGraphicsLineItem,
    QGraphicsItem,
    QDialogButtonBox,
    QLabel,
    QMenu,
    QMessageBox,
)
import shutil

from PySide6.QtCore import (
    QModelIndex,
    Qt,
    QPoint,
    QLine,
    QDir,
)


def createView(parent,viewName, cellItem):
    if viewName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a view name")
    # libraryItem = self.model.findItems(
    #     cellPath.parent.name, flags=Qt.MatchExactly
    # )[0]
    cellPath = cellItem.data(Qt.UserRole+2)
    viewPath = cellPath.joinpath(viewName)
    viewPath.touch()  # create the view file
    viewItem = QStandardItem(viewName)
    viewItem.setData(viewPath, Qt.UserRole + 2)
    viewItem.setData("view", Qt.UserRole + 1)
    cellItem.appendRow(viewItem)
    # needs to decide on how to handle the view type
    print(f"Created {viewName} at {str(viewPath)}")

# function for copying a cell
def copyCell(parent,model,cellItem,copyName, selectedLibPath):
    cellPath = cellItem.data(Qt.UserRole + 2)    
    if copyName == "":
        copyName = "newCell"
    copyPath = selectedLibPath.joinpath(copyName)
    if copyPath.exists():
        QMessageBox.warning(parent, "Error", "Cell already exits.")
    else:
        assert cellPath.exists()
        shutil.copytree(cellPath, copyPath)  # copied the cell
        libraryItem = model.findItems(
            selectedLibPath.name, flags=Qt.MatchExactly
        )[
            0
        ]  # find the library item
        # create new cell item
        cellItem = QStandardItem(copyPath.name)
        cellItem.setEditable(False)
        cellItem.setData("cell", Qt.UserRole + 1)
        cellItem.setData(copyPath, Qt.UserRole + 2)
        # go through view list and add to cell item
        viewList = [
            str(view.stem)
            for view in copyPath.iterdir()
            if view.suffix == ".yaml"
        ]

        for view in viewList:
            viewItem = QStandardItem(view)
            viewItem.setData("view", Qt.UserRole + 1)
            # set the data to the item to be the path to the view.
            viewItem.setData(
                copyPath.joinpath(view).with_suffix(".yaml"),
                Qt.UserRole + 2,
            )
            viewItem.setEditable(False)
            cellItem.appendRow(viewItem)
        libraryItem.appendRow(cellItem)

def renameCell(parent,cellItem,newName):
    cellPath = cellItem.data(Qt.UserRole + 2)
    if newName.strip() == "":
        QMessageBox.warning(parent, "Error", "Please enter a cell name")
    else:
        cellPath.rename(cellPath.parent/newName)
        cellItem.setText(newName)

