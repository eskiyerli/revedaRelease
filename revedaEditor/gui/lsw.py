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

from PySide6.QtWidgets import QTableView
from PySide6.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QBrush,
    QColor,
    QPixmap,
    QBitmap,
)
from PySide6.QtCore import Signal, Qt, QModelIndex


class layerDataModel(QStandardItemModel):
    def __init__(self, data: list):
        super().__init__()
        self._data = data or []
        self.setColumnCount(5)  # Set the number of columns

        # Set the headers for the columns
        self.setHeaderData(0, Qt.Horizontal, "")
        self.setHeaderData(1, Qt.Horizontal, "Layer")
        self.setHeaderData(2, Qt.Horizontal, "Purpose")
        self.setHeaderData(3, Qt.Horizontal, "V")
        self.setHeaderData(4, Qt.Horizontal, "S")

        for row, layer in enumerate(self._data):
            self.insertRow(row)
            bitmap = QBitmap.fromImage(QPixmap(layer.btexture).scaled(5, 5).toImage())
            brush = QBrush(bitmap)
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


class layerViewTable(QTableView):
    dataSelected = Signal(str, str)
    layerSelectable = Signal(str, str, bool)
    layerVisible = Signal(str, str, bool)

    def __init__(self, parent=None, model: layerDataModel = None):
        super().__init__(parent)
        self._model = model
        self.setModel(self._model)
        self.resizeColumnsToContents()
        self.setShowGrid(False)
        self.setMaximumWidth(280)
        self.setSelectionBehavior(QTableView.SelectRows)
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
