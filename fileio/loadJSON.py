"""
======================= START OF LICENSE NOTICE =======================
  Copyright (C) 2022 Murat Eskiyerli. All Rights Reserved

  NO WARRANTY. THE PRODUCT IS PROVIDED BY DEVELOPER "AS IS" AND ANY
  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL DEVELOPER BE LIABLE FOR
  ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
  GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
  IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
  OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THE PRODUCT, EVEN
  IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
======================== END OF LICENSE NOTICE ========================
  Primary Author: Murat Eskiyerli

"""

# Load symbol and maybe later schematic from json file.
# import pathlib

import json

from PySide6.QtCore import (QPoint, Qt, )  # QtCore
from PySide6.QtGui import (QColor, QPen, )

import common.shape as shp
import fileio.symbolEncoder as se
import common.net as net


def createSymbolItems(item, gridTuple):
    """
    Create symbol items from json file.
    """
    if item["type"] == "rect":
        return createRectItem(item, gridTuple)
    elif item["type"] == "circle":
        return createCircleItem(item, gridTuple)
    elif item["type"] == "line":
        return createLineItem(item, gridTuple)
    elif item["type"] == "pin":
        return createPinItem(item, gridTuple)
    elif item["type"] == "label":
        return createLabelItem(item, gridTuple)


def createRectItem(item, gridTuple):
    """
    Create symbol items from json file.
    """
    start = QPoint(item["rect"][0], item["rect"][1])
    end = QPoint(item["rect"][2], item["rect"][3])
    penStyle = Qt.PenStyle.__dict__[item["lineStyle"]]  # convert string to enum
    penWidth = item["width"]
    penColor = QColor(*item["color"])
    pen = QPen(penColor, penWidth, penStyle)
    pen.setCosmetic(item["cosmetic"])
    rect = shp.rectangle(start, end, pen,
        gridTuple)  # note that we are using grid values for scene
    rect.setPos(QPoint(item["location"][0], item["location"][1]), )
    rect.angle = item["angle"]
    return rect


def createCircleItem(item, gridTuple):
    centre = QPoint(item["centre"][0], item["centre"][1])
    end = QPoint(item["end"][0], item["end"][1])
    penStyle = Qt.PenStyle.__dict__[item["lineStyle"]]  # convert string to enum
    penWidth = item["width"]
    penColor = QColor(*item["color"])
    pen = QPen(penColor, penWidth, penStyle)
    pen.setCosmetic(item["cosmetic"])
    circle = shp.circle(centre, end, pen,
        gridTuple)  # note that we are using grid values for scene
    circle.setPos(QPoint(item["location"][0], item["location"][1]), )
    circle.angle = item["angle"]
    return circle


def createLineItem(item, gridTuple):
    start = QPoint(item["start"][0], item["start"][1])
    end = QPoint(item["end"][0], item["end"][1])
    penStyle = Qt.PenStyle.__dict__[item["lineStyle"]]
    penWidth = item["width"]
    penColor = QColor(*item["color"])
    pen = QPen(penColor, penWidth, penStyle)
    pen.setCosmetic(item["cosmetic"])
    line = shp.line(start, end, pen, gridTuple)
    line.setPos(QPoint(item["location"][0], item["location"][1]))
    line.angle = item["angle"]
    return line


def createPinItem(item, gridTuple):
    start = QPoint(item["start"][0], item["start"][1])
    penStyle = Qt.PenStyle.__dict__[item["lineStyle"]]
    penWidth = item["width"]
    penColor = QColor(*item["color"])
    pen = QPen(penColor, penWidth, penStyle)
    pen.setCosmetic(item["cosmetic"])
    pin = shp.pin(start, pen, item["name"], item["dir"], item["pinType"],
        gridTuple, )
    pin.setPos(QPoint(item["location"][0], item["location"][1]))
    pin.angle = item["angle"]
    return pin


def createLabelItem(item, gridTuple):
    start = QPoint(item["start"][0], item["start"][1])
    penStyle = Qt.PenStyle.__dict__[item["lineStyle"]]
    penWidth = item["width"]
    penColor = QColor(*item["color"])
    pen = QPen(penColor, penWidth, penStyle)
    pen.setCosmetic(item["cosmetic"])
    label = shp.label(start, pen, item["definition"], gridTuple, item["labelType"],
        item["height"], item["align"], item["orient"], item["use"], )
    label.setPos(QPoint(item["location"][0], item["location"][1]))
    label.angle = item["angle"]
    label.labelName = item["name"]
    label.labelText = item["text"]
    label.labelVisible = item["visible"]
    label.labelValue = item["value"]
    return label


