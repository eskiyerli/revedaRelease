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

# Load symbol and maybe later schematic from json file.
# import pathlib

import json

from PySide6.QtCore import (QPoint, Qt, )  # QtCore
from PySide6.QtGui import (QColor, QPen, )

import common.shape as shp
import fileio.symbolEncoder as se
import common.net as net
import common.pens as pens


def createSymbolItems(item, gridTuple):
    """
    Create symbol items from json file.
    """
    if item["type"] == "rect":
        return createRectItem(item, gridTuple)
    elif item["type"] == "circle":
        return createCircleItem(item, gridTuple)
    elif item["type"] == "arc":
        return createArcItem(item, gridTuple)
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
    pen = pens.pen.returnPen(item['pen'])
    rect = shp.rectangle(start, end, pen,
                         gridTuple)  # note that we are using grid values for scene
    rect.setPos(QPoint(item["loc"][0], item["loc"][1]), )
    rect.angle = item["ang"]
    return rect


def createCircleItem(item, gridTuple):
    centre = QPoint(item["cen"][0], item["cen"][1])
    end = QPoint(item["end"][0], item["end"][1])
    pen = pens.pen.returnPen(item['pen'])
    circle = shp.circle(centre, end, pen,
                        gridTuple)  # note that we are using grid values for scene
    circle.setPos(QPoint(item["loc"][0], item["loc"][1]), )
    circle.angle = item["ang"]
    return circle


def createArcItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    end = QPoint(item["end"][0], item["end"][1])
    pen = pens.pen.returnPen(item['pen'])
    arc = shp.arc(start, end, pen,
                  gridTuple)  # note that we are using grid values for scene
    arc.setPos(QPoint(item["loc"][0], item["loc"][1]))
    arc.angle = item["ang"]
    return arc


def createLineItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    end = QPoint(item["end"][0], item["end"][1])
    pen = pens.pen.returnPen(item['pen'])
    line = shp.line(start, end, pen, gridTuple)
    line.setPos(QPoint(item["loc"][0], item["loc"][1]))
    line.angle = item["ang"]
    return line


def createPinItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    pen = pens.pen.returnPen(item['pen'])
    pin = shp.pin(start, pen, item["nam"], item["pd"], item["pt"], gridTuple, )
    pin.setPos(QPoint(item["loc"][0], item["loc"][1]))
    pin.angle = item["ang"]
    return pin


def createLabelItem(item, gridTuple):
    start = QPoint(item["st"][0], item["st"][1])
    pen = pens.pen.returnPen(item['pen'])
    label = shp.label(start, pen, item["def"], gridTuple, item["lt"], item["ht"],
                      item["al"], item["or"], item["use"], )
    label.setPos(QPoint(item["loc"][0], item["loc"][1]))
    label.angle = item["ang"]
    label.labelName = item["nam"]
    label.labelText = item["txt"]
    label.labelVisible = item["vis"]
    label.labelValue = item["val"]
    return label


def createTextItem(item, gridTuple: (int, int)):
    start = QPoint(item["st"][0], item["st"][1])
    pen = pens.pen.returnPen(item['pen'])
    text = shp.text(start, pen, item['tc'], gridTuple, item['ff'], item['fs'],
                    item['th'], item['ta'], item['to'])
    text.setPos(QPoint(item["loc"][0], item["loc"][1]))
    return text


def createSymbolAttribute(item):
    if item["type"] == "attr":
        return se.symbolAttribute(item["nam"], item["def"])


def createSchematicItems(item, libraryDict, viewName: str, gridTuple: (int, int)):
    """
    Create schematic items from json file.
    """
    if item["type"] == "symbolShape":
        libraryPath = libraryDict.get(item["lib"])
        if libraryPath is None:
            print(f'{item["lib"]} cannot be found.')
            return None
        cell = item["cell"]
        instCounter = item["ic"]
        itemShapes = list()
        symbolAttributes = dict()
        labelDict = item["ld"]
        draftPen = pens.pen.returnPen('draftPen')
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
                    elif shape["type"] == "arc":
                        itemShapes.append(createArcItem(shape, gridTuple))
                    elif shape["type"] == "line":
                        itemShapes.append(createLineItem(shape, gridTuple))
                    elif shape["type"] == "pin":
                        itemShapes.append(createPinItem(shape, gridTuple))
                    elif shape["type"] == "label":
                        itemShapes.append(createLabelItem(shape, gridTuple))
                    # just recreate attributes dictionary
                    elif shape["type"] == "attr":
                        symbolAttributes[shape["nam"]] = shape["def"]
            except json.decoder.JSONDecodeError:
                print("Error: Invalid Symbol file")
        symbolInstance = shp.symbolShape(draftPen, gridTuple, itemShapes,
                                         symbolAttributes)
        symbolInstance.libraryName = item["lib"]
        symbolInstance.cellName = item["cell"]
        symbolInstance.counter = instCounter
        symbolInstance.instanceName = item["nam"]
        symbolInstance.angle = item["ang"]
        symbolInstance.viewName = "symbol"
        symbolInstance.attributes = symbolAttributes
        for label in symbolInstance.labels.values():
            if label.labelName in labelDict.keys():
                label.labelValue = labelDict[label.labelName][0]
                label.labelVisible = labelDict[label.labelName][1]
                label.labelDefs()
        symbolInstance.setPos(item["loc"][0], item["loc"][1])
        return symbolInstance


def createSchematicNets(item):
    """
    Create schematic items from json file.
    """
    if item["type"] == "schematicNet":
        start = QPoint(item["st"][0], item["st"][1])
        end = QPoint(item["end"][0], item["end"][1])
        position = QPoint(item["loc"][0], item["loc"][1])
        pen = pens.pen.returnPen(item['pen'])
        netItem = net.schematicNet(start, end, pen)
        netItem.name = item["nam"]
        netItem.nameSet = item["ns"]
        netItem.setPos(position)
        return netItem


def createSchematicPins(item, gridTuple):
    """
    Create schematic items from json file.
    """
    if item["type"] == "schematicPin":
        start = QPoint(item["st"][0], item["st"][1])
        pen = pens.pen.returnPen(item['pen'])
        pinName = item["pn"]
        pinDir = item["pd"]
        pinType = item["pt"]
        pinItem = shp.schematicPin(start, pen, pinName, pinDir, pinType,
                                   gridTuple)
        pinItem.setPos(QPoint(item["loc"][0], item["loc"][1]))
        pinItem.angle = item["ang"]
        return pinItem
