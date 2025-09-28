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
Physical unit conversion utilities for spectral analysis.
"""

import numpy as np
from typing import Dict, Optional, Any
from .unit_utils import UnitDetector

class PhysicalUnitConverter:
    """
    Handles conversion of physical quantities to SI units for spectral analysis.
    """
    
    # Conversion factors to SI units
    CONVERSION_FACTORS = {
        # Acceleration conversions to m/s²
        'g': 9.80665,  # Standard gravity
        'm/s²': 1.0,
        'ft/s²': 0.3048,
        
        # Angular acceleration to rad/s²
        'deg/s²': np.pi / 180.0,
        'rad/s²': 1.0,
        
        # Pressure to Pa
        'psi': 6894.76,
        'bar': 100000.0,
        'mbar': 100.0,
        'hPa': 100.0,
        'Pa': 1.0,
        
        # Temperature to K (requires offset handling)
        'C': {'factor': 1.0, 'offset': 273.15},
        'F': {'factor': 5.0/9.0, 'offset': 459.67 * 5.0/9.0},
        'K': 1.0,
        
        # Angular velocity to rad/s
        'deg/s': np.pi / 180.0,
        'rad/s': 1.0,
        'RPM': np.pi / 30.0,
        
        # Velocity to m/s
        'kt': 0.514444,
        'mph': 0.44704,
        'km/h': 1.0/3.6,
        'ft/s': 0.3048,
        'm/s': 1.0,
    }
    
    # SI units for different physical quantities
    SI_UNITS = {
        'acceleration': 'm/s²',
        'angular_rate': 'rad/s',
        'pressure': 'Pa',
        'temperature': 'K',
        'velocity': 'm/s',
        'angle': 'rad',
        'frequency': 'Hz',
    }
    
    def __init__(self):
        self.unit_detector = UnitDetector()
    
    def should_convert_for_fft(self, unit: Optional[str], category: Optional[str]) -> bool:
        """
        Determine if a parameter should be converted to SI units for FFT analysis.
        
        Args:
            unit: The unit string
            category: The unit category from UnitDetector
            
        Returns:
            True if conversion is recommended for FFT analysis
        """
        if not unit or not category:
            return False
            
        # Convert these categories to SI for meaningful FFT analysis
        convert_categories = {
            'acceleration', 'angular_rate', 'pressure', 'velocity'
        }
        
        return category in convert_categories
    
    def convert_to_si(self, values: np.ndarray, unit: Optional[str], 
                      category: Optional[str]) -> tuple[np.ndarray, str]:
        """
        Convert values to SI units.
        
        Args:
            values: Input values array
            unit: Original unit
            category: Unit category
            
        Returns:
            Tuple of (converted_values, si_unit_string)
        """
        if not self.should_convert_for_fft(unit, category):
            return values, unit or ""
        
        normalized_unit = self.unit_detector.normalize_unit(unit)
        
        if normalized_unit not in self.CONVERSION_FACTORS:
            return values, unit or ""
        
        conversion = self.CONVERSION_FACTORS[normalized_unit]
        si_unit = self.SI_UNITS.get(category, unit or "")
        
        if isinstance(conversion, dict):
            # Handle temperature conversions with offset
            converted = values * conversion['factor'] + conversion['offset']
        else:
            # Simple multiplication
            converted = values * conversion
        
        return converted, si_unit
    
    def get_conversion_info(self, unit: Optional[str], category: Optional[str]) -> Dict[str, Any]:
        """
        Get information about the conversion that would be applied.
        Args:
            unit: Original unit
            category: Unit category        
        Returns:
            Dictionary with conversion details
        """
        if not self.should_convert_for_fft(unit, category):
            return {
                'should_convert': False,
                'original_unit': unit,
                'si_unit': unit,
                'conversion_factor': 1.0
            }
        
        normalized_unit = self.unit_detector.normalize_unit(unit)
        conversion = self.CONVERSION_FACTORS.get(normalized_unit, 1.0)
        si_unit = self.SI_UNITS.get(category, unit or "")
        
        factor = conversion if not isinstance(conversion, dict) else conversion['factor']
        
        return {
            'should_convert': True,
            'original_unit': unit,
            'si_unit': si_unit,
            'conversion_factor': factor,
            'has_offset': isinstance(conversion, dict)
        }