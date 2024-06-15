########################################################################
#
# Copyright 2023 IHP PDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
########################################################################

# This file contains the implementation of the IHP PDK in Revolution EDA.
# Therefore, it complies with the license assigned by the IHP.

import math
import os

from PySide6.QtCore import QPoint, QPointF, QRectF
from PySide6.QtGui import (
    QFontDatabase,
    QFont,
)
from dotenv import load_dotenv
from quantiphy import Quantity
from functools import lru_cache

import revedaEditor.backend.dataDefinitions as ddef
import revedaEditor.common.layoutShapes as lshp
from pdk.sg13_tech import SG13_Tech as sg13

load_dotenv()

if os.environ.get("REVEDA_PDK_PATH"):
    import pdk.layoutLayers as laylyr
    import pdk.process as fabproc
else:
    import defaultPDK.layoutLayers as laylyr
    import defaultPDK.process as fabproc


class baseCell(lshp.layoutPcell):
    """
    Base class for all layout parametric cells.
    """

    techClass = sg13()
    _techParams = techClass.techParams
    _sg13grid = Quantity(_techParams["grid"]).real
    _epsilon = _techParams["epsilon1"]
    heatTransLayer = laylyr.HeatTrans_drw

    @classmethod
    def GridFix(cls, x):

        return cls.fix(x / cls._sg13grid + cls._epsilon) * cls._sg13grid

    @staticmethod
    def fix(value):
        if isinstance(value, float):
            return int(math.floor(value))
        else:
            return value

    def __init__(self, shapes=list):
        super().__init__(shapes)
        fontFamilies = QFontDatabase().families()
        fontFamily = [
            font for font in fontFamilies if QFontDatabase().isFixedPitch(font)
        ][0]
        self._fixedFont = QFont(fontFamily, 16)
        self._labelFontStyle = self._fixedFont.styleName()
        self._labelFontFamily = self._fixedFont.family()
        self._labelFontSize = self._fixedFont.pointSize()
        self._labelFontTuple = (
            self._labelFontFamily,
            self._labelFontStyle,
            self._labelFontSize,
        )

    @staticmethod
    def oddp(value):
        """
        Returns True if value is odd, False if value is even.
        """
        return bool(value & 1)


    # ***********************************************************************************************************************
    # contactArray
    # ***********************************************************************************************************************
    def contactArray(
        self,
        pathLayer: ddef.layLayer | int,
        contLayer: ddef.layLayer,
        xl,
        yl,
        xh,
        yh,
        ox,
        oy,
        ws,
        ds,
    ):
        eps = baseCell._epsilon

        w = xh - xl
        h = yh - yl

        mlist = list()

        nx = int(math.floor((w - ox * 2 + ds) / (ws + ds) + eps))

        if nx <= 0:
            return mlist

        if nx == 1:
            dsx = 0
        else:
            dsx = (w - ox * 2 - ws * nx) / (nx - 1)

        ny = int(math.floor((h - oy * 2 + ds) / (ws + ds) + eps))
        if ny <= 0:
            return mlist

        if ny == 1:
            dsy = 0
        else:
            dsy = (h - oy * 2 - ws * ny) / (ny - 1)

        x = 0
        if nx == 1:
            x = (w - ws) / 2
        else:
            x = ox

        if pathLayer:
            point1 = self.toSceneCoord(QPointF(xl, yl))
            point2 = self.toSceneCoord(QPointF(xh, yh))
            mlist.append(lshp.layoutRect(point1, point2, pathLayer))

        for i in range(int(nx)):
            # for(i=1; i<=nx; i++) {
            y = 0
            if ny == 1:
                y = (h - ws) / 2
            else:
                y = oy

            for j in range(int(ny)):
                point1 = self.toSceneCoord(
                    QPointF(xl + baseCell.GridFix(x), yl + baseCell.GridFix(y))
                )
                point2 = self.toSceneCoord(
                    QPointF(
                        xl + baseCell.GridFix(x + ws), yl + baseCell.GridFix(y + ws)
                    )
                )
                mlist.append(lshp.layoutRect(point1, point2, contLayer))
                # for(j=1; j<=ny; j++) {
                # mlist.append(dbCreateRect(self, contLayer,
                #                           Box(xl + tog(x), yl + tog(y), xl + tog(x + ws),
                #                               yl + tog(y + ws))))
                y = y + ws + dsy

            x = x + ws + dsx

        if pathLayer:
            point1 = self.toSceneCoord(QPointF(xl, yl))
            point2 = self.toSceneCoord(QPointF(xh, yh))
            # mlist.append(dbCreateRect(self, pathLayer, Box(xl, yl, xh, yh)))
            mlist.append(lshp.layoutRect(point1, point2, pathLayer))
        return mlist

    def ihpAddThermalLayer(self, heatLayer:ddef.layLayer, point1: QPoint, point2: QPoint, addThermalText:bool, labelText: str):
        shapes = []
        center = QRectF(point1, point2).center()
        shapes.append(lshp.layoutRect(point1, point2, heatLayer))
        
        if addThermalText:
            shapes.append(lshp.layoutLabel(
                center,
                labelText,
                *self._labelFontTuple,
                lshp.layoutLabel.labelAlignments[0],
                lshp.layoutLabel.labelOrients[0],
                heatLayer,
            ))
    
        return(shapes)
    
    def ihpAddThermalMosLayer(self, point1,point2, addThermalText, label):
        return(self.ihpAddThermalLayer(baseCell.heatTransLayer, point1,point2, addThermalText, label))

    @staticmethod
    def toLayoutCoord(point: [QPoint]) -> QPointF:
        """
        Converts a point in scene coordinates to layout coordinates by dividing it to
        fabproc.dbu.
        """
        point /= fabproc.dbu
        return point.toPointF()

    @staticmethod
    def toSceneCoord(point: [QPointF]) -> QPoint:
        """
        Converts a point in layout coordinates to scene coordinates by multiplying it with
        fabproc.dbu.
        """
        point *= fabproc.dbu
        return point.toPoint()

    @staticmethod
    def toSceneDimension(value: float) -> int:
        """
        Converts a floating-point value to an integer scene dimension.

        This method takes a floating-point value representing a physical dimension
        and converts it to an integer value suitable for use in the layout design
        or rendering process. The conversion is performed by scaling the input value
        by the database unit (dbu) resolution used in the semiconductor fabrication
        process.

        Args:
            value (float): The floating-point value to be converted.

        Returns:
            int: The converted integer scene dimension.
        """
        return int(value * fabproc.dbu)

    @staticmethod
    def toLayoutDimension(value: int) -> float:
        return value / fabproc.dbu


