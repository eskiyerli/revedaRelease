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
from PySide6.QtCore import (Qt,QRect)
from PySide6.QtGui import (QStandardItemModel, QStandardItem,QPainter)
from PySide6.QtWidgets import (QTableView, QCheckBox, QComboBox)

class outputsModel(QStandardItemModel):
    def __init__(self, outputsDict, expressionDict):
        super().__init__()
        self.outputsDict = outputsDict
        self.expressionDict = expressionDict
        self.setHorizontalHeaderLabels(["Plot", "Save", "Output", 'Analysis',
                                        "Type", "DNO"])

        if self.outputsDict!= {}:
            for output, value in self.outputsDict.items():
                item_plot = QStandardItem()
                item_plot.setCheckState(Qt.Checked if value[0] else Qt.Unchecked)
                item_save = QStandardItem()
                item_save.setCheckState(Qt.Checked if value[1] else Qt.Unchecked)
                item_output = QStandardItem(output)
                item_analysis = QStandardItem(value[2])
                item_type = QStandardItem('Signal')
                item_dno = QStandardItem()
                item_dno.setCheckState(Qt.Checked if value[3] else Qt.Unchecked)
                self.appendRow([item_plot, item_save, item_output, item_analysis,
                                item_type, item_dno])
        if self.expressionDict!={}:

            for expression, value in self.expressionDict.items():
                item_plot = QStandardItem()
                item_plot.setCheckState(Qt.Checked if value[0] else Qt.Unchecked)
                item_save = QStandardItem()
                item_save.setCheckState(Qt.Checked if value[1] else Qt.Unchecked)
                item_output = QStandardItem(expression)
                item_analysis = QStandardItem(value[2])
                item_type = QStandardItem('Expression')
                item_dno = QStandardItem()
                item_dno.setCheckState(Qt.Checked if value[3] else Qt.Unchecked)
                self.appendRow([item_plot, item_save, item_output, item_analysis,
                                item_type, item_dno])
        if self.rowCount() == 0:
            item_plot = QStandardItem()
            item_plot.setCheckable(True)
            item_save = QStandardItem()
            item_plot.setCheckable(True)
            item_output = QStandardItem('')
            item_analysis = QStandardItem('')
            item_type = QStandardItem('Signal')
            item_dno = QStandardItem()
            item_dno.setCheckable(True)
            self.appendRow([item_plot, item_save, item_output, item_analysis,
                            item_type, item_dno])



class outputsTableView(QTableView):
    def __init__(self, parent, model):
        super().__init__(parent)
        self.parent = parent
        self.model = model
        self.setModel(self.model)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableView.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        self.doubleClicked.connect(self.handleDoubleClick)
        self.setColumnWidth(0, 40)
        self.setColumnWidth(1, 40)

    def handleDoubleClick(self, index):
        print('double click')

        # self.parent.showOutputDialog(index)


