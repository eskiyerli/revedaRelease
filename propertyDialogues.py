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
    QRadioButton,
    QGridLayout,
    QCheckBox,
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
        self.rectLeftLine.setText(
            str(self.rectItem.start.toTuple()[0] + self.location[0])
        )
        self.fLayout.addRow(QLabel("X Origin:"), self.rectLeftLine)
        self.rectTopLine = QLineEdit()
        self.rectTopLine.setText(
            str(self.rectItem.start.toTuple()[1] + self.location[1])
        )
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
        self.startXLine.setText(
            str(self.lineItem.start.toTuple()[0] + self.location[0])
        )
        self.fLayout.addRow(QLabel("Start (X):"), self.startXLine)
        self.startYLine = QLineEdit()
        self.startYLine.setText(
            str(self.lineItem.start.toTuple()[1] + self.location[1])
        )
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
        self.pinDir.addItems(shp.pin.pinDirs)
        self.pinDir.setToolTip("Select pin direction")
        self.fLayout.addRow(QLabel("Pin Direction"), self.pinDir)
        self.pinType = QComboBox()
        self.pinType.addItems(shp.pin.pinTypes)
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
        self.pinXLine.setText(str(self.pinItem.start.x() + self.location[0]))
        self.pinXLine.setToolTip("X Coordinate")
        self.fLayout.addRow(QLabel("X:"), self.pinXLine)
        self.pinYLine = QLineEdit()
        self.pinYLine.setText(str(self.pinItem.start.y() + self.location[1]))
        self.pinYLine.setToolTip("Y Coordinate")
        self.fLayout.addRow(QLabel("Y:"), self.pinYLine)


class createSymbolLabelDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Label")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        self.fLayout = QFormLayout()
        self.labelNameEdit = QLineEdit()
        self.labelNameEdit.setPlaceholderText("Label Definition")
        self.labelNameEdit.setToolTip("Enter label Definition")
        self.fLayout.addRow(QLabel("Label Definition"), self.labelNameEdit)
        self.labelHeightEdit = QLineEdit()
        self.labelHeightEdit.setPlaceholderText("Label Height")
        self.labelHeightEdit.setToolTip("Enter label Height")
        self.fLayout.addRow(QLabel("Label Height"), self.labelHeightEdit)
        self.labelAlignCombo = QComboBox()
        self.labelAlignCombo.addItems(shp.label.labelAlignments)
        self.fLayout.addRow(QLabel("Label Alignment"), self.labelAlignCombo)
        self.labelOrientCombo = QComboBox()
        self.labelOrientCombo.addItems(shp.label.labelOrients)
        self.fLayout.addRow(QLabel("Label Orientation"), self.labelOrientCombo)
        self.labelUseCombo = QComboBox()
        self.labelUseCombo.addItems(shp.label.labelUses)
        self.fLayout.addRow(QLabel("Label Use"), self.labelUseCombo)
        self.mainLayout.addLayout(self.fLayout)
        self.labelTypeGroup = QGroupBox("Label Type")
        self.labelTypeLayout = QHBoxLayout()
        self.normalType = QRadioButton(shp.label.labelTypes[0])
        self.normalType.setChecked(True)
        self.NLPType = QRadioButton(shp.label.labelTypes[1])
        self.pyLType = QRadioButton(shp.label.labelTypes[2])
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
        self.labelNameEdit.setText(str(labelItem.labelName))
        self.labelHeightEdit.setText(str(labelItem.labelHeight))
        self.labelAlignCombo.setCurrentText(labelItem.labelAlign)
        self.labelOrientCombo.setCurrentText(labelItem.labelOrient)
        self.labelUseCombo.setCurrentText(labelItem.labelUse)
        if self.labelItem.labelType == "Normal":
            self.normalType.setChecked(True)
        elif self.labelItem.labelType == "NLPLabel":
            self.NLPType.setChecked(True)
        elif self.labelItem.labelType == "PyLabel":
            self.pyLType.setChecked(True)
        self.labelXLine = QLineEdit()
        self.labelXLine.setText(str(self.labelItem.start.x() + self.location[0]))
        self.labelXLine.setToolTip("X Coordinate")
        self.fLayout.addRow(QLabel("X:"), self.labelXLine)
        self.labelYLine = QLineEdit()
        self.labelYLine.setText(str(self.labelItem.start.y() + self.location[1]))
        self.labelYLine.setToolTip("Y Coordinate")
        self.fLayout.addRow(QLabel("Y:"), self.labelYLine)