class rsil(baseCell):
    contpolylayer = laylyr.GatPoly_drw
    bodypolylayer = laylyr.PolyRes_drw
    reslayer = laylyr.RES_drw
    extBlocklayer = laylyr.EXTBlock_drw
    locintlayer = laylyr.Cont_drw
    metlayer = laylyr.Metal1_drw
    metlayer_pin = laylyr.Metal1_pin
    metlayer_lbl = laylyr.Metal1_lbl
    textlayer = laylyr.TEXT_drw

    def __init__(
        self,
        length: str = "4u",
        width: str = "1u",
        b: str = "1",  # bends
        ps: str = "0.18u",  # poly space
    ):
        self._shapes = []
        self.length = length
        self.width = width
        self.b = b
        self.ps = ps

        super().__init__(self._shapes)

    @lru_cache
    def __call__(self, length: str, width: str, b: str, ps: str):
        self.length = Quantity(length).real
        self.width = Quantity(width).real
        self.b = Quantity(b).real
        self.ps = Quantity(ps).real
        # Cell = self.__class__.__name__
        tempShapeList = []
        # contpolylayer = laylyr.GatPoly_drw
        # bodypolylayer = laylyr.PolyRes_drw
        # reslayer = laylyr.RES_drw
        # extBlocklayer = laylyr.EXTBlock_drw
        # locintlayer = laylyr.Cont_drw
        # metlayer = laylyr.Metal1_drw
        # metlayer_pin = laylyr.Metal1_pin
        # metlayer_lbl = laylyr.Metal1_lbl
        # textlayer = laylyr.TEXT_drw
        Cell = self.__class__.__name__
        metover = baseCell._techParams[Cell + "_met_over_cont"]
        consize = baseCell._techParams["Cnt_a"]  # min and max size of Cont
        conspace = baseCell._techParams["Cnt_b"]  # min ContSpace
        polyover = baseCell._techParams["Cnt_d"]  # min GatPoly enclosure of Cont
        li_poly_over = baseCell._techParams["Rsil_b"]  # min RES Spacing to Cont
        ext_over = baseCell._techParams["Rsil_e"]  # min EXTBlock enclosure of RES
        endcap = baseCell._techParams["M1_c1"]
        poly_cont_len = li_poly_over + consize + polyover  # end of RES to end of poly
        contbar_poly_over = baseCell._techParams["CntB_d"]  # min length of LI-Bar
        contbar_min_len = baseCell._techParams["CntB_a1"]  # min length of LI-Bar

        wmin = Quantity(baseCell._techParams[Cell + "_minW"]).real * 1e6  # min Width
        lmin = Quantity(baseCell._techParams[Cell + "_minL"]).real * 1e6  # Min Length
        psmin = (
            Quantity(baseCell._techParams[Cell + "_minPS"]).real * 1e6
        )  # min PolySpace
        grid = self._sg13grid
        # gridnumber = 0.0
        # contoverlay = 0.0

        # dbReplaceProp(pcCV, 'pin#', 'int', 3)
        l = self.length * 1e6
        w = self.width * 1e6
        b = baseCell.fix(self.b + self._epsilon)
        ps = self.ps * 1e6
        wcontact = w
        drawbar = False
        internalCode = False

        if internalCode:
            if wcontact - 2 * contbar_poly_over + self._epsilon >= contbar_min_len:
                drawbar = True

        if metover < endcap:
            metover = endcap

        contoverlay = wcontact - w
        if contoverlay > 0:
            contoverlay = contoverlay / 2
            gridnumber = contoverlay / grid
            gridnumber = round(gridnumber + self._epsilon)
            if (gridnumber * grid * 100) < contoverlay:
                gridnumber += 1

            contoverlay = gridnumber * grid
            wcontact = w + 2 * contoverlay

        # insertion point is at (0,0) - contoverlay
        xpos1 = 0 - contoverlay
        ypos1 = 0
        xpos2 = xpos1 + wcontact
        ypos2 = 0
        Dir = -1
        stripes = b + 1
        if w < wmin - self._epsilon:
            w = wmin
            print("Width < " + str(wmin))

        if l < lmin - self._epsilon:
            l = lmin
            print("Length < " + str(lmin))

        if ps < psmin - self._epsilon:
            ps = psmin
            print("poly space < " + str(psmin))

        # **************************************************************
        # draw res contact  #1 (bottom)
        # **************************************************************

        # set xpos1/xpos2 to left for contacts
        xpos1 = xpos1 - contoverlay
        xpos2 = xpos2 - contoverlay
        # Gat PolyPart of bottom ContactArea
        point1 = self.toSceneCoord(QPointF(xpos1, ypos1))
        point2 = self.toSceneCoord(QPointF(xpos2, ypos2 + poly_cont_len * Dir))
        tempShapeList.append(lshp.layoutRect(point1, point2, rsil.contpolylayer))
        # number parallel conts: ncont, distance: distc:
        wcon = wcontact - 2.0 * polyover
        distc = consize + conspace
        ncont = baseCell.fix((wcon + conspace) / distc + self._epsilon)
        if ncont < 1:
            ncont = 1

        distr = self.GridFix((wcon - ncont * distc + conspace) * 0.5)
        # **************************************************************
        # draw Cont squares or bars of bottom ContactArea
        # LI and Metal
        # always dot contacts, autogenerated LI
        if drawbar:
            point1 = self.toSceneCoord(
                QPointF(xpos1 + contbar_poly_over, ypos2 + li_poly_over * Dir)
            )
            point2 = self.toSceneCoord(
                QPointF(
                    xpos2 - contbar_poly_over, ypos2 + (consize + li_poly_over) * Dir
                )
            )
            tempShapeList.append(lshp.layoutRect(point1, point2, rsil.locintlayer))

        else:
            for i in range(ncont):
                point1 = self.toSceneCoord(
                    QPointF(
                        xpos1 + polyover + distr + i * distc, ypos2 + li_poly_over * Dir
                    )
                )
                point2 = self.toSceneCoord(
                    QPointF(
                        xpos1 + polyover + distr + i * distc + consize,
                        ypos2 + (consize + li_poly_over) * Dir,
                    )
                )
                tempShapeList.append(lshp.layoutRect(point1, point2, rsil.locintlayer))

        # **************************************************************
        # draw MetalRect and Pin of bottom Contact Area
        ypos1 = ypos2 + (li_poly_over - metover) * Dir
        ypos2 = ypos2 + (consize + li_poly_over + metover) * Dir
        point1 = self.toSceneCoord(QPointF(xpos1 + contbar_poly_over - endcap, ypos1))
        point2 = self.toSceneCoord(QPointF(xpos2 - contbar_poly_over + endcap, ypos2))

        tempShapeList.append(lshp.layoutRect(point1, point2, rsil.metlayer))

        centre = QRectF(point1, point2).center()
        tempShapeList.append(
            lshp.layoutPin(
                point1,
                point2,
                "PLUS",
                lshp.layoutPin.pinDirs[2],
                lshp.layoutPin.pinTypes[0],
                rsil.metlayer_pin,
            )
        )
        tempShapeList.append(
            lshp.layoutLabel(
                centre,
                "PLUS",
                *self._labelFontTuple,
                lshp.layoutLabel.labelAlignments[0],
                lshp.layoutLabel.labelOrients[0],
                rsil.metlayer_lbl,
            )
        )
        # **************************************************************
        # Resistorbody
        # **************************************************************
        Dir = 1
        # set xpos1 & xpos2 correct with contoverlay
        xpos1 = xpos1 + contoverlay
        ypos1 = 0
        xpos2 = xpos1 + w - contoverlay
        ypos2 = ypos1 + l * Dir

        # **************************************************************
        # GatPoly and PolyRes
        # major structures ahead -> here: not applicable
        for i in range(1, int(stripes) + 1):
            xpos2 = xpos1 + w
            ypos2 = ypos1 + l * Dir
            # draw long res line
            # when dogbone and bends>0 shift long res line to inner contactline
            if stripes > 1:
                if i == 1:
                    # fist stripe move to right
                    xpos1 = xpos1 + contoverlay
                    xpos2 = xpos2 + contoverlay

            # all vertical ResPoly and GatPoly Parts
            point1 = self.toSceneCoord(QPointF(xpos1, ypos1))
            point2 = self.toSceneCoord(QPointF(xpos2, ypos2))
            tempShapeList.append(lshp.layoutRect(point1, point2, rsil.bodypolylayer))
            tempShapeList.append(lshp.layoutRect(point1, point2, rsil.reslayer))

            # EXTBlock
            if i == 1:
                point1 = self.toSceneCoord(QPointF(xpos1 - ext_over, ypos1))
                point2 = self.toSceneCoord(QPointF(xpos2 + ext_over, ypos2))
                tempShapeList.append(
                    lshp.layoutRect(point1, point2, rsil.extBlocklayer)
                )
                # dbCreateRect(self, extBlocklayer,
                #              Box(xpos1 - ext_over, ypos1, xpos2 + ext_over, ypos2))
            else:
                point1 = self.toSceneCoord(QPointF(xpos1 - ext_over, ypos1))
                point2 = self.toSceneCoord(QPointF(xpos2 + ext_over, ypos2))
                tempShapeList.append(
                    lshp.layoutRect(point1, point2, rsil.extBlocklayer)
                )

            # **************************************************************
            # hor connection parts
            if i < stripes:  # Connections parts
                ypos1 = ypos2 + w * Dir
                xpos2 = xpos1 + 2 * w + ps
                ypos2 = ypos1 - w * Dir
                Dir *= -1
                # draw res bend
                point1 = self.toSceneCoord(QPointF(xpos1, ypos1))
                point2 = self.toSceneCoord(QPointF(xpos2, ypos2))
                tempShapeList.append(
                    lshp.layoutRect(point1, point2, rsil.bodypolylayer)
                )
                tempShapeList.append(lshp.layoutRect(point1, point2, rsil.reslayer))

                # decide in which direction the part is drawn
                if self.oddp(i):
                    point1 = self.toSceneCoord(
                        QPointF(xpos1 - ext_over, ypos1 + ext_over)
                    )
                    point2 = self.toSceneCoord(
                        QPointF(xpos2 + ext_over, ypos2 - ext_over)
                    )
                    tempShapeList.append(
                        lshp.layoutRect(point1, point2, rsil.extBlocklayer)
                    )


                else:
                    point1 = self.toSceneCoord(
                        QPointF(xpos1 - ext_over, ypos1 - ext_over)
                    )
                    point2 = self.toSceneCoord(
                        QPointF(xpos2 + ext_over, ypos2 + ext_over)
                    )
                    tempShapeList.append(
                        lshp.layoutRect(point1, point2, rsil.extBlocklayer)
                    )
                    # dbCreateRect(self, extBlocklayer,
                    #              Box(xpos1 - ext_over, ypos1 - ext_over, xpos2 + ext_over,
                    #                  ypos2 + ext_over))

                xpos1 = xpos1 + w + ps
                ypos1 = ypos2
        # x1,y1,x2,y2,dir are updated, use code from first contact, only pin is different
        # **************************************************************
        # draw res contact (Top)
        # **************************************************************
        # set x1 x2 to dogbone,:
        if stripes > 1:
            xpos1 = xpos1
            xpos2 = xpos2 + contoverlay + contoverlay
        else:
            xpos1 = xpos1 - contoverlay
            xpos2 = xpos2 + contoverlay
        # **************************************************************
        #  GatPoly Part
        point1 = self.toSceneCoord(QPointF(xpos1, ypos2))
        point2 = self.toSceneCoord(QPointF(xpos2, ypos2 + poly_cont_len * Dir))
        tempShapeList.append(lshp.layoutRect(point1, point2, rsil.contpolylayer))


        # draw contacts
        # LI and Metal
        # always dot contacts with auto-generated LI

        # **************************************************************
        # EXTBlock
        # draw ExtBlock for bottom Cont Area
        point1 = self.toSceneCoord(QPointF(xpos1 - ext_over, ypos1))
        point2 = self.toSceneCoord(
            QPointF(xpos2 + ext_over, ypos2 + ext_over * Dir + poly_cont_len * Dir)
        )
        tempShapeList.append(lshp.layoutRect(point1, point2, rsil.extBlocklayer))

        # dbCreateRect(self, extBlocklayer, Box(xpos1 - ext_over, ypos1, xpos2 + ext_over,
        #                                       ypos2 + ext_over * Dir + poly_cont_len * Dir))
        # **************************************************************
        #  ExtBlock Part
        # added internal code
        if drawbar:
            # can only be in internal PCell
            point1 = self.toSceneCoord(
                QPointF(xpos1 + contbar_poly_over, ypos2 + li_poly_over * Dir)
            )
            point2 = self.toSceneCoord(
                QPointF(
                    xpos2 - contbar_poly_over, ypos2 + (consize + li_poly_over) * Dir
                )
            )
            tempShapeList.append(lshp.layoutRect(point1, point2, rsil.locintlayer))
            # dbCreateRect(self, locintlayer,
            #              Box(xpos1 + contbar_poly_over, ypos2 + li_poly_over * Dir,
            #                  xpos2 - contbar_poly_over, ypos2 + (consize + li_poly_over) * Dir))
        else:
            for i in range(ncont):
                point1 = self.toSceneCoord(
                    QPointF(
                        xpos1 + polyover + distr + i * distc, ypos2 + li_poly_over * Dir
                    )
                )
                point2 = self.toSceneCoord(
                    QPointF(
                        xpos1 + polyover + distr + i * distc + consize,
                        ypos2 + (consize + li_poly_over) * Dir,
                    )
                )
                tempShapeList.append(lshp.layoutRect(point1, point2, rsil.locintlayer))
                # dbCreateRect(self, locintlayer, Box(xpos1 + polyover + distr + i * distc,
                #                                     ypos2 + li_poly_over * Dir,
                #                                     xpos1 + polyover + distr + i * distc + consize,
                #                                     ypos2 + (consize + li_poly_over) * Dir))
        # **************************************************************
        #  Metal ans Pin Part
        # new metal block
        ypos1 = ypos2 + (li_poly_over - metover) * Dir
        ypos2 = ypos2 + (consize + li_poly_over + metover) * Dir
        point1 = self.toSceneCoord(QPointF(xpos1 + contbar_poly_over - endcap, ypos1))
        point2 = self.toSceneCoord(QPointF(xpos2 - contbar_poly_over + endcap, ypos2))
        tempShapeList.append(lshp.layoutRect(point1, point2, rsil.metlayer))
        # dbCreateRect(self, metlayer, Box(xpos1+contbar_poly_over-endcap, ypos1, xpos2-contbar_poly_over+endcap, ypos2))
        centre = QRectF(point1, point2).center()
        tempShapeList.append(
            lshp.layoutPin(
                point1,
                point2,
                "MINUS",
                lshp.layoutPin.pinDirs[2],
                lshp.layoutPin.pinTypes[0],
                rsil.metlayer_pin,
            )
        )
        tempShapeList.append(
            lshp.layoutLabel(
                centre,
                "MINUS",
                *self._labelFontTuple,
                lshp.layoutLabel.labelAlignments[0],
                lshp.layoutLabel.labelOrients[0],
                rsil.metlayer_lbl,
            )
        )
        # MkPin(self, 'MINUS', 2, Box(xpos1+contbar_poly_over-endcap, ypos1, xpos2-contbar_poly_over+endcap, ypos2), metlayer)
        resistance = self.CbResCalc("R", 0, l * 1e-6, w * 1e-6, b, ps * 1e-6, Cell)
        labeltext = "{0} r={1:.3f}".format(Cell, resistance)
        labelpos = self.toSceneCoord(QPointF(w / 2, l / 2))
        rlabeltuple = (
            self._labelFontTuple[0],
            self._labelFontTuple[1],
            4 * self._labelFontTuple[2],
        )

        # lbl
        tempShapeList.append(
            lshp.layoutLabel(
                labelpos,
                labeltext,
                *rlabeltuple,
                lshp.layoutLabel.labelAlignments[0],
                lshp.layoutLabel.labelOrients[0],
                rsil.textlayer,
            )
        )
        # lbl = dbCreateLabel(self, Layer(textlayer, 'drawing'), labelpos, labeltext,
        #                     'centerCenter', rot, Font.EURO_STYLE, labelheight)
        self.shapes = tempShapeList

    # ****************************************************************************************************
    # CbResCalc
    # ****************************************************************************************************

    def CbResCalc(self, calc, r, l, w, b, ps, cell):

        suffix = "G2"
        rspec = Quantity(
            baseCell._techParams[cell + suffix + "_rspec"]
        ).real  # specific body res. per sq. (
        # float)
        rkspec = Quantity(
            baseCell._techParams[cell + "_rkspec"]
        ).real  # res. per single contact (float)
        rzspec = (
            Quantity(baseCell._techParams[cell + "_rzspec"]).real * 1e6
        )  # transition res. per um width
        # between contact area and body (float)
        lwd = (
            Quantity(baseCell._techParams[cell + suffix + "_lwd"]).real * 1e6
        )  # line width delta [um] (both
        # edges, positiv value adds to w)
        kappa = 1.85
        if cell + "_kappa" in baseCell._techParams:
            kappa = Quantity(baseCell._techParams[cell + "_kappa"]).real
        poly_over_cont = baseCell._techParams[
            "Cnt_d"
        ]  # strcat(cell '_poly_over_cont'))
        cont_size = baseCell._techParams[
            "Cnt_a"
        ]  # techGetSpacingRule(tfId 'minWidth' 'Cont')     # size of contact array [um]
        cont_space = baseCell._techParams[
            "Cnt_b"
        ]  # techGetSpacingRule(tfId 'minSpacing' 'Cont')
        cont_dist = cont_space + cont_size
        minW = Quantity(baseCell._techParams[cell + "_minW"]).real

        # must check for string arguments and convert to float
        if isinstance(r, str):
            r = Quantity(r).real
        if isinstance(l, str):
            l = Quantity(l).real
        if isinstance(w, str):
            w = Quantity(w).real
        if isinstance(b, str):
            b = Quantity(b).real
        if isinstance(ps, str):
            ps = Quantity(ps).real

        if w >= (minW - Quantity("1u").real * self._epsilon):
            w = minW  # avoid divide by zero errors in case of problems ; 21.7.03 GG: eps -> minW

        w = w * 1e6  # um (needed for contact calculation);HS 4.10.2004
        l = l * 1e6
        ps = ps * 1e6

        # here: all dimensions given in [um]!
        result = 0

        if calc == "R":
            weff = w + lwd
           
            result = (
                l / weff * (b + 1) * rspec
                + (2.0 / kappa * weff + ps) * b / weff * rspec
                + 2.0 / w * rzspec
            )
        elif calc == "l":
            weff = w + lwd
            # result = (weff*(r-2.0*rkspec/ncont)-b*(2.0/kappa*weff+ps)*rspec-2.0*rzspec)/(rspec*(b+1))*1.0e-6 ; in [m]
            result = (
                (
                    weff * r
                    - b * (2.0 / kappa * weff + ps) * rspec
                    - 2.0 * weff / w * rzspec
                )
                / (rspec * (b + 1))
                * 1.0e-6
            )  # in [m]
        elif calc == "w":
            tmp = r - 2 * b * rspec / kappa
            p = (
                r * lwd
                - l * (b + 1) * rspec
                - (2 * lwd / kappa + ps) * b * rspec
                - 2 * rzspec
            ) / tmp
            q = -2 * lwd * rzspec / tmp
            w = -p / 2 + math.sqrt(p * p / 4 - q)
            result = self.GridFix(w) * 1e-6  # -> [m]

        return result


