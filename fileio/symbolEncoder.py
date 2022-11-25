import json
from collections import namedtuple
import common.shape as shp
import common.net as net

from PySide6.QtCore import (QDir, QLine, QRect, QRectF, QPoint, QPointF,
                            QSize, )
from PySide6.QtGui import (QAction, QKeySequence, QColor, QFont, QIcon,
                           QPainter, QPen, QBrush, QFontMetrics,
                           QStandardItemModel, QTransform, QCursor,
                           QUndoCommand, QUndoStack, )


class symbolAttribute(object):
    def __init__(self, name: str, definition: str):
        self.name = name
        self.definition = definition

    def __str__(self):
        return f'{self.name}: {self.definition}'

    def __repr__(self):
        return f'{self.name}:  {self.definition}'


class symbolEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, shp.rectangle):
            itemDict = {"type": "rect",
                        "rect": item.rect.getCoords(),
                        "pen" : item.pen.pname,
                        "loc": (item.scenePos() - item.scene().origin).toTuple(),
                        "ang": item.angle, }
            return itemDict
        elif isinstance(item, shp.line):
            itemDict = {"type": "line",
                        "st": item.start.toTuple(),
                        "end": item.end.toTuple(),
                        "pen": item.pen.pname,
                        "loc": (item.scenePos() - item.scene().origin).toTuple(),
                        "ang": item.angle, }
            return itemDict
        elif isinstance(item, shp.circle):
            itemDict = {"type": "circle",
                        "cen": item.centre.toTuple(),
                        "end": item.end.toTuple(),
                        "pen": item.pen.pname,
                        "loc": (item.scenePos() - item.scene().origin).toTuple(),
                        "ang": item.angle, }
            return itemDict
        elif isinstance(item, shp.pin):
            itemDict = {"type": "pin",
                        "st": item.start.toTuple(),
                        "pen": item.pen.pname,
                        "nam": item.pinName,
                        "pd": item.pinDir,
                        "pt": item.pinType,
                        "loc": (item.scenePos() - item.scene().origin).toTuple(),
                        "ang": item.angle, }
            return itemDict
        elif isinstance(item,shp.text):
            itemDict = {"type": "text",
                        "st": item.start.toTuple(),
                        "pen": item.pen.pname,
                        'tc': item.textContent,
                        'ff': item.fontFamily,
                        'fs': item.fontStyle,
                        'th': item.textHeight,
                        'ta': item.textAlignment,
                        'to': item.textOrient,
                        }
            return itemDict
        elif isinstance(item, shp.label):
            itemDict = {"type": "label",
                        "st": item.start.toTuple(),
                        "pen": item.pen.pname,
                        "nam": item.labelName,
                        "def": item.labelDefinition,
                        # label as entered
                        "txt": item.labelText,  # shown label
                        "val": item.labelValue,     # label value
                        "vis": item.labelVisible,     # label visibility
                        "lt": item.labelType,
                        "ht": item.labelHeight,
                        "al": item.labelAlign,
                        "or": item.labelOrient,
                        "use": item.labelUse,
                        "loc": (item.scenePos() - item.scene().origin).toTuple(),
                        "ang": item.angle,}
            return itemDict
        elif isinstance(item, symbolAttribute):
            itemDict = {"type": "attr",
                        "nam": item.name,
                        "def": item.definition, }
            return itemDict


class schematicEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, shp.symbolShape):
            # only value and visibility be changed in the symbol instance.

            itemLabelDict = {
                item.labelName: [item.labelValue, item.labelVisible] for item
                in item.labels.values()}
            itemDict = {"type": "symbolShape",
                        "lib": item.libraryName,
                        "cell": item.cellName,
                        "view": item.viewName,
                        "nam": item.instanceName,
                        "ic": item.counter,
                        "ld": itemLabelDict,
                        "loc": (item.scenePos() - item.scene().origin).toTuple(),
                        "ang": item.angle, }
            return itemDict
        elif isinstance(item, net.schematicNet):
            itemDict = {"type": "schematicNet",
                        "st": item.start.toTuple(),
                        "end": item.end.toTuple(),
                        "pen": item.pen.pname,
                        "loc": (item.scenePos() - item.scene().origin).toTuple(),
                        "nam": item.name,
                        "ns": item.nameSet, }
            return itemDict
        elif isinstance(item, shp.schematicPin):
            itemDict = {"type": "schematicPin",
                        "st": item.start.toTuple(),
                        "pen": item.pen.pname,
                        "pn": item.pinName,
                        "pd": item.pinDir,
                        "pt": item.pinType,
                        "loc": (item.scenePos() - item.scene().origin).toTuple(),
                        "ang": item.angle, }
            return itemDict
        elif isinstance(item,shp.text):
            itemDict = {"type": "text",
                        "st": item.start.toTuple(),
                        "pen": item.pen.pname,
                        'tc': item.textContent,
                        'ff': item.fontFamily,
                        'fs': item.fontStyle,
                        'th': item.textHeight,
                        'ta': item.textAlignment,
                        'to': item.textOrient,
                        }
            return itemDict