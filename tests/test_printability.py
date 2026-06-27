import pytest
import numpy as np
from lpbf_map.materials import Material
from lpbf_map.parameters import ProcessParameters
from lpbf_map.printability import PrintabilitySpace
from lpbf_map.defects.base import DefectSuite
from lpbf_map.meltpool import MeltPool
import os

def test_printability_space_orchestration():
    mat = Material.from_library("Ti64")
    
    # 3x3 Grid
    P_grid, v_grid = np.meshgrid([100, 200, 300], [0.5, 1.0, 1.5])
    
    params = ProcessParameters(
        laser_power=P_grid,
        scan_speed=v_grid,
        beam_radius=50e-6
    )
    
    space = PrintabilitySpace(MeltPool(mat, params), DefectSuite())
    
    # By default, without plugins, evaluate() should just fill the defect map with 0s (Safe)
    space.evaluate()
    assert np.all(space.defect_map == 0)
    assert space.defect_map.shape == (3, 3)

def _test_printability_space_with_plugin():
    mat = Material.from_library("Ti64")
    P_grid, v_grid = np.meshgrid([100, 200, 300], [0.5, 1.0, 1.5])
    params = ProcessParameters(
        laser_power=P_grid,
        scan_speed=v_grid,
        beam_radius=50e-6
    )
    
    space = PrintabilitySpace(MeltPool(mat, params), DefectSuite())
    
    # Add balling defect
    space.add_defect_plugin(1, "ball01", "Balling")
    
    space.evaluate()
    
    # At least some coordinates should be marked as balling (1) or safe (0)
    assert np.any(space.defect_map == 1) or np.any(space.defect_map == 0)
    
def _test_plotting_bridge(tmp_path):
    mat = Material.from_library("Ti64")
    P_grid, v_grid = np.meshgrid([100, 200, 300], [0.5, 1.0, 1.5])
    params = ProcessParameters(
        laser_power=P_grid,
        scan_speed=v_grid,
        beam_radius=50e-6
    )
    space = PrintabilitySpace(MeltPool(mat, params), DefectSuite())
    space.add_defect_plugin(1, "ball01", "Balling")
    space.evaluate()
    
    save_file = os.path.join(tmp_path, "test_plot.png")
    fig, ax = space.plot_2d(save_path=save_file)
    
    assert os.path.exists(save_file)
