#   “Commons Clause” License Condition v1.0
#  #
#   The Software is provided to you by the Licensor under the License, as defined
#   below, subject to the following condition.
#  #
#   Without limiting other conditions in the License, the grant of rights under the
#   License will not include, and the License does not grant to you, the right to
#   Sell the Software.
#  #
#   For purposes of the foregoing, “Sell” means practicing any or all of the rights
#   granted to you under the License to provide to third parties, for a fee or other
#   consideration (including without limitation fees for hosting or consulting/
#   support services related to the Software), a product or service whose value
#   derives, entirely or substantially, from the functionality of the Software. Any
#   license notice or attribution required by the License must also include this
#   Commons Clause License Condition notice.
#  #
#   Software: Revolution EDA
#   License: Mozilla Public License 2.0
#   Licensor: Revolution Semiconductor (Registered in the Netherlands)

# properties dialogues for various symbol items

import pathlib

from PySide6.QtGui import (QFontDatabase, )
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QDialogButtonBox, QLineEdit, QLabel, QComboBox,
                               QGroupBox, QRadioButton, QGridLayout, QTextEdit,
                               QMenu)

import common.net as net
import common.shape as shp
import gui.editFunctions as edf


class rectPropertyDialog(QDialog):
    '''
    Property dialog for symbol rectangles.
    '''
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
            str(self.rectItem.start.toTuple()[0] + self.location[0]))
        self.fLayout.addRow(QLabel("X Origin:"), self.rectLeftLine)
        self.rectTopLine = QLineEdit()
        self.rectTopLine.setText(
            str(self.rectItem.start.toTuple()[1] + self.location[1]))
        self.fLayout.addRow(QLabel("Y Origin:"), self.rectTopLine)
        self.mainLayout.addLayout(self.fLayout)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()


class circlePropertyDialog(QDialog):
    def __init__(self, parent, circleItem: shp.circle):
        super().__init__(parent)
        self.parent = parent
        self.circleItem = circleItem
        self.location = self.circleItem.scenePos().toTuple()
        self.centre = self.circleItem.mapToScene(
            self.circleItem.centre).toTuple()
        self.radius = self.circleItem.radius

        self.setWindowTitle("Circle Properties")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        self.fLayout = QFormLayout()
        self.fLayout.setContentsMargins(10, 10, 10, 10)
        self.centerXEdit = edf.shortLineEdit()
        self.centerXEdit.setText(str(self.centre[0]))
        self.fLayout.addRow(QLabel("center x-coord:"), self.centerXEdit)
        self.centerYEdit = edf.shortLineEdit()
        self.centerYEdit.setText(str(self.centre[1]))
        self.fLayout.addRow(QLabel("center y-coord:"), self.centerYEdit)
        self.radiusEdit = edf.shortLineEdit()
        self.radiusEdit.setText(str(self.radius))
        self.fLayout.addRow(QLabel("radius:"), self.radiusEdit)
        self.mainLayout.addLayout(self.fLayout)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()

