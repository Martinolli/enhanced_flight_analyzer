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

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import base64
from io import BytesIO

from .flight_param_limits import PARAM_LIMITS
from .statistical_analysis import FlightDataStatistics


class FlightReportGenerator:
    """
    Comprehensive flight data report generator that analyzes parameters against limits
    and provides detailed statistical analysis in HTML format.
    """
    
    def __init__(self):
        self.param_limits = PARAM_LIMITS
        self.statistics = FlightDataStatistics()
        
    def generate_comprehensive_report(self, df: pd.DataFrame, 
                                    flight_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a comprehensive HTML report with parameter limit analysis and statistics.
        
        Args:
            df: Flight data DataFrame
            flight_info: Optional flight information dictionary
            
        Returns:
            HTML string containing the complete report
        """
        # Analyze data
        limit_analysis = self._analyze_parameter_limits(df)
        basic_stats = self._compute_basic_statistics(df)
        exceedance_summary = self._compute_exceedance_summary(limit_analysis)
        
        # Generate visualizations
        limit_violations_chart = self._create_limit_violations_chart(limit_analysis)
        parameter_distribution_chart = self._create_parameter_distribution_chart(df, limit_analysis)
        timeline_chart = self._create_timeline_violations_chart(df, limit_analysis)
        
        # Build HTML report
        html_content = self._build_html_report(
            df=df,
            flight_info=flight_info,
            limit_analysis=limit_analysis,
            basic_stats=basic_stats,
            exceedance_summary=exceedance_summary,
            charts={
                'violations': limit_violations_chart,
                'distributions': parameter_distribution_chart,
                'timeline': timeline_chart
            }
        )
        
        return html_content
    
    def _analyze_parameter_limits(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze all parameters against their defined limits.
        
        Args:
            df: Flight data DataFrame
            
        Returns:
            Dictionary containing limit analysis results
        """
        analysis_results = {}
        
        for param_name in df.columns:
            if param_name in ['Timestamp', 'Elapsed Time (s)']:
                continue
                
            if param_name in self.param_limits:
                limits = self.param_limits[param_name]
                param_data = df[param_name].dropna()
                
                if len(param_data) == 0:
                    continue
                
                # Check for limit violations
                min_violations = param_data < limits['min']
                max_violations = param_data > limits['max']
                
                analysis_results[param_name] = {
                    'limits': limits,
                    'data_points': len(param_data),
                    'min_value': float(param_data.min()),
                    'max_value': float(param_data.max()),
                    'mean_value': float(param_data.mean()),
                    'std_value': float(param_data.std()),
                    'min_violations': {
                        'count': int(min_violations.sum()),
                        'percentage': float(min_violations.sum() / len(param_data) * 100),
                        'indices': param_data[min_violations].index.tolist(),
                        'values': param_data[min_violations].tolist()
                    },
                    'max_violations': {
                        'count': int(max_violations.sum()),
                        'percentage': float(max_violations.sum() / len(param_data) * 100),
                        'indices': param_data[max_violations].index.tolist(),
                        'values': param_data[max_violations].tolist()
                    },
                    'total_violations': int(min_violations.sum() + max_violations.sum()),
                    'compliance_percentage': float((len(param_data) - min_violations.sum() - max_violations.sum()) / len(param_data) * 100),
                    'severity': self._assess_violation_severity(min_violations.sum() + max_violations.sum(), len(param_data))
                }
        
        return analysis_results
    
    def _assess_violation_severity(self, violation_count: int, total_points: int) -> str:
        """Assess the severity of parameter violations.
        Args:
            violation_count: Number of violations
            total_points: Total number of data points
        Returns:
            Severity level as a string
        """
        if violation_count == 0:
            return "COMPLIANT"
        
        violation_percentage = (violation_count / total_points) * 100
        
        if violation_percentage < 1:
            return "LOW"
        elif violation_percentage < 5:
            return "MEDIUM"
        elif violation_percentage < 10:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _compute_basic_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute basic flight statistics.
        Args:
            df: Flight data DataFrame
        Returns:
            Dictionary containing basic statistics
        
        """
        stats = {}
        
        # Flight duration
        if 'Elapsed Time (s)' in df.columns:
            elapsed_time = df['Elapsed Time (s)']
            stats['duration_seconds'] = float(elapsed_time.max() - elapsed_time.min())
            stats['duration_minutes'] = stats['duration_seconds'] / 60
            stats['duration_hours'] = stats['duration_minutes'] / 60
        
        # Data quality
        stats['total_parameters'] = len(df.columns)
        stats['total_data_points'] = len(df)
        stats['parameters_with_limits'] = len([col for col in df.columns if col in self.param_limits])
        
        # Missing data analysis
        missing_data = df.isnull().sum()
        stats['missing_data'] = {
            'total_missing': int(missing_data.sum()),
            'parameters_with_missing': int((missing_data > 0).sum()),
            'worst_parameter': missing_data.idxmax() if missing_data.sum() > 0 else None,
            'worst_missing_count': int(missing_data.max()) if missing_data.sum() > 0 else 0
        }
        
        return stats
    
    def _compute_exceedance_summary(self, limit_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Compute summary of limit exceedances.
        Args:
            limit_analysis: Dictionary containing limit analysis results
        Returns:
            Summary dictionary
        
        """
        summary = {
            'total_parameters_analyzed': len(limit_analysis),
            'compliant_parameters': 0,
            'parameters_with_violations': 0,
            'total_violations': 0,
            'severity_breakdown': {'COMPLIANT': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0},
            'worst_violators': []
        }
        
        violation_list = []
        
        for param_name, analysis in limit_analysis.items():
            if analysis['total_violations'] == 0:
                summary['compliant_parameters'] += 1
            else:
                summary['parameters_with_violations'] += 1
                violation_list.append({
                    'parameter': param_name,
                    'violations': analysis['total_violations'],
                    'percentage': 100 - analysis['compliance_percentage'],
                    'severity': analysis['severity']
                })
            
            summary['total_violations'] += analysis['total_violations']
            summary['severity_breakdown'][analysis['severity']] += 1
        
        # Sort by violation percentage and get worst violators
        violation_list.sort(key=lambda x: x['percentage'], reverse=True)
        summary['worst_violators'] = violation_list[:10]  # Top 10 worst violators
        
        return summary
    
    def _create_limit_violations_chart(self, limit_analysis: Dict[str, Any]) -> str:
        """Create a chart showing limit violations by parameter.
        Args:
            limit_analysis: Dictionary containing limit analysis results
        Returns:
            HTML div string containing the chart
        
        
        """
        if not limit_analysis:
            return ""
        
        # Prepare data for visualization
        params = []
        violation_counts = []
        compliance_percentages = []
        severities = []
        
        for param_name, analysis in limit_analysis.items():
            if analysis['total_violations'] > 0:  # Only show parameters with violations
                params.append(param_name[:30] + "..." if len(param_name) > 30 else param_name)
                violation_counts.append(analysis['total_violations'])
                compliance_percentages.append(analysis['compliance_percentage'])
                severities.append(analysis['severity'])
        
        if not params:
            return "<p><strong>✅ No parameter limit violations detected!</strong></p>"
        
        # Create bar chart
        fig = go.Figure()
        
        # Color mapping for severity
        color_map = {
            'LOW': '#FFA500',      # Orange
            'MEDIUM': '#FF6347',   # Tomato
            'HIGH': '#FF4500',     # Red Orange
            'CRITICAL': '#DC143C'  # Crimson
        }
        
        colors = [color_map.get(severity, '#808080') for severity in severities]
        
        fig.add_trace(go.Bar(
            x=params,
            y=violation_counts,
            marker_color=colors,
            text=[f"{count} ({100-comp:.1f}%)" for count, comp in zip(violation_counts, compliance_percentages)],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Violations: %{y}<br>Severity: %{customdata}<extra></extra>',
            customdata=severities
        ))
        
        fig.update_layout(
            title="Parameter Limit Violations",
            xaxis_title="Parameters",
            yaxis_title="Number of Violations",
            xaxis_tickangle=-45,
            height=500,
            showlegend=False
        )
        
        return fig.to_html(include_plotlyjs='inline', div_id="violations_chart")
    
    def _create_parameter_distribution_chart(self, df: pd.DataFrame, 
                                           limit_analysis: Dict[str, Any]) -> str:
        """Create distribution charts for parameters with violations.
        Args:
            df: Flight data DataFrame
            limit_analysis: Dictionary containing limit analysis results
        Returns:
            HTML div string containing the chart

        """
        if not limit_analysis:
            return ""
        
        # Find parameters with violations
        violation_params = [param for param, analysis in limit_analysis.items() 
                          if analysis['total_violations'] > 0]
        
        if not violation_params:
            return "<p><strong>No parameters with violations to display.</strong></p>"
        
        # Limit to top 6 worst violators for readability
        violation_params = violation_params[:6]
        
        # Create subplots
        rows = (len(violation_params) + 2) // 3  # 3 columns
        cols = min(3, len(violation_params))
        
        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=[param[:25] + "..." if len(param) > 25 else param 
                          for param in violation_params],
            vertical_spacing=0.1
        )
        
        for i, param in enumerate(violation_params):
            row = (i // 3) + 1
            col = (i % 3) + 1
            
            param_data = df[param].dropna()
            limits = limit_analysis[param]['limits']
            
            # Create histogram
            fig.add_trace(
                go.Histogram(
                    x=param_data,
                    nbinsx=30,
                    name=param,
                    showlegend=False,
                    opacity=0.7
                ),
                row=row, col=col
            )
            
            # Add limit lines
            fig.add_vline(
                x=limits['min'], 
                line_dash="dash", 
                line_color="red",
                annotation_text="Min Limit",
                row=row, col=col
            )
            
            fig.add_vline(
                x=limits['max'], 
                line_dash="dash", 
                line_color="red",
                annotation_text="Max Limit",
                row=row, col=col
            )
        
        fig.update_layout(
            title="Parameter Distributions with Limit Violations",
            height=300 * rows,
            showlegend=False
        )
        
        return fig.to_html(include_plotlyjs='inline', div_id="distributions_chart")
    
    def _create_timeline_violations_chart(self, df: pd.DataFrame, 
                                        limit_analysis: Dict[str, Any]) -> str:
        """Create a timeline chart showing when violations occurred.
        Args:
            df: Flight data DataFrame
            limit_analysis: Dictionary containing limit analysis results
        Returns:
            HTML div string containing the chart     
        
        """
        if 'Elapsed Time (s)' not in df.columns:
            return "<p><strong>Timeline chart requires 'Elapsed Time (s)' column.</strong></p>"
        
        # Find parameters with violations
        violation_params = [param for param, analysis in limit_analysis.items() 
                          if analysis['total_violations'] > 0]
        
        if not violation_params:
            return "<p><strong>No violations to display on timeline.</strong></p>"
        
        # Limit to top 3 worst violators for readability
        violation_params = violation_params[:3]
        
        fig = go.Figure()
        
        colors = ['red', 'orange', 'purple']
        
        for i, param in enumerate(violation_params):
            analysis = limit_analysis[param]
            
            # Get violation indices
            all_violation_indices = (analysis['min_violations']['indices'] + 
                                   analysis['max_violations']['indices'])
            
            if all_violation_indices:
                violation_times = df.loc[all_violation_indices, 'Elapsed Time (s)']
                violation_values = df.loc[all_violation_indices, param]
                
                fig.add_trace(go.Scatter(
                    x=violation_times,
                    y=[i] * len(violation_times),  # Stack violations vertically
                    mode='markers',
                    marker=dict(
                        color=colors[i % len(colors)],
                        size=8,
                        symbol='x'
                    ),
                    name=param[:30] + "..." if len(param) > 30 else param,
                    hovertemplate=f'<b>{param}</b><br>Time: %{{x:.1f}}s<br>Value: %{{customdata}}<extra></extra>',
                    customdata=violation_values
                ))
        
        fig.update_layout(
            title="Timeline of Parameter Limit Violations",
            xaxis_title="Elapsed Time (seconds)",
            yaxis_title="Parameter",
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(violation_params))),
                ticktext=[param[:30] + "..." if len(param) > 30 else param 
                         for param in violation_params]
            ),
            height=400,
            showlegend=True
        )
        
        return fig.to_html(include_plotlyjs='inline', div_id="timeline_chart")
    
    def _build_html_report(self, df: pd.DataFrame, flight_info: Optional[Dict[str, Any]],
                          limit_analysis: Dict[str, Any], basic_stats: Dict[str, Any],
                          exceedance_summary: Dict[str, Any], charts: Dict[str, str]) -> str:
        """Build the complete HTML report."""
        
        # Generate timestamp
        report_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Data Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #1e3c72;
            border-bottom: 3px solid #2a5298;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-card h3 {{
            margin: 0;
            font-size: 2em;
        }}
        .metric-card p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
        }}
        .severity-critical {{ background: linear-gradient(135deg, #DC143C 0%, #B22222 100%); }}
        .severity-high {{ background: linear-gradient(135deg, #FF4500 0%, #FF6347 100%); }}
        .severity-medium {{ background: linear-gradient(135deg, #FF6347 0%, #FFA500 100%); }}
        .severity-low {{ background: linear-gradient(135deg, #FFA500 0%, #FFD700 100%); }}
        .severity-compliant {{ background: linear-gradient(135deg, #32CD32 0%, #228B22 100%); }}
        
        .table-container {{
            overflow-x: auto;
            margin-bottom: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .violation-critical {{ background-color: #ffebee; }}
        .violation-high {{ background-color: #fff3e0; }}
        .violation-medium {{ background-color: #fff8e1; }}
        .violation-low {{ background-color: #f3e5f5; }}
        
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }}
        
        .summary-box {{
            background: #e3f2fd;
            border-left: 5px solid #2196f3;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        
        .warning-box {{
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        
        .error-box {{
            background: #f8d7da;
            border-left: 5px solid #dc3545;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✈️ Flight Data Analysis Report</h1>
            <p>Comprehensive Parameter Limit Analysis & Statistical Summary</p>
            <p>Generated on: {report_timestamp}</p>
        </div>
"""
        
        # Flight Information Section
        if flight_info:
            html_content += self._build_flight_info_section(flight_info)
        
        # Executive Summary
        html_content += self._build_executive_summary(basic_stats, exceedance_summary)
        
        # Parameter Limit Analysis
        html_content += self._build_limit_analysis_section(limit_analysis, exceedance_summary)
        
        # Charts Section
        html_content += self._build_charts_section(charts)
        
        # Detailed Statistics
        html_content += self._build_detailed_statistics_section(basic_stats, df)
        
        # Recommendations
        html_content += self._build_recommendations_section(exceedance_summary)
        
        # Footer
        html_content += f"""
        <div class="footer">
            <p>Report generated by Enhanced Flight Data Analyzer Pro v2.4.0</p>
            <p>© 2025 Martinolli - Licensed under Apache License 2.0</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content
    
    def _build_flight_info_section(self, flight_info: Dict[str, Any]) -> str:
        """Build flight information section.
        Args:
            flight_info: Dictionary containing flight information
        Returns:
            HTML string for flight information section
        """
        return f"""
        <div class="section">
            <h2>📋 Flight Information</h2>
            <div class="summary-box">
                <p><strong>Flight ID:</strong> {flight_info.get('flight_id', 'N/A')}</p>
                <p><strong>Aircraft:</strong> {flight_info.get('aircraft', 'N/A')}</p>
                <p><strong>Date:</strong> {flight_info.get('date', 'N/A')}</p>
                <p><strong>Pilot:</strong> {flight_info.get('pilot', 'N/A')}</p>
            </div>
        </div>
"""
    
    def _build_executive_summary(self, basic_stats: Dict[str, Any], 
                                exceedance_summary: Dict[str, Any]) -> str:
        """Build executive summary section.
        Args:
            basic_stats: Dictionary containing basic statistics
            exceedance_summary: Dictionary containing exceedance summary
        Returns:
            HTML string for executive summary section
        
        """
        
        # Determine overall status
        if exceedance_summary['severity_breakdown']['CRITICAL'] > 0:
            status_class = "error-box"
            status_icon = "🚨"
            status_text = "CRITICAL VIOLATIONS DETECTED"
        elif exceedance_summary['severity_breakdown']['HIGH'] > 0:
            status_class = "warning-box"
            status_icon = "⚠️"
            status_text = "HIGH SEVERITY VIOLATIONS DETECTED"
        elif exceedance_summary['parameters_with_violations'] > 0:
            status_class = "warning-box"
            status_icon = "⚠️"
            status_text = "PARAMETER VIOLATIONS DETECTED"
        else:
            status_class = "summary-box"
            status_icon = "✅"
            status_text = "ALL PARAMETERS WITHIN LIMITS"
        
        duration_str = f"{basic_stats.get('duration_minutes', 0):.1f} minutes"
        if basic_stats.get('duration_hours', 0) >= 1:
            duration_str = f"{basic_stats.get('duration_hours', 0):.1f} hours"
        
        return f"""
        <div class="section">
            <h2>📊 Executive Summary</h2>
            
            <div class="{status_class}">
                <h3>{status_icon} {status_text}</h3>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>{basic_stats.get('total_data_points', 0):,}</h3>
                    <p>Data Points</p>
                </div>
                <div class="metric-card">
                    <h3>{duration_str}</h3>
                    <p>Flight Duration</p>
                </div>
                <div class="metric-card">
                    <h3>{basic_stats.get('parameters_with_limits', 0)}</h3>
                    <p>Parameters Analyzed</p>
                </div>
                <div class="metric-card severity-{'compliant' if exceedance_summary['parameters_with_violations'] == 0 else 'critical'}">
                    <h3>{exceedance_summary['parameters_with_violations']}</h3>
                    <p>Parameters with Violations</p>
                </div>
                <div class="metric-card severity-{'compliant' if exceedance_summary['total_violations'] == 0 else 'critical'}">
                    <h3>{exceedance_summary['total_violations']:,}</h3>
                    <p>Total Violations</p>
                </div>
                <div class="metric-card severity-compliant">
                    <h3>{exceedance_summary['compliant_parameters']}</h3>
                    <p>Compliant Parameters</p>
                </div>
            </div>
        </div>
"""
    
    def _build_limit_analysis_section(self, limit_analysis: Dict[str, Any], 
                                    exceedance_summary: Dict[str, Any]) -> str:
        """Build parameter limit analysis section.
        Args:
            limit_analysis: Dictionary containing limit analysis results
            exceedance_summary: Dictionary containing exceedance summary
        Returns:
            HTML string for limit analysis section
        """
        
        # Severity breakdown
        severity_cards = ""
        for severity, count in exceedance_summary['severity_breakdown'].items():
            if count > 0:
                severity_cards += f"""
                <div class="metric-card severity-{severity.lower()}">
                    <h3>{count}</h3>
                    <p>{severity.title()}</p>
                </div>
"""
        
        # Worst violators table
        violators_table = ""
        if exceedance_summary['worst_violators']:
            violators_table = """
            <div class="table-container">
                <h3>🔴 Worst Parameter Violators</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Violations</th>
                            <th>Violation %</th>
                            <th>Severity</th>
                            <th>Min Limit</th>
                            <th>Max Limit</th>
                            <th>Actual Min</th>
                            <th>Actual Max</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            
            for violator in exceedance_summary['worst_violators']:
                param = violator['parameter']
                analysis = limit_analysis[param]
                row_class = f"violation-{violator['severity'].lower()}"
                
                violators_table += f"""
                        <tr class="{row_class}">
                            <td><strong>{param}</strong></td>
                            <td>{violator['violations']}</td>
                            <td>{violator['percentage']:.2f}%</td>
                            <td>{violator['severity']}</td>
                            <td>{analysis['limits']['min']}</td>
                            <td>{analysis['limits']['max']}</td>
                            <td>{analysis['min_value']:.3f}</td>
                            <td>{analysis['max_value']:.3f}</td>
                        </tr>
"""
            
            violators_table += """
                    </tbody>
                </table>
            </div>
"""
        
        return f"""
        <div class="section">
            <h2>🎯 Parameter Limit Analysis</h2>
            
            <h3>Severity Breakdown</h3>
            <div class="metrics-grid">
                {severity_cards}
            </div>
            
            {violators_table}
        </div>
"""
    
    def _build_charts_section(self, charts: Dict[str, str]) -> str:
        """Build charts section.
        Args:
            charts: Dictionary containing HTML divs of charts
        Returns:
            HTML string for charts section
        """
        return f"""
        <div class="section">
            <h2>📈 Visualizations</h2>
            
            <div class="chart-container">
                <h3>Parameter Limit Violations</h3>
                {charts.get('violations', '<p>No violations chart available.</p>')}
            </div>
            
            <div class="chart-container">
                <h3>Parameter Distributions</h3>
                {charts.get('distributions', '<p>No distribution chart available.</p>')}
            </div>
            
            <div class="chart-container">
                <h3>Violation Timeline</h3>
                {charts.get('timeline', '<p>No timeline chart available.</p>')}
            </div>
        </div>
"""
    
    def _build_detailed_statistics_section(self, basic_stats: Dict[str, Any], 
                                         df: pd.DataFrame) -> str:
        """Build detailed statistics section.
        Args:
            basic_stats: Dictionary containing basic statistics
            df: Flight data DataFrame
        Returns:
            HTML string for detailed statistics section
        """
        
        # Data quality metrics
        missing_info = basic_stats['missing_data']
        
        return f"""
        <div class="section">
            <h2>📋 Detailed Statistics</h2>
            
            <div class="summary-box">
                <h3>Data Quality Metrics</h3>
                <p><strong>Total Parameters:</strong> {basic_stats['total_parameters']}</p>
                <p><strong>Parameters with Defined Limits:</strong> {basic_stats['parameters_with_limits']}</p>
                <p><strong>Total Missing Data Points:</strong> {missing_info['total_missing']:,}</p>
                <p><strong>Parameters with Missing Data:</strong> {missing_info['parameters_with_missing']}</p>
                {f"<p><strong>Worst Parameter for Missing Data:</strong> {missing_info['worst_parameter']} ({missing_info['worst_missing_count']} missing)</p>" if missing_info['worst_parameter'] else ""}
            </div>
        </div>
"""
    
    def _build_recommendations_section(self, exceedance_summary: Dict[str, Any]) -> str:
        """Build recommendations section.
        Args:
            exceedance_summary: Dictionary containing exceedance summary
        Returns:
            HTML string for recommendations section        
        """
        
        recommendations = []
        
        if exceedance_summary['severity_breakdown']['CRITICAL'] > 0:
            recommendations.append("🚨 <strong>IMMEDIATE ACTION REQUIRED:</strong> Critical parameter violations detected. Review flight operations and aircraft systems immediately.")
        
        if exceedance_summary['severity_breakdown']['HIGH'] > 0:
            recommendations.append("⚠️ <strong>HIGH PRIORITY:</strong> High severity violations require investigation. Check sensor calibration and operational procedures.")
        
        if exceedance_summary['parameters_with_violations'] > 0:
            recommendations.append("🔍 <strong>INVESTIGATION:</strong> Review violated parameters for potential sensor issues or operational anomalies.")
        
        if exceedance_summary['parameters_with_violations'] == 0:
            recommendations.append("✅ <strong>EXCELLENT:</strong> All parameters operated within defined limits. Flight operations appear nominal.")
        
        recommendations.append("📊 <strong>DATA QUALITY:</strong> Regularly review data collection systems to ensure accurate parameter monitoring.")
        recommendations.append("🔄 <strong>CONTINUOUS MONITORING:</strong> Implement real-time parameter monitoring for future flights.")
        
        recommendations_html = ""
        for rec in recommendations:
            recommendations_html += f"<p>{rec}</p>"
        
        return f"""
        <div class="section">
            <h2>💡 Recommendations</h2>
            <div class="summary-box">
                {recommendations_html}
            </div>
        </div>
"""
