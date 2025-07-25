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
# (C) 2024 Revolution Semiconductor

from dataclasses import dataclass
from ..dataDefinitions import InitCond
from typing import Dict, Set, List
import copy
from .xyceConfig import (LTE_CHOICES, ANALYSIS_CHOICES, TRAN_METHODS,
                         DEFAULT_XYCE_ANALYSIS_CONFIG, DEFAULT_TIMEINT_OPTIONS,
                         DEFAULT_NONLIN_OPTIONS,
                         DEFAULT_DEVICE_OPTIONS, DEFAULT_PARSER_OPTIONS, BANNED_PARAMS,
                         DEFAULT_NLSTRAT_OPTIONS, DEFAULT_RUN_OPTIONS, HSPICE_EXT_OPTIONS)


@dataclass
class simOptions:
    timeintOptions: Dict
    nonlinOptions: Dict
    deviceOptions: Dict
    parserOptions: Dict


@dataclass
class xyceRunConfiguration:
    printHelp: bool
    outputBaseName: str
    logFile: bool
    binaryRawFile: str
    asciiRawFile: bool
    useNox: bool
    printParam: bool
    checkSyntax: bool
    quiet: bool
    varFileName: str
    noiseSourceFileName: str
    randomSeed: int
    maxOrder: int
    hspiceExt: int


class XyceOptions:

    def __init__(self) -> None:
        self.modelLibList = []  # model libraries list
        self.includePathsTupleList = []  # list of include paths
        self.variableCount = 0
        self.variablesDict: Dict[str, str] = {}
        self.outputsSet = {}
        self.analysisChoices = ANALYSIS_CHOICES
        self.analysesDict = copy.deepcopy(DEFAULT_XYCE_ANALYSIS_CONFIG)

        self.selectedAnalyses = list()
        self.saveOptionsDict: Dict[str, int] = {"saveNodes": 1, "saveCurrents": 1,
                                                "saveExpressions": 1, }
        self.simTextDict = {0: "TRAN", 1: "AC", 2: "NOISE", 3: "DC", 4: "HB"}
        self.tranMethods = copy.deepcopy(TRAN_METHODS)
        self.lteChoices = copy.deepcopy(LTE_CHOICES)
        self.nlstratChoices = copy.deepcopy(DEFAULT_NLSTRAT_OPTIONS)
        self.simOptions = simOptions(copy.deepcopy(DEFAULT_TIMEINT_OPTIONS),
                                     copy.deepcopy(DEFAULT_NONLIN_OPTIONS),
                                     copy.deepcopy(DEFAULT_DEVICE_OPTIONS),
                                     copy.deepcopy(DEFAULT_PARSER_OPTIONS), )
        self.initCondList: List[InitCond] = []
        self.nodeSetList: List[InitCond] = []
        self.vaFileSet = set()
        self.vaModelSet = set()
        self.instNamePrefix = ""
        self.tranLabels = list()
        self.globalVarsDict = dict()
        self.bannedParams = BANNED_PARAMS
        self.runConfig = xyceRunConfiguration(**DEFAULT_RUN_OPTIONS)
