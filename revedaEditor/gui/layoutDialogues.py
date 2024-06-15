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

import importlib
import inspect
import pathlib

from PySide6.QtGui import (
    QStandardItem,
    QFontDatabase,
    QDoubleValidator,
    QValidator,
)

from PySide6.QtCore import (Qt,)

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QWidget,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
)

import revedaEditor.common.layoutShapes as lshp
import revedaEditor.gui.editFunctions as edf
import os
from dotenv import load_dotenv
load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):

    import pdk.layoutLayers as laylyr
    import pdk.process as fabproc
else:
    import defaultPDK.layoutLayers as laylyr
    import defaultPDK.process as fabproc

class pcellInstanceDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("PCell Instance Options")
        self.setMinimumWidth(250)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vLayout = QVBoxLayout()

        instanceParamsGroup = QGroupBox("Instance Parameters")
        self.instanceParamsLayout = QFormLayout()
        instanceParamsGroup.setLayout(self.instanceParamsLayout)
        self.pcellLibName = edf.longLineEdit()
        self.pcellLibName.setReadOnly(True)
        self.instanceParamsLayout.addRow("PCell Library:", self.pcellLibName)
        self.pcellCellName = edf.longLineEdit()
        self.pcellCellName.setReadOnly(True)
        self.instanceParamsLayout.addRow("PCell Cell:", self.pcellCellName)
        self.pcellViewName = edf.longLineEdit()
        self.pcellViewName.setReadOnly(True)
        self.instanceParamsLayout.addRow("PCell View:", self.pcellViewName)
        vLayout.addWidget(instanceParamsGroup)

        self.locationGroup = QGroupBox("Location")
        self.locationLayout = QFormLayout()
        self.locationGroup.setLayout(self.locationLayout)
        self.xEdit = edf.shortLineEdit()
        self.yEdit = edf.shortLineEdit()
        self.locationLayout.addRow("Location X:", self.xEdit)
        self.locationLayout.addRow("Location Y:", self.yEdit)
        vLayout.addWidget(self.locationGroup)
        self.locationGroup.hide()
        vLayout.addWidget(self.buttonBox)
        self.setLayout(vLayout)
        self.show()


class pcellInstancePropertiesDialog(pcellInstanceDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("PCell Instance Properties")
        self.instanceNameEdit = edf.longLineEdit()
        self.instanceParamsLayout.addRow("Instance Name:", self.instanceNameEdit)
        self.locationGroup.show()


class pcellLinkDialogue(QDialog):
    def __init__(self, parent, viewItem: QStandardItem):
        super().__init__(parent)
        # self.logger = parent.logger
        self.viewItem = viewItem
        # TODO: A more elegant solution
        self.pcells = self.getClasses("pdk.pcells")
        self.setWindowTitle("PCell Settings")
        self.setMinimumSize(400, 200)
        self.mainLayout = QVBoxLayout()
        groupBox = QGroupBox()
        groupLayout = QVBoxLayout()
        formLayout = QFormLayout()
        groupBox.setLayout(groupLayout)
        self.pcellCB = QComboBox()
        self.pcellCB.addItems(self.pcells)
        formLayout.addRow(edf.boldLabel("PCell:"), self.pcellCB)
        groupLayout.addLayout(formLayout)
        self.mainLayout.addWidget(groupBox)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()

    @staticmethod
    def getClasses(moduleName: str):
        module = importlib.import_module(moduleName)
        classes = []
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, lshp.layoutPcell):
                classes.append(name)
        return classes


