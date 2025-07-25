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
# (C) 2025 Revolution Semiconductor

import logging
import os
import pathlib
import platform
from datetime import datetime
import numpy as np
from typing import List, Tuple, Optional, Set, Dict, TextIO

from PySide6.QtCore import (Qt, QProcess)
from PySide6.QtWidgets import QFormLayout, QDialog, QMainWindow, QApplication
from dotenv import load_dotenv
from pyqtgraph.colormap import path
from plugins.revedasim import dataDefinitions as sddef
from plugins.revedasim import fieldValues as fvs
from plugins.revedasim import analysisDialogue as ad
from plugins.revedasim import dialogueWindows as dw
from plugins.revedasim import processManager as prm
from plugins.revedasim.analysisPanel import  xyceAnalysesModel
from plugins.revedasim.baseSimulator import BaseSimulator
from revedaEditor.backend.libBackEnd import viewItem, cellItem, libraryItem
from plugins.revedasim.xyceConfig.xyceOptions import XyceOptions, HSPICE_EXT_OPTIONS


class XyceSimulator(BaseSimulator):
    """Class for Xyce simulator."""

    def __init__(self, simMainW: QMainWindow, runSetup: sddef.SimulatorRunSetup,
                 benchViewItem: viewItem):
        if runSetup.simulatorName == "Xyce":
            self.simMainW = simMainW
            self._app = QApplication.instance()
            self.logger = logging.getLogger('reveda')
            self.runSetup = runSetup
            self.benchViewItem = benchViewItem
            self.cellItem: cellItem = self.benchViewItem.parent()
            self.libraryItem: libraryItem = self.cellItem.parent()

            self.netlistPathObj = self.generateNetlistPath(
                self.runSetup.outputPrefixPath, self.cellItem.cellName)
            load_dotenv()
            vaModulePath = os.getenv("REVEDA_VA_MODULE_PATH")
            if vaModulePath:
                if pathlib.Path(vaModulePath).is_absolute():
                    self._vaModulePathObj = pathlib.Path(vaModulePath)
                else:
                    self._vaModulePathObj = self.runSetup.pdkPath.joinpath(vaModulePath)
            else:
                self._vaModulePathObj = self.runSetup.outputPrefixPath.joinpath(".vaModules")
                self._vaModulePathObj.mkdir(parents=True, exist_ok=True)
        else:
            raise ValueError(f"Invalid simulator name: {runSetup.simulatorName}")

    def initialize(self, xyceOptions: XyceOptions):
        """Initialize or change XyceSimulator attributes."""
        xyceOptionsDict = vars(xyceOptions)
        for key, value in xyceOptionsDict.items():
            setattr(self, key, value)

    def generateNetlistPath(self, outputPathPrefix: pathlib.Path, baseName: str) \
            -> (
            pathlib.Path):
        return outputPathPrefix.joinpath(self.cellItem.cellName,
                                         self.benchViewItem.viewName,
                                         baseName).with_suffix(".cir")

    def createRunDeckPath(self, key: str)-> pathlib.Path:
        netlistPathObjParts = list(self.netlistPathObj.with_suffix("").parts)
        netlistPathObjParts[-1] += f"_{key}"
        runDeckObj = pathlib.Path(*netlistPathObjParts).with_suffix(".sp")
        return runDeckObj

    def updateAnalysesModel(self, dlg: ad.xyceAnalysesDialogue, analysesModel: xyceAnalysesModel):

        for key, _ in dlg.tabWidgets.items():
            self.analysesDict[key][0] = dlg.enableCheckDict[key].isChecked()
            valuesList = [fvs.returnFieldValue(
                dlg.formLayoutDict[key].itemAt(row, QFormLayout.FieldRole)) for row in
                range(dlg.formLayoutDict[key].rowCount())]
            self.analysesDict[key][1].update(
                zip(self.analysesDict[key][1].keys(), valuesList))
        analysesModel.populateModel(self.analysesDict)

    def updateSimulationOptions(self, dlg: dw.xyceSimOptionsDialogue):

        dlg.tranMethodRadioBox.button(self.simOptions.timeintOptions["method"]).setChecked(
            True)
        dlg.lteRadioButtons[self.simOptions.timeintOptions["newlte"]].setChecked(True, )
        dlg.timeintabstolEdit.setText(self.simOptions.timeintOptions["abstol"], )
        dlg.timeintreltolEdit.setText(self.simOptions.timeintOptions["reltol"], )
        dlg.timeintdelmaxEdit.setText(self.simOptions.timeintOptions["delmax"], )
        dlg.nonlinabstolEdit.setText(self.simOptions.nonlinOptions["abstol"], )
        dlg.nonlinreltolEdit.setText(self.simOptions.nonlinOptions["reltol"], )
        # dlg.nonlindelmaxEdit.setText(
        #     self.simOptions.nonlinOptions["delmax"],
        # )
        dlg.nonlinmaxStepEdit.setText(self.simOptions.nonlinOptions["maxstep"], )
        dlg.nonlinmaxsearchStepEdit.setText(
            self.simOptions.nonlinOptions["maxsearchstep"], )
        dlg.devicegminEdit.setText(self.simOptions.deviceOptions["gmin"])
        dlg.deviceresminEdit.setText(self.simOptions.deviceOptions["minres"], )
        dlg.devicecapminEdit.setText(self.simOptions.deviceOptions["mincap"], )
        dlg.tempEdit.setText(self.simOptions.deviceOptions["temp"])
        dlg.tnomEdit.setText(self.simOptions.deviceOptions["tnom"])
        dlg.binningCheckbox.setChecked(self.simOptions.parserOptions["model_binning"])
        dlg.dimensionScaleEdit.setText(self.simOptions.parserOptions["scale"], )
        dlg.noxCheckBox.setChecked(self.simOptions.nonlinOptions["nox"])
        dlg.nlstrategyCB.addItems(self.nlstratChoices)
        dlg.nlstrategyCB.setCurrentIndex(self.simOptions.nonlinOptions["nlstrategy"])

        if dlg.exec() == QDialog.Accepted:
            self.simOptions.timeintOptions["method"] = (dlg.tranMethodRadioBox.checkedId())
            self.simOptions.timeintOptions["newlte"] = dlg.lteRadioBox.checkedId()
            self.simOptions.timeintOptions["abstol"] = dlg.timeintabstolEdit.text()
            self.simOptions.timeintOptions["reltol"] = dlg.timeintreltolEdit.text()
            self.simOptions.timeintOptions["delmax"] = dlg.timeintdelmaxEdit.text()

            self.simOptions.nonlinOptions["nox"] = (1 if dlg.noxCheckBox.isChecked() else 0)
            self.simOptions.nonlinOptions["nlstrategy"] = (dlg.nlstrategyCB.currentIndex())
            self.simOptions.nonlinOptions["abstol"] = dlg.nonlinabstolEdit.text()
            self.simOptions.nonlinOptions["reltol"] = dlg.nonlinreltolEdit.text()
            # self.simOptions.nonlinOptions["delmax"] = dlg.nonlindelmaxEdit.text()
            self.simOptions.nonlinOptions["maxstep"] = dlg.nonlinmaxStepEdit.text()
            self.simOptions.nonlinOptions["maxsearchstep"] = (
                dlg.nonlinmaxsearchStepEdit.text())

            self.simOptions.deviceOptions["gmin"] = dlg.devicegminEdit.text()
            self.simOptions.deviceOptions["minres"] = dlg.deviceresminEdit.text()
            self.simOptions.deviceOptions["mincap"] = dlg.devicecapminEdit.text()

            self.simOptions.deviceOptions["temp"] = dlg.tempEdit.text()
            # self.tempValueEdit.setText(self.simOptions.deviceOptions["temp"])
            self.simOptions.deviceOptions["tnom"] = dlg.tnomEdit.text()

            self.simOptions.parserOptions["model_binning"] = (
                1 if dlg.binningCheckbox.isChecked() else 0)
            self.simOptions.parserOptions["scale"] = dlg.dimensionScaleEdit.text()

    def processPlugins(self) -> Tuple[Optional[pathlib.Path], Set[str], List[pathlib.Path]]:
        soFiles = list(self._vaModulePathObj.glob("*.so"))
        if platform.system() in {"Windows", "Darwin"}:
            if hasattr(self, "logger"):
                self.logger.info(f"{platform.system()} is not supported for Xyce "
                                  f"plugins")
            return None, set(), []


        destinationPath = self.netlistPathObj.parent / ".plugins"
        try:
            destinationPath.mkdir(parents=True, exist_ok=True)
        except FileNotFoundError:
            if hasattr(self, "logger"):
                self.logger.error("Cannot create .plugins directory")
            return None, set()

        pluginPathsSet = {
            pathlib.Path(line.split()[1])
            for includeLine in self.includePathsTupleList if includeLine[0]
            for line in pathlib.Path(includeLine[1]).read_text().splitlines()
            if line.startswith("*.HDL")
        }
        pluginPathsSet.update(
            pathlib.Path(line.split()[1])
            for line in self.netlistPathObj.read_text().splitlines()
            if line.startswith("*.HDL")
        )

        pluginNamesSet = set()
        for pluginPath in pluginPathsSet:
            process = QProcess()
            process.setProgram(str(self.runSetup.pluginPath))
            process.setArguments(["-o", pluginPath.name, str(pluginPath), str(destinationPath)])
            process.start()
            process.waitForFinished()
            pluginNamesSet.add(
                f"lib{pluginPath.name}.so" if platform.system() == "Linux" else pluginPath.name)

        return destinationPath, pluginNamesSet, soFiles

    def writeParameters(self, spfile:TextIO) -> None:
        paramList, stepList, valuesList = [], [], []

        for key, value in self.variablesDict.items():
            if not key.strip():
                continue

            value = value.strip()
            if self.checkParamName(key):
                if ":" in value:
                    parts = list(map(str.strip, value.split(":")))
                    if len(parts) == 2:
                        stepList.append(f" {key} {parts[0].strip()} {parts[1].strip()} 1.0")
                    elif len(parts) == 3:
                        stepList.append(
                            f" {key} {parts[0].strip()} {parts[2].strip()} {parts[1].strip()}")
                    paramList.append(f" {key}={parts[0].strip()}")
                elif "," in value:
                    parts = list(map(str.strip, value.split(",")))
                    valuesList.append((f" {key}", " ".join(parts)))
                    if self.checkParamName(key):
                        paramList.append(f" {key}={parts[0]}")
                else:
                    paramList.append(f" {key}={value}")
        if paramList:
            for param in paramList:
                spfile.write(f".PARAM {param.upper()}\n")
        if stepList:
            for step in stepList:
                spfile.write(f".STEP {step}\n")
        if valuesList:
            for value in valuesList:
                spfile.write(f".STEP {value[0]} LIST {value[1]}\n")

    def createRunSet(self, initCondModel, nodesetModel, outputsModel) -> None:
        if self.analysesDict:
            for key, value in self.analysesDict.items():
                if value[0]:
                    runDeckObj = self.createRunDeckPath(key)
                    with runDeckObj.open("w") as spfile:
                        spfile.write("*".join(["\n", 80 * "*", "\n",
                                               f"* Library: {self.libraryItem.libraryName}\n",
                                               f"* Top Cell Name: {self.cellItem.cellName}\n",
                                               f"* View Name: {self.benchViewItem.viewName}\n",
                                               f"* Date: {datetime.now()}\n", 80 * "*",
                                               "\n", ]))
                        spfile.write(".PREPROCESS REPLACEGROUND TRUE\n")
                        spfile.write(f'.INC "{str(self.netlistPathObj)}"\n')
                        self.writeModelLibs(spfile)
                        self.writeIncludePaths(spfile)
                        self.writeXyceOptions(key, spfile, value)
                        if key.strip() == 'tran':
                            spfile.write(
                                f".OPTIONS TIMEINT {fvs.dictToString(self.simOptions.timeintOptions)}\n")
                        spfile.write(f"{self.writeAnalysisStatement(key, value[1])}")

                        self.writeParameters(spfile)
                        self.writeInitConditions(spfile, initCondModel)
                        self.writeNodesets(spfile, nodesetModel)
                        self.writePrintLines(key, spfile, outputsModel)
                        spfile.write(".END\n")
        else:
            if hasattr(self, "logger"):
                self.logger.warning("No analysis selected")
            else:
                print("No analysis selected")

    def writeIncludePaths(self, spfile):
        if self.includePathsTupleList:
            for item in self.includePathsTupleList:
                if item[0]:
                    spfile.write(f".INC '{item[1]}'\n")

    def writeModelLibs(self, spfile):
        if self.modelLibList:
            for item in self.modelLibList:
                if item.select:
                    spfile.write(
                        f'.LIB "{item.modelPath}" {item.modelSection}\n')

    def writeXyceOptions(self, key, spfile, value):
        spfile.write(
            f".OPTIONS NONLIN {fvs.dictToString(self.simOptions.nonlinOptions)}\n")
        spfile.write(
            f".OPTIONS DEVICE {fvs.dictToString(self.simOptions.deviceOptions)}\n")
        spfile.write(
            f".OPTIONS PARSER {fvs.dictToString(self.simOptions.parserOptions)}\n")
        # if self.analysesDict:
        #     for key, value in self.analysesDict.items():
        #         if value[0]:



    # def writeParameters(self, paramDict: Dict) -> Tuple[List[str], List[str], List[str]]:
    #     paramStringList = list()
    #     stepStringList = list()
    #     listStringList = list()
    #     for key, value in paramDict.items():
    #         if key.strip():
    #             stripValue = value.strip()
    #             if stripValue.startswith("{") and stripValue.endswith("}"):  # expression
    #                 paramStringList.append(f" {key}={stripValue[1:-1]}")
    #             elif ":" in stripValue:
    #                 splitParms = stripValue.split(":")
    #                 match len(splitParms):
    #                     case 2:
    #                         stepStringList.append(f" {key} {splitParms[0].strip()}"
    #                                               f' {splitParms[1].strip()} "1.0"')
    #                     case 3:
    #                         stepStringList.append(f" {key} {splitParms[0].strip()} "
    #                                               f"{splitParms[2].strip()} "
    #                                               f"{splitParms[1].strip()}")
    #                 if self.checkParamName(key):
    #                     paramStringList.append(f" {key}={splitParms[0].strip()}")
    #             elif "," in stripValue:
    #                 splitParms = list(map(str.strip, stripValue.split(",")))
    #                 listStringList.append((f" {key}", " ".join(splitParms)))
    #                 if self.checkParamName(key):
    #                     paramStringList.append(f" {key}={splitParms[0].strip()}")
    #             else:
    #                 if self.checkParamName(key):
    #                     paramStringList.append(f" {key}={value}")
    #     return paramStringList, stepStringList, listStringList

    def writePrintLines(self, key: str, spfile: TextIO, outputsModel) -> None:
        """
        Write .PRINT lines to the netlist file based on the outputs selected in the outputs model.

        Args:
            key (str): The analysis to write the print lines for.
            spfile (TextIO): The file to write the print lines to.

        Returns:
            None
        """

        if self.saveOptionsDict["saveNodes"] == 1:
            self.writeOutputs(key, "V", spfile,outputsModel)
        elif self.saveOptionsDict["saveNodes"] == 2:
            self.writeOutputLines(key, spfile, "V(*)")
        if self.saveOptionsDict["saveCurrents"] == 1:
            self.writeOutputs(key, "I", spfile, outputsModel)
        elif self.saveOptionsDict["saveCurrents"] == 2:
            self.writeOutputLines(key, spfile, "I(*)")
        if self.saveOptionsDict["saveExpressions"] != 0:
            self.writeExpressions(key, spfile, outputsModel)

    def writeOutputs(self, key: str, outputType: str, spfile: TextIO, outputsModel):
        """
        Write outputs to a file based on the outputs model.

        Args:
        key (str): The key for the output.
        type (str): The type of output to filter by.
        spfile (TextIO): The file to write the outputs to.
        """
        outputString = ""
        lines = ""

        for row in range(outputsModel.rowCount()):
            if (outputsModel.data(outputsModel.index(row, 3),
                              Qt.CheckStateRole) == Qt.Checked or outputsModel.data(
                outputsModel.index(row, 4), Qt.CheckStateRole) == Qt.Checked):
                output = outputsModel.data(outputsModel.index(row, 1))
                if output.startswith(outputType):
                    if len(outputString) + len(output) < 120:
                        outputString += f" {output}"
                    else:
                        lines += f"{outputString}\n"
                        outputString = f"+ {output} "

        if not lines:
            lines = outputString
        self.writeOutputLines(key, spfile, lines)

    def writeExpressions(self, key: str, spfile: TextIO, outputsModel):
        output_chunks = []
        current_chunk = ""

        for row in range(outputsModel.rowCount()):
            if any(outputsModel.data(outputsModel.index(row, col), Qt.CheckStateRole) == Qt.Checked
                   for col in (3, 4)):
                output = outputsModel.data(outputsModel.index(row, 1)).strip()
                if output.startswith("{") and output.endswith("}"):
                    output = output[1:-1]  # Remove surrounding braces
                    if (len(current_chunk) + len(
                            output) + 3 > 120):  # +3 for " {}" and space
                        output_chunks.append(current_chunk.rstrip())
                        current_chunk = f"+ {{{output}}} "
                    else:
                        current_chunk += f" {{{output}}}"

        if current_chunk:
            output_chunks.append(current_chunk.rstrip())

        lines = "\n".join(output_chunks) if output_chunks else ""
        self.writeOutputLines(key, spfile, lines)

    @staticmethod
    def writeOutputLines(key: str, spfile: TextIO, lines: str):
        if lines.strip():
            key_map = {"tran": ".PRINT TRAN", "ac": ".PRINT AC", "noise": ".PRINT NOISE",
                "dc": ".PRINT DC", "hb": ".PRINT HB", "op": ".PRINT OP"}
            base_command = key_map.get(key, "")
            if key == "ac":
                spfile.write(f"{base_command} {lines}\n.PRINT AC_IC {lines}\n")
            elif key == "hb":
                spfile.write(f"{base_command} {lines}\n.PRINT HB_IC {lines}\n"
                             f".PRINT HB_FD {lines}\n.PRINT HB_TD {lines}\n"
                             f".PRINT HB_STARTUP {lines}\n")
            else:
                spfile.write(f"{base_command} {lines}\n")

    def writeInitConditions(self, spfile: TextIO, initCondModel):
        for row in range(initCondModel.rowCount()):
            if initCondModel.data(initCondModel.index(row, 1)):
                initCond = initCondModel.data(initCondModel.index(row, 0))
                initCondValue = initCondModel.data(initCondModel.index(row, 1))
                if initCondValue:
                    spfile.write(f".IC {initCond}={initCondValue}\n")

    def writeNodesets(self, spfile: TextIO, nodesetModel):
        for row in range(nodesetModel.rowCount()):
            if nodesetModel.data(nodesetModel.index(row, 1)):
                nodeSet = nodesetModel.data(nodesetModel.index(row, 0))
                nodeSetValue = nodesetModel.data(nodesetModel.index(row, 1))
                if nodeSetValue:
                    spfile.write(f".NODESET {nodeSet}={nodeSetValue}\n")


    def writeAnalysisStatement(self, key: str, valuesDict: Dict):
        match key:
            case "tran":
                tranString = ""
                for key, value in valuesDict.items():
                    if value:
                        if key not in ("uiuc", "tSchedule"):
                            tranString += fvs.numOrParameter(value)
                        elif key == "tSchedule":
                            tranString += f" {{schedule({value})}}"
                        elif key == "uiuc":
                            tranString += " UIC"
                return f".TRAN {tranString}\n"
            case "ac":
                acString = ""
                for key, value in valuesDict.items():
                    if value:
                        if key == "linlog":
                            acString += self.sweepType(value)
                        else:
                            acString += fvs.numOrParameter(value)
                return f".AC {acString}\n"
            case "noise":
                noiseString = ""
                for key, value in valuesDict.items():
                    match key:
                        case "outnode":
                            noiseString += f" V({value}"
                        case "refnode":
                            if value:
                                noiseString += f",{value})"
                            else:
                                noiseString += ")"
                        case "inputSource":
                            if value:
                                noiseString += f" {value}"
                        case "linlog":
                            noiseString += self.sweepType(value)
                        case "fstep":
                            noiseString += fvs.numOrParameter(value)
                        case "fstart":
                            noiseString += fvs.numOrParameter(value)
                        case "fstop":
                            noiseString += fvs.numOrParameter(value)
                return f".NOISE {noiseString}\n"
            case "dc":
                dcString = ""
                # there is an error in the keys order.
                keyOrder = ["linlog", "input", "sweepType", "start", "stop", "step", ]
                valuesDict = {k: valuesDict[k] for k in keyOrder}
                for key, value in valuesDict.items():
                    match key:
                        case "linlog":
                            dcString += self.sweepType(value)
                        case "input":
                            if int(valuesDict["sweepType"]):
                                dcString += (
                                    f" {{{list(self.variablesDict.keys())[value]}}}")
                            else:
                                dcString += f" {value}"
                        case "start":
                            dcString += fvs.numOrParameter(value)
                        case "stop":
                            dcString += fvs.numOrParameter(value)
                        case "step":
                            dcString += fvs.numOrParameter(value)
                return f".DC {dcString}\n"
            case "hb":
                hbString = ""
                hbOptionsStr = ""
                for key, value in valuesDict.items():
                    match key:
                        case "frequency":
                            hbString += f" {value.replace(',', ' ')}"
                        case "numfreq":
                            hbOptionsStr += f" NUMFREQ={int(value)}"
                        case "intmodmax":
                            hbOptionsStr += f" INTMODMAX={int(value)}"
                        case "tahb":
                            hbOptionsStr += f" TAHB={int(value)}"
                        case "startupperiods":
                            if valuesDict["tahb"]:
                                hbOptionsStr += f" NUMPTS={int(value)}"
                        case "numpts":
                            hbOptionsStr += f" NUMPTS={int(value)}"
                        case "voltlim":
                            hbOptionsStr += f" VOLTLIM={int(value)}"
                        case "saveicdata":
                            hbOptionsStr += f" SAVEICDATA={int(value)}"

                return f".OPTIONS HBINT {hbOptionsStr}\n.HB {hbString}\n"
            case "op":
                opString = ".OP\n"  # default
                saveString = ""
                for key, value in valuesDict.items():
                    match key:
                        case "type":
                            typeString = "IC" if value == 0 else "NODESET"
                            saveString += f" TYPE={typeString}"
                        case "filename":
                            saveString += f" FILE={pathlib.Path(value).name}"
                        case "level":
                            levelString = "ALL" if value == 0 else "NONE"
                            saveString += f" LEVEL={levelString}"
                opString += f".SAVE {saveString}\n"
                return opString
            case _:
                return "\n"



    def createRunArguments(self) -> List[str]:
        argumentsList = []
        simulationPathObj = self.netlistPathObj.parent
        pluginsPath, pluginNamesSet, soFiles = self.processPlugins()

        # Combine plugin paths and SO files in one step if either exists
        if pluginNamesSet or soFiles:
            pluginsPaths = [str(pluginsPath / pluginName) for pluginName in pluginNamesSet] + soFiles
            if pluginsPaths:
                argumentsList.extend(["-plugin", ",".join(str(ppath) for ppath in pluginsPaths)])

        if self.runConfig.printHelp:
            argumentsList.append("-h")
            return argumentsList
        if self.runConfig.checkSyntax:
            argumentsList.append("-syntax")
            return argumentsList
        if self.runConfig.asciiRawFile:
            argumentsList.append("-a")
        if self.runConfig.useNox:
            argumentsList.extend(["-nox", "on"])
        else:
            argumentsList.append(["-nox", "off"])
        if self.runConfig.printParam:
            argumentsList.append("-param")
        if self.runConfig.outputBaseName != "":
            argumentsList.append(["-o", f"{self.runConfig.outputBaseName}"])
        if self.runConfig.quiet:
            argumentsList.append("-quiet")
        if self.runConfig.varFileName:
            argumentsList.extend(
                ["-namesfile", str(simulationPathObj / self.runConfig.varFileName)])
        if self.runConfig.noiseSourceFileName:
            argumentsList.extend(["-noise_names_file",
                                  str(simulationPathObj / self.runConfig.noiseSourceFileName), ])
        if self.runConfig.randomSeed:
            argumentsList.extend(["-randseed", str(self.runConfig.randomSeed)])
        if self.runConfig.maxOrder:
            argumentsList.extend(["-maxord", str(self.runConfig.maxOrder)])
        if self.runConfig.hspiceExt < 4:
            argumentsList.extend(
                ["-hspice-ext", HSPICE_EXT_OPTIONS[self.runConfig.hspiceExt]])
        return argumentsList

    def runSimulation(self, processManager: prm.ProcessManager):

        os.chdir(self.netlistPathObj.parent)

        if self.analysesDict:
            for key, value in self.analysesDict.items():
                if value[0]:
                    runDeckObj = self.createRunDeckPath(key)
                    argumentsList = self.createRunArguments()
                    if self.runConfig.binaryRawFile:
                        if key == 'hb':
                            # hb analysis does not accept raw file option
                            argumentsList.extend(["-a"])
                        else:
                            argumentsList.extend(["-r", f"{runDeckObj.with_suffix('.raw').name}"])
                    if self.runConfig.logFile:
                        argumentsList.extend(
                            ["-l", self.netlistPathObj.parent.joinpath(
                                runDeckObj.with_suffix('.log')).name])
                    argumentsList.append(runDeckObj.name)
                    if self.runConfig.printParam:
                        paramFileObj = self.netlistPathObj.parent / (
                            f"{self.netlistPathObj.stem}_{key}_param.txt")
                        processManager.add_process(str(self.runSetup.simulatorPath),
                            argumentsList, str(paramFileObj), )
                        pass
                    else:
                        processManager.add_process(str(self.runSetup.simulatorPath),
                            argumentsList)
                        pass

    @staticmethod
    def processHierarchyTrail(hierString: str) -> str:
        splitHierStringList = hierString.split(".")
        if len(splitHierStringList) > 1:
            return f"{':'.join([f'X{strItem}' for strItem in splitHierStringList[:-1]])}:"
        else:
            return ""

    @staticmethod
    def sweepType(value):
        match value:
            case 0:
                return " LIN"
            case 1:
                return " OCT"
            case 2:
                return " DEC"
            case _:
                return " LIN"


    def checkParamName(self, key: str) -> bool:
        return key.upper() not in self.bannedParams

    def plotOutputs(self, outputsSet: set):
        """Plot outputs from the simulation results."""
        import importlib

        if self._app.plugins.get("plugins.revedaPlot") is None:
            raise RuntimeError("revedaPlot plugin is not available.")
        else:
            revedaPlot = self._app.plugins.get("plugins.revedaPlot")
            prf = importlib.import_module(f"{revedaPlot.__name__}.processRawFile")
            paf = importlib.import_module(f"{revedaPlot.__name__}.processAsciFile")
            oacph = importlib.import_module(f"{revedaPlot.__name__}.outputACPrefixHandler")
            if self.runConfig.binaryRawFile:
                xcolumn = 0
                for key, value in self.analysesDict.items():
                    if value[0]:
                        runDeckObj = self.createRunDeckPath(key)
                        rawFile = runDeckObj.with_suffix(".raw")
                        rawDataFileObj = prf.rawDataObj(rawFile)
                        dataFrames = rawDataFileObj.get_dataframes()

                        for dft in dataFrames:
                            try:
                                ycolumns = []
                                if key == "ac":
                                    ycolumns = oacph.processOutputsWPrefixes(dft,outputsSet)
                                elif key == 'hb':
                                    # don't plot. Will use ascii plot
                                    pass
                                else:
                                    dft, ycolumns = prf.processRawFile(dft, outputsSet)
                                    #
                                    #
                                    # # Fallback to traditional column indexing if no prefixes processed
                                    # if not ycolumns:
                                    #     for output in outputsSet:
                                    #         try:
                                    #             ycolumns.append(
                                    #                 dft.dataFrame.columns.index(output[2:-1]))
                                    #         except ValueError:
                                    #             self.logger.warning(f'Column for output {output} not found.')

                                # plotMainWindow.plotData(dft, xcolumn, ycolumns)
                                return (dft, xcolumn, ycolumns)
                            except ValueError:
                                self.logger.warning('No output signals found.')

                # plotMainWindow.show()
            elif self.runConfig.asciiRawFile:
                xcolumn = 0
                paf = self._app.plugins.get("plugins.revedaPlot").processAsciFile
                for key, value in self.analysesDict.items():
                    if value[0]:
                        runDeckObj = self.createRunDeckPath(key)
                        if key == "hb":
                            fdFilePath:pathlib.Path = runDeckObj.with_suffix(".HB.FD.prn")
                            tdFilePath: pathlib.Path = runDeckObj.with_suffix(".HB.TD.prn")
                            fdDataFileObj = paf.AsciiDataObj(fdFilePath)
                            tdDataFileObj = paf.AsciiDataObj(tdFilePath)
                            fdDataFrames = fdDataFileObj.get_dataframes()
                            tdDataFrames = tdDataFileObj.get_dataframes()
                        #     for fdDataFrame in fdDataFrames:
                        #         fdDataFrame.plot()
                        #     for tdDataFrame in tdDataFrames:
                        #         tdDataFrame.plot()
                        # else:
                        #     # Handle regular ASCII files (DC, AC, TRAN, etc.)
                        #     prnFilePath: pathlib.Path = runDeckObj.with_suffix(".prn")
                        #     if prnFilePath.exists():
                        #         try:
                        #             dataFileObj = paf.AsciiDataObj(prnFilePath)
                        #             dataFrames = dataFileObj.get_dataframes()
                        #
                        #             for dft in dataFrames:
                        #                 try:
                        #                     ycolumns = []
                        #                     if key == "ac":
                        #                         ycolumns = plf.plotACSignal(dft, outputsSet)
                        #                     else:
                        #                         # Use prefix-aware plotting for all other analysis types
                        #                         updated_dft, ycolumns = plf.plotSignalWithPrefixes(dft, outputsSet)
                        #                         dft = updated_dft
                        #
                        #                         # Fallback to traditional column indexing if no prefixes processed
                        #                         if not ycolumns:
                        #                             for output in outputsSet:
                        #                                 try:
                        #                                     ycolumns.append(
                        #                                         dft.dataFrame.columns.index(output[2:-1]))
                        #                                 except ValueError:
                        #                                     self.logger.warning(f'Column for output {output} not found.')
                        #
                        #                     return (dft, xcolumn, ycolumns)
                        #                 except ValueError:
                        #                     self.logger.warning('No output signals found.')
                        #         except FileNotFoundError:
                        #             self.logger.warning(f'PRN file {prnFilePath} not found.')
                        #         except Exception as e:
                        #             self.logger.error(f'Error processing ASCII file {prnFilePath}: {str(e)}')
