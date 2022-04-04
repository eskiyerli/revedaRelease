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
import pathlib

from PySide6.QtCore import (QDir, QLine, QRect, QRectF, QPoint, QPointF, QSize,
                            Qt, )  # QtCore
from PySide6.QtGui import (QAction, QKeySequence, QColor, QFont, QIcon,
                           QPainter, QPen, )
from PySide6.QtWidgets import (QGraphicsItem, )

import shape as shp
import symbolEncoder as se
import json


def createSymbolItems(item, gridTuple):
    '''
    Create symbol items from json file.
    '''
    if item["type"] == "rect":
        start = QPoint(item["rect"][0], item["rect"][1])
        end = QPoint(item["rect"][2], item["rect"][3])
        penStyle = Qt.PenStyle.__dict__[
            item["lineStyle"].split(".")[-1]]  # convert string to enum
        penWidth = item["width"]
        penColor = QColor(*item["color"])
        pen = QPen(penColor, penWidth, penStyle)
        pen.setCosmetic(item["cosmetic"])
        rect = shp.rectangle(start, end, pen,
                             gridTuple)  # note that we are using grid values for scene
        rect.setPos(QPoint(item["location"][0], item["location"][1]), )
        return rect
    elif item["type"] == "line":
        start = QPoint(item["start"][0], item["start"][1])
        end = QPoint(item["end"][0], item["end"][1])
        penStyle = Qt.PenStyle.__dict__[item["lineStyle"].split(".")[-1]]
        penWidth = item["width"]
        penColor = QColor(*item["color"])
        pen = QPen(penColor, penWidth, penStyle)
        pen.setCosmetic(item["cosmetic"])
        line = shp.line(start, end, pen, gridTuple)
        line.setPos(QPoint(item["location"][0], item["location"][1]))
        return line
    elif item["type"] == "pin":
        start = QPoint(item["start"][0], item["start"][1])
        penStyle = Qt.PenStyle.__dict__[item["lineStyle"].split(".")[-1]]
        penWidth = item["width"]
        penColor = QColor(*item["color"])
        pen = QPen(penColor, penWidth, penStyle)
        pen.setCosmetic(item["cosmetic"])
        pin = shp.pin(
            start,
            pen,
            item["pinName"],
            item["pinDir"],
            item["pinType"],
            gridTuple,
        )
        pin.setPos(QPoint(item["location"][0], item["location"][1]))
        return pin
    elif item["type"] == "label":
        start = QPoint(item["start"][0], item["start"][1])
        penStyle = Qt.PenStyle.__dict__[item["lineStyle"].split(".")[-1]]
        penWidth = item["width"]
        penColor = QColor(*item["color"])
        pen = QPen(penColor, penWidth, penStyle)
        pen.setCosmetic(item["cosmetic"])
        label = shp.label(
            start,
            pen,
            item["labelName"],
            gridTuple,
            item["labelType"],
            item["labelHeight"],
            item["labelAlign"],
            item["labelOrient"],
            item["labelUse"],
        )
        label.setPos(QPoint(item["location"][0], item["location"][1]))
        return label


def createSymbolAttribute(item):
    if item["type"] == "attribute":
        return se.symbolAttribute(item["name"], item["attributeType"],
                                  item["definition"])


def createSchematicItems(item, libraryDict, viewName, gridTuple):
    '''
    Create schematic items from json file.
    '''
    if item["type"] == "symbolShape":
        position = QPoint(item["location"][0], item["location"][1])
        library = pathlib.Path(libraryDict[item["library"]])
        name = item["name"]
        instCounter = item["instCounter"]
        itemAttributes = {}
        itemShapes = []
        draftPen = QPen(QColor("white"), 1)
        file = library.joinpath(name, viewName + '.json')
        print(file)
        with open(file, 'r') as temp:
            try:
                shapes = json.load(temp)
                for shape in shapes:
                    if (shape["type"] == "rect" or shape["type"] == "line" or
                            shape["type"] == "pin" or shape[
                                "type"] == "label"):
                        # append recreated shapes to items list
                        itemShapes.append(
                            createSymbolItems(shape, gridTuple))
                    # elif item["type"] == "attribute":
                    #     itemAttributes[item["name"]] = [item["attributeType"],
                    #                                     item["definition"]]
                symbolInstance = shp.symbolShape(draftPen, gridTuple,
                                                 *itemShapes, **itemAttributes)
                symbolInstance.pinLocations = {}
            except json.decoder.JSONDecodeError:
                print("Error: Invalid Symbol file")
        for child in symbolInstance.childItems():
            if type(child) is shp.label and child.labelType == "NLPLabel":
                if child.labelName == '[@cellName]':
                    child.setText(str(file.parent.stem))
                elif child.labelName == '[@instName]':
                    child.setText(f'I{item["instCounter"]}')
                #     elif type(child) is shp.pin:
                #         symbolInstance.pinLocations[
                #             child.pinName] = child.start + child.pos().toPoint()
        symbolInstance.setPos(position)
        symbolInstance.setData(0, library)
        symbolInstance.setData(1, name)
        symbolInstance.setData(2, instCounter)
        return symbolInstance
