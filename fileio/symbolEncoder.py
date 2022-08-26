import json

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
                        "lineStyle": str(item.pen.style()),
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
                        "lineStyle": str(item.pen.style()),
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
                        "lineStyle": str(item.pen.style()),
                        "cosmetic": item.pen.isCosmetic(),
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "angle": item.angle, }
            return itemDict
        elif isinstance(item, shp.pin):
            itemDict = {"type": "pin",
                        "start": item.start.toTuple(),
                        "color": item.pen.color().toTuple(),
                        "width": item.pen.width(),
                        "lineStyle": str(item.pen.style()),
                        "cosmetic": item.pen.isCosmetic(),
                        "pinName": item.pinName,
                        "pinDir": item.pinDir,
                        "pinType": item.pinType,
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "angle": item.angle, }
            return itemDict
        elif isinstance(item, shp.label):
            itemDict = {"type": "label",
                        "start": item.start.toTuple(),
                        "color": item.pen.color().toTuple(),
                        "width": item.pen.width(),
                        "lineStyle": str(item.pen.style()),
                        "cosmetic": item.pen.isCosmetic(),
                        "labelName": item.labelName,
                        "labelDefinition": item.labelDefinition,
                        # label as entered
                        "labelText": item.labelText,  # shown label
                        "labelType": item.labelType,
                        "labelHeight": item.labelHeight,
                        "labelAlign": item.labelAlign,
                        "labelOrient": item.labelOrient,
                        "labelUse": item.labelUse,
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "angle": item.angle, }
            return itemDict
        elif isinstance(item, symbolAttribute):
            itemDict = {"type": "attribute", "name": item.name,
                        "definition": item.definition, }
            return itemDict


class schematicEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, shp.symbolShape):
            # only label name, definition, and text can be changed in the symbol instance.
            itemLabelDict = {
                item.labelName: [item.labelDefinition, item.labelText] for item
                in item.labels}
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
                        "lineStyle": str(item.pen.style()),
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
                        "lineStyle": str(item.pen.style()),
                        "cosmetic": item.pen.isCosmetic(),
                        "pinName": item.pinName,
                        "pinDir": item.pinDir,
                        "pinType": item.pinType,
                        "location": (item.scenePos() - item.scene().origin).toTuple(),
                        "angle": item.angle, }
            return itemDict
