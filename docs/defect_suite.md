# Defect Suite API

The `lpbf_maps` package uses a highly modular plugin system for evaluating printability defects. Instead of hardcoding complex conditional logic into a central loop, the library uses the **DefectSuite** to orchestrate independent **DefectCriterion** plugins.

This design gives you the freedom to easily swap, combine, or invent new physical defect criteria without modifying the core simulation engine.

## 1. The `DefectCriterion` Base Class

Every defect model must inherit from the `DefectCriterion` base class. This class enforces a strict contract: your plugin must implement a `check(melt_pool, index)` method that returns `True` if the defect is present, and `False` if the region is safe.

```python
from abc import ABC, abstractmethod

class DefectCriterion(ABC):
    @abstractmethod
    def check(self, melt_pool, index: tuple) -> bool:
        """
        Evaluates the physics at a specific N-dimensional grid coordinate.
        Returns True if the defect condition is met.
        """
        pass
```

### Safely Accessing Properties

Because the `MeltPool` natively supports vectorized parameters and materials, it broadcasts properties to an N-dimensional grid. **Never** access arrays directly inside a criterion (e.g., `melt_pool.parameters.laser_power`). Doing so will return arrays instead of scalar values, leading to `ValueError: The truth value of an array is ambiguous.`

Always use the built-in `get_property(name, index)` method. This safely handles array broadcasting and returns the precise scalar physical value at the evaluation coordinate.

## 2. Writing a Custom Defect Plugin

To write your own physical rule, inherit from `DefectCriterion`, use `get_property` to extract local variables, and return a boolean.

Here is an example of a custom defect that checks if the local volumetric energy density exceeds a critical threshold:

```python
from lpbf_maps.defects.base import DefectCriterion

class ExcessiveEnergyCriterion(DefectCriterion):
    def __init__(self, max_energy_density: float = 1e9):
        self.max_energy_density = max_energy_density

    def check(self, melt_pool, index: tuple) -> bool:
        # 1. Safely extract local scalar parameters using the melt_pool API
        P = melt_pool.get_property('laser_power', index)
        v = melt_pool.get_property('scan_speed', index)
        h = melt_pool.get_property('hatch_spacing', index)
        t = melt_pool.get_property('layer_thickness', index)
        
        # 2. Evaluate physical model
        ved = P / (v * h * t)
        
        # 3. Return True if the defect is active
        return ved > self.max_energy_density
```

## 3. The `DefectSuite` and Priority IDs

The `DefectSuite` acts as the orchestrator. When you add criteria to the suite, you must assign each a **Priority ID** (an integer `> 0`). 

When evaluating a coordinate, the suite checks criteria in ascending order of their Priority ID (e.g., ID `1` is checked before ID `2`). As soon as a criterion returns `True`, the suite immediately assigns that ID to the coordinate and stops checking. If no criteria return `True`, the coordinate is assigned `0` (Safe).

```python
from lpbf_maps.defects.base import DefectSuite
from lpbf_maps.defects.lof import LackOfFusionCriterion
from lpbf_maps.defects.keyhole_gan import KeyholeGanCriterion

# Create the suite
suite = DefectSuite()

# Register plugins with unique Priority IDs
suite.add(priority_id=1, criterion=LackOfFusionCriterion())
suite.add(priority_id=2, criterion=KeyholeGanCriterion())
suite.add(priority_id=3, criterion=ExcessiveEnergyCriterion(max_energy_density=5e9))
```

This priority system ensures overlapping defects are resolved deterministically (the lower ID "masks" the higher ID in the final 2D printability map). To visualize the pure, unmasked region of each defect, use `space.plot_individual_defects()`.
