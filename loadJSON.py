# Load symbol and maybe later schematic from json file.

from PySide6.QtCore import (QDir, QLine, QRect, QRectF, QPoint, QPointF, QSize, Qt,) # QtCore
from PySide6.QtGui import (QAction, QKeySequence, QColor, QFont, QIcon, QPainter, QPen, QBrush, QFontMetrics,
                           QStandardItemModel, QTransform, QCursor, QUndoCommand, QUndoStack)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                               QFormLayout, QGraphicsLineItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox,
                               QPushButton, QRadioButton, QTabWidget, QToolBar, QTreeView, QVBoxLayout, QWidget,
                               QGraphicsItem, )

import shape as shp
import symbolEncoder as se

def createSymbolItems(item,gridTuple):
    '''
    Create symbol items from json file.
    '''
    if item["type"] == "rect":
        start = QPoint(item["rect"][0], item["rect"][1])
        end = QPoint(item["rect"][2], item["rect"][3])
        penStyle = Qt.PenStyle.__dict__[item["lineStyle"].split(".")[-1]]  # convert string to enum
        penWidth = item["width"]
        penColor = QColor(*item["color"])
        pen = QPen(penColor, penWidth, penStyle)
        pen.setCosmetic(item["cosmetic"])
        rect = shp.rectangle(start, end, pen, gridTuple)  # note that we are using grid values for scene
        rect.setPos(QPoint(item["location"][0], item["location"][1]), )
        return rect
    elif item["type"] == "line":
        start = QPoint(item["start"][0], item["start"][1])
        end = QPoint(item["end"][0], item["end"][1])
        penStyle = Qt.PenStyle.__dict__[item["lineStyle"].split(".")[-1]]
        penWidth = item["width"]
        penColor = QColor(*item["color"])
        pen = QPen(penColor, penWidth, penStyle)
        pen.setCosmetic(item["cosmetic"])
        line = shp.line(start, end, pen, gridTuple)
        line.setPos(QPoint(item["location"][0], item["location"][1]))
        return line
    elif item["type"] == "pin":
        start = QPoint(item["start"][0], item["start"][1])
        penStyle = Qt.PenStyle.__dict__[item["lineStyle"].split(".")[-1]]
        penWidth = item["width"]
        penColor = QColor(*item["color"])
        pen = QPen(penColor, penWidth, penStyle)
        pen.setCosmetic(item["cosmetic"])
        pin = shp.pin(
            start,
            pen,
            item["pinName"],
            item["pinDir"],
            item["pinType"],
            gridTuple,
        )
        pin.setPos(QPoint(item["location"][0], item["location"][1]))
        return pin
    elif item["type"] == "label":
        start = QPoint(item["start"][0], item["start"][1])
        penStyle = Qt.PenStyle.__dict__[item["lineStyle"].split(".")[-1]]
        penWidth = item["width"]
        penColor = QColor(*item["color"])
        pen = QPen(penColor, penWidth, penStyle)
        pen.setCosmetic(item["cosmetic"])
        label = shp.label(
            start,
            pen,
            item["labelName"],
            gridTuple,
            item["labelType"],
            item["labelHeight"],
            item["labelAlign"],
            item["labelOrient"],
            item["labelUse"],
        )
        label.setPos(QPoint(item["location"][0], item["location"][1]))
        return label
def createSymbolAttribute(item):
   if item["type"] == "attribute":
        return se.symbolAttribute(item["name"],item["attributeType"],item["definition"])
