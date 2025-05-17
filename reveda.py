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
#    consideration (including without limitation fees for hosting) a product or service whose value
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
# nuitka-project: --enable-plugin=pyside6
# nuitka-project: --nofollow-import-to=defaultPDK, gf180_pdk,
# nuitka-project: --include-data-dir=compiled_plugins=plugins
# nuitka-project: --output-dir=dist
# nuitka-project: --product-version="0.7.9"
# nuitka-project: --linux-icon=./logo-color.png
# nuitka-project: --windows-icon-from-ico=./logo-color.png
# nuitka-project: --company-name="Revolution EDA"
# nuitka-project: --file-description="Electronic Design Automation Software for Professional Custom IC Design Engineers"

# import time
import importlib
import os
import pkgutil
import platform
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Optional
import logging
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication

import revedaEditor.gui.pythonConsole as pcon
import revedaEditor.gui.revedaMain as rvm


class revedaApp(QApplication):
    """
    Initializes the class instance and sets the paths to the revedaeditor and revedasim if the corresponding
    environment variables exist. Also adds the paths to the system path if available.

    Returns:
        None
    """
    LOGGER = "reveda"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Load environment variables and setup paths
        load_dotenv()
        reveda_runpathObj = Path(__file__).resolve().parent
        
        # Initialize logger
        self.logger = logging.Logger(self.LOGGER)
        f_handler = logging.FileHandler("reveda.log")
        f_handler.setLevel(logging.INFO)
        f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        f_handler.setFormatter(f_format)
        self.logger.addHandler(f_handler)
        # Setup paths and plugins
        self.setPaths(reveda_runpathObj)
        self.plugins = {}
        
        # Plugin setup
        plugin_dir = reveda_runpathObj / "plugins"
        if plugin_dir not in sys.path:
            sys.path.insert(0, str(plugin_dir))
        self.discover_plugins(plugin_dir)
        
        # Log loaded plugins
        self.logger.info(f"Loaded plugins: {self.plugins}")

    def discover_plugins(self, plugin_dir):
        for finder, name, ispkg in pkgutil.iter_modules([plugin_dir]):
            module = importlib.import_module(name)
            self.plugins[f'{plugin_dir.name}.{name}'] = module

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

        if not isinstance(reveda_runpathObj, Path):
            raise ValueError("reveda_runpathObj must be a Path object")
            
        if not reveda_runpathObj.exists():
            raise ValueError(f"Base path does not exist: {reveda_runpathObj}")

        # Resolve PDK path
        self.reveda_pdk_path = os.environ.get("REVEDA_PDK_PATH")
        self.revedaPdkPathObj = self._resolve_path(
            self.reveda_pdk_path, reveda_runpathObj, "REVEDA_PDK_PATH"
        )
        if self.revedaPdkPathObj:
            sys.path.append(str(self.revedaPdkPathObj))


def initialize_app(argv) -> tuple[revedaApp, Optional[str]]:
    """Initialize application and determine style"""
    OS_STYLE_MAP = {"Windows": "Fusion", "Linux": "Fusion", "Darwin": "macOS"}
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
    app.mainW = mainW
    console = mainW.centralW.console
    redirect = pcon.Redirect(console.errorwrite)
    with redirect_stdout(console), redirect_stderr(redirect):
        mainW.show()
        return app.exec()

if __name__ == "__main__":
    main()
