import pathlib
import sys
from builtins import print
from datetime import datetime
from itertools import cycle
from platform import system

import numpy as np
import polars as pl
import pyqtgraph as pg
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QAction, QKeySequence, QIcon, QColor
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, QMenu, QToolBar,
                               QApplication, QFileDialog, QTabWidget, )

from . import resources as resources  # type: ignore
from .dataDefinitions import dataFrameTuple


class revedaPlotItem(pg.PlotItem):
    color_list = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b",
        "#e377c2", "#7f7f7f", "#bcbd22", "#17becf", ]
    colors = cycle(color_list)

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        grid_pen = pg.mkPen(color="#ffffff", width=1, style=Qt.DotLine)
        self.showGrid(x=True, y=True, alpha=0.5)
        self.getAxis("bottom").setPen(grid_pen)
        self.getAxis("left").setPen(grid_pen)
        self.setMenuEnabled(False)
        self.combined = True
        self.vline = None
        self.labelBar = QLabel()
        self.labelBar.setTextFormat(Qt.MarkdownText)
        self.labelBar.setContentsMargins(5, 5, 5, 5)
        self.parent.parentWidget().labelBarLayout.addWidget(self.labelBar)
        self.xarray = np.ndarray(0, )
        self.markers = []
        self._setupActions()

    def plot(self, *args, **kwargs):
        if "pen" not in kwargs:
            kwargs["pen"] = pg.mkPen(next(self.colors), width=1)
        item = super().plot(*args, **kwargs)
        return item

    def multiDataPlot(self, *, x=None, y=None, constKwargs=None, **kwargs):
        """Override to match parent signature and return list of plot items."""
        items = []
        if x is not None and y is not None:
            for i in range(y.shape[1]):
                item = self.plot(x=x, y=y[:, i], **kwargs)
                items.append(item)
        return items

    def contextMenuEvent(self, ev):
        menu = QMenu()
        pos = QPoint(int(ev.screenPos().x()), int(ev.screenPos().y()))
        menu.addAction(self.clearAction)
        menu.addAction(self.xZoomAction)
        menu.addAction(self.yZoomAction)
        menu.addAction(self.fitAllAction)
        menu.addAction(self.combinedPlotAction)
        menu.addAction(self.addVlineAction)
        menu.exec(pos)

    def _setupActions(self):
        self.clearAction = QAction("Clear Plot", self)
        self.clearAction.setShortcut(QKeySequence("Ctrl+X"))
        self.clearAction.triggered.connect(self.clear)
        self.xZoomAction = QAction("X-axis Zoom", self)
        self.yZoomAction = QAction("Y-axis Zoom", self)
        self.fitAllAction = QAction("Fit All", self)
        self.xZoomAction.triggered.connect(self.xAxisZoom)
        self.yZoomAction.triggered.connect(self.yAxisZoom)
        self.fitAllAction.triggered.connect(self.vb.autoRange)
        self.combinedPlotAction = QAction("Combined Plot", self)
        self.combinedPlotAction.setCheckable(True)
        self.combinedPlotAction.setChecked(self.combined)
        self.combinedPlotAction.triggered.connect(self.toggleCombined)
        self.addVlineAction = QAction("Add Vertical Line", self)
        self.addVlineAction.setCheckable(True)
        self.addVlineAction.setChecked(False)
        self.addMarkerAction = QAction("Add a marker", self)
        self.addMarkerAction.setCheckable(True)
        self.addMarkerAction.setChecked(False)

        # self.combinedAction.setShortcut(QKeySequence("Ctrl+Shift+C"))

    def setupConnections(self):
        self.scene().sigMouseMoved.connect(self._handleMouseMove)
        self.scene().sigMouseClicked.connect(self._handleMouseClick)

    def _handleMouseMove(self, pos: QPointF):
        # Check if the click is within this plot item's bounds
        if self.sceneBoundingRect().contains(pos):
            mousePoint = self.vb.mapSceneToView(pos)
            xpos, ypos = mousePoint.x(), mousePoint.y()
            # Update the status bar with the coordinates
            if self.vline is not None and self.addVlineAction.isChecked():
                self.vline.setPos(
                    xpos)  # if hasattr(self.parent, 'statusBar'):  #     self.parent.statusBar().showMessage(f"X: {xpos:.2f}, Y: {ypos:.2f}")

    def _handleMouseClick(self, event):
        pos = event.scenePos()  # Check if the click is within this plot item's bounds
        if event.button() == Qt.LeftButton and self.sceneBoundingRect().contains(pos):
            self.parent.selectedPlot = self
            if self.addVlineAction.isChecked():
                mousePoint = self.vb.mapSceneToView(pos)
                xpos = mousePoint.x()
                # Call toggleVerticalLine with the x position of the click
                if self.vline is None:
                    # Create new vertical line
                    self.vline = pg.InfiniteLine(pos=xpos, angle=90, movable=True,
                        pen=pg.mkPen("r", width=2))
                    self.addItem(self.vline)
                    self.xarray = self.listDataItems()[0].xData
                    self.vline.setBounds((self.xarray[0], self.xarray[-1]))
                    self.parent.parentWidget().labelBarLayout.addWidget(self.labelBar)
                    self.vline.sigPositionChanged.connect(
                        lambda: self._handleVlinePosChanged(self.xarray, self.vline))

    def _handleVlinePosChanged(self, xarray: np.ndarray, line: pg.InfiniteLine):
        # This method is called when the vertical line is dragged

        xpos = line.pos().x()
        # Print the interpolated y value for each curve at the vertical line position
        ystring = ""
        for curve in self.listDataItems():
            yarray = curve.yData
            yinterpolated = np.interp(xpos, xarray, yarray)
            # Update the label bar with the interpolated y value
            ystring += f"{pg.siFormat(yinterpolated)}, "
        self.labelBar.setText(f"**x-value**: {pg.siFormat(xpos)}, **y-values**: {ystring}")

    def toggleVerticalLine(self):
        if self.addVlineAction.isChecked():
            self.addVlineAction.setChecked(False)
            self.removeItem(self.vline)
            self.parent.parentWidget().clearLabels()
            self.labelBar = QLabel()
            self.labelBar.setTextFormat(Qt.MarkdownText)
            self.labelBar.setContentsMargins(5, 5, 5, 5)
            self.parent.parentWidget().labelBarLayout.addWidget(self.labelBar)
            self.vline = None
        else:
            self.addVlineAction.setChecked(True)

    def xAxisZoom(self):
        vb = self.getViewBox()
        if vb and hasattr(self, "context_pos"):
            # Convert mouse position to data coordinates
            mouse_point = vb.mapSceneToView(self.context_pos)
            center_x = mouse_point.x()

            # Get current x range
            x_range = vb.viewRange()[0]
            current_width = x_range[1] - x_range[0]
            new_width = current_width * 0.5  # 50% zoom

            # Calculate new range centered on mouse position
            new_min = center_x - new_width / 2
            new_max = center_x + new_width / 2

            vb.setXRange(new_min, new_max)

    def yAxisZoom(self):
        vb = self.getViewBox()
        if vb and hasattr(self, "context_pos"):
            # Convert mouse position to data coordinates
            mouse_point = vb.mapSceneToView(self.context_pos)
            center_y = mouse_point.y()

            # Get current x range
            y_range = vb.viewRange()[0]
            current_width = y_range[1] - y_range[0]
            new_width = current_width * 0.5  # 50% zoom

            # Calculate new range centered on mouse position
            new_min = center_y - new_width / 2
            new_max = center_y + new_width / 2

            vb.setXRange(new_min, new_max)

    def resetColors(self):
        self.colors = cycle(self.color_list)

    def toggleCombined(self):
        self.combined = not self.combined
        self.parent.setCombined(self.combined)

    def findClosestIndex(self, dataArray: np.ndarray, xpos: float):
        idx = np.searchsorted(dataArray, xpos)
        if idx == 0:
            return (0, 1)
        elif idx == len(dataArray):
            return (len(dataArray) - 1,)
        else:
            left = dataArray[idx - 1]
            right = dataArray[idx]
            return (left, right)


