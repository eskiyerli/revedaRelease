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
import defaultPDK.layoutLayers as laylyr

# common process parameters
dbu = 100  # grid points per micron

# Some predefined rules
# via defintions
con = ddef.viaDefTuple(
    "con", laylyr.contactLayer_drw, "", "0.1", "10", "0.1", "10", "0.1", "10"
)
v1 = ddef.viaDefTuple(
    "v1", laylyr.via1Layer_drw, "", "0.2", "10", "0.2", "10", "0.1", "10"
)
processVias = [con, v1]
processViaNames = [item.name for item in processVias]
