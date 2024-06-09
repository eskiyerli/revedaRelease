import gdstk
import revedaEditor.common.layoutShapes as lshp
import revedaEditor.backend.schBackEnd as scb
import pathlib
import inspect


class gdsImporter:
    def __init__(self, inputFile: pathlib.Path, cellview: scb.viewItem):
        self.inputFile = inputFile
        self.cellview = cellview
        self._library = gdstk.library(inputFile)
        self._topCells = self._library.topCells()

    def gdsImporter(self, inputFile: pathlib.Path):
        for cell in self._topCells:
            paths