class arcPropertyDialog(QDialog):
    def __init__(self, parent, arcItem: shp.arc):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Arc Properties")
        self.arcItem = arcItem
        self.location = self.arcItem.scenePos().toTuple()
        # self.arcType = self.arcItem.arcType
        # self.arcTypeCombo = QComboBox()
        # self.arcTypeCombo.addItems(shp.arc.arcTypes)
        # self.arcTypeCombo.setCurrentText(self.arcType)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        self.fLayout = QFormLayout()
        self.fLayout.setContentsMargins(10, 10, 10, 10)
        # self.mainLayout.addWidget(self.arcTypeCombo)
        self.startXEdit = edf.shortLineEdit()
        self.startXEdit.setText(
            str(self.arcItem.start.toTuple()[0] + self.location[0]))
        self.fLayout.addRow(QLabel("X Origin:"), self.startXEdit)
        self.startYEdit = edf.shortLineEdit()
        self.startYEdit.setText(
            str(self.arcItem.start.toTuple()[1] + self.location[1]))
        self.fLayout.addRow(QLabel("Y Origin:"), self.startYEdit)
        self.widthEdit = edf.shortLineEdit()
        self.widthEdit.setText(str(self.arcItem.width))
        self.fLayout.addRow(QLabel("Width:"), self.widthEdit)
        self.heightEdit = edf.shortLineEdit()
        self.heightEdit.setText(str(self.arcItem.height))
        self.fLayout.addRow(QLabel("Height:"), self.heightEdit)
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
            str(self.lineItem.start.toTuple()[0] + self.location[0]))
        self.fLayout.addRow(QLabel("Start (X):"), self.startXLine)
        self.startYLine = QLineEdit()
        self.startYLine.setText(
            str(self.lineItem.start.toTuple()[1] + self.location[1]))
        self.fLayout.addRow(QLabel("Start (Y):"), self.startYLine)
        self.endXLine = QLineEdit()
        self.endXLine.setText(
            str(self.lineItem.end.toTuple()[0] + self.location[0]))
        self.fLayout.addRow(QLabel("End (X):"), self.endXLine)
        self.endYLine = QLineEdit()
        self.endYLine.setText(
            str(self.lineItem.end.toTuple()[1] + self.location[1]))
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
        self.labelDefinition = QLineEdit()
        self.labelDefinition.setPlaceholderText("Label Definition")
        self.labelDefinition.setToolTip("Enter label Definition")
        self.fLayout.addRow(QLabel("Label Definition"), self.labelDefinition)
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
        self.labelVisiCombo = QComboBox()
        self.labelVisiCombo.addItems(["Yes", "No"])
        self.fLayout.addRow(QLabel("Label Visible"),self.labelVisiCombo)
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
        assert isinstance(labelItem, shp.label)
        super().__init__(parent)
        self.parent = parent
        self.labelItem = labelItem
        self.location = self.labelItem.scenePos().toTuple()

        self.setWindowTitle("Label Properties")
        self.labelDefinition.setText(str(labelItem.labelDefinition))
        self.labelHeightEdit.setText(str(labelItem.labelHeight))
        self.labelAlignCombo.setCurrentText(labelItem.labelAlign)
        self.labelOrientCombo.setCurrentText(labelItem.labelOrient)
        self.labelUseCombo.setCurrentText(labelItem.labelUse)
        if labelItem.labelVisible:
            self.labelVisiCombo.setCurrentText("Yes")
        else:
            self.labelVisiCombo.setCurrentText("No")
        if self.labelItem.labelType == "Normal":
            self.normalType.setChecked(True)
        elif self.labelItem.labelType == "NLPLabel":
            self.NLPType.setChecked(True)
        elif self.labelItem.labelType == "PyLabel":
            self.pyLType.setChecked(True)
        self.labelXLine = QLineEdit()
        self.labelXLine.setText(
            str(self.labelItem.start.x() + self.location[0]))
        self.labelXLine.setToolTip("X Coordinate")
        self.fLayout.addRow(QLabel("X:"), self.labelXLine)
        self.labelYLine = QLineEdit()
        self.labelYLine.setText(
            str(self.labelItem.start.y() + self.location[1]))
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
        propsGroup = QGroupBox("Symbol Attributes")
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
        # self.attributeTypeList = []
        self.attributeDefList = []
        # Symbol Properties
        self.symbolPropsLayout.addWidget(QLabel("Attribute Name"), 0, 0)
        # self.symbolPropsLayout.addWidget(QLabel("Type"), 0, 1)
        self.symbolPropsLayout.addWidget(QLabel("Definition"), 0, 1)
        i = 0
        for item in self.attributes:
            # print(f'item is :{item}')
            self.attributeNameList.append(edf.longLineEdit())
            self.attributeNameList[i].setText(item.name)
            self.symbolPropsLayout.addWidget(self.attributeNameList[i], i + 1,
                0)
            # attrTypeCombo = QComboBox()
            # attrTypeCombo.addItems(shp.label.labelTypes)
            # self.attributeTypeList.append(attrTypeCombo)
            # self.attributeTypeList[i].setCurrentText(item.type)
            # self.symbolPropsLayout.addWidget(self.attributeTypeList[i], i + 1, 1)
            self.attributeDefList.append(edf.longLineEdit())
            self.attributeDefList[i].setText(item.definition)
            self.symbolPropsLayout.addWidget(self.attributeDefList[i], i + 1, 1)
            i += 1

        self.attributeNameList.append(edf.longLineEdit())
        # attrTypeCombo = QComboBox()
        # attrTypeCombo.addItems(shp.label.labelTypes)
        # self.attributeTypeList.append(attrTypeCombo)
        self.attributeDefList.append(edf.longLineEdit())
        self.symbolPropsLayout.addWidget(self.attributeNameList[-1], i + 2, 0)
        # self.symbolPropsLayout.addWidget(self.attributeTypeList[-1], i + 2, 1)
        self.symbolPropsLayout.addWidget(self.attributeDefList[-1], i + 2, 1)
        self.attributeNameList[-1].setPlaceholderText("Enter Attribute Name")
        # self.attributeTypeList[-1].setToolTip("Enter Attribute Type")
        self.attributeDefList[-1].setToolTip("Enter Attribute Definition")
        self.attributeDefList[-1].editingFinished.connect(
            lambda: self.updateAttributeDef(i + 1))

    def updateAttributeDef(self, i):
        i += 1
        self.attributeNameList.append(edf.longLineEdit())
        # attrTypeCombo = QComboBox()
        # attrTypeCombo.addItems(shp.label.labelTypes)
        # self.attributeTypeList.append(attrTypeCombo)
        self.attributeDefList.append(edf.longLineEdit())
        self.symbolPropsLayout.addWidget(self.attributeNameList[-1], i + 1, 0)
        # self.symbolPropsLayout.addWidget(self.attributeTypeList[-1], i + 1, 1)
        self.symbolPropsLayout.addWidget(self.attributeDefList[-1], i + 1, 1)
        self.attributeNameList[-1].setPlaceholderText("Enter Attribute Name")
        # self.attributeTypeList[-1].setToolTip("Enter Attribute Type")
        self.attributeDefList[-1].setToolTip("Enter Attribute Definition")
        self.attributeDefList[-1].editingFinished.connect(
            lambda: self.updateAttributeDef(i))

    def symbolLabelsMethod(self):
        self.labelDefinitionList = []
        self.labelHeightList = []
        self.labelAlignmentList = []
        self.labelOrientationList = []
        self.labelUseList = []
        self.labelTypeList = []
        self.labelItemList = []
        i = 0
        self.symbolLabelsLayout.addWidget(edf.boldLabel("Definition"), 0, 0)
        self.symbolLabelsLayout.addWidget(edf.boldLabel("Height"), 0, 1)
        self.symbolLabelsLayout.addWidget(edf.boldLabel("Alignment"), 0, 2)
        self.symbolLabelsLayout.addWidget(edf.boldLabel("Orientation"), 0, 3)
        self.symbolLabelsLayout.addWidget(edf.boldLabel("Use"), 0, 4)
        self.symbolLabelsLayout.addWidget(edf.boldLabel("Type"), 0, 5)
        for item in self.items:
            if type(item) == shp.label:
                i += 1
                self.labelItemList.append(item)
                self.labelDefinitionList.append(edf.longLineEdit())
                self.labelDefinitionList[-1].setText(item.labelDefinition)
                self.labelDefinitionList[-1].setReadOnly(True)
                self.symbolLabelsLayout.addWidget(
                    self.labelDefinitionList[i - 1], i, 0)
                self.labelHeightList.append(edf.shortLineEdit())
                self.labelHeightList[-1].setText(str(item.labelHeight))
                self.symbolLabelsLayout.addWidget(self.labelHeightList[i - 1],
                    i, 1)
                self.labelAlignmentList.append(QComboBox())
                self.labelAlignmentList[-1].addItems(shp.label.labelAlignments)
                self.labelAlignmentList[-1].setCurrentText(item.labelAlign)
                self.symbolLabelsLayout.addWidget(self.labelAlignmentList[-1],
                    i, 2)
                self.labelOrientationList.append(QComboBox())
                self.labelOrientationList[-1].addItems(shp.label.labelOrients)
                self.labelOrientationList[-1].setCurrentText(item.labelOrient)
                self.symbolLabelsLayout.addWidget(self.labelOrientationList[-1],
                    i, 3)
                self.labelUseList.append(QComboBox())
                self.labelUseList[-1].addItems(shp.label.labelUses)
                self.labelUseList[-1].setCurrentText(item.labelUse)
                self.symbolLabelsLayout.addWidget(self.labelUseList[-1], i, 4)
                self.labelTypeList.append(QComboBox())
                self.labelTypeList[-1].addItems(shp.label.labelTypes)
                self.labelTypeList[-1].setCurrentText(item.labelType)
                self.symbolLabelsLayout.addWidget(self.labelTypeList[-1], i, 5)
        if i == 0:  # no labels to edit
            self.symbolLabelsLayout.addWidget(QLabel("No symbol labels found."),
                1, 0)


