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

import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QFileDialog,
    QToolBar,
    QFontDialog,
    QInputDialog,
    QMessageBox,
    QLabel,
)
from PySide6.QtGui import (
    QTextCharFormat,
    QColor,
    QFont,
    QSyntaxHighlighter,
    QAction,
    QIcon,
)

from PySide6.QtCore import (
    Signal,
)
import re
import revedaEditor.resources.resources
import revedaEditor.backend.dataDefinitions as ddef


class verilogaHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#0000FF"))
        keywordFormat.setFontWeight(QFont.Bold)
        functionFormat = QTextCharFormat()
        functionFormat.setForeground(QColor("#00FF00"))
        functionFormat.setFontWeight(QFont.Bold)

        self.highlightingRules = [
            (
                r"\b(module|endmodule|input|output|inout|parameter|analog|real|electrical)\b",
                keywordFormat,
            ),
            (
                r"\b(cos|sin|ln|log|min|pow|sinh|sqrt|tan|tanh|exp|cosh|ddt|ddx|idt)\b",
                functionFormat,
            ),
            # Add more highlighting rules as needed
        ]

        self.highlightingComment = QTextCharFormat()
        self.highlightingComment.setForeground(
            QColor("#007F00")
        )  # Green color for comments

        self.commentStart = "//"
        self.multi_comment_start = "/*"
        self.multi_comment_end = "*/"

    def highlightBlock(self, text):
        for pattern, char_format in self.highlightingRules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), char_format)

        index = text.find(self.commentStart)
        while index >= 0:
            comment_length = len(text) - index
            self.setFormat(index, comment_length, self.highlightingComment)
            index = text.find(self.commentStart, index + comment_length)

        self.setCurrentBlockState(0)
        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = text.find(self.multi_comment_start)

        while startIndex >= 0:
            endIndex = text.find(self.multi_comment_end, startIndex)
            if endIndex == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - startIndex
            else:
                comment_length = endIndex - startIndex + len(self.multi_comment_end)
            self.setFormat(startIndex, comment_length, self.highlightingComment)
            startIndex = text.find(
                self.multi_comment_start, startIndex + comment_length
            )


class xyceHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#0000FF"))
        keywordFormat.setFontWeight(QFont.Bold)
        analysisFormat = QTextCharFormat()
        analysisFormat.setForeground(QColor("#00FF0F"))
        analysisFormat.setFontWeight(QFont.Bold)

        self.highlightingRules = [
            (
                r"(\.subckt|\.end|\.ends|\.param|\.model|\.lib|\.sweep)\b",
                keywordFormat,
            ),
            (
                r"\b(\.ac|\.dc|\.tran|\.hb|\.noise|\.op)\b",
                analysisFormat,
            ),
            # Add more highlighting rules as needed
        ]

        self.highlightingComment = QTextCharFormat()
        self.highlightingComment.setForeground(
            QColor("#007F00")
        )  # Green color for comments

        self.comment_start = "*"
        self.multi_comment_start = "/*"
        self.multi_comment_end = "*/"

    def highlightBlock(self, inputText):
        text = inputText.lower()
        for pattern, char_format in self.highlightingRules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), char_format)

        index = text.find(self.comment_start)
        while index >= 0:
            comment_length = len(text) - index
            self.setFormat(index, comment_length, self.highlightingComment)
            index = text.find(self.comment_start, index + comment_length)

        self.setCurrentBlockState(0)
        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = text.find(self.multi_comment_start)

        while startIndex >= 0:
            endIndex = text.find(self.multi_comment_end, startIndex)
            if endIndex == -1:
                self.setCurrentBlockState(1)
                comment_length = len(text) - startIndex
            else:
                comment_length = endIndex - startIndex + len(self.multi_comment_end)
            self.setFormat(startIndex, comment_length, self.highlightingComment)
            startIndex = text.find(
                self.multi_comment_start, startIndex + comment_length
            )


