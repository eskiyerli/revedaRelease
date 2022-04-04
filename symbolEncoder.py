import json
import shape as shp
from PySide6.QtCore import (QDir, QLine, QRect, QRectF, QPoint, QPointF, QSize, )
from PySide6.QtGui import (QAction, QKeySequence, QColor, QFont, QIcon, QPainter, QPen, QBrush, QFontMetrics,
                           QStandardItemModel, QTransform, QCursor, QUndoCommand, QUndoStack)

class symbolAttribute(object):
    def __init__(self, name:str,  type:str, definition:str):   # type: str, str, str
        self.name = name
        self.type = type
        self.definition = definition

    def __str__(self):
        return f'{self.name}: {self.type}  {self.definition}'

    def __repr__(self):
        return f'{self.name}: {self.type}  {self.definition}'

class symbolEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, shp.rectangle):
            itemDict = {
                "type": "rect",
                "rect": item.__dict__["rect"].getCoords(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "location": (item.scenePos()-item.scene().origin).toTuple(),
            }
            return itemDict
        elif isinstance(item, shp.line):
            itemDict = {
                "type": "line",
                "start": item.__dict__["start"].toTuple(),
                "end": item.__dict__["end"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "location": (item.scenePos()-item.scene().origin).toTuple(),
            }
            return itemDict
        elif isinstance(item, shp.pin):
            itemDict = {
                "type": "pin",
                "start": item.__dict__["start"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "pinName": item.__dict__["pinName"],
                "pinDir": item.__dict__["pinDir"],
                "pinType": item.__dict__["pinType"],
                "location": (item.scenePos()-item.scene().origin).toTuple(),
            }
            return itemDict
        elif isinstance(item, shp.label):
            itemDict = {
                "type": "label",
                "start": item.__dict__["start"].toTuple(),
                "color": item.__dict__["pen"].color().toTuple(),
                "width": item.__dict__["pen"].width(),
                "lineStyle": str(item.__dict__["pen"].style()),
                "cosmetic": item.__dict__["pen"].isCosmetic(),
                "labelName": item.__dict__["labelName"],
                "labelType": item.__dict__["labelType"],
                "labelHeight": item.__dict__["labelHeight"],
                "labelAlign": item.__dict__["labelAlign"],
                "labelOrient": item.__dict__["labelOrient"],
                "labelUse": item.__dict__["labelUse"],
                "location": (item.scenePos()-item.scene().origin).toTuple(),
            }
            return itemDict
        elif isinstance(item, symbolAttribute):
            itemDict = {
                "type": "attribute",
                "name": item.name,
                "attributeType": item.type,
                "definition": item.definition,
            }
            return itemDict

class schematicEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, shp.symbolShape):
            itemDict = {
                "type": "symbolShape",
                "library": str(item.data(0).stem),
                "name": str(item.data(1)),
                "instCounter": item.data(2),
                "location": (item.scenePos()-item.scene().origin).toTuple(),
            }
            return itemDict


