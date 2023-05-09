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
from PySide6.QtCore import (Qt,)
from PySide6.QtGui import (QStandardItemModel, QStandardItem,)
from PySide6.QtWidgets import (QTableView, QStyledItemDelegate, QCheckBox)
class analysesModel(QStandardItemModel):
    def __init__(self,analysisDict:dict):
        super().__init__()
        self.analysisDict = analysisDict
        self.setHorizontalHeaderLabels(["Analysis", 'Arguments'])


        for analysis, attributes in self.analysisDict.items():
            item_selected = QStandardItem(analysis)
            item_selected.setCheckable(True)
            attributeText = (',').join(map(str, list(attributes.values())))
            item_attribute = QStandardItem(attributeText)
            self.appendRow([item_selected, item_attribute])

class CheckBoxDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # option.text = ""
        option.decorationAlignment = Qt.AlignLeft
        option.textAlignment = Qt.AlignCenter
        option.displayAlignment = Qt.AlignCenter
class analysisTableView(QTableView):
    def __init__(self, parent, model):
        super().__init__(parent=parent)
        self.parent = parent
        self.model = model
        self.setModel(self.model)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        # self.setEditTriggers(QTableView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)
        delegate0 = CheckBoxDelegate()
        self.setItemDelegateForColumn(0,delegate0)
        self.setColumnWidth(0,80)
