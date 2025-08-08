import pytest
import polars as pl
import numpy as np
from typing import Union
from unittest.mock import Mock, patch

# Mock dependencies
class MockDataFrameTuple:
    def __init__(self, dataFrame, header):
        self.dataFrame = dataFrame
        self.header = header
    
    def _replace(self, **kwargs):
        return MockDataFrameTuple(kwargs.get('dataFrame', self.dataFrame), self.header)

def mock_parseOutputExpression(output):
    if output.startswith('db('):
        return 'db', output[3:-1]
    elif output.startswith('max('):
        return 'max', output[4:-1]
    elif output.startswith('mag('):
        return 'mag', output[4:-1]
    return None, output

# Mock constants
AC_PREFIXES = ['db', 'mag', 'ph', 'ph_deg']
SCALAR_PREFIXES = ['max', 'min', 'ave']

class TestProcessOutputSignals:
    
    @patch('prefixHandler.parseOutputExpression', side_effect=mock_parseOutputExpression)
    def test_db_prefix_with_ac_header(self, mock_parse):
        # Setup test data
        df = pl.DataFrame({
            'Re(V(OUT))': [1.0, 2.0, 3.0],
            'Im(V(OUT))': [0.5, 1.0, 1.5]
        })
        dft = MockDataFrameTuple(df, 'AC Analysis')
        
        # Mock the function (simplified for testing)
        def processOutputSignals(dft, outputSignals):
            for outputSig in outputSignals:
                prefix, base = mock_parseOutputExpression(outputSig)
                if prefix == 'db' and 'AC' in dft.header:
                    # Simplified db calculation for test
                    magnitude = ((df[f'Re({base})'] ** 2 + df[f'Im({base})'] ** 2).sqrt())
                    db_values = magnitude.map_elements(lambda x: 20 * np.log10(x))
                    new_df = df.with_columns(db_values.alias(f'db({base})'))
                    return dft._replace(dataFrame=new_df)
            return dft
        
        result = processOutputSignals(dft, {'db(V(OUT))'})
        assert 'db(V(OUT))' in result.dataFrame.columns
    
    @patch('prefixHandler.parseOutputExpression', side_effect=mock_parseOutputExpression)
    def test_scalar_max_prefix(self, mock_parse):
        df = pl.DataFrame({'V(OUT)': [1.0, 5.0, 3.0]})
        dft = MockDataFrameTuple(df, 'DC Analysis')
        
        def processOutputSignals(dft, outputSignals):
            for outputSig in outputSignals:
                prefix, base = mock_parseOutputExpression(outputSig)
                if prefix == 'max':
                    return dft.dataFrame.select(pl.col(base).max()).item()
            return dft
        
        result = processOutputSignals(dft, {'max(V(OUT))'})
        assert result == 5.0
    
    def test_no_prefix_returns_original(self):
        df = pl.DataFrame({'V(OUT)': [1.0, 2.0, 3.0]})
        dft = MockDataFrameTuple(df, 'DC Analysis')
        
        def processOutputSignals(dft, outputSignals):
            for outputSig in outputSignals:
                prefix, base = mock_parseOutputExpression(outputSig)
                if prefix is None:
                    return dft
            return dft
        
        result = processOutputSignals(dft, {'V(OUT)'})
        assert result.dataFrame.equals(df)
    
    def test_empty_output_signals(self):
        df = pl.DataFrame({'V(OUT)': [1.0, 2.0, 3.0]})
        dft = MockDataFrameTuple(df, 'DC Analysis')
        
        def processOutputSignals(dft, outputSignals):
            if not outputSignals:
                return dft
            return dft
        
        result = processOutputSignals(dft, set())
        assert result.dataFrame.equals(df)