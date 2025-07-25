import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import io

class DataProcessor:
    """
    Handles data loading, processing, and validation for flight test data.
    """
    
    def __init__(self):
        self.supported_formats = ['.csv', '.txt']
        self.required_columns = ['Timestamp', 'Elapsed Time (s)']
    
    def load_data(self, file) -> pd.DataFrame:
        """
        Enhanced data loading with proper parsing and validation.
        
        Args:
            file: Uploaded file object from Streamlit
            
        Returns:
            Processed DataFrame or empty DataFrame if loading fails
        """
        try:
            # Read the file content
            content = file.read().decode('utf-8-sig')
            lines = content.strip().split('\n')
            
            if len(lines) < 3:
                st.error("File must have at least 2 header rows and 1 data row")
                return pd.DataFrame()
            
            # Parse the header lines
            header1 = lines[0].split(',')  # Parameter names/descriptions
            header2 = lines[1].split(',')  # Units
            
            # Create proper column names
            columns = self._create_column_names(header1, header2)
            
            # Parse the data rows
            data_rows = self._parse_data_rows(lines[2:], len(columns))
            
            if not data_rows:
                st.error("No valid data rows found")
                return pd.DataFrame()
            
            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=columns)
            
            # Process and validate data
            df = self._process_timestamps(df)
            df = self._convert_numeric_columns(df)
            df = self._calculate_derived_columns(df)
            df = self._validate_data_quality(df)
            
            return df
            
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def _create_column_names(self, header1: List[str], header2: List[str]) -> List[str]:
        """
        Create proper column names from header rows.
        """
        columns = []
        for i, (param, unit) in enumerate(zip(header1, header2)):
            if i == 0:  # First column is timestamp
                columns.append('Timestamp')
            else:
                param = param.strip()
                unit = unit.strip()
                
                # Clean up parameter name
                if param.startswith('Description'):
                    param = param.replace('Description', '').strip()
                
                # Add unit to parameter name if available and meaningful
                if unit and unit not in ['EU', '', 'N/A', '-']:
                    columns.append(f"{param} ({unit})")
                else:
                    columns.append(param)
        
        return columns
    
    def _parse_data_rows(self, data_lines: List[str], expected_columns: int) -> List[List[str]]:
        """
        Parse data rows and filter valid ones.
        """
        data_rows = []
        for line_num, line in enumerate(data_lines, start=3):
            if line.strip():  # Skip empty lines
                row = [cell.strip() for cell in line.split(',')]
                
                # Validate row length
                if len(row) == expected_columns:
                    data_rows.append(row)
                elif len(row) > expected_columns:
                    # Truncate extra columns
                    data_rows.append(row[:expected_columns])
                    st.warning(f"Line {line_num}: Extra columns truncated")
                elif len(row) < expected_columns:
                    # Pad with empty values
                    row.extend([''] * (expected_columns - len(row)))
                    data_rows.append(row)
                    st.warning(f"Line {line_num}: Missing columns padded with empty values")
        
        return data_rows
    
    def _process_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process timestamp column and handle different formats.
        """
        if 'Timestamp' not in df.columns:
            st.error("Timestamp column not found")
            return df
        
        # Try different timestamp formats
        timestamp_formats = [
            '%j:%H:%M:%S.%f',  # day:hour:minute:second.millisecond
            '%Y-%m-%d %H:%M:%S.%f',  # Standard datetime with milliseconds
            '%Y-%m-%d %H:%M:%S',  # Standard datetime
            '%H:%M:%S.%f',  # Time only with milliseconds
            '%H:%M:%S'  # Time only
        ]
        
        parsed_timestamps = None
        for fmt in timestamp_formats:
            try:
                parsed_timestamps = pd.to_datetime(df['Timestamp'], format=fmt, errors='coerce')
                if parsed_timestamps.notna().sum() > len(df) * 0.8:  # At least 80% valid
                    break
            except:
                continue
        
        if parsed_timestamps is None or parsed_timestamps.notna().sum() == 0:
            st.error("Could not parse timestamps. Expected formats: day:hour:minute:second.millisecond or standard datetime")
            return pd.DataFrame()
        
        # Update DataFrame with parsed timestamps
        df['Timestamp'] = parsed_timestamps
        
        # Remove rows with invalid timestamps
        valid_mask = df['Timestamp'].notna()
        if not valid_mask.all():
            invalid_count = (~valid_mask).sum()
            st.warning(f"Removed {invalid_count} rows with invalid timestamps")
            df = df[valid_mask].reset_index(drop=True)
        
        if df.empty:
            st.error("No valid timestamps found")
            return pd.DataFrame()
        
        return df
    
    def _convert_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert numeric columns and handle conversion errors.
        """
        for col in df.columns:
            if col != 'Timestamp':
                # Attempt numeric conversion
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                
                # Check conversion success rate
                valid_ratio = numeric_series.notna().sum() / len(df)
                
                if valid_ratio > 0.8:  # At least 80% valid numeric values
                    df[col] = numeric_series
                    if valid_ratio < 1.0:
                        invalid_count = numeric_series.isna().sum()
                        st.warning(f"Column '{col}': {invalid_count} non-numeric values converted to NaN")
                else:
                    st.warning(f"Column '{col}': Too many non-numeric values, keeping as text")
        
        return df
    
    def _calculate_derived_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate derived columns like elapsed time.
        """
        if 'Timestamp' in df.columns and df['Timestamp'].notna().any():
            # Calculate elapsed time
            start_time = df['Timestamp'].min()
            df['Elapsed Time (s)'] = (df['Timestamp'] - start_time).dt.total_seconds()
            
            # Calculate sampling rate
            if len(df) > 1:
                time_diffs = df['Elapsed Time (s)'].diff().dropna()
                median_interval = time_diffs.median()
                if median_interval > 0:
                    sampling_rate = 1.0 / median_interval
                    st.info(f"Detected sampling rate: {sampling_rate:.1f} Hz (interval: {median_interval:.3f}s)")
        
        return df
    
    def _validate_data_quality(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data quality and provide feedback.
        """
        # Check for completely empty columns
        empty_cols = df.columns[df.isnull().all()].tolist()
        if empty_cols:
            st.warning(f"Empty columns detected: {empty_cols}")
            df = df.drop(columns=empty_cols)
        
        # Check for duplicate timestamps
        if 'Timestamp' in df.columns:
            duplicate_timestamps = df['Timestamp'].duplicated().sum()
            if duplicate_timestamps > 0:
                st.warning(f"Found {duplicate_timestamps} duplicate timestamps")
        
        # Check for constant values (might indicate sensor issues)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in ['Elapsed Time (s)']:
                unique_values = df[col].nunique()
                if unique_values == 1:
                    st.warning(f"Column '{col}' has constant value: {df[col].iloc[0]}")
                elif unique_values < len(df) * 0.01:  # Less than 1% unique values
                    st.info(f"Column '{col}' has very few unique values ({unique_values})")
        
        return df
    
    def get_parameter_categories(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Categorize parameters based on common flight test naming conventions.
        """
        categories = {
            'Control Surfaces': [],
            'Flight Angles': [],
            'Forces & Loads': [],
            'Positions & Commands': [],
            'Trim Settings': [],
            'Other Parameters': []
        }
        
        for col in df.columns:
            if col in ['Timestamp', 'Elapsed Time (s)']:
                continue
                
            col_lower = col.lower()
            
            # Control surfaces
            if any(keyword in col_lower for keyword in 
                   ['aileron', 'elevator', 'rudder', 'flap', 'spoiler', 'tab']):
                categories['Control Surfaces'].append(col)
            
            # Flight angles
            elif any(keyword in col_lower for keyword in 
                     ['angle', 'alpha', 'beta', 'aoa', 'sideslip', 'pitch', 'roll', 'yaw']):
                categories['Flight Angles'].append(col)
            
            # Forces and loads
            elif any(keyword in col_lower for keyword in 
                     ['force', 'load', 'strain', 'stress', 'moment', 'torque']):
                categories['Forces & Loads'].append(col)
            
            # Positions and commands
            elif any(keyword in col_lower for keyword in 
                     ['position', 'cmd', 'command', 'stick', 'pedal']):
                categories['Positions & Commands'].append(col)
            
            # Trim settings
            elif 'trim' in col_lower:
                categories['Trim Settings'].append(col)
            
            # Everything else
            else:
                categories['Other Parameters'].append(col)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def detect_anomalies(self, df: pd.DataFrame, parameter: str, 
                        method: str = 'zscore', threshold: float = 3.0) -> pd.Series:
        """
        Detect anomalies in a parameter using various methods.
        
        Args:
            df: DataFrame containing the data
            parameter: Parameter name to analyze
            method: Anomaly detection method ('zscore', 'iqr', 'isolation')
            threshold: Threshold for anomaly detection
            
        Returns:
            Boolean series indicating anomalies
        """
        if parameter not in df.columns or not pd.api.types.is_numeric_dtype(df[parameter]):
            return pd.Series(dtype=bool)
        
        data = df[parameter].dropna()
        
        if method == 'zscore':
            z_scores = np.abs((data - data.mean()) / data.std())
            anomalies = z_scores > threshold
        
        elif method == 'iqr':
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            anomalies = (data < lower_bound) | (data > upper_bound)
        
        else:  # Default to zscore
            z_scores = np.abs((data - data.mean()) / data.std())
            anomalies = z_scores > threshold
        
        # Align with original DataFrame index
        result = pd.Series(False, index=df.index)
        result.loc[data.index] = anomalies
        
        return result
    
    def calculate_statistics(self, df: pd.DataFrame, parameters: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Calculate comprehensive statistics for selected parameters.
        """
        stats = {}
        
        for param in parameters:
            if param in df.columns and pd.api.types.is_numeric_dtype(df[param]):
                data = df[param].dropna()
                
                if len(data) > 0:
                    stats[param] = {
                        'count': len(data),
                        'mean': data.mean(),
                        'std': data.std(),
                        'min': data.min(),
                        'max': data.max(),
                        'median': data.median(),
                        'q25': data.quantile(0.25),
                        'q75': data.quantile(0.75),
                        'range': data.max() - data.min(),
                        'skewness': data.skew(),
                        'kurtosis': data.kurtosis()
                    }
        
        return stats
    
    def export_processed_data(self, df: pd.DataFrame, format: str = 'csv') -> str:
        """
        Export processed data in various formats.
        
        Args:
            df: DataFrame to export
            format: Export format ('csv', 'excel', 'json')
            
        Returns:
            Exported data as string or bytes
        """
        if format == 'csv':
            return df.to_csv(index=False)
        elif format == 'json':
            return df.to_json(orient='records', date_format='iso')
        elif format == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Flight Data', index=False)
            return output.getvalue()
        else:
            return df.to_csv(index=False)

