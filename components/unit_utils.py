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
Unit detection and handling utilities for flight data parameters.
"""

import re
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict


# ----------------------------
# Normalization Maps
# ----------------------------

UNIT_SYNONYMS = {
    # Temperature
    "degc": "C",
    "dgc": "C",
    "celsius": "C",
    "c": "C",
    "degf": "F",
    "fahrenheit": "F",
    # Angle
    "deg": "deg",
    "degree": "deg",
    "degrees": "deg",
    "rad": "rad",
    "radian": "rad",
    "radians": "rad",
    # Speed / velocity
    "kts": "kt",
    "kt": "kt",
    "knots": "kt",
    "knot": "kt",
    "mph": "mph",
    "km/h": "km/h",
    "mps": "m/s",
    # Pressure
    "psi": "psi",
    "psig": "psi",  # treat gauge same for grouping
    "psid": "psi",  # differential — decide if you want separate
    "mbar": "mbar",
    "hpa": "hPa",
    "inhg": "inHg",
    # Length / altitude
    "ft": "ft",
    "feet": "ft",
    # Rates
    "ft/min": "ft/min",
    "kt/s": "kt/s",
    # Acceleration
    "g": "g",
    "m/s2": "m/s²",
    "m/s²": "m/s²",
    "ft/s2": "ft/s²",
    "ft/s²": "ft/s²",
    "deg/s": "deg/s",
    # Frequency / rotation
    "hz": "Hz",
    "rpm": "RPM",
    # Electrical
    "vdc": "V",
    "v": "V",
    "volt": "V",
    "volts": "V",
    "a": "A",
    "amp": "A",
    "amps": "A",
    "ma": "mA",
    "mv": "mV",
    # Energy / capacity
    "ah": "Ah",
    # Mass / force / weight
    "kg": "kg",
    "kgf": "kgf",
    # Percentage
    "%": "%",
    "percent": "%",
    # Dimensionless placeholders
    "adm": "ADM"
}

# Categories map normalized units to a conceptual category
UNIT_CATEGORIES = {
    # Temperature
    "C": "temperature", "F": "temperature", "K": "temperature",
    # Angle & angular rate
    "deg": "angle", "rad": "angle", "deg/s": "angular_rate",
    # Kinematic
    "m/s": "velocity", "ft/s": "velocity", "kt": "velocity",
    "km/h": "velocity", "mph": "velocity", "mach": "velocity",
    "ft/min": "vertical_rate", "kt/s": "accel_derived",
    # Acceleration
    "g": "acceleration", "m/s²": "acceleration", "ft/s²": "acceleration",
    # Pressure
    "psi": "pressure", "mbar": "pressure", "hPa": "pressure",
    "inHg": "pressure", "bar": "pressure", "atm": "pressure",
    # Frequency / rotation
    "Hz": "frequency", "kHz": "frequency", "MHz": "frequency", "RPM": "frequency",
    # Electrical
    "V": "electrical", "mV": "electrical", "A": "electrical", "mA": "electrical",
    # Capacity / energy related
    "Ah": "capacity",
    # Mass / forces (rough grouping)
    "kg": "mass", "kgf": "force", "N": "force", "lbf": "force",
    # Percentage / ratio
    "%": "percentage",
    # Dimensionless / flags
    "ADM": "dimensionless", "": "dimensionless"
}

# Pattern for extracting a trailing parenthetical unit
PAREN_UNIT_RE = re.compile(r"\(([^)]+)\)\s*$")
# Fallback simple trailing token pattern
TRAILING_TOKEN_RE = re.compile(r'[\s\-]([A-Za-z%/°²³0-9]+)$')


class UnitDetector:
    """
    Detects, normalizes, categorizes units, and groups parameters by unit compatibility.
    """

    def extract_unit_from_parameter(self, param_name: str) -> Optional[str]:
        """Extract raw unit (without normalization) from a parameter label."""
        name = param_name.strip()
        m = PAREN_UNIT_RE.search(name)
        if m:
            raw = m.group(1).strip()
            return raw or None

        # Fallback: last token heuristic
        m2 = TRAILING_TOKEN_RE.search(name)
        if m2:
            tok = m2.group(1).strip()
            # Heuristic: skip if token contains spaces (already filtered), or is too long
            if 0 < len(tok) <= 8 and not tok.isdigit():
                return tok
        return None

    def normalize_unit(self, unit: Optional[str]) -> Optional[str]:
        """
        Normalize a raw unit string to a canonical form using synonyms mapping.
        Returns None if input is None, otherwise normalized string.
        Arguments:
            unit: The raw unit string to normalize.
        Returns:
            The normalized unit string.
        """
        if unit is None:
            return None
        u = unit.strip()
        # unify unicode degree sign
        u = u.replace("°", "deg")
        key = u.lower()
        return UNIT_SYNONYMS.get(key, u)

    def get_unit_category(self, unit: Optional[str]) -> Optional[str]:
        """
        Get the category of a unit based on its normalized form.
        Returns None if input is None, otherwise the category string.
        Arguments:
            unit: The raw unit string to categorize.
        Returns:
            The category string.
        """
        if unit is None:
            return "dimensionless"
        normalized = self.normalize_unit(unit) or ""
        return UNIT_CATEGORIES.get(normalized, None)

    def are_units_compatible(self, unit1: Optional[str], unit2: Optional[str]) -> bool:
        """
        Determine if two raw unit strings are compatible (same category).
        If either unit is unknown, only treat as compatible if identical normalized forms.
        Arguments:
            unit1: First raw unit string.
            unit2: Second raw unit string.
        Returns:
            True if compatible, False otherwise.
        """
        cat1 = self.get_unit_category(unit1)
        cat2 = self.get_unit_category(unit2)
        if cat1 is None or cat2 is None:
            # Unknown categories: only treat compatible if identical normalized forms
            return (self.normalize_unit(unit1) == self.normalize_unit(unit2))
        return cat1 == cat2

    def _get_base_parameter_name(self, param_name: str) -> str:
        """
        Derive a base parameter name by stripping parenthetical units and trailing unit-like tokens.
        Arguments:
            param_name: The full parameter name.
        Returns:
            The base parameter name without unit indications.
        """
        # Remove parenthetical
        base = PAREN_UNIT_RE.sub('', param_name).strip()
        # If trailing token looks like an extracted unit, optionally strip it
        m = TRAILING_TOKEN_RE.search(base)
        if m:
            tok = m.group(1)
            # Only strip if recognized as a unit after normalization
            if self.get_unit_category(tok) is not None or self.normalize_unit(tok) != tok:
                base = base[:m.start()].strip()
        return base or param_name

    def analyze_parameter_units(self, parameters: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze a list of parameter names, extracting and normalizing units, categorizing them,
        and deriving base names.
        Returns a mapping from parameter name to its analysis info.
        Arguments:
            parameters: List of parameter names to analyze.
        Returns:
            Dictionary with analysis info for each parameter.
            Dictionary keys are parameter names, values are dictionaries with analysis info.
            Each analysis info dictionary has keys "raw_unit", "unit", "category", and "base_name".
        """

        analysis: Dict[str, Dict[str, Any]] = {}
        for p in parameters:
            raw_unit = self.extract_unit_from_parameter(p)
            normalized = self.normalize_unit(raw_unit)
            category = self.get_unit_category(raw_unit)
            analysis[p] = {
                "raw_unit": raw_unit,
                "unit": normalized,
                "category": category,
                "base_name": self._get_base_parameter_name(p)
            }
        return analysis

    def group_parameters_by_unit_compatibility(self, parameters: List[str]) -> List[List[str]]:
        """
        Group parameters by their unit compatibility.
        Returns a list of groups, each group being a list of parameter names.
        Arguments:
            parameters: List of parameter names to group.
        Returns:
            List of groups, each group is a list of parameter names.
        
        """
        analysis = self.analyze_parameter_units(parameters)
        # Map (category) -> list of params
        grouping: Dict[str, List[str]] = defaultdict(list)
        for p in parameters:
            cat = analysis[p]["category"] or f"__unknown__:{analysis[p]['unit']}"
            grouping[cat].append(p)

        # Deterministic ordering: sort categories then keep original parameter order within category
        ordered_groups = []
        for cat in sorted(grouping.keys()):
            ordered_group = [p for p in parameters if p in grouping[cat]]
            ordered_groups.append(ordered_group)
        return ordered_groups


