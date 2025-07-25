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

import pathlib
from collections import namedtuple
import polars as pl


columnTag = namedtuple("columnTag", ["order", "name", "type"])
dataFrameTuple = namedtuple("dataFrameTuple", ["header", "dataFrame", "columnTag"])


class AsciiDataObj:
    def __init__(self, prn_path: pathlib.Path):
        self.prn_path = prn_path
        self.titles = [""]
        self.dataFrame = None
        self.dataFrameTuple = None
        self._read_files()

    def _read_files(self):
        """Read and parse both PRN and RES files."""
        if not self.prn_path.exists():
            raise FileNotFoundError(f"PRN file {self.prn_path} does not exist.")

        # Read PRN file
        # self.get_dataframes()
        filenameParts = self.prn_path.name.split(".")[-2:-4:-1]
        respath = self.prn_path
        for part in filenameParts[-3:]:
            respath = respath.with_suffix("")
        else:
            respath = respath.with_suffix(".res")
        self._respath = respath if respath.exists() else None
        # Read RES file if it exists
        if self._respath and self._respath.exists():
            self._read_res_file(self._respath)

    @staticmethod
    def createColumnType(col):
        """Determine the column type based on the column name."""
        col_lower = col.lower()
        if col_lower == "time":
            return "time"
        elif "v(" in col_lower:
            return "voltage"
        elif "#branch" in col_lower:
            return "current"
        elif "freq" in col_lower:
            return "freq"
        else:
            return ""

    def get_dataframes(self):
        """Read the PRN file and extract header and data, handling multiple sections."""
        try:
            data_sections = []
            dataFrameTuples = []
            with open(self.prn_path, "r") as prn_file:
                # Read header line
                first_line = prn_file.readline().strip()
                header = first_line.split()[1:]  # Skip the first index column
                columnTags = [
                    columnTag(i, col, self.createColumnType(col))
                    for i, col in enumerate(header)
                ]
                current_section = []
                last_index = -1

                for line in prn_file:
                    line = line.strip()
                    if line and not line.startswith("#"):  # Skip comments
                        try:
                            values = line.split()

                            # Try to parse first value as number to detect data start
                            current_index = int(float(values[0]))

                            # If index resets to 0 and we already have data, start a new section
                            if (
                                current_index == 0
                                and last_index > 0
                                and current_section
                            ):
                                data_sections.append(current_section)
                                current_section = []

                            current_section.append(
                                values[1:]
                            )  # Store data excluding index
                            last_index = current_index
                        except (ValueError, IndexError):
                            # Not a data line, continue
                            continue

                # Add the last section if it has data
                if current_section:
                    data_sections.append(current_section)

            if data_sections:
                for section in data_sections:
                    # Convert each section to a polars DataFrame
                    df = pl.DataFrame(
                        section,
                        schema={col: pl.Float64 for col in header},
                        orient="row",
                    )
                    print(df)
                    dataFrameTuples.append(dataFrameTuple(header, df, columnTags))

        except Exception as e:
            raise RuntimeError(f"Error reading PRN file: {e}")
        finally:
            return dataFrameTuples

    def _read_res_file(self, respath: pathlib.Path):
        """Read the RES file for additional metadata."""
        try:
            valueslist = []
            with open(respath, "r") as res_file:
                # Process RES file content
                # This is typically metadata about the simulation
                keysline = res_file.readline().strip()
                keys = keysline.split()
                for line in res_file:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        valuesline = line.strip()
                        values = valuesline.split()
                        if len(keys) == len(values):
                            linedict = dict()
                            for key, value in zip(keys, values):
                                linedict[key] = value
                            valueslist.append(linedict)
            return valueslist

        except Exception as e:
            print(f"Warning: Could not read RES file: {e}")
            return []

    @property
    def dataFrames(self) -> list[dataFrameTuple]:
        return self.get_dataframes()


if __name__ == "__main__":
    # Example usage
    from platform import system

    if system() == "Linux":
        filePath = pathlib.Path(
            "/home/eskiyerli/onedrive_reveda/Projects/testbenches"
            "/commonSourceAmp/revbench_win/commonSourceAmp_hb.sp.HB.FD.prn"
        )
    else:
        filePath = pathlib.Path(
            "C:/Users/eskiye50/OneDrive - Revolution Semiconductor/Projects/testbenches/"
            "commonSourceAmp/revbench_win/commonSourceAmp_hb.sp.HB.FD.prn"
        )

    dataObj = AsciiDataObj(filePath)
    dataFrames = dataObj.get_dataframes()
    print(dataObj.titles)
    for i, df in enumerate(dataFrames):
        print(f"DataFrame {i + 1}:")
        print(f"header: {df.header}")

        print(f"columnTag: {df.columnTag}")
        print(f"Shape: {df.dataFrame.shape}")
        # print(f'time column index: {df.dataFrame.columns.index('FREQ')}')
        print(f"Columns: {df.dataFrame[:,0]}")
        print(df.dataFrame.head(10))
        print("\n")
