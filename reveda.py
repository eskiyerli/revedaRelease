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

import os
import sys
from PySide6.QtWidgets import (QApplication)
from PySide6.QtGui import QScreen, QGuiApplication
import revedaEditor.gui.revedaMain as rvm
import revedaEditor.gui.pythonConsole as pcon
from contextlib import redirect_stdout, redirect_stderr
from dotenv import load_dotenv


# simulation window

class revedaApp(QApplication):
    """
    Initializes the class instance and sets the paths to the revedaeditor and revedasim if the corresponding 
    environment variables exist. Also adds the paths to the system path if available.

    Returns:
        None
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load environment variables
        load_dotenv()
        # Set the paths to the revedaeditor and revedasim
        self.revedaeditor_path = os.environ.get("REVEDAEDIT_PATH", None)
        self.revedasim_path = os.environ.get("REVEDASIM_PATH", None)
         # Add the revedaeditor path to the system path if available
        if self.revedaeditor_path:
            sys.path.append(self.revedaeditor_path)
         # Add the revedasim path to the system path if available
        if self.revedasim_path:
            sys.path.append(self.revedasim_path)

def main():
    # Start Main application window
    app = revedaApp(sys.argv)
    app.setStyle("Fusion")

    mainW = rvm.MainWindow()
    mainW.setWindowTitle("Revolution EDA")

    # empty argument as there is no parent window.
    redirect = pcon.Redirect(mainW.centralW.console.errorwrite)
    with redirect_stdout(mainW.centralW.console), redirect_stderr(redirect):
        mainW.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()