class instanceProperties(QDialog):
    def __init__(self, parent, instance: shp.symbolShape = None):
        # assert isinstance(instance, shp.symbolShape)
        super().__init__(parent)
        self.parent = parent
        self.instance = instance
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Instance Properties")
        self.mainLayout = QVBoxLayout()
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        formLayout = QFormLayout()
        self.libNameEdit = edf.longLineEdit()
        self.libNameEdit.setText(self.instance.libraryName)
        formLayout.addRow(edf.boldLabel("Library Name", self), self.libNameEdit)
        self.cellNameEdit = edf.longLineEdit()
        self.cellNameEdit.setText(self.instance.cellName)
        formLayout.addRow(edf.boldLabel("Cell Name", self), self.cellNameEdit)
        self.viewNameEdit = edf.longLineEdit()
        self.viewNameEdit.setText(self.instance.viewName)
        formLayout.addRow(edf.boldLabel("View Name", self), self.viewNameEdit)
        self.instNameEdit = edf.longLineEdit()
        self.instNameEdit.setText(self.instance.instanceName)
        formLayout.addRow(edf.boldLabel("Instance Name", self), self.instNameEdit)
        location = (
                self.instance.scenePos() - self.instance.scene().origin).toTuple()
        self.xLocationEdit = edf.shortLineEdit()
        self.xLocationEdit.setText(str(location[0]))
        formLayout.addRow(edf.boldLabel("x location", self), self.xLocationEdit)
        self.yLocationEdit = edf.shortLineEdit()
        self.yLocationEdit.setText(str(location[1]))
        formLayout.addRow(edf.boldLabel("y location", self), self.yLocationEdit)
        self.angleEdit = edf.longLineEdit()
        self.angleEdit.setText(str(self.instance.angle))
        formLayout.addRow(edf.boldLabel("Angle", self), self.angleEdit)
        formLayout.setVerticalSpacing(10)
        self.instanceLabelsLayout = QGridLayout()
        row_index = 0
        for label in self.instance.labels.values():
            if label.labelDefinition not in shp.label.predefinedLabels:
                self.instanceLabelsLayout.addWidget(
                    edf.boldLabel(label.labelName, self), row_index, 0)
                labelValueEdit = edf.longLineEdit()
                labelValueEdit.setText(str(label.labelValue))
                self.instanceLabelsLayout.addWidget(labelValueEdit, row_index,
                    1)
                visibleCombo = QComboBox(self)
                visibleCombo.setInsertPolicy(QComboBox.NoInsert)
                visibleCombo.addItems(["True", "False"])
                if label.labelVisible:
                    visibleCombo.setCurrentIndex(0)
                else:
                    visibleCombo.setCurrentIndex(1)
                self.instanceLabelsLayout.addWidget(visibleCombo,row_index,2)
                row_index += 1

        instanceAttributesLayout = QGridLayout()
        instanceAttributesLayout.setColumnMinimumWidth(0, 100)
        for counter, name in enumerate(self.instance.attr.keys()):
            instanceAttributesLayout.addWidget(edf.boldLabel(name, self), counter,
                0)
            labelType = edf.longLineEdit()
            labelType.setReadOnly(True)
            labelName = edf.longLineEdit()
            labelName.setText(self.instance.attr[name])
            instanceAttributesLayout.addWidget(labelName, counter, 1)

        self.mainLayout.addLayout(formLayout)
        self.mainLayout.addWidget(edf.boldLabel("Instance Labels", self))
        self.mainLayout.addLayout(self.instanceLabelsLayout)
        self.mainLayout.addSpacing(40)
        self.mainLayout.addWidget(edf.boldLabel("Instance Attributes", self))
        self.mainLayout.addLayout(instanceAttributesLayout)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


