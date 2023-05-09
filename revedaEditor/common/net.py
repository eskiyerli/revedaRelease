
#   “Commons Clause” License Condition v1.0
#  #
#   The Software is provided to you by the Licensor under the License, as defined
#   below, subject to the following condition.
#  #
#   Without limiting other conditions in the License, the grant of rights under the
#   License will not include, and the License does not grant to you, the right to
#   Sell the Software.
#  #
#   For purposes of the foregoing, “Sell” means practicing any or all of the rights
#   granted to you under the License to provide to third parties, for a fee or other
#   consideration (including without limitation fees for hosting or consulting/
#   support services related to the Software), a product or service whose value
#   derives, entirely or substantially, from the functionality of the Software. Any
#   license notice or attribution required by the License must also include this
#   Commons Clause License Condition notice.
#  #
#   Software: Revolution EDA
#   License: Mozilla Public License 2.0
#   Licensor: Revolution Semiconductor (Registered in the Netherlands)

# net class definition.
from PySide6.QtCore import (QPoint, Qt, QLineF, QRectF, QPointF, QRect)
from PySide6.QtGui import (QPen, QStaticText, QPainterPath, QColor, QFont,)
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsItem,
                               QGraphicsEllipseItem, QGraphicsRectItem,
                               QGraphicsSceneMouseEvent)
# import revedaEditor.common.pens as pens
import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.backend.undoStack as us


