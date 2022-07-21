import revedaeditor.gui.editorWindows as edw
import revedaeditor.app as app
from PySide6.QtWidgets import (QWidget)
import pathlib


def getLibraryDict():
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