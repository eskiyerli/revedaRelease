import numpy as np
# from engineering_notation import EngNumber


class readPlotDataCold:
    """
    reads the text prn file and loads it into a numpy data array.
    Then splits it according to splitColumn and splitValue.
    """

    def __init__(self, outputPath, splitColumn=0, splitValue=0):
        if outputPath.exists():
            with outputPath.open(mode="r+") as f:
                # read and split first line of the output file, i.e. the column headers
                self.outputTags = f.readline().split()[1:]  # creates a list
                tagLength = len(self.outputTags)  # number of columns

                if tagLength != 0:
                    data = f.read()  # read the rest
                    try:
                        loadedArray = np.fromstring(data, sep=" ")  # create a numpy array
                    except ValueError:
                        pass
                    # reshape 1-D array to 2-D array. taglength is increased by 1
                    # to account for removal of index tag.
                    reshapedArray = np.reshape(loadedArray, (-1, tagLength + 1))
                    del loadedArray  # delete loadedArray to save memory
                    # splitRowsList = np.where(
                    #     reshapedArray[:, splitColumn] == splitValue)[0][1:]
                    # split rows list start from second value
                    splitRowsList = np.nonzero(reshapedArray[:, splitColumn] == splitValue)[0][1:]
                    self.numArrays = len(splitRowsList)
                    # check if there are more than one array. Remove index column to save memory.
                    if self.numArrays == 0:
                        self.arrayList = [np.array(reshapedArray[:, 1:])]  # a list of a single array
                    else:
                        self.arrayList = np.split(reshapedArray[:, 1:], splitRowsList, axis=0)
        else:
            self.arrayList = None  #
            self.outputTags = None


class readPlotDataC:
    """
    reads the text prn file and loads it into a numpy data array.
    Then splits it according to splitColumn and splitValue.
    """

    def __init__(self, outputPath, splitColumn=0, splitValue=0):
        if outputPath.exists():
            with outputPath.open(mode="r+") as f:
                # read and split first line of the output file, i.e. the column headers
                self.outputTags = f.readline().split()[1:]  # creates a list
                tagLength = len(self.outputTags)  # number of columns

            if tagLength != 0:
                dataArray = np.loadtxt(outputPath, skiprows=1)
                # dataArray = np.genfromtxt(outputPath, skip_header=1)
                splitRowsList = np.nonzero(dataArray[:, splitColumn] == splitValue)[0][1:]
                self.numArrays = len(splitRowsList)
                # check if there are more than one array. Remove index column to save memory.
                if self.numArrays == 0:
                    self.arrayList = [np.array(dataArray[:, 1:])]  # a list of a single array
                else:
                    self.arrayList = np.split(dataArray[:, 1:], splitRowsList, axis=0)
        else:
            self.arrayList = None  #
            self.outputTags = None


class readSimpleSweepLabels:
    """
    Reads sweep data and creates a list of sweep value tags.
    """

    def __init__(self, outputPath) -> None:
        if outputPath.exists():
            with outputPath.open(mode="r+") as f:
                # read and split first line of the output file, i.e. the column headers
                outputTags = f.readline().split()[1:]
                # tagLength = len(outputTags)  # number of columns

            if outputTags != []:
                dataArray = np.loadtxt(outputPath, skiprows=1,comments='End')[:,1:]
                self.labelList = []
                for i in range(dataArray.shape[0]):  # iterate over rows
                    labelString = ""
                    for j in range(dataArray.shape[1]):
                        labelString += outputTags[j] + "=" + str(dataArray[i, j]) + ", "
                    self.labelList.append(labelString[:-2])
        else:
            self.labelList = [''] # empty string
            self.outputTags = [''] # empty string


class readLabelsSkipFirstSweep:
    """
    Read sweep data (*.prn) file and creates a list of sweep value tags. Skip first column.
    """

    def __init__(self, outputPath) -> None:
        if outputPath.exists():
            with outputPath.open(mode="r+") as f:
                # read and split first line of the output file, i.e. the column headers
                self.outputTags = f.readline().split()[1:]
                tagLength = len(self.outputTags)  # number of columns
                reshapedArray = np.loadtxt(outputPath, skiprows=1,comments='End')[:,1:]
            if tagLength == 1:  # there is only one sweep
                self.labelList = self.outputTags[0] # only one tag
                self.innerSweepSize = reshapedArray.shape[0]
                self.innerSweepValues = reshapedArray[:, 0]
                self.outerSweepValues = []
            elif tagLength == 2:  # two sweeps
                # innersweepRows is true whenever the first value is repeated.
                innerSweepRows = np.nonzero(reshapedArray[:, 0] == reshapedArray[0, 0])
                self.innerSweepSize = innerSweepRows[0][1] - innerSweepRows[0][0]
                self.innerSweepValues = reshapedArray[0 : innerSweepRows[0][1], 0]
                self.outerSweepSize = int(reshapedArray.shape[0] / self.innerSweepSize)
                self.outerSweepValues = [
                    reshapedArray[i * self.innerSweepSize, 1]
                    for i in range(int(reshapedArray.shape[0] / self.innerSweepSize))
                ]
                self.labelList = []
                for i in range(int(reshapedArray.shape[0] / self.innerSweepSize)):  # iterate over rows
                    labelString = ""
                    for j in range(reshapedArray.shape[1] - 1):
                        labelString += (
                            self.outputTags[j + 1]
                            + "="
                            + str(reshapedArray[i * self.innerSweepSize, j + 1])
                            + ", "
                        )
                    self.labelList.append(labelString[:-2])
            elif tagLength > 2:
                innerSweepRows = np.nonzero(reshapedArray[:, 0] == reshapedArray[0, 0])
                self.innerSweepSize = innerSweepRows[0][1] - innerSweepRows[0][0]
                self.innerSweepValues = reshapedArray[0 : innerSweepRows[0][1], 0]
                self.outerSweepValues = [
                    reshapedArray[i * self.innerSweepSize, 1]
                    for i in range(int(reshapedArray.shape[0] / self.innerSweepSize))
                ]
                outerSweepStarts = np.nonzero(self.outerSweepValues[:] == self.outerSweepValues[0])[0]
                self.outerSweepSize = outerSweepStarts[1] - outerSweepStarts[0]
                self.labelList = []
                for i in range(int(reshapedArray.shape[0] / self.innerSweepSize)):  # iterate over rows
                    labelString = ""
                    for j in range(reshapedArray.shape[1] - 1):
                        labelString += (
                            self.outputTags[j + 1]
                            + "="
                            + str(reshapedArray[i * self.innerSweepSize, j + 1])
                            + ", "
                        )
                    self.labelList.append(labelString[:-2])
                self.outerLabelList = []
                for i in range(
                    int(reshapedArray.shape[0] / (self.innerSweepSize * self.outerSweepSize))
                ):  # iterate over rows
                    labelString = ""
                    for j in range(2, reshapedArray.shape[1]):
                        labelString += (
                            self.outputTags[j]
                            + "="
                            + str(reshapedArray[i * self.innerSweepSize * self.outerSweepSize, j])
                            + ", "
                        )
                    self.outerLabelList.append(labelString[:-2])
        else:
            self.labelList = []
            self.innerSweepSize = 1
            self.outerSweepValues = None
