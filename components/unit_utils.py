"""
Unit detection and handling utilities for flight data parameters.
"""
import re
from typing import Dict, List, Optional, Tuple, Set


class UnitDetector:
    """
    Utility class for detecting and parsing units from parameter names.
    """
    
    def __init__(self):
        # Common unit patterns for flight data
        self.unit_patterns = {
            # Time units
            'time': {'s', 'sec', 'second', 'seconds', 'ms', 'millisecond', 'milliseconds', 'min', 'minute', 'minutes', 'h', 'hr', 'hour', 'hours'},
            
            # Angular units
            'angle': {'deg', 'degree', 'degrees', 'rad', 'radian', 'radians', 'arc-deg', 'arc-min', 'arc-sec'},
            
            # Force/Load units
            'force': {'N', 'newton', 'newtons', 'lbf', 'lb', 'pound', 'pounds', 'kgf', 'kg-force'},
            
            # Acceleration units
            'acceleration': {'g', 'g-force', 'm/s2', 'm/s²', 'ft/s2', 'ft/s²'},
            
            # Pressure units
            'pressure': {'Pa', 'pascal', 'kPa', 'MPa', 'psi', 'psig', 'bar', 'atm', 'torr', 'mmHg'},
            
            # Temperature units
            'temperature': {'C', 'DGC', 'degC', 'celsius', 'F', 'degF', 'fahrenheit', 'K', 'kelvin'},
            
            # Speed/Velocity units
            'velocity': {'m/s', 'ft/s', 'kts', 'knots', 'mph', 'km/h', 'mach'},
            
            # Percentage/Ratio units
            'percentage': {'%', 'percent', 'ratio', 'fraction'},
            
            # Voltage/Current units
            'electrical': {'V', 'volt', 'volts', 'A', 'amp', 'amps', 'mA', 'mV'},
            
            # Frequency units
            'frequency': {'Hz', 'hertz', 'kHz', 'MHz', 'rpm', 'rev/min'},
            
            # Dimensionless
            'dimensionless': {'', 'ADM', 'count', 'index', 'flag', 'status'}
        }
        
        # Create reverse lookup for unit category
        self.unit_to_category = {}
        for category, units in self.unit_patterns.items():
            for unit in units:
                self.unit_to_category[unit.lower()] = category
    
    def extract_unit_from_parameter(self, param_name: str) -> Optional[str]:
        """
        Extract unit from parameter name like 'Parameter (unit)'.
        
        Args:
            param_name: Parameter name potentially containing units
            
        Returns:
            Extracted unit string or None if no unit found
        """
        # Look for units in parentheses
        match = re.search(r'\(([^)]*)\)$', param_name.strip())
        if match:
            unit = match.group(1).strip()
            return unit if unit else None
        
        # Look for units after a dash or space at the end
        match = re.search(r'[\s\-]([A-Za-z%/²]+)$', param_name.strip())
        if match:
            potential_unit = match.group(1).strip()
            # Only return if it looks like a valid unit (avoid false positives)
            if len(potential_unit) <= 6 and not potential_unit.isdigit():
                return potential_unit
        
        return None
    
    def get_unit_category(self, unit: str) -> Optional[str]:
        """
        Get the category of a unit (e.g., 'time', 'angle', 'force').
        
        Args:
            unit: Unit string
            
        Returns:
            Unit category or None if not recognized
        """
        if not unit:
            return 'dimensionless'
        
        unit_lower = unit.lower()
        return self.unit_to_category.get(unit_lower)
    
    def are_units_compatible(self, unit1: str, unit2: str) -> bool:
        """
        Check if two units are compatible (same category).
        
        Args:
            unit1: First unit
            unit2: Second unit
            
        Returns:
            True if units are compatible, False otherwise
        """
        cat1 = self.get_unit_category(unit1)
        cat2 = self.get_unit_category(unit2)
        
        # Both unknown units are considered incompatible
        if cat1 is None and cat2 is None:
            return unit1 == unit2  # Only compatible if identical
        
        return cat1 == cat2
    
    def analyze_parameter_units(self, parameters: List[str]) -> Dict[str, Dict[str, any]]:
        """
        Analyze units for a list of parameters.
        
        Args:
            parameters: List of parameter names
            
        Returns:
            Dictionary with unit analysis for each parameter
        """
        analysis = {}
        
        for param in parameters:
            unit = self.extract_unit_from_parameter(param)
            category = self.get_unit_category(unit)
            
            analysis[param] = {
                'unit': unit,
                'category': category,
                'base_name': self._get_base_parameter_name(param)
            }
        
        return analysis
    
    def group_parameters_by_unit_compatibility(self, parameters: List[str]) -> List[List[str]]:
        """
        Group parameters by unit compatibility.
        
        Args:
            parameters: List of parameter names
            
        Returns:
            List of groups, where each group contains parameters with compatible units
        """
        analysis = self.analyze_parameter_units(parameters)
        groups = []
        grouped_params = set()
        
        for param in parameters:
            if param in grouped_params:
                continue
                
            # Start a new group
            group = [param]
            grouped_params.add(param)
            param_category = analysis[param]['category']
            
            # Find other parameters with compatible units
            for other_param in parameters:
                if (other_param not in grouped_params and 
                    other_param != param and
                    analysis[other_param]['category'] == param_category):
                    group.append(other_param)
                    grouped_params.add(other_param)
            
            groups.append(group)
        
        return groups
    
    def _get_base_parameter_name(self, param_name: str) -> str:
        """
        Get the base parameter name without units.
        
        Args:
            param_name: Full parameter name
            
        Returns:
            Base parameter name without units
        """
        # Remove units in parentheses
        base = re.sub(r'\s*\([^)]*\)$', '', param_name.strip())
        
        # Only remove units after dash/space if it's a single "word" that looks like a unit
        potential_base = re.sub(r'[\s\-]([A-Za-z%/²]{1,6})$', '', base.strip())
        
        # Only apply this removal if the removed part was likely a unit (short, no spaces)
        removed_part_match = re.search(r'[\s\-]([A-Za-z%/²]{1,6})$', base.strip())
        if removed_part_match:
            removed_part = removed_part_match.group(1)
            # Only remove if it looks like a unit (short and no internal spaces)
            if len(removed_part) <= 6 and ' ' not in removed_part:
                base = potential_base
        
        return base.strip() or param_name.strip()


def detect_unit_mismatch(parameters: List[str]) -> Dict[str, any]:
    """
    Detect unit mismatches in a list of parameters.
    
    Args:
        parameters: List of parameter names
        
    Returns:
        Dictionary with mismatch analysis
    """
    detector = UnitDetector()
    analysis = detector.analyze_parameter_units(parameters)
    groups = detector.group_parameters_by_unit_compatibility(parameters)
    
    # Identify mismatches
    has_mismatch = len(groups) > 1
    unique_categories = set()
    unique_units = set()
    
    for param in parameters:
        unit_info = analysis[param]
        if unit_info['category']:
            unique_categories.add(unit_info['category'])
        if unit_info['unit']:
            unique_units.add(unit_info['unit'])
    
    return {
        'has_mismatch': has_mismatch,
        'parameter_groups': groups,
        'unique_categories': list(unique_categories),
        'unique_units': list(unique_units),
        'parameter_analysis': analysis,
        'needs_dual_axis': has_mismatch and len(unique_categories) > 1
    }