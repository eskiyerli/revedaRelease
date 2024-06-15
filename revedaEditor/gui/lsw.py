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
import pathlib
from pathlib import Path

from PySide6.QtCore import (Signal, Qt, QModelIndex, )
from PySide6.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QBrush,
    QColor,
    QBitmap,
    QImage,
)
from PySide6.QtWidgets import (QTableView, QMenu, QGraphicsItem,)

import os
from dotenv import load_dotenv
load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):
    import pdk.layoutLayers as laylyr
else:
    import defaultPDK.layoutLayers as laylyr


class layerDataModel(QStandardItemModel):
    def __init__(self, data: list):
        super().__init__()
        self._data = data or []
        self.setColumnCount(5)  # Set the number of columns

        # Set the headers for the columns
        self.setHeaderData(0, Qt.Horizontal, "")
        self.setHeaderData(1, Qt.Horizontal, "Layer")
        self.setHeaderData(2, Qt.Horizontal, "Purp.")
        self.setHeaderData(3, Qt.Horizontal, "V")
        self.setHeaderData(4, Qt.Horizontal, "S")

        for row, layer in enumerate(self._data):
            self.insertRow(row)
            # bitmap = QBitmap.fromImage(QPixmap(layer.btexture).scaled(5, 5).toImage())
            reveda_pdk_path = os.environ.get("REVEDA_PDK_PATH", None)
            if reveda_pdk_path is None:
                reveda_pdk_pathobj = Path(__file__).parent.parent.joinpath("defaultPDK")
            else:
                reveda_pdk_pathobj = pathlib.Path(reveda_pdk_path)
            texturePath = reveda_pdk_pathobj.joinpath(layer.btexture)
            _bitmap = QBitmap.fromImage(self.createImage(texturePath, layer.bcolor))
            # bitmap = QBitmap.fromImage(QPixmap(layer.btexture).scaled(QSize(4, 4),
            #                         Qt.KeepAspectRatio, Qt.SmoothTransformation).toImage())
            brush = QBrush(_bitmap)
            brush.setColor(QColor(layer.bcolor))
            item = QStandardItem()
            item.setForeground(QBrush(QColor(255, 255, 255)))
            item.setBackground(brush)
            self.setItem(row, 0, item)
            self.setItem(row, 1, QStandardItem(layer.name))
            self.setItem(row, 2, QStandardItem(layer.purpose))
            item = QStandardItem()
            item.setCheckable(True)
            item.setCheckState(Qt.Checked if layer.selectable else Qt.Unchecked)
            self.setItem(row, 3, item)
            item = QStandardItem()
            item.setCheckable(True)
            item.setCheckState(Qt.Checked if layer.visible else Qt.Unchecked)
            self.setItem(row, 4, item)

    def createData(self, layerlist: list) -> list:
        [
            self._data.append(
                (
                    layer.name,
                    layer.visible,
                    layer.selectable,
                    layer.btexture,
                    layer.bcolor,
                )
            )
            for layer in layerlist
        ]

    @staticmethod
    def createImage(filePath:Path, color: QColor):
        # Read the file and split lines
        with filePath.open('r') as file:
            lines = file.readlines()

        height = len(lines)
        width = len(lines[0].split())

        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(QColor(0, 0, 0, 0))

        for y, line in enumerate(lines):
            for x, value in enumerate(line.split()):
                if int(value) == 1:
                    image.setPixelColor(x, y, color)  #
                else:
                    image.setPixelColor(x, y, QColor(0, 0, 0, 0))  # Transparent for 0

        return image

class layerViewTable(QTableView):
    dataSelected = Signal(str, str)
    layerSelectable = Signal(str, str, bool)
    layerVisible = Signal(str, str, bool)

    def __init__(self, parent=None, model: layerDataModel = None):
        super().__init__(parent)
        self._model = model
        self.parent = parent
        self.layoutScene = self.parent.scene
        self.setModel(self._model)
        self.selectedRow: int = -1
        self.resizeColumnsToContents()
        self.setShowGrid(False)
        # self.setMaximumWidth(400)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.verticalHeader().setVisible(False)
        selection_model = self.selectionModel()
        selection_model.selectionChanged.connect(self.onSelectionChanged)
        self._model.dataChanged.connect(self.onDataChanged)

    def onSelectionChanged(self, selected, deselected):
        if selected.indexes():
            # Get the first selected index
            layerNameIndex = selected.indexes()[1]
            layerPurposeIndex = selected.indexes()[2]
            # Get the row and column of the selected index
            # Get the data from the model at the selected index
            layerName = self._model.data(layerNameIndex)
            layerPurpose = self._model.data(layerPurposeIndex)
            self.dataSelected.emit(layerName, layerPurpose)

    def onDataChanged(
        self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: list
    ):
        # Check if the changed data involves the check state
        if Qt.CheckStateRole in roles:
            row = topLeft.row()
            column = topLeft.column()
            item = self._model.item(row, column)
            # if item and item.isCheckable():
            if column == 4:
                if item.checkState() == Qt.Checked:
                    self.layerSelectable.emit(
                        self._model.item(row, 1).text(),
                        self._model.item(row, 2).text(),
                        True,
                    )
                else:
                    self.layerSelectable.emit(
                        self._model.item(row, 1).text(),
                        self._model.item(row, 2).text(),
                        False,
                    )
            elif column == 3:
                if item.checkState() == Qt.Checked:
                    self.layerVisible.emit(
                        self._model.item(row, 1).text(),
                        self._model.item(row, 2).text(),
                        True,
                    )
                else:
                    self.layerVisible.emit(
                        self._model.item(row, 1).text(),
                        self._model.item(row, 2).text(),
                        False,
                    )

    def noLayersVisible(self):
        for layer in laylyr.pdkAllLayers:
            layer.visible = False
        for row in range(self._model.rowCount()):
            self._model.item(row, 3).setCheckState(Qt.Unchecked)

    def allLayersVisible(self):
        for layer in laylyr.pdkAllLayers:
            layer.visible = True
        for row in range(self._model.rowCount()):
            self._model.item(row, 3).setCheckState(Qt.Checked)

    def noLayersSelectable(self):
        for layer in laylyr.pdkAllLayers:
            layer.selectable = False
        for row in range(self._model.rowCount()):
            self._model.item(row, 4).setCheckState(Qt.Unchecked)
        for item in self.layoutScene.items():
            if hasattr(item, 'layer') and item.parentItem() is None:
                item.setEnabled(False)

    def allLayersSelectable(self):
        for layer in laylyr.pdkAllLayers:
            layer.selectable = True
        for row in range(self._model.rowCount()):
            self._model.item(row, 4).setCheckState(Qt.Checked)
            for item in self.layoutScene.items():
                if item.parentItem() is None and hasattr(item, 'layer'):
                    item.setEnabled(True)