def detect_unit_mismatch(parameters: List[str]) -> Dict[str, Any]:
    """
    High-level mismatch detection used by ChartManager.
    Returns structure:
        {
            'has_mismatch': bool,
            'parameter_groups': List[List[str]],
            'unique_categories': [...],
            'unique_units': [...],
            'parameter_analysis': {param: {...}},
            'needs_dual_axis': bool
        }
    Arguments:
        parameters: List of parameter names to analyze.
    Returns:
        Dictionary with mismatch analysis results.
    """
    detector = UnitDetector()
    analysis = detector.analyze_parameter_units(parameters)
    groups = detector.group_parameters_by_unit_compatibility(parameters)

    unique_categories: Set[str] = set()
    unique_units: Set[str] = set()
    for p in parameters:
        info = analysis[p]
        if info["category"]:
            unique_categories.add(info["category"])
        if info["unit"]:
            unique_units.add(info["unit"])

    has_mismatch = len(groups) > 1
    # Decide dual-axis necessity: at least 2 distinct semantic categories (exclude dimensionless only split)
    categories_no_dimless = [c for c in unique_categories if c != "dimensionless"]
    needs_dual = has_mismatch and len(categories_no_dimless) > 1

    return {
        "has_mismatch": has_mismatch,
        "parameter_groups": groups,
        "unique_categories": sorted(unique_categories),
        "unique_units": sorted(u for u in unique_units if u),
        "parameter_analysis": analysis,
        "needs_dual_axis": needs_dual
    }