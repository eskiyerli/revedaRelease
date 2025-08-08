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

"""
Output prefix handler for processing mathematical operations on dataframe columns.
Handles prefixes like db(), ph(), mag() for decibel, phase, and magnitude calculations.
"""

from typing import Union, Tuple, Optional

import numpy as np
import polars as pl

from plugins.revedaPlot.dataDefinitions import dataFrameTuple

# Cache for processed columns to avoid redundant calculations
_processed_columns_cache = {}
AC_PREFIXES = ['db', 'mag', 'ph', 'ph_deg']
SCALAR_PREFIXES = ['max', 'min', 'ave']
VALUE_PREFIXES = ['yvalue', 'xvalue']
SIGNAL_OPERATIONS = AC_PREFIXES + SCALAR_PREFIXES + VALUE_PREFIXES

def processOutputSignals(dft: dataFrameTuple, outputSignals: set[str]) -> (Union)[
    pl.DataFrame, float]:
    tempDataFrame = dft.dataFrame
    returnValue: float = 0.0
    for outputSig in outputSignals:
        prefix, base = parseOutputExpression(outputSig)
        if prefix in AC_PREFIXES and ('AC' or 'HB FD') in dft.header:
            match prefix:
                case 'db':
                    tempDataFrame = tempDataFrame.with_columns(
                        (20 * ((pl.col(f'Re({base})') ** 2 + pl.col(f'Im({base})') ** 2)).sqrt().log10()).alias(f'db({base})'))
                case 'mag':
                    tempDataFrame = tempDataFrame.with_columns(
                        ((pl.col(f'Re({base})') ** 2 + pl.col(f'Im({base})') ** 2)).sqrt().alias(f'mag({base})'))
                case 'ph':
                    tempDataFrame = tempDataFrame.with_columns(
                        pl.arctan2(pl.col(f'Im({base})'), pl.col(f'Re({base})')).alias(f'ph({base})'))
                case 'ph_deg':
                    tempDataFrame = tempDataFrame.with_columns(
                        (pl.arctan2(pl.col(f'Im({base})'), pl.col(f'Re({base})')) * 180 / np.pi).alias(f'ph_deg({base})'))
            return dft._replace(dataFrame=tempDataFrame)
        elif (prefix in SCALAR_PREFIXES and ('TRAN' or 'DC' or 'HB TD') in
              dft.header):
            match prefix:
                case 'max':
                    returnValue = tempDataFrame.select(pl.col(base).max()).item()
                case 'min':
                    returnValue = tempDataFrame.select(pl.col(base).min()).item()
                case 'ave':
                    returnValue = tempDataFrame.select(pl.col(base).mean()).item()
            return returnValue

def parseOutputExpression(output: str) -> Tuple[Optional[str], str]:
    """
    Parse an output expression to extract prefix and base signal name.

    Args:
        output (str): Output expression like "db(V(OUT))" or "V(OUT)"

    Returns:
        Tuple[Optional[str], str]: (prefix, base_signal_name)

    Examples:
        "db(V(OUT))" -> ("db", "V(OUT)")
        "ph(I(M1))" -> ("ph", "I(M1)")
        "V(OUT)" -> (None, "V(OUT)")
    """
    output = output.strip()
    # Check for prefix pattern: prefix(signal)
    for prefix in SIGNAL_OPERATIONS:
        prefix_pattern = f"{prefix}("
        if output.startswith(prefix_pattern) and output.endswith("))"):
            # Extract the inner expression
            inner_expression = output[len(prefix_pattern):-1]
            return prefix, inner_expression

    # No prefix found
    return "", output


def main():
    # Example usage
    from platform import system
    from plugins.revedaPlot.processAsciFile import AsciiDataObj
    import pathlib
    
    # Get the path of this file
    testsPath = pathlib.Path(__file__).resolve().parent.joinpath('tests')
    print(f"Current file path: {testsPath}")

    filePath = testsPath.joinpath("commonSourceAmp_ac.sp.FD.prn")
    dataObj = AsciiDataObj(filePath)
    dfts = dataObj.getDataFrames()

    for i, df in enumerate(dfts):
        print(f"DataFrame {i + 1}:")
        print(f"header: {df.header}")
        print(f'Columns: {df.dataFrame.columns}')
        # returnValue = processOutputSignals(df, {"ph(V(OUT))"})
        # if isinstance(returnValue,dataFrameTuple):
        #     print(returnValue.dataFrame.head(10))
        returnValue = processOutputSignals(df,{"max(V(OUT))"})
        if isinstance(returnValue, float):
            print(returnValue)
        print("\n")

if __name__ == "__main__":
    main()
