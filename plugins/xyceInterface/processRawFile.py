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

import numpy as np
import polars as pl

columnTag = namedtuple("columnTag", ["order", "name", "type"])
dataFrameTuple = namedtuple("dataFrameTuple", ["header", "dataFrame", "columnTag"])


class rawDataObj:
    def __init__(self, filepath: pathlib.Path):
        self.filepath = filepath
        self.sections = []
        self._read_file()

    def _read_file(self):
        with self.filepath.open("rb") as f:
            content = f.read()
        splitSections = content.split(b"Plotname:")

        if len(splitSections) > 1:
            self.sections = []
            for i, section_bytes in enumerate(splitSections[1:]):
                # Find the binary marker in bytes
                binary_marker = b"Binary:"
                binary_pos = section_bytes.find(binary_marker) + len(binary_marker)

                # Skip any whitespace after "Binary:" marker
                while (
                    binary_pos < len(section_bytes)
                    and section_bytes[binary_pos] in b"\r\n\t "
                ):
                    binary_pos += 1

                # Extract header and binary data
                header_text = "Plotname:" + section_bytes[:binary_pos].decode(
                    "utf-8", errors="replace"
                )
                binary_data = section_bytes[binary_pos:]

                self.sections.append(
                    {"header": header_text, "binary_data": binary_data}
                )

    def get_dataframes(self) -> list:
        """Parse all sections and return a list of polars dataframes."""
        dataframes = []

        for section in self.sections:
            header_dict = self._parse_header(section["header"])
            dataFrame = self._parseBinaryData(section["binary_data"], header_dict)
            if dataFrame is not None:
                dataframes.append(
                    dataFrameTuple(
                        header_dict.get("Plotname", ""),
                        dataFrame,
                        header_dict.get("Variables"),
                    )
                )

        return dataframes

    def _parse_header(self, headerText):
        """Parse the header text into a dictionary."""
        header_lines = headerText.splitlines()
        header_dict = {}
        variables = []
        in_variables_section = False

        for line in header_lines:
            line = line.strip()
            if not line:
                continue

            if line == "Variables:":
                in_variables_section = True
                continue

            if in_variables_section:
                # Check if we've exited the Variables section
                if ":" in line and not line[0].isdigit():
                    in_variables_section = False
                else:
                    # Parse variable line
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            order = int(parts[0])
                            name = parts[1]
                            var_type = parts[2]
                            variables.append(columnTag(order, name, var_type))
                        except (ValueError, IndexError):
                            pass
                    continue

            # Process regular header lines with key:value format
            if ":" in line:
                key_value = line.split(":", 1)
                if len(key_value) == 2:
                    key = key_value[0].strip()
                    value = key_value[1].strip()
                    header_dict[key] = value

        # Add variables to the dictionary if any were found
        if variables:
            header_dict["Variables"] = variables

        return header_dict

    def _parseBinaryData(self, binary_data, header_dict) -> pl.DataFrame:
        """Parse binary data into a polars DataFrame."""
        try:
            noVariables = int(header_dict.get("No. Variables", 0))
            noPoints = int(header_dict.get("No. Points", 0))
        except ValueError:
            print("Error: 'No. Variables' or 'No. Points' is not a valid integer.")
            return None

        if not noVariables or not noPoints:
            return None

        variables = header_dict.get("Variables", [])
        if not variables:
            return None

        # Extract column names from variables
        column_names = [var.name for var in variables]

        if header_dict["Flags"] == "complex":
            # Complex data: each point is 2 doubles (real and imaginary parts)
            data = np.frombuffer(binary_data, dtype=np.float64).reshape(
                noPoints, noVariables * 2
            )

            # Create a dictionary for the DataFrame
            data_dict = {}
            for i, name in enumerate(column_names):
                data_dict[f"{name}_real"] = data[:, i * 2]  # Real part
                data_dict[f"{name}_imag"] = data[:, i * 2 + 1]  # Imaginary part

            # Create polars DataFrame
            dataFrame = pl.DataFrame(data_dict)
        else:
            # Real data: each point is 1 double
            binaryData = np.frombuffer(binary_data, dtype=np.float64)
            data = binaryData.reshape(noPoints, noVariables)

            # Create a dictionary for the DataFrame
            data_dict = {}
            for i, name in enumerate(column_names):
                data_dict[name] = data[:, i]

            # Create polars DataFrame
            dataFrame = pl.DataFrame(data_dict)

        return dataFrame

    @property
    def dataFrames(self) -> list[dataFrameTuple]:
        return self.get_dataframes()

    @property
    def titles(self):
        titlesList = []
        for section in self.sections:
            header_dict = self._parse_header(section["header"])
            titlesList.append(header_dict.get("Plotname", ""))
        return titlesList


if __name__ == "__main__":
    from platform import system

    if system() == "Linux":
        filepath = pathlib.Path(
            "/home/eskiyerli/onedrive_reveda/Projects/testbenches/commonSourceAmp/revbench/commonSourceAmp_ac.raw"
        )
    elif system() == "Windows":
        # filepath = pathlib.Path(
        #     "C:\\Users\\eskiye50\\OneDrive - Revolution "
        #     "Semiconductor\\Projects\\testbenches\\commonSourceAmp\\revbench"
        #     "\\commonSourceAmp_tran.raw"
        # )
        filepath = pathlib.Path(
            "C:\\Users\\eskiye50\\OneDrive - Revolution "
            "Semiconductor\\Projects\\testbenches\\commonSourceAmp\\revbench_win"
            "\\commonSourceAmp_ac.raw"
        )

    reader = rawDataObj(filepath)
    dataframes = reader.get_dataframes()
    print(reader.titles)
    for i, df in enumerate(dataframes):
        print(f"DataFrame {i + 1}:")
        print(f"header: {df.header}")

        print(f"columnTag: {df.columnTag}")
        print(f"Shape: {df.dataFrame.shape}")
        # print(f'time column index: {df.dataFrame.columns.index('frequency')}')
        # print(f"Columns: {df.dataFrame[:,0]}")
        # print(df.dataFrame.head(10))
        print("\n")
