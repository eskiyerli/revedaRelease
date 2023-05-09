
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

from PySide6.QtGui import (QFont, QFontMetrics, QFontDatabase)

class font(QFont):
    def __init__(self,fontFamily:str, fontStyle:str, fontSize:int, kerning:bool,logger):
        self._fontFamily = fontFamily
        self._fontStyle = fontStyle
        self._fontSize = fontSize
        self._kerning = kerning
        self._logger = logger
        self.setFamily(self._fontFamily)
        self.setStyle(self._fontStyle)
        self.setPointSize(self._fontSize)
        self.setKerning(self._kerning)
        self.setStyleHint(QFont.TypeWriter)

    @property
    def fontFamily(self):
        return self._fontFamily

    @fontFamily.setter
    def fontFamily(self, value:str):
        fontFamilies = QFontDatabase.families(QFontDatabase.Latin)
        fixedFamilies = [family for family in fontFamilies if
                         QFontDatabase.isFixedPitch(family)]
        if value not in fixedFamilies:
            self._logger.warning('No such font family present in the system. Another '
                                 'font '
                           'will be substituted.')
        self._fontFamily = value
        self.setFamily(self._fontFamily)

    @property
    def fontStyle(self):
        return self._fontStyle

    @fontStyle.setter
    def fontStyle(self,value:str):
        fstyles = QFontDatabase.styles(self._fontFamily)
        if value not in fstyles:
            self._logger.warning(f'No matching style is available. Available styles '
                                 f'are: {",".join(fstyles)}')
        else:
            self.setStyle(value)


