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
#    Add-ons and extensions developed for this software may be distributed
#    under their own separate licenses.
#
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
#

# The PySide6 plugin covers qt-plugins
# nuitka-project: --standalone
# nuitka-project: --include-plugin-directory=revedaEditor
# nuitka-project: --nofollow-import-to=pdk,defaultPDK
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --include-module=_json
# nuitka-project: --product-version="0.7.1"
# nuitka-project: --linux-icon=./logo-color.png
# nuitka-project: --windows-icon-from-ico=./logo-color.png
# nuitka-project: --company-name="Revolution EDA"
# nuitka-project: --file-description="Electronic Design Automation Software for Professional Custom IC Design Engineers"
import os
import platform
import sys
from PySide6.QtWidgets import QApplication


import revedaEditor.gui.revedaMain as rvm
import revedaEditor.gui.pythonConsole as pcon
from contextlib import redirect_stdout, redirect_stderr
from dotenv import load_dotenv
from pathlib import Path


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
        reveda_runpathObj = Path(__file__).resolve().parent
        self.revedaeditor_path = None
        self.revedasim_path = None
        self.reveda_pdk_path = None
        self.setPaths(reveda_runpathObj)

    def setPaths(self, reveda_runpathObj):
        # Set the paths to the revedaeditor and revedasim
        self.revedaeditor_path = os.environ.get("REVEDAEDIT_PATH", None)
        if self.revedaeditor_path:
            if Path(self.revedaeditor_path).is_absolute():
                self.revedaeditor_pathObj = Path(self.revedaeditor_path)
            else:
                self.revedaeditor_pathObj = reveda_runpathObj.joinpath(
                    self.revedaeditor_path
                )
        self.revedasim_path = os.environ.get("REVEDASIM_PATH", None)
        if self.revedasim_path:
            if Path(self.revedasim_path).is_absolute():
                self.revedasim_pathObj = Path(self.revedasim_path)
            else:
                self.revedasim_pathObj = reveda_runpathObj.joinpath(self.revedasim_path)
            sys.path.append(str(self.revedasim_pathObj))
        self.reveda_pdk_path = os.environ.get("REVEDA_PDK_PATH", None)
        if self.reveda_pdk_path:
            if Path(self.reveda_pdk_path).is_absolute():
                self.reveda_pdk_pathObj = Path(self.reveda_pdk_path)
            else:
                self.reveda_pdk_pathObj = reveda_runpathObj.joinpath(
                    self.reveda_pdk_path
                )
            sys.path.append(str(self.reveda_pdk_pathObj))


def main():
    # Start Main application window
    app = revedaApp(sys.argv)
    os_name = platform.system()

    if os_name == "Windows":
        app.setStyle("Windows")
    elif os_name == "Linux":
        app.setStyle("Breeze")
    elif os_name == "Darwin":  # macOS
        app.setStyle("macOS")

    mainW = rvm.MainWindow()
    mainW.setWindowTitle("Revolution EDA")

    # empty argument as there is no parent window.
    redirect = pcon.Redirect(mainW.centralW.console.errorwrite)
    with redirect_stdout(mainW.centralW.console), redirect_stderr(redirect):
        mainW.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
