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

import numpy as np
import polars as pl
from typing import Tuple, Optional, Dict, Callable, Set
try:
    from .processAsciFile import dataFrameTuple
except ImportError:
    from processAsciFile import dataFrameTuple

# Cache for processed columns to avoid redundant calculations
_processed_columns_cache = {}

AC_OPERATIONS = ['db', 'mag', 'ph']

def parse_output_expression(output: str) -> Tuple[Optional[str], str]:
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
    for prefix in AC_OPERATIONS:
        prefix_pattern = f"{prefix}("
        if output.startswith(prefix_pattern) and output.endswith(")"):
            # Extract the inner expression
            inner_expression = output[len(prefix_pattern):-1]
            return prefix, inner_expression

    # No prefix found
    return None, output

def extrBaseColName(sigExpr: str) -> str:
    """
    Extract the base column name from a signal expression.

    Args:
        sigExpr (str): Signal expression like "V(OUT)" or "I(M1)"

    Returns:
        str: Base column name like "OUT" or "M1"
    """
    # Handle standard format like "V(OUT)" -> "OUT"
    if sigExpr.startswith(("V(", "I(")) and sigExpr.endswith(")"):
        return sigExpr[2:-1]

    # Handle other formats or return as-is
    return sigExpr

def compute_db(df: pl.DataFrame, baseColName: str) -> pl.DataFrame:
    """
    Compute decibel conversion: 20 * log10(magnitude).

    For complex signals, computes magnitude first, then converts to dB.
    For real signals, takes absolute value, then converts to dB.
    """
    dbColName = f"{baseColName}_db"

    # Check if we have complex data (real and imaginary parts)
    real_col = f"{baseColName}_real"
    imag_col = f"{baseColName}_imag"

    if real_col in df.columns and imag_col in df.columns:
        # Complex signal - compute magnitude first, then dB
        magnitude = (df[real_col] ** 2 + df[imag_col] ** 2).sqrt()
        # Use numpy log10 for better compatibility
        mag_vals = magnitude.to_numpy()
        mag_vals = np.maximum(mag_vals, 1e-12)  # Avoid log(0)
        db_values = 20 * np.log10(mag_vals)
    elif baseColName in df.columns:
        # Real signal - take absolute value, then dB
        magnitude = df[baseColName].abs()
        # Use numpy log10 for better compatibility
        mag_vals = magnitude.to_numpy()
        mag_vals = np.maximum(mag_vals, 1e-12)  # Avoid log(0)
        db_values = 20 * np.log10(mag_vals)
    else:
        raise ValueError(f"Column '{baseColName}' not found in dataframe")

    return df.with_columns(pl.Series(dbColName, db_values))

