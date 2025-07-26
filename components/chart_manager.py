import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy.fft import fft
from scipy.signal import welch

class ChartManager:
    """
    Manages chart creation and configuration for the enhanced flight analyzer.
    """
    
    def __init__(self):
        self.color_schemes = {
            'viridis': px.colors.sequential.Viridis,
            'plasma': px.colors.sequential.Plasma,
            'inferno': px.colors.sequential.Inferno,
            'magma': px.colors.sequential.Magma,
            'cividis': px.colors.sequential.Cividis,
            'blues': px.colors.sequential.Blues,
            'reds': px.colors.sequential.Reds,
            'greens': px.colors.sequential.Greens,
            'purples': px.colors.sequential.Purples
        }
    
    def create_chart(self, df: pd.DataFrame, config: Dict[str, Any]) -> Optional[go.Figure]:
        """
        Create a chart based on the provided configuration.
        
        Args:
            df: DataFrame containing the flight data
            config: Chart configuration dictionary
            
        Returns:
            Plotly figure object or None if creation fails
        """
        try:
            if not config.get('parameters'):
                return None
            
            chart_type = config.get('type', 'line')
            x_axis = config.get('x_axis', 'Elapsed Time (s)')
            title = config.get('title', 'Flight Data Chart')
            y_axis_label = config.get('y_axis_label', 'Value')
            color_scheme = config.get('color_scheme', 'viridis')

            if chart_type == 'frequency':
                return self.create_frequency_plot(df, config)
            
            # Validate x-axis column exists
            if x_axis not in df.columns:
                return None
            
            # Filter valid parameters
            valid_params = [param for param in config['parameters'] if param in df.columns]
            if not valid_params:
                return None
            
            # Create chart based on type
            if chart_type == 'line':
                return self._create_line_chart(df, x_axis, valid_params, title, y_axis_label, color_scheme)
            elif chart_type == 'scatter':
                return self._create_scatter_chart(df, x_axis, valid_params, title, y_axis_label, color_scheme)
            elif chart_type == 'bar':
                return self._create_bar_chart(df, x_axis, valid_params, title, y_axis_label, color_scheme)
            elif chart_type == 'area':
                return self._create_area_chart(df, x_axis, valid_params, title, y_axis_label, color_scheme)
            else:
                return self._create_line_chart(df, x_axis, valid_params, title, y_axis_label, color_scheme)
                
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None
    
    def create_frequency_plot(self, df: pd.DataFrame, config: Dict[str, Any]) -> Optional[go.Figure]:
        """
        Create a frequency plot based on the provided configuration.
        
        Args:
            df: DataFrame containing the flight data
            config: Chart configuration dictionary
            
        Returns:
            Plotly figure object or None if creation fails
        """
        try:
            if not config.get('parameters'):
                return None
            
            title = config.get('title', 'Frequency Analysis')
            y_axis_label = config.get('y_axis_label', 'Magnitude')
            color_scheme = config.get('color_scheme', 'viridis')
            freq_type = config.get('freq_type', 'fft')  # 'fft' or 'psd'
            
            # Validate parameters
            valid_params = [param for param in config['parameters'] if param in df.columns]
            if not valid_params:
                return None
            
            fig = go.Figure()
            colors = self._get_colors(color_scheme, len(valid_params))
            
            for i, param in enumerate(valid_params):
                if freq_type == 'fft':
                    freq, magnitude = self._compute_fft(df[param], df['Elapsed Time (s)'])
                    y_axis_label = 'Magnitude'
                else:  # PSD
                    freq, magnitude = self._compute_psd(df[param], df['Elapsed Time (s)'])
                    y_axis_label = 'Power/Frequency'
                
                fig.add_trace(go.Scatter(
                    x=freq,
                    y=magnitude,
                    mode='lines',
                    name=param,
                    line=dict(color=colors[i % len(colors)], width=2),
                    hovertemplate=f'<b>{param}</b><br>' +
                                f'Frequency: %{{x:.2f}} Hz<br>' +
                                f'{y_axis_label}: %{{y:.3e}}<extra></extra>'
                ))
            
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=16)),
                xaxis_title='Frequency (Hz)',
                yaxis_title=y_axis_label,
                xaxis_type='log',
                yaxis_type='log',
                hovermode='closest',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=50, r=50, t=80, b=50),
                height=400
            )
            
            return fig
        
        except Exception as e:
            print(f"Error creating frequency plot: {e}")
            return None

    def _compute_fft(self, data: pd.Series, time: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
        """Compute the FFT of the input data."""
        n = len(data)
        dt = (time.iloc[-1] - time.iloc[0]) / (n - 1)  # Time step
        
        fft_values = fft(data.values)
        frequencies = np.fft.fftfreq(n, dt)[:n//2]
        magnitudes = 2.0/n * np.abs(fft_values[0:n//2])
        
        return frequencies, magnitudes

    def _compute_psd(self, data: pd.Series, time: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
        """Compute the Power Spectral Density using Welch's method."""
        dt = (time.iloc[-1] - time.iloc[0]) / (len(time) - 1)  # Time step
        frequencies, psd = welch(data.values, fs=1/dt)
        
        return frequencies, psd
    
    def _create_line_chart(self, df: pd.DataFrame, x_axis: str, parameters: List[str], 
                          title: str, y_axis_label: str, color_scheme: str) -> go.Figure:
        """Create a line chart."""
        fig = go.Figure()
        
        colors = self._get_colors(color_scheme, len(parameters))
        
        for i, param in enumerate(parameters):
            fig.add_trace(go.Scatter(
                x=df[x_axis],
                y=df[param],
                mode='lines',
                name=param,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=f'<b>{param}</b><br>' +
                             f'{x_axis}: %{{x}}<br>' +
                             f'Value: %{{y:.3f}}<extra></extra>'
            ))
        
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            xaxis_title=x_axis,
            yaxis_title=y_axis_label,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=80, b=50),
            height=400
        )
        
        return fig
    
    def _create_scatter_chart(self, df: pd.DataFrame, x_axis: str, parameters: List[str], 
                             title: str, y_axis_label: str, color_scheme: str) -> go.Figure:
        """Create a scatter chart."""
        fig = go.Figure()
        
        colors = self._get_colors(color_scheme, len(parameters))
        
        for i, param in enumerate(parameters):
            fig.add_trace(go.Scatter(
                x=df[x_axis],
                y=df[param],
                mode='markers',
                name=param,
                marker=dict(
                    color=colors[i % len(colors)],
                    size=4,
                    opacity=0.7
                ),
                hovertemplate=f'<b>{param}</b><br>' +
                             f'{x_axis}: %{{x}}<br>' +
                             f'Value: %{{y:.3f}}<extra></extra>'
            ))
        
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            xaxis_title=x_axis,
            yaxis_title=y_axis_label,
            hovermode='closest',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=80, b=50),
            height=400
        )
        
        return fig
    
    def _create_bar_chart(self, df: pd.DataFrame, x_axis: str, parameters: List[str], 
                         title: str, y_axis_label: str, color_scheme: str) -> go.Figure:
        """Create a bar chart (useful for discrete time intervals)."""
        fig = go.Figure()
        
        colors = self._get_colors(color_scheme, len(parameters))
        
        # Sample data for bar chart (take every nth point to avoid overcrowding)
        sample_interval = max(1, len(df) // 50)  # Show max 50 bars
        sampled_df = df.iloc[::sample_interval]
        
        for i, param in enumerate(parameters):
            fig.add_trace(go.Bar(
                x=sampled_df[x_axis],
                y=sampled_df[param],
                name=param,
                marker_color=colors[i % len(colors)],
                opacity=0.8,
                hovertemplate=f'<b>{param}</b><br>' +
                             f'{x_axis}: %{{x}}<br>' +
                             f'Value: %{{y:.3f}}<extra></extra>'
            ))
        
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            xaxis_title=x_axis,
            yaxis_title=y_axis_label,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=80, b=50),
            height=400,
            barmode='group'
        )
        
        return fig
    
    def _create_area_chart(self, df: pd.DataFrame, x_axis: str, parameters: List[str], 
                          title: str, y_axis_label: str, color_scheme: str) -> go.Figure:
        """Create an area chart."""
        fig = go.Figure()
        
        colors = self._get_colors(color_scheme, len(parameters))
        
        for i, param in enumerate(parameters):
            fig.add_trace(go.Scatter(
                x=df[x_axis],
                y=df[param],
                mode='lines',
                name=param,
                fill='tonexty' if i > 0 else 'tozeroy',
                line=dict(color=colors[i % len(colors)], width=1),
                fillcolor=colors[i % len(colors)].replace('rgb', 'rgba').replace(')', ',0.3)'),
                hovertemplate=f'<b>{param}</b><br>' +
                             f'{x_axis}: %{{x}}<br>' +
                             f'Value: %{{y:.3f}}<extra></extra>'
            ))
        
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            xaxis_title=x_axis,
            yaxis_title=y_axis_label,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=80, b=50),
            height=400
        )
        
        return fig
    
    def _get_colors(self, color_scheme: str, num_colors: int) -> List[str]:
        """Get a list of colors from the specified color scheme."""
        if color_scheme in self.color_schemes:
            colors = self.color_schemes[color_scheme]
            if len(colors) >= num_colors:
                return colors[:num_colors]
            else:
                # Repeat colors if we need more than available
                return (colors * ((num_colors // len(colors)) + 1))[:num_colors]
        else:
            # Default to a basic color palette
            default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            return (default_colors * ((num_colors // len(default_colors)) + 1))[:num_colors]
    
    def create_multi_axis_chart(self, df: pd.DataFrame, primary_params: List[str], 
                               secondary_params: List[str], title: str = "Multi-Axis Chart") -> go.Figure:
        """
        Create a chart with multiple y-axes for parameters with different scales.
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        primary_colors = self._get_colors('blues', len(primary_params))
        secondary_colors = self._get_colors('reds', len(secondary_params))
        
        # Add primary parameters
        for i, param in enumerate(primary_params):
            if param in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['Elapsed Time (s)'],
                        y=df[param],
                        name=param,
                        line=dict(color=primary_colors[i], width=2)
                    ),
                    secondary_y=False,
                )
        
        # Add secondary parameters
        for i, param in enumerate(secondary_params):
            if param in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['Elapsed Time (s)'],
                        y=df[param],
                        name=param,
                        line=dict(color=secondary_colors[i], width=2, dash='dash')
                    ),
                    secondary_y=True,
                )
        
        # Set axis titles
        fig.update_xaxes(title_text="Elapsed Time (s)")
        fig.update_yaxes(title_text="Primary Parameters", secondary_y=False)
        fig.update_yaxes(title_text="Secondary Parameters", secondary_y=True)
        
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            hovermode="x unified",
            height=500,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig
    
    def create_correlation_heatmap(self, df: pd.DataFrame, parameters: List[str], 
                                  title: str = "Parameter Correlation") -> go.Figure:
        """
        Create a correlation heatmap for selected parameters.
        """
        # Filter numeric columns and selected parameters
        valid_params = [param for param in parameters if param in df.columns and pd.api.types.is_numeric_dtype(df[param])]
        
        if len(valid_params) < 2:
            return None
        
        # Calculate correlation matrix
        corr_matrix = df[valid_params].corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu_r',
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate='<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.3f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=16)),
            xaxis_title="Parameters",
            yaxis_title="Parameters",
            height=500,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        return fig

