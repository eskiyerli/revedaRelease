import json
from collections import namedtuple
import revedaeditor.common.shape as shp
import revedaeditor.common.net as net

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
                        "color": item.pen.color().toTuple(),
                        "width": item.pen.width(),
                        "lineStyle": str(item.pen.style()).split('.')[-1],
                        "cosmetic": item.pen.isCosmetic(),
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "angle": item.angle, }
            return itemDict
        elif isinstance(item, shp.line):
            itemDict = {"type": "line",
                        "start": item.start.toTuple(),
                        "end": item.end.toTuple(),
                        "color": item.pen.color().toTuple(),
                        "width": item.pen.width(),
                        "lineStyle": str(item.pen.style()).split('.')[-1],
                        "cosmetic": item.pen.isCosmetic(),
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "angle": item.angle, }
            return itemDict
        elif isinstance(item, shp.circle):
            itemDict = {"type": "circle",
                        "centre": item.centre.toTuple(),
                        "end": item.end.toTuple(),
                        "color": item.pen.color().toTuple(),
                        "width": item.pen.width(),
                        "lineStyle": str(item.pen.style()).split('.')[-1],
                        "cosmetic": item.pen.isCosmetic(),
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "angle": item.angle, }
            return itemDict
        elif isinstance(item, shp.pin):
            itemDict = {"type": "pin",
                        "start": item.start.toTuple(),
                        "color": item.pen.color().toTuple(),
                        "width": item.pen.width(),
                        "lineStyle": str(item.pen.style()).split('.')[-1],
                        "cosmetic": item.pen.isCosmetic(),
                        "name": item.pinName,
                        "dir": item.pinDir,
                        "pinType": item.pinType,
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "angle": item.angle, }
            return itemDict
        elif isinstance(item, shp.label):
            itemDict = {"type": "label",
                        "start": item.start.toTuple(),
                        "color": item.pen.color().toTuple(),
                        "width": item.pen.width(),
                        "lineStyle": str(item.pen.style()).split('.')[-1],
                        "cosmetic": item.pen.isCosmetic(),
                        "name": item.labelName,
                        "definition": item.labelDefinition,
                        # label as entered
                        "text": item.labelText,  # shown label
                        "value": item.labelValue,     # label value
                        "visible": item.labelVisible,     # label visibility
                        "labelType": item.labelType,
                        "height": item.labelHeight,
                        "align": item.labelAlign,
                        "orient": item.labelOrient,
                        "use": item.labelUse,
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "angle": item.angle,}
            return itemDict
        elif isinstance(item, symbolAttribute):
            itemDict = {"type": "attribute", "name": item.name,
                        "definition": item.definition, }
            return itemDict


class schematicEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, shp.symbolShape):
            # only value and visibility be changed in the symbol instance.

            itemLabelDict = {
                item.labelName: [item.labelValue, item.labelVisible] for item
                in item.labels.values()}
            itemDict = {"type": "symbolShape",
                        "library": item.libraryName,
                        "cell": item.cellName,
                        "view": item.viewName,
                        "name": item.instanceName,
                        "instCounter": item.counter,
                        "labelDict": itemLabelDict,
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "angle": item.angle, }
            return itemDict
        elif isinstance(item, net.schematicNet):
            itemDict = {"type": "schematicNet",
                        "start": item.start.toTuple(),
                        "end": item.end.toTuple(),
                        "color": item.pen.color().toTuple(),
                        "width": item.pen.width(),
                        "lineStyle": str(item.pen.style()).split('.')[-1],
                        "cosmetic": item.pen.isCosmetic(),
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "name": item.name,
                        "nameSet": item.nameSet, }
            return itemDict
        elif isinstance(item, shp.schematicPin):
            itemDict = {"type": "schematicPin",
                        "start": item.start.toTuple(),
                        "color": item.pen.color().toTuple(),
                        "width": item.pen.width(),
                        "lineStyle": str(item.pen.style()).split('.')[-1],
                        "cosmetic": item.pen.isCosmetic(),
                        "pinName": item.pinName,
                        "pinDir": item.pinDir,
                        "pinType": item.pinType,
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "angle": item.angle, }
            return itemDict
