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
Layout Manager for Dashboard and Chart Arrangements
Manages different layout templates and chart arrangements for the dashboard.
"""
# Import required libraries
import streamlit as st
import json
from typing import Dict, List, Any, Tuple, Optional

class LayoutManager:
    """
    Manages dashboard layouts and chart arrangements.
    """
    
    def __init__(self):
        self.layout_templates = {
            "single": {
                "name": "Single Chart",
                "description": "One large chart taking full width",
                "grid": "1x1",
                "max_charts": 1
            },
            "side_by_side": {
                "name": "Side by Side",
                "description": "Two charts side by side",
                "grid": "1x2",
                "max_charts": 2
            },
            "quad": {
                "name": "2x2 Grid",
                "description": "Four charts in a 2x2 grid",
                "grid": "2x2",
                "max_charts": 4
            },
            "wide_grid": {
                "name": "3x2 Grid",
                "description": "Six charts in a 3x2 grid",
                "grid": "3x2",
                "max_charts": 6
            },
            "tall_grid": {
                "name": "2x3 Grid",
                "description": "Six charts in a 2x3 grid",
                "grid": "2x3",
                "max_charts": 6
            },
            "vertical": {
                "name": "Vertical Stack",
                "description": "Charts stacked vertically",
                "grid": "1x4",
                "max_charts": 4
            }
        }
    
    def get_layout_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available layout templates.
        Arguments:
            None
        Returns:
            Dictionary of layout templates
        """
        return self.layout_templates
    
    def create_layout_grid(self, layout_type: str, charts: List[Dict[str, Any]], 
                          chart_manager, df) -> None:
        """
        Create and display charts in the specified layout.
        
        Args:
            layout_type: Type of layout (e.g., "2x2", "1x2", etc.)
            charts: List of chart configurations
            chart_manager: ChartManager instance
            df: DataFrame containing the data
        Returns:
            None
        """
        if not charts:
            st.info("No charts to display. Add charts using the sidebar.")
            return
        
        if layout_type == "1x1":
            self._create_single_layout(charts, chart_manager, df)
        elif layout_type == "1x2":
            self._create_side_by_side_layout(charts, chart_manager, df)
        elif layout_type == "2x2":
            self._create_2x2_layout(charts, chart_manager, df)
        elif layout_type == "3x2":
            self._create_3x2_layout(charts, chart_manager, df)
        elif layout_type == "2x3":
            self._create_2x3_layout(charts, chart_manager, df)
        elif layout_type == "1x4":
            self._create_vertical_layout(charts, chart_manager, df)
        else:
            self._create_2x2_layout(charts, chart_manager, df)  # Default
    
    def _create_single_layout(self, charts: List[Dict[str, Any]], chart_manager, df) -> None:
        """Create single chart layout.
        Arguments:
            charts: List of chart configurations
            chart_manager: ChartManager instance
            df: DataFrame containing the data
        Returns:
            None
        """
        if len(charts) > 0:
            chart_config = charts[0]
            fig = chart_manager.create_chart(df, chart_config)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key=f"single_{chart_config['id']}")
    
    def _create_side_by_side_layout(self, charts: List[Dict[str, Any]], chart_manager, df) -> None:
        """Create side-by-side layout.
        Arguments:
            charts: List of chart configurations
            chart_manager: ChartManager instance
            df: DataFrame containing the data
        Returns:
            None
        """
        col1, col2 = st.columns(2)
        
        with col1:
            if len(charts) > 0:
                fig1 = chart_manager.create_chart(df, charts[0])
                if fig1:
                    st.plotly_chart(fig1, use_container_width=True, key=f"side1_{charts[0]['id']}")
        
        with col2:
            if len(charts) > 1:
                fig2 = chart_manager.create_chart(df, charts[1])
                if fig2:
                    st.plotly_chart(fig2, use_container_width=True, key=f"side2_{charts[1]['id']}")
    
    def _create_2x2_layout(self, charts: List[Dict[str, Any]], chart_manager, df) -> None:
        """Create 2x2 grid layout.
        Arguments:
            charts: List of chart configurations
            chart_manager: ChartManager instance
            df: DataFrame containing the data
        Returns:
            None      
        """
        # First row
        col1, col2 = st.columns(2)
        with col1:
            if len(charts) > 0:
                fig = chart_manager.create_chart(df, charts[0])
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"grid1_{charts[0]['id']}")
        
        with col2:
            if len(charts) > 1:
                fig = chart_manager.create_chart(df, charts[1])
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"grid2_{charts[1]['id']}")
        
        # Second row
        col3, col4 = st.columns(2)
        with col3:
            if len(charts) > 2:
                fig = chart_manager.create_chart(df, charts[2])
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"grid3_{charts[2]['id']}")
        
        with col4:
            if len(charts) > 3:
                fig = chart_manager.create_chart(df, charts[3])
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"grid4_{charts[3]['id']}")
    
    def _create_3x2_layout(self, charts: List[Dict[str, Any]], chart_manager, df) -> None:
        """Create 3x2 grid layout.
        Arguments:
            charts: List of chart configurations
            chart_manager: ChartManager instance
            df: DataFrame containing the data
        Returns:
            None
        
        """
        # First row
        col1, col2, col3 = st.columns(3)
        with col1:
            if len(charts) > 0:
                fig = chart_manager.create_chart(df, charts[0])
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"3x2_1_{charts[0]['id']}")
        
        with col2:
            if len(charts) > 1:
                fig = chart_manager.create_chart(df, charts[1])
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"3x2_2_{charts[1]['id']}")
        
        with col3:
            if len(charts) > 2:
                fig = chart_manager.create_chart(df, charts[2])
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"3x2_3_{charts[2]['id']}")
        
        # Second row
        col4, col5, col6 = st.columns(3)
        with col4:
            if len(charts) > 3:
                fig = chart_manager.create_chart(df, charts[3])
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"3x2_4_{charts[3]['id']}")
        
        with col5:
            if len(charts) > 4:
                fig = chart_manager.create_chart(df, charts[4])
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"3x2_5_{charts[4]['id']}")
        
        with col6:
            if len(charts) > 5:
                fig = chart_manager.create_chart(df, charts[5])
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"3x2_6_{charts[5]['id']}")
    
    def _create_2x3_layout(self, charts: List[Dict[str, Any]], chart_manager, df) -> None:
        """Create 2x3 grid layout.
        Arguments:
            charts: List of chart configurations
            chart_manager: ChartManager instance
            df: DataFrame containing the data
        Returns:
            None
        """
        for row in range(3):
            col1, col2 = st.columns(2)
            
            with col1:
                chart_idx = row * 2
                if chart_idx < len(charts):
                    fig = chart_manager.create_chart(df, charts[chart_idx])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, key=f"2x3_{chart_idx}_{charts[chart_idx]['id']}")
            
            with col2:
                chart_idx = row * 2 + 1
                if chart_idx < len(charts):
                    fig = chart_manager.create_chart(df, charts[chart_idx])
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, key=f"2x3_{chart_idx}_{charts[chart_idx]['id']}")
    
    def _create_vertical_layout(self, charts: List[Dict[str, Any]], chart_manager, df) -> None:
        """Create vertical stack layout.
        Arguments:
            charts: List of chart configurations
            chart_manager: ChartManager instance
            df: DataFrame containing the data
        Returns:
            None
        
        """
        for i, chart_config in enumerate(charts[:6]):  # Limit to 6 charts
            fig = chart_manager.create_chart(df, chart_config)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key=f"vert_{i}_{chart_config['id']}")
    
    def create_dashboard_template(self, template_name: str, df, chart_manager) -> List[Dict[str, Any]]:
        """
        Create predefined dashboard templates for common flight test analyses.
        
        Args:
            template_name: Name of the template to create
            df: DataFrame containing the flight data
            chart_manager: ChartManager instance
            
        Returns:
            List of chart configurations for the template
        """
        templates = {
            "control_surfaces": self._create_control_surfaces_template(df),
            "flight_angles": self._create_flight_angles_template(df),
            "forces_analysis": self._create_forces_template(df),
            "comprehensive": self._create_comprehensive_template(df)
        }
        
        return templates.get(template_name, [])
    
    def _create_control_surfaces_template(self, df) -> List[Dict[str, Any]]:
        """Create template for control surfaces analysis.
        Arguments:
            df: DataFrame containing the flight data
        Returns:
            List of chart configurations for control surfaces analysis        
        """
        charts = []
        
        # Find control surface parameters
        aileron_params = [col for col in df.columns if 'aileron' in col.lower()]
        elevator_params = [col for col in df.columns if 'elevator' in col.lower()]
        rudder_params = [col for col in df.columns if 'rudder' in col.lower()]
        flap_params = [col for col in df.columns if 'flap' in col.lower()]
        
        chart_id = 0
        
        if aileron_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Aileron Control',
                'type': 'line',
                'parameters': aileron_params[:3],  # Limit to 3 parameters
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Deflection (deg)',
                'color_scheme': 'blues'
            })
            chart_id += 1
        
        if elevator_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Elevator Control',
                'type': 'line',
                'parameters': elevator_params[:3],
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Deflection (deg)',
                'color_scheme': 'reds'
            })
            chart_id += 1
        
        if rudder_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Rudder Control',
                'type': 'line',
                'parameters': rudder_params[:3],
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Deflection (deg)',
                'color_scheme': 'greens'
            })
            chart_id += 1
        
        if flap_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Flap Position',
                'type': 'line',
                'parameters': flap_params[:3],
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Position (deg)',
                'color_scheme': 'purples'
            })
        
        return charts
    
    def _create_flight_angles_template(self, df) -> List[Dict[str, Any]]:
        """Create template for flight angles analysis.
        Arguments:
            df: DataFrame containing the flight data
        Returns:
            List of chart configurations for flight angles analysis
        
        """
        charts = []
        
        # Find angle parameters
        aoa_params = [col for col in df.columns if any(keyword in col.lower() for keyword in ['alpha', 'angle of attack', 'aoa'])]
        sideslip_params = [col for col in df.columns if any(keyword in col.lower() for keyword in ['beta', 'sideslip', 'betha'])]
        
        chart_id = 0
        
        if aoa_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Angle of Attack',
                'type': 'line',
                'parameters': aoa_params[:2],
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Angle (deg)',
                'color_scheme': 'viridis'
            })
            chart_id += 1
        
        if sideslip_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Sideslip Angle',
                'type': 'line',
                'parameters': sideslip_params[:2],
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Angle (deg)',
                'color_scheme': 'plasma'
            })
        
        return charts
    
    def _create_forces_template(self, df) -> List[Dict[str, Any]]:
        """Create template for forces analysis.
        Arguments:
            df: DataFrame containing the flight data
        Returns:
            List of chart configurations for forces analysis
        """
        charts = []
        
        # Find force parameters
        force_params = [col for col in df.columns if any(keyword in col.lower() for keyword in ['force', 'strain', 'load'])]
        
        if force_params:
            # Group forces by type
            longitudinal_forces = [col for col in force_params if 'longitudinal' in col.lower()]
            lateral_forces = [col for col in force_params if 'lateral' in col.lower()]
            other_forces = [col for col in force_params if col not in longitudinal_forces + lateral_forces]
            
            chart_id = 0
            
            if longitudinal_forces:
                charts.append({
                    'id': f'template_chart_{chart_id}',
                    'title': 'Longitudinal Forces',
                    'type': 'line',
                    'parameters': longitudinal_forces[:3],
                    'x_axis': 'Elapsed Time (s)',
                    'y_axis_label': 'Force (kg)',
                    'color_scheme': 'blues'
                })
                chart_id += 1
            
            if lateral_forces:
                charts.append({
                    'id': f'template_chart_{chart_id}',
                    'title': 'Lateral Forces',
                    'type': 'line',
                    'parameters': lateral_forces[:3],
                    'x_axis': 'Elapsed Time (s)',
                    'y_axis_label': 'Force (kg)',
                    'color_scheme': 'reds'
                })
                chart_id += 1
            
            if other_forces:
                charts.append({
                    'id': f'template_chart_{chart_id}',
                    'title': 'Other Forces',
                    'type': 'line',
                    'parameters': other_forces[:3],
                    'x_axis': 'Elapsed Time (s)',
                    'y_axis_label': 'Force (kg)',
                    'color_scheme': 'greens'
                })
        
        return charts
    
    def _create_comprehensive_template(self, df) -> List[Dict[str, Any]]:
        """Create comprehensive analysis template.
        Arguments:
            df: DataFrame containing the flight data
        Returns:    
            List of chart configurations for comprehensive analysis
        """
        charts = []
        chart_id = 0
        
        # Control surfaces overview
        control_params = [col for col in df.columns if any(keyword in col.lower() for keyword in ['aileron', 'elevator', 'rudder'])]
        if control_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Control Surfaces Overview',
                'type': 'line',
                'parameters': control_params[:4],
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Deflection (deg)',
                'color_scheme': 'viridis'
            })
            chart_id += 1
        
        # Flight angles
        angle_params = [col for col in df.columns if any(keyword in col.lower() for keyword in ['alpha', 'beta', 'angle'])]
        if angle_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Flight Angles',
                'type': 'line',
                'parameters': angle_params[:3],
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Angle (deg)',
                'color_scheme': 'plasma'
            })
            chart_id += 1
        
        # Forces
        force_params = [col for col in df.columns if any(keyword in col.lower() for keyword in ['force', 'strain'])]
        if force_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Force Measurements',
                'type': 'line',
                'parameters': force_params[:3],
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Force (kg)',
                'color_scheme': 'inferno'
            })
            chart_id += 1
        
        # Trim settings
        trim_params = [col for col in df.columns if 'trim' in col.lower()]
        if trim_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Trim Settings',
                'type': 'line',
                'parameters': trim_params[:3],
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Trim (deg)',
                'color_scheme': 'cividis'
            })
            chart_id += 1
        
        # Dual-axis example: Altitude vs Temperature
        altitude_params = [col for col in df.columns if any(keyword in col.lower() for keyword in ['altitude', 'height'])]
        temp_params = [col for col in df.columns if any(keyword in col.lower() for keyword in ['temp', 'temperature'])]
        
        if altitude_params and temp_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Altitude vs Temperature (Dual-Axis)',
                'type': 'line',
                'parameters': altitude_params[:2],
                'secondary_y_params': temp_params[:2],
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Altitude',
                'secondary_y_axis_label': 'Temperature',
                'color_scheme': 'magma'
            })
            chart_id += 1
        
        # Dual-axis example: Speed vs Engine parameters
        speed_params = [col for col in df.columns if any(keyword in col.lower() for keyword in ['speed', 'velocity', 'airspeed'])]
        engine_params = [col for col in df.columns if any(keyword in col.lower() for keyword in ['rpm', 'power', 'thrust', 'engine'])]
        
        if speed_params and engine_params:
            charts.append({
                'id': f'template_chart_{chart_id}',
                'title': 'Speed vs Engine (Dual-Axis)',
                'type': 'line',
                'parameters': speed_params[:2],
                'secondary_y_params': engine_params[:2],
                'x_axis': 'Elapsed Time (s)',
                'y_axis_label': 'Speed',
                'secondary_y_axis_label': 'Engine Parameters',
                'color_scheme': 'blues'
            })
        
        return charts
    
    def save_layout_config(self, config: Dict[str, Any], name: str) -> bool:
        """
        Save a layout configuration for future use.
        
        Args:
            config: Layout configuration dictionary
            name: Name to save the configuration under
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # In a real application, this would save to a database or file
            # For now, we'll store in session state
            if 'saved_layouts' not in st.session_state:
                st.session_state.saved_layouts = {}
            
            st.session_state.saved_layouts[name] = config
            return True
        except Exception as e:
            st.error(f"Error saving layout: {e}")
            return False
    
    def load_layout_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a saved layout configuration.
        
        Args:
            name: Name of the configuration to load
            
        Returns:
            Layout configuration dictionary or None if not found
        """
        try:
            if 'saved_layouts' in st.session_state:
                return st.session_state.saved_layouts.get(name)
            return None
        except Exception as e:
            st.error(f"Error loading layout: {e}")
            return None
    
    def get_saved_layouts(self) -> List[str]:
        """
        Get list of saved layout names.
        
        Returns:
            List of saved layout names
        """
        if 'saved_layouts' in st.session_state:
            return list(st.session_state.saved_layouts.keys())
        return []

    def _create_single_layout(self, charts, chart_manager, df):
        if len(charts) > 0:
            cfg = charts[0]
            fig = chart_manager.create_chart(df, cfg)
            if fig:
                chart_id = cfg.get("id", "chart0") if isinstance(cfg, dict) else cfg.id
                st.plotly_chart(fig, use_container_width=True, key=f"single_{chart_id}")
