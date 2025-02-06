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

from __future__ import annotations
import pathlib
from typing import TYPE_CHECKING, List

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.libBackEnd as libb
import revedaEditor.common.shapes as shp

if TYPE_CHECKING:
    from revedaEditor.gui.schematicEditor import schematicEditor
import datetime


class xyceNetlist:
    def __init__(self, schematic: schematicEditor, filePathObj: pathlib.Path,
            useConfig: bool = False, ):
        self.filePathObj = filePathObj
        self.schematic = schematic
        self._use_config = useConfig
        self._scene = self.schematic.centralW.scene
        self.libraryDict = self.schematic.libraryDict
        self.libraryView = self.schematic.libraryView
        self._configDict = None
        self.libItem = libm.getLibItem(self.schematic.libraryView.libraryModel,
            self.schematic.libName, )
        self.cellItem = libm.getCellItem(self.libItem, self.schematic.cellName)

        self._switchViewList = schematic.switchViewList
        self._stopViewList = schematic.stopViewList
        self.netlistedViewsSet = set()  # keeps track of netlisted views.
        self.includeLines = set()  # keeps track of include lines.
        self.vamodelLines = set()  # keeps track of vamodel lines.
        self.vahdlLines = set()  # keeps track of *.HDL lines.

    def __repr__(self):
        return f"xyceNetlist(filePathObj={self.filePathObj}, schematic={self.schematic}, useConfig={self._use_config})"

    @property
    def switchViewList(self) -> List[str]:
        return self._switchViewList

    @switchViewList.setter
    def switchViewList(self, value: List[str]):
        self._switchViewList = value

    @property
    def stopViewList(self) -> List[str]:
        return self._stopViewList

    @stopViewList.setter
    def stopViewList(self, value: List[str]):
        self._stopViewList = value

    def writeNetlist(self):
        with self.filePathObj.open(mode="w") as cirFile:
            cirFile.write("*".join(["\n", 80 * "*", "\n", "* Revolution EDA CDL Netlist\n",
                f"* Library: {self.schematic.libName}\n",
                f"* Top Cell Name: {self.schematic.cellName}\n",
                f"* View Name: {self.schematic.viewName}\n",
                f"* Date: {datetime.datetime.now()}\n", 80 * "*", "\n",
                ".GLOBAL gnd!\n\n", ]))

            # now go down the rabbit hole to track all circuit elements.
            self.recursiveNetlisting(self.schematic, cirFile)

            # cirFile.write(".END\n")
            for line in self.includeLines:
                cirFile.write(f"{line}\n")
            for line in self.vamodelLines:
                cirFile.write(f"{line}\n")
            for line in self.vahdlLines:
                cirFile.write(f"{line}\n")

    @property
    def configDict(self):
        return self._configDict

    @configDict.setter
    def configDict(self, value: dict):
        assert isinstance(value, dict)
        self._configDict = value

    def recursiveNetlisting(self, schematic: schematicEditor, cirFile):
        """
        Recursively traverse all sub-circuits and netlist them.
        """
        try:
            schematicScene = schematic.centralW.scene
            schematicScene.nameSceneNets()  # name all nets in the schematic

            sceneSymbolSet = schematicScene.findSceneSymbolSet()
            schematicScene.generatePinNetMap(tuple(sceneSymbolSet))

            for elementSymbol in sceneSymbolSet:
                self.processElementSymbol(elementSymbol, schematic, cirFile)
        except Exception as e:
            self.schematic.logger.error(f"Netlisting error: {e}")

    def processElementSymbol(self, elementSymbol, schematic, cirFile):
        if elementSymbol.symattrs.get("XyceNetlistPass") != "1" and (
                not elementSymbol.netlistIgnore):
            libItem = libm.getLibItem(schematic.libraryView.libraryModel,
                elementSymbol.libraryName)
            cellItem = libm.getCellItem(libItem, elementSymbol.cellName)
            netlistView = self.determineNetlistView(elementSymbol, cellItem)

            # Create the netlist line for the item.
            self.createItemLine(cirFile, elementSymbol, cellItem, netlistView)
        elif elementSymbol.netlistIgnore:
            cirFile.write(f"*{elementSymbol.instanceName} is marked to be ignored\n")
        elif not elementSymbol.symattrs.get("XyceNetlistPass", False):
            cirFile.write(
                f"*{elementSymbol.instanceName} has no XyceNetlistLine attribute\n")

    def determineNetlistView(self, elementSymbol, cellItem):
        viewItems = [cellItem.child(row) for row in range(cellItem.rowCount())]
        viewNames = [view.viewName for view in viewItems]

        if self._use_config:
            return self.configDict.get(elementSymbol.cellName)[1]
        else:
            for viewName in self._switchViewList:
                if viewName in viewNames:
                    return viewName
            return "symbol"

    def createItemLine(self, cirFile, elementSymbol: shp.schematicSymbol,
            cellItem: libb.cellItem, netlistView: str, ):
        if "schematic" in netlistView:
            # First write subckt call in the netlist.
            cirFile.write(self.createXyceSymbolLine(elementSymbol))
            schematicItem = libm.getViewItem(cellItem, netlistView)
            if netlistView not in self._stopViewList:
                # now load the schematic
                schematicObj = schematicEditor(schematicItem, self.libraryDict,
                    self.libraryView)
                schematicObj.loadSchematic()

                viewTuple = ddef.viewTuple(schematicObj.libName, schematicObj.cellName,
                    schematicObj.viewName)

                if viewTuple not in self.netlistedViewsSet:
                    self.netlistedViewsSet.add(viewTuple)
                    pinList = elementSymbol.symattrs.get("pinOrder", ", ").replace(",", " ")
                    cirFile.write(f".SUBCKT {schematicObj.cellName} {pinList}\n")
                    self.recursiveNetlisting(schematicObj, cirFile)
                    cirFile.write(".ENDS\n")
        elif "symbol" in netlistView:
            cirFile.write(self.createXyceSymbolLine(elementSymbol))
        elif "spice" in netlistView:
            cirFile.write(self.createSpiceLine(elementSymbol))
        elif "veriloga" in netlistView:
            cirFile.write(self.createVerilogaLine(elementSymbol))

    def createXyceSymbolLine(self, elementSymbol: shp.schematicSymbol):
        """
        Create a netlist line from a nlp device format line.
        """
        try:
            xyceNetlistFormatLine = elementSymbol.symattrs["XyceSymbolNetlistLine"].strip()

            # Process labels
            for labelItem in elementSymbol.labels.values():
                xyceNetlistFormatLine = xyceNetlistFormatLine.replace(labelItem.labelName,
                    labelItem.labelValue)

            # Process attributes
            for attrb, value in elementSymbol.symattrs.items():
                xyceNetlistFormatLine = xyceNetlistFormatLine.replace(f"%{attrb}", value)

            # Add pin list
            pinList = " ".join(elementSymbol.pinNetMap.values())
            xyceNetlistFormatLine = (
                    xyceNetlistFormatLine.replace("@pinList", pinList) + "\n")

            return xyceNetlistFormatLine

        except Exception as e:
            self._scene.logger.error(
                f"Error creating netlist line for {elementSymbol.instanceName}: {e}")
            return (
                f"*Netlist line is not defined for symbol of {elementSymbol.instanceName}\n")

    def createSpiceLine(self, elementSymbol: shp.schematicSymbol):
        """
        Create a netlist line from a nlp device format line.
        """
        try:
            spiceNetlistFormatLine = elementSymbol.symattrs["XyceSpiceNetlistLine"].strip()
            for labelItem in elementSymbol.labels.values():
                if labelItem.labelName in spiceNetlistFormatLine:
                    spiceNetlistFormatLine = spiceNetlistFormatLine.replace(
                        labelItem.labelName, labelItem.labelValue)

            for attrb, value in elementSymbol.symattrs.items():
                if f"%{attrb}" in spiceNetlistFormatLine:
                    spiceNetlistFormatLine = spiceNetlistFormatLine.replace(f"%{attrb}",
                        value)
            pinList = elementSymbol.symattrs.get("pinOrder", ", ").replace(",", " ")
            spiceNetlistFormatLine = (
                    spiceNetlistFormatLine.replace("@pinList", pinList) + "\n")
            self.includeLines.add(elementSymbol.symattrs.get("incLine",
                "* no include line is found for {item.cellName}").strip())
            return spiceNetlistFormatLine
        except Exception as e:
            self._scene.logger.error(f"Spice subckt netlist error: {e}")
            self._scene.logger.error(
                f"Netlist line is not defined for {elementSymbol.instanceName}")
            # if there is no NLPDeviceFormat line, create a warning line
            return (
                f"*Netlist line is not defined for symbol of {elementSymbol.instanceName}\n")

    def createVerilogaLine(self, elementSymbol):
        """
        Create a netlist line from a nlp device format line.
        """
        try:
            verilogaNetlistFormatLine = elementSymbol.symattrs[
                "XyceVerilogaNetlistLine"].strip()
            for labelItem in elementSymbol.labels.values():
                if labelItem.labelName in verilogaNetlistFormatLine:
                    verilogaNetlistFormatLine = verilogaNetlistFormatLine.replace(
                        labelItem.labelName, labelItem.labelValue)

            for attrb, value in elementSymbol.symattrs.items():
                if f"%{attrb}" in verilogaNetlistFormatLine:
                    verilogaNetlistFormatLine = verilogaNetlistFormatLine.replace(
                        f"%{attrb}", value)
            pinList = " ".join(elementSymbol.pinNetMap.values())
            verilogaNetlistFormatLine = (
                    verilogaNetlistFormatLine.replace("@pinList", pinList) + "\n")
            self.vamodelLines.add(elementSymbol.symattrs.get("vaModelLine",
                "* no model line is found for {item.cellName}").strip())
            self.vahdlLines.add(elementSymbol.symattrs.get("vaHDLLine",
                "* no hdl line is found for {item.cellName}").strip())
            return verilogaNetlistFormatLine
        except Exception as e:
            self._scene.logger.error(e)
            self._scene.logger.error(
                f"Netlist line is not defined for {elementSymbol.instanceName}")
            # if there is no NLPDeviceFormat line, create a warning line
            return (
                f"*Netlist line is not defined for symbol of {elementSymbol.instanceName}\n")
