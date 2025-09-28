# Copyright (c) 2025 Martinolli
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Enhanced data processing for large flight test datasets.
This module provides memory-efficient loading, processing, and summarization
of large datasets, integrating with Streamlit for user interaction.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Iterator
import streamlit as st
from pathlib import Path
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
import warnings

class LargeDatasetHandler:
    """
    Handles large flight test datasets with memory-efficient processing.
    """
    
    def __init__(self, chunk_size: int = 10000, max_memory_mb: int = 500):
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb
        self.temp_dir = tempfile.mkdtemp(prefix="flight_analyzer_")
    
    def estimate_memory_usage(self, file_path: str) -> Dict[str, Any]:
        """
        Estimate memory usage for a dataset file.
        
        Args:
            file_path: Path to the data file
            
        Returns:
            Dictionary with memory usage estimates
        """
        try:
            # Read just the first few rows to estimate
            sample_df = pd.read_csv(file_path, nrows=100, skiprows=1)
            
            # Estimate memory per row
            memory_per_row = sample_df.memory_usage(deep=True).sum()
            
            # Count total rows (efficient method)
            with open(file_path, 'r') as f:
                total_rows = sum(1 for _ in f) - 2  # Subtract header rows
            
            estimated_memory_mb = (memory_per_row * total_rows) / (1024 * 1024)
            
            return {
                'total_rows': total_rows,
                'columns': len(sample_df.columns),
                'estimated_memory_mb': estimated_memory_mb,
                'requires_chunking': estimated_memory_mb > self.max_memory_mb,
                'recommended_chunk_size': min(self.chunk_size, max(1000, int(self.max_memory_mb * 1024 * 1024 / memory_per_row)))
            }
        except Exception as e:
            return {'error': str(e)}
    
    def load_data_chunked(self, file_path: str, progress_callback=None) -> pd.DataFrame:
        """
        Load large datasets in chunks with progress tracking.
        
        Args:
            file_path: Path to the data file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete DataFrame or sampled DataFrame for very large files
        """
        memory_info = self.estimate_memory_usage(file_path)
        
        if 'error' in memory_info:
            raise ValueError(f"Cannot estimate file size: {memory_info['error']}")
        
        total_rows = memory_info['total_rows']
        
        if not memory_info['requires_chunking']:
            # Small file, load normally
            return self._load_standard(file_path)
        
        # Large file, use chunked loading
        if total_rows > 1000000:  # > 1M rows
            return self._load_with_sampling(file_path, progress_callback)
        else:
            return self._load_chunked_full(file_path, progress_callback)
    
    def _load_standard(self, file_path: str) -> pd.DataFrame:
        """Load file using standard method.

        Args:
            file_path: Path to the data file
        Returns:
            DataFrame with loaded data"""
        # Read headers
        with open(file_path, 'r') as f:
            header1 = f.readline().strip().split(',')
            header2 = f.readline().strip().split(',')
        
        # Create column names
        columns = self._create_column_names(header1, header2)
        
        # Load data
        df = pd.read_csv(file_path, skiprows=2, names=columns)
        return self._process_dataframe(df)
    
    def _load_chunked_full(self, file_path: str, progress_callback=None) -> pd.DataFrame:
        """Load large file in chunks and combine.
        Args:
            file_path: Path to the data file
            progress_callback: Progress callback function
        Returns:
            Combined DataFrame
        """
        # Read headers
        with open(file_path, 'r') as f:
            header1 = f.readline().strip().split(',')
            header2 = f.readline().strip().split(',')
        
        columns = self._create_column_names(header1, header2)
        
        # Process in chunks
        chunk_iter = pd.read_csv(file_path, skiprows=2, names=columns, chunksize=self.chunk_size)
        
        processed_chunks = []
        total_processed = 0
        
        for i, chunk in enumerate(chunk_iter):
            processed_chunk = self._process_dataframe(chunk)
            processed_chunks.append(processed_chunk)
            total_processed += len(chunk)
            
            if progress_callback:
                progress_callback(total_processed)
        
        # Combine all chunks
        return pd.concat(processed_chunks, ignore_index=True)
    
    def _load_with_sampling(self, file_path: str, progress_callback=None, 
                           sample_rate: float = 0.1) -> pd.DataFrame:
        """
        Load very large files with intelligent sampling.
        
        Args:
            file_path: Path to the data file
            progress_callback: Progress callback function
            sample_rate: Fraction of data to sample (0.1 = 10%)
            
        Returns:
            Sampled DataFrame
        """
        memory_info = self.estimate_memory_usage(file_path)
        total_rows = memory_info['total_rows']
        
        # Calculate sampling parameters
        target_rows = int(total_rows * sample_rate)
        skip_interval = max(1, total_rows // target_rows)
        
        # Read headers
        with open(file_path, 'r') as f:
            header1 = f.readline().strip().split(',')
            header2 = f.readline().strip().split(',')
        
        columns = self._create_column_names(header1, header2)
        
        # Sample rows systematically
        sampled_rows = []
        with open(file_path, 'r') as f:
            # Skip headers
            f.readline()
            f.readline()
            
            for i, line in enumerate(f):
                if i % skip_interval == 0:
                    sampled_rows.append(line.strip().split(','))
                
                if progress_callback and i % 10000 == 0:
                    progress_callback(i)
        
        # Create DataFrame from sampled data
        df = pd.DataFrame(sampled_rows, columns=columns)
        processed_df = self._process_dataframe(df)
        
        # Add metadata about sampling
        processed_df.attrs['sampling_info'] = {
            'original_rows': total_rows,
            'sampled_rows': len(processed_df),
            'sample_rate': sample_rate,
            'skip_interval': skip_interval
        }
        
        return processed_df
    
    def _create_column_names(self, header1: List[str], header2: List[str]) -> List[str]:
        """Create proper column names from header rows.
        Args:
            header1: First header row
            header2: Second header row
        Returns:
            List of cleaned column names        
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
                
                # Create column name with unit
                if unit and unit not in ['EU', '']:
                    columns.append(f"{param} ({unit})")
                else:
                    columns.append(param)
        
        return columns
    
    def _process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process DataFrame with timestamp conversion and numeric conversion.
        Args:
            df: DataFrame to process
        Returns:
            Processed DataFrame with timestamp converted to datetime and numeric columns
            converted to numeric, with elapsed time in seconds calculated.
        
        """
        # Convert timestamp
        if 'Timestamp' in df.columns:
            try:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%j:%H:%M:%S.%f')
                df['Elapsed Time (s)'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds()
            except:
                # Fallback for different timestamp formats
                df['Elapsed Time (s)'] = range(len(df))
        
        # Convert numeric columns
        for col in df.columns:
            if col not in ['Timestamp']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def create_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Create a comprehensive summary of the dataset.
        
        Args:
            df: DataFrame to summarize
            
        Returns:
            Dictionary with dataset summary
        """
        summary = {
            'basic_info': {
                'rows': len(df),
                'columns': len(df.columns),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
                'time_range': None,
                'sampling_info': df.attrs.get('sampling_info', None)
            },
            'column_info': {},
            'data_quality': {
                'missing_values': {},
                'duplicate_rows': df.duplicated().sum(),
                'constant_columns': []
            }
        }
        
        # Time range information
        if 'Elapsed Time (s)' in df.columns:
            time_col = df['Elapsed Time (s)'].dropna()
            if len(time_col) > 0:
                summary['basic_info']['time_range'] = {
                    'start': float(time_col.min()),
                    'end': float(time_col.max()),
                    'duration': float(time_col.max() - time_col.min()),
                    'sampling_rate': len(time_col) / (time_col.max() - time_col.min()) if time_col.max() > time_col.min() else 0
                }
        
        # Column analysis
        for col in df.columns:
            col_data = df[col]
            col_info = {
                'dtype': str(col_data.dtype),
                'non_null_count': col_data.count(),
                'null_count': col_data.isnull().sum(),
                'null_percentage': (col_data.isnull().sum() / len(df)) * 100
            }
            
            if pd.api.types.is_numeric_dtype(col_data):
                col_info.update({
                    'min': float(col_data.min()) if col_data.count() > 0 else None,
                    'max': float(col_data.max()) if col_data.count() > 0 else None,
                    'mean': float(col_data.mean()) if col_data.count() > 0 else None,
                    'std': float(col_data.std()) if col_data.count() > 0 else None,
                    'unique_values': col_data.nunique()
                })
                
                # Check for constant columns
                if col_data.nunique() <= 1:
                    summary['data_quality']['constant_columns'].append(col)
            
            summary['column_info'][col] = col_info
            summary['data_quality']['missing_values'][col] = col_info['null_count']
        
        return summary
    
    def optimize_dataframe_memory(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize DataFrame memory usage by downcasting numeric types.
        
        Args:
            df: DataFrame to optimize
            
        Returns:
            Memory-optimized DataFrame
        """
        optimized_df = df.copy()
        
        for col in optimized_df.columns:
            if col == 'Timestamp':
                continue
                
            col_data = optimized_df[col]
            
            if pd.api.types.is_numeric_dtype(col_data):
                # Try to downcast numeric types
                if pd.api.types.is_integer_dtype(col_data):
                    optimized_df[col] = pd.to_numeric(col_data, downcast='integer')
                elif pd.api.types.is_float_dtype(col_data):
                    optimized_df[col] = pd.to_numeric(col_data, downcast='float')
        
        return optimized_df
    
    def create_data_preview(self, df: pd.DataFrame, n_rows: int = 100) -> Dict[str, Any]:
        """
        Create a preview of the dataset for UI display.
        
        Args:
            df: DataFrame to preview
            n_rows: Number of rows to include in preview
            
        Returns:
            Dictionary with preview data
        """
        preview_df = df.head(n_rows)
        
        return {
            'preview_data': preview_df.to_dict('records'),
            'column_names': list(df.columns),
            'total_rows': len(df),
            'preview_rows': len(preview_df),
            'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    
    def cleanup_temp_files(self):
        """Clean up temporary files created during processing."""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            warnings.warn(f"Could not clean up temporary directory: {e}")


# Integration with Streamlit UI
def create_large_dataset_ui():
    """
    Create Streamlit UI components for large dataset handling.
    Args:
        None (uses Streamlit session state)
    Returns:
        None (modifies Streamlit session state)
    """
    st.subheader("📊 Large Dataset Handling")
    
    # Dataset size estimation
    if st.session_state.get('uploaded_file'):
        handler = LargeDatasetHandler()
        
        with st.spinner("Analyzing dataset size..."):
            memory_info = handler.estimate_memory_usage(st.session_state.uploaded_file)
        
        if 'error' not in memory_info:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Rows", f"{memory_info['total_rows']:,}")
            with col2:
                st.metric("Estimated Memory", f"{memory_info['estimated_memory_mb']:.1f} MB")
            with col3:
                st.metric("Columns", memory_info['columns'])
            
            # Show recommendations
            if memory_info['requires_chunking']:
                st.warning("⚠️ Large dataset detected. Chunked processing recommended.")
                
                # Sampling options
                st.subheader("Sampling Options")
                sample_rate = st.slider("Sample Rate (%)", 1, 100, 10) / 100
                
                if st.button("Load with Sampling"):
                    with st.spinner("Loading sampled data..."):
                        df = handler._load_with_sampling(
                            st.session_state.uploaded_file, 
                            sample_rate=sample_rate
                        )
                        st.session_state.data = df
                        st.success(f"✅ Loaded {len(df):,} rows (sampled from {memory_info['total_rows']:,})")
            else:
                st.success("✅ Dataset size is manageable for full loading.")