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

import polars as pl

try:
    from .dataDefinitions import dataFrameTuple, columnTag
except ImportError:
    from dataDefinitions import dataFrameTuple, columnTag


class AsciiDataObj:
    def __init__(self, prn_path: pathlib.Path):
        self.prn_path = prn_path
        self._respath = None
        self._resList = []
        self._read_files()

    def _read_files(self):
        """Read and parse both PRN and RES files."""
        if not self.prn_path.exists():
            raise FileNotFoundError(f"PRN file {self.prn_path} does not exist.")

        # Build RES file path by removing last 2 suffixes
        tempPath = self.prn_path
        analysisType= str(tempPath.name).split('.')[0].split('_')[1]
        outputDir = tempPath.parent
        # Search for files matching the criteria
        respath = next(
            (f for f in outputDir.iterdir()
             if f.is_file() and analysisType in f.name and f.suffix == '.res'),
            None
        )
        if isinstance(respath, pathlib.Path) and respath.exists():
            self._respath = respath
            self._resList = self.readResFile(respath)

    @staticmethod
    def getHeader(filePath: pathlib.Path):
        suffixes = filePath.suffixes
        stem = filePath.stem.lower()

        if 'ac' in stem:
            return "AC Analysis"
        elif 'hb' in stem:
            return 'HB FD Analysis' if '.FD' in suffixes else 'HB TD Analysis' if '.TD' in suffixes else 'HB Analysis'
        elif 'noise' in stem:
            return "Noise Analysis"
        elif 'tran' in stem:
            return "Transient Analysis"
        elif 'dc' in stem:
            return "DC Analysis"
        return "Analysis"

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

    @staticmethod
    def _rename_column(col_name: str) -> str:
        """Rename columns according to the specified pattern."""
        if "frequency_real" in col_name.lower():
            return 'FREQ'
        if "frequency_imag" in col_name.lower():
            return "FREQ_IM"
        if col_name.endswith("#branch_real"):
            return f"Re(I({col_name[:-13]}))"
        if col_name.endswith("#branch_imag"):
            return f"Im(I({col_name[:-13]}))"
        if col_name.endswith("_real"):
            return f"Re(V({col_name[:-5]}))"
        if col_name.endswith("_imag"):
            return f"Im(V({col_name[:-5]}))"
        return col_name

    # Compile regex patterns once at class level
    _ANALYSIS_PATTERN = re.compile(r'(\w+\s+Analysis)(?!.*Analysis)')
    _STEP_PATTERN = re.compile(r'Step (\d+)')
    _PARAM_PATTERN = re.compile(r'name\s*=\s*(\w+)\s+value\s*=\s*([\d\.]+)')

    @classmethod
    def parse_step_header(cls, header_str):
        """Convert step analysis header to simplified format."""
        analysis_match = cls._ANALYSIS_PATTERN.search(header_str)
        analysis_type = analysis_match.group(1) if analysis_match else "Analysis"

        step_match = cls._STEP_PATTERN.search(header_str)
        step_num = step_match.group(1) if step_match else "1"

        param_match = cls._PARAM_PATTERN.search(header_str)
        if param_match:
            return f"{analysis_type}: STEP={step_num}, {param_match.group(1)}={param_match.group(2)}"
        return f"{analysis_type}: STEP={step_num}"

    def getDataFrames(self) -> list[dataFrameTuple]:
        """Read the PRN file and extract header and data, handling multiple sections."""
        try:
            with self.prn_path.open('r') as prnFile:
                columnNames = prnFile.readline().strip().split()[1:]  # Skip index column

                data_sections = []
                current_section = []
                last_index = -1

                for line in prnFile:
                    if not (line := line.strip()) or line.startswith("#"):
                        continue

                    try:
                        values = line.split()
                        current_index = int(float(values[0]))

                        # Start new section if index resets to 0
                        if current_index == 0 and last_index > 0 and current_section:
                            data_sections.append(current_section)
                            current_section = []

                        current_section.append(values[1:])
                        last_index = current_index
                    except (ValueError, IndexError):
                        continue

                if current_section:
                    data_sections.append(current_section)

            # Create DataFrames
            base_header = self.getHeader(self.prn_path)
            schema = {col: pl.Float64 for col in columnNames}

            return [
                dataFrameTuple(
                    f"{base_header}: {', '.join(f'{k}={v}' for k, v in self._resList[i].items())}"
                    if self._resList and i < len(self._resList) else base_header,
                    pl.DataFrame(section, schema=schema, orient="row")
                )
                for i, section in enumerate(data_sections)
            ]

        except Exception as e:
            raise RuntimeError(f"Error reading PRN file: {e}")

    def readResFile(self, respath: pathlib.Path):
        """Read the RES file for additional metadata."""
        try:
            with respath.open("r") as res_file:
                keys = res_file.readline().strip().split()
                return [
                    dict(zip(keys, values))
                    for raw_line in res_file
                    if (stripped := raw_line.strip()) and not stripped.startswith("#")
                    and len(values := stripped.split()) == len(keys)
                ]
        except Exception as e:
            print(f"Warning: Could not read RES file: {e}")
            return []

    @property
    def dataFrames(self) -> list[dataFrameTuple]:
        return self.getDataFrames()


