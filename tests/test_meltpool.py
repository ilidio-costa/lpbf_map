import pytest
from lpbf_map.materials import Material
from lpbf_map.parameters import ProcessParameters
from lpbf_map.meltpool import MeltPool

def test_melt_pool_initialization():
    mat = Material.from_library("Ti64")
    
    # Typical processing parameters for Ti64
    params = ProcessParameters(
        laser_power=250.0,
        scan_speed=1.0,
        beam_radius=50e-6
    )
    
    pool = MeltPool(material=mat, parameters=params)
    
    # Verify dimensions are calculated and non-zero
    assert pool.length > 0.0
    assert pool.width > 0.0
    assert pool.depth > 0.0

    # For Ti64 at 250W, 1m/s, we expect depth in the tens of microns range (e.g. > 1e-5)
    assert pool.depth > 1e-5
    assert pool.width > 1e-5

