import pathlib


class verilogaC:
    """
    This class represents an imported verilog-A module.
    """

    def __init__(self, pathObj: pathlib.Path):
        keyWords = ["analog", "electrical"]
        self.instanceParams = {}
        self.modelParams = {}
        with open(pathObj) as f:
            fileLines = f.readlines()
        # splitLines=[fileline.split() for fileline in fileLines]
        newLines = []
        comment = False
        for line in fileLines:  # concatenate the lines until it reaches a ;
            strippedLine = line.strip()
            if strippedLine:  # line is not empty
                if strippedLine[:2] == "/*":  # check if it starts a comment line
                    comment = True  # comment flag is raised.
                if not comment and strippedLine[:2] != "//":
                    newLines.append(strippedLine)
                if comment and strippedLine[-3:] == "*/":
                    comment = False
        fileLines = []  # empty the list
        tempLine = ""
        moduleFlag = False
        for line in newLines:
            if line.split()[0] == "module":  # wait until module statement
                moduleFlag = True
            if moduleFlag and line.split()[0] not in keyWords:
                tempLine += line
                if line[-1] == ";":
                    fileLines.append(tempLine[:-1])  # remove trailing semi-colon
                    tempLine = ""

        for line in fileLines:
            splitLine = line.split()
            if splitLine:
                if splitLine[0] == "module":
                    self.vaModule = splitLine[1].split("(")[0]
                    indexLow = line.index("(")
                    indexHigh = line.index(")")
                    self.pins = [pin.strip() for pin in
                                 line[indexLow + 1: indexHigh].split(",")]
                elif splitLine[0] == "in":
                    self.inPins = self.extractPin(line, 3)
                elif splitLine[0] == "out":
                    self.outPins = self.extractPin(line, 4)
                elif splitLine[0] == "inout":
                    self.inoutPins = self.extractPin(line, 6)
                elif splitLine[0] == "parameter":
                    paramName = line.split("=")[0].split()[-1].strip()
                    paramValue = line.split("=")[1].split()[0].strip()
                    try:
                        paramAttr = line.split("(*")[1]
                    except IndexError:
                        paramAttr = ""
                    if "type" in paramAttr and '"instance"' in paramAttr:
                        # parameter value is between = and (*
                        self.instanceParams[paramName] = paramValue
                        if "xyceAlsoModel" in paramAttr and '"yes"' in paramAttr:
                            self.modelParams[paramName] = paramValue
                    else:  # no parameter attribute statement
                        self.modelParams[paramName] = paramValue

    @staticmethod
    def extractPin(line, start: int):
        return [pin.strip().strip(";") for pin in line[start:].split(",")]