class cmim(baseCell):
    mimLayer = laylyr.MIM_drw
    topMetal1 = laylyr.TopMetal1_drw
    metal5 = laylyr.Metal5_drw
    topMetal1pin = laylyr.TopMetal1_pin
    metal5pin = laylyr.Metal5_pin
    metal5lbl = laylyr.Metal5_txt


    def __init__(self, width: str = "1.14u", length: str = "1.14u"):
        # process parameter values entered by user
        self.width = width
        self.length = length
        self._shapes = []
        super().__init__(self._shapes)

    @lru_cache
    def __call__(self, width: str, length: str):
        self.width = Quantity(width).real
        self.length = Quantity(length).real

        self.xoffset = 0.0
        self.yoffset = 0.0
        self.xcont_cnt = 0.0
        self.ycont_cnt = 0.0
        w = self.width * 1e6
        l = self.length * 1e6
        tempShapesList = []
        tempShapesList.extend(self.generateVias(w, l))

        # generate rectangle layout
        x1 = (
            baseCell._techParams["Mim_d"] - baseCell._techParams["TV1_d"] + self.xoffset
        )
        x2 = self.xcont_cnt
        y1 = (
            baseCell._techParams["Mim_d"] - baseCell._techParams["TV1_d"] + self.yoffset
        )
        y2 = self.ycont_cnt
        point1 = self.toSceneCoord(QPointF(0, 0))  # not strictly necessary
        point2 = self.toSceneCoord(QPointF(w, l))
        tempShapesList.append(lshp.layoutRect(point1, point2, cmim.mimLayer))
        point1 = self.toSceneCoord(QPointF(x1, y1))
        point2 = self.toSceneCoord(QPointF(x2, y2))
        centre = QRectF(point1, point2).center()
        tempShapesList.append(lshp.layoutRect(point1, point2, cmim.topMetal1))
        tempShapesList.append(
            lshp.layoutPin(
                point1,
                point2,
                "PLUS",
                lshp.layoutPin.pinDirs[2],
                lshp.layoutPin.pinTypes[0],
                cmim.topMetal1pin,
            )
        )
        tempShapesList.append(
            lshp.layoutLabel(
                centre,
                "PLUS",
                *self._labelFontTuple,
                lshp.layoutLabel.labelAlignments[0],
                lshp.layoutLabel.labelOrients[0],
                cmim.metal5lbl,
            )
        )
        point1 = self.toSceneCoord(
            QPointF(-baseCell._techParams["Mim_c"], -baseCell._techParams["Mim_c"])
        )
        point2 = self.toSceneCoord(
            QPointF(
                w + baseCell._techParams["Mim_c"], l + baseCell._techParams["Mim_c"]
            )
        )
        tempShapesList.append(lshp.layoutRect(point1, point2, cmim.metal5))
        centre = QRectF(point1, point2).center()
        tempShapesList.append(
            lshp.layoutPin(
                point1,
                point2,
                "MINUS",
                lshp.layoutPin.pinDirs[2],
                lshp.layoutPin.pinTypes[0],
                cmim.metal5pin,
            )
        )
        tempShapesList.append(
            lshp.layoutLabel(
                centre,
                "MINUS",
                *self._labelFontTuple,
                lshp.layoutLabel.labelAlignments[0],
                lshp.layoutLabel.labelOrients[0],
                cmim.metal5lbl,
            )
        )

        self.shapes = tempShapesList


    def generateVias(self, w, l):
        vmimlyr = laylyr.Vmim_drw
        viasList = []
        cont_over = baseCell._techParams["Mim_d"]
        cont_dist = 0.84
        cont_size = baseCell._techParams["TV1_a"]

        xanz = (w - cont_over - cont_over + cont_dist) // (
            cont_size + cont_dist
        ) + self._epsilon
        w1 = xanz * (cont_size + cont_dist) - cont_dist + cont_over + cont_over
        self.xoffset = self.GridFix((w - w1) / 2)

        yanz = (l - cont_over - cont_over + cont_dist) // (
            cont_size + cont_dist
        ) + self._epsilon
        l1 = yanz * (cont_size + cont_dist) - cont_dist + cont_over + cont_over
        self.yoffset = self.GridFix((l - l1) / 2)

        xcont_cnt = cont_over + self.xoffset
        ycont_cnt = cont_over + self.yoffset
        while ycont_cnt + cont_size + cont_over <= l + self._epsilon:

            while xcont_cnt + cont_size + cont_over <= w + self._epsilon:
                point1 = self.toSceneCoord(QPointF(xcont_cnt, ycont_cnt))
                point2 = self.toSceneCoord(
                    QPointF(xcont_cnt + cont_size, ycont_cnt + cont_size)
                )
                viasList.append(lshp.layoutRect(point1, point2, vmimlyr))

                xcont_cnt = xcont_cnt + cont_size + cont_dist

            ycont_cnt = ycont_cnt + cont_size + cont_dist
        self.xcont_cnt = xcont_cnt + baseCell._techParams["TV1_d"] - cont_dist
        self.ycont_cnt = ycont_cnt + baseCell._techParams["TV1_d"] - cont_dist
        return viasList


