# This software is proprietary and confidential.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited.
#
# This software is provided as an add-on to Revolution EDA distributed under the
# Mozilla Public License, version 2.0. The source code for this add-on software
# is not made available and all rights are reserved.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


LTE_CHOICES = ("0", "1", "2", "3")

ANALYSIS_CHOICES = ("TRAN", "AC", "NOISE", "DC", "HB", "OP")
TRAN_METHODS = (
    "Trap",
    "Gear",
)
DEFAULT_XYCE_ANALYSIS_CONFIG = {
    "tran": [
        False,
        {
            "tInitStep": "1u",
            "tstop": "1m",
            "tstart": "0",
            "tMaxStep": "",
            "tSchedule": "",
            "uiuc": 0,
        },
    ],
    "ac": [
        False,
        {
            "linlog": 2,
            "fstep": "100",
            "fstart": "1k",
            "fstop": "100k",
        },
    ],
    "noise": [
        False,
        {
            "outnode": "",
            "refnode": "0",
            "inputSource": "",
            "sourceResistance": "",
            "linlog": 0,
            "fstep": "100 ",
            "fstart": "1k",
            "fstop": "1Meg",
        },
    ],
    "dc": [
        False,
        {
            "sweepType": 0,
            "input": "",  # name of input source or variable
            "linlog": 0,
            "start": "0",
            "stop": "1",
            "step": "10",
        },
    ],
    "op": [
        True,
        {
            "type": 0,
            "filename": "",
            "level": 0
        },
    ],
    "hb": [
        False,
        {
            "frequency": "1e9",
            "numfreq": "10",
            "intmodmax": "3",
            "tahb": False,
            "startupperiods": "2",
            "numpts": "101",
            "voltlim": True,
            "saveicdata": False,
        },
    ],
}

DEFAULT_NONLIN_OPTIONS = {
            "nox": 1,
            "searchmethod": 0,
            "nlstrategy": 0,
            "abstol": "1e-12",
            "reltol": "1e-3",
            "maxstep": "200",
            "maxsearchstep": "2",
        }
DEFAULT_DEVICE_OPTIONS = {
            "temp": "27",
            "tnom": "27",
            "gmin": "1e-12",
            "voltlim": 1,
            "b3soivoltlim": 1,
            "maxtimestep": "1e99",
            "minres": "0",
            "mincap": "0",
        }

DEFAULT_TIMEINT_OPTIONS = {
            "method": 7,
            "newlte": 1,
            "erroption": 0,
            "abstol": "1e-12",
            "reltol": "1e-3",
            "delmax": "1e1",
        }
DEFAULT_PARSER_OPTIONS = {"model_binning": 1, "scale": "1.0"}
DEFAULT_NLSTRAT_OPTIONS = ["Newton", "Gradient", "Trust Region"]
BANNED_PARAMS = ('TEMP', 'VT', 'FREQ', 'HERTZ', 'TIME', 'GMIN', 'TEMPER')
DEFAULT_RUN_OPTIONS = {
    "printHelp": False,
    "outputBaseName": "",
    "logFile": True,
    "binaryRawFile": True,
    "asciiRawFile": False,
    "useNox": True,
    "printParam": False,
    "checkSyntax": False,
    "quiet": False,
    "varFileName": "",
    "noiseSourceFileName": "",
    "randomSeed": 0,
    "maxOrder": 2,
    "hspiceExt": 0,
}
HSPICE_EXT_OPTIONS = ['All', 'Separator', 'Units', 'Math', 'None']
