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
                "rect": item.__dict__["rect"].getCoords(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "location": (item.scenePos() - item.scene().origin).toTuple(),
                "angle": item.__dict__["angle"],}
            return itemDict
        elif isinstance(item, shp.line):
            itemDict = {"type": "line",
                "start": item.__dict__["start"].toTuple(),
                "end": item.__dict__["end"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "location": (item.scenePos() - item.scene().origin).toTuple(),
                "angle": item.__dict__["angle"], }
            return itemDict
        elif isinstance(item, shp.circle):
            itemDict = {"type": "circle",
                "centre": item.__dict__["centre"].toTuple(),
                "end": item.__dict__["end"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "location": (item.scenePos() - item.scene().origin).toTuple(),
                "angle": item.__dict__["angle"], }
            return itemDict
        elif isinstance(item, shp.pin):
            itemDict = {"type": "pin",
                "start": item.__dict__["start"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "pinName": item.__dict__["pinName"],
                "pinDir": item.__dict__["pinDir"],
                "pinType": item.__dict__["pinType"],
                "location": (item.scenePos() - item.scene().origin).toTuple(),
                "angle": item.__dict__["angle"], }

            return itemDict
        elif isinstance(item, shp.label):
            itemDict = {"type": "label",
                "start": item.__dict__["start"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "labelName": item.__dict__["_labelName"],
                "labelDefinition": item.__dict__["_labelDefinition"],
                # label as entered
                "labelText": item.__dict__["_labelText"],  # shown label
                "labelType": item.__dict__["_labelType"],
                "labelHeight": item.__dict__["_labelHeight"],
                "labelAlign": item.__dict__["_labelAlign"],
                "labelOrient": item.__dict__["_labelOrient"],
                "labelUse": item.__dict__["_labelUse"],
                "location": (item.scenePos() - item.scene().origin).toTuple(),
                "angle": item.__dict__["angle"], }
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
                "library": item.__dict__["libraryName"],
                "cell": item.__dict__["cellName"],
                "view": item.__dict__["viewName"],
                "name": item.__dict__["instanceName"],
                "instCounter": item.__dict__["counter"],
                # "pinLocations": item.__dict__["pinLocations"],
                # "attributes": item.__dict__["attr"],
                "labelDict": itemLabelDict,
                "location": (item.scenePos() - item.scene().origin).toTuple(),
                "angle": item.__dict__["angle"],}
            return itemDict
        elif isinstance(item, net.schematicNet):
            itemDict = {"type": "schematicNet",
                "start": item.__dict__["start"].toTuple(),
                "end": item.__dict__["end"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "location": (item.scenePos() - item.scene().origin).toTuple(),
                "name": item.__dict__["name"],
                "nameSet": item.__dict__["nameSet"], }
            return itemDict
        elif isinstance(item, shp.schematicPin):
            itemDict = {"type": "schematicPin",
                "start": item.__dict__["start"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "pinName": item.__dict__["pinName"],
                "pinDir": item.__dict__["pinDir"],
                "pinType": item.__dict__["pinType"],
                "location": (item.scenePos() - item.scene().origin).toTuple(),
                "angle": item.__dict__["angle"],}
            return itemDict