class netProperties(QDialog):
    def __init__(self, parent, net: net.schematicNet = None):
        # assert isinstance(instance, shp.symbolShape)
        super().__init__(parent)
        self.parent = parent
        self.net = net
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Net Properties")
        self.mainLayout = QVBoxLayout()
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        formBox = QGroupBox('Net Properties')
        formLayout = QFormLayout()
        self.netNameEdit = edf.longLineEdit()
        self.netNameEdit.setText(self.net.name)
        formLayout.addRow(edf.boldLabel("Net Name", self), self.netNameEdit)
        formBox.setLayout(formLayout)
        self.mainLayout.addWidget(formBox)
        self.mainLayout.addSpacing(40)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


class createSchematicPinDialog(createPinDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Create Schematic Pin")


class schematicPinPropertiesDialog(createPinDialog):
    def __init__(self, parent, item):
        super().__init__(parent)
        self.setWindowTitle(f"{item.pinName} - Pin Properties")
        self.pinName.setText(item.pinName)
        self.pinDir.setCurrentText(item.pinDir)
        self.pinType.setCurrentText(item.pinType)

class symbolNameDialog(QDialog):
    def __init__(self, cellPath:pathlib.Path, cellName: str, parent):
        super().__init__(parent)
        self.cellPath = cellPath
        self.cellName = cellName
        self.symbolViewNames = [view.stem for view in cellPath.iterdir() if 'symbol' in
                                view.stem]
        self.initUI()
    def initUI(self):
        self.setWindowTitle('Create a symbol?')
        self.mainLayout = QVBoxLayout()
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        formLayout = QFormLayout()
        formLayout.addRow(edf.boldLabel('Library Name'), QLabel(
            self.cellPath.parent.stem) )
        formLayout.addRow(edf.boldLabel('Cell Name'), QLabel(self.cellPath.stem))
        self.symbolViewsCB = QComboBox()
        self.symbolViewsCB.addItems(self.symbolViewNames)
        self.symbolViewsCB.setEditable(True)
        formLayout.addRow(edf.boldLabel('Symbol View Name:'), self.symbolViewsCB)
        self.mainLayout.addLayout(formLayout)
        self.mainLayout.addSpacing(40)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

class symbolCreateDialog(QDialog):
    def __init__(self, parent, inputPinNames: list, outputPinNames: list,
                 inoutPinNames: list):
        super().__init__(parent)
        self.parent = parent
        self.inputPinNames = inputPinNames
        self.outputPinNames = outputPinNames
        self.inoutPinNames = inoutPinNames
        self.setWindowTitle("Create Symbol")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.mainLayout = QVBoxLayout()

        self.fLayout = QFormLayout()
        self.topPinsEdit = edf.longLineEdit()
        self.topPinsEdit.setText(', '.join(self.inoutPinNames))
        self.topPinsEdit.setToolTip("Enter top pins")
        self.fLayout.addRow(edf.boldLabel("Top Pins:"), self.topPinsEdit)
        self.leftPinsEdit = edf.longLineEdit()
        self.leftPinsEdit.setText(', '.join(self.inputPinNames))
        self.leftPinsEdit.setToolTip("Enter left pins")
        self.fLayout.addRow(edf.boldLabel("Left Pins:"), self.leftPinsEdit)
        self.bottomPinsEdit = edf.longLineEdit()
        self.bottomPinsEdit.setToolTip("Enter bottom pins")
        self.fLayout.addRow(edf.boldLabel("Bottom Pins:"), self.bottomPinsEdit)
        self.rightPinsEdit = edf.longLineEdit()
        self.rightPinsEdit.setText(', '.join(self.outputPinNames))
        self.rightPinsEdit.setToolTip("Enter right pins")
        self.fLayout.addRow(edf.boldLabel("Right Pins:"), self.rightPinsEdit)
        self.mainLayout.addLayout(self.fLayout)
        self.mainLayout.addSpacing(20)
        self.geomLayout = QFormLayout()
        self.stubLengthEdit = QLineEdit()
        self.stubLengthEdit.setText('60')
        self.stubLengthEdit.setToolTip('Enter stub lengths')
        self.geomLayout.addRow(edf.boldLabel("Stub Length:"), self.stubLengthEdit)
        self.pinDistanceEdit = QLineEdit()
        self.pinDistanceEdit.setText('80')
        self.pinDistanceEdit.setToolTip('Enter pin spacing')
        self.geomLayout.addRow(edf.boldLabel("Pin spacing:"), self.pinDistanceEdit)
        self.mainLayout.addLayout(self.geomLayout)
        self.mainLayout.addSpacing(40)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()


class noteTextEdit(QDialog):
    '''
    Set text properties.
    '''
    def __init__(self,parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Edit Text")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        mainLayout = QVBoxLayout()
        self.plainTextEdit = QTextEdit()
        mainLayout.addWidget(self.plainTextEdit)
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamilies = [family for family in fontFamilies if
                         QFontDatabase.isFixedPitch(family)]
        formLayout = QFormLayout()
        self.familyCB = QComboBox()
        self.familyCB.addItems(fixedFamilies)
        self.familyCB.currentTextChanged.connect(self.familyFontStyles)
        formLayout.addRow(edf.boldLabel('Font Name'),self.familyCB)
        self.fontStyleCB = QComboBox()
        self.fontStyles = QFontDatabase.styles(fixedFamilies[0])
        self.fontStyleCB.addItems(self.fontStyles)
        self.fontStyleCB.currentTextChanged.connect(self.styleFontSizes)
        formLayout.addRow(edf.boldLabel('Font Style'), self.fontStyleCB)
        self.fontsizeCB = QComboBox()
        self.fontSizes = [str(size) for size in QFontDatabase.pointSizes(fixedFamilies[0],
                                                          self.fontStyles[0])]
        self.fontsizeCB.addItems(self.fontSizes)
        formLayout.addRow(edf.boldLabel('Font Size'),self.fontsizeCB)
        self.textAlignmCB = QComboBox()
        self.textAlignmCB.addItems(shp.text.textAlignments)
        formLayout.addRow(edf.boldLabel('Text Alignment'),self.textAlignmCB)
        self.textOrientCB = QComboBox()
        self.textOrientCB.addItems(shp.text.textOrients)
        formLayout.addRow(edf.boldLabel('Text Orientation'), self.textOrientCB)
        mainLayout.addLayout(formLayout)
        mainLayout.addSpacing(40)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.show()

    def familyFontStyles(self,s):
        self.fontStyleCB.clear()
        self.fontStyles = QFontDatabase.styles(self.familyCB.currentText())
        self.fontStyleCB.addItems(self.fontStyles)

    def styleFontSizes(self,s):
        self.fontsizeCB.clear()
        selectedFamily = self.familyCB.currentText()
        selectedStyle = self.fontStyleCB.currentText()
        self.fontSizes = [str(size) for size in QFontDatabase.pointSizes(
            selectedFamily, selectedStyle)]
        self.fontsizeCB.addItems(self.fontSizes)

class noteTextEditProperties(noteTextEdit):
    def __init__(self,parent, note:shp.text):
        super().__init__(parent)
        self.note = note
        self.plainTextEdit.setText(self.note.textContent)
        self.familyCB.setCurrentText(self.note.fontFamily)
        self.fontStyleCB.setCurrentText(self.note.fontStyle)
        self.fontsizeCB.setCurrentText(self.note.textHeight)
        self.textAlignmCB.setCurrentText(self.note.textAlignment)
        self.textOrientCB.setCurrentText(self.note.textOrient)


class displayConfigDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Display Options")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.vLayout = QVBoxLayout()
        fLayout = QFormLayout()
        self.majorGridEntry = QLineEdit()
        fLayout.addRow("Major Grid:", self.majorGridEntry)

        self.vLayout.addLayout(fLayout)
        self.vLayout.addStretch(1)
        self.vLayout.addWidget(self.buttonBox)
        self.setLayout(self.vLayout)
        self.show()