def main():
    # Example usage
    from platform import system

    if system() == "Linux":
        filePath = pathlib.Path("/home/eskiyerli/onedrive_reveda/Projects/testbenches"
                                "/commonSourceAmp/commonSourceAmp_ac.sp.FD.prn")
        # filePath = pathlib.Path("/home/eskiyerli/onedrive_reveda/Projects/testbenches"
        #                         "/commonSourceAmp/commonSourceAmp_tran.sp.prn")
        # filePath = pathlib.Path("/home/eskiyerli/onedrive_reveda/Projects/testbenches"
        #                         "/commonSourceAmp/commonSourceAmp_hb.sp.HB.FD.prn")
        # filePath = pathlib.Path("/home/eskiyerli/onedrive_reveda/Projects/testbenches"
        #                         "/commonSourceAmp/commonSourceAmp_dc.sp.prn")
    else:
        # filePath = pathlib.Path(
        #     "C:/Users/eskiye50/OneDrive - Revolution Semiconductor/Projects/testbenches/"
        #     "commonSourceAmp/revbench_win/commonSourceAmp_hb.sp.HB.FD.prn")
        filePath = pathlib.Path("C:/Users/eskiye50/OneDrive - Revolution Semiconductor/Projects/testbenches/"
            "commonSourceAmp/commonSourceAmp_ac.sp.FD.prn")
        # filePath = pathlib.Path("C:/Users/eskiye50/OneDrive - Revolution Semiconductor/Projects/testbenches/"
        #     "commonSourceAmp/commonSourceAmp_tran.sp.prn")
        # filePath = pathlib.Path("C:/Users/eskiye50/OneDrive - Revolution Semiconductor/Projects/testbenches/"
        #     "commonSourceAmp/commonSourceAmp_hb.sp.HB.FD.prn")
        # filePath = pathlib.Path("C:/Users/eskiye50/OneDrive - Revolution Semiconductor/Projects/testbenches/"
        #     "commonSourceAmp/commonSourceAmp_dc.sp.prn")
    dataObj = AsciiDataObj(filePath)
    dataFrames = dataObj.getDataFrames()

    for i, df in enumerate(dataFrames):
        print(f"DataFrame {i + 1}:")
        print(f"header: {df.header}")

        print(f"Columns: {df.dataFrame.columns}")
        # print(f'time column index: {df.dataFrame.columns.index('FREQ')}')
        # print(f"Columns: {df.dataFrame[:,0]}")
        # print(df.dataFrame.head(10))
        print("\n")

if __name__ == "__main__":
    main()
