from components.unit_utils import detect_unit_mismatch

def test_unit_grouping_dual_axis_needed():
    params = ["Altitude (ft)", "Temperature (C)", "Airspeed (kt)"]
    info = detect_unit_mismatch(params)
    assert info["has_mismatch"]
    assert info["needs_dual_axis"]
    assert len(info["parameter_groups"]) >= 2

def test_unit_grouping_single_group():
    params = ["Pitch Angle (deg)", "Roll Angle (deg)", "Yaw Angle (deg)"]
    info = detect_unit_mismatch(params)
    assert not info["needs_dual_axis"]  # same category