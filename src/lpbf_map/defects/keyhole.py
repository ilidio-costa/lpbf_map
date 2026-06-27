from .base import DefectCriterion

class KeyholeCriterion(DefectCriterion):
    """
    Geometric Ratio criterion for Keyhole porosity.
    Returns True if the melt pool is too deep relative to its width (W/D < threshold).
    """
    def __init__(self, threshold: float = 2.3):
        self.threshold = threshold
        
    def check(self, melt_pool, idx: tuple) -> bool:
        width = float(melt_pool.width[idx])
        depth = float(melt_pool.depth[idx])
        
        if depth == 0:
            return False # No depth means no keyhole
            
        return (width / depth) < self.threshold
