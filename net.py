# net class definition.
from PySide6.QtGui import (QPen, QColor, )
from PySide6.QtCore import (QPoint, Qt, QMargins)
from PySide6.QtWidgets import (QGraphicsLineItem, QGraphicsItem,
                               QGraphicsEllipseItem, QGraphicsSceneMouseEvent, )

# import shape as shp
# import math
import net


class schematicNet(QGraphicsLineItem):
    uses = ["SIGNAL", "ANALOG", "CLOCK", "GROUND", "POWER", ]

    def __init__(self, start: QPoint, end: QPoint, pen: QPen, name: str
                 ):
        assert isinstance(pen, QPen)
        self.pen = pen
        self.name = name
        self.horizontal = True
        self.start = start
        self.end = end

        x1, y1 = self.start.x(), self.start.y()
        x2, y2 = self.end.x(), self.end.y()
        if abs(x1 - x2) >= abs(y1 - y2):  # horizontal
            self.horizontal = True
            self.start = QPoint(min(x1, x2), y1)
            self.end = QPoint(max(x1, x2), y1)
            super().__init__(self.start.x(), y1, self.end.x(), y1)
        else:
            self.horizontal = False
            self.start = QPoint(x1, min(y1, y2))
            self.end = QPoint(x1, max(y1, y2))
            super().__init__(x1, self.start.y(), x1, self.end.y())

        self.setPen(self.pen)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

    def paint(self, painter, option, widget) -> None:
        if self.isSelected():
            painter.setPen(QPen(Qt.white, 2, Qt.SolidLine))
        else:
            painter.setPen(self.pen)
        painter.drawLine(self.start, self.end)

    def setName(self, name):
        self.name = name

    def itemChange(self, change, value):

        if change == QGraphicsItem.ItemPositionChange and self.scene():
            newPos = value.toPoint()
            sceneRect = self.scene().sceneRect()
            gridTuple = self.scene().gridTuple
            viewRect = self.scene().views()[0].viewport().rect()
            newPos.setX(round(newPos.x() / gridTuple[0]) * gridTuple[0])
            newPos.setY(round(newPos.y() / gridTuple[1]) * gridTuple[1])

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
        return super().itemChange(change, value)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.scene().drawWire:
            self.setFlag(QGraphicsItem.ItemIsSelectable, False)
            self.setFlag(QGraphicsItem.ItemIsMovable, False)
        else:
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        newNet = True
        dnetBRect = self.mapRectToScene(self.boundingRect()).toRect()
        viewRect = self.scene().parent.view.mapToScene(
            self.scene().parent.view.viewport().rect()
            ).boundingRect()
        netsInView = [item for item in self.scene().items(viewRect) if
                      isinstance(item, net.schematicNet)]
        scene = self.scene()
        # print(f'nets in view {netsInView}')
        # check any overlapping nets in the view
        # editing is done in the view and thus there is no need to check all nets in the scene
        for netItem in netsInView:
            netItemBRect = netItem.mapRectToScene(
                netItem.boundingRect()
                ).toRect()
            if dnetBRect.intersects(netItemBRect) and netItem != self:
                if self.horizontal and netItem.horizontal:
                    mergedRect = dnetBRect.united(
                        netItemBRect
                        )  # create a merged horizontal rectangle
                    print(mergedRect)
                    scene.removeItem(
                        netItem
                        )  # remove the old net from the scene
                    scene.removeItem(
                        self
                        )  # remove the drawn net from the scene
                    scene.schematicNets[netItem.name].remove(
                        netItem
                        )  # remove the old net from the nets dict
                    self = scene.netDraw(
                        mergedRect.bottomLeft(), mergedRect.bottomRight(),
                        scene.wirePen, netItem.name
                        )  # create a new net with the merged rectangle
                    print(self.boundingRect().width())
                    scene.schematicNets[netItem.name].extend(
                        [self]
                        )  # add the new net to the list
                    scene.addItem(self)  # add the new net to the scene
                    scene.parent.parent.messageLine.setText(
                        "Net merged"
                        )  # newNet = False
        #         elif not (drawnNet.horizontal or netItem.horizontal):
        #             mergedRect = dnetBRect.united(
        #                 netItem.boundingRect()
        #                 ).toRect()  # create a merged horizontal rectangle
        #             self.removeItem(
        #                 netItem
        #                 )  # remove the old net from the scene
        #             self.removeItem(
        #                 drawnNet
        #                 )  # remove the drawn net from the scene
        #             self.schematicNets[netItem.name].remove(
        #                 netItem
        #                 )  # remove the old net from the net list
        #             netItem = self.netDraw(
        #                 mergedRect.bottomRight(),
        #                 mergedRect.topLeft(),
        #                 self.wirePen, netItem.name
        #                 )  # create a new net with the merged rectangle
        #             self.schematicNets[netItem.name].extend(
        #                 [
        #                     netItem]
        #                 )  # add the new net to the list
        #             self.addItem(netItem)  # add the new net to the scene
        #             self.parent.parent.messageLine.setText(
        #                 "Net merged"
        #                 )
        #             newNet = False
        #         # drawn net is horizontal and existing net is vertical
        #         # drawn net is split into two nets
        #         elif drawnNet.horizontal and not netItem.horizontal:
        #             crossRectCenter = dnetBRect.intersected(
        #                 netItem.boundingRect()
        #                 ).center()
        #             # check if crossing point is either end of existing net
        #             if (
        #                     netItem.start.y() == crossRectCenter.y()
        #                     or netItem.end.y() == crossRectCenter.y()
        #             ) and not (
        #                     drawnNet.start.x() == crossRectCenter.x()
        #                     or drawnNet.end.x() == crossRectCenter.x()):
        #                 net1 = self.netDraw(
        #                     drawnNet.start, crossRectCenter,
        #                     self.wirePen, netItem.name
        #                     )
        #                 net2 = self.netDraw(
        #                     crossRectCenter, drawnNet.end,
        #                     self.wirePen,
        #                     netItem.name
        #                     )
        #                 # remove net from scene after splitting
        #                 self.removeItem(drawnNet)
        #                 # add split nets
        #                 self.addItem(net1)
        #                 self.addItem(net2)
        #                 self.schematicNets[netItem.name].extend(
        #                     [
        #                         net1, net2]
        #                     )
        #                 self.parent.parent.messageLine.setText(
        #                     "Net split"
        #                     )
        #                 newNet = False
        #
        #         elif not drawnNet.horizontal and netItem.horizontal:
        #             crossRectCenter = dnetBRect.intersected(
        #                 netItem.boundingRect()
        #                 ).center()
        #             # check if crossing point is either end of existing net
        #             if (
        #                     netItem.start.x() == crossRectCenter.x()
        #                     or netItem.end.x() == crossRectCenter.x()
        #             ) and not (
        #                     drawnNet.start.y() == crossRectCenter.y()
        #                     or drawnNet.end.y() == crossRectCenter.y()):
        #                 net1 = self.netDraw(
        #                     drawnNet.start, crossRectCenter,
        #                     self.wirePen, netItem.name
        #                     )
        #                 net2 = self.netDraw(
        #                     crossRectCenter, drawnNet.end,
        #                     self.wirePen,
        #                     netItem.name
        #                     )
        #                 # remove net from scene after splitting
        #                 self.removeItem(drawnNet)
        #                 # add split nets
        #                 self.addItem(net1)
        #                 self.addItem(net2)
        #                 self.schematicNets[netItem.name].extend(
        #                     [
        #                         net1, net2]
        #                     )
        #                 self.parent.parent.messageLine.setText(
        #                     "Net split"
        #                     )
        #                 newNet = False
        # dnetBRect = self.mapRectToScene(self.boundingRect()).toRect()
        # netMergedFlag = False
        # netAddedFlag = False
        # # check if it intersects another net and merge them.
        # for name, netItemList in self.scene().schematicNets.items():
        #     for netItem in netItemList:
        #         netItemBRect = netItem.mapRectToScene(netItem.boundingRect()).toRect()
        #         if netItem.name != self.name and dnetBRect.intersects(netItemBRect):
        #             if self.horizontal and netItem.horizontal:
        #                 netMergedFlag = self.mergeHorizontalNets(dnetBRect, netItem, netItemBRect)
        #             elif not (self.horizontal or netItem.horizontal):
        #                 netMergedFlag = self.mergeVerticalNets(dnetBRect, netItem, netItemBRect)
        #             elif self.horizontal and not netItem.horizontal:
        #                 crossRect = dnetBRect.intersected(netItemBRect).marginsAdded(
        #                     QMargins(2, 2, 2, 2))
        #                 crossRectCenter = crossRect.center()
        #             # check if the net is starts or ends in the existing net.
        #                 if not (netItem.start.y() < crossRectCenter.y() < netItem.end.y()):
        #                     crossDot = QGraphicsEllipseItem(crossRect)  # create a dot to mark the cross net
        #                     crossDot.setPen(self.pen)
        #                     crossDot.setBrush(self.pen.color())
        #                     crossDot.setParentItem(self)
        #                     self.scene().addItem(crossDot)
        #                     self.name = netItem.name  # get the net name from the connected net
        #                     netAddedFlag = True

        super().mouseReleaseEvent(event)

