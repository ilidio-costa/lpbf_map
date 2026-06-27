from abc import ABC, abstractmethod
from typing import Tuple, Any

class DefectCriterion(ABC):
    """
    Abstract base class for a parametric defect.
    """
    @abstractmethod
    def check(self, melt_pool: Any, idx: Tuple[int, ...]) -> bool:
        """
        Evaluates whether the defect occurs at the specific N-dimensional grid coordinate.
        """
        pass

class DefectSuite:
    """
    Container for prioritizing and executing DefectCriteria over a MeltPool.
    """
    def __init__(self):
        self.criteria = []
        
    def add(self, priority_id: int, criterion: DefectCriterion):
        """
        Registers a defect with a priority ID. Lower ID = higher priority.
        """
        self.criteria.append((priority_id, criterion))
        # Sort by priority ID (lowest first)
        self.criteria.sort(key=lambda x: x[0])
        
    def evaluate(self, melt_pool: Any, idx: Tuple[int, ...]) -> int:
        """
        Checks all registered criteria at the given index. Returns the first matching defect ID, or 0 if Safe.
        """
        for priority_id, criterion in self.criteria:
            if criterion.check(melt_pool, idx):
                return priority_id
        return 0 # Safe Zone
