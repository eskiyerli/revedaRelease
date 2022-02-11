# properties dialogues for various symbol items
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QDialogButtonBox,
    QLineEdit,
    QLabel,
    QComboBox,
    QGroupBox,
    QRadioButton
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


class createPinDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Pin")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        self.fLayout = QFormLayout()
        self.pinName = QLineEdit()
        self.pinName.setPlaceholderText("Pin Name")
        self.pinName.setToolTip("Enter pin name")
        self.fLayout.addRow(QLabel("Pin Name"), self.pinName)
        self.pinDir = QComboBox()
        self.pinDir.addItems(shp.pin().pinDirs)
        self.pinDir.setToolTip("Select pin direction")
        self.fLayout.addRow(QLabel("Pin Direction"), self.pinDir)
        self.pinType = QComboBox()
        self.pinType.addItems(
            shp.pin().pinTypes
        )
        self.pinType.setToolTip("Select pin type")
        self.fLayout.addRow(QLabel("Pin Type"), self.pinType)
        self.mainLayout.addLayout(self.fLayout)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()


class pinPropertyDialog(createPinDialog):
    def __init__(self, parent, pinItem: shp.pin):
        super().__init__(parent)
        self.parent = parent
        self.pinItem = pinItem
        self.location = self.pinItem.scenePos().toTuple()

        self.setWindowTitle("Pin Properties")
        self.pinName.setText(str(pinItem.pinName))
        self.pinType.setCurrentText(pinItem.pinType)
        self.pinDir.setCurrentText(pinItem.pinDir)
        self.pinXLine = QLineEdit()
        self.pinXLine.setText(str(self.pinItem.start.x()+self.location[0]))
        self.pinXLine.setToolTip("X Coordinate")
        self.fLayout.addRow(QLabel("X:"), self.pinXLine)
        self.pinYLine = QLineEdit()
        self.pinYLine.setText(str(self.pinItem.start.y()+self.location[1]))
        self.pinYLine.setToolTip("Y Coordinate")
        self.fLayout.addRow(QLabel("Y:"), self.pinYLine)


class createSymbolLabelDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Label")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        self.fLayout = QFormLayout()
        self.labelName = QLineEdit()
        self.labelName.setPlaceholderText("Label Name")
        self.labelName.setToolTip("Enter label name")
        self.fLayout.addRow(QLabel("Label Name"), self.labelName)
        self.labelHeight = QLineEdit()
        self.labelHeight.setPlaceholderText("Label Height")
        self.labelHeight.setToolTip("Enter label Height")
        self.fLayout.addRow(QLabel("Label Height"), self.labelHeight)
        self.labelAlignment = QComboBox()
        self.labelAlignment.addItems(shp.label().labelAlignments)
        self.fLayout.addRow(QLabel("Label Alignment"), self.labelAlignment)
        self.labelOrientation = QComboBox()
        self.labelOrientation.addItems(
            shp.label().labelOrientations
        )
        self.fLayout.addRow(QLabel("Label Orientation"), self.labelOrientation)
        self.labelUse = QComboBox()
        self.labelUse.addItems(shp.label().labelUses)
        self.fLayout.addRow(QLabel("Label Use"), self.labelUse)
        self.mainLayout.addLayout(self.fLayout)
        self.labelTypeGroup = QGroupBox("Label Type")
        self.labelTypeLayout = QHBoxLayout()
        self.normalType = QRadioButton(shp.label().labelTypes[0])
        self.normalType.setChecked(True)
        self.NLPType = QRadioButton(shp.label().labelTypes[1])
        self.pyLType = QRadioButton(shp.label().labelTypes[2])
        self.labelTypeLayout.addWidget(self.normalType)
        self.labelTypeLayout.addWidget(self.NLPType)
        self.labelTypeLayout.addWidget(self.pyLType)
        self.labelTypeGroup.setLayout(self.labelTypeLayout)
        self.mainLayout.addWidget(self.labelTypeGroup)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()


class labelPropertyDialog(createSymbolLabelDialog):
    def __init__(self, parent, labelItem: shp.label):
        super().__init__(parent)
        self.parent = parent
        self.labelItem = labelItem
        self.location = self.labelItem.scenePos().toTuple()

        self.setWindowTitle("Label Properties")
        self.labelName.setText(str(labelItem.labelName))
        self.labelHeight.setText(str(labelItem.labelHeight))
        self.labelAlignment.setCurrentText(labelItem.labelAlignment)
        self.labelOrientation.setCurrentText(labelItem.labelOrient)
        self.labelUse.setCurrentText(labelItem.labelUse)
        if labelItem.labelType == "Normal":
            self.normalType.setChecked(True)
        elif labelItem.labelType == "NLPLabel":
            self.NLPType.setChecked(True)
        elif labelItem.labelType == "PyLabel":
            self.pyLType.setChecked(True)