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


class vacaskNetlist():
    def __init__(
        self,
        schematic: schematicEditor,
        filePathObj: pathlib.Path,
        useConfig: bool = False,
    ):
        self.filePathObj = filePathObj
        self.schematic = schematic
        self._use_config = useConfig
        self._scene = self.schematic.centralW.scene
        self.libraryDict = self.schematic.libraryDict
        self.libraryView = self.schematic.libraryView
        self._configDict = None
        self.libItem = libm.getLibItem(
            self.schematic.libraryView.libraryModel,
            self.schematic.libName,
        )
        self.cellItem = libm.getCellItem(self.libItem, self.schematic.cellName)

        self._switchViewList = schematic.switchViewList
        self._stopViewList = schematic.stopViewList
        self.netlistedViewsSet = set()  # keeps track of netlisted views.

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
            cirFile.write(
                "*".join(
                    [
                        "\n",
                        80 * "/",
                        "\n",
                        "// Revolution EDA VACASK Netlist\n",
                        f"// Library: {self.schematic.libName}\n",
                        f"// Top Cell Name: {self.schematic.cellName}\n",
                        f"// View Name: {self.schematic.viewName}\n",
                        f"// Date: {datetime.datetime.now()}\n",
                        80 * "/",
                        "\n",
                        "ground 0\n\n",
                    ]
                )
            )

            # now go down the rabbit hole to track all circuit elements.
            self.recursiveNetlisting(self.schematic, cirFile)

            for line in self.includeLines:
                cirFile.write(f"{line}\n")
            for line in self.vamodelLines:
                cirFile.write(f"{line}\n")
            for line in self.vahdlLines:
                cirFile.write(f"{line}\n")