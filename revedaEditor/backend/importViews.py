#
#    “Commons Clause” License Condition v1.0
#   #
#    The Software is provided to you by the Licensor under the License, as defined
#    below, subject to the following condition.
#   #
#    Without limiting other conditions in the License, the grant of rights under the
#    License will not include, and the License does not grant to you, the right to
#    Sell the Software.
#   #
#    For purposes of the foregoing, “Sell” means practicing any or all of the rights
#    granted to you under the License to provide to third parties, for a fee or other
#    consideration (including without limitation fees for hosting or consulting/
#    support services related to the Software), a product or service whose value
#    derives, entirely or substantially, from the functionality of the Software. Any
#    license notice or attribution required by the License must also include this
#    Commons Clause License Condition notice.
#   #
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)

import json
import pathlib
import shutil

from PySide6.QtCore import (Qt, QPoint)
from PySide6.QtWidgets import (QMainWindow, QDialog)

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.hdlBackEnd as hdl
import revedaEditor.backend.libraryMethods as libm  # library view functions
import revedaEditor.backend.schBackEnd as scb  # import the backend
import revedaEditor.common.pens as pens
import revedaEditor.common.shape as shp
import revedaEditor.fileio.symbolEncoder as se
import revedaEditor.gui.editorWindows as edw
import revedaEditor.gui.propertyDialogues as pdlg


def createVaView(parent: QMainWindow, importDlg: QDialog, libraryModel:
edw.designLibrariesModel, importedVaObj: hdl.verilogaC):
    importedVaFilePathObj = pathlib.Path(importDlg.vaFileEdit.text())
    libItem = libm.getLibItem(
        libraryModel, importDlg.libNamesCB.currentText()
    )
    libItemRow = libItem.row()
    libCellNames = [
        libraryModel.item(libItemRow).child(i).cellName
        for i in range(libraryModel.item(libItemRow).rowCount())
    ]
    cellName = importDlg.cellNamesCB.currentText().strip()
    if cellName not in libCellNames and cellName != "":
        scb.createCell(parent, libraryModel, libItem, cellName)
    cellItem = libm.getCellItem(libItem, cellName)
    newVaFilePathObj = cellItem.data(Qt.UserRole + 2).joinpath(
        importedVaFilePathObj.name
    )
    vaItem = scb.createCellView(parent, importDlg.vaViewName.text(), cellItem)
    shutil.copy(importedVaFilePathObj, newVaFilePathObj)
    items = list()
    items.insert(0, {"cellView": "veriloga"})
    items.insert(1, {"filePath": str(newVaFilePathObj.name)})
    items.insert(2, {"vaModule": importedVaObj.vaModule})
    items.insert(3, {"netlistLine": importedVaObj.netListLine})
    with vaItem.data(Qt.UserRole + 2).open(mode="w") as f:
        json.dump(items, f, indent=4)
    return ddef.viewItemTuple(libItem, cellItem, vaItem)


