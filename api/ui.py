
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

# TODO: fix these functions.
import gui.editorWindows as edw
from PySide6.QtWidgets import (QWidget)
import pathlib


def getLibraryDict():
    global app
    return app.mainW.libraryDict


def getLibraryView():
    if app.mainW.libraryBrowser is None:
        app.mainW.libraryBrowser = edw.libraryBrowser(app.mainW)
        return app.mainW.libraryBrowser.libBrowserCont.designView
    else:
        return app.mainW.libraryBrowser.libBrowserCont.designView


def exportSpiceNetlist(libraryName: str, cellName: str, viewName: str,
                       netlistPath: str):
    libraryDict = getLibraryDict()
    libraryPath = libraryDict.get(libraryName)
    libraryView = getLibraryView()
    if libraryPath is not None:
        viewPath = pathlib.Path(libraryPath).joinpath(cellName).joinpath(
            viewName).with_suffix(".json")
        schematicEditor = edw.schematicEditor(viewPath, libraryDict,
                                              libraryView)
        schematicScene = schematicEditor.centralW.scene
        schematicScene.loadSchematicCell(viewPath)
        schematicScene.createNetlist(pathlib.Path(netlistPath), True)

def createSymbol(libraryName:str, cellName:str, viewName:str):
    libraryDict = getLibraryDict()
    libraryPath = libraryDict.get(libraryName)
    libraryView = getLibraryView()
    if libraryPath is not None:
        viewPath = pathlib.Path(libraryPath).joinpath(cellName).joinpath(
            viewName).with_suffix(".json")
        schematicEditor = edw.schematicEditor(viewPath, libraryDict,
                                              libraryView)
        schematicScene = schematicEditor.centralW.scene

        schematicScene.loadSchematicCell(viewPath)
        schematicScene.createSymbol()