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

from quantiphy import Quantity


class baseInst:
    def __init__(self, labels_dict: dict):
        self._labelsDict = labels_dict


class res(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)

    def doubleR(self):
        Rvalue = self._labelsDict.get("R").labelValue
        if Rvalue.isalnum():
            return str(2 * Quantity(Rvalue))
        return "?"


class rsil(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict["@W"].labelValue)
        self.L = Quantity(self._labelsDict["@L"].labelValue)
        self.b = Quantity(self._labelsDict["@b"].labelValue)
        self.m = Quantity(self._labelsDict["@m"].labelValue)

    def Rparm(self):
        returnValue = (
            9.0e-6 / self.W
            + 7.0
            * ((self.b + 1) * self.L + (1.081 * (self.W + 1.0e-8) + 0.18e-6) * self.b)
            / (self.W + 1.0e-8)
        ) / self.m
        return returnValue


class sg13_hv_nmos(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.L = Quantity(self._labelsDict["@L"].labelValue)
        self.W = Quantity(self._labelsDict["@W"].labelValue)
        self.ng = Quantity(self._labelsDict["@ng"].labelValue)
        self.m = Quantity(self._labelsDict["@m"].labelValue)


class sg13_hv_pmos(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.L = Quantity(self._labelsDict["@L"].labelValue)
        self.W = Quantity(self._labelsDict["@W"].labelValue)
        self.ng = Quantity(self._labelsDict["@ng"].labelValue)
        self.m = Quantity(self._labelsDict["@m"].labelValue)


class cap_cmim(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict["@W"].labelValue)
        self.L = Quantity(self._labelsDict["@L"].labelValue)
        self.MF = Quantity(self._labelsDict["@MF"].labelValue)

    def Cparm(self):
        returnValue = self.MF * (
            self.W * self.L * 1.5e-3 + 2 * (self.W + self.L) * 40e-12
        )
        return returnValue


class cap_cpara(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.C = Quantity(self._labelsDict["@C"].labelValue)


class cap_rfcmim(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict["@W"].labelValue)
        self.L = Quantity(self._labelsDict["@L"].labelValue)
        self.wfeed = Quantity(self._labelsDict["@wfeed"].labelValue)

    def Cparm(self):
        returnValue = self.W * self.L * 1.5e-3 + 2 * (self.W + self.L) * 40e-12
        return returnValue


class dantenna(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.l = Quantity(self._labelsDict["@l"].labelValue)
        self.w = Quantity(self._labelsDict["@w"].labelValue)


class dpantenna(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.l = Quantity(self._labelsDict["@l"].labelValue)
        self.w = Quantity(self._labelsDict["@w"].labelValue)


class npn13G2(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.Nx = Quantity(self._labelsDict["@Nx"].labelValue)


class npn13G2l(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.Nx = Quantity(self._labelsDict["@Nx"].labelValue)
        self.El = Quantity(self._labelsDict["@El"].labelValue)


class npn13G2v(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.Nx = Quantity(self._labelsDict["@Nx"].labelValue)


class ntap1(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.R = Quantity(self._labelsDict["@R"].labelValue)
        self.Imax = Quantity(self._labelsDict["@Imax"].labelValue)

    def Rparm(self):
        returnValue = 262.847
        return returnValue


class pnpMPA(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.w = Quantity(self._labelsDict["@w"].labelValue)
        self.l = Quantity(self._labelsDict["@l"].labelValue)


class ptap1(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.R = Quantity(self._labelsDict["@R"].labelValue)
        self.Imax = Quantity(self._labelsDict["@Imax"].labelValue)

    def Rparm(self):
        returnValue = 262.847
        return returnValue


class rhigh(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict["@W"].labelValue)
        self.L = Quantity(self._labelsDict["@L"].labelValue)
        self.b = Quantity(self._labelsDict["@b"].labelValue)
        self.m = Quantity(self._labelsDict["@m"].labelValue)

    def Rparm(self):
        returnValue = (
            1.6e-4 / self.W
            + 1360.0
            * ((self.b + 1) * self.L + (1.081 * (self.W - 0.04e-6) + 0.18e-6) * self.b)
            / (self.W - 0.04e-6)
        ) / self.m
        return returnValue


class rppd(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.W = Quantity(self._labelsDict["@W"].labelValue)
        self.L = Quantity(self._labelsDict["@L"].labelValue)
        self.b = Quantity(self._labelsDict["@b"].labelValue)
        self.m = Quantity(self._labelsDict["@m"].labelValue)

    def Rparm(self):
        print("i am in rparm")
        return (
            70.0e-6 / self.W
            + 260.0
            * ((self.b + 1) * self.L + (1.081 * (self.W + 6.0e-9) + 0.18e-6) * self.b)
            / (self.W + 6.0e-9)
        ) / self.m


class sg13_lv_nmos(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.L = Quantity(self._labelsDict["@L"].labelValue)
        self.W = Quantity(self._labelsDict["@W"].labelValue)
        self.ng = Quantity(self._labelsDict["@ng"].labelValue)
        self.m = Quantity(self._labelsDict["@m"].labelValue)


class sg13_lv_pmos(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.L = Quantity(self._labelsDict["@L"].labelValue)
        self.W = Quantity(self._labelsDict["@W"].labelValue)
        self.ng = Quantity(self._labelsDict["@ng"].labelValue)
        self.m = Quantity(self._labelsDict["@m"].labelValue)


class sg13_lv_rf_nmos(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.L = Quantity(self._labelsDict["@L"].labelValue)
        self.W = Quantity(self._labelsDict["@W"].labelValue)
        self.ng = Quantity(self._labelsDict["@ng"].labelValue)
        self.m = Quantity(self._labelsDict["@m"].labelValue)
        self.rfmode = Quantity(self._labelsDict["@rfmode"].labelValue)


class sg13_lv_rf_pmos(baseInst):
    def __init__(self, labels_dict: dict):
        super().__init__(labels_dict)
        self.L = Quantity(self._labelsDict["@L"].labelValue)
        self.W = Quantity(self._labelsDict["@W"].labelValue)
        self.ng = Quantity(self._labelsDict["@ng"].labelValue)
        self.m = Quantity(self._labelsDict["@m"].labelValue)
        self.rfmode = Quantity(self._labelsDict["@rfmode"].labelValue)