# def compute_phase(df: pl.DataFrame, base_col_name: str) -> pl.DataFrame:
#     """
#     Compute phase in degrees from complex signal.
#     """
#     processed_col_name = f"{base_col_name}_ph"
#
#     # Check if we have complex data (real and imaginary parts)
#     real_col = f"{base_col_name}_real"
#     imag_col = f"{base_col_name}_imag"
#
#     if real_col in df.columns and imag_col in df.columns:
#         # Complex signal - compute phase using arctan2
#         # Use numpy arctan2 since polars doesn't have built-in arctan2
#         real_vals = df[real_col].to_numpy()
#         imag_vals = df[imag_col].to_numpy()
#         phase_rad = np.arctan2(imag_vals, real_vals)
#         phase_deg = phase_rad * 180 / np.pi
#     else:
#         raise ValueError(f"Phase calculation requires complex data. "
#                        f"Columns '{real_col}' and '{imag_col}' not found in dataframe")
#
#     return df.with_columns(pl.Series(processed_col_name, phase_deg))
#
# def compute_magnitude(df: pl.DataFrame, base_col_name: str) -> pl.DataFrame:
#     """
#     Compute magnitude from complex signal.
#     """
#     processed_col_name = f"{base_col_name}_mag"
#
#     # Check if we have complex data (real and imaginary parts)
#     real_col = f"{base_col_name}_real"
#     imag_col = f"{base_col_name}_imag"
#
#     if real_col in df.columns and imag_col in df.columns:
#         # Complex signal - compute magnitude
#         magnitude = (df[real_col] ** 2 + df[imag_col] ** 2).sqrt()
#     elif base_col_name in df.columns:
#         # Real signal - magnitude is absolute value
#         magnitude = df[base_col_name].abs()
#     else:
#         raise ValueError(f"Column '{base_col_name}' not found in dataframe")
#
#     return df.with_columns(magnitude.alias(processed_col_name))
#
# # Map of prefix operations
# PREFIX_OPERATIONS = {
#     'db': compute_db,
#     'ph': compute_phase,
#     'mag': compute_magnitude,
# }
#
# def process_output(dft: dataFrameTuple, output: str) -> Tuple[dataFrameTuple, str]:
#     """
#     Process an output expression and apply any mathematical operations.
#
#     Args:
#         dft (dataFrameTuple): Data frame tuple containing the simulation data
#         output (str): Output expression to process
#
#     Returns:
#         Tuple[dataFrameTuple, str]: Updated dataframe tuple and the processed column name
#     """
#     global _processed_columns_cache
#
#     prefix, base_signal = parse_output_expression(output)
#     base_col_name = extract_base_column_name(base_signal)
#
#     if prefix is None:
#         # No prefix, return original column name
#         return dft, base_col_name
#
#     # Generate processed column name
#     processed_col_name = f"{base_col_name}_{prefix}"
#
#     # Check if already processed
#     cache_key = f"{prefix}_{base_col_name}"
#     if cache_key in _processed_columns_cache:
#         return dft, processed_col_name
#
#     # Apply the mathematical operation
#     if prefix in PREFIX_OPERATIONS:
#         try:
#             df = dft.dataFrame
#             operation = PREFIX_OPERATIONS[prefix]
#
#             # Apply the operation and add new column
#             new_df = operation(df, base_col_name)
#
#             # Update the dataframe tuple
#             updated_dft = dft._replace(dataFrame=new_df)
#
#             # Cache the result
#             _processed_columns_cache[cache_key] = processed_col_name
#
#             return updated_dft, processed_col_name
#
#         except Exception as e:
#             raise ValueError(f"Error processing output '{output}' with prefix '{prefix}': {str(e)}")
#     else:
#         raise ValueError(f"Unsupported prefix '{prefix}' in output '{output}'")
#
# def get_column_indices(dft: dataFrameTuple, column_names: list) -> list:
#     """
#     Get column indices for the specified column names.
#
#     Args:
#         dft (dataFrameTuple): Dataframe tuple
#         column_names (list): List of column names
#
#     Returns:
#         list: List of column indices
#     """
#     indices = []
#     df_columns = dft.dataFrame.columns
#
#     for col_name in column_names:
#         try:
#             index = df_columns.index(col_name)
#             indices.append(index)
#         except ValueError:
#             print(f"Warning: Column '{col_name}' not found in dataframe")
#
#     return indices
#
# def process_outputs_set(dft: dataFrameTuple, outputs_set: Set[str]) -> Tuple[dataFrameTuple, Dict[str, str]]:
#     """
#     Process multiple outputs and return updated dataframe with column mapping.
#
#     Args:
#         dft (dataFrameTuple): Input dataframe tuple
#         outputs_set (set): Set of output expressions to process
#
#     Returns:
#         Tuple[dataFrameTuple, Dict[str, str]]: Updated dataframe and mapping of
#                                              original_output -> processed_column_name
#     """
#     updated_dft = dft
#     column_mapping = {}
#
#     for output in outputs_set:
#         try:
#             updated_dft, processed_col = process_output(updated_dft, output)
#             column_mapping[output] = processed_col
#         except Exception as e:
#             # Log error but continue processing other outputs
#             print(f"Warning: Failed to process output '{output}': {str(e)}")
#             # Use fallback column name
#             fallback_col = extract_base_column_name(output)
#             column_mapping[output] = fallback_col
#
#     return updated_dft, column_mapping
#
# def processOutputsWPrefixes(dft: dataFrameTuple, outputs_set: set) -> Tuple[dataFrameTuple, list]:
#     """
#     Process outputs and return column indices (for backward compatibility).
#
#     Args:
#         dft (dataFrameTuple): Input dataframe tuple
#         outputs_set (set): Set of output expressions
#
#     Returns:
#         Tuple[dataFrameTuple, list]: Updated dataframe and list of column indices
#     """
#     updated_dft, column_mapping = process_outputs_set(dft, outputs_set)
#
#     # Get column indices for the processed columns
#     processed_columns = list(column_mapping.values())
#     column_indices = get_column_indices(updated_dft, processed_columns)
#
#     return updated_dft, column_indices