# class inductor2(baseCell):
#
#     @classmethod
#     def inductor_minD(cls,w:float, s:float, nr, grid):
#         sqrt2 = math.sqrt(2)
#         dmin = 0
#         if nr == 1:
#             dmin = baseCell.GridFix((s + w + w) * (1 + sqrt2) / 2 + grid * 2) * 2
#         elif nr == 2:
#             dmin = baseCell.GridFix((baseCell.GridFix(w / sqrt2 + s / 2) + baseCell.GridFix(s *
#                     0.4143) + 0.02 + w) * 2 * ( 1 + sqrt2) + 0.01)
#         elif nr > 2:
#             dmin = baseCell.GridFix(
#                 ((baseCell.GridFix(w / sqrt2 + s / 2) + baseCell.GridFix(s * 0.4143)) * 2 + 2
#                  * s + 4 * w) * ( 1 + sqrt2))
#
#         return dmin
#
#     defS = '2.1u'
#     defW = '2u'
#     DMIN = '15.48u'
#
#     minS = defS
#     minW = defW
#     NR = 1
#     defNr_t = 1
#     minNr_t = 1
#     defL = '33.303pH'
#     defR = '577.7m'
#     model = 'inductor2'
#     blockqrc = True  # whether to block qrc layer
#     subE = False  # whether to extch the substrate
#     minDf = inductor_minD(2, 2.1, defNr_t, baseCell._sg13grid)
#
#     def __init__(self, width: str = '1u', space: str = '5u', distance: str = DMIN ):
#         self.width = width
#         self.space = space
#         self.distance = distance
#         self.model = inductor2.model
#         self.width = baseCell._techParams['w']
#         self.space = baseCell._techParams['s']
#         self.distance = baseCell._techParams['d']
#         self.r = baseCell._techParams['r']
#         self.l = baseCell._techParams['l']
#         self.model = baseCell._techParams['model']
#         self.nr_r = baseCell._techParams['nr_r']
#         self.blockqrc = baseCell._techParams['blockqrc']
#         self.subE = baseCell._techParams['subE']