class verilogaEditor(QMainWindow):
    closedSignal = Signal(ddef.viewTuple, str)

    def __init__(self, parent, fileName=""):
        super().__init__(parent=parent)
        self._cellViewTuple = ddef.viewTuple("", "", "")
        self.parent = parent
        self.fileName: str = fileName
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)

        self.createActions()
        self.createMenus()
        self.createToolbar()

        self.statusLine = self.statusBar()
        self.statusLabel = QLabel()
        self.statusLine.addPermanentWidget(self.statusLabel)

        self.textEdit.cursorPositionChanged.connect(self.updateStatus)

        self.setWindowTitle("Verilog-A Editor")
        self.resize(600, 800)
        self.initEditor()

    def initEditor(self):
        self.highlighter = verilogaHighlighter(self.textEdit.document())
        if self.fileName:
            with open(self.fileName, "r") as file:
                text = file.read()
                self.textEdit.setPlainText(text)

    def createActions(self):
        documentOpenIcon = QIcon(":/icons/document-task.png")
        self.openAction = QAction(documentOpenIcon, "&Open", self)
        self.openAction.setShortcut("Ctrl+O")
        self.openAction.triggered.connect(self.openFile)

        saveIcon = QIcon(":/icons/document.png")
        self.saveAction = QAction(saveIcon, "&Save", self)
        self.saveAction.setShortcut("Ctrl+S")
        self.saveAction.triggered.connect(self.saveFile)

        saveAsIcon = QIcon(":/icons/document--plus.png")
        self.saveAsAction = QAction(saveAsIcon, "Save &As", self)
        self.saveAsAction.triggered.connect(self.saveAsFile)

        quitIcon = QIcon(":/icons/external.png")
        self.quitAction = QAction(quitIcon, "&Quit", self)
        self.quitAction.setShortcut("Ctrl+Q")
        self.quitAction.triggered.connect(self.close)

        fontIcon = QIcon(":icons/ui-label.png")
        self.fontAction = QAction(fontIcon, "&Font", self)
        self.fontAction.setShortcut("Ctrl+F")
        self.fontAction.triggered.connect(self.changeFont)

        cutIcon = QIcon(":/icons/cutter.png")
        self.cutAction = QAction(cutIcon, "&Cut", self)
        self.cutAction.setShortcut("Ctrl+X")
        self.cutAction.triggered.connect(self.textEdit.cut)

        copyIcon = QIcon(":/icons/document-copy.png")
        self.copyAction = QAction(copyIcon, "&Copy", self)
        self.copyAction.setShortcut("Ctrl+C")
        self.copyAction.triggered.connect(self.textEdit.copy)

        pasteIcon = QIcon(":/icons/clipboard-paste.png")
        self.pasteAction = QAction(pasteIcon, "&Paste", self)
        self.pasteAction.setShortcut("Ctrl+V")
        self.pasteAction.triggered.connect(self.textEdit.paste)

        findIcon = QIcon(":/icons/clipboard--pencil.png")
        self.findAction = QAction(findIcon, "&Find", self)
        self.findAction.setShortcut("Ctrl+F")
        self.findAction.triggered.connect(self.findText)

        replaceIcon = QIcon(":/icons/clipboard-search-result.png")
        self.replaceAction = QAction(replaceIcon, "&Replace", self)
        self.replaceAction.setShortcut("Ctrl+H")
        self.replaceAction.triggered.connect(self.replaceText)

    def createMenus(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)
        fileMenu.addAction(self.quitAction)

        format_menu = menubar.addMenu("&Format")
        format_menu.addAction(self.fontAction)

        editMenu = menubar.addMenu("&Edit")
        editMenu.addAction(self.cutAction)
        editMenu.addAction(self.copyAction)
        editMenu.addAction(self.pasteAction)
        editMenu.addAction(self.findAction)
        editMenu.addAction(self.replaceAction)

    def createToolbar(self):
        toolbar = QToolBar("Toolbar")
        self.addToolBar(toolbar)

        toolbar.addAction(self.openAction)
        toolbar.addAction(self.saveAction)
        toolbar.addAction(self.saveAsAction)
        toolbar.addAction(self.quitAction)
        toolbar.addSeparator()
        toolbar.addAction(self.fontAction)
        toolbar.addSeparator()
        toolbar.addAction(self.cutAction)
        toolbar.addAction(self.copyAction)
        toolbar.addAction(self.pasteAction)
        toolbar.addSeparator()
        toolbar.addAction(self.findAction)
        toolbar.addAction(self.replaceAction)

    def openFile(self):
        (self.fileName, _) = QFileDialog.getOpenFileName(
            self, "Open File", "", "Verilog-A Files (*.va);;All Files (*)"
        )
        if self.fileName:
            with open(self.fileName, "r") as file:
                text = file.read()
                self.textEdit.setPlainText(text)

    def saveFile(self):
        if self.fileName:
            with open(self.fileName, "w") as file:
                text = self.textEdit.toPlainText()
                file.write(text)
        else:
            self.saveAsFile()

    def saveAsFile(self):
        (self.fileName, _) = QFileDialog.getSaveFileName(
            self, "Save File", "", "Verilog-A Files (*.va);;All Files (*)"
        )
        if self.fileName:
            with open(self.fileName, "w") as file:
                text = self.textEdit.toPlainText()
                file.write(text)

    def changeFont(self):
        ok, font = QFontDialog.getFont(self.textEdit.font(), self)
        if ok:
            self.textEdit.setFont(font)

    def findText(self):
        text, ok = QInputDialog.getText(self, "Find", "Enter text to find:")
        if ok:
            document = self.textEdit.document()
            cursor = document.find(text)
            if cursor.isNull():
                QMessageBox.information(self, "Find", "Text not found.")
            else:
                self.textEdit.setTextCursor(cursor)

    def replaceText(self):
        findText, ok1 = QInputDialog.getText(self, "Replace", "Enter text to find:")
        if ok1:
            replace_text, ok2 = QInputDialog.getText(
                self, "Replace", "Enter replacement text:"
            )
            if ok2:
                document = self.textEdit.document()
                cursor = document.find(findText)
                if cursor.isNull():
                    QMessageBox.information(self, "Replace", "Text not found.")
                else:
                    cursor.insertText(replace_text)

    def updateStatus(self):
        cursor = self.textEdit.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.statusLabel.setText(f"Line: {line}, Column: {column}")

    def closeEvent(self, event):
        if self.textEdit.toPlainText():
            reply = QMessageBox.question(
                self,
                "Save File",
                "Do you want to save the file?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.saveFile()
        self.closedSignal.emit(self.cellViewTuple, self.fileName)
        super().closeEvent(event)

    @property
    def cellViewTuple(self) -> ddef.viewTuple:
        return self._cellViewTuple

    @cellViewTuple.setter
    def cellViewTuple(self, viewTuple):
        if isinstance(viewTuple, ddef.viewTuple):
            self._cellViewTuple = viewTuple


class xyceEditor(verilogaEditor):
    def __init__(self,parent, fileName=""):
        super().__init__(parent, fileName)
        self.initEditor()
        self.setWindowTitle("Xyce/SPICE Editor")

    def initEditor(self):
        self.highlighter = xyceHighlighter(self.textEdit.document())
        if self.fileName:
            with open(self.fileName, "r") as file:
                text = file.read()
                self.textEdit.setPlainText(text)

    def openFile(self):
        (self.fileName, _) = QFileDialog.getOpenFileName(
            self, "Open File", "", "Xyce Files (*.sp);;All Files (*)"
        )
        if self.fileName:
            with open(self.fileName, "r") as file:
                text = file.read()
                self.textEdit.setPlainText(text)

    def saveAsFile(self):
        (self.fileName, _) = QFileDialog.getSaveFileName(
            self, "Save File", "", "Xyce Files (*.sp);;All Files (*)"
        )
        if self.fileName:
            with open(self.fileName, "w") as file:
                text = self.textEdit.toPlainText()
                file.write(text)


def main():
    app = QApplication(sys.argv)
    editor = verilogaEditor('')
    editor.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