class symbolLabelsDialogue(QDialog):
    """
    Dialog for changing symbol labels and attributes. Symbol properties... menu item.
    """

    def __init__(self, parent, items: list, attributes: list):
        super().__init__(parent)
        self.parent = parent
        self.items = items
        self.attributes = attributes
        self.setWindowTitle("Symbol Labels")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.mainLayout = QVBoxLayout()
        self.symbolPropsLayout = QGridLayout()
        self.symbolLabelsLayout = QGridLayout()
        self.symbolAttrsMethod()
        # Symbol Labels Layout
        self.symbolLabelsMethod()
        labelsGroup = QGroupBox("Symbol Labels")
        labelsGroup.setLayout(self.symbolLabelsLayout)
        self.mainLayout.addWidget(labelsGroup)
        self.mainLayout.addStretch(1)
        # self.mainLayout.addLayout(self.symbolLabelsLayout)
        propsGroup = QGroupBox("Symbol Properties")
        propsGroup.setLayout(self.symbolPropsLayout)
        self.mainLayout.addWidget(propsGroup)
        self.mainLayout.addStretch(1)
        # self.mainLayout.addLayout(self.symbolPropsLayout)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def symbolAttrsMethod(self):
        self.attributeNameList = []
        self.attributeTypeList = []
        self.attributeDefList = []
        # Symbol Properties
        self.symbolPropsLayout.addWidget(QLabel("Attribute Name"), 0, 0)
        self.symbolPropsLayout.addWidget(QLabel("Type"), 0, 1)
        self.symbolPropsLayout.addWidget(QLabel("Definition"), 0, 2)
        i = 0
        for item in self.attributes:
            # print(f'item is :{item}')
            self.attributeNameList.append(longLineEdit())
            self.attributeNameList[i].setText(item.name)
            self.symbolPropsLayout.addWidget(self.attributeNameList[i], i + 1, 0)
            attrTypeCombo = QComboBox()
            attrTypeCombo.addItems(shp.label.labelTypes)
            self.attributeTypeList.append(attrTypeCombo)
            self.attributeTypeList[i].setCurrentText(item.type)
            self.symbolPropsLayout.addWidget(self.attributeTypeList[i], i + 1, 1)
            self.attributeDefList.append(longLineEdit())
            self.attributeDefList[i].setText(item.definition)
            self.symbolPropsLayout.addWidget(self.attributeDefList[i], i + 1, 2)
            i += 1

        self.attributeNameList.append(longLineEdit())
        attrTypeCombo = QComboBox()
        attrTypeCombo.addItems(shp.label.labelTypes)
        self.attributeTypeList.append(attrTypeCombo)
        self.attributeDefList.append(longLineEdit())
        self.symbolPropsLayout.addWidget(self.attributeNameList[-1], i+2, 0)
        self.symbolPropsLayout.addWidget(self.attributeTypeList[-1], i+2, 1)
        self.symbolPropsLayout.addWidget(self.attributeDefList[-1], i+2, 2)
        self.attributeNameList[-1].setPlaceholderText("Enter Attribute Name")
        self.attributeTypeList[-1].setToolTip("Enter Attribute Type")
        self.attributeDefList[-1].setToolTip("Enter Attribute Definition")
        self.attributeDefList[-1].editingFinished.connect(
            lambda: self.updateAttributeDef(i+1)
        )

    def updateAttributeDef(self, i):
        i += 1
        self.attributeNameList.append(longLineEdit())
        attrTypeCombo = QComboBox()
        attrTypeCombo.addItems(shp.label.labelTypes)
        self.attributeTypeList.append(attrTypeCombo)
        self.attributeDefList.append(longLineEdit())
        self.symbolPropsLayout.addWidget(self.attributeNameList[-1], i + 1, 0)
        self.symbolPropsLayout.addWidget(self.attributeTypeList[-1], i + 1, 1)
        self.symbolPropsLayout.addWidget(self.attributeDefList[-1], i + 1, 2)
        self.attributeNameList[-1].setPlaceholderText("Enter Attribute Name")
        self.attributeTypeList[-1].setToolTip("Enter Attribute Type")
        self.attributeDefList[-1].setToolTip("Enter Attribute Definition")
        self.attributeDefList[-1].editingFinished.connect(
            lambda: self.updateAttributeDef(i)
        )

    def symbolLabelsMethod(self):
        self.labelNameList = []
        self.labelHeightList = []
        self.labelAlignmentList = []
        self.labelOrientationList = []
        self.labelUseList = []
        self.labelTypeList = []
        self.labelItemList = []
        i = 0
        self.symbolLabelsLayout.addWidget(QLabel("Definition"), 0, 0)
        self.symbolLabelsLayout.addWidget(QLabel("Height"), 0, 1)
        self.symbolLabelsLayout.addWidget(QLabel("Alignment"), 0, 2)
        self.symbolLabelsLayout.addWidget(QLabel("Orientation"), 0, 3)
        self.symbolLabelsLayout.addWidget(QLabel("Use"), 0, 4)
        self.symbolLabelsLayout.addWidget(QLabel("Type"), 0, 5)
        for item in self.items:
            if type(item) == shp.label:
                i += 1
                self.labelItemList.append(item)
                self.labelNameList.append(longLineEdit())
                self.labelNameList[-1].setText(item.labelName)
                self.labelNameList[-1].setReadOnly(True)
                self.symbolLabelsLayout.addWidget(self.labelNameList[i - 1], i, 0)
                self.labelHeightList.append(shortLineEdit())
                self.labelHeightList[-1].setText(str(item.labelHeight))
                self.symbolLabelsLayout.addWidget(self.labelHeightList[i - 1], i, 1)
                self.labelAlignmentList.append(QComboBox())
                self.labelAlignmentList[-1].addItems(shp.label.labelAlignments)
                self.labelAlignmentList[-1].setCurrentText(item.labelAlign)
                self.symbolLabelsLayout.addWidget(self.labelAlignmentList[-1], i, 2)
                self.labelOrientationList.append(QComboBox())
                self.labelOrientationList[-1].addItems(shp.label.labelOrients)
                self.labelOrientationList[-1].setCurrentText(item.labelOrient)
                self.symbolLabelsLayout.addWidget(self.labelOrientationList[-1], i, 3)
                self.labelUseList.append(QComboBox())
                self.labelUseList[-1].addItems(shp.label.labelUses)
                self.labelUseList[-1].setCurrentText(item.labelUse)
                self.symbolLabelsLayout.addWidget(self.labelUseList[-1], i, 4)
                self.labelTypeList.append(QComboBox())
                self.labelTypeList[-1].addItems(shp.label.labelTypes)
                self.labelTypeList[-1].setCurrentText(item.labelType)
                self.symbolLabelsLayout.addWidget(self.labelTypeList[-1], i, 5)
        if i == 0:  # no labels to edit
            self.symbolLabelsLayout.addWidget(QLabel("No symbol labels found."), 1, 0)


class shortLineEdit(QLineEdit):
    def __init__(self):
        super().__init__(None)
        self.setMaximumWidth(50)


class longLineEdit(QLineEdit):
    def __init__(self):
        super().__init__(None)
        self.setMaximumWidth(250)
