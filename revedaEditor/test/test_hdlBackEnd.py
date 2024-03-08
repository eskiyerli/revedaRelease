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
#    Add-ons and extensions developed for this software may be distributed
#    under their own separate licenses.
#
#    Software: Revolution EDA
#    License: Mozilla Public License 2.0
#    Licensor: Revolution Semiconductor (Registered in the Netherlands)
#

import pytest
import revedaEditor.backend.hdlBackEnd as hdl
import pathlib


@pytest.fixture
def spiceFile1():
    modulePath = pathlib.Path(__file__).resolve()
    subcktCirObj = modulePath.parent.joinpath("circuit1.sp")
    return subcktCirObj


@pytest.fixture
def spiceFile2():
    modulePath = pathlib.Path(__file__).resolve()
    subcktCirObj = modulePath.parent.joinpath("circuit2.sp")
    return subcktCirObj


@pytest.fixture
def spiceFile3():
    modulePath = pathlib.Path(__file__).resolve()
    subcktCirObj = modulePath.parent.joinpath("circuit3.sp")
    return subcktCirObj


def test_subckt_line_extract(spiceFile1):
    xyceNetlistObj = hdl.spiceC(spiceFile1)
    subcktLines = xyceNetlistObj.subcktLineExtract()
    assert subcktLines == ".SUBCKT newckt a b c"


def test_subckt_line_with_param(spiceFile2):
    xyceNetlistObj = hdl.spiceC(spiceFile2)
    subcktLines = xyceNetlistObj.subcktLineExtract()
    assert subcktLines == ".SUBCKT newckt a b c PARAM: res = 1k"


def test_subckt_line_two_cont(spiceFile3):
    xyceNetlistObj = hdl.spiceC(spiceFile3)
    subcktLines = xyceNetlistObj.subcktLineExtract()

    assert subcktLines == ".SUBCKT newckt a b c PARAM: res = 1k cap = 1p"


def test_subckt_dict_extract(spiceFile1):
    xyceNetlistObj = hdl.spiceC(spiceFile1)
    subcktParams = xyceNetlistObj.extractSubcktParams()
    assert subcktParams["name"] == "newckt"
    assert subcktParams["pins"] == ["a", "b", "c"]


def test_subckt_dict_extract2(spiceFile2):
    xyceNetlistObj = hdl.spiceC(spiceFile2)
    subcktParams = xyceNetlistObj.extractSubcktParams()
    assert subcktParams["name"] == "newckt"
    assert subcktParams["pins"] == ["a", "b", "c"]
    assert subcktParams["params"] == {"res": "1k"}


def test_subckt_dict_extract3(spiceFile3):
    xyceNetlistObj = hdl.spiceC(spiceFile3)
    subcktParams = xyceNetlistObj.extractSubcktParams()
    assert subcktParams["name"] == "newckt"
    assert subcktParams["pins"] == ["a", "b", "c"]
    assert subcktParams["params"] == {"res": "1k", "cap": "1p"}


@pytest.fixture
def capvaModule():
    modulePath = pathlib.Path(__file__).resolve()
    vaModuleObj = modulePath.parent.joinpath("cap.va")
    return vaModuleObj


@pytest.fixture()
def delayvaModule():
    modulePath = pathlib.Path(__file__).resolve()
    vaModuleObj = modulePath.parent.joinpath("delay.va")
    return vaModuleObj


@pytest.fixture()
def flickerNvaModule():
    modulePath = pathlib.Path(__file__).resolve()
    vaModuleObj = modulePath.parent.joinpath("flickerNoise.va")
    return vaModuleObj


@pytest.fixture()
def resVaModule():
    modulePath = pathlib.Path(__file__).resolve()
    vaModuleObj = modulePath.parent.joinpath("res.va")
    return vaModuleObj


@pytest.fixture()
def diodeVaModule():
    modulePath = pathlib.Path(__file__).resolve()
    vaModuleObj = modulePath.parent.joinpath("diode.va")
    return vaModuleObj


def test_capvamodule(capvaModule):
    capvaObj = hdl.verilogaC(capvaModule)

    assert capvaObj.vaModule == "capacitor"
    assert capvaObj.pins == ["p", "n"]
    assert capvaObj.inPins == []
    assert capvaObj.inoutPins == ["p", "n"]
    assert capvaObj.instanceParams["c"] == "0"
    assert capvaObj.modelParams["c"] == "0"


#
#
def test_delayvamodule(delayvaModule):
    delayvaObj = hdl.verilogaC(delayvaModule)
    assert delayvaObj.vaModule == "sig_delay"
    assert delayvaObj.pins == ["in", "out1", "out2"]
    assert delayvaObj.inPins == ["in"]
    assert delayvaObj.outPins == ["out1", "out2"]
    assert delayvaObj.modelParams["td"] == "3e-6"


#
#
def test_flickervamodule(flickerNvaModule):
    flickerNObj = hdl.verilogaC(flickerNvaModule)
    assert flickerNObj.vaModule == "flickerNoise"
    assert flickerNObj.pins == ["p", "n"]
    assert flickerNObj.inPins == []
    assert flickerNObj.outPins == []
    assert flickerNObj.inoutPins == ["p", "n"]
    assert flickerNObj.modelParams["kf"] == "1.0e-20"
    assert flickerNObj.modelParams["ef"] == "1.0"
    assert flickerNObj.instanceParams["kf"] == "1.0e-20"


def test_resvamodule(diodeVaModule):
    diodeObj = hdl.verilogaC(diodeVaModule)
    assert diodeObj.vaModule == "diode"
    assert diodeObj.pins == ["a", "c"]
    assert diodeObj.inPins == []
    assert diodeObj.inoutPins == ["a", "c"]
    assert diodeObj.modelParams["IS"] == "1.0e-14"
    assert diodeObj.instanceParams == {}