def createVaSymbol(parent: QMainWindow,
                   vaItemTuple: ddef.viewItemTuple,
                   libraryDict: dict,
                   libraryBrowser: edw.libraryBrowser,
                   importedVaObj: hdl.verilogaC):
    symbolViewItem = scb.createCellView(parent, "symbol", vaItemTuple.cellItem)
    newVaFilePathObj = vaItemTuple.cellItem.data(Qt.UserRole + 2).joinpath(
        importedVaObj.pathObj.name)
    symbolWindow = edw.symbolEditor(
        symbolViewItem,
        libraryDict,
        libraryBrowser.libBrowserCont.designView,
    )
    symbolPen = pens.sPen.returnPen("symbolPen")
    labelPen = pens.sPen.returnPen("labelPen")
    pinPen = pens.sPen.returnPen(("pinPen"))
    dlg = pdlg.symbolCreateDialog(
        parent,
        importedVaObj.inPins,
        importedVaObj.outPins,
        importedVaObj.inoutPins,
    )
    dlg.leftPinsEdit.setText(",".join(importedVaObj.inPins))
    dlg.rightPinsEdit.setText(",".join(importedVaObj.outPins))
    dlg.topPinsEdit.setText(",".join(importedVaObj.inoutPins))

    if dlg.exec() == QDialog.Accepted:
        try:
            leftPinNames = list(
                filter(
                    None,
                    [
                        pinName.strip()
                        for pinName in dlg.leftPinsEdit.text().split(
                        ","
                    )
                    ],
                )
            )
            rightPinNames = list(
                filter(
                    None,
                    [
                        pinName.strip()
                        for pinName in dlg.rightPinsEdit.text().split(
                        ","
                    )
                    ],
                )
            )
            topPinNames = list(
                filter(
                    None,
                    [
                        pinName.strip()
                        for pinName in dlg.topPinsEdit.text().split(",")
                    ],
                )
            )
            bottomPinNames = list(
                filter(
                    None,
                    [
                        pinName.strip()
                        for pinName in dlg.bottomPinsEdit.text().split(
                        ","
                    )
                    ],
                )
            )
            stubLength = int(float(dlg.stubLengthEdit.text().strip()))
            pinDistance = int(float(dlg.pinDistanceEdit.text().strip()))
            rectXDim = (
                               max(len(topPinNames), len(bottomPinNames)) + 1
                       ) * pinDistance
            rectYDim = (
                               max(len(leftPinNames), len(rightPinNames)) + 1
                       ) * pinDistance
        except ValueError:
            parent.logger.error("Enter valid value")
        symbolScene = symbolWindow.centralW.scene
        symbolScene.rectDraw(
            QPoint(0, 0),
            QPoint(rectXDim, rectYDim),
            symbolPen,
            symbolScene.gridTuple,
        )
        symbolScene.labelDraw(
            QPoint(int(0.25 * rectXDim), int(0.4 * rectYDim)),
            labelPen,
            "[@cellName]",
            symbolScene.gridTuple,
            "NLPLabel",
            "12",
            "Center",
            "R0",
            "Instance",
        )
        symbolScene.labelDraw(
            QPoint(int(rectXDim), int(-0.2 * rectYDim)),
            labelPen,
            "[@instName]",
            symbolScene.gridTuple,
            "NLPLabel",
            "12",
            "Center",
            "R0",
            "Instance",
        )
        vaFileLabel = symbolScene.labelDraw(
            QPoint(int(0.25 * rectXDim), int(0.6 * rectYDim)),
            labelPen,
            f"[@vaFile:vaFile=%:vaFile={str(newVaFilePathObj)}]",
            symbolScene.gridTuple,
            "NLPLabel",
            "12",
            "Center",
            "R0",
            "Instance",
        )
        vaFileLabel.labelVisible = False
        vaModuleLabel = symbolScene.labelDraw(
            QPoint(int(0.25 * rectXDim), int(0.8 * rectYDim)),
            labelPen,
            f"[@vaModule:vaModule=%:vaModule={importedVaObj.vaModule}]",
            symbolScene.gridTuple,
            "NLPLabel",
            "12",
            "Center",
            "R0",
            "Instance",
        )
        vaModuleLabel.labelVisible = False
        vaModelLabel = symbolScene.labelDraw(
            QPoint(int(0.25 * rectXDim), int(1 * rectYDim)),
            labelPen,
            f"[@vaModel:vaModel=%:vaModel={importedVaObj.vaModule}Model]",
            symbolScene.gridTuple,
            "NLPLabel",
            "12",
            "Center",
            "R0",
            "Instance",
        )
        vaModelLabel.labelVisible = False
        i = 0
        instParamNum = len(importedVaObj.instanceParams)
        for key, value in importedVaObj.instanceParams.items():
            symbolScene.labelDraw(
                QPoint(
                    int(rectXDim),
                    int(i * 0.2 * rectYDim / instParamNum),
                ),
                labelPen,
                f"[@{key}:{key}=%:{key}={value}]",
                symbolScene.gridTuple,
                "NLPLabel",
                "12",
                "Center",
                "R0",
                "Instance",
            )

        leftPinLocs = [
            QPoint(-stubLength, (i + 1) * pinDistance)
            for i in range(len(leftPinNames))
        ]
        rightPinLocs = [
            QPoint(rectXDim + stubLength, (i + 1) * pinDistance)
            for i in range(len(rightPinNames))
        ]
        bottomPinLocs = [
            QPoint((i + 1) * pinDistance, rectYDim + stubLength)
            for i in range(len(bottomPinNames))
        ]
        topPinLocs = [
            QPoint((i + 1) * pinDistance, -stubLength)
            for i in range(len(topPinNames))
        ]
        for i, pinName in enumerate(leftPinNames):
            symbolScene.lineDraw(
                leftPinLocs[i],
                leftPinLocs[i] + QPoint(stubLength, 0),
                symbolScene.symbolPen,
                symbolScene.gridTuple,
            )
            symbolScene.addItem(
                shp.pin(leftPinLocs[i], pinPen, pinName)
            )
        for i, pinName in enumerate(rightPinNames):
            symbolScene.lineDraw(
                rightPinLocs[i],
                rightPinLocs[i] + QPoint(-stubLength, 0),
                symbolScene.symbolPen,
                symbolScene.gridTuple,
            )
            symbolScene.addItem(
                shp.pin(rightPinLocs[i], pinPen, pinName)
            )
        for i, pinName in enumerate(topPinNames):
            symbolScene.lineDraw(
                topPinLocs[i],
                topPinLocs[i] + QPoint(0, stubLength),
                symbolScene.symbolPen,
                symbolScene.gridTuple,
            )
            symbolScene.addItem(shp.pin(topPinLocs[i], pinPen, pinName))
        for i, pinName in enumerate(bottomPinNames):
            symbolScene.lineDraw(
                bottomPinLocs[i],
                bottomPinLocs[i] + QPoint(0, -stubLength),
                symbolScene.symbolPen,
                symbolScene.gridTuple,
            )
            symbolScene.addItem(
                shp.pin(bottomPinLocs[i], pinPen, pinName)
            )
        symbolScene.attributeList = list()  # empty attribute list
        for key, value in importedVaObj.modelParams.items():
            symbolScene.attributeList.append(
                se.symbolAttribute(key, value)
            )
        symbolScene.attributeList.append(
            se.symbolAttribute(
                "NLPDeviceFormat", importedVaObj.netListLine
            )
        )
        symbolWindow.show()
        symbolViewTuple = ddef.viewTuple(vaItemTuple.libraryItem.libraryName,
                                         vaItemTuple.cellItem.cellName, 'symbol')
        symbolWindow.libraryView.openViews[symbolViewTuple] = symbolWindow
