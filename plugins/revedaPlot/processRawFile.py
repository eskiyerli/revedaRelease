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
import re

import numpy as np
import polars as pl

try:
    from .dataDefinitions import dataFrameTuple, columnTag
except ImportError:
    from dataDefinitions import dataFrameTuple, columnTag


class RawDataObj:
    def __init__(self, filepath: pathlib.Path):
        self.filepath = filepath
        self.sections = []
        self._read_file()

    @staticmethod
    def _rename_complex_column(col_name: str) -> str:
        """Rename columns according to the specified pattern."""
        if "frequency" in col_name.lower():
            return 'FREQ'
        if col_name.endswith("#branch_real"):
            return f"Re(I({col_name[:-13]}))"
        if col_name.endswith("#branch_imag"):
            return f"Im(I({col_name[:-13]}))"
        if col_name.endswith("_real"):
            return f"Re(V({col_name[:-5]}))"
        if col_name.endswith("_imag"):
            return f"Im(V({col_name[:-5]}))"
        return col_name

    @staticmethod
    def _rename_simple_column(col_name:str)-> str:

        if col_name.endswith('#branch'):
            return f'I({col_name[:-7]})'
        else:
            return f'V({col_name})'

    
    # Compile regex patterns once at class level
    _STEP_PATTERN = re.compile(r'Step (\d+)')
    _PARAM_PATTERN = re.compile(r'name\s*=\s*(\w+)\s+value\s*=\s*([\d\.]+)')
    _DESC_PATTERN = re.compile(r'value\s*=\s*[\d\.]+\s+(.+?)$')
    
    @classmethod
    def parse_step_header(cls, header_str):
        """Convert step analysis header to simplified format."""
        step_match = cls._STEP_PATTERN.search(header_str)
        step_num = step_match.group(1) if step_match else "1"
        
        param_match = cls._PARAM_PATTERN.search(header_str)
        desc_match = cls._DESC_PATTERN.search(header_str)
        
        result = f"Step Analysis: STEP={step_num}"
        if param_match:
            result += f", {param_match.group(1)}={param_match.group(2)}"
        if desc_match:
            result += f" - {desc_match.group(1).strip()}"
        
        return result

    def _read_file(self):
        with self.filepath.open("rb") as f:
            content = f.read()
        
        sections = content.split(b"Plotname:")[1:]  # Skip first empty section
        if not sections:
            return
            
        self.sections = []
        binary_marker = b"Binary:"
        whitespace = b"\r\n\t "
        
        for section_bytes in sections:
            binary_pos = section_bytes.find(binary_marker)
            if binary_pos == -1:
                continue
            binary_pos += len(binary_marker)
            
            # Skip whitespace more efficiently
            while binary_pos < len(section_bytes) and section_bytes[binary_pos:binary_pos+1] in whitespace:
                binary_pos += 1
            
            header_text = "Plotname:" + section_bytes[:binary_pos - len(binary_marker)].decode("utf-8", errors="replace")
            self.sections.append({"header": header_text, "binary_data": section_bytes[binary_pos:]})

    def getDataFrames(self) -> list[dataFrameTuple]:
        """Parse all sections and return a list of polars dataframes."""
        dataframes = []

        for section in self.sections:
            header_dict = self._parse_header(section["header"])
            print(header_dict)
            dataFrame = self._parseBinaryData(section["binary_data"], header_dict)
            if dataFrame is not None:
                plotname = header_dict.get("Plotname", "")
                # Parse step header if it contains step analysis info
                if "Step Analysis" in plotname:
                    plotname = self.parse_step_header(plotname)
                dataframes.append(dataFrameTuple(plotname, dataFrame))

        return dataframes

    def _parse_header(self, headerText):
        """Parse the header text into a dictionary."""
        lines = [line.strip() for line in headerText.splitlines() if line.strip()]
        header_dict = {}
        variables = []
        in_variables = False

        for line in lines:
            if line == "Variables:":
                in_variables = True
                continue

            if in_variables:
                if ":" in line and not line[0].isdigit():
                    in_variables = False
                else:
                    parts = line.split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        variables.append(parts[1])
                    continue

            if ":" in line:
                key, value = line.split(":", 1)
                header_dict[key.strip()] = value.strip()

        if variables:
            header_dict["Variables"] = variables
        return header_dict

    def _parseBinaryData(self, binary_data, header_dict) -> pl.DataFrame:
        """Parse binary data into a polars DataFrame."""
        try:
            noVariables = int(header_dict.get("No. Variables", 0))
            noPoints = int(header_dict.get("No. Points", 0))
            variables = header_dict.get("Variables", [])
        except (ValueError, TypeError):
            return None

        if not (noVariables and noPoints and variables):
            return None
        data = np.frombuffer(binary_data, dtype=np.float64)
        if header_dict.get("Flags") == "complex":
            data = data.reshape(noPoints, noVariables * 2)
            data_dict = {}
            for i, name in enumerate(variables):
                if i != 0:
                    data_dict[self._rename_complex_column(f"{name}_real")] = data[:, i * 2]
                    data_dict[self._rename_complex_column(f"{name}_imag")] = data[:, i * 2 + 1]
                else:
                    data_dict[self._rename_complex_column(name)] = data[:,i*2]
        else:
            data = data.reshape(noPoints, noVariables)
            data_dict = {name if i == 0 else self._rename_simple_column(name): data[:, i] 
                        for i, name in enumerate(variables)}

        return pl.DataFrame(data_dict)


    @property
    def dataFrames(self) -> list[dataFrameTuple]:
        return self.getDataFrames()


if __name__ == "__main__":
    from platform import system

    if system() == "Linux":
        # filepath = pathlib.Path(
        #     "/home/eskiyerli/onedrive_reveda/Projects/testbenches/commonSourceAmp/commonSourceAmp_ac.raw")
        filepath = pathlib.Path(
            "/home/eskiyerli/onedrive_reveda/Projects/testbenches/commonSourceAmp"
            "/commonSourceAmp_dc.raw")
        # filepath = pathlib.Path(
        #     "/home/eskiyerli/onedrive_reveda/Projects/testbenches/commonSourceAmp"
        #     "/commonSourceAmp_tran.raw")
    elif system() == "Windows":
        # filepath = pathlib.Path(
        #     "C:\\Users\\eskiye50\\OneDrive - Revolution "
        #     "Semiconductor\\Projects\\testbenches\\commonSourceAmp\\revbench"
        #     "\\commonSourceAmp_tran.raw"
        # )
        filepath = pathlib.Path("C:\\Users\\eskiye50\\OneDrive - Revolution "
                                "Semiconductor\\Projects\\testbenches\\commonSourceAmp\\revbench_win"
                                "\\commonSourceAmp_ac.raw")

    reader = RawDataObj(filepath)
    dataframes = reader.getDataFrames()
    for i, df in enumerate(dataframes):
        print(f"DataFrame {i + 1}:")
        print(f"header: {df.header}")
        print(f"Columns: {df.dataFrame.columns}")
        # print(f'time column index: {df.dataFrame.columns.index('FREQ')}')
        # print(f"Columns: {df.dataFrame[:,0]}")
        print(df.dataFrame.tail(2))
        print("\n")
