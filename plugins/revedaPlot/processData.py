import numpy as np
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# from engineering_notation import EngNumber


class processPrnFile:
    """
    reads the text prn file and loads it into a numpy data array.
    Then splits it according to splitColumn and splitValue.
    """
    def __init__(self, outputPath, splitColumn=0, splitValue=0):
        if not outputPath.exists():
            self.arrayList = self.outputTags = None
            return

        # Use 'r' instead of 'r+' since we're only reading
        with outputPath.open(mode='r') as f:
            # More efficient string splitting
            header = next(f)
            self.outputTags = header.split()[1:]
            tagLength = len(self.outputTags)

            if tagLength == 0:
                self.arrayList = self.outputTags = None
                return

            # Use numpy's loadtxt for more efficient loading
            try:
                # Skip the header (skiprows=1) and load directly into 2D array
                data_array = np.loadtxt(f, dtype=float)
            except ValueError as e:
                self.arrayList = self.outputTags = None
                return

            # Find split points more efficiently
            split_mask = (data_array[:, splitColumn] == splitValue)
            splitRowsList = np.nonzero(split_mask)[0][1:]
            self.numArrays = len(splitRowsList)

            # Remove the index column (column 0)
            data_array = data_array[:, 1:]

            # Create array list based on split points
            self.arrayList = (
                [data_array] if self.numArrays == 0
                else np.split(data_array, splitRowsList, axis=0)
            )

    # def __init__(self, outputPath, splitColumn=0, splitValue=0):
    #     if outputPath.exists():
    #         with outputPath.open(mode="r+") as f:
    #             # read and split first line of the output file, i.e. the column headers
    #             self.outputTags = f.readline().split()[1:]  # creates a list
    #             tagLength = len(self.outputTags)  # number of columns
    #
    #         if tagLength != 0:
    #             dataArray = np.loadtxt(outputPath, skiprows=1)
    #             # dataArray = np.genfromtxt(outputPath, skip_header=1)
    #             splitRowsList = np.nonzero(dataArray[:, splitColumn] == splitValue)[0][1:]
    #             self.numArrays = len(splitRowsList)
    #             # check if there are more than one array. Remove index column to save memory.
    #             if self.numArrays == 0:
    #                 self.arrayList = [np.array(dataArray[:, 1:])]  # a list of a single array
    #             else:
    #                 self.arrayList = np.split(dataArray[:, 1:], splitRowsList, axis=0)
    #     else:
    #         self.arrayList = None  #
    #         self.outputTags = None


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
#
#
# class readLabelsSkipFirstSweep:
#     """
#     Read sweep data (*.prn) file and creates a list of sweep value tags. Skip first column.
#     """
#
#     def __init__(self, outputPath) -> None:
#         if outputPath.exists():
#             with outputPath.open(mode="r+") as f:
#                 # read and split first line of the output file, i.e. the column headers
#                 self.outputTags = f.readline().split()[1:]
#                 tagLength = len(self.outputTags)  # number of columns
#                 reshapedArray = np.loadtxt(outputPath, skiprows=1,comments='End')[:,1:]
#             if tagLength == 1:  # there is only one sweep
#                 self.labelList = self.outputTags[0] # only one tag
#                 self.innerSweepSize = reshapedArray.shape[0]
#                 self.innerSweepValues = reshapedArray[:, 0]
#                 self.outerSweepValues = []
#             elif tagLength == 2:  # two sweeps
#                 # innersweepRows is true whenever the first value is repeated.
#                 innerSweepRows = np.nonzero(reshapedArray[:, 0] == reshapedArray[0, 0])
#                 self.innerSweepSize = innerSweepRows[0][1] - innerSweepRows[0][0]
#                 self.innerSweepValues = reshapedArray[0 : innerSweepRows[0][1], 0]
#                 self.outerSweepSize = int(reshapedArray.shape[0] / self.innerSweepSize)
#                 self.outerSweepValues = [
#                     reshapedArray[i * self.innerSweepSize, 1]
#                     for i in range(int(reshapedArray.shape[0] / self.innerSweepSize))
#                 ]
#                 self.labelList = []
#                 for i in range(int(reshapedArray.shape[0] / self.innerSweepSize)):  # iterate over rows
#                     labelString = ""
#                     for j in range(reshapedArray.shape[1] - 1):
#                         labelString += (
#                             self.outputTags[j + 1]
#                             + "="
#                             + str(reshapedArray[i * self.innerSweepSize, j + 1])
#                             + ", "
#                         )
#                     self.labelList.append(labelString[:-2])
#             elif tagLength > 2:
#                 innerSweepRows = np.nonzero(reshapedArray[:, 0] == reshapedArray[0, 0])
#                 self.innerSweepSize = innerSweepRows[0][1] - innerSweepRows[0][0]
#                 self.innerSweepValues = reshapedArray[0 : innerSweepRows[0][1], 0]
#                 self.outerSweepValues = [
#                     reshapedArray[i * self.innerSweepSize, 1]
#                     for i in range(int(reshapedArray.shape[0] / self.innerSweepSize))
#                 ]
#                 outerSweepStarts = np.nonzero(self.outerSweepValues[:] == self.outerSweepValues[0])[0]
#                 self.outerSweepSize = outerSweepStarts[1] - outerSweepStarts[0]
#                 self.labelList = []
#                 for i in range(int(reshapedArray.shape[0] / self.innerSweepSize)):  # iterate over rows
#                     labelString = ""
#                     for j in range(reshapedArray.shape[1] - 1):
#                         labelString += (
#                             self.outputTags[j + 1]
#                             + "="
#                             + str(reshapedArray[i * self.innerSweepSize, j + 1])
#                             + ", "
#                         )
#                     self.labelList.append(labelString[:-2])
#                 self.outerLabelList = []
#                 for i in range(
#                     int(reshapedArray.shape[0] / (self.innerSweepSize * self.outerSweepSize))
#                 ):  # iterate over rows
#                     labelString = ""
#                     for j in range(2, reshapedArray.shape[1]):
#                         labelString += (
#                             self.outputTags[j]
#                             + "="
#                             + str(reshapedArray[i * self.innerSweepSize * self.outerSweepSize, j])
#                             + ", "
#                         )
#                     self.outerLabelList.append(labelString[:-2])
#         else:
#             self.labelList = []
#             self.innerSweepSize = 1
#             self.outerSweepValues = None


