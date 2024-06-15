#    “Commons Clause” License Condition v1.0
#
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

import os

from PySide6.QtCore import (QPoint, )
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGraphicsSimpleTextItem, QGraphicsItem
from dotenv import load_dotenv
from quantiphy import Quantity

load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):
    import pdk.symLayers as symlyr
    import pdk.callbacks as cb
else:
    import defaultPDK.symLayers as symlyr
    import defaultPDK.callbacks as cb


class symbolLabel(QGraphicsSimpleTextItem):
    """
    label: text class definition for symbol drawing.
    labelText is what is shown on the symbol in a schematic
    """

    labelAlignments = ["Left", "Center", "Right"]
    labelOrients = ["R0", "R90", "R180", "R270", "MX", "MX90", "MY", "MY90"]
    labelUses = ["Normal", "Instance", "Pin", "Device", "Annotation"]
    labelTypes = ["Normal", "NLPLabel", "PyLabel"]
    predefinedLabels = [
        "[@libName]",
        "[@cellName]",
        "[@viewName]",
        "[@instName]",
        "[@modelName]",
        "[@elementNum]",
    ]

    def __init__(
        self,
        start: QPoint,
        labelDefinition: str,
        labelType: str,
        labelHeight: int,
        labelAlign: str,
        labelOrient: str,
        labelUse: str,
    ):
        super().__init__("")
        self._start = start  # top left corner
        self._labelDefinition = labelDefinition  # label definition is what is
        # entered in the symbol editor
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        self._labelName = ""  # label Name
        self._labelValue = ""  # label value
        self._labelText = ""  # Displayed label
        self._labelHeight = labelHeight
        self._labelAlign = labelAlign
        self._labelOrient = labelOrient
        self._labelUse = labelUse
        self._labelType = labelType
        self._labelFont = QFont("Arial")
        self._labelFont.setPointSize(int(float(self._labelHeight)))
        self._labelFont.setKerning(False)
        self._labelVisible: bool = False

        self._angle = 0.0  # rotation angle
        self.setBrush(symlyr.labelBrush)
        self.setPos(self._start)

        match self._labelOrient:
            case "R0":
                self.setRotation(0)
            case "R90":
                self.setRotation(90)
            case "R180":
                self.setRotation(180)
            case "R270":
                self.setRotation(270)
            case _:
                self.setRotation(0)

    def __repr__(self):
        return (
            f"symbolLabel({self._start},{self._labelDefinition},"
            f" {self._labelType}, {self._labelHeight}, {self._labelAlign}, {self._labelOrient},"
            f" {self._labelUse})"
        )

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if value:
                self.setBrush(symlyr.selectedLabelBrush)
            else:
                self.setBrush(symlyr.labelBrush)
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        self.scene().itemContextMenu.exec_(event.screenPos())

    @property
    def start(self) -> QPoint:
        return self._start

    @start.setter
    def start(self, start: QPoint):
        self._start = start

    @property
    def labelName(self):
        return self._labelName

    @labelName.setter
    def labelName(self, labelName: str):
        self._labelName = labelName

    @property
    def labelDefinition(self):
        return self._labelDefinition

    @labelDefinition.setter
    def labelDefinition(self, labelDefinition: str):
        if isinstance(labelDefinition, str):
            self._labelDefinition = labelDefinition.strip()
            self.labelDefs()

    @property
    def labelValue(self):
        return self._labelValue

    @labelValue.setter
    def labelValue(self, labelValue):
        self._labelValue = labelValue
        # if label value is set.
        self.labelDefs()

    @property
    def labelText(self):
        return self._labelText

    @labelText.setter
    def labelText(self, labelText):
        self._labelText = labelText
        self.labelDefs()

    @property
    def labelType(self):
        return self._labelType

    @labelType.setter
    def labelType(self, labelType):
        if labelType in self.labelTypes:
            self._labelType = labelType
            self.labelDefs()
        elif self.scene():
            self.scene().logger.error("Invalid label type")

    @property
    def labelAlign(self):
        return self._labelAlign

    @labelAlign.setter
    def labelAlign(self, labelAlignment):
        if labelAlignment in self.labelAlignments:
            self._labelAlign = labelAlignment
        elif self.scene():
            self.scene().logger.error("Invalid label alignment")

    @property
    def labelHeight(self):
        return self._labelHeight

    @labelHeight.setter
    def labelHeight(self, labelHeight):
        self.prepareGeometryChange()
        self._labelHeight = int(float(labelHeight))
        self._labelFont.setPointSize(self._labelHeight)
        self.setFont(self._labelFont)

    @property
    def labelOrient(self):
        return self._labelOrient

    @labelOrient.setter
    def labelOrient(self, labelOrient):
        if labelOrient in self.labelOrients:
            self._labelOrient = labelOrient
        else:
            self.scene().logger.error("Invalid label orientation")

    @property
    def labelUse(self):
        return self._labelUse

    @labelUse.setter
    def labelUse(self, labelUse):
        if labelUse in self.labelUses:
            self._labelUse = labelUse
        elif self.scene():
            self.scene().logger.error("Invalid label use")

    @property
    def labelFont(self):
        return self._labelFont

    @labelFont.setter
    def labelFont(self, labelFont: QFont):
        self._labelFont = labelFont

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.prepareGeometryChange()
        self.setRotation(value)

    @property
    def labelVisible(self) -> bool:
        return self._labelVisible

    @labelVisible.setter
    def labelVisible(self, value: bool):
        assert isinstance(value, bool)
        if value:
            self.setOpacity(1)
            self._labelVisible = True
        else:
            self.setOpacity(0.001)
            self._labelVisible = False

    def moveBy(self, delta: QPoint):
        self._start += delta

    def labelDefs(self):
        """
        This method creates label name, value, and text from a label definition.
        It should be called when a label is defined or redefined.
        """
        self.prepareGeometryChange()

        if self._labelType == symbolLabel.labelTypes[0]:  # normal label
            # Set label name, value, and text to label definition
            self._labelName = f"@{self._labelDefinition}"
            self._labelValue = self._labelDefinition
            self._labelText = self._labelDefinition
        elif self._labelType == symbolLabel.labelTypes[1]:  # NLPLabel
            self.createNLPLabel()
        elif self._labelType == symbolLabel.labelTypes[2]:  # pyLabel
            # self._labelText = f'{self._labelDefinition}'
            self.createPyLabel()
        self.setText(self._labelText)

    def createNLPLabel(self):
        try:
            if self._labelDefinition.strip().startswith("[@"):
                # Find the end of the expression
                end_index = self._labelDefinition.find("]")
                expression = self._labelDefinition[1:end_index]
                parts = expression.split(":")
                self._labelName = parts[0].strip()
                if self.parentItem() is None:  # symbol editor
                    self._labelText = self._labelDefinition
                    self._labelValue = ""
                else:
                    if self._labelDefinition in symbolLabel.predefinedLabels:
                        match self._labelDefinition:
                            case "[@cellName]":
                                # Set label name to "cellName" and value and text to parent item's cell name
                                self._labelValue = self.parentItem().cellName
                                self._labelText = self._labelValue
                            case "[@instName]":
                                # Set label name to "instName" and value and text to parent item's counter with prefix "I"
                                self._labelValue = f"I{self.parentItem().counter}"
                                self._labelText = self._labelValue
                            case "[@libName]":
                                # Set label name to "libName" and value and text to parent item's library name
                                self._labelValue = self.parentItem().libraryName
                                self._labelText = self._labelValue
                            case "[@viewName]":
                                # Set label name to "viewName" and value and text to parent item's view name
                                self._labelValue = self.parentItem().viewName
                                self._labelText = self._labelValue
                            case "[@modelName]":
                                # Set label name to "modelName" and value and text to parent item's "modelName" attribute
                                self._labelValue = self.parentItem().attr.get(
                                    "modelName", ""
                                )
                                self._labelText = self._labelValue
                            case "[@elementNum]":
                                # Set label name to "elementNum" and value and text to parent item's counter
                                self._labelValue = f"{self.parentItem().counter}"
                                self._labelText = self._labelValue
                    else:
                        if len(parts) > 1:
                            formatString = parts[1]
                            defaultValue = parts[2] if len(parts) > 2 else ""
                        else:
                            formatString = ""
                            defaultValue = ""

                        if formatString:
                            prefix, suffix = formatString.split("%")
                            if self._labelValue:
                                self._labelText = f"{prefix}{self._labelValue}{suffix}"
                            elif defaultValue:
                                self._labelValue = defaultValue.replace(prefix, "")
                                self._labelText = defaultValue
                            else:
                                self._labelValue = "?"
                                self._labelText = f"{prefix}{self._labelValue}{suffix}"
        except Exception as e:
            self.scene().logger.error(
                f"Error parsing label definition: {self._labelDefinition}, {e}"
            )



    def createPyLabel(self):
        """
        Create a PyLabel using the label definition and parent item information.
        """
        try:
            # Split the label definition into name and function
            labelName, labelFunction = map(str.strip, self._labelDefinition.split("="))

            # Check if parent item exists and has 'cellName' attribute
            if self.parentItem() and hasattr(self.parentItem(), "cellName"):
                # Construct the expression to evaluate
                parentItem = self.parentItem()
                parentCellName = parentItem.cellName
                parentLabelsDict = parentItem.labels
                if hasattr(cb, parentCellName):
                    callbackClass = getattr(cb, parentCellName)
                    callbackClassObj = callbackClass(parentLabelsDict)
                    if hasattr(callbackClassObj, labelFunction):
                        labelMethod = getattr(callbackClassObj, labelFunction)
                        if labelMethod:
                            self._labelValue = Quantity(labelMethod()).render(prec=3)
                        else:
                            self._labelValue = '?'

                # Set the label text with the name and value
                        self._labelText = f"{labelName}={self._labelValue}"
            else:
                # Set the label text with the name and function
                self._labelText = f"{labelName} = {labelFunction}"
            self._labelName = f"@{labelName}"
        except Exception as e:
            # Log the error if scene exists
            if self.scene():
                self.scene().logger.error(f"PyLabel Error: {e}")
