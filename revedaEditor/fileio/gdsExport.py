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

import gdstk
import revedaEditor.common.layoutShapes as lshp
import pathlib
import inspect
import os
from dotenv import load_dotenv

load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):
    import pdk.pcells as pcells
else:
    import defaultPDK.pcells as pcells

class gdsExporter:
    def __init__(self, cellname: str, items: list, outputFileObj: pathlib.Path):
        self._cellname = cellname
        self._items = items
        self._outputFileObj = outputFileObj
        self._libraryName = None
        self._unit = 1e-6
        self._precision = 1e-9
        self._topCell = None
        self._cellCache = {}  # Cache to store already processed cells
        self._itemCounter = 0

    def gds_export(self):
        self._outputFileObj.parent.mkdir(parents=True, exist_ok=True)
        lib = gdstk.Library(unit=self._unit, precision=self._precision)
        self._topCell = lib.new_cell(self._cellname)  # top Cell
        for item in self._items:
            self.createCells(lib, item, self._topCell)

        lib.write_gds(self._outputFileObj)

    def createCells(self, library: gdstk.Library, item: lshp.layoutShape, parentCell: gdstk.Cell):
        match type(item):
            case lshp.layoutInstance:
                cell_key = (item.libraryName, item.cellName, item.viewName)
                if cell_key not in self._cellCache:
                    cellGDSName = f"{item.libraryName}_{item.cellName}_{item.viewName}_{self._itemCounter}"
                    self._itemCounter += 1
                    new_cell = library.new_cell(cellGDSName)
                    self._cellCache[cell_key] = new_cell
                    for shape in item.shapes:
                        self.createCells(library, shape, new_cell)
                else:
                    new_cell = self._cellCache[cell_key]
                
                ref = gdstk.Reference(
                    new_cell,
                    item.pos().toPoint().toTuple(),
                    rotation=item.angle,
                )
                parentCell.add(ref)
            
            case lshp.layoutRect:
                rect = gdstk.rectangle(
                    corner1=item.start.toTuple(),
                    corner2=item.end.toTuple(),
                    layer=item.layer.gdsLayer,
                    datatype=item.layer.datatype,
                )
                parentCell.add(rect)
            
            case lshp.layoutPath:
                path = gdstk.FlexPath(
                    points=[
                        item.draftLine.p1().toTuple(),
                        item.draftLine.p2().toTuple(),
                    ],
                    width=item.width,
                    ends=(item.startExtend, item.endExtend),
                    simple_path=True,
                    layer=item.layer.gdsLayer,
                    datatype=item.layer.datatype,
                )
                parentCell.add(path)
            
            case lshp.layoutLabel:
                label = gdstk.Label(
                    text=item.labelText,
                    origin=item.start.toTuple(),
                    rotation=item.angle,
                    layer=item.layer.gdsLayer,
                )
                parentCell.add(label)
            
            case lshp.layoutPin:
                pin = gdstk.rectangle(
                    corner1=item.start.toTuple(),
                    corner2=item.end.toTuple(),
                    layer=item.layer.gdsLayer,
                    datatype=item.layer.datatype,
                )
                parentCell.add(pin)
            
            case lshp.layoutPolygon:
                points = [point.toTuple() for point in item.points]
                polygon = gdstk.Polygon(
                    points=points,
                    layer=item.layer.gdsLayer,
                    datatype=item.layer.datatype,
                )
                parentCell.add(polygon)
            
            case lshp.layoutViaArray:
                via_key = (item.via.width, item.via.height, item.via.layer.name, item.via.layer.purpose)
                if via_key not in self._cellCache:
                    viaName = f"via_{item.via.width}_{item.via.height}_{item.via.layer.name}_{item.via.layer.purpose}"
                    viaCell = library.new_cell(viaName)
                    via = gdstk.rectangle(
                        item.mapToScene(item.via.rect.topLeft()).toTuple(),
                        item.mapToScene(item.via.rect.bottomRight()).toTuple(),
                        layer=item.via.layer.gdsLayer,
                        datatype=item.via.layer.datatype,
                    )
                    viaCell.add(via)
                    self._cellCache[via_key] = viaCell
                else:
                    viaCell = self._cellCache[via_key]
                
                viaArray = gdstk.Reference(
                    cell=viaCell,
                    origin=item.start.toTuple(),
                    columns=item.xnum,
                    rows=item.ynum,
                    spacing=(item.xs + item.width, item.ys + item.height),
                )
                parentCell.add(viaArray)
            
            case _:
                match item.__class__.__bases__[0]:
                    case pcells.baseCell:
                        pcellParamDict = self.extractPcellInstanceParameters(item)
                        pcell_key = (item.libraryName, type(item).__name__, frozenset(pcellParamDict.items()))
                        
                        if pcell_key not in self._cellCache:
                            pcellNameSuffix = "_".join(
                                [f"{key}_{value}" for key, value in pcellParamDict.items()]
                            ).replace(".", "p")
                            pcellName = f"{item.libraryName}_{type(item).__name__}_{pcellNameSuffix}"
                            new_cell = library.new_cell(pcellName)
                            self._cellCache[pcell_key] = new_cell
                            for shape in item.shapes:
                                self.createCells(library, shape, new_cell)
                        else:
                            new_cell = self._cellCache[pcell_key]
                        
                        ref = gdstk.Reference(
                            new_cell,
                            item.pos().toPoint().toTuple(),
                            rotation=item.angle,
                        )
                        parentCell.add(ref)

    @staticmethod
    def extractPcellInstanceParameters(instance: lshp.layoutPcell) -> dict:
        initArgs = inspect.signature(instance.__class__.__init__).parameters
        argsUsed = [
            param for param in initArgs if (param != "self" and param != "snapTuple")
        ]
        argDict = {arg: getattr(instance, arg) for arg in argsUsed}
        return argDict

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, value):
        self._unit = value

    @property
    def precision(self):
        return self._precision

    @precision.setter
    def precision(self, value):
        self._precision = value