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


from PySide6.QtCore import (
    Qt, Signal,
)
from PySide6.QtWidgets import QLineEdit, QLabel, QWidget


class shortLineEdit(QLineEdit):
    def __init__(self, value: str = ""):
        super().__init__(None)
        self.setMaximumWidth(90)
        if isinstance(value, str):
            self.setText(value)
        else:
            self.setText(str(value))


class boldLabel(QLabel):
    def __init__(self, text: str, parent: QWidget = None):
        super().__init__(text, parent)
        self.setTextFormat(Qt.RichText)
        self.setText("<b>" + text + "</b>")


class longLineEdit(QLineEdit):
    cursorPlaced = Signal()

    def __init__(self, value: str = ""):
        super().__init__(None)
        self.setMaximumWidth(500)
        self.setMinimumWidth(200)
        if isinstance(value, str):
            self.setText(value)
        else:
            self.setText(str(value))

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.cursorPlaced.emit()
