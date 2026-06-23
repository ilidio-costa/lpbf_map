import pytest
import numpy as np
from lpbf_maps.parameters import ProcessParameters

def test_parameters_initialization_single():
    params = ProcessParameters(
        laser_power=200,
        scan_speed=1.0,
        beam_radius=50e-6
    )
    assert not params.is_vectorized
    assert params.laser_power == 200
    assert params.ambient_temperature == 298.0
    
def test_parameters_initialization_vectorized():
    P_grid = np.array([[100, 200], [100, 200]])
    v_grid = np.array([[0.5, 0.5], [1.0, 1.0]])
    
    params = ProcessParameters(
        laser_power=P_grid,
        scan_speed=v_grid,
        beam_radius=50e-6
    )
    assert params.is_vectorized
    
    # Extract point
    single = params.get_point((0, 1))
    assert not single.is_vectorized
    assert single.laser_power == 200
    assert single.scan_speed == 0.5

def test_parameters_invalid():
    with pytest.raises(ValueError, match="Laser power must be strictly positive"):
        ProcessParameters(laser_power=-50, scan_speed=1.0, beam_radius=50e-6)
