import pytest
import pathlib
import revedaEditor.backend.hdlBackEnd as hdl


@pytest.fixture()
def diodeVAObj():
    modulePath = pathlib.Path(__file__).resolve()
    diodePathObj = modulePath.parent.joinpath("diode.va")
    diodeVaObj = hdl.verilogaC(diodePathObj)
    return diodeVaObj


test
