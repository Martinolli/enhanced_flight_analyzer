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
Enhanced statistical analysis capabilities for flight test data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats
from scipy.signal import find_peaks, savgol_filter
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings

class FlightDataStatistics:
    """
    Comprehensive statistical analysis for flight test data.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def compute_basic_statistics(self, df: pd.DataFrame, parameters: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Compute basic statistical measures for selected parameters.
        
        Args:
            df: DataFrame containing the data
            parameters: List of parameter names to analyze
            
        Returns:
            Dictionary with statistics for each parameter
        """
        stats_dict = {}
        
        for param in parameters:
            if param not in df.columns:
                continue
                
            data = df[param].dropna()
            if len(data) == 0:
                continue
            
            stats_dict[param] = {
                'count': len(data),
                'mean': float(np.mean(data)),
                'std': float(np.std(data)),
                'min': float(np.min(data)),
                'max': float(np.max(data)),
                'median': float(np.median(data)),
                'q25': float(np.percentile(data, 25)),
                'q75': float(np.percentile(data, 75)),
                'skewness': float(stats.skew(data)),
                'kurtosis': float(stats.kurtosis(data)),
                'range': float(np.max(data) - np.min(data)),
                'iqr': float(np.percentile(data, 75) - np.percentile(data, 25)),
                'cv': float(np.std(data) / np.mean(data)) if np.mean(data) != 0 else np.inf
            }
        
        return stats_dict
    
    def detect_outliers(self, df: pd.DataFrame, parameters: List[str], 
                       method: str = 'iqr', threshold: float = 1.5) -> Dict[str, Dict[str, Any]]:
        """
        Detect outliers in flight test data using various methods.
        
        Args:
            df: DataFrame containing the data
            parameters: List of parameter names to analyze
            method: Outlier detection method ('iqr', 'zscore', 'modified_zscore')
            threshold: Threshold for outlier detection
            
        Returns:
            Dictionary with outlier information for each parameter
        """
        outlier_info = {}
        
        for param in parameters:
            if param not in df.columns:
                continue
                
            data = df[param].dropna()
            if len(data) == 0:
                continue
            
            outlier_indices = []
            outlier_values = []
            
            if method == 'iqr':
                q1 = np.percentile(data, 25)
                q3 = np.percentile(data, 75)
                iqr = q3 - q1
                lower_bound = q1 - threshold * iqr
                upper_bound = q3 + threshold * iqr
                outlier_mask = (data < lower_bound) | (data > upper_bound)
                
            elif method == 'zscore':
                z_scores = np.abs(stats.zscore(data))
                outlier_mask = z_scores > threshold
                
            elif method == 'modified_zscore':
                median = np.median(data)
                mad = np.median(np.abs(data - median))
                modified_z_scores = 0.6745 * (data - median) / mad
                outlier_mask = np.abs(modified_z_scores) > threshold
            
            outlier_indices = data.index[outlier_mask].tolist()
            outlier_values = data[outlier_mask].tolist()
            
            outlier_info[param] = {
                'method': method,
                'threshold': threshold,
                'outlier_count': len(outlier_indices),
                'outlier_percentage': (len(outlier_indices) / len(data)) * 100,
                'outlier_indices': outlier_indices,
                'outlier_values': outlier_values,
                'bounds': {
                    'lower': lower_bound if method == 'iqr' else None,
                    'upper': upper_bound if method == 'iqr' else None
                }
            }
        
        return outlier_info
    
    def compute_correlation_analysis(self, df: pd.DataFrame, parameters: List[str], 
                                   method: str = 'pearson') -> Dict[str, Any]:
        """
        Compute comprehensive correlation analysis between parameters.
        
        Args:
            df: DataFrame containing the data
            parameters: List of parameter names to analyze
            method: Correlation method ('pearson', 'spearman', 'kendall')
            
        Returns:
            Dictionary with correlation results
        """
        # Filter to numeric parameters that exist in the dataframe
        valid_params = [p for p in parameters if p in df.columns and pd.api.types.is_numeric_dtype(df[p])]
        
        if len(valid_params) < 2:
            return {'error': 'Need at least 2 numeric parameters for correlation analysis'}
        
        # Create correlation matrix
        corr_data = df[valid_params].dropna()
        
        if method == 'pearson':
            corr_matrix = corr_data.corr(method='pearson')
        elif method == 'spearman':
            corr_matrix = corr_data.corr(method='spearman')
        elif method == 'kendall':
            corr_matrix = corr_data.corr(method='kendall')
        else:
            corr_matrix = corr_data.corr(method='pearson')
        
        # Find strongest correlations
        corr_pairs = []
        for i in range(len(valid_params)):
            for j in range(i+1, len(valid_params)):
                param1 = valid_params[i]
                param2 = valid_params[j]
                corr_value = corr_matrix.iloc[i, j]
                
                if not np.isnan(corr_value):
                    corr_pairs.append({
                        'param1': param1,
                        'param2': param2,
                        'correlation': float(corr_value),
                        'abs_correlation': abs(float(corr_value))
                    })
        
        # Sort by absolute correlation strength
        corr_pairs.sort(key=lambda x: x['abs_correlation'], reverse=True)
        
        return {
            'method': method,
            'correlation_matrix': corr_matrix.to_dict(),
            'parameter_list': valid_params,
            'strongest_correlations': corr_pairs[:10],  # Top 10
            'data_points': len(corr_data)
        }
    
    def perform_trend_analysis(self, df: pd.DataFrame, time_col: str, 
                             parameters: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Perform trend analysis on time series data.
        
        Args:
            df: DataFrame containing the data
            time_col: Name of the time column
            parameters: List of parameter names to analyze
            
        Returns:
            Dictionary with trend analysis results
        """
        trend_results = {}
        
        if time_col not in df.columns:
            return {'error': f'Time column {time_col} not found'}
        
        time_data = df[time_col].dropna()
        
        for param in parameters:
            if param not in df.columns:
                continue
            
            # Get aligned time and parameter data
            param_data = df[param].dropna()
            common_indices = time_data.index.intersection(param_data.index)
            
            if len(common_indices) < 3:
                continue
            
            t = time_data.loc[common_indices].values
            y = param_data.loc[common_indices].values
            
            # Linear trend analysis
            slope, intercept, r_value, p_value, std_err = stats.linregress(t, y)
            
            # Detect change points using simple derivative analysis
            if len(y) > 10:
                # Smooth the data first
                window_length = min(11, len(y) // 3)
                if window_length % 2 == 0:
                    window_length += 1
                
                try:
                    y_smooth = savgol_filter(y, window_length, 3)
                    dy_dt = np.gradient(y_smooth, t)
                    
                    # Find peaks in the derivative (potential change points)
                    peaks, _ = find_peaks(np.abs(dy_dt), height=np.std(dy_dt))
                    change_points = t[peaks].tolist() if len(peaks) > 0 else []
                except:
                    change_points = []
            else:
                change_points = []
            
            trend_results[param] = {
                'linear_trend': {
                    'slope': float(slope),
                    'intercept': float(intercept),
                    'r_squared': float(r_value**2),
                    'p_value': float(p_value),
                    'std_error': float(std_err),
                    'trend_direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
                },
                'change_points': change_points,
                'data_points': len(common_indices),
                'time_range': {
                    'start': float(t[0]),
                    'end': float(t[-1]),
                    'duration': float(t[-1] - t[0])
                }
            }
        
        return trend_results
    
    def compute_parameter_stability(self, df: pd.DataFrame, parameters: List[str], 
                                  window_size: int = 10) -> Dict[str, Dict[str, float]]:
        """
        Analyze parameter stability using rolling statistics.
        
        Args:
            df: DataFrame containing the data
            parameters: List of parameter names to analyze
            window_size: Size of rolling window for stability analysis
            
        Returns:
            Dictionary with stability metrics for each parameter
        """
        stability_results = {}
        
        for param in parameters:
            if param not in df.columns:
                continue
            
            data = df[param].dropna()
            if len(data) < window_size:
                continue
            
            # Rolling statistics
            rolling_mean = data.rolling(window=window_size).mean()
            rolling_std = data.rolling(window=window_size).std()
            
            # Stability metrics
            mean_stability = np.std(rolling_mean.dropna()) / np.mean(np.abs(rolling_mean.dropna())) if len(rolling_mean.dropna()) > 0 else np.inf
            std_stability = np.std(rolling_std.dropna()) / np.mean(rolling_std.dropna()) if len(rolling_std.dropna()) > 0 and np.mean(rolling_std.dropna()) > 0 else np.inf
            
            # Overall stability score (lower is more stable)
            stability_score = (mean_stability + std_stability) / 2
            
            stability_results[param] = {
                'mean_stability': float(mean_stability),
                'std_stability': float(std_stability),
                'overall_stability_score': float(stability_score),
                'stability_rating': self._rate_stability(stability_score),
                'window_size': window_size,
                'data_points': len(data)
            }
        
        return stability_results
    
    def _rate_stability(self, score: float) -> str:
        """Rate stability based on stability score."""
        if score < 0.1:
            return 'Very Stable'
        elif score < 0.3:
            return 'Stable'
        elif score < 0.6:
            return 'Moderately Stable'
        elif score < 1.0:
            return 'Unstable'
        else:
            return 'Very Unstable'
    
    def perform_pca_analysis(self, df: pd.DataFrame, parameters: List[str], 
                           n_components: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform Principal Component Analysis on selected parameters.
        
        Args:
            df: DataFrame containing the data
            parameters: List of parameter names to analyze
            n_components: Number of components to compute (None for all)
            
        Returns:
            Dictionary with PCA results
        """
        # Filter to numeric parameters
        valid_params = [p for p in parameters if p in df.columns and pd.api.types.is_numeric_dtype(df[p])]
        
        if len(valid_params) < 2:
            return {'error': 'Need at least 2 numeric parameters for PCA'}
        
        # Prepare data
        pca_data = df[valid_params].dropna()
        
        if len(pca_data) < 2:
            return {'error': 'Insufficient data points for PCA'}
        
        # Standardize the data
        data_scaled = self.scaler.fit_transform(pca_data)
        
        # Perform PCA
        if n_components is None:
            n_components = min(len(valid_params), len(pca_data))
        
        pca = PCA(n_components=n_components)
        components = pca.fit_transform(data_scaled)
        
        # Create results
        results = {
            'n_components': n_components,
            'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
            'cumulative_variance_ratio': np.cumsum(pca.explained_variance_ratio_).tolist(),
            'components': pca.components_.tolist(),
            'parameter_names': valid_params,
            'data_points': len(pca_data),
            'principal_components': components.tolist()
        }
        
        # Add component interpretations
        component_interpretations = []
        for i, component in enumerate(pca.components_):
            # Find parameters with highest absolute loadings
            loadings = [(valid_params[j], float(component[j])) for j in range(len(component))]
            loadings.sort(key=lambda x: abs(x[1]), reverse=True)
            
            component_interpretations.append({
                'component': i + 1,
                'variance_explained': float(pca.explained_variance_ratio_[i]),
                'top_loadings': loadings[:3],  # Top 3 contributors
                'interpretation': self._interpret_component(loadings[:3])
            })
        
        results['component_interpretations'] = component_interpretations
        
        return results
    
    def _interpret_component(self, top_loadings: List[Tuple[str, float]]) -> str:
        """Generate interpretation for a PCA component.
        Args:
            top_loadings: List of tuples (parameter name, loading value)
        Returns:
            Interpretation string        
        """
        if not top_loadings:
            return "No significant loadings"
        
        primary = top_loadings[0]
        interpretation = f"Primarily driven by {primary[0]} ({primary[1]:.3f})"
        
        if len(top_loadings) > 1:
            secondary = top_loadings[1]
            if abs(secondary[1]) > 0.3:  # Significant secondary loading
                interpretation += f", with contribution from {secondary[0]} ({secondary[1]:.3f})"
        
        return interpretation