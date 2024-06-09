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
import revedaEditor.backend.dataDefinitions as ddef
import pdk.layoutLayers as laylyr
from pdk.sg13_tech import SG13_Tech as sg13
from quantiphy import Quantity

techClass = sg13()
techParams = techClass.techParams

# common process parameters
dbu = 1000  # grid points per micron

# Some predefined rules
# via defintions
cont = ddef.viaDefTuple("cont", laylyr.Cont_drw, "", 0.16, 0.16, 0.16, 0.16, 0.18, 10)
viamim = ddef.viaDefTuple('viamim', laylyr.Vmim_drw, "", techParams['TV1_a'], 10,
                          techParams['TV1_a'], 10, 0.84, 10)
# v1 = ddef.viaDefTuple(
#     "v1", laylyr.via1Layer_drw, "", "0.2", "10", "0.2", "10", "0.1", "10"
# )
# processVias = [con, v1]
# processViaNames = [item.name for item in processVias]
