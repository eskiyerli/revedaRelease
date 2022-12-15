#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  9 09:41:45 2022

@author: eskiyerli
"""


#   “Commons Clause” License Condition v1.0
#  #
#   The Software is provided to you by the Licensor under the License, as defined
#   below, subject to the following condition.
#  #
#   Without limiting other conditions in the License, the grant of rights under the
#   License will not include, and the License does not grant to you, the right to
#   Sell the Software.
#  #
#   For purposes of the foregoing, “Sell” means practicing any or all of the rights
#   granted to you under the License to provide to third parties, for a fee or other
#   consideration (including without limitation fees for hosting or consulting/
#   support services related to the Software), a product or service whose value
#   derives, entirely or substantially, from the functionality of the Software. Any
#   license notice or attribution required by the License must also include this
#   Commons Clause License Condition notice.
#  #
#   Software: Revolution EDA
#   License: Mozilla Public License 2.0
#   Licensor: Revolution Semiconductor (Registered in the Netherlands)

import pathlib


class verilogaC:
    """
    This class represents an imported verilog-A module.
    """

    def __init__(self, pathObj: pathlib.Path):
        keyWords = ["analog", "electrical"]
        self.vaModule = ''
        self.instanceParams = dict()
        self.modelParams = dict()
        self.inPins = list()
        self.inoutPins = list()
        self.outPins = list()
        self.statementLines = list()
        with open(pathObj) as f:
            self.fileLines = f.readlines()
        self.stripComments()
        self.oneLiners()
        # splitLines=[fileline.split() for fileline in fileLines]

    def stripComments(self):

        comment = False
        for line in self.fileLines:  # concatenate the lines until it reaches a ;
            stripLine = line.strip()
            if stripLine.startswith('/*'):
                comment = True
            if not comment:
                doubleSlashLoc = stripLine.find('//')
                if doubleSlashLoc > -1:
                    stripLine = stripLine[:doubleSlashLoc]
                if stripLine != '':
                    self.statementLines.append(stripLine)
            if comment and stripLine.endswith('*/'):
                comment = False

    def oneLiners(self):
        tempLine = ''
        oneLiners = list()
        for line in self.statementLines:
            stripLine = line.strip()
            if not stripLine.startswith('`include'):
                tempLine = f'{tempLine} {stripLine}'
            if stripLine.endswith(';'):
                oneLiners.append(tempLine.strip())
                splitLine = tempLine.strip().split()
                if splitLine:
                    if splitLine[0] == 'module':
                        self.vaModule = splitLine[1].split('(')[0]
                        indexLow = line.index("(")
                        indexHigh = line.index(")")
                        self.pins = [pin.strip() for pin in
                                     line[indexLow + 1: indexHigh].split(",")]
                    elif splitLine[0] == 'in' or splitLine[0] == 'input':
                        pinsList = splitLine[1].split(';')[0].split(',')
                        self.inPins.extend([pin.strip() for pin in pinsList])
                    elif splitLine[0] == 'out' or splitLine[0] == 'output':
                        pinsList = splitLine[1].split(';')[0].split(',')
                        self.outPins.extend([pin.strip() for pin in pinsList])
                    elif splitLine[0] == 'inout':
                        pinsList = splitLine[1].split(';')[0].split(',')
                        self.inoutPins.extend([pin.strip() for pin in pinsList])
                    elif splitLine[0] == "parameter":
                        paramDefPart = tempLine.split('*(')[0]
                        paramName = paramDefPart.split('=')[0].split()[-1].strip()
                        paramValue = paramDefPart.split('=')[1].split()[0].strip()

                        try:
                            paramAttr = tempLine.strip().split("(*")[1]
                        except IndexError:
                            paramAttr = ""
                        if "type" in paramAttr and '"instance"' in paramAttr:
                            # parameter value is between = and (*
                            self.instanceParams[paramName] = paramValue
                            if "xyceAlsoModel" in paramAttr and '"yes"' in paramAttr:
                                self.modelParams[paramName] = paramValue
                        else:  # no parameter attribute statement
                            self.modelParams[paramName] = paramValue
                tempLine = ''
