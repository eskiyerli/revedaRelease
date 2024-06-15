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
import inspect
import os
from dotenv import load_dotenv
load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):
    import pdk.layoutLayers as laylyr
else:
    import defaultPDK.layoutLayers as laylyr

import revedaEditor.common.layoutShapes as lshp


class layoutEncoder(json.JSONEncoder):
    def default(self, item):
        match type(item):
            case lshp.layoutInstance:
                itemDict = {
                    "type": "Inst",
                    "lib": item.libraryName,
                    "cell": item.cellName,
                    "view": item.viewName,
                    "nam": item.instanceName,
                    "ic": item.counter,
                    "loc": (item.scenePos() - item.scene().origin).toTuple(),
                    "ang": item.angle,
                }
            case lshp.layoutRect:
                itemDict = {
                    "type": "Rect",
                    "tl": item.mapToScene(item.rect.topLeft()).toTuple(),
                    "br": item.mapToScene(item.rect.bottomRight()).toTuple(),
                    "ang": item.angle,
                    "ln": laylyr.pdkAllLayers.index(item.layer),
                }
            case lshp.layoutPath:
                itemDict = {
                    "type": "Path",
                    "dfl1": item.mapToScene(item.draftLine.p1()).toTuple(),
                    "dfl2": item.mapToScene(item.draftLine.p2()).toTuple(),
                    "ln": laylyr.pdkDrawingLayers.index(item.layer),
                    "w": item.width,
                    "se": item.startExtend,
                    "ee": item.endExtend,
                    "md": item.mode,
                    "nam": item.name,
                    "ang": item.angle,
                }
            case lshp.layoutViaArray:
                viaDict = {
                    "st": item.via.mapToScene(item.via.start).toTuple(),
                    "vdt": item.via.viaDefTuple.name,
                    "w": item.via.width,
                    "h": item.via.height,
                    "ang": item.angle,
                }
                itemDict = {
                    "type": "Via",
                    "st": item.mapToScene(item.start).toTuple(),
                    "via": viaDict,
                    "xs": item.xs,
                    "ys": item.ys,
                    "xn": item.xnum,
                    "yn": item.ynum,
                }
            case lshp.layoutPin:
                itemDict = {
                    "type": "Pin",
                    "tl": item.mapToScene(item.rect.topLeft()).toTuple(),
                    "br": item.mapToScene(item.rect.bottomRight()).toTuple(),
                    "pn": item.pinName,
                    "pd": item.pinDir,
                    "pt": item.pinType,
                    "ln": laylyr.pdkPinLayers.index(item.layer),
                    "ang": item.angle,
                }
            case lshp.layoutLabel:
                itemDict = {
                    "type": "Label",
                    "st": item.mapToScene(item.start).toTuple(),
                    "lt": item.labelText,
                    "ff": item.fontFamily,
                    "fs": item.fontStyle,
                    "fh": item.fontHeight,
                    "la": item.labelAlign,
                    "lo": item.labelOrient,
                    "ln": laylyr.pdkTextLayers.index(item.layer),
                    "ang": item.angle,
                }
            case lshp.layoutPolygon:
                pointsList = [item.mapToScene(point).toTuple() for point in item.points]
                itemDict = {
                    "type": "Polygon",
                    "ps": pointsList,
                    "ln": laylyr.pdkAllLayers.index(item.layer),
                    "ang": item.angle,
                }
            case lshp.layoutRuler:
                itemDict = {
                    "type": "Ruler",
                    "dfl1": item.mapToScene(item.draftLine.p1()).toTuple(),
                    "dfl2": item.mapToScene(item.draftLine.p2()).toTuple(),
                    "md": item.mode,
                    "ang": item.angle,
                }
            case _:  # now check super class types:
                match item.__class__.__bases__[0]:
                    case baseCell:
                        init_args = inspect.signature(
                            item.__class__.__init__
                        ).parameters
                        args_used = [param for param in init_args if (param != "self")]

                        argDict = {arg: getattr(item, arg) for arg in args_used}
                        itemDict = {
                            "type": "Pcell",
                            "lib": item.libraryName,
                            "cell": item.cellName,
                            "view": item.viewName,
                            "nam": item.instanceName,
                            "ic": item.counter,
                            "loc": (item.scenePos() - item.scene().origin).toTuple(),
                            "ang": item.angle,
                            "params": argDict,
                        }
        return itemDict
