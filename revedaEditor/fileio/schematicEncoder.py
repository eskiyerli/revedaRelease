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

import revedaEditor.common.net as net
import revedaEditor.common.shapes as shp


class schematicEncoder(json.JSONEncoder):
    def default(self, item):
        if isinstance(item, shp.schematicSymbol):
            # if item was drawn as a draft, then just carry the labels
            if item.draft:
                itemLabelDict = item.labelDict
            else:
                itemLabelDict = {
                    label.labelName: [label.labelValue, label.labelVisible]
                    for label in item.labels.values()
                }
            itemDict = {
                "type": "sys",
                "lib": item.libraryName,
                "cell": item.cellName,
                "view": item.viewName,
                "nam": item.instanceName,
                "ic": item.counter,
                "ld": itemLabelDict,
                "loc": (item.scenePos() - item.scene().origin).toTuple(),
                "ang": item.angle,
                "ign": int(item.netlistIgnore),
                "br": item.boundingRect().getCoords(),
            }
            return itemDict
        elif isinstance(item, net.schematicNet):
            itemDict = {
                "type": "scn",
                "st": (item.mapToScene(item.draftLine.p1()) - item.scene().origin)
                .toPoint()
                .toTuple(),
                "end": (item.mapToScene(item.draftLine.p2()) - item.scene().origin)
                .toPoint()
                .toTuple(),
                "nam": item.name,
                "ns": item.nameStrength.value
            }
            return itemDict
        elif isinstance(item, shp.schematicPin):
            itemDict = {
                "type": "scp",
                "st": (item.mapToScene(item.start) - item.scene().origin).toTuple(),
                "pn": item.pinName,
                "pd": item.pinDir,
                "pt": item.pinType,
                "ang": item.angle,
            }
            return itemDict
        elif isinstance(item, shp.text):
            itemDict = {
                "type": "txt",
                "st": (item.mapToScene(item.start) - item.scene().origin).toTuple(),
                "tc": item.textContent,
                "ff": item.fontFamily,
                "fs": item.fontStyle,
                "th": item.textHeight,
                "ta": item.textAlignment,
                "to": item.textOrient,
                "ang": item.angle,
            }
            return itemDict
        # elif isinstance(item, net.crossingDot):
        #     itemDict = {
        #         "type": "dot",
        #         "pt": (item.mapToScene(item.point) - item.scene().origin).toTuple(),
        #     }
        #     return itemDict
