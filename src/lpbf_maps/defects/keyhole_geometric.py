from .base import DefectCriterion
from typing import Tuple
from ..meltpool import MeltPool

class KeyholeGeometricCriterion(DefectCriterion):
    """
    Geometric Ratio criterion for Keyhole porosity.
    Returns True if the melt pool is too deep relative to its width (W/D < threshold).
    """
    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold
        
    def check(self, melt_pool: MeltPool, idx: Tuple[int, ...]) -> bool:
        depth = float(melt_pool.depth[idx] if melt_pool.is_vectorized else melt_pool.depth)
        beam_radius = melt_pool.get_property('beam_radius', idx)
        return depth > beam_radius * self.threshold
