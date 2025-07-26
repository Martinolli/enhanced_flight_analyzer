import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
import json
import base64
from typing import Dict, List, Any, Optional
import io

from components.chart_manager import ChartManager
from components.flight_param_limits import PARAM_LIMITS


class ExportManager:
    """
    Manages export functionality for charts, dashboards, and data.
    """
    
    def __init__(self):
        self.export_formats = {
            'html': 'HTML Dashboard',
            'pdf': 'PDF Report',
            'png': 'PNG Images',
            'svg': 'SVG Images',
            'json': 'JSON Data',
            'csv': 'CSV Data',
            'excel': 'Excel Workbook'
        }
    
    def export_dashboard_html(self, charts: Dict[str, Dict[str, Any]], df: pd.DataFrame) -> str:
        """
        Export the entire dashboard as an interactive HTML file.
        
        Args:
            charts: Dictionary of chart configurations
            df: DataFrame containing the flight data
            
        Returns:
            HTML content as string
        """
        try:
            from components.chart_manager import ChartManager
            chart_manager = ChartManager()
            
            # Generate HTML content
            html_content = self._generate_html_template()
            
            # Add chart data and configurations
            chart_htmls = []
            for chart_id, config in charts.items():
                fig = chart_manager.create_chart(df, config)
                if fig:
                    chart_html = pio.to_html(fig, include_plotlyjs='cdn', div_id=f"chart_{chart_id}")
                    chart_htmls.append(chart_html)
            
            # Combine all charts into the template
            charts_section = '\n'.join(chart_htmls)
            
            # Add metadata
            metadata = {
                'export_date': datetime.now().isoformat(),
                'data_points': len(df),
                'parameters': len(df.columns) - 2,
                'charts_count': len(charts)
            }
            
            # Replace placeholders in template
            html_content = html_content.replace('{{CHARTS_SECTION}}', charts_section)
            html_content = html_content.replace('{{METADATA}}', json.dumps(metadata, indent=2))
            html_content = html_content.replace('{{TITLE}}', 'Flight Data Analysis Dashboard')
            
            return html_content
            
        except Exception as e:
            st.error(f"Error exporting dashboard: {e}")
            return ""
    
    def generate_automatic_interpretations(self, df: pd.DataFrame) -> list:
        interpretations = []
        for param, limits in PARAM_LIMITS.items():
            if param in df.columns:
                min_val = df[param].min()
                max_val = df[param].max()
                if min_val < limits["min"]:
                    interpretations.append(
                        f"⚠️ {param}: valor mínimo {min_val:.2f} < limite mínimo permitido ({limits['min']})."
                    )
                if max_val > limits["max"]:
                    interpretations.append(
                        f"⚠️ {param}: valor máximo {max_val:.2f} > limite máximo permitido ({limits['max']})."
                    )
                if limits["min"] <= min_val and max_val <= limits["max"]:
                    interpretations.append(
                        f"✅ {param}: todos os valores dentro dos limites especificados."
                    )
        if not interpretations:
            interpretations.append("Nenhum parâmetro crítico identificado com valores fora dos limites default.")
        return interpretations

    def generate_auto_report(self, charts, df, stats=None, info=None, filename="report.html"):
        if isinstance(charts, str):
            raise ValueError("Charts is a string, expected a dictionary of chart configs.")
        if not isinstance(df, pd.DataFrame):
            raise ValueError("DataFrame is required.")

        html_parts = []
        # 1. Cabeçalho e informações básicas
        html_parts.append(f"<h1>Relatório Automático - Ensaio em Voo</h1>")
        html_parts.append(f"<p><b>Total de pontos:</b> {len(df)}<br>")
        html_parts.append(f"<b>Número de parâmetros:</b> {len(df.columns)-2}<br>")
        duration = df['Elapsed Time (s)'].max() / 60 if 'Elapsed Time (s)' in df.columns else 0
        html_parts.append(f"<b>Duração total:</b> {duration:.1f} minutos</p>")
        
        # 2. Resumo estatístico (média, min, max, std)
        html_parts.append("<h2>Resumo Estatístico</h2>")
        html_parts.append(df.describe().to_html(classes='stats-table', float_format="%.2f"))
        
        # 3. Gráficos principais
        html_parts.append("<h2>Gráficos</h2>")
        for config in charts.values():
            chart_manager = ChartManager()
            fig = chart_manager.create_chart(df, config)
            if fig:
                fig_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
                html_parts.append(f"<h3>{config['title']}</h3>{fig_html}")
        
        # 4. Possíveis alertas automáticos (simples)
        html_parts.append("<h2>Notas Automáticas</h2>")
        if (df.isnull().sum().sum()) > 0:
            html_parts.append("<p style='color:red;'>⚠️ Dados ausentes detectados em alguns parâmetros.</p>")
        else:
            html_parts.append("<p>✅ Nenhum dado ausente detectado.</p>")

        # 5. Interpretações automáticas
        html_parts.append("<h2>Interpretações Automáticas</h2>")
        for interp in self.generate_automatic_interpretations(df):
            html_parts.append(f"<p>{interp}</p>")

        # 6. Finalização
        html_parts.append("<hr><p style='text-align:center;'>Relatório gerado automaticamente pelo Enhanced Flight Data Analyzer Pro</p>")

        # 7. Junta tudo e salva
        full_html = "<html><head><title>Relatório de Ensaio em Voo</title></head><body>" + "".join(html_parts) + "</body></html>"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_html)
        return full_html

    def _generate_html_template(self) -> str:
        """Generate the HTML template for dashboard export."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2rem;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
        }
        .header p {
            margin: 0.5rem 0 0 0;
            font-size: 1.2rem;
            opacity: 0.9;
        }
        .metadata {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metadata h3 {
            margin-top: 0;
            color: #333;
        }
        .charts-container {
            display: grid;
            gap: 20px;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
        }
        .chart-wrapper {
            background: white;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .footer {
            text-align: center;
            margin-top: 2rem;
            padding: 1rem;
            color: #666;
            font-size: 0.9rem;
        }
        @media (max-width: 768px) {
            .charts-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>✈️ Flight Data Analysis Dashboard</h1>
        <p>Interactive flight test data visualization</p>
    </div>
    
    <div class="metadata">
        <h3>📊 Dashboard Information</h3>
        <pre id="metadata-content">{{METADATA}}</pre>
    </div>
    
    <div class="charts-container">
        {{CHARTS_SECTION}}
    </div>
    
    <div class="footer">
        <p>Generated by Enhanced Flight Data Analyzer Pro | Export Date: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    </div>
    
    <script>
        // Add any custom JavaScript for interactivity
        console.log('Flight Data Dashboard loaded successfully');
        
        // Add print functionality
        function printDashboard() {
            window.print();
        }
        
        // Add keyboard shortcuts
        document.addEventListener('keydown', function(event) {
            if (event.ctrlKey && event.key === 'p') {
                event.preventDefault();
                printDashboard();
            }
        });
    </script>
</body>
</html>
        """
    
    def export_chart_image(self, fig: go.Figure, filename: str, format: str = 'png', 
                          width: int = 1200, height: int = 800) -> bytes:
        """
        Export a single chart as an image.
        
        Args:
            fig: Plotly figure object
            filename: Name for the exported file
            format: Image format ('png', 'svg', 'pdf')
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            Image data as bytes
        """
        try:
            if format.lower() == 'png':
                img_bytes = pio.to_image(fig, format='png', width=width, height=height)
            elif format.lower() == 'svg':
                img_bytes = pio.to_image(fig, format='svg', width=width, height=height)
            elif format.lower() == 'pdf':
                img_bytes = pio.to_image(fig, format='pdf', width=width, height=height)
            else:
                img_bytes = pio.to_image(fig, format='png', width=width, height=height)
            
            return img_bytes
            
        except Exception as e:
            st.error(f"Error exporting chart image: {e}")
            return b""
    
    def export_data_csv(self, df: pd.DataFrame, include_metadata: bool = True) -> str:
        """
        Export data as CSV with optional metadata.
        
        Args:
            df: DataFrame to export
            include_metadata: Whether to include metadata header
            
        Returns:
            CSV content as string
        """
        try:
            output = io.StringIO()
            
            if include_metadata:
                # Add metadata header
                output.write(f"# Flight Data Export\n")
                output.write(f"# Export Date: {datetime.now().isoformat()}\n")
                output.write(f"# Data Points: {len(df)}\n")
                output.write(f"# Parameters: {len(df.columns)}\n")
                output.write(f"# Duration: {df['Elapsed Time (s)'].max():.2f} seconds\n")
                output.write("#\n")
            
            # Export data
            df.to_csv(output, index=False)
            
            return output.getvalue()
            
        except Exception as e:
            st.error(f"Error exporting CSV: {e}")
            return ""
    
    def export_data_excel(self, df: pd.DataFrame, charts_config: Dict[str, Any] = None) -> bytes:
        """
        Export data as Excel workbook with multiple sheets.
        
        Args:
            df: DataFrame to export
            charts_config: Chart configurations to include as metadata
            
        Returns:
            Excel file as bytes
        """
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='Flight Data', index=False)
                
                # Statistics sheet
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    stats_df = df[numeric_cols].describe()
                    stats_df.to_excel(writer, sheet_name='Statistics')
                
                # Metadata sheet
                metadata = {
                    'Export Date': [datetime.now().isoformat()],
                    'Data Points': [len(df)],
                    'Parameters': [len(df.columns)],
                    'Duration (seconds)': [df['Elapsed Time (s)'].max() if 'Elapsed Time (s)' in df.columns else 0],
                    'Sampling Rate (Hz)': [1.0 / df['Elapsed Time (s)'].diff().median() if 'Elapsed Time (s)' in df.columns else 0]
                }
                metadata_df = pd.DataFrame(metadata)
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
                
                # Chart configurations sheet
                if charts_config:
                    charts_data = []
                    for chart_id, config in charts_config.items():
                        charts_data.append({
                            'Chart ID': chart_id,
                            'Title': config.get('title', ''),
                            'Type': config.get('type', ''),
                            'Parameters': ', '.join(config.get('parameters', [])),
                            'X-Axis': config.get('x_axis', ''),
                            'Y-Axis Label': config.get('y_axis_label', ''),
                            'Color Scheme': config.get('color_scheme', '')
                        })
                    
                    if charts_data:
                        charts_df = pd.DataFrame(charts_data)
                        charts_df.to_excel(writer, sheet_name='Chart Configurations', index=False)
            
            return output.getvalue()
            
        except Exception as e:
            st.error(f"Error exporting Excel: {e}")
            return b""
    
    def export_data_json(self, df: pd.DataFrame, charts_config: Dict[str, Any] = None) -> str:
        """
        Export data as JSON with metadata.
        
        Args:
            df: DataFrame to export
            charts_config: Chart configurations to include
            
        Returns:
            JSON content as string
        """
        try:
            export_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'data_points': len(df),
                    'parameters': len(df.columns),
                    'duration_seconds': df['Elapsed Time (s)'].max() if 'Elapsed Time (s)' in df.columns else 0,
                    'columns': df.columns.tolist()
                },
                'data': df.to_dict('records')
            }
            
            if charts_config:
                export_data['charts_configuration'] = charts_config
            
            return json.dumps(export_data, indent=2, default=str)
            
        except Exception as e:
            st.error(f"Error exporting JSON: {e}")
            return ""
    
    def create_flight_report(self, df: pd.DataFrame, charts: Dict[str, Any], 
                           report_title: str = "Flight Test Analysis Report") -> str:
        """
        Create a comprehensive flight test report.
        
        Args:
            df: DataFrame containing flight data
            charts: Chart configurations
            report_title: Title for the report
            
        Returns:
            HTML report content
        """
        try:
            # Calculate summary statistics
            numeric_cols = df.select_dtypes(include=['number']).columns
            summary_stats = {}
            
            for col in numeric_cols:
                if col not in ['Elapsed Time (s)']:
                    summary_stats[col] = {
                        'mean': df[col].mean(),
                        'std': df[col].std(),
                        'min': df[col].min(),
                        'max': df[col].max(),
                        'range': df[col].max() - df[col].min()
                    }
            
            # Generate report HTML
            report_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report_title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
        .section {{ margin: 30px 0; }}
        .stats-table {{ width: 100%; border-collapse: collapse; }}
        .stats-table th, .stats-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .stats-table th {{ background-color: #f2f2f2; }}
        .chart-section {{ page-break-inside: avoid; margin: 30px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{report_title}</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>Flight Data Summary</h2>
        <ul>
            <li>Data Points: {len(df)}</li>
            <li>Parameters: {len(df.columns) - 2}</li>
            <li>Duration: {df['Elapsed Time (s)'].max():.2f} seconds</li>
            <li>Charts Generated: {len(charts)}</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Parameter Statistics</h2>
        <table class="stats-table">
            <tr>
                <th>Parameter</th>
                <th>Mean</th>
                <th>Std Dev</th>
                <th>Min</th>
                <th>Max</th>
                <th>Range</th>
            </tr>
            """
            
            for param, stats in summary_stats.items():
                report_html += f"""
            <tr>
                <td>{param}</td>
                <td>{stats['mean']:.3f}</td>
                <td>{stats['std']:.3f}</td>
                <td>{stats['min']:.3f}</td>
                <td>{stats['max']:.3f}</td>
                <td>{stats['range']:.3f}</td>
            </tr>
                """
            
            report_html += """
        </table>
    </div>
    
    <div class="section">
        <h2>Chart Configurations</h2>
        <table class="stats-table">
            <tr>
                <th>Chart</th>
                <th>Type</th>
                <th>Parameters</th>
            </tr>
            """
            
            for chart_id, config in charts.items():
                params = ', '.join(config.get('parameters', []))
                report_html += f"""
            <tr>
                <td>{config.get('title', chart_id)}</td>
                <td>{config.get('type', 'line')}</td>
                <td>{params}</td>
            </tr>
                """
            
            report_html += """
        </table>
    </div>
    
    <div class="section">
        <h2>Data Quality Assessment</h2>
        <ul>
            """
            
            # Data quality checks
            missing_data = df.isnull().sum()
            if missing_data.sum() > 0:
                report_html += f"<li>Missing values detected in {missing_data[missing_data > 0].count()} parameters</li>"
            else:
                report_html += "<li>No missing values detected</li>"
            
            # Check for constant values
            constant_params = []
            for col in numeric_cols:
                if col not in ['Elapsed Time (s)'] and df[col].nunique() == 1:
                    constant_params.append(col)
            
            if constant_params:
                report_html += f"<li>Constant values detected in: {', '.join(constant_params)}</li>"
            else:
                report_html += "<li>No constant value parameters detected</li>"
            
            report_html += """
        </ul>
    </div>
    
    <div class="section">
        <h2>Analysis Notes</h2>
        <p>This report was automatically generated from flight test data. 
        Please review the data quality assessment and verify parameter ranges 
        are within expected limits for your specific aircraft and test conditions.</p>
    </div>
    
</body>
</html>
            """
            
            return report_html
            
        except Exception as e:
            st.error(f"Error creating flight report: {e}")
            return ""
    
    def get_export_formats(self) -> Dict[str, str]:
        """Get available export formats."""
        return self.export_formats
    
    def validate_export_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate data before export and return validation results.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Validation results dictionary
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'info': []
        }
        
        # Check if DataFrame is empty
        if df.empty:
            validation['is_valid'] = False
            validation['errors'].append("DataFrame is empty")
            return validation
        
        # Check for required columns
        if 'Elapsed Time (s)' not in df.columns:
            validation['warnings'].append("Elapsed Time column not found")
        
        # Check for numeric data
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            validation['warnings'].append("No numeric columns found")
        
        # Check data quality
        missing_data = df.isnull().sum()
        if missing_data.sum() > 0:
            validation['warnings'].append(f"Missing values found in {missing_data[missing_data > 0].count()} columns")
        
        # Add info
        validation['info'].append(f"Data points: {len(df)}")
        validation['info'].append(f"Parameters: {len(df.columns)}")
        validation['info'].append(f"Numeric parameters: {len(numeric_cols)}")
        
        return validation

