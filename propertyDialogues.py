# properties dialogues for various symbol items
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QDialogButtonBox,
    QLineEdit,
    QLabel,
    QComboBox,
)

import shape as shp

class rectPropertyDialog(QDialog):
    def __init__(self, parent, rectItem: shp.rectangle):
        super().__init__(parent)
        self.parent = parent
        self.rectItem = rectItem
        self.location = self.rectItem.scenePos().toTuple()
        self.coords = self.rectItem.rect.getRect()

        self.setWindowTitle("Rectangle Properties")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        self.fLayout = QFormLayout()
        self.fLayout.setContentsMargins(10, 10, 10, 10)
        self.rectWidthLine = QLineEdit()
        self.rectWidthLine.setText(str(self.coords[2]))
        self.fLayout.addRow(QLabel("Width:"), self.rectWidthLine)
        self.rectHeightLine = QLineEdit()
        self.rectHeightLine.setText(str(self.coords[3]))
        self.fLayout.addRow(QLabel("Height:"), self.rectHeightLine)
        self.rectLeftLine = QLineEdit()
        self.rectLeftLine.setText(str(self.rectItem.start.toTuple()[0] + self.location[0]))
        self.fLayout.addRow(QLabel("X Origin:"), self.rectLeftLine)
        self.rectTopLine = QLineEdit()
        self.rectTopLine.setText(str(self.rectItem.start.toTuple()[1] + self.location[1]))
        self.fLayout.addRow(QLabel("Y Origin:"), self.rectTopLine)
        self.mainLayout.addLayout(self.fLayout)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()


class linePropertyDialog(QDialog):
    def __init__(self, parent, lineItem: shp.line):
        super().__init__(parent)
        self.parent = parent
        self.lineItem = lineItem
        self.location = self.lineItem.scenePos().toTuple()

        self.setWindowTitle("Line Properties")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        self.fLayout = QFormLayout()
        self.fLayout.setContentsMargins(10, 10, 10, 10)
        self.startXLine = QLineEdit()
        self.startXLine.setText(str(self.lineItem.start.toTuple()[0] + self.location[0]))
        self.fLayout.addRow(QLabel("Start (X):"), self.startXLine)
        self.startYLine = QLineEdit()
        self.startYLine.setText(str(self.lineItem.start.toTuple()[1] + self.location[1]))
        self.fLayout.addRow(QLabel("Start (Y):"), self.startYLine)
        self.endXLine = QLineEdit()
        self.endXLine.setText(str(self.lineItem.end.toTuple()[0] + self.location[0]))
        self.fLayout.addRow(QLabel("End (X):"), self.endXLine)
        self.endYLine = QLineEdit()
        self.endYLine.setText(str(self.lineItem.end.toTuple()[1] + self.location[1]))
        self.fLayout.addRow(QLabel("End (Y):"), self.endYLine)
        self.mainLayout.addLayout(self.fLayout)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()

class pinPropertyDialog(QDialog):
    def __init__(self, parent, pinItem: shp.pin):
        super().__init__(parent)
        self.parent = parent
        self.pinItem = pinItem
        self.location = self.pinItem.scenePos().toTuple()

        self.setWindowTitle("Pin Properties")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        self.fLayout = QFormLayout()
        self.fLayout.setContentsMargins(10, 10, 10, 10)
        self.pinNameLine = QLineEdit()
        self.pinNameLine.setText(str(pinItem.pinName))
        self.fLayout.addRow(QLabel("pinName:"), self.pinNameLine)
        self.pinTypeCombo = QComboBox()
        self.pinTypeCombo.addItems(["Signal", "Ground", "Power", "Clock", "Digital", "Analog"])
        self.pinTypeCombo.setCurrentText(pinItem.pinType)
        self.pinTypeCombo.setToolTip("Select Pin Type")
        self.fLayout.addRow(QLabel("pinType:"), self.pinTypeCombo)
        self.pinDirCombo = QComboBox()
        self.pinDirCombo.addItems(["Input", "Output", "Inout"])
        self.pinDirCombo.setCurrentText(pinItem.pinDir)
        self.pinDirCombo.setToolTip("Select Pin Direction")
        self.fLayout.addRow(QLabel("pinDir:"), self.pinDirCombo)
        self.pinXLine = QLineEdit()
        self.pinXLine.setText(str(self.pinItem.start.x()+self.location[0]))
        self.pinXLine.setToolTip("X Coordinate")
        self.fLayout.addRow(QLabel("X:"), self.pinXLine)
        self.pinYLine = QLineEdit()
        self.pinYLine.setText(str(self.pinItem.start.y()+self.location[1]))
        self.pinYLine.setToolTip("Y Coordinate")
        self.fLayout.addRow(QLabel("Y:"), self.pinYLine)
        self.mainLayout.addLayout(self.fLayout)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()