class schematicNet(QGraphicsLineItem):
    '''
    Base schematic net class.
    '''
    uses = ["SIGNAL", "ANALOG", "CLOCK", "GROUND", "POWER", ]


    def __init__(self, start: QPoint, end: QPoint, pen: QPen):
        assert isinstance(pen, QPen)
        self._pen = pen
        self._name = None
        self._horizontal = True
        self._start = start
        self._end = end
        self._nameSet = False  # if a name has been set
        self._nameConflict = False  # if a name conflict has been detected
        self._connections = dict()  # dictionary of connections
        super().__init__(QLineF(self._start, self._end))
        self.setPen(self._pen)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        # self._createdNets = dict()
        self._endPoints = [self._start, self._end]
        self._dots = set()
        self._dotPoints = set()
        self._touchingNets = set()
        self._dashedLines = dict()
        self._newWires = list()

    def __repr__(self):
        return f"schematicNet(start={self.mapToScene(self._start)}, " \
               f"end={self.mapToScene(self._end)}"

    def shape(self):
        '''
        Return the shape of the net.
        '''
        gridTuple = self.scene().gridTuple
        path = QPainterPath()
        path.addRect(QRectF(self.line().p1(),self.line().p2()).normalized().adjusted(
            -0.5*gridTuple[0], -0.5*gridTuple[1], 0.5*gridTuple[0], 0.5*gridTuple[1]))
        return path

    def paint(self, painter, option, widget) -> None:
        line = self.line()
        painter.setPen(self._pen)
        if self.isSelected():
            painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
        if self.name is not None:
            if self._nameConflict:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            # if there is name conflict, draw the line and name in red.
            textLoc = line.center()
            painter.drawStaticText(textLoc, QStaticText(self.name))
        painter.drawLine(line)



    def sceneEvent(self, event):
        try:
            if self.scene().drawWire:
                return False
            super().sceneEvent(event)
            return True
        except AttributeError:
            return False

    @property
    def start(self):
        return self._start
        # return self._start

    @start.setter
    def start(self, start: QPoint):
        self._start = start
        self.prepareGeometryChange()
        self.setLine(QLineF(start, self._end))

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end: QPoint):
        self._end = end
        self.prepareGeometryChange()
        self.setLine(QLineF(self._start, end))

    @property
    def pen(self):
        return self._pen

    @pen.setter
    def pen(self, pen: QPen):
        self._pen = pen
        self.setPen(pen)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name != "": # net name should not be an empty string
            self._name = name
            # self.nameSet = True



    @property
    def nameSet(self) -> bool:
        return self._nameSet

    @nameSet.setter
    def nameSet(self, value: bool):
        assert isinstance(value,bool)
        self._nameSet = value

    @property
    def nameConflict(self) -> bool:
        return self._nameConflict

    @nameConflict.setter
    def nameConflict(self, value: bool):
        assert isinstance(value,bool)
        self._nameConflict = value

    @property
    def length(self):
        return self.line().length()

    @property
    def endPoints(self):
        return [self.mapToScene(self._start).toPoint(), self.mapToScene(self._end).toPoint()]
        # return [self.mapToScene(self.line().p1()),self.mapToScene(self.line().p2())]


    @property
    def horizontal(self):
        self._horizontal = (self.line().p1().y() == self.line().p2().y())
        return self._horizontal

    @property
    def dots(self):
        return self._dots

    @property
    def dotPoints(self):
        return self._dotPoints

    def findDotPoints(self):
        try:
            [self.scene().removeItem(dot) for dot in self._dots]
            self._dots.clear()
            self._dotPoints.clear()
            self._touchingNets.clear()

            if self.horizontal:
                nets = {netItem for netItem in self.scene().items(
                    self.sceneBoundingRect()) if
                        (isinstance(netItem, schematicNet) and not
                         netItem.horizontal)}

            else:
                nets = {netItem for netItem in self.scene().items(
                    self.sceneBoundingRect()) if
                        (isinstance(netItem, schematicNet) and
                         netItem.horizontal)}
            for netItem in nets:
                for selfEnd in self.endPoints:
                    if (netItem.sceneBoundingRect().contains(
                            selfEnd) and selfEnd not in
                            netItem.endPoints):
                        self._dotPoints.add(self.mapFromScene(selfEnd).toPoint())
                        self._touchingNets.add(netItem)

            [self._dots.add(crossingDot(dotPoint,3,self.scene().wirePen)) for dotPoint in
             self._dotPoints]
            [dot.setParentItem(self) for dot in self._dots]
            [self.scene().addItem(dot) for dot in self._dots]
            for netItem in self._touchingNets:
                netItem.findDotPoints()

        except Exception as e:
            self.scene().logger.error(f'Error in net.findDotPoints: {e}')

    def createDashLines(self):
        self._dashedLines = list()
        try:
            if self.horizontal:
                nets = {netItem for netItem in self.scene().items(
                    self.sceneBoundingRect()) if
                        (isinstance(netItem, schematicNet) and not
                        netItem.horizontal)}

            else:
                nets = {netItem for netItem in self.scene().items(
                    self.sceneBoundingRect()) if
                        (isinstance(netItem, schematicNet) and
                         netItem.horizontal)}
            for netItem in nets:
                for selfEnd in self.endPoints:
                    if selfEnd in netItem.endPoints:
                        # print(f'self end:{selfEnd}, net end:'
                        #       f'{netItem.endPoints.index(selfEnd)}'
                        netItemEnd = netItem.endPoints[netItem.endPoints.index(selfEnd)]
                        self._dashedLines.append(ddef.netEndTuple(schematicNet(
                            netItemEnd, selfEnd, self.scene().otherPen),
                                        self.endPoints.index(selfEnd), self.horizontal))

        except Exception as e:
            self.scene().logger.error(f'Error in net.createDashLines: {e}')

    def extendDashLines(self):

        try:
            for netEndTuple in self._dashedLines:
                netEndTuple.net.end = self.endPoints[netEndTuple.index]

                if not netEndTuple.net.scene():
                    self.scene().addItem(netEndTuple.net)

        except Exception as e:
            self.scene().logger.error(f'Error in net.extendDashLines: {e}')

    def extendNets(self):
        try:
            for netEndTuple in self._dashedLines:
                start = netEndTuple.net.start
                end = netEndTuple.net.end
                lines = list()
                if start != end:
                    if start.y() != end.y() or start.x() != end.x():
                        if netEndTuple.orient:  # if self is horizontal
                            # | -  Start vertical, connect horizontal
                            lines.append(schematicNet(start, QPoint(end.x(), start.y()),
                                                      self.scene().wirePen))
                            lines.append(schematicNet(QPoint(end.x(), start.y()),end,
                                                      self.scene().wirePen))
                        else: # if self is vertical
                            # - |
                            lines.append(schematicNet(start, QPoint(start.x(), end.y()),
                                                      self.scene().wirePen))
                            lines.append(schematicNet(QPoint(start.x(), end.y()),end,
                                                      self.scene().wirePen))
                    elif start.y() == end.y() or start.x() == end.x():
                        lines.append(schematicNet(start, end, self.scene().wirePen))

                [self.scene().addItem(line) for line in lines]
        except Exception as e:
            self.scene().logger.error(f'Error in net.extendNets: {e}')

    def itemChange(self, change, value):

        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = value.toPoint()
            sceneRect = self.scene().sceneRect()
            gridTuple = self.scene().gridTuple
            viewRect = self.scene().views()[0].viewport().rect()
            # newPos.setX(round(newPos.x() / gridTuple[0]) * gridTuple[0])
            # newPos.setY(round(newPos.y() / gridTuple[1]) * gridTuple[1])
            # Keep the item inside the view rect.
            if not sceneRect.contains(newPos):
                # Keep the item inside the scene rect.
                if newPos.x() > sceneRect.right():
                    sceneRect.setRight(newPos.x())
                    viewRect.setRight(newPos.x())
                elif newPos.x() < sceneRect.left():
                    sceneRect.setLeft(newPos.x())
                    viewRect.setLeft(newPos.x())
                if newPos.y() > sceneRect.bottom():
                    sceneRect.setBottom(newPos.y())
                    viewRect.setBottom(newPos.y())
                elif newPos.y() < sceneRect.top():
                    sceneRect.setTop(newPos.y())
                    viewRect.setTop(newPos.y())
            return newPos
        elif change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            # self.mergeNets()
            self.extendDashLines()
            self.findDotPoints()
        elif change == QGraphicsItem.ItemSelectedHasChanged and self.scene():
            if value:
                self.scene().schematicWindow.messageLine.setText("Selected Net")
                self.mergeNets()
                self.findDotPoints()
            else:
                # self.removeDashedLines()
                # self.mergeNets()
                self.scene().schematicWindow.messageLine.setText("Unselected Net")
        return super().itemChange(change, value)

    def removeDashedLines(self):
        for netEndTuple in self._dashedLines:
            self.scene().removeItem(netEndTuple.net)
            del netEndTuple

    def contextMenuEvent(self, event):
        self.scene().itemContextMenu.exec_(event.screenPos())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.createDashLines()

    # def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     super().mouseMoveEvent(event)
    #     # self.extendDashLines()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        try:
            self.extendNets()
            self.removeDashedLines()
            self.mergeNets()
            self.findDotPoints()
        except Exception as e:
            self.scene().logger.error(f'Error in net.mouseReleaseEvent: {e}')


    def mergeNets(self):
        if self.horizontal:
            nets = {netItem for netItem in self.scene().items(
                self.sceneBoundingRect()) if (isinstance(netItem,schematicNet) and
                                        netItem.horizontal and netItem.pen is
                                              not self.scene().otherPen)}
            startXList = [netItem.start.x() for netItem in nets]
            endXList = [netItem.end.x() for netItem in nets]
            startXList.extend(endXList)
            startX = min(startXList)
            endX = max(startXList)
            # self.setLine(QLineF(startX, self.start.y(), endX, self.end.y()))
            self.start = QPoint(startX, self.start.y())
            self.end = QPoint(endX, self.end.y())
            for netItem in nets.difference({self}):
                self.scene().removeItem(netItem)
                del netItem
        else:
            nets = {netItem for netItem in self.scene().items(
                self.sceneBoundingRect()) if (isinstance(netItem,schematicNet)
                                and not netItem.horizontal and netItem.pen is
                                              not self.scene().otherPen)}
            startYList = [netItem.start.y() for netItem in nets]
            endYList = [netItem.end.y() for netItem in nets]
            startYList.extend(endYList)
            startY = min(startYList)
            endY = max(startYList)
            # self.setLine(QLineF(self.start.x(), startY, self.end.x(), endY))
            self.start = QPoint(self.start.x(),startY)
            self.end = QPoint(self.end.x(),endY)
            self.update()
            for netItem in nets.difference({self}):
                self.scene().removeItem(netItem)
                del netItem


class crossingDot(QGraphicsEllipseItem):
    def __init__(self, point: QPoint, radius: int, pen: QPen):
        self.radius = radius
        self._pen = pen
        self.point = point
        super().__init__(point.x() - radius, point.y() - radius, 2 * radius, 2 * radius)
        self.setPen(pen)
        self.setBrush(pen.color())

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.white, 2, Qt.SolidLine))
            painter.setBrush(Qt.white)
        else:
            painter.setPen(self._pen)
            painter.setBrush(self._pen.color())
        painter.drawEllipse(self.point, self.radius, self.radius)

class snapPointRect(QGraphicsRectItem):
    def __init__(self, centre:QPoint, width:int, pen: QPen):
        self._centre = centre
        self._width = width
        self._pen = pen
        snapRect = QRectF(QPointF(centre.x()-width*0.5, centre.y()-0.5*width), QPointF(
            centre.x()+width*0.5,centre.y()+width*0.5))

        super().__init__(snapRect)
        self.setRotation(90)

    def paint(self,painter,option,widget) -> None:
        painter.setPen(self._pen)
        painter.drawRect(self.rect)
