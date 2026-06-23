from .base import DefectCriterion
from typing import Tuple
from ..meltpool import MeltPool

class LackOfFusionDepthRatioCriterion(DefectCriterion):
    """
    Depth-to-Layer-Thickness Ratio criterion for Lack of Fusion.
    Returns True if the melt pool depth does not sufficiently penetrate the layer thickness.
    """
    def __init__(self, threshold: float = 1.5):
        self.threshold = threshold
        
    def check(self, melt_pool: MeltPool, idx: Tuple[int, ...]) -> bool:
        depth = float(melt_pool.depth[idx] if melt_pool.is_vectorized else melt_pool.depth)
        layer_thickness = melt_pool.get_property('layer_thickness', idx)
        
        if layer_thickness is None:
            return False
            
        if layer_thickness == 0:
            return False
            
        return (depth / layer_thickness) < self.threshold
