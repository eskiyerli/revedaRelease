from PySide6.QtGui import (QFont, QFontMetrics, QFontDatabase)

class font(QFont):
    def __init__(self,fontName):
        self._fontName = fontName
