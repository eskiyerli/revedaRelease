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

class variablesModel(QStandardItemModel):
    def __init__(self, variablesDict):
        super().__init__()
        self.variablesDict = variablesDict
        self.setHorizontalHeaderLabels(["Variable Name", 'Value'])
        if self.variablesDict is not {}:
            for variable, value in self.variablesDict.items():
                item_name = QStandardItem(variable)
                item_value = QStandardItem(str(value))
                self.appendRow([item_name, item_value])
        else:
            self.appendRow([QStandardItem(''), QStandardItem('')])
class variablesTableView(QTableView):
    def __init__(self,parent, model):
        super().__init__(parent)
        self.parent = parent
        self.model = model
        self.setModel(self.model)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        # self.setEditTriggers(QTableView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)