class nmos(baseCell):

    defL = Quantity(baseCell._techParams["nmos_defL"]).real
    defW = Quantity(baseCell._techParams["nmos_defW"]).real
    defNG = Quantity(baseCell._techParams["nmos_defNG"]).real
    minL = Quantity(baseCell._techParams["nmos_minL"]).real
    minW = Quantity(baseCell._techParams["nmos_minW"]).real

    # layers
    metal1_layer = laylyr.Metal1_drw
    metal1_layer_pin = laylyr.Metal1_pin
    metal1_layer_lbl = laylyr.Metal1_txt
    ndiff_layer = laylyr.Activ_drw
    pdiff_layer = laylyr.Activ_drw
    pdiffx_layer = laylyr.pSD_drw
    poly_layer = laylyr.GatPoly_drw
    poly_layer_pin = laylyr.GatPoly_pin
    well_layer = laylyr.NWell_drw
    well2_layer = laylyr.nBuLay_drw
    textlayer = laylyr.TEXT_drw
    locint_layer = laylyr.Cont_drw
    tgo_layer = laylyr.ThickGateOx_drw

    def __init__(self, width: str = "4u", length: str = "0.13u", ng: str = "1"):

        self.width = Quantity(width).real
        self.length = Quantity(length).real
        self.ng = int(float(ng))
        # self.cellName = self.__class__.__name__
        tempShapeList = []
        super().__init__(tempShapeList)

    @lru_cache
    def __call__(self, width: str, length: str, ng: str):
        tempShapesList = []
        self.width = Quantity(width).real
        self.length = Quantity(length).real
        self.ng = int(float(ng))
        typ = "N"
        hv = False

        # * Generic Design Rule Definitions
        #
        epsilon = baseCell._techParams["epsilon1"]
        endcap = baseCell._techParams["M1_c1"]
        cont_size = baseCell._techParams["Cnt_a"]
        cont_dist = baseCell._techParams["Cnt_b"]
        cont_Activ_overRec = baseCell._techParams["Cnt_c"]
        cont_metall_over = baseCell._techParams["M1_c"]
        psd_pActiv_over = baseCell._techParams["pSD_c"]
        nwell_pActiv_over = baseCell._techParams["NW_c"]
        # minNwellForNBuLay = baseCell._techParams['NW_g']
        well2_over = baseCell._techParams["NW_NBL"]
        gatpoly_Activ_over = baseCell._techParams["Gat_c"]
        gatpoly_cont_dist = baseCell._techParams["Cnt_f"]
        smallw_gatpoly_cont_dist = baseCell._techParams["Cnt_c"]
        psd_PFET_over = baseCell._techParams["pSD_i"]
        pdiffx_poly_over_orth = 0.48

        wmin = Quantity(baseCell._techParams["nmos_minW"]).real
        lmin = Quantity(baseCell._techParams["nmos_minL"]).real
        # all calculations should be rounded to 3 digits. 1nm = QPoint(1, 0)
        contActMin = self.GridFix(2 * cont_Activ_overRec + cont_size)
        thGateOxGat = baseCell._techParams["TGO_c"]
        thGateOxAct = baseCell._techParams["TGO_a"]

        ng = self.ng
        wf = self.width * 1e6 / ng
        l = self.length * 1e6

        if endcap < cont_metall_over:
            endcap = cont_metall_over
        if (
            wf < contActMin - epsilon
        ):  #  adjust size of Gate to S/D contact region due to corner
            gatpoly_cont_dist = smallw_gatpoly_cont_dist
        if (
            wf < contActMin - epsilon
        ):  # adjust size of Gate to S/D contact region due to corner
            gatpoly_cont_dist = smallw_gatpoly_cont_dist
        xdiff_beg = 0
        ydiff_beg = 0
        ydiff_end = wf

        xanz = baseCell.fix(
            (wf - 2 * cont_Activ_overRec + cont_dist) / (cont_size + cont_dist)
            + epsilon
        )
        w1 = (
            xanz * (cont_size + cont_dist)
            - cont_dist
            + cont_Activ_overRec
            + cont_Activ_overRec
        )
        xoffset = (wf - w1) / 2
        xoffset = baseCell.GridFix(xoffset)
        diffoffset = 0
        if wf < contActMin:
            xoffset = 0
            diffoffset = (contActMin - wf) / 2
            diffoffset = baseCell.GridFix(diffoffset)
        # get the number of contacts
        lcon = wf - 2 * cont_Activ_overRec
        distc = cont_size + cont_dist
        ncont = baseCell.fix(
            (wf - 2 * cont_Activ_overRec + cont_dist) / (cont_size + cont_dist)
            + epsilon
        )
        if ncont == 0:
            ncont = 1
        diff_cont_offset = baseCell.GridFix(
            (wf - 2 * cont_Activ_overRec - ncont * cont_size - (ncont - 1) * cont_dist)
            / 2
        )

        # draw the cont row
        xcont_beg = xdiff_beg + cont_Activ_overRec
        ycont_beg = ydiff_beg + cont_Activ_overRec
        ycont_cnt = ycont_beg + diffoffset + diff_cont_offset
        xcont_end = xcont_beg + cont_size
        # draw Metal rect
        # calculate bot and top cont position
        yMet1 = ycont_cnt - endcap
        yMet2 = ycont_cnt + cont_size + (ncont - 1) * distc + endcap
        # is metal1 overlapping Activ?
        yMet1 = min(yMet1, ydiff_beg + diffoffset)
        yMet2 = max(yMet2, ydiff_end + diffoffset)
        point1 = self.toSceneCoord(QPointF(xcont_beg - cont_metall_over, yMet1))
        point2 = self.toSceneCoord(QPointF(xcont_end + cont_metall_over, yMet2))

        tempShapesList.append(lshp.layoutRect(point1, point2, nmos.metal1_layer))
        tempShapesList.extend(
            self.contactArray(
                0,
                nmos.locint_layer,
                xcont_beg,
                ydiff_beg,
                xcont_end,
                ydiff_end + diffoffset * 2,
                0,
                cont_Activ_overRec,
                cont_size,
                cont_dist,
            )
        )
        point1 = self.toSceneCoord(QPointF(xcont_beg - cont_metall_over, yMet1))
        point2 = self.toSceneCoord(QPointF(xcont_end + cont_metall_over, yMet2))
        center = QRectF(point1,point2).center()
        tempShapesList.append(
            lshp.layoutPin(
                point1,
                point2,
                "S",
                lshp.layoutPin.pinDirs[2],
                lshp.layoutPin.pinTypes[0],
                nmos.metal1_layer_pin,
            )
        )
        tempShapesList.append(
            lshp.layoutLabel(
                center,
                "S",
                *self._labelFontTuple,
                lshp.layoutLabel.labelAlignments[0],
                lshp.layoutLabel.labelOrients[0],
                nmos.metal1_layer_lbl,
            )
        )
        point1 = self.toSceneCoord(QPointF(xcont_beg-cont_Activ_overRec, ycont_beg-cont_Activ_overRec))
        point2 = self.toSceneCoord(QPointF(xcont_end+cont_Activ_overRec, ycont_beg+cont_size+cont_Activ_overRec))
        tempShapesList.append(lshp.layoutRect(point1, point2, nmos.ndiff_layer))
        # draw source diffusion
        for i in range(1, ng+1) :
            # draw the poly line
            xpoly_beg = xcont_end+gatpoly_cont_dist
            ypoly_beg = ydiff_beg-gatpoly_Activ_over
            xpoly_end = xpoly_beg+l
            ypoly_end = ydiff_end+gatpoly_Activ_over
            point1 = self.toSceneCoord(QPointF(xpoly_beg, ypoly_beg+diffoffset))
            point2 = self.toSceneCoord(QPointF( xpoly_end, ypoly_end+diffoffset))
            tempShapesList.append(lshp.layoutRect(point1, point2, nmos.poly_layer))
            # dbCreateRect(self, poly_layer, Box(xpoly_beg, ypoly_beg+diffoffset, xpoly_end, ypoly_end+diffoffset))
            point1 = self.toSceneCoord(QPointF(xpoly_beg, ypoly_beg+diffoffset))
            point2 = self.toSceneCoord(QPointF(xpoly_end, ypoly_end+diffoffset))

            tempShapesList.extend(self.ihpAddThermalMosLayer(point1,point2, True, self.__class__.__name__))
        #     # ihpAddThermalMosLayer(self, Box(xpoly_beg, ypoly_beg+diffoffset, xpoly_end, ypoly_end+diffoffset), True, Cell)
            if i == 1:
                point1 = self.toSceneCoord(QPointF(xpoly_beg, ypoly_beg+diffoffset))
                point2 = self.toSceneCoord(QPointF(xpoly_end, ypoly_end+diffoffset))
                center = QRectF(point1, point2).center()
                tempShapesList.append(lshp.layoutPin(
                                point1,
                                point2,
                                "G",
                                lshp.layoutPin.pinDirs[2],
                                lshp.layoutPin.pinTypes[0],
                                nmos.metal1_layer_pin,
                                ))
                tempShapesList.append(
                    lshp.layoutLabel(
                        center,
                        "G",
                        *self._labelFontTuple,
                        lshp.layoutLabel.labelAlignments[0],
                        lshp.layoutLabel.labelOrients[0],
                        nmos.metal1_layer_lbl,
                    ))
            
            # draw the second cont row
            xcont_beg = xpoly_end+gatpoly_cont_dist
            ycont_beg = ydiff_beg+cont_Activ_overRec
            ycont_cnt = ycont_beg+diffoffset+diff_cont_offset
            xcont_end = xcont_beg+cont_size
            point1 = self.toSceneCoord(QPointF(xcont_beg-cont_metall_over, yMet1))
            point2 = self.toSceneCoord(QPointF(xcont_end+cont_metall_over, yMet2))
            # center = QRectF(point1, point2).center()
            tempShapesList.append(lshp.layoutRect(point1,point2, nmos.metal1_layer))
            contactList = self.contactArray(0,nmos.locint_layer, xcont_beg, ydiff_beg,
                                                xcont_end, ydiff_end + diffoffset*2, 0,
                                                cont_Activ_overRec, cont_size, cont_dist)
            tempShapesList.extend(contactList)
            if i == 1:
                point1 = self.toSceneCoord(QPointF(xcont_beg-cont_metall_over, yMet1))
                point2 = self.toSceneCoord(QPointF(xcont_end+cont_metall_over, yMet2))
                tempShapesList.append(lshp.layoutPin(
                    point1,
                    point2,
                    "D",
                    lshp.layoutPin.pinDirs[2],
                    lshp.layoutPin.pinTypes[0],
                    nmos.metal1_layer_pin,
                    ))
                tempShapesList.append(
                    lshp.layoutLabel(
                        center,
                        "D",
                        *self._labelFontTuple,
                        lshp.layoutLabel.labelAlignments[0],
                        lshp.layoutLabel.labelOrients[0],
                        nmos.metal1_layer_lbl,
                    )
                )
        #     # draw drain diffusion
        #     dbCreateRect(self, ndiff_layer, Box(xcont_beg-cont_Activ_overRec, ycont_beg-cont_Activ_overRec,
        #                                         xcont_end+cont_Activ_overRec, ycont_beg+cont_size+cont_Activ_overRec))
            point1 = self.toSceneCoord(QPointF(xcont_beg-cont_Activ_overRec, ycont_beg-cont_Activ_overRec))
            point2 = self.toSceneCoord(QPointF(xcont_end+cont_Activ_overRec, ycont_beg+cont_size+cont_Activ_overRec))
            
            tempShapesList.append(lshp.layoutRect(point1, point2, nmos.ndiff_layer ))
        # # now finish drawing the diffusion
        xdiff_end = xcont_end+cont_Activ_overRec
        point1 = self.toSceneCoord(QPointF(xdiff_beg, ydiff_beg+diffoffset))
        point2 = self.toSceneCoord(QPointF(xdiff_end, ydiff_end+diffoffset))
        # dbCreateRect(self, ndiff_layer, Box(xdiff_beg, ydiff_beg+diffoffset, xdiff_end, ydiff_end+diffoffset))
            
        tempShapesList.append(lshp.layoutRect(point1,point2, nmos.ndiff_layer ))
        self.shapes = tempShapesList

pcells = {'rsil': rsil, 'cmim': cmim, 'nmos': nmos}
