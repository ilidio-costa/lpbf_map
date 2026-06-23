import numpy as np
from typing import Optional, Tuple, Dict, Any

from .meltpool import MeltPool
from .defects.base import DefectSuite

class PrintabilitySpace:
    """
    Master Orchestrator.
    Encapsulates the MeltPool and DefectSuite. Evaluates the defect map lazily.
    """
    def __init__(self, melt_pool: MeltPool, defect_suite: DefectSuite):
        self.melt_pool = melt_pool
        self.defect_suite = defect_suite
        self.defect_map: Optional[np.ndarray] = None
        
        # Store metadata for plotting
        self.defect_labels: Dict[int, str] = {0: "Safe"}
        
        # Auto-populate defect labels from the suite
        for priority_id, criterion in self.defect_suite.criteria:
            # e.g., 'LackOfFusionCriterion' -> 'LackOfFusion'
            label = criterion.__class__.__name__.replace("Criterion", "")
            self.defect_labels[priority_id] = label

    def evaluate(self):
        """
        Runs the parameter sweep across the N-dimensional grid, passing the pool's local context into the rule engine.
        """
        shape = self.melt_pool.shape
        self.defect_map = np.zeros(shape, dtype=int)
        
        if len(shape) == 0:
            # Single point evaluation
            self.defect_map = np.array(self.defect_suite.evaluate(self.melt_pool, ()))
            return

        for idx in np.ndindex(shape):
            # The suite queries the MeltPool dynamically
            status = self.defect_suite.evaluate(self.melt_pool, idx)
            self.defect_map[idx] = status

    def len(self, property_name: str) -> int:
        """
        Error-safe size check for a named parameter array in the evaluation grid.

        Standard Python `len()` raises a TypeError on 0-dimensional NumPy scalars,
        making it unreliable for inspecting mixed scalar/array grids.
        This method handles that case gracefully.

        Args:
            property_name: The name of the attribute to inspect.

        Returns:
            The size of the first dimension of the array, or 1 if scalar.
        """
        if hasattr(self.melt_pool.parameters, property_name):
            value = getattr(self.melt_pool.parameters, property_name)
        elif hasattr(self.melt_pool.material, property_name):
            value = getattr(self.melt_pool.material, property_name)
        else:
            raise ValueError(f"Property '{property_name}' not found in ProcessParameters or Material.")
        
        array = np.asarray(value)
        if array.ndim == 0:
            return 1
        return array.shape[0]

    def get_material_property(self, property_name: str) -> float:
        """
        Deep Traversal API for Material properties.
        Retrieves any named attribute from the associated Material object.
        """
        if hasattr(self.melt_pool.material, property_name):
            return getattr(self.melt_pool.material, property_name)
        raise ValueError(f"Property '{property_name}' not found in Material.")

    def get_parameter_value(self, name: str, index: tuple) -> float:
        """
        Deep Traversal & Inspection API.
        Extracts a physical value from the parameters at a specific N-dimensional index.
        """
        params = self.melt_pool.parameters.get_point(index)
        if hasattr(params, name):
            return getattr(params, name)
        raise ValueError(f"Parameter '{name}' not found in ProcessParameters.")

    def slice_2d(self, x_axis: str, y_axis: str, fixed_indices: Optional[dict] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Slices an N-dimensional grid down to a 2D plane for plotting via strict ijk indexing.
        fixed_indices is a dict mapping dimension index (0, 1, 2...) to the integer bin index.
        Returns: X_grid, Y_grid, defect_map_slice
        """
        if self.defect_map is None:
            self.evaluate()
            
        if fixed_indices is None:
            fixed_indices = {}
            
        shape = self.melt_pool.shape
        ndim = len(shape)
        
        if ndim < 2:
            raise ValueError("Parameters must be at least 2D to extract a 2D slice.")
            
        slice_obj = [slice(None)] * ndim
        for dim, bin_idx in fixed_indices.items():
            slice_obj[dim] = bin_idx
            
        slice_obj = tuple(slice_obj)
        
        def _get_raw(axis):
            if hasattr(self.melt_pool.parameters, axis):
                return getattr(self.melt_pool.parameters, axis)
            if hasattr(self.melt_pool.material, axis):
                return getattr(self.melt_pool.material, axis)
            raise ValueError(f"Property '{axis}' not found.")
            
        x_grid_raw = _get_raw(x_axis)
        y_grid_raw = _get_raw(y_axis)
        
        x_grid_full = np.broadcast_to(x_grid_raw, shape)
        y_grid_full = np.broadcast_to(y_grid_raw, shape)
        
        return x_grid_full[slice_obj], y_grid_full[slice_obj], self.defect_map[slice_obj]

    def plot_2d(self, x_axis: str, y_axis: str, fixed_indices: Optional[dict] = None, save_path: Optional[str] = None):
        """
        Plots a 2D printability map. Automatically extracts the grids and defect map slice.
        Axis labels are derived from the parameter names passed as x_axis and y_axis.
        """
        from .printability_plots import plot_2d_printability_map

        x_grid, y_grid, defect_slice = self.slice_2d(x_axis, y_axis, fixed_indices)

        # Build human-readable axis labels from the parameter names
        x_label = x_axis.replace('_', ' ').title()
        y_label = y_axis.replace('_', ' ').title()

        return plot_2d_printability_map(
            x_grid=x_grid,
            y_grid=y_grid,
            x_label=x_label,
            y_label=y_label,
            defect_map=defect_slice,
            defect_labels=self.defect_labels,
            save_path=save_path
        )

    def plot_individual_defects(self, x_axis: str, y_axis: str, fixed_indices: Optional[dict] = None, save_path: Optional[str] = None):
        """
        Plots an array of subplots, where each isolates a single defect criterion from the suite.
        """
        from .printability_plots import plot_individual_defects_map
        
        x_grid, y_grid, _ = self.slice_2d(x_axis, y_axis, fixed_indices)
        
        x_label = x_axis.replace('_', ' ').title()
        y_label = y_axis.replace('_', ' ').title()
        
        shape = self.melt_pool.shape
        ndim = len(shape)
        if fixed_indices is None:
            fixed_indices = {}
            
        individual_maps = {}
        
        for priority_id, criterion in self.defect_suite.criteria:
            single_map = np.zeros(shape, dtype=int)
            for idx in np.ndindex(shape):
                if criterion.check(self.melt_pool, idx):
                    single_map[idx] = priority_id
            
            slice_obj = [slice(None)] * ndim
            for dim, bin_idx in fixed_indices.items():
                slice_obj[dim] = bin_idx
            slice_obj = tuple(slice_obj)
            
            individual_maps[priority_id] = single_map[slice_obj]
            
        return plot_individual_defects_map(
            x_grid=x_grid,
            y_grid=y_grid,
            individual_maps=individual_maps,
            defect_labels=self.defect_labels,
            x_label=x_label,
            y_label=y_label,
            save_path=save_path
        )

    def plot_3d_safe_zone(self, x_axis: str, y_axis: str, z_axis: str, save_path: Optional[str] = None):
        """
        Plots the 3D evolution of the safe zone across a third parameter.
        """
        from .printability_plots import plot_3d_safe_zone_evolution
        
        if self.defect_map is None:
            self.evaluate()

        def _get_raw(axis):
            if hasattr(self.melt_pool.parameters, axis):
                return getattr(self.melt_pool.parameters, axis)
            if hasattr(self.melt_pool.material, axis):
                return getattr(self.melt_pool.material, axis)
            raise ValueError(f"Property '{axis}' not found.")
            
        x_grid_raw = _get_raw(x_axis)
        y_grid_raw = _get_raw(y_axis)
        z_grid_raw = _get_raw(z_axis)
        
        shape = self.melt_pool.shape
        x_grid = np.broadcast_to(x_grid_raw, shape)
        y_grid = np.broadcast_to(y_grid_raw, shape)
        z_grid = np.broadcast_to(z_grid_raw, shape)
        
        # The plotter expects (laser_power_grid, scan_speed_grid, z_grid...)
        return plot_3d_safe_zone_evolution(
            x_grid=y_grid, # laser power
            y_grid=x_grid, # scan speed
            z_grid=z_grid,
            defect_map_3d=self.defect_map,
            z_var_name=z_axis,
            defect_labels=self.defect_labels,
            save_path=save_path
        )
