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

    def _resolve_path(self, env_path: str | None, base_path: Path, env_var_name: str) -> Path | None:
        """Helper method to resolve and validate a path from environment variable."""
        if not env_path:
            return None
            
        try:
            path_obj = Path(env_path)
            if path_obj.is_absolute():
                resolved_path = path_obj
            else:
                resolved_path = base_path.joinpath(env_path)
                
            if not resolved_path.exists():
                print(f"Warning: Path specified in {env_var_name} does not exist: {resolved_path}")
            return resolved_path
        except Exception as e:
            print(f"Error resolving path from {env_var_name}: {str(e)}")
            return None

    def setPaths(self, reveda_runpathObj: Path) -> None:
        """
        Set the paths to revedaeditor, revedasim, and PDK components.
        
        Args:
            reveda_runpathObj: Base path object for resolving relative paths
            
        Raises:
            ValueError: If reveda_runpathObj is None or not a Path object
        """
        if not isinstance(reveda_runpathObj, Path):
            raise ValueError("reveda_runpathObj must be a Path object")
            
        if not reveda_runpathObj.exists():
            raise ValueError(f"Base path does not exist: {reveda_runpathObj}")

        # Resolve revedaeditor path
        self.revedaeditor_path = os.environ.get("REVEDAEDIT_PATH", str(Path.cwd()))
        self.revedaeditor_pathObj = self._resolve_path(
            self.revedaeditor_path, reveda_runpathObj, "REVEDAEDIT_PATH"
        )

        # Resolve revedasim path
        self.revedasim_path = os.environ.get("REVEDASIM_PATH")
        self.revedasim_pathObj = self._resolve_path(
            self.revedasim_path, reveda_runpathObj, "REVEDASIM_PATH"
        )
        if self.revedasim_pathObj:
            sys.path.append(str(self.revedasim_pathObj))

        # Resolve PDK path
        self.reveda_pdk_path = os.environ.get("REVEDA_PDK_PATH")
        self.revedaPdkPathObj = self._resolve_path(
            self.reveda_pdk_path, reveda_runpathObj, "REVEDA_PDK_PATH"
        )
        if self.revedaPdkPathObj:
            sys.path.append(str(self.revedaPdkPathObj))


OS_STYLE_MAP = {"Windows": "Fusion", "Linux": "Fusion", "Darwin": "macOS"}


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
