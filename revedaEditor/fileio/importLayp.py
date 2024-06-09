import xml.etree.ElementTree as ET
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


from pathlib import Path

from PySide6.QtGui import (
    QColor,
)

from revedaEditor.backend.dataDefinitions import layLayer
from revedaEditor.gui.stippleEditor import stippleEditor


def parseLyp(lypFile):
    lypFileObj = Path(lypFile)
    tree = ET.parse(lypFileObj)
    root = tree.getroot()
    pdkDrawingLayers = 'pdkDrawingLayers = ['
    pdkPinLayers = 'pdkPinLayers = ['
    pdkViaLayers = 'pdkViaLayers = ['
    pdkTextLayers = 'pdkTextLayers= ['

    with lypFileObj.parent.joinpath("layoutLayers.py").open("w") as file:
        try:
            for i, layerItem in enumerate(root.iterfind("properties")):
                pcolor = QColor.fromString(layerItem.find("frame-color").text.upper())
                bcolor = QColor.fromString(layerItem.find("fill-color").text.upper())
                btexture = f'{layerItem.find("dither-pattern").text}.txt'
                selectable = bool(layerItem.find("valid").text.capitalize())
                visible = bool(layerItem.find("visible").text.capitalize())
                pwidth = int(float(layerItem.find("width").text))
                name = layerItem.find("name").text.split(".")[0]
                purpose = layerItem.find("name").text.split(".")[1]
                gdsLayer = int(float(layerItem.find("source").text.split("/")[0]))
                dataType = int(float(layerItem.find("source").text.split("/")[1]))

                layoutLayerItem = layLayer(
                    name,
                    purpose,
                    pcolor,
                    pwidth,
                    1,
                    bcolor,
                    btexture,
                    i,
                    selectable,
                    visible,
                    gdsLayer,
                    dataType,
                )
                file.write(
                    f"{layoutLayerItem.name}_{layoutLayerItem.purpose}="
                    f"ddef.{layoutLayerItem}\n"
                )
                match purpose:
                    case "drw":
                        pdkDrawingLayers += (f"{layoutLayerItem.name}_"
                                             f"{layoutLayerItem.purpose}, ")
                    case "pin":
                        pdkPinLayers += f"{layoutLayerItem.name}_{layoutLayerItem.purpose}, "
                    case "lbl":
                        pdkTextLayers += f"{layoutLayerItem.name}_{layoutLayerItem.purpose}, "
                    case "txt":
                        pdkTextLayers += f"{layoutLayerItem.name}_{layoutLayerItem.purpose}, "
            pdkDrawingLayers += ']\n'
            pdkPinLayers += ']\n'
            pdkTextLayers += ']\n'
            pdkAllLayers = 'pdkDrawingLayers + pdkPinLayers + pdkTextLayers\n'
            file.write(pdkDrawingLayers)
            file.write(pdkPinLayers)
            file.write(pdkTextLayers)
            file.write(pdkAllLayers)
        except Exception as e:
            print(f"error: {e}")

        for ditherPattern in root.iterfind("custom-dither-pattern"):
            for orderItem in ditherPattern.iterfind("order"):
                fileName = f"C{orderItem.text}.txt"
                fileObj = lypFileObj.parent.joinpath(fileName)
                with fileObj.open("w") as patternFile:
                    for pattern in ditherPattern.findall("pattern"):
                        lineCount = 0
                        for lineItem in pattern.iterfind("line"):
                            patternFile.write(
                                f"{lineItem.text.replace('.','0 ').replace('*','1 ')}\n"
                            )
                            lineCount += 1
                            rowLength = len(lineItem)
                imageFileObj = fileObj.with_suffix(".png")
                stippleEditW = stippleEditor(None)
                stippleEditW.loadPatternFromFile(str(fileObj))
                stippleEditW.imageExportToFile(str(imageFileObj))