@dataclass
class SweepData:
    """Data structure to hold sweep information"""
    inner_sweep_size: int
    inner_sweep_values: np.ndarray
    outer_sweep_values: List
    label_list: List[str]
    outer_label_list: Optional[List[str]] = None

class ReadLabelsSkipFirstSweep:
    """Read sweep data (*.prn) file and creates a list of sweep value tags. Skip first column."""

    def __init__(self, output_path: Path) -> None:
        if not output_path.exists():
            self._initialize_empty()
            return

        try:
            # Read header and data more efficiently
            with output_path.open('r') as f:
                self.output_tags = next(f).split()[1:]
                tag_length = len(self.output_tags)

            # Load data all at once, skipping first column
            data = np.loadtxt(output_path, skiprows=1, comments='End')[:, 1:]

            # Process data based on tag length
            self._process_data(data, tag_length)

        except (IOError, ValueError) as e:
            print(f"Error processing file: {e}")
            self._initialize_empty()

    def _initialize_empty(self) -> None:
        """Initialize empty attributes"""
        self.label_list = []
        self.inner_sweep_size = 1
        self.outer_sweep_values = None
        self.output_tags = None
        self.inner_sweep_values = None
        self.outer_label_list = None

    def _create_label_string(self, data_row: np.ndarray, tags: List[str], start_idx: int = 1) -> str:
        """Create label string from data row and tags"""
        return ", ".join(f"{tag}={val}" for tag, val in zip(tags[start_idx:], data_row[start_idx:]))

    def _process_single_sweep(self, data: np.ndarray) -> None:
        """Process single sweep data"""
        self.label_list = self.output_tags[0]
        self.inner_sweep_size = data.shape[0]
        self.inner_sweep_values = data[:, 0]
        self.outer_sweep_values = []

    def _process_multi_sweep(self, data: np.ndarray) -> None:
        """Process multi-sweep data"""
        # Find inner sweep boundaries
        inner_sweep_rows = np.nonzero(data[:, 0] == data[0, 0])[0]
        self.inner_sweep_size = inner_sweep_rows[1] - inner_sweep_rows[0]
        self.inner_sweep_values = data[:self.inner_sweep_size, 0]

        # Calculate outer sweep values
        rows_per_inner = self.inner_sweep_size
        self.outer_sweep_values = data[::rows_per_inner, 1]

        # Create label lists efficiently
        num_outer_sweeps = len(data) // rows_per_inner
        self.label_list = [
            self._create_label_string(data[i * rows_per_inner], self.output_tags)
            for i in range(num_outer_sweeps)
        ]

    def _process_triple_sweep(self, data: np.ndarray) -> None:
        """Process triple sweep data"""
        self._process_multi_sweep(data)

        # Find outer sweep size
        outer_sweep_starts = np.nonzero(self.outer_sweep_values == self.outer_sweep_values[0])[0]
        self.outer_sweep_size = outer_sweep_starts[1] - outer_sweep_starts[0]

        # Create outer label list
        rows_per_outer = self.inner_sweep_size * self.outer_sweep_size
        num_outer_labels = len(data) // rows_per_outer
        self.outer_label_list = [
            self._create_label_string(data[i * rows_per_outer], self.output_tags, start_idx=2)
            for i in range(num_outer_labels)
        ]

    def _process_data(self, data: np.ndarray, tag_length: int) -> None:
        """Process data based on tag length"""
        if tag_length == 1:
            self._process_single_sweep(data)
        elif tag_length == 2:
            self._process_multi_sweep(data)
        elif tag_length > 2:
            self._process_triple_sweep(data)
