import sys
from PySide6.QtCore import QRunnable, Slot, Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QDialog,
    QLabel,
    QPushButton,
)

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWebEngineWidgets import (
    QWebEngineView,
)
from PySide6.QtPrintSupport import (
    QPrintDialog,
    QPrinter,
    QPrintPreviewDialog,
)


class helpBrowser(QMainWindow):
    def __init__(self, parent):
        super().__init__(parent=parent)

        self.initUI()

    def initUI(self):
        """
        Initializes the UI of the Help Browser window.
        """
        # Set window title
        self.setWindowTitle("Help Browser")

        # Set window geometry
        self.setGeometry(100, 100, 800, 600)

        # Create central widget
        self.centralW = QWidget(self)

        # Create layout for central widget
        layout = QVBoxLayout(self.centralW)

        # Create web view
        webView = QWebEngineView()

        # Add web view to layout
        layout.addWidget(webView)

        # Set central widget
        self.setCentralWidget(self.centralW)

        # Create menu bar
        menuBar = self.menuBar()

        # Create 'Print' menu
        printMenu = menuBar.addMenu("Print")

        # Create print action
        printIcon = QIcon(":/icons/printer--arrow.png")
        self.printAction = QAction(printIcon, "Print...", self)

        # Create print preview action
        printPreviewIcon = QIcon(":/icons/printer--arrow.png")
        self.printPreviewAction = QAction(printPreviewIcon, "Print Preview...", self)

        # Connect print action to printClick method
        self.printAction.triggered.connect(self.printClick)

        # Connect print preview action to printPreviewClick method
        self.printPreviewAction.triggered.connect(self.printPreviewClick)

        # Add print and print preview actions to print menu
        printMenu.addAction(self.printAction)
        printMenu.addAction(self.printPreviewAction)

        # Set website URL for web view
        websiteUrl = "https://www.reveda.eu/documentation/"
        self.centralW.layout().itemAt(0).widget().setUrl(websiteUrl)

    def printClick(self):
        """
        Handles the 'Print' action.
        """
        # Create print dialog
        dlg = QPrintDialog(self)

        # If print dialog is accepted, start printing
        if dlg.exec() == QDialog.Accepted:
            # Get printer
            printer = dlg.printer()

            # Start print view in a separate thread
            printRunner = startThread(self.printView(printer))
            self.appMainW.threadPool.start(printRunner)

            # Log printing started
            self.logger.info("Printing started")

    def printPreviewClick(self):
        """
        Handles the 'Print Preview' action.
        """
        # Create printer with screen resolution
        printer = QPrinter(QPrinter.ScreenResolution)

        # Set output format to PDF
        printer.setOutputFormat(QPrinter.PdfFormat)

        # Create print preview dialog
        ppdlg = QPrintPreviewDialog(self)

        # Connect paintRequested signal to printView method
        ppdlg.paintRequested.connect(self.printView)

        # Show print preview dialog
        ppdlg.exec()


class aboutDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("About Revolution EDA")
        self.setGeometry(100, 100, 400, 200)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(300)

        layout = QVBoxLayout()

        # Add information about your application using rich text
        about_label = QLabel(
            "<h2>Revolution EDA</h2>"
            "<p><strong>Version:</strong> 0.6.3</p>"
            "<p><strong>Copyright: Revolution Semiconductor</strong> © 2024</p>"
            "<p><strong>License:</strong> Mozilla Public License 2.0 amended with Commons Clause</p>"
            "<p><strong> Website:</strong> <a href='https://www.reveda.eu'>Revolution EDA</a></p>"
            "<p><strong> GitHub:</strong> <a href='https://github.com/eskiyerli/revedaRelease'>Revolution EDA GitHub Repository</a></p>"
        )
        about_label.setOpenExternalLinks(True)  # Allow clickable links
        layout.addWidget(about_label)
        layout.addSpacing(20)

        # Add a "Close" button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)


def show_about_dialog():
    dialog = AboutDialog()
    dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("Revolution EDA")
    main_window.setGeometry(100, 100, 800, 600)

    # Create an "About" action
    about_action = QAction("About", main_window)
    about_action.setShortcut(QKeySequence(Qt.Key_F1))
    about_action.triggered.connect(show_about_dialog)

    # Create a menu bar
    menu_bar = main_window.menuBar()
    help_menu = menu_bar.addMenu("Help")
    help_menu.addAction(about_action)

    main_window.show()
    sys.exit(app.exec_())


class startThread(QRunnable):
    __slots__ = ("fn",)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    @Slot()
    def run(self) -> None:
        try:
            self.fn
        except Exception as e:
            print(e)


def main():
    app = QApplication(sys.argv)
    window = helpBrowser()

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
