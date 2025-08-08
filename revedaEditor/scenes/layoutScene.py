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
#    consideration (including without limitation fees for hosting) a product or service whose value
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


import inspect
import json
import pathlib
import time
from typing import List, Dict, Any, Union, Generator

from contextlib import contextmanager

from PySide6.QtCore import (QPoint, QPointF, QRect, QRectF, Qt, QLineF,)
from PySide6.QtGui import (QColor, QGuiApplication, QTransform, QPen, QFontDatabase,
                           QFont, )
from PySide6.QtWidgets import (QDialog, QGraphicsSceneMouseEvent, QGraphicsLineItem,
                               QCompleter, QGraphicsRectItem, QGraphicsItem)

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.libraryMethods as libm
import revedaEditor.backend.libraryModelView as lmview
import revedaEditor.backend.undoStack as us
import revedaEditor.common.layoutShapes as lshp  # import layout shapes
import revedaEditor.fileio.layoutEncoder as layenc
import revedaEditor.fileio.loadJSON as lj
import revedaEditor.gui.editFunctions as edf
import revedaEditor.gui.fileDialogues as fd
import revedaEditor.gui.layoutDialogues as ldlg
import revedaEditor.gui.propertyDialogues as pdlg
from revedaEditor.backend.pdkPaths import importPDKModule
from revedaEditor.scenes.editorScene import editorScene

fabproc = importPDKModule('process')
laylyr = importPDKModule('layoutLayers')
schlyr = importPDKModule('schLayers')
pcells = importPDKModule('pcells')


