#    “Commons Clause” License Condition v1.0
#   #
#    The Software is provided to you by the Licensor under the License, as defined
#    below, subject to the following condition.
#
#    Without limiting other conditions in the License, the grant of rights under the
#    License will not include, and the License does not grant to you, the right to
#    Sell the Software.
#
#    For purposes of the foregoing, “Sell” means practicing any or all of the rights
#    granted to you under the License to provide to third parties, for a fee or other
#    consideration (including without limitation fees for hosting or consulting/
#    support services related to the Software), a product or service whose value
#    derives, entirely or substantially, from the functionality of the Software. Any
#    license notice or attribution required by the License must also include this
#    Commons Clause License Condition notice.
#
#   Add-ons and extensions developed for this software may be distributed
#   under their own separate licenses.
#
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
#

import json

import revedaEditor.common.shapes as shp
import revedaEditor.common.labels as lbl


class symbolAttribute(object):
    def __init__(self, name: str, definition: str):
        self._name = name
        self._definition = definition

    def __str__(self):
        return f"{self.name}: {self.definition}"

    def __repr__(self):
        return f"{type(self)}({self.name},{self.definition})"

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        assert isinstance(value, str)
        self._name = value

    @property
    def definition(self):
        return self._definition

    @definition.setter
    def definition(self, value):
        assert isinstance(value, str)
        self._definition = value


class symbolEncoder(json.JSONEncoder):
    def default(self, item):
        match type(item):
            case shp.symbolRectangle:
                itemDict = {
                    "type": "rect",
                    "rect": item.rect.getCoords(),
                    "loc": (item.scenePos() - item.scene().origin).toTuple(),
                    "ang": item.angle,
                }
                return itemDict
            case shp.symbolLine:
                itemDict = {
                    "type": "line",
                    "st": item.start.toTuple(),
                    "end": item.end.toTuple(),
                    "loc": (item.scenePos() - item.scene().origin).toTuple(),
                    "ang": item.angle,
                }
                return itemDict
            case shp.symbolCircle:
                itemDict = {
                    "type": "circle",
                    "cen": item.centre.toTuple(),
                    "end": item.end.toTuple(),
                    "loc": (item.scenePos() - item.scene().origin).toTuple(),
                    "ang": item.angle,
                }
                return itemDict
            case shp.symbolPolygon:
                pointsList = [item.mapToScene(point).toTuple() for point in item.points]
                itemDict = {
                    "type": "polygon",
                    "ps": pointsList,
                }
                return itemDict
            case shp.symbolArc:
                itemDict = {
                    "type": "arc",
                    "st": item.start.toTuple(),
                    "end": item.end.toTuple(),
                    "loc": (item.scenePos() - item.scene().origin).toTuple(),
                    "ang": item.angle,
                }
                return itemDict
            case shp.symbolPin:
                itemDict = {
                    "type": "pin",
                    "st": item.start.toTuple(),
                    "nam": item.pinName,
                    "pd": item.pinDir,
                    "pt": item.pinType,
                    "loc": (item.scenePos() - item.scene().origin).toTuple(),
                    "ang": item.angle,
                }
                return itemDict
            case shp.text:
                itemDict = {
                    "type": "text",
                    "st": item.start.toTuple(),
                    "tc": item.textContent,
                    "ff": item.fontFamily,
                    "fs": item.fontStyle,
                    "th": item.textHeight,
                    "ta": item.textAlignment,
                    "to": item.textOrient,
                    "loc": (item.scenePos() - item.scene().origin).toTuple(),
                    "ang": item.angle,
                }
                return itemDict
            case lbl.symbolLabel:
                itemDict = {
                    "type": "label",
                    "st": item.start.toTuple(),
                    "nam": item.labelName,
                    "def": item.labelDefinition,  # label as entered
                    "txt": item.labelText,  # shown label
                    "val": item.labelValue,  # label value
                    "vis": item.labelVisible,  # label visibility
                    "lt": item.labelType,
                    "ht": item.labelHeight,
                    "al": item.labelAlign,
                    "or": item.labelOrient,
                    "use": item.labelUse,
                    "loc": (item.scenePos() - item.scene().origin).toTuple(),
                }
                return itemDict
            case symbolAttribute:
                itemDict = {
                    "type": "attr",
                    "nam": item.name,
                    "def": item.definition,
                }
                return itemDict