# class net:
#     def __init__(self, name: str, pins:list, instPins:list, cellview: str):
#         self.name = name
#         self.pins = pins
#         self.instPins = instPins
#         self.cellview = cellview
#         self.uses = [
#             "DB_SIGNAL",
#             "DB_ANALOG",
#             "DB_CLOCK",
#             "DB_GROUND",
#             "DB_POWER",
#             "DB_RESET",
#             "DB_SCAN",
#             "DB_TIEOFF",
#             "DB_TIEHI",
#             "DB_TIELO",
#         ]
#         self.use = "DB_SIGNAL"  # default use
#         self.sources = ['DB_DIST', 'DB_NETLIST', 'DB_TEST', 'DB_TIMING', 'DB_USER',]
#         self.source = 'DB_DIST'  # default source
#         self.global_ = False  # default not global
#         self.special = False  # default not special
#
#
#     def __str__(self):
#         return self.name
#
#     def __repr__(self):
#         return self.name
#
#     def __eq__(self, other):
#         return self.name == other.cellName
#
#     def cellview(self):
#         return self.cellview
#
#     def pins(self):
#         return self.pins
#
#     def instPins(self):
#         return self.instPins
#
#     def name(self, *args):
#         if len(args) == 0:
#             return self.name
#         elif len(args) == 1:
#             self.name = args[0]
#         else:
#             raise ValueError("Invalid number of arguments")
#
#     def objType(self):
#         return "NET"
#
#     def objName(self):
#         return "NET"
#
#     def cellView(self):
#         return self.cellview
#
#     def setUse(self, use):
#         if use in self.uses:
#             self.use = use
#         else:
#             raise ValueError("Invalid use")
#
#     def use(self): # returns use number of net
#         return self.uses.index(self.use)
#
#     def getUseStr(self):
#         return self.use
#
#     def setSource(self,source):
#         if source in self.sources:
#             self.source = source
#         else:
#             raise ValueError("Invalid source")
#
#     def source(self): # returns source number of net
#         return self.sources.index(self.source)
#
#     def getSourceStr(self):
#         return self.source
#
#     def setGlobal(self, global_):
#         self.global_ = True
#
#     def isGlobal(self):
#         return self.global_
#
#     def setSpecial(self, special):
#         self.special = True
#
#     def isSpecial(self):
#         return self.special
#
#     def setPins(self, pins):
#         self.pins = pins
#
#
