
from PySide6.QtCore import (Qt, )
from PySide6.QtWidgets import (QLineEdit, QLabel, QWidget)

class shortLineEdit(QLineEdit):
    def __init__(self):
        super().__init__(None)
        self.setMaximumWidth(80)


class boldLabel(QLabel):
    def __init__(self, text: str, parent: QWidget = None):
        super().__init__(text, parent)
        self.setTextFormat(Qt.RichText)
        self.setText("<b>" + text + "</b>")


class longLineEdit(QLineEdit):
    def __init__(self):
        super().__init__(None)
        self.setMaximumWidth(500)
