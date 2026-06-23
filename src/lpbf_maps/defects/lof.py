import numpy as np
from .base import DefectCriterion

class LackOfFusionCriterion(DefectCriterion):
    """
    Geometric Overlap criterion for Lack of Fusion.
    Returns True if voids form between adjacent tracks.
    """
    def check(self, melt_pool, idx: tuple) -> bool:
        depth = float(melt_pool.depth[idx] if melt_pool.is_vectorized else melt_pool.depth)
        width = float(melt_pool.width[idx] if melt_pool.is_vectorized else melt_pool.width)
        
        layer_thickness = melt_pool.get_property('layer_thickness', idx)
        hatch_spacing = melt_pool.get_property('hatch_spacing', idx)
        
        if layer_thickness is None or hatch_spacing is None:
            return False

        if depth <= 1e-9 or width <= 1e-9:
            return True   

        if (hatch_spacing/width)**2 >= 1:
            return True 

        return layer_thickness > depth * np.sqrt(1 - (hatch_spacing/width)**2)
