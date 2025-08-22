import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from components.unit_utils import UnitDetector, detect_unit_mismatch


class TestUnitDetector:
    
    def setup_method(self):
        self.detector = UnitDetector()
    
    def test_extract_unit_from_parameter(self):
        """Test unit extraction from parameter names."""
        # Test cases with units in parentheses
        assert self.detector.extract_unit_from_parameter("Temperature (DGC)") == "DGC"
        assert self.detector.extract_unit_from_parameter("Angle (deg)") == "deg"
        assert self.detector.extract_unit_from_parameter("Force (N)") == "N"
        assert self.detector.extract_unit_from_parameter("Pressure (psi)") == "psi"
        
        # Test cases without units
        assert self.detector.extract_unit_from_parameter("Temperature") is None
        assert self.detector.extract_unit_from_parameter("Simple Parameter") is None
        
        # Test edge cases
        assert self.detector.extract_unit_from_parameter("Param ()") is None
        assert self.detector.extract_unit_from_parameter("") is None
    
    def test_get_unit_category(self):
        """Test unit category detection."""
        # Test time units
        assert self.detector.get_unit_category("s") == "time"
        assert self.detector.get_unit_category("sec") == "time"
        assert self.detector.get_unit_category("ms") == "time"
        
        # Test angle units
        assert self.detector.get_unit_category("deg") == "angle"
        assert self.detector.get_unit_category("rad") == "angle"
        
        # Test temperature units
        assert self.detector.get_unit_category("DGC") == "temperature"
        assert self.detector.get_unit_category("C") == "temperature"
        
        # Test force units
        assert self.detector.get_unit_category("N") == "force"
        assert self.detector.get_unit_category("lbf") == "force"
        
        # Test dimensionless
        assert self.detector.get_unit_category("") == "dimensionless"
        assert self.detector.get_unit_category(None) == "dimensionless"
        
        # Test unknown units
        assert self.detector.get_unit_category("unknown") is None
    
    def test_are_units_compatible(self):
        """Test unit compatibility checking."""
        # Same category - compatible
        assert self.detector.are_units_compatible("deg", "rad") == True
        assert self.detector.are_units_compatible("s", "ms") == True
        assert self.detector.are_units_compatible("N", "lbf") == True
        
        # Different categories - incompatible
        assert self.detector.are_units_compatible("deg", "s") == False
        assert self.detector.are_units_compatible("N", "DGC") == False
        
        # Identical units - compatible
        assert self.detector.are_units_compatible("deg", "deg") == True
        
        # Unknown units - only compatible if identical
        assert self.detector.are_units_compatible("xyz", "xyz") == True
        assert self.detector.are_units_compatible("xyz", "abc") == False
    
    def test_analyze_parameter_units(self):
        """Test parameter unit analysis."""
        parameters = [
            "Temperature (DGC)", 
            "Angle (deg)", 
            "Force (N)", 
            "Time (s)"
        ]
        
        analysis = self.detector.analyze_parameter_units(parameters)
        
        assert len(analysis) == 4
        assert analysis["Temperature (DGC)"]["unit"] == "DGC"
        assert analysis["Temperature (DGC)"]["category"] == "temperature"
        assert analysis["Angle (deg)"]["unit"] == "deg"
        assert analysis["Angle (deg)"]["category"] == "angle"
        assert analysis["Force (N)"]["unit"] == "N"
        assert analysis["Force (N)"]["category"] == "force"
        assert analysis["Time (s)"]["unit"] == "s"
        assert analysis["Time (s)"]["category"] == "time"
    
    def test_group_parameters_by_unit_compatibility(self):
        """Test parameter grouping by unit compatibility."""
        parameters = [
            "Temperature1 (DGC)",
            "Temperature2 (C)", 
            "Angle1 (deg)",
            "Angle2 (rad)",
            "Force (N)",
            "Pressure (psi)"
        ]
        
        groups = self.detector.group_parameters_by_unit_compatibility(parameters)
        
        # Should have 3 groups: temperature, angle, and individual force/pressure
        assert len(groups) == 4
        
        # Find temperature group
        temp_group = None
        angle_group = None
        for group in groups:
            if "Temperature1 (DGC)" in group:
                temp_group = group
            elif "Angle1 (deg)" in group:
                angle_group = group
        
        assert temp_group is not None
        assert angle_group is not None
        assert len(temp_group) == 2  # Both temperature parameters
        assert len(angle_group) == 2  # Both angle parameters
    
    def test_get_base_parameter_name(self):
        """Test base parameter name extraction."""
        assert self.detector._get_base_parameter_name("Temperature (DGC)") == "Temperature"
        assert self.detector._get_base_parameter_name("Angle (deg)") == "Angle"
        assert self.detector._get_base_parameter_name("Simple Parameter") == "Simple Parameter"
        assert self.detector._get_base_parameter_name("") == ""


class TestDetectUnitMismatch:
    
    def test_detect_unit_mismatch_with_mismatched_units(self):
        """Test mismatch detection with different unit categories."""
        parameters = [
            "Temperature (DGC)",
            "Angle (deg)", 
            "Force (N)"
        ]
        
        result = detect_unit_mismatch(parameters)
        
        assert result['has_mismatch'] == True
        assert result['needs_dual_axis'] == True
        assert len(result['parameter_groups']) == 3  # Each parameter in its own group
        assert len(result['unique_categories']) == 3
    
    def test_detect_unit_mismatch_with_compatible_units(self):
        """Test mismatch detection with compatible units."""
        parameters = [
            "Temperature1 (DGC)",
            "Temperature2 (C)"
        ]
        
        result = detect_unit_mismatch(parameters)
        
        assert result['has_mismatch'] == False
        assert result['needs_dual_axis'] == False
        assert len(result['parameter_groups']) == 1  # All in one group
        assert len(result['unique_categories']) == 1
    
    def test_detect_unit_mismatch_mixed_scenario(self):
        """Test mismatch detection with mixed compatible/incompatible units."""
        parameters = [
            "Temperature1 (DGC)",
            "Temperature2 (C)",
            "Angle (deg)",
            "Force (N)"
        ]
        
        result = detect_unit_mismatch(parameters)
        
        assert result['has_mismatch'] == True
        assert result['needs_dual_axis'] == True
        assert len(result['parameter_groups']) == 3  # Temperature group + individual angle + individual force
        assert len(result['unique_categories']) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])