class createPathDialogue(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Create Path")
        # self.setMinimumSize(300, 300)
        mainLayout = QVBoxLayout()
        self.pathOrientBox = QGroupBox("Path Orientation")
        horizontalLayout = QHBoxLayout(self.pathOrientBox)
        self.pathOrientBox.setLayout(horizontalLayout)
        pathOrientGroup = QButtonGroup()
        self.manhattanButton = QRadioButton("Manhattan")
        pathOrientGroup.addButton(self.manhattanButton)
        horizontalLayout.addWidget(self.manhattanButton)
        self.diagonalButton = QRadioButton("Diagonal")
        pathOrientGroup.addButton(self.diagonalButton)
        horizontalLayout.addWidget(self.diagonalButton)
        self.anyButton = QRadioButton("Any")
        pathOrientGroup.addButton(self.anyButton)
        horizontalLayout.addWidget(self.anyButton)
        self.horizontalButton = QRadioButton("Horizontal")
        pathOrientGroup.addButton(self.horizontalButton)
        horizontalLayout.addWidget(self.horizontalButton)
        self.verticalButton = QRadioButton("Vertical")
        pathOrientGroup.addButton(self.verticalButton)
        horizontalLayout.addWidget(self.verticalButton)
        self.manhattanButton.setChecked(True)
        pathOrientGroup.setExclusive(True)
        mainLayout.addWidget(self.pathOrientBox)
        groupBox = QGroupBox()
        self.formLayout = QFormLayout()
        groupBox.setLayout(self.formLayout)
        self.pathLayerCB = QComboBox()
        self.formLayout.addRow(edf.boldLabel("Path Layer:"), self.pathLayerCB)
        self.pathWidth = edf.shortLineEdit()
        self.formLayout.addRow(edf.boldLabel("Path Width:"), self.pathWidth)
        self.pathNameEdit = edf.shortLineEdit()
        self.formLayout.addRow(edf.boldLabel("Path Name:"), self.pathNameEdit)
        self.startExtendEdit = edf.shortLineEdit()
        self.formLayout.addRow(edf.boldLabel("Start Extend:"), self.startExtendEdit)
        self.endExtendEdit = edf.shortLineEdit()
        self.formLayout.addRow(edf.boldLabel("End Extend:"), self.endExtendEdit)
        mainLayout.addWidget(groupBox)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.show()


class layoutPathPropertiesDialog(createPathDialogue):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Path Properties")
        # self.mainLayout.removeWidget(self.pathOrientBox)
        self.p1PointEditX = edf.shortLineEdit()
        self.p1PointEditY = edf.shortLineEdit()
        self.p2PointEditX = edf.shortLineEdit()
        self.p2PointEditY = edf.shortLineEdit()
        self.formLayout.addRow(edf.boldLabel("P1 Point X:"), self.p1PointEditX)
        self.formLayout.addRow(edf.boldLabel("P1 Point Y:"), self.p1PointEditY)
        self.formLayout.addRow(edf.boldLabel("P2 Point X:"), self.p2PointEditX)
        self.formLayout.addRow(
            edf.boldLabel("P2 Point Y:"), self.p2PointEditY
        )  # self.update()


class createLayoutPinDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Layout Pin")
        self.setMinimumWidth(300)
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamilies = [
            family for family in fontFamilies if QFontDatabase.isFixedPitch(family)
        ]
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        self.pinPropGroupBox = QGroupBox("Pin Properties")
        fLayout = QFormLayout()
        self.pinPropGroupBox.setLayout(fLayout)
        self.pinName = QLineEdit()
        self.pinName.setPlaceholderText("Pin Name")
        self.pinName.setToolTip("Enter pin name")
        fLayout.addRow(edf.boldLabel("Pin Name"), self.pinName)
        self.pinDir = QComboBox()
        self.pinDir.addItems(lshp.layoutPin.pinDirs)
        self.pinDir.setToolTip("Select pin direction")
        fLayout.addRow(edf.boldLabel("Pin Direction"), self.pinDir)
        self.pinType = QComboBox()
        self.pinType.addItems(lshp.layoutPin.pinTypes)
        self.pinType.setToolTip("Select pin type")
        fLayout.addRow(edf.boldLabel("Pin Type"), self.pinType)
        self.mainLayout.addWidget(self.pinPropGroupBox)
        self.layerSelectGroupBox = QGroupBox("Select layers")
        self.layerFormLayout = QFormLayout()
        self.layerSelectGroupBox.setLayout(self.layerFormLayout)
        self.pinLayerCB = QComboBox()
        self.layerFormLayout.addRow(edf.boldLabel("Pin Layer:"), self.pinLayerCB)
        self.labelLayerCB = QComboBox()
        self.labelLayerText = edf.boldLabel("Label Layer:")
        self.layerFormLayout.addRow(self.labelLayerText, self.labelLayerCB)
        self.mainLayout.addWidget(self.layerSelectGroupBox)
        labelPropBox = QGroupBox("Label Properties")
        labelPropLayout = QFormLayout()
        labelPropBox.setLayout(labelPropLayout)
        self.familyCB = QComboBox()
        self.familyCB.addItems(fixedFamilies)
        self.familyCB.currentTextChanged.connect(self.familyFontStyles)
        labelPropLayout.addRow(edf.boldLabel("Font Name"), self.familyCB)
        self.fontStyleCB = QComboBox()
        self.fontStyles = QFontDatabase.styles(fixedFamilies[0])
        self.fontStyleCB.addItems(self.fontStyles)
        self.fontStyleCB.currentTextChanged.connect(self.styleFontSizes)
        labelPropLayout.addRow(edf.boldLabel("Font Style"), self.fontStyleCB)
        self.labelHeightCB = QComboBox()
        self.fontSizes = [
            str(size)
            for size in QFontDatabase.pointSizes(fixedFamilies[0], self.fontStyles[0])
        ]
        self.labelHeightCB.addItems(self.fontSizes)
        labelPropLayout.addRow(edf.boldLabel("Label Height"), self.labelHeightCB)
        self.labelAlignCB = QComboBox()
        self.labelAlignCB.addItems(lshp.layoutLabel.labelAlignments)
        labelPropLayout.addRow(QLabel("Label Alignment"), self.labelAlignCB)
        self.labelOrientCB = QComboBox()
        self.labelOrientCB.addItems(lshp.layoutLabel.labelOrients)
        labelPropLayout.addRow(QLabel("Label Orientation"), self.labelOrientCB)
        self.mainLayout.addWidget(labelPropBox)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()

    def familyFontStyles(self, s):
        self.fontStyleCB.clear()
        self.fontStyles = QFontDatabase.styles(self.familyCB.currentText())
        self.fontStyleCB.addItems(self.fontStyles)

    def styleFontSizes(self, s):
        self.labelHeightCB.clear()
        selectedFamily = self.familyCB.currentText()
        selectedStyle = self.fontStyleCB.currentText()
        self.fontSizes = [
            str(size)
            for size in QFontDatabase.pointSizes(selectedFamily, selectedStyle)
        ]
        self.labelHeightCB.addItems(self.fontSizes)


class layoutPinProperties(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.setWindowTitle("Layout Pin Properties")
        self.setMinimumWidth(300)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        pinPropGroupBox = QGroupBox("Pin Properties")
        fLayout = QFormLayout()
        pinPropGroupBox.setLayout(fLayout)
        self.pinName = QLineEdit()
        self.pinName.setPlaceholderText("Pin Name")
        self.pinName.setToolTip("Enter pin name")
        fLayout.addRow(edf.boldLabel("Pin Name"), self.pinName)
        self.pinDir = QComboBox()
        self.pinDir.addItems(lshp.layoutPin.pinDirs)
        self.pinDir.setToolTip("Select pin direction")
        fLayout.addRow(edf.boldLabel("Pin Direction"), self.pinDir)
        self.pinType = QComboBox()
        self.pinType.addItems(lshp.layoutPin.pinTypes)
        self.pinType.setToolTip("Select pin type")
        fLayout.addRow(edf.boldLabel("Pin Type"), self.pinType)
        self.pinLayerCB = QComboBox()
        fLayout.addRow(edf.boldLabel("Pin Layer:"), self.pinLayerCB)
        self.pinBottomLeftX = edf.shortLineEdit()
        fLayout.addRow(edf.boldLabel("Pin Bottom Left X:"), self.pinBottomLeftX)
        self.pinBottomLeftY = edf.shortLineEdit()
        fLayout.addRow(edf.boldLabel("Pin Bottom Left Y:"), self.pinBottomLeftY)
        self.pinTopRightX = edf.shortLineEdit()
        fLayout.addRow(edf.boldLabel("Pin Top Right X:"), self.pinTopRightX)
        self.pinTopRightY = edf.shortLineEdit()
        fLayout.addRow(edf.boldLabel("Pin Top Right Y:"), self.pinTopRightY)
        self.mainLayout.addWidget(pinPropGroupBox)

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()


class createLayoutLabelDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Layout Label")
        self.setMinimumWidth(300)
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamilies = [
            family for family in fontFamilies if QFontDatabase.isFixedPitch(family)
        ]
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.mainLayout = QVBoxLayout()
        labelPropBox = QGroupBox("Label Properties")
        self.labelPropLayout = QFormLayout()
        labelPropBox.setLayout(self.labelPropLayout)
        self.labelName = QLineEdit()
        self.labelName.setPlaceholderText("Label Name")
        self.labelName.setToolTip("Enter label name")
        self.labelPropLayout.addRow(edf.boldLabel("Label Name"), self.labelName)
        self.labelLayerCB = QComboBox()
        self.labelPropLayout.addRow(edf.boldLabel("Label Layer:"), self.labelLayerCB)
        self.familyCB = QComboBox()
        self.familyCB.addItems(fixedFamilies)
        self.familyCB.currentTextChanged.connect(self.familyFontStyles)
        self.labelPropLayout.addRow(edf.boldLabel("Font Name"), self.familyCB)
        self.fontStyleCB = QComboBox()
        self.fontStyles = QFontDatabase.styles(fixedFamilies[0])
        self.fontStyleCB.addItems(self.fontStyles)
        self.fontStyleCB.currentTextChanged.connect(self.styleFontSizes)
        self.labelPropLayout.addRow(edf.boldLabel("Font Style"), self.fontStyleCB)
        self.labelHeightCB = QComboBox()
        self.fontSizes = [
            str(size)
            for size in QFontDatabase.pointSizes(fixedFamilies[0], self.fontStyles[0])
        ]
        self.labelHeightCB.addItems(self.fontSizes)
        self.labelPropLayout.addRow(edf.boldLabel("Label Height"), self.labelHeightCB)
        self.labelAlignCB = QComboBox()
        self.labelAlignCB.addItems(lshp.layoutLabel.labelAlignments)
        self.labelPropLayout.addRow(edf.boldLabel("Label Alignment"), self.labelAlignCB)
        self.labelOrientCB = QComboBox()
        self.labelOrientCB.addItems(lshp.layoutLabel.labelOrients)
        self.labelPropLayout.addRow(
            edf.boldLabel("Label Orientation"), self.labelOrientCB
        )
        self.mainLayout.addWidget(labelPropBox)
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        self.show()

    def familyFontStyles(self, s):
        self.fontStyleCB.clear()
        self.fontStyles = QFontDatabase.styles(self.familyCB.currentText())
        self.fontStyleCB.addItems(self.fontStyles)

    def styleFontSizes(self, s):
        selectedFamily = self.familyCB.currentText()
        selectedStyle = self.fontStyleCB.currentText()
        self.fontSizes = [
            str(size)
            for size in QFontDatabase.pointSizes(selectedFamily, selectedStyle)
        ]
        self.labelHeightCB.clear()
        self.labelHeightCB.addItems(self.fontSizes)


class layoutLabelProperties(createLayoutLabelDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Layout Label Properties")
        self.labelTopLeftX = edf.shortLineEdit()
        self.labelPropLayout.addRow(
            edf.boldLabel("Label Top Left X:"), self.labelTopLeftX
        )
        self.labelTopLeftY = edf.shortLineEdit()
        self.labelPropLayout.addRow(
            edf.boldLabel("Label Top Left Y:"), self.labelTopLeftY
        )


class createLayoutViaDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self._parent = parent
        self.setWindowTitle("Create Via(s)")
        self.setMinimumWidth(300)

        
        mainLayout = QVBoxLayout()
        self.viaTypeGroup = QGroupBox("Via Type")
        self.viaTypeLayout = QHBoxLayout()
        self.singleViaRB = QRadioButton("Single")
        self.singleViaRB.setChecked(True)
        self.singleViaRB.clicked.connect(self.singleViaClicked)
        self.arrayViaRB = QRadioButton("Array")
        self.arrayViaRB.clicked.connect(self.arrayViaClicked)
        self.viaTypeLayout.addWidget(self.singleViaRB)
        self.viaTypeLayout.addWidget(self.arrayViaRB)
        self.viaTypeGroup.setLayout(self.viaTypeLayout)
        mainLayout.addWidget(self.viaTypeGroup)
        self.singleViaPropsGroup = QGroupBox("Single Via Properties")
        singleViaPropsLayout = QFormLayout()
        self.singleViaPropsGroup.setLayout(singleViaPropsLayout)
        self.singleViaNamesCB = QComboBox()
        
        self.singleViaNamesCB.currentTextChanged.connect(self.singleViaNameChanged)
        singleViaPropsLayout.addRow(edf.boldLabel("Via Name"), self.singleViaNamesCB)
        self.singleViaWidthEdit = edf.shortLineEdit()
        
        self.singleViaWidthEdit.editingFinished.connect(self.singleViaWidthChanged)
        singleViaPropsLayout.addRow(edf.boldLabel("Via Width"), self.singleViaWidthEdit)
        self.singleViaHeightEdit = edf.shortLineEdit()
        
        self.singleViaHeightEdit.editingFinished.connect(self.singleViaHeightChanged)
        singleViaPropsLayout.addRow(
            edf.boldLabel("Via Height"), self.singleViaHeightEdit
        )
        mainLayout.addWidget(self.singleViaPropsGroup)
        self.arrayViaPropsGroup = QGroupBox("Single Via Properties")
        arrayViaPropsLayout = QFormLayout()
        self.arrayViaPropsGroup.setLayout(arrayViaPropsLayout)
        self.arrayViaNamesCB = QComboBox()
        
        self.arrayViaNamesCB.currentTextChanged.connect(self.arrayViaNameChanged)
        arrayViaPropsLayout.addRow(edf.boldLabel("Via Name"), self.arrayViaNamesCB)
        self.arrayViaWidthEdit = edf.shortLineEdit()
        
        self.arrayViaWidthEdit.editingFinished.connect(self.arrayViaWidthChanged)
        arrayViaPropsLayout.addRow(edf.boldLabel("Via Width"), self.arrayViaWidthEdit)
        self.arrayViaHeightEdit = edf.shortLineEdit()
        
        self.singleViaHeightEdit.editingFinished.connect(self.arrayViaHeightChanged)
        arrayViaPropsLayout.addRow(edf.boldLabel("Via Height"), self.arrayViaHeightEdit)
        self.arrayViaSpacingEdit = edf.shortLineEdit()
        
        self.arrayViaSpacingEdit.editingFinished.connect(self.arrayViaSpacingChanged)
        arrayViaPropsLayout.addRow(edf.boldLabel("Spacing"), self.arrayViaSpacingEdit)
        self.arrayXNumEdit = edf.shortLineEdit()
        self.arrayXNumEdit.setText("1")
        arrayViaPropsLayout.addRow(edf.boldLabel("Array X Size"), self.arrayXNumEdit)
        self.arrayYNumEdit = edf.shortLineEdit()
        self.arrayYNumEdit.setText("1")
        arrayViaPropsLayout.addRow(edf.boldLabel("Array Y Size"), self.arrayYNumEdit)
        mainLayout.addWidget(self.arrayViaPropsGroup)
        self.arrayViaPropsGroup.hide()
        self.singleViaPropsGroup.show()

        self.viaLocationGroup = QGroupBox("Via Location")
        self.viaLocationLayout = QFormLayout()
        self.viaLocationGroup.setLayout(self.viaLocationLayout)
        self.startXEdit = edf.shortLineEdit()
        self.viaLocationLayout.addRow(edf.boldLabel("Start X:"), self.startXEdit)
        self.startYEdit = edf.shortLineEdit()
        self.viaLocationLayout.addRow(edf.boldLabel("Start Y:"), self.startYEdit)
        mainLayout.addWidget(self.viaLocationGroup)
        self.viaLocationGroup.hide()

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.show()

    def singleViaClicked(self):
        self.arrayViaPropsGroup.hide()
        self.singleViaPropsGroup.show()
        self.adjustSize()

    def arrayViaClicked(self):
        self.singleViaPropsGroup.hide()
        self.arrayViaPropsGroup.show()
        self.adjustSize()

    def singleViaNameChanged(self, text: str):
        via = [item for item in fabproc.processVias if item.name == text][0]
        self.singleViaWidthEdit.setText(via.minWidth)
        self.singleViaHeightEdit.setText(via.minHeight)

    def arrayViaNameChanged(self, text: str):
        via = [item for item in fabproc.processVias if item.name == text][0]
        self.arrayViaWidthEdit.setText(via.minWidth)
        self.arrayViaHeightEdit.setText(via.minHeight)

    def singleViaWidthChanged(self):
        text = self.singleViaWidthEdit.text()
        viaDefTuple = [
            item
            for item in fabproc.processVias
            if item.name == self.singleViaNamesCB.currentText()
        ][0]
        self.validateValue(
            text, self.singleViaWidthEdit, viaDefTuple.minWidth, viaDefTuple.maxWidth
        )

    def singleViaHeightChanged(self):
        text = self.singleViaHeightEdit.text()
        viaDefTuple = [
            item
            for item in fabproc.processVias
            if item.name == self.singleViaNamesCB.currentText()
        ][0]
        self.validateValue(
            text, self.singleViaHeightEdit, viaDefTuple.minHeight, viaDefTuple.maxHeight
        )

    def arrayViaWidthChanged(self):
        text = self.arrayViaWidthEdit.text()
        viaDefTuple = [
            item
            for item in fabproc.processVias
            if item.name == self.arrayViaNamesCB.currentText()
        ][0]
        self.validateValue(
            text, self.arrayViaWidthEdit, viaDefTuple.minWidth, viaDefTuple.maxWidth
        )

    def arrayViaHeightChanged(self):
        text = self.arrayViaHeightEdit.text()
        viaDefTuple = [
            item
            for item in fabproc.processVias
            if item.name == self.arrayViaNamesCB.currentText()
        ][0]
        self.validateValue(
            text, self.arrayViaHeightEdit, viaDefTuple.minHeight, viaDefTuple.maxHeight
        )

    def arrayViaSpacingChanged(self):
        text = self.arrayViaSpacingEdit.text()
        viaDefTuple = [
            item
            for item in fabproc.processVias
            if item.name == self.arrayViaNamesCB.currentText()
        ][0]
        self.validateValue(
            text,
            self.arrayViaSpacingEdit,
            viaDefTuple.minSpacing,
            viaDefTuple.maxSpacing,
        )

    def validateValue(self, text, lineEdit: QLineEdit, min: str, max: str):
        validator = QDoubleValidator()
        validator.setRange(float(min), float(max))
        pos = 0
        if validator.validate(text, pos)[0] != QValidator.Acceptable:
            if float(text) < float(min):
                self._parent.logger.warning(f"Value too small, set back to {min}")
                lineEdit.setText(min)
            else:
                self._parent.logger.warning(f"Value too large, set back to {max}")
                lineEdit.setText(max)


class layoutViaProperties(createLayoutViaDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Layout Via Properties")

        self.viaLocationGroup.show()
        self.show()


class layoutRectProperties(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Layout Rectangle Properties")
        self.setMinimumWidth(300)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainLayout = QVBoxLayout()
        self.rectGroup = QGroupBox("Rectangle Properties")
        self.rectGroupLayout = QFormLayout()
        self.rectGroup.setLayout(self.rectGroupLayout)
        self.rectLayerCB = QComboBox()
        self.rectGroupLayout.addRow(edf.boldLabel("Rectangle Layer:"), self.rectLayerCB)
        self.rectWidthEdit = edf.shortLineEdit()
        self.rectGroupLayout.addRow(edf.boldLabel("Width:"), self.rectWidthEdit)
        self.rectHeightEdit = edf.shortLineEdit()
        self.rectGroupLayout.addRow(edf.boldLabel("Height:"), self.rectHeightEdit)
        self.topLeftEditX = edf.shortLineEdit()
        self.rectGroupLayout.addRow(edf.boldLabel("Top Left X:"), self.topLeftEditX)
        self.topLeftEditY = edf.shortLineEdit()
        self.rectGroupLayout.addRow(edf.boldLabel("Top Left Y:"), self.topLeftEditY)
        mainLayout.addWidget(self.rectGroup)
        mainLayout.addWidget(self.buttonBox)
        self.setLayout(mainLayout)
        self.show()


class pointsTableWidget(QTableWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Del.", 'X', "Y"])
        self.setColumnWidth(0,8)
        self.setShowGrid(True)
        self.setGridStyle(Qt.SolidLine)


class layoutPolygonProperties(QDialog):
    def __init__(self, parent: QWidget, tupleList: list):
        super().__init__(parent)
        self.tupleList = tupleList
        self.setWindowTitle("Layout Polygon Properties")
        self.setMinimumWidth(300)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        polygonLayerGroup = QGroupBox("Polygon Layer")
        polygonLayerGroupLayout = QFormLayout()
        self.polygonLayerCB = QComboBox()
        polygonLayerGroupLayout.addRow(edf.boldLabel("Layer:"),self.polygonLayerCB)
        mainLayout.addLayout(polygonLayerGroupLayout)
        self.tableWidget = pointsTableWidget(self)
        mainLayout.addWidget(self.tableWidget)
        mainLayout.addWidget(self.buttonBox)

        self.populateTable()


    def populateTable(self):
        self.tableWidget.setRowCount(len(self.tupleList) + 1)  # Add one extra row

        for row, item in enumerate(self.tupleList):
            self.addRow(row, item)

        # Add an empty row at the end
        self.addEmptyRow(len(self.tupleList))

        # Connect cellChanged signal to handle when the last row is edited
        self.tableWidget.cellChanged.connect(self.handleCellChange)

    def addRow(self, row, item):

        delete_checkbox = QCheckBox()
        self.tableWidget.setCellWidget(row, 0, delete_checkbox)

        self.tableWidget.setItem(row, 1, QTableWidgetItem(str(item[0])))
        self.tableWidget.setItem(row, 2, QTableWidgetItem(str(item[1])))
        delete_checkbox.stateChanged.connect(
            lambda state, r=row: self.deleteRow(r, state)
        )

    def addEmptyRow(self, row):

        # self.table_widget.insertRow(row)
        delete_checkbox = QCheckBox()
        self.tableWidget.setCellWidget(row, 0, delete_checkbox)
        delete_checkbox.stateChanged.connect(
            lambda state, r=row: self.deleteRow(r, state))

        self.tableWidget.setItem(row, 1, QTableWidgetItem(""))
        self.tableWidget.setItem(row, 2, QTableWidgetItem(""))

    def handleCellChange(self, row, column):
        if (
            row == self.tableWidget.rowCount() - 1
        ):  # Check if last row and tuple text column
            if self.tableWidget.item(row,2) is not None:
                text1 = self.tableWidget.item(row, 1).text()
                text2 = self.tableWidget.item(row, 2).text()
                if text1 != "" and text2 != "":
                    self.tableWidget.insertRow(row + 1)
                    self.addEmptyRow(row + 1)

    def deleteRow(self, row, state):
        print("delete")
        if state == 2:  # Checked state
            self.tableWidget.removeRow(row)



#
# class layoutPolygonProperties(QDialog):
#     def __init__(self, parent: QWidget, numPoints: int):
#         super().__init__(parent)
#         self.setWindowTitle("Layout Polygon Properties")
#         self.setMinimumWidth(300)
#         self._numPoints = numPoints
#         self._i = 0
#         self._checkBoxList = []
#         self.pointXEdits = []
#         self.pointYEdits = []
#         self.mainLayout = QVBoxLayout()
#         polygonLayerGroup = QGroupBox("Polygon Layer")
#         polygonLayerGroupLayout = QFormLayout()
#         self.polygonLayerCB = QComboBox()
#         polygonLayerGroupLayout.addRow(edf.boldLabel("Layer:"),self.polygonLayerCB)
#         self.mainLayout.addLayout(polygonLayerGroupLayout)
#         self.polygonGroup = QGroupBox("Polygon Properties")
#         self.polygonGroupLayout = QGridLayout()
#         self.polygonGroup.setLayout(self.polygonGroupLayout)
#         self.polygonGroupLayout.addWidget(edf.boldLabel("Points:"), 0, 0)
#         self.polygonGroupLayout.addWidget(edf.boldLabel("X:"), 0, 1)
#         self.polygonGroupLayout.addWidget(edf.boldLabel("Y:"), 0, 2)
#         self.polygonGroupLayout.addWidget(edf.boldLabel("Delete:"), 0, 3)
#         for self._i in range(numPoints+1):
#             self.polygonGroupLayout.addWidget(
#                 edf.boldLabel(f"Point {self._i + 1}"), self._i+1, 0
#             )
#             self.pointXEdits.append(edf.shortLineEdit())
#             self.polygonGroupLayout.addWidget(self.pointXEdits[-1], self._i+1, 1)
#             self.pointYEdits.append(edf.shortLineEdit())
#             self.polygonGroupLayout.addWidget(self.pointYEdits[-1], self._i+1, 2)
#             self._checkBoxList.append(QCheckBox())
#             self.polygonGroupLayout.addWidget(
#                 self._checkBoxList[self._i], self._i+1, 3
#             )
#             self._checkBoxList[self._i].stateChanged.connect(self._deleteRow)
#         # now add an empty row and when it is edited add a new row.
#         self.polygonGroupLayout.itemAtPosition(
#             self._i + 1, 2
#         ).widget().editingFinished.connect(self._newPointYChanged)
#         self.mainLayout.addWidget(self.polygonGroup)
#
#         QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
#         self.buttonBox = QDialogButtonBox(QBtn)
#         self.buttonBox.accepted.connect(self.accept)
#         self.buttonBox.rejected.connect(self.reject)
#         self.mainLayout.addWidget(self.buttonBox)
#         self.setLayout(self.mainLayout)
#         self.show()
#
#     def _newPointYChanged(self):
#         """
#         This function is called when the user clicks the add point button for a polygon.
#         It adds a new row to the layout with the appropriate labels and input fields for
#         the x and y coordinates of the new point.
#         The function also adds a delete button to the new row that allows the user to
#         delete the point.
#
#         Returns:
#             None
#         """
#         self._i += 1
#         self.polygonGroupLayout.addWidget(
#             edf.boldLabel(f"Point {self._i + 1}"), self._i + 2, 0
#         )
#         self.pointXEdits.append(edf.shortLineEdit())
#         self.polygonGroupLayout.addWidget(self.pointXEdits[-1], self._i + 2, 1)
#         self.pointYEdits.append(edf.shortLineEdit())
#         self.polygonGroupLayout.addWidget(self.pointYEdits[-1], self._i + 2, 2)
#         self._checkBoxList.append(QCheckBox())
#         self.polygonGroupLayout.addWidget(self._checkBoxList[self._i], self._i + 2, 3)
#         self._checkBoxList[self._i].stateChanged.connect(self._deleteRow)
#
#     def _deleteRow(self, state):
#         """
#         This function is called when the user clicks the delete button for a polygon point.
#         It removes the corresponding row from the layout and adjusts the layout size.
#
#         Parameters:
#         state (int): The state of the delete button, which is 2 when the button is clicked.
#
#         Returns:
#         None
#         """
#         if state == 2:
#             sender = self.sender()
#             row = self._checkBoxList.index(sender) + 1
#             for i in range(4):
#                 widget = self.polygonGroupLayout.itemAtPosition(row, i).widget()
#                 print(widget)
#                 # self.polygonGroupLayout.removeWidget(widget)
#                 # widget.deleteLater()
#             self.adjustSize()
#

class layoutInstancePropertiesDialog(QDialog):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self.setWindowTitle("Layout Instance Properties")
        self.setMinimumWidth(300)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vLayout = QVBoxLayout()
        instanceParamsGroup = QGroupBox("Instance Parameters")
        self.instanceParamsLayout = QFormLayout()
        instanceParamsGroup.setLayout(self.instanceParamsLayout)
        self.instanceLibName = edf.longLineEdit()
        self.instanceLibName.setReadOnly(True)
        self.instanceParamsLayout.addRow("Instance Library:", self.instanceLibName)
        self.instanceCellName = edf.longLineEdit()
        self.instanceCellName.setReadOnly(True)
        self.instanceParamsLayout.addRow("Instance Cell:", self.instanceCellName)
        self.instanceViewName = edf.longLineEdit()
        self.instanceViewName.setReadOnly(True)
        self.instanceParamsLayout.addRow("Instance View:", self.instanceViewName)
        self.instanceNameEdit = edf.longLineEdit()
        self.instanceParamsLayout.addRow("Instance Name:", self.instanceNameEdit)
        vLayout.addWidget(instanceParamsGroup)

        self.locationGroup = QGroupBox("Location")
        self.locationLayout = QFormLayout()
        self.locationGroup.setLayout(self.locationLayout)
        self.xEdit = edf.shortLineEdit()
        self.yEdit = edf.shortLineEdit()
        self.locationLayout.addRow("Location X:", self.xEdit)
        self.locationLayout.addRow("Location Y:", self.yEdit)
        vLayout.addWidget(self.locationGroup)
        vLayout.addWidget(self.buttonBox)
        self.setLayout(vLayout)
        self.show()