class layoutScene(editorScene):
    def __init__(self, parent):
        super().__init__(parent)
        self.selectEdLayer = laylyr.pdkAllLayers[0]
        self.layoutShapes = ["Inst", "Rect", "Path", "Label", "Via", "Pin", "Polygon",
                             "Pcell", "Ruler", ]
        # draw modes
        self.editModes = ddef.layoutModes(selectItem=False, deleteItem=False,
                                          moveItem=False, copyItem=False, rotateItem=False,
                                          changeOrigin=False, panView=False, drawPath=False,
                                          drawPin=False, drawArc=False, drawPolygon=False,
                                          addLabel=False, addVia=False, drawRect=False,
                                          drawLine=False, drawCircle=False, drawRuler=False,
                                          stretchItem=False, addInstance=False, )
        self.editModes.setMode("selectItem")
        self.selectModes = ddef.layoutSelectModes(selectAll=True, selectPath=False,
                                                  selectInstance=False, selectVia=False,
                                                  selectPin=False, selectLabel=False,
                                                  selectText=False, )
        self.newInstance = None
        self.layoutInstanceTuple = None
        self._scale = fabproc.dbu
        self.itemCounter = 0
        self._newPath = None
        self._stretchPath = None
        self.newPathTuple = None
        self.draftLine = None
        self.m45Rotate = QTransform()
        self.m45Rotate.rotate(-45)
        self._newPin = None
        self.newPinTuple = None
        self.newLabelTuple = None
        self._newLabel = None
        self._newRect = None
        self._newPolygon = None
        self.arrayViaTuple = None
        self._singleVia = None
        self._arrayVia = None
        self._polygonGuideLine = None
        self._newRuler = None
        self._selectionRectItem = None
        self.rulersSet = set()
        self.rulerFont = self.setRulerFont(12)
        self.rulerFont.setKerning(False)
        self.rulerTickGap = fabproc.dbu
        self.rulerTickLength = 10
        self.rulerWidth = 2

    @property
    def drawMode(self):
        return any((self.editModes.drawPath, self.editModes.drawPin, self.editModes.drawArc,
                    self.editModes.drawPolygon, self.editModes.drawRect,
                    self.editModes.drawCircle, self.editModes.drawRuler,))

    # Order of drawing
    # 1. Rect
    # 2. Path
    # 3. Pin
    # 4. Label
    # 5. Via/Contact
    # 6. Polygon
    # 7. Add instance
    # 8. select item/s
    # 9. rotate item/s

    @staticmethod
    def toLayoutCoord(point: QPoint) -> QPointF:
        """
        Converts a point in scene coordinates to layout coordinates by dividing it to
        fabproc.dbu.
        """
        if isinstance(point, QPointF):
            returnPoint = point / fabproc.dbu
        elif isinstance(point, QPoint):
            returnPoint = point.toPointF() / fabproc.dbu
        else:
            returnPoint = QPointF(0.0, 0.0)
        return returnPoint

    @staticmethod
    def toSceneCoord(point: Union[QPoint | QPointF]) -> QPoint | QPointF:
        """
        Converts a point in layout coordinates to scene coordinates by multiplying it with
        fabproc.dbu.
        """
        point *= fabproc.dbu
        return point

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:

        super().mousePressEvent(event)
        modifiers = QGuiApplication.keyboardModifiers()
        if event.button() != Qt.LeftButton:
            return
        try:
            self.mousePressLoc = event.scenePos().toPoint()
            if self.editModes.selectItem:
                self.clearSelection()
                if (
                        modifiers == Qt.KeyboardModifier.ShiftModifier or modifiers == Qt.KeyboardModifier.ControlModifier):
                    self._selectionRectItem = QGraphicsRectItem()
                    self._selectionRectItem.setRect(
                        QRectF(self.mousePressLoc.x(), self.mousePressLoc.y(), 0, 0))
                    self._selectionRectItem.setPen(schlyr.draftPen)
                    self.addItem(self._selectionRectItem)
        except Exception as e:
            self.logger.error(f"Mouse press error: {e}")

    def mouseMoveEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        """
        Handle the mouse move event.

        Args:
            mouse_event (QGraphicsSceneMouseEvent): The mouse event object.

        Returns:
            None
        """
        # Get the current mouse position
        self.mouseMoveLoc = mouse_event.scenePos().toPoint()
        # Call the parent class's mouseMoveEvent method
        super().mouseMoveEvent(mouse_event)
        # Get the keyboard modifiers
        # modifiers = QGuiApplication.keyboardModifiers()

        # Handle drawing path mode
        if self.editModes.drawPath and self._newPath is not None:
            self._newPath.draftLine = QLineF(self._newPath.draftLine.p1(),
                                             self.mouseMoveLoc)
        elif self.editModes.drawRect and self._newRect:
            self._newRect.end = self.mouseMoveLoc
        # Handle drawing pin mode with no new pin
        elif self.editModes.drawPin:
            if self._newPin is not None:
                self._newPin.end = self.mouseMoveLoc
        elif self.editModes.addLabel and self._newLabel is not None:
            self._newLabel.start = self.mouseMoveLoc
        elif self.editModes.addInstance and self.newInstance is not None:
            self.newInstance.setPos(self.mouseMoveLoc - self.newInstance.start)
        # Handle drawing polygon mode
        elif self.editModes.drawPolygon and self._newPolygon is not None:
            self._polygonGuideLine.setLine(
                QLineF(self._newPolygon.points[-1], self.mouseMoveLoc))
        elif self.editModes.drawRuler and self._newRuler is not None:
            self._newRuler.draftLine = QLineF(self._newRuler.draftLine.p1(),
                                              self.mouseMoveLoc)
        # Handle adding via mode with array via tuple
        elif self.editModes.addVia and self._arrayVia is not None:
            self._arrayVia.setPos(self.mouseMoveLoc - self._arrayVia.start)

        elif self.editModes.stretchItem and self._stretchPath is not None:
            self._stretchPath.draftLine = QLineF(self._stretchPath.draftLine.p1(),
                                                 self.mouseMoveLoc)
        elif self.editModes.selectItem and self._selectionRectItem is not None:
            self._selectionRectItem.setRect(QRect(self.mouseReleaseLoc, self.mouseMoveLoc))
        # Calculate the cursor position in layout units
        cursorPosition = self.toLayoutCoord(self.mouseMoveLoc - self.origin)

        # Show the cursor position in the status line
        self.statusLine.showMessage(
            f"Cursor Position: ({cursorPosition.x():.3f}, {cursorPosition.y():.3f})")

    def mouseReleaseEvent(self, mouse_event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(mouse_event)
        self.mouseReleaseLoc = mouse_event.scenePos().toPoint()
        # modifiers = QGuiApplication.keyboardModifiers()
        try:
            if mouse_event.button() == Qt.LeftButton:
                if self.editModes.drawPath:
                    self.drawLayoutPath()
                elif self.editModes.drawRect:
                    self.drawLayoutRect()
                elif self.editModes.drawPin:
                    self.drawLayoutPin()
                elif self.editModes.addLabel:
                    self.addLayoutLabel()
                elif self.editModes.addInstance:
                    self.addLayoutInstance()
                elif self.editModes.drawPolygon:
                    self.drawLayoutPolygon()
                elif self.editModes.drawRuler:
                    self.drawLayoutRuler()
                elif self.editModes.addVia:
                    self.addLayoutViaArray()
                elif self.editModes.changeOrigin:
                    self.origin = self.mouseReleaseLoc
                elif self.editModes.rotateItem:
                    self.editorWindow.messageLine.setText("Rotate item")
                    if self.selectedItems():
                        # Rotate selected items
                        self.rotateSelectedItems(self.mouseReleaseLoc)

        except Exception as e:
            self.logger.error(f"mouse release error: {e}")

    def addLayoutViaArray(self):
        if self._arrayVia is not None:
            self.arrayViaTuple = None
            self._arrayVia = None

        singleVia = lshp.layoutVia(QPoint(0, 0), *self.arrayViaTuple.singleViaTuple, )
        self._arrayVia = lshp.layoutViaArray(self.mouseReleaseLoc, singleVia,
                                             self.arrayViaTuple.xs, self.arrayViaTuple.ys,
                                             self.arrayViaTuple.xnum,
                                             self.arrayViaTuple.ynum, )
        self.addUndoStack(self._arrayVia)


    def drawLayoutRuler(self):
        if self._newRuler:
            if self._newRuler.draftLine.isNull():
                self.undoStack.removeLastCommand()
            self._newRuler = None
        self._newRuler = lshp.layoutRuler(
            QLineF(self.mouseReleaseLoc, self.mouseReleaseLoc), width=self.rulerWidth,
            tickGap=self.rulerTickGap, tickLength=self.rulerTickLength,
            tickFont=self.rulerFont, )
        self.addUndoStack(self._newRuler)

    def drawLayoutPolygon(self):
        if self._newPolygon is None:
            # Create a new polygon
            self._newPolygon = lshp.layoutPolygon(
                [self.mouseReleaseLoc, self.mouseReleaseLoc], self.selectEdLayer, )
            self.addUndoStack(self._newPolygon)
            # Create a guide line for the polygon
            self._polygonGuideLine = QGraphicsLineItem(
                QLineF(self._newPolygon.points[-2], self._newPolygon.points[-1]))
            self._polygonGuideLine.setPen(QPen(QColor(255, 255, 0), 0.1*fabproc.dbu, Qt.DashLine))
            self._polygonGuideLine.pen().setCosmetic(False)
            self.addUndoStack(self._polygonGuideLine)
        else:
            self._newPolygon.addPoint(self.mouseReleaseLoc)

    def addLayoutInstance(self):
        if self.newInstance is not None:
            self.newInstance = None
        if self.layoutInstanceTuple:
            self.newInstance = self.addNewInstance()
            self.addUndoStack(self.newInstance)
            self.newInstance.setPos(self.mouseReleaseLoc - self.newInstance.start)

    def addLayoutLabel(self):
        if self._newLabel is not None:
            self.newLabelTuple = None
            self._newLabel = None
        if self.newLabelTuple is not None:
            self._newLabel = lshp.layoutLabel(self.mouseReleaseLoc, *self.newLabelTuple)
            self.addUndoStack(self._newLabel)

    def drawLayoutPin(self):
        self.editorWindow.messageLine.setText("Pin mode.")
        # Create a new pin
        if self._newPin:
            if self._newPin.rect.isNull():
                self.undoStack.removeLastCommand()
            else:
                self.editModes.setMode('addLabel')
                self._newLabel = lshp.layoutLabel(self.mouseReleaseLoc, *self.newLabelTuple)
                self._newPin.label = self._newLabel
                self.addUndoStack(self._newLabel)
            self._newPin = None
        self._newPin = lshp.layoutPin(self.mouseReleaseLoc, self.mouseReleaseLoc,
                                      *self.newPinTuple)
        self.addUndoStack(self._newPin)

    def drawLayoutRect(self):
        self.editorWindow.messageLine.setText("Rectangle mode.")
        # Create a new rectangle
        if self._newRect:
            if self._newRect.rect.isNull():
                self.removeItem(self._newRect)
                self.undoStack.removeLastCommand()
            self._newRect = None
        self._newRect = lshp.layoutRect(self.mouseReleaseLoc, self.mouseReleaseLoc,
                                        self.selectEdLayer, )
        self.addUndoStack(self._newRect)

    def drawLayoutPath(self):
        self.editorWindow.messageLine.setText("Path mode")
        if self._newPath:
            if self._newPath.draftLine.isNull():
                self.undoStack.removeLastCommand()
            self._newPath = None

            # Create a new path
        self._newPath = lshp.layoutPath(QLineF(self.mousePressLoc, self.mousePressLoc),
                                        self.newPathTuple.layer, self.newPathTuple.width,
                                        self.newPathTuple.startExtend,
                                        self.newPathTuple.endExtend,
                                        self.newPathTuple.mode, )
        self._newPath.name = self.newPathTuple.name
        self.addUndoStack(self._newPath)

    def addNewInstance(self) -> Union[lshp.layoutInstance, lshp.layoutPcell]:
        newInstance = self.instLayout(self.layoutInstanceTuple)
        dlg = ldlg.layoutInstanceDialogue(self.editorWindow)
        if isinstance(newInstance, pcells.baseCell):
            dlg.instanceLibName.setText(newInstance.libraryName)
            dlg.instanceCellName.setText(newInstance.cellName)
            dlg.instanceViewName.setText(newInstance.viewName)
            lineEditDict = self.extractPcellInstanceParameters(newInstance)
            if lineEditDict:
                dlg.pcellParamsGroup.show()
                for key, value in lineEditDict.items():
                    dlg.pcellParamsLayout.addRow(key, value)
            if dlg.exec() == QDialog.Accepted:
                instanceValuesDict = {}
                for key, value in lineEditDict.items():
                    instanceValuesDict[key] = value.text()
                if instanceValuesDict:
                    newInstance(*instanceValuesDict.values())
        return newInstance

    def instLayout(self, layoutInstanceTuple: ddef.viewItemTuple) -> Union[
        lshp.layoutInstance, lshp.layoutPcell]:
        """
        Read a layout file and create layoutShape objects from it.
        """
        match layoutInstanceTuple.viewItem.viewType:
            case "layout":
                with layoutInstanceTuple.viewItem.viewPath.open("r") as temp:
                    try:
                        decodedData = json.load(temp)
                        if decodedData[0]["viewType"] != "layout":
                            self.logger.error("Not a layout cell")
                        else:
                            instanceShapes = [lj.layoutItems(self).create(item) for item in
                                              decodedData[2:] if
                                              item.get("type") in self.layoutShapes]
                            layoutInstance = lshp.layoutInstance(instanceShapes)
                            layoutInstance.libraryName = (
                                layoutInstanceTuple.libraryItem.libraryName)
                            layoutInstance.cellName = (
                                layoutInstanceTuple.cellItem.cellName)
                            layoutInstance.viewName = (
                                layoutInstanceTuple.viewItem.viewName)
                            self.itemCounter += 1
                            layoutInstance.counter = self.itemCounter
                            layoutInstance.instanceName = f"I{layoutInstance.counter}"
                            # For each instance assign a counter number from the scene
                            return layoutInstance
                    except json.JSONDecodeError:
                        self.logger.warning("Invalid JSON File")
            case "pcell":
                with open(layoutInstanceTuple.viewItem.viewPath, "r") as temp:
                    try:
                        pcellRefDict = json.load(temp)
                        if pcellRefDict[0]["cellView"] != "pcell":
                            self.logger.error("Not a pcell cell")
                        else:
                            # create a pcell instance with default parameters.
                            pcellInstance = eval(f"pcells.{pcellRefDict[1]['reference']}()")
                            # now evaluate pcell

                            pcellInstance.libraryName = (
                                layoutInstanceTuple.libraryItem.libraryName)
                            pcellInstance.cellName = (layoutInstanceTuple.cellItem.cellName)
                            pcellInstance.viewName = (layoutInstanceTuple.viewItem.viewName)
                            self.itemCounter += 1
                            pcellInstance.counter = self.itemCounter
                            # This needs to become more sophisticated.
                            pcellInstance.instanceName = f"I{pcellInstance.counter}"

                            return pcellInstance
                    except Exception as e:
                        self.logger.error(f"Cannot read pcell: {e}")

    def findScenelayoutCellSet(self) -> set[lshp.layoutInstance]:
        """
        Find all the symbols on the scene as a set.
        """
        return {item for item in self.items() if isinstance(item, lshp.layoutInstance)}


    def saveLayoutCell(self, filePathObj: pathlib.Path) -> None:
        """Save the layout cell to a JSON file.

        Args:
            filePathObj (pathlib.Path): Path object for the output file

        Raises:
            IOError: If there are issues writing to the file
            JSONEncodeError: If there are issues encoding the JSON
            ValueError: If the layout data is invalid
        """
        def get_layout_data() -> list:
            """Prepare layout data with validation.

            Returns:
                list: List of layout items

            Raises:
                ValueError: If required attributes are missing
            """
            if not hasattr(self, 'snapTuple'):
                raise ValueError("Missing required attribute: snapTuple")

            # Pre-validate top-level items
            top_level_items = [item for item in self.items() if item.parentItem() is None]

            return [
                {"viewType": "layout"},
                {"snapGrid": self.snapTuple},
                *top_level_items
            ]

        def safeJsonWrite(file_obj, data: list) -> None:
            """Write JSON data with optimized settings.

            Args:
                file_obj: File object to write to
                data: Data to be written

            Raises:
                JSONEncodeError: If JSON encoding fails
            """
            json.dump(
                data,
                file_obj,
                cls=layenc.layoutEncoder,
                separators=(',', ':'),  # Minimize JSON size
                check_circular=False    # Optimize for non-circular references
            )

        try:
            # Create parent directory if it doesn't exist
            filePathObj.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data before file operation
            layout_data = get_layout_data()

            # Use temporary file for atomic write
            temp_path = filePathObj.with_suffix('.tmp')
            try:
                with temp_path.open(mode='w', buffering=65536) as f:  # 64KB buffer
                    safeJsonWrite(f, layout_data)

                # Atomic rename for safer file writing
                temp_path.replace(filePathObj)

            finally:
                # Clean up temp file if it still exists
                if temp_path.exists():
                    temp_path.unlink()

            self.logger.info(
                f"Saved layout to {self.editorWindow.cellName}:{self.editorWindow.viewName}"
                f"({len(layout_data)} items)"
            )

        except ValueError as e:
            self.logger.error(f"Invalid layout data: {str(e)}")
            raise

        except (IOError, json.JSONEncodeError) as e:
            self.logger.error(
                f"Failed to save layout to {filePathObj}: {str(e)}"
            )
            raise

        except Exception as e:
            self.logger.error(f"Unexpected error while saving layout: {str(e)}")
            raise


    def loadDesign(self, filePathObj: pathlib.Path) -> None:
        """Load the layout cell from the given JSON file.

        Args:
            filePathObj (pathlib.Path): Path to the layout cell file.

        Raises:
            IOError: If there are issues reading the file
            json.JSONDecodeError: If the file contains invalid JSON
            ValueError: If the file structure is invalid
            KeyError: If required grid settings are missing
        """
        CHUNK_SIZE = 65536  # 64KB chunks for reading

        def setup_grid_settings(grid_settings: dict) -> None:
            """Configure grid-related attributes from settings."""
            try:
                snap_grid = grid_settings["snapGrid"]
                if len(snap_grid) != 2 or not all(isinstance(x, (int, float)) for x in snap_grid):
                    raise ValueError("Invalid snap grid values")

                self.majorGrid, self.snapGrid = snap_grid
                self.snapTuple = (self.snapGrid, self.snapGrid)
                self.snapDistance = 2 * self.snapGrid

            except (KeyError, TypeError, IndexError) as e:
                raise ValueError(f"Invalid grid settings: {e}")

        def validate_header(data: list) -> tuple:
            """Validate header and return processed data.

            Returns:
                tuple: (view_type, grid_settings, remaining_data)
            """
            if len(data) < 3:
                raise ValueError("Insufficient data in layout file")

            view_type, grid_settings, *item_data = data

            if not isinstance(view_type, dict):
                raise ValueError("Invalid view type format")
            if view_type.get("viewType") != "layout":
                raise ValueError("Unsupported view type")
            if not isinstance(grid_settings, dict):
                raise ValueError("Invalid grid settings format")

            return view_type, grid_settings, item_data

        def stream_load_json(file_path: pathlib.Path) -> dict:
            """Load JSON file in streaming mode for large files."""
            with file_path.open('rb') as f:
                raw_data = f.read(CHUNK_SIZE)
                decoder = json.JSONDecoder()
                buffer = ''

                while raw_data:
                    buffer += raw_data.decode('utf-8')
                    raw_data = f.read(CHUNK_SIZE)

                try:
                    return decoder.decode(buffer)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format: {e}")

        try:
            with self.measureDuration():
                # Validate file existence and size
                if not filePathObj.exists():
                    raise FileNotFoundError(f"Layout file not found: {filePathObj}")

                file_size = filePathObj.stat().st_size
                self.logger.debug(f"Loading layout file of size: {file_size/1024:.2f}KB")

                # Load and validate data
                decoded_data = stream_load_json(filePathObj)
                if not isinstance(decoded_data, list):
                    raise ValueError("Invalid layout file format")

                # Process header and setup grid
                view_type, grid_settings, item_data = validate_header(decoded_data)
                setup_grid_settings(grid_settings)

                # Clear existing items if any
                self.clear()

                self.createLayoutItems(item_data)


        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"File operation error: {str(e)}")
            raise

        except ValueError as e:
            self.logger.error(f"Invalid layout data: {str(e)}")
            raise

        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise

    def createLayoutItems(self, decoded_data: List[Dict[str, Any]]) -> None:
        """Create layout items from decoded data and add them to the undo stack.

        Args:
            decoded_data (List[Dict[str, Any]]): List of item data dictionaries containing
                shape information and properties.
        """
        if not isinstance(decoded_data, list):
            self.logger.error("Invalid input: decoded_data must be a list")
            return

        if not decoded_data:
            self.logger.debug("No layout items to create")
            return

        def create_valid_items() -> List[Any]:
            layout_factory = lj.layoutItems(self)
            valid_items = []

            for item in decoded_data:
                try:
                    if _is_valid_shape(item):
                        valid_items.append(layout_factory.create(item))
                    else:
                        self.logger.warning(f"Skipping invalid shape type: {item.get('type')}")
                except Exception as e:
                    self.logger.error(f"Error creating layout item: {str(e)}")
                    continue

            return valid_items

        def _is_valid_shape(item: Dict[str, Any]) -> bool:
            return isinstance(item, dict) and item.get("type") in self.layoutShapes

        try:
            loaded_items = create_valid_items()
            if loaded_items:
                self.undoStack.push(us.loadShapesUndo(self, loaded_items))
            else:
                self.logger.warning("No valid layout items were created")

        except Exception as e:
            self.logger.error(f"Failed to create layout items: {str(e)}")

    def deleteSelectedItems(self):
        for item in self.selectedItems():
            # if pin is to be deleted, the associated label should be also deleted.
            if isinstance(item, lshp.layoutPin) and item.label is not None:
                undoCommand = us.deleteShapeUndo(self, item.label)
                self.undoStack.push(undoCommand)
        super().deleteSelectedItems()

    def viewObjProperties(self):
        """
        Display the properties of the selected object.
        """
        try:
            selectedItems = [item for item in self.selectedItems() if
                             item.parentItem() is None]
            if selectedItems is not None:
                for item in selectedItems:
                    match type(item):
                        case lshp.layoutRect:
                            self.layoutRectProperties(item)
                        case lshp.layoutPin:
                            self.layoutPinProperties(item)
                        case lshp.layoutLabel:
                            self.layoutLabelProperties(item)
                        case lshp.layoutPath:
                            self.layoutPathProperties(item)
                        case lshp.layoutViaArray:
                            self.layoutViaProperties(item)
                        case lshp.layoutPolygon:
                            self.layoutPolygonProperties(item)
                        case lshp.layoutInstance:
                            self.layoutInstanceProperties(item, False)
                        case _:
                            if item.__class__.__bases__[0] == pcells.baseCell:
                                self.layoutInstanceProperties(item, True)

        except Exception as e:
            self.logger.error(f"{type(item)} property editor error: {e}")

    def layoutPolygonProperties(self, item):

        pointsTupleList = [self.toLayoutCoord(point).toTuple() for point in item.points]

        dlg = ldlg.layoutPolygonProperties(self.editorWindow, pointsTupleList)
        dlg.polygonLayerCB.addItems(
            [f"{item.name} [{item.purpose}]" for item in laylyr.pdkAllLayers])
        dlg.polygonLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")

        if dlg.exec() == QDialog.Accepted:
            newLayer = laylyr.pdkAllLayers[dlg.polygonLayerCB.currentIndex()]
            tempPoints = []
            for i in range(dlg.tableWidget.rowCount()):
                xcoor = dlg.tableWidget.item(i, 1).text()
                ycoor = dlg.tableWidget.item(i, 2).text()
                if xcoor != "" and ycoor != "":
                    tempPoints.append(
                        self.toSceneCoord(QPointF(float(xcoor), float(ycoor))))
            newPoints = tempPoints
            newPolygon = lshp.layoutPolygon(newPoints, newLayer)
            self.undoStack.push(us.addDeleteShapeUndo(self, newPolygon, item))

    def layoutRectProperties(self, item):
        dlg = ldlg.layoutRectProperties(self.editorWindow)
        dlg.rectLayerCB.addItems(
            [f"{item.name} [{item.purpose}]" for item in laylyr.pdkAllLayers])
        dlg.rectLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.rectWidthEdit.setText(str(item.width / fabproc.dbu))
        dlg.rectHeightEdit.setText(str(item.height / fabproc.dbu))
        dlg.topLeftEditX.setText(str(item.rect.topLeft().x() / fabproc.dbu))
        dlg.topLeftEditY.setText(str(item.rect.topLeft().y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            layer = laylyr.pdkAllLayers[dlg.rectLayerCB.currentIndex()]
            newRect = lshp.layoutRect(QPoint(0, 0), QPoint(0, 0), layer)
            newRect.rect = QRectF(float(dlg.topLeftEditX.text()) * fabproc.dbu,
                                  float(dlg.topLeftEditY.text()) * fabproc.dbu,
                                  float(dlg.rectWidthEdit.text()) * fabproc.dbu,
                                  float(dlg.rectHeightEdit.text()) * fabproc.dbu, )
            self.undoStack.push(us.addDeleteShapeUndo(self, newRect, item))

    def layoutViaProperties(self, item):
        dlg = ldlg.layoutViaProperties(self.editorWindow)
        if item.xnum == 1 and item.ynum == 1:
            dlg.singleViaRB.setChecked(True)
            dlg.singleViaClicked()
            dlg.singleViaNamesCB.addItems(fabproc.processViaNames)
            dlg.singleViaNamesCB.setCurrentText(item.via.viaDefTuple.name)
            dlg.singleViaWidthEdit.setText(str(item.width / fabproc.dbu))
            dlg.singleViaHeightEdit.setText(str(item.via.height / fabproc.dbu))
        else:
            dlg.arrayViaRB.setChecked(True)
            dlg.arrayViaClicked()
            dlg.arrayViaNamesCB.addItems(fabproc.processViaNames)
            dlg.arrayViaNamesCB.setCurrentText(item.via.viaDefTuple.name)
            dlg.arrayViaWidthEdit.setText(str(item.via.width / fabproc.dbu))
            dlg.arrayViaHeightEdit.setText(str(item.via.height / fabproc.dbu))
            dlg.arrayXspacingEdit.setText(str(item.xs / fabproc.dbu))
            dlg.arrayYspacingEdit.setText(str(item.xs/ fabproc.dbu))
            dlg.arrayXNumEdit.setText(str(item.xnum))
            dlg.arrayYNumEdit.setText(str(item.ynum))
        dlg.startXEdit.setText(str(self.toLayoutCoord(item.mapToScene(item.start)).x()))
        dlg.startYEdit.setText(str(self.toLayoutCoord(item.mapToScene(item.start)).y()))
        if dlg.exec() == QDialog.Accepted:
            startX = int(float(dlg.startXEdit.text()))
            startY = int(float(dlg.startYEdit.text()))
            start = self.toSceneCoord(QPoint(startX, startY))
            if dlg.singleViaRB.isChecked():
                selViaDefTuple = fabproc.processVias[
                    fabproc.processViaNames.index(dlg.singleViaNamesCB.currentText())]
                singleViaTuple = ddef.singleViaTuple(selViaDefTuple, float(
                    dlg.singleViaWidthEdit.text().strip()) * fabproc.dbu, float(
                    dlg.singleViaHeightEdit.text().strip()) * fabproc.dbu, )
                arrayViaTuple = ddef.arrayViaTuple(singleViaTuple, float(
                    selViaDefTuple.minSpacing) * fabproc.dbu, float(
                    selViaDefTuple.minSpacing) * fabproc.dbu, 1, 1, )
            else:
                selViaDefTuple = [viaDefTuple for viaDefTuple in fabproc.processVias if
                                  viaDefTuple.name == dlg.arrayViaNamesCB.currentText()][
                    0]

                singleViaTuple = ddef.singleViaTuple(selViaDefTuple, float(
                    dlg.arrayViaWidthEdit.text().strip()) * fabproc.dbu, float(
                    dlg.arrayViaHeightEdit.text().strip()) * fabproc.dbu, )
                arrayViaTuple = ddef.arrayViaTuple(singleViaTuple, float(
                    dlg.arrayXspacingEdit.text().strip()) * fabproc.dbu, float(
                    dlg.arrayYspacingEdit.text().strip()) * fabproc.dbu, int(float(
                    dlg.arrayXNumEdit.text().strip())), int(float(
                    dlg.arrayYNumEdit.text().strip())), )
            singleVia = lshp.layoutVia(QPoint(0, 0), *arrayViaTuple.singleViaTuple, )
            arrayVia = lshp.layoutViaArray(start, singleVia, arrayViaTuple.xs,
                                           arrayViaTuple.ys, arrayViaTuple.xnum,
                                           arrayViaTuple.ynum, )
            self.undoStack.push(us.addDeleteShapeUndo(self, arrayVia, item))

    def layoutPathProperties(self, item):
        dlg = ldlg.layoutPathPropertiesDialog(self.editorWindow)
        match item.mode:
            case 0:
                dlg.manhattanButton.setChecked(True)
            case 1:
                dlg.diagonalButton.setChecked(True)
            case 2:
                dlg.anyButton.setChecked(True)
            case 3:
                dlg.horizontalButton.setChecked(True)
            case 4:
                dlg.verticalButton.setChecked(True)
        dlg.pathLayerCB.addItems(
            [f"{item.name} [{item.purpose}]" for item in laylyr.pdkDrawingLayers])
        dlg.pathLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.pathWidth.setText(str(item.width / fabproc.dbu))
        dlg.pathNameEdit.setText(item.name)
        roundingFactor = len(str(fabproc.dbu)) - 1
        dlg.startExtendEdit.setText(
            str(round(item.startExtend / fabproc.dbu, roundingFactor)))
        dlg.endExtendEdit.setText(str(round(item.endExtend / fabproc.dbu, roundingFactor)))
        dlg.p1PointEditX.setText(
            str(round(item.draftLine.p1().x() / fabproc.dbu, roundingFactor)))
        dlg.p1PointEditY.setText(
            str(round(item.draftLine.p1().y() / fabproc.dbu, roundingFactor)))
        dlg.p2PointEditX.setText(
            str(round(item.draftLine.p2().x() / fabproc.dbu, roundingFactor)))
        dlg.p2PointEditY.setText(
            str(round(item.draftLine.p2().y() / fabproc.dbu, roundingFactor)))
        dlg.angleEdit.setText(str(item.angle))
        if dlg.exec() == QDialog.Accepted:
            name = dlg.pathNameEdit.text()
            layer = laylyr.pdkDrawingLayers[dlg.pathLayerCB.currentIndex()]
            width = fabproc.dbu * float(dlg.pathWidth.text())
            startExtend = fabproc.dbu * float(dlg.startExtendEdit.text())
            endExtend = fabproc.dbu * float(dlg.endExtendEdit.text())
            p1 = self.toSceneCoord(
                QPointF(float(dlg.p1PointEditX.text()), float(dlg.p1PointEditY.text()), ))
            p2 = self.toSceneCoord(
                QPointF(float(dlg.p2PointEditX.text()), float(dlg.p2PointEditY.text()), ))
            draftLine = QLineF(p1, p2)
            newPath = lshp.layoutPath(draftLine, layer, width, startExtend, endExtend)
            newPath.angle = int(float(dlg.angleEdit.text()))
            self.undoStack.push(us.addDeleteShapeUndo(self, newPath, item))

    def layoutLabelProperties(self, item):
        dlg = ldlg.layoutLabelProperties(self.editorWindow)
        dlg.labelName.setText(item.labelText)
        dlg.labelLayerCB.addItems(
            [f"{layer.name} [{layer.purpose}]" for layer in laylyr.pdkTextLayers])
        dlg.labelLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.familyCB.setCurrentText(item.fontFamily)
        dlg.fontStyleCB.setCurrentText(item.fontStyle)
        dlg.labelHeightCB.setCurrentText(str(int(float(item.fontHeight))))
        dlg.labelAlignCB.setCurrentText(item.labelAlign)
        dlg.labelOrientCB.setCurrentText(item.labelOrient)
        start = item.mapToScene(item.start)

        if dlg.exec() == QDialog.Accepted:
            labelName = dlg.labelName.text()
            labelLayerName = dlg.labelLayerCB.currentText().split()[0]
            labelLayer = [
                item for item in laylyr.pdkTextLayers if item.name == labelLayerName
            ][0]
            fontFamily = dlg.familyCB.currentText()
            fontStyle = dlg.fontStyleCB.currentText()
            fontHeight = dlg.labelHeightCB.currentText()
            labelAlign = dlg.labelAlignCB.currentText()
            labelOrient = dlg.labelOrientCB.currentText()
            newLabelTuple = ddef.layoutLabelTuple(
                labelName,
                fontFamily,
                fontStyle,
                fontHeight,
                labelAlign,
                labelOrient,
                labelLayer,
            )
            newLabel = lshp.layoutLabel(start, *newLabelTuple)
            self.undoStack.push(us.addDeleteShapeUndo(self, newLabel, item))
            self.addItem(newLabel)

    def layoutPinProperties(self, item):
        dlg = ldlg.layoutPinProperties(self.editorWindow)
        dlg.pinName.setText(item.pinName)
        dlg.pinDir.setCurrentText(item.pinDir)
        dlg.pinType.setCurrentText(item.pinType)

        dlg.pinLayerCB.addItems(
            [f"{pinLayer.name} [{pinLayer.purpose}]" for pinLayer in laylyr.pdkPinLayers])
        dlg.pinLayerCB.setCurrentText(f"{item.layer.name} [{item.layer.purpose}]")
        dlg.pinBottomLeftX.setText(str(item.mapToScene(item.start).x() / fabproc.dbu))
        dlg.pinBottomLeftY.setText(str(item.mapToScene(item.start).y() / fabproc.dbu))
        dlg.pinTopRightX.setText(str(item.mapToScene(item.end).x() / fabproc.dbu))
        dlg.pinTopRightY.setText(str(item.mapToScene(item.end).y() / fabproc.dbu))
        if dlg.exec() == QDialog.Accepted:
            pinName = dlg.pinName.text()
            pinDir = dlg.pinDir.currentText()
            pinType = dlg.pinType.currentText()
            labelText = dlg.pinName.text()
            start = self.snapToGrid(self.toSceneCoord(
                QPointF(float(dlg.pinBottomLeftX.text()),
                        float(dlg.pinBottomLeftY.text()), )), self.snapTuple, )
            end = self.snapToGrid(self.toSceneCoord(
                QPointF(float(dlg.pinTopRightX.text()), float(dlg.pinTopRightY.text()), )),
                self.snapTuple, )
            pinLayer = laylyr.pdkPinLayers[dlg.pinLayerCB.currentIndex()]
            newPin = lshp.layoutPin(start, end, pinName, pinDir, pinType, pinLayer)
            newLabel = lshp.layoutLabel(item.label.start, labelText, item.label.fontFamily,
                                        item.label.fontStyle, item.label.fontHeight,
                                        item.label.labelAlign, item.label.labelOrient,
                                        item.label.layer)
            newPin.label = newLabel

            undoCommandsList = [us.addDeleteShapeUndo(self, newPin, item),
                                us.addDeleteShapeUndo(self, newLabel, item.label)]
            self.addUndoMacroStack(undoCommandsList,
                                   'pin/label edit')  # self.undoStack.beginMacro('pin/label edit')  # self.undoStack.push(us.addDeleteShapeUndo(self, newPin, item))  # self.undoStack.push(us.addDeleteShapeUndo(self, newLabel, item.label))  # self.undoStack.endMacro()

    def layoutInstanceProperties(self, item: Union[lshp.layoutInstance, lshp.layoutPcell],
                                 pcell: bool = False):

        libraryModel = lmview.layoutViewsModel(self.editorWindow.libraryDict,
                                               self.editorWindow.layoutViews)
        dlg = ldlg.layoutInstancePropertiesDialogue(self.editorWindow)
        if pcell:
            dlg.pcellParamsGroup.show()
            lineEditDict = self.extractPcellInstanceParameters(item)
            if lineEditDict:
                dlg.pcellParamsGroup.show()
                for key, value in lineEditDict.items():
                    dlg.pcellParamsLayout.addRow(key, value)
        libItem = libm.getLibItem(libraryModel, item.libraryName)
        cellItem = libm.getCellItem(libItem, item.cellName)
        viewItem = libm.getViewItem(cellItem, item.viewName)
        instanceTuple = ddef.viewItemTuple(libItem, cellItem, viewItem)
        dlg.instanceLibName.setText(item.libraryName)
        libNameCompleter = QCompleter(libraryModel.listLibraries())
        libNameCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        dlg.instanceLibName.setCompleter(libNameCompleter)
        # create cell name completer list.
        dlg.instanceLibName.editingFinished.connect(lambda: self.cellNameComplete(dlg,
                                                                                  libraryModel.listLibraryCells(
                                                                                      dlg.instanceLibName.text())))
        dlg.instanceCellName.setText(item.cellName)
        # create view name completer list
        dlg.instanceCellName.editingFinished.connect(lambda: self.viewNameComplete(dlg,
                                                                                   libraryModel.listCellViews(
                                                                                       dlg.instanceLibName.text(),
                                                                                       dlg.instanceCellName.text(),
                                                                                       [
                                                                                           'layout',
                                                                                           'pcell'])))
        dlg.instanceViewName.setText(item.viewName)
        dlg.instanceViewName.editingFinished.connect(
            lambda: self.changePcellParameterFields(dlg, libraryModel, instanceTuple))
        dlg.instanceNameEdit.setText(item.instanceName)

        dlg.xEdit.setText(str(item.scenePos().x() / fabproc.dbu))
        dlg.yEdit.setText(str(item.scenePos().y() / fabproc.dbu))

        if dlg.exec() == QDialog.Accepted:
            libraryName = dlg.instanceLibName.text().strip()
            cellName = dlg.instanceCellName.text().strip()
            viewName = dlg.instanceViewName.text().strip()
            instanceName = dlg.instanceNameEdit.text().strip()
            libItem = libm.getLibItem(libraryModel, libraryName)
            cellItem = libm.getCellItem(libItem, cellName)
            viewItem = libm.getViewItem(cellItem, viewName)

            layoutInstanceTuple = ddef.viewItemTuple(libItem, cellItem, viewItem)
            newLayoutInstance = self.instLayout(layoutInstanceTuple)
            newLayoutInstance.instanceName = instanceName
            lineEditDict = ldlg.formDictionary(
                dlg.pcellParamsLayout).extractDictFormLayout()
            instanceValuesDict = {}
            if lineEditDict:
                for key, value in lineEditDict.items():
                    instanceValuesDict[key] = value.text()
            if instanceValuesDict:
                newLayoutInstance(*instanceValuesDict.values())
            newLayoutInstance.setPos(QPoint(
                self.snapToBase(float(dlg.xEdit.text()) * fabproc.dbu, self.snapTuple[0]),
                self.snapToBase(float(dlg.yEdit.text()) * fabproc.dbu,
                                self.snapTuple[1]), ))
            self.undoStack.push(us.addDeleteShapeUndo(self, newLayoutInstance, item))

    def changePcellParameterFields(self, dlg: ldlg.layoutInstancePropertiesDialogue,
                                   libraryModel: lmview.layoutViewsModel,
                                   instanceTuple: ddef.viewItemTuple):
        """Update the PCell parameter fields based on the selected instance tuple."""
        # Get the new item tuple
        lib_item = libm.getLibItem(libraryModel, dlg.instanceLibName.text().strip())
        cell_item = libm.getCellItem(lib_item, dlg.instanceCellName.text().strip())
        view_item = libm.getViewItem(cell_item, dlg.instanceViewName.text().strip())
        new_item_tuple = ddef.viewItemTuple(lib_item, cell_item, view_item)

        # Check if the view item has a 'viewType' key
        if hasattr(new_item_tuple.viewItem, 'viewType'):
            # Clear the pcell parameters layout
            self.clearLayout(dlg.pcellParamsLayout)

            # Create a new instance
            new_instance = self.instLayout(new_item_tuple)

            # Check the view type
            if new_item_tuple.viewItem.viewType == 'pcell':
                # Extract PCell instance parameters
                line_edit_dict = self.extractPcellInstanceParameters(new_instance)

                # Add PCell parameters to the layout
                if line_edit_dict:
                    dlg.pcellParamsGroup.show()
                    for key, value in line_edit_dict.items():
                        dlg.pcellParamsLayout.addRow(key, value)
            elif new_item_tuple.viewItem.viewType == 'layout':
                # Hide the PCell parameters group
                dlg.pcellParamsGroup.hide()

    def extractPcellInstanceParameters(self, instance: lshp.layoutPcell) -> dict:
        initArgs = inspect.signature(instance.__class__.__init__).parameters
        argsUsed = [param for param in initArgs if (param != "self")]
        argDict = {arg: getattr(instance, arg) for arg in argsUsed}
        lineEditDict = {key: edf.shortLineEdit(value) for key, value in argDict.items()}
        return lineEditDict

    def clearLayout(self, layout):
        """Clear the layout by deleting all its children."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clearLayout(child.layout())

    def moveBySelectedItems(self):
        if self.selectedItems():
            dlg = pdlg.moveByDialogue(self.editorWindow)
            dlg.xEdit.setText("0.0")
            dlg.yEdit.setText("0.0")
            if dlg.exec() == QDialog.Accepted:
                for item in self.selectedItems():
                    item.moveBy(self.snapToBase(float(dlg.xEdit.text()) * fabproc.dbu,
                                                self.snapTuple[0]),
                                self.snapToBase(float(dlg.yEdit.text()) * fabproc.dbu,
                                                self.snapTuple[1]), )
                self.editorWindow.messageLine.setText(
                    f"Moved items by {dlg.xEdit.text()} and {dlg.yEdit.text()}")
                self.editModes.setMode("selectItem")

    def copySelectedItems(self):
        selectedItems = [item for item in self.selectedItems() if item.parentItem() is None]
        if selectedItems:
            for item in selectedItems:
                selectedItemJson = json.dumps(item, cls=layenc.layoutEncoder)
                itemCopyDict = json.loads(selectedItemJson)
                shape = lj.layoutItems(self).create(itemCopyDict)
                if shape is not None:
                    item.setSelected(False)
                    self.addUndoStack(shape)
                    shape.setSelected(True)
                    # shift position by four grid units to right and down
                    shape.setPos(QPoint(item.pos().x() + self.snapTuple[0] * fabproc.dbu,
                                        item.pos().y() + self.snapTuple[1] * fabproc.dbu, ))
                    if isinstance(shape, lshp.layoutInstance) or isinstance(shape,
                                                                            lshp.layoutPcell):
                        self.itemCounter += 1
                        shape.counter = self.itemCounter
                        shape.instanceName = f"I{shape.counter}"

    def deleteAllRulers(self):
        for ruler in self.rulersSet:
            undoCommand = us.deleteShapeUndo(self, ruler)
            self.undoStack.push(undoCommand)

    def goDownHier(self):
        if self.selectedItems():
            for item in self.selectedItems():
                if isinstance(item, lshp.layoutInstance):
                    dlg = fd.goDownHierDialogue(self.editorWindow)
                    libItem = libm.getLibItem(self.editorWindow.libraryView.libraryModel,
                                              item.libraryName)
                    cellItem = libm.getCellItem(libItem, item.cellName)
                    viewNames = [cellItem.child(i).text() for i in
                                 range(cellItem.rowCount())
                                 # if cellItem.child(i).text() != item.viewName
                                 if "layout" in cellItem.child(i).text()]
                    dlg.viewListCB.addItems(viewNames)
                    if dlg.exec() == QDialog.Accepted:
                        libItem = libm.getLibItem(
                            self.editorWindow.libraryView.libraryModel, item.libraryName)
                        cellItem = libm.getCellItem(libItem, item.cellName)
                        viewItem = libm.getViewItem(cellItem, dlg.viewListCB.currentText())
                        openViewT = (
                            self.editorWindow.libraryView.libBrowsW.openCellView(viewItem,
                                                                                 cellItem,
                                                                                 libItem))
                        if self.editorWindow.appMainW.openViews[openViewT]:
                            childWindow = self.editorWindow.appMainW.openViews[openViewT]
                            childWindow.parentEditor = self.editorWindow
                            childWindow.parentObj = item
                            childWindow.layoutToolbar.addAction(childWindow.goUpAction)
                            if dlg.buttonId == 2:
                                childWindow.centralW.scene.readOnly = True

    def stretchPath(self, pathItem: lshp.layoutPath, stretchEnd: str):
        match stretchEnd:
            case "p2":
                self._stretchPath = lshp.layoutPath(
                    QLineF(pathItem.sceneEndPoints[0], pathItem.sceneEndPoints[1]),
                    pathItem.layer, pathItem.width, pathItem.startExtend,
                    pathItem.endExtend, pathItem.mode, )
            case "p1":
                self._stretchPath = lshp.layoutPath(
                    QLineF(pathItem.sceneEndPoints[1], pathItem.sceneEndPoints[0]),
                    pathItem.layer, pathItem.width, pathItem.startExtend,
                    pathItem.endExtend, pathItem.mode, )
        self._stretchPath.stretch = True
        self._stretchPath.name = pathItem.name

        addDeleteStretchNetCommand = us.addDeleteShapeUndo(self, self._stretchPath,
                                                           pathItem)
        self.undoStack.push(addDeleteStretchNetCommand)

    def findClosestFontSize(self, sizes: List[int], target: int = 16) -> int:
        return min(sizes, key=lambda x: abs(x - target))

    def setRulerFont(self, target_size: int = 16) -> QFont:
        fontDatabase = QFontDatabase()
        fixedFamilies = None
        if fontDatabase:
            fixedFamilies = [family for family in fontDatabase.families(QFontDatabase.Latin)
                             if fontDatabase.isFixedPitch(family)]

        if not fixedFamilies:
            self.logger.warning("No fixed-pitch fonts found. Using default font.")
            return QFont()
        else:
            for family in fixedFamilies:
                styles = fontDatabase.styles(family)
                if not styles:
                    continue

                style = styles[0]  # Use the first available style
                sizes = fontDatabase.pointSizes(family, style)

                if sizes:
                    closest_size = self.findClosestFontSize(sizes, target_size)
                    font = QFont(family)
                    font.setStyleName(style)
                    font.setPointSize(closest_size)
                    font.setKerning(False)
                    return font

        self.scene().logger.warning("No suitable font found. Using default font.")
        return QFont()

    def updateItem(self, item: QGraphicsItem):
        #update the item to the latest version of the layout cell if it is edited in another editor window
        if isinstance(item, lshp.layoutInstance):
            libItem = libm.getLibItem(self.editorWindow.libraryView.libraryModel, item.libraryName)
            cellItem = libm.getCellItem(libItem, item.cellName)
            viewItem = libm.getViewItem(cellItem, item.viewName)
            viewItemTuple = ddef.viewItemTuple(libItem, cellItem, viewItem)
            if viewItem:
                newItem = self.instLayout(viewItemTuple)
                newItem.instanceName = item.instanceName
                newItem.setPos(item.pos())
                newItem.setRotation(item.rotation())
                newItem.setScale(item.scale())
                newItem.setTransform(item.transform())
                updateRect = item.boundingRect()
                self.removeItem(item)
                self.addItem(newItem)
                self.update(updateRect)