def createSymbolAttribute(item):
    if item["type"] == "attribute":
        return se.symbolAttribute(item["name"], item["definition"])


def createSchematicItems(item, libraryDict, viewName, gridTuple: (int, int)):
    """
    Create schematic items from json file.
    """
    if item["type"] == "symbolShape":
        libraryPath = libraryDict.get(item["library"])
        if libraryPath is None:
            print(f'{item["library"]} cannot be found.')
            return None
        cell = item["cell"]
        instCounter = item["instCounter"]
        itemShapes = list()
        symbolAttributes = dict()
        labelDict = item["labelDict"]
        draftPen = QPen(QColor("white"), 1)
        # find the symbol file
        file = libraryPath.joinpath(cell, viewName + ".json")
        # load json file and create shapes
        with open(file, "r") as temp:
            try:
                shapes = json.load(temp)
                for shape in shapes[1:]:
                    if shape["type"] == "rect":
                        itemShapes.append(createRectItem(shape, gridTuple))
                    elif shape["type"] == "circle":
                        itemShapes.append(createCircleItem(shape, gridTuple))
                    elif shape["type"] == "line":
                        itemShapes.append(createLineItem(shape, gridTuple))
                    elif shape["type"] == "pin":
                        itemShapes.append(createPinItem(shape, gridTuple))
                    elif shape["type"] == "label":
                        itemShapes.append(createLabelItem(shape, gridTuple))
                    # just recreate attributes dictionary
                    elif shape["type"] == "attribute":
                        symbolAttributes[shape["name"]] = shape["definition"]
            except json.decoder.JSONDecodeError:
                print("Error: Invalid Symbol file")
        symbolInstance = shp.symbolShape(draftPen, gridTuple, itemShapes,
            symbolAttributes)
        symbolInstance.libraryName = item["library"]
        symbolInstance.cellName = item["cell"]
        symbolInstance.counter = instCounter
        symbolInstance.instanceName = item["name"]
        symbolInstance.angle = item["angle"]
        symbolInstance.viewName = "symbol"
        symbolInstance.attr = symbolAttributes
        for label in symbolInstance.labels.values():
            if label.labelName in labelDict.keys():
                label.labelValue = labelDict[label.labelName][0]
                label.labelVisible = labelDict[label.labelName][1]
                label.labelDefs()
        symbolInstance.setPos(item["location"][0], item["location"][1])
        return symbolInstance

def createSchematicNets(item):
    """
    Create schematic items from json file.
    """
    if item["type"] == "schematicNet":
        start = QPoint(item["start"][0], item["start"][1])
        end = QPoint(item["end"][0], item["end"][1])
        position = QPoint(item["location"][0], item["location"][1])
        penStyle = Qt.PenStyle.__dict__[item["lineStyle"]]
        penWidth = item["width"]
        penColor = QColor(*item["color"])
        pen = QPen(penColor, penWidth, penStyle)
        pen.setCosmetic(item["cosmetic"])
        netItem = net.schematicNet(start, end, pen)
        netItem.name = item["name"]
        netItem.nameSet = item["nameSet"]
        netItem.setPos(position)
        return netItem


def createSchematicPins(item, gridTuple):
    """
    Create schematic items from json file.
    """
    if item["type"] == "schematicPin":
        start = QPoint(item["start"][0], item["start"][1])
        penStyle = Qt.PenStyle.__dict__[item["lineStyle"]]
        penWidth = item["width"]
        penColor = QColor(*item["color"])
        pen = QPen(penColor, penWidth, penStyle)
        pen.setCosmetic(item["cosmetic"])
        pinName = item["pinName"]
        pinDir = item["pinDir"]
        pinType = item["pinType"]
        pinItem = shp.schematicPin(start, pen, pinName, pinDir, pinType, gridTuple)
        pinItem.setPos(QPoint(item["location"][0], item["location"][1]))
        pinItem.angle = item["angle"]
        return pinItem
