from .base import DefectCriterion
from typing import Tuple
from ..meltpool import MeltPool

class BallingYadroitsevCriterion(DefectCriterion):
    """
    Yadroitsev criterion for Balling.
    Returns True if the melt track width is too narrow compared to the layer thickness.
    """
    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold
        
    def check(self, melt_pool: MeltPool, idx: Tuple[int, ...]) -> bool:
        width = float(melt_pool.width[idx] if melt_pool.is_vectorized else melt_pool.width)
        layer_thickness = melt_pool.get_property('layer_thickness', idx)
        
        if layer_thickness is None:
            return False
            
        if width == 0:
            return True
            
        return (width / layer_thickness) < self.threshold