class revedaLayoutWidget(pg.GraphicsLayoutWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setBackground("k")
        self.plots = []
        self.combined = True
        self.dft = dataFrameTuple(pl.DataFrame(), "", "")
        self.xcolumn = 0
        self.ycolumns = [1]
        self._selectedPlot = None

    def addTitle(self, title: str):
        self.titleItem = pg.LabelItem(title, size="16pt", color="#ffff00", )
        self.addItem(self.titleItem, row=0, col=0, colspan=2)

    def addPlotRow(self, row: int, plotItem=None):
        self.nextRow()
        if plotItem is not None:
            self.addItem(plotItem, row=row, col=1)
        else:
            plotItem = revedaPlotItem(self)
            self.addItem(plotItem, row=row, col=1)
        plotItem.setupConnections()
        self.plots.append(plotItem)

        # Use custom ViewBox for legend
        legendVB = CustomLegendViewBox(lockAspect=True)
        self.addItem(legendVB, row=row, col=0)
        legendVB.setMaximumWidth(200)

        return plotItem, legendVB

    def plotData(self, dft: dataFrameTuple, xcolumn: int, ycolumns: list[int]):
        # sort the DataFrame by the xcolumn
        dataFrame = dft.dataFrame.sort(by=dft.dataFrame.columns[xcolumn], descending=False)
        self.dft = dataFrameTuple(header=dft.header, dataFrame=dataFrame,
            columnTag=dft.columnTag, )
        self.xcolumn = xcolumn
        self.ycolumns = ycolumns
        self.addTitle(f"{self.dft.header}:{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        legends = [self.processLegendText(self.dft.dataFrame.columns[ycol]) for ycol in
            ycolumns]
        if self.combined:
            plotItem, legendVB = self.addPlotRow(1)
            plotItem.multiDataPlot(x=self.dft.dataFrame[:, xcolumn],
                y=self.dft.dataFrame[:, ycolumns])
            plotCurves = plotItem.listDataItems()
            plotItem.getAxis("bottom").setLabel(
                text=self.processLegendText(self.dft.dataFrame.columns[xcolumn]))
            plotItem.combined = True
            legendItem = pg.LegendItem()
            legendVB.addItem(legendItem)
            for i in range(len(legends)):
                legendItem.addItem(plotCurves[i], legends[i])
                legendItem.setPos(0, -20 - i * 20)
        else:
            for i, ycol in enumerate(ycolumns):
                plotItem, legendVB = self.addPlotRow(i + 1)
                plotItem.plot(x=dft.dataFrame[:, xcolumn], y=dft.dataFrame[:, ycol])
                # plotItem.scatterPlot(
                #     x=self.dft.dataFrame[:, xcolumn],
                #     y=self.dft.dataFrame[:, ycol],
                #     pen=pg.mkPen(next(revedaPlotItem.colors), width=1),
                #     symbol='o',
                #     size=5,
                # )
                plotItem.combined = False
                plotItem.getAxis("bottom").setLabel(
                    text=self.processLegendText(self.dft.dataFrame.columns[xcolumn]))
                legendItem = pg.LegendItem()
                legendVB.addItem(legendItem)
                legendItem.addItem(plotItem.listDataItems()[0], legends[i])
                legendItem.setPos(0, -100)

    def clearPlots(self):
        self.clear()

    def setCombined(self, combined: bool):
        self.combined = combined
        self.clearPlots()
        self.plots = []
        self.parentWidget().clearLabels()
        # Reset colors for all new plot items
        revedaPlotItem.colors = cycle(revedaPlotItem.color_list)
        self.plotData(self.dft, self.xcolumn, self.ycolumns)
        # Update all plot items' action states
        for plot in self.plots:
            plot.combinedPlotAction.setChecked(combined)

    def exportPlots(self, filename):
        originalBrush = self.backgroundBrush()
        self.setBackgroundBrush(QColor(Qt.white))
        exporter = pg.exporters.ImageExporter(self.scene())
        exporter.export(filename)
        self.setBackgroundBrush(originalBrush)

    def processLegendText(self, columnName: str):
        if columnName.endswith("#branch"):
            return f"I({columnName[:-7]})"  # Remove the '#branch' suffix
        else:
            return f"V({columnName})"

    @property
    def selectedPlot(self):
        if self._selectedPlot is not None:
            return self._selectedPlot
        else:
            return self.plots[0]

    @selectedPlot.setter
    def selectedPlot(self, pItem: pg.PlotItem):
        self._selectedPlot = pItem


class revedaPlotTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("revedaPlotTabWidget")
        self.mainLayout = QVBoxLayout(self)
        self.labelBarLayout = QVBoxLayout()
        self.mainLayout.addLayout(self.labelBarLayout)
        self.labelBarLayout.setContentsMargins(5, 5, 5, 5)
        self.layoutWidget = revedaLayoutWidget(self)
        self.mainLayout.addWidget(self.layoutWidget)
        self.setLayout(self.mainLayout)

    def clearLabels(self):
        """Clear all labels in the label bar."""
        for i in reversed(range(self.labelBarLayout.count())):
            widget = self.labelBarLayout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.labelBarLayout = QVBoxLayout()
        self.labelBarLayout.setContentsMargins(5, 5, 5, 5)
        self.mainLayout.insertLayout(0, self.labelBarLayout)


class revedaPlotMain(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.appMainW = parent.appMainW if parent else None
        self.setWindowTitle("Reveda Plot Main Window")
        self.setGeometry(100, 100, 1000, 800)
        self.centralWidget = QTabWidget(self)  # type: ignore
        self.centralWidget.setTabsClosable(True)
        self.setCentralWidget(self.centralWidget)  # type: ignore
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)
        self._setup_actions()
        self._connect_actions()
        self._setup_menu()

        self.setup_toolbar()

    def _setup_menu(self):
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        # File menu with export options
        file_menu = menubar.addMenu("&File")
        export_menu = file_menu.addMenu("&Export")
        export_menu.addAction(self.export_png_action)
        export_menu.addAction(self.export_jpg_action)
        file_menu.addAction(self.exitAction)

        # View menu for plot options
        view_menu = menubar.addMenu("&View")

        # These will be populated when a tab is added
        self.plot_type_menu = view_menu.addMenu("&Plot Type")
        self.plot_type_menu.addAction(self.combinedAction)
        self.plot_type_menu.addAction(self.separateAction)

    def _setup_actions(self):
        exitIcon = QIcon(":/icons/external.png")
        combinedIcon = QIcon(":icons/image.png")
        separateIcon = QIcon(":icons/images.png")
        vlineIcon = QIcon(":icons/pencil-ruler.png")
        markerIcon = QIcon(":icons/marker--pencil.png")
        clearIcon = QIcon(":icons/eraser.png")

        self.exitAction = QAction(exitIcon, "Exit", self)
        self.exitAction.setShortcut("Ctrl+Q")
        self.exitAction.setStatusTip("Exit application")

        self.combinedAction = QAction(combinedIcon, "&Combined Plot", self)
        self.combinedAction.setShortcut(QKeySequence("Ctrl+C"))
        self.combinedAction.setCheckable(True)
        self.combinedAction.setChecked(True)

        self.separateAction = QAction(separateIcon, "&Separate Plots", self)
        self.separateAction.setShortcut(QKeySequence("Ctrl+S"))
        self.separateAction.setCheckable(True)
        self.separateAction.setChecked(False)

        self.clearAction = QAction(clearIcon, "&Clear", self)
        self.clearAction.setShortcut(QKeySequence("Ctrl+L"))
        self.clearAction.setStatusTip("Clear the plot")

        self.vlineAction = QAction(vlineIcon, "Toggle &Vertical Line", self)
        self.vlineAction.setShortcut(QKeySequence("Ctrl+V"))
        self.vlineAction.setStatusTip("Toggle vertical line")
        self.vlineAction.setCheckable(True)

        self.marker_action = QAction(markerIcon, "Toggle &Marker Mode", self)
        self.marker_action.setShortcut(QKeySequence("Ctrl+M"))
        self.marker_action.setStatusTip("Toggle marker mode")
        self.marker_action.setCheckable(True)

        # Export actions
        exportIcon = QIcon(":icons/image-export.png")  # Placeholder icon
        self.export_png_action = QAction(exportIcon, "Export to &PNG", self)
        self.export_png_action.setShortcut(QKeySequence("Ctrl+P"))

        self.export_jpg_action = QAction(exportIcon, "Export to &JPEG", self)
        self.export_jpg_action.setShortcut(QKeySequence("Ctrl+J"))

        # zoom in x and y
        self.zoom_in_x_action = QAction("Zoom In X", self)
        self.zoom_in_x_action.setShortcut(QKeySequence("Ctrl++"))
        self.zoom_in_y_action = QAction("Zoom In Y", self)
        self.zoom_in_y_action.setShortcut(QKeySequence("Ctrl+="))

    def _connect_actions(self):
        # # Connect actions to the current tab's methods
        self.combinedAction.triggered.connect(lambda: self.setCombined(True))
        self.separateAction.triggered.connect(lambda: self.setCombined(False))
        self.vlineAction.triggered.connect(self.toggleVLine)
        # self.marker_action.triggered.connect(
        #     lambda: self.tabsWidget.currentWidget().toggle_marker_mode()
        # )

        self.export_png_action.triggered.connect(lambda: self.exportPlot("png"))
        # self.export_jpg_action.triggered.connect(
        #     lambda: self.tabsWidget.currentWidget()._export_plot("jpg")
        # )
        self.exitAction.triggered.connect(self.closeWindow)
        self.clearAction.triggered.connect(
            lambda: self.centralWidget.currentWidget().layoutWidget.clearPlots())

    def setCombined(self, combined: bool):
        """Set the plot type (combined or separate) for the current tab."""
        if combined:
            self.combinedAction.setChecked(True)
            self.separateAction.setChecked(False)
        else:
            self.combinedAction.setChecked(False)
            self.separateAction.setChecked(True)
        self.centralWidget.currentWidget().layoutWidget.setCombined(combined)

    def toggleVLine(self):
        self.centralWidget.currentWidget().layoutWidget.selectedPlot.toggleVerticalLine()

    def exportPlot(self, format):
        """Export the current plot to the specified format."""
        if format.lower() == "png":
            fileFilter = "PNG Files (*.png)"
            ext = ".png"
            imgFormat = "PNG"
        else:
            fileFilter = "JPEG Files (*.jpg *.jpeg)"
            ext = ".jpg"
            imgFormat = "JPEG"
        filePath, _ = QFileDialog.getSaveFileName(self, f"Export Plot as {format.upper()}",
            "", fileFilter)
        if not filePath:
            return
        if not filePath.lower().endswith(ext):
            filePath += ext
        self.centralWidget.currentWidget().layoutWidget.exportPlots(filePath)

    def closeWindow(self):
        """Close the main window."""
        plotViewTuple = viewTuple(self.appMainW.libraryItem.libraryName,
            self.appMainW.cellItem.cellName, "revedaPlot", )
        self.appMainW.openViews.pop(plotViewTuple, None)
        self.close()

    def setup_toolbar(self):
        self.toolbar.addAction(self.combinedAction)
        self.toolbar.addAction(self.separateAction)
        self.toolbar.addAction(self.clearAction)
        self.toolbar.addAction(self.exitAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.vlineAction)
        self.toolbar.addAction(self.marker_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.export_png_action)
        self.toolbar.addAction(self.export_jpg_action)

    def plotData(self, dft: dataFrameTuple, xcolumn: int, ycolumns: list,
            combined: bool = True, ):
        tabIndex = self.centralWidget.addTab(revedaPlotTabWidget(self.centralWidget),
            "Plot")
        self.centralWidget.setCurrentIndex(tabIndex)
        tabWidget: revedaPlotTabWidget = self.centralWidget.widget(tabIndex)
        self.centralWidget.setTabText(tabIndex, f"Plot-{tabIndex}")
        tabWidget.combined = combined
        tabWidget.layoutWidget.plotData(dft, xcolumn, ycolumns)


class CustomLegendViewBox(pg.ViewBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMenuEnabled(False)  # Disable default pyqtgraph context menu
        self.menu = None
        self._setup_actions()

    def _setup_actions(self):
        self.resetAction = QAction("Reset Legend Position", self)
        self.resetAction.triggered.connect(self._reset_position)

    def _reset_position(self):
        # Reset to default position
        self.setRange(xRange=(-100, 100), yRange=(-100, 100))

    def raiseContextMenu(self, ev):
        menu = QMenu()
        menu.addAction(self.resetAction)
        menu.exec(ev.screenPos().toPoint())

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.RightButton:
            ev.accept()
            self.raiseContextMenu(ev)
        else:
            super().mouseClickEvent(ev)


def main_raw():
    # Create QApplication instance
    app = QApplication(sys.argv)
    mainWindow = revedaPlotMain()
    import processRawFile as prf
    if system() == "Linux":
        filepath = pathlib.Path(
            "/home/eskiyerli/onedrive_reveda/Projects/testbenches/commonSourceAmp/revbench"
            "/commonSourceAmp_tran.raw")
    elif system() == "Windows":
        filepath = pathlib.Path(
            "C:\\Users\\eskiye50\\OneDrive - Revolution Semiconductor\\Projects\\testbenches\\commonSourceAmp\\revbench\\commonSourceAmp_tran.raw")

    dataObj = prf.RawDataObj(filepath)
    for i, dft in enumerate(dataObj.getDataFrames()):
        print(dft.dataFrame.columns)
        mainWindow.plotData(dft, xcolumn=1, ycolumns=[1, 2, 3], combined=False)

    mainWindow.show()
    app.exec()


def main_ascii():
    # Create QApplication instance
    app = QApplication(sys.argv)
    mainWindow = revedaPlotMain()
    import processAsciFile as paf
    if system() == "Linux":
        filepath = pathlib.Path(
            "/home/eskiyerli/onedrive_reveda/Projects/testbenches/commonSourceAmp/revbench_win/commonSourceAmp_hb.sp.HB.FD.prn")
    elif system() == "Windows":
        filepath = pathlib.Path(
            "C:\\Users\\eskiye50\\OneDrive - Revolution Semiconductor\\Projects\\testbenches\\commonSourceAmp\\revbench\\commonSourceAmp_tran.txt")

    dataObj = paf.AsciiDataObj(filepath)
    for i, dft in enumerate(dataObj.getDataFrames()):
        mainWindow.plotData(dft, xcolumn=0, ycolumns=[1, 2, 3, 4], combined=False)

    mainWindow.show()
    app.exec()


if __name__ == "__main__":
    main_ascii()
