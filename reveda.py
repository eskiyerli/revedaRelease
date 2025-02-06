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
# nuitka-project-if: {OS} == "Darwin":
#    nuitka-project: --standalone
#    nuitka-project: --macos-create-app-bundle
# The PySide6 plugin covers qt-plugins
# nuitka-project: --standalone
# nuitka-project: --windows-console-mode=attach
# nuitka-project: --include-plugin-directory=revedaEditor
# nuitka-project: --nofollow-import-to= defaultPDK, revedasim, revedaPlot, ihp_pdk, gf180_pdk
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --product-version="0.7.9"
# nuitka-project: --linux-icon=./logo-color.png
# nuitka-project: --windows-icon-from-ico=./logo-color.png
# nuitka-project: --company-name="Revolution EDA"
# nuitka-project: --file-description="Electronic Design Automation Software for Professional Custom IC Design Engineers"

import os
import platform
import sys
from PySide6.QtWidgets import QApplication
from typing import Optional
# import time

import revedaEditor.gui.revedaMain as rvm
import revedaEditor.gui.pythonConsole as pcon
from contextlib import redirect_stdout, redirect_stderr
from dotenv import load_dotenv
from pathlib import Path


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
                self.revedaPdkPathObj = Path(self.reveda_pdk_path)
            else:
                self.revedaPdkPathObj = reveda_runpathObj.joinpath(
                    self.reveda_pdk_path
                )
            sys.path.append(str(self.revedaPdkPathObj))

OS_STYLE_MAP = {"Windows": "Windows", "Linux": "Breeze", "Darwin": "macOS"}


def initialize_app(argv) -> tuple[revedaApp, Optional[str]]:
    """Initialize application and determine style"""
    app = revedaApp(argv)
    style = OS_STYLE_MAP.get(platform.system())
    return app, style


def main():
    app, style = initialize_app(sys.argv)
    if style:
        app.setStyle(style)
        print(f"Applied {style} style")
    mainW = rvm.MainWindow()
    mainW.setWindowTitle("Revolution EDA")
    console = mainW.centralW.console
    redirect = pcon.Redirect(console.errorwrite)
    with redirect_stdout(console), redirect_stderr(redirect):
        mainW.show()
        return app.exec()

if __name__ == "__main__":
    main()

