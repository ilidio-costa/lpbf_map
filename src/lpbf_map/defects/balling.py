from .base import DefectCriterion
from typing import Tuple
from ..meltpool import MeltPool

class BallingPlateauRayleighCriterion(DefectCriterion):
    """
    Plateau-Rayleigh capillary instability criterion for Balling.
    Returns True if the melt track length-to-width ratio exceeds the threshold.
    """
    def __init__(self, threshold: float = 2.3):
        self.threshold = threshold
        
    def check(self, melt_pool: MeltPool, idx: Tuple[int, ...]) -> bool:
        length = float(melt_pool.length[idx] if melt_pool.is_vectorized else melt_pool.length)
        width = float(melt_pool.width[idx] if melt_pool.is_vectorized else melt_pool.width)
        
        if width == 0:
            return True
            
        return (length / width) >= self.threshold
