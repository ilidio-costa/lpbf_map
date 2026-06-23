import numpy as np
from scipy.integrate import fixed_quad
from scipy.optimize import minimize_scalar, brentq
from dataclasses import dataclass
from typing import Tuple, Optional

from .materials import Material
from .parameters import ProcessParameters

## ======================= Eagar-Tsai Model ======================= ##

def _eagar_tsai_integrand_substituted(u, x, y, z, scan_speed, thermal_diffusivity, beam_radius):
    """
    Eagar-Tsai temperature integrand under the variable substitution s = u²,
    where s is the elapsed time variable. This substitution removes the
    lower-bound singularity at s → 0 and is required for stable numerical
    quadrature. Returns the integrand value at each quadrature point u.
    """
    u = np.atleast_1d(u)
    s = u**2
    denom = 4 * thermal_diffusivity * s + beam_radius**2
    term_z = z**2 / (4 * thermal_diffusivity * s) if z != 0 else np.zeros_like(s)
    term_lat = (y**2 + (x + scan_speed * s)**2) / denom
    return 2 * np.exp(-term_z - term_lat) / denom

def _calculate_eagar_tsai_temperature_at_point(x, y, z, laser_power, scan_speed, beam_radius, material_dict, ambient_temperature=0):
    absorptivity = material_dict['absorptivity']
    thermal_conductivity = material_dict['thermal_conductivity']
    thermal_diffusivity = material_dict['thermal_diffusivity']
    
    pre_factor = (absorptivity * laser_power / (np.pi * thermal_conductivity)) * np.sqrt(thermal_diffusivity / np.pi)

    t_peak = max(0.0, -x / scan_speed) + (beam_radius / scan_speed)
    u_peak_guess = np.sqrt(t_peak)
    max_val = float(np.squeeze(_eagar_tsai_integrand_substituted(u_peak_guess, x, y, z, scan_speed, thermal_diffusivity, beam_radius)))
    
    if max_val < 1e-20:
        return ambient_temperature
        
    time_spread = np.sqrt(4.0 * thermal_diffusivity * t_peak) / scan_speed
    time_spread = max(time_spread, beam_radius / scan_speed) 
    
    t_lower = max(0.0, t_peak - 8.0 * time_spread)
    t_upper = t_peak + 8.0 * time_spread
    
    u_lower = np.sqrt(t_lower)
    u_upper = np.sqrt(t_upper)

    integral_val, _ = fixed_quad(
        _eagar_tsai_integrand_substituted, u_lower, u_upper, 
        args=(x, y, z, scan_speed, thermal_diffusivity, beam_radius), n=250  
    )
    
    return (pre_factor * integral_val) + ambient_temperature

def _calculate_eagar_tsai_meltpool_dimensions(laser_power, scan_speed, beam_radius, material_dict, ambient_temperature=0, resolution=100):
    melting_temperature = material_dict['melting_temperature']
    tol = beam_radius / float(resolution) if resolution else 1e-6 

    res_peak = minimize_scalar(
        lambda x: -_calculate_eagar_tsai_temperature_at_point(x, 0, 0, laser_power, scan_speed, beam_radius, material_dict, ambient_temperature), 
        bounds=(-5*beam_radius, beam_radius), method='bounded', options={'xatol': tol}
    )
    x_peak, temperature_max = res_peak.x, -res_peak.fun
    
    if temperature_max < melting_temperature:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    func_x = lambda x: _calculate_eagar_tsai_temperature_at_point(x, 0, 0, laser_power, scan_speed, beam_radius, material_dict, ambient_temperature) - melting_temperature
    
    step = beam_radius
    x_scan_fwd = x_peak + step
    while _calculate_eagar_tsai_temperature_at_point(x_scan_fwd, 0, 0, laser_power, scan_speed, beam_radius, material_dict, ambient_temperature) > melting_temperature:
        x_scan_fwd += step
        step *= 1.5
        if x_scan_fwd > x_peak + 0.1: break 
    try: x_front = brentq(func_x, x_peak, x_scan_fwd, xtol=tol)
    except ValueError: x_front = x_peak

    step = beam_radius
    x_scan_bwd = x_peak - step
    while _calculate_eagar_tsai_temperature_at_point(x_scan_bwd, 0, 0, laser_power, scan_speed, beam_radius, material_dict, ambient_temperature) > melting_temperature:
        x_scan_bwd -= step
        step *= 1.5
        if x_scan_bwd < x_peak - 0.1: break
    try: x_tail = brentq(func_x, x_scan_bwd, x_peak, xtol=tol)
    except ValueError: x_tail = x_peak
    
    length = x_front - x_tail

    def get_depth_at_x(x_loc):
        if _calculate_eagar_tsai_temperature_at_point(x_loc, 0, 0, laser_power, scan_speed, beam_radius, material_dict, ambient_temperature) < melting_temperature: return 0.0
        func_z = lambda z: _calculate_eagar_tsai_temperature_at_point(x_loc, 0, z, laser_power, scan_speed, beam_radius, material_dict, ambient_temperature) - melting_temperature
        z_scan, step_z = -beam_radius, beam_radius
        while _calculate_eagar_tsai_temperature_at_point(x_loc, 0, z_scan, laser_power, scan_speed, beam_radius, material_dict, ambient_temperature) > melting_temperature:
            z_scan -= step_z
            step_z *= 1.5
            if z_scan < -0.01: break
        try: return abs(brentq(func_z, z_scan, 0, xtol=tol))
        except ValueError: return 0.0

    res_d = minimize_scalar(
        lambda x: -get_depth_at_x(x), bounds=(x_tail, x_front), 
        method='bounded', options={'xatol': tol}
    )
    depth = -res_d.fun

    def get_width_at_x(x_loc):
        if _calculate_eagar_tsai_temperature_at_point(x_loc, 0, 0, laser_power, scan_speed, beam_radius, material_dict, ambient_temperature) < melting_temperature: return 0.0
        func_y = lambda y: _calculate_eagar_tsai_temperature_at_point(x_loc, y, 0, laser_power, scan_speed, beam_radius, material_dict, ambient_temperature) - melting_temperature
        y_scan, step_y = beam_radius, beam_radius
        while _calculate_eagar_tsai_temperature_at_point(x_loc, y_scan, 0, laser_power, scan_speed, beam_radius, material_dict, ambient_temperature) > melting_temperature:
            y_scan += step_y
            step_y *= 1.5
            if y_scan > 0.01: break
        try: return brentq(func_y, 0, y_scan, xtol=tol) * 2.0
        except ValueError: return 0.0

    res_w = minimize_scalar(
        lambda x: -get_width_at_x(x), bounds=(x_tail, x_front), 
        method='bounded', options={'xatol': tol} 
    )
    width = -res_w.fun

    return length, width, depth, x_tail, x_front

## ======================= Rubenchik Model ====================== ##

def _rubenchik_integrand_substituted(u, xi, yi, zi, p):
    u = np.atleast_1d(u)
    tau = u**2
    denom_geom = 4 * p * tau + 1
    term_z = (zi**2) / (4 * tau) if zi != 0 else np.zeros_like(tau)
    term_lateral = (yi**2 + (xi + tau)**2) / denom_geom
    return 2 * np.exp(-term_z - term_lateral) / denom_geom

def _calculate_rubenchik_dimensionless_variables(x, y, z, material_dict, laser_power, scan_speed, beam_radius, ambient_temperature=0):
    # Local shorthand for formula alignment (see naming conventions):
    #   p_val  → peclet_number (thermal_diffusivity / (scan_speed * beam_radius))
    #   xi, yi, zi → dimensionless spatial coordinates
    #   P_eff  → effective_laser_power [W]
    #   B_val  → normalized_enthalpy (Rubenchik parameter)
    density, specific_heat, melting_temperature = material_dict['density'], material_dict['specific_heat'], material_dict['melting_temperature']
    thermal_diffusivity, absorptivity = material_dict['thermal_diffusivity'], material_dict['absorptivity']
    
    p_val = thermal_diffusivity / (scan_speed * beam_radius)
    xi = x / beam_radius
    yi = y / beam_radius
    zi = z / (np.sqrt( thermal_diffusivity * beam_radius / scan_speed )) 

    P_eff = melting_temperature/(melting_temperature - ambient_temperature) * laser_power

    numerator = absorptivity * P_eff
    denominator = np.pi * density * specific_heat * melting_temperature * np.sqrt(thermal_diffusivity * scan_speed * beam_radius**3)
    B_val = numerator / denominator

    return (xi, yi, zi), B_val, p_val

def _calculate_rubenchik_temperature_at_point(coords, B, p, material_dict):
    xi, yi, zi = coords
    tau_peak = max(0.0, -xi) + 1.0
    u_peak_guess = np.sqrt(tau_peak)
    max_val = float(np.squeeze(_rubenchik_integrand_substituted(u_peak_guess, xi, yi, zi, p)))

    if max_val < 1e-20:
        return 0.0

    tau_spread = np.sqrt(4.0 * p * tau_peak)
    tau_spread = max(tau_spread, 1.0)
    
    tau_lower = max(0.0, tau_peak - 8.0 * tau_spread)
    tau_upper = tau_peak + 8.0 * tau_spread
    
    u_lower = np.sqrt(tau_lower)
    u_upper = np.sqrt(tau_upper)

    integral_val, _ = fixed_quad(
        _rubenchik_integrand_substituted, u_lower, u_upper, 
        args=(xi, yi, zi, p), n=250
    )

    temperature_rise = material_dict['melting_temperature'] * (B / np.sqrt(np.pi)) * integral_val
    return temperature_rise

def _calculate_rubenchik_meltpool_dimensions(laser_power, scan_speed, beam_radius, material_dict, ambient_temperature=0, resolution=100):
    melting_temperature = material_dict['melting_temperature']
    tol = beam_radius / float(resolution) if resolution else 1e-6 

    def rubenchik_temp_at(x, y, z):
        coords, B, p = _calculate_rubenchik_dimensionless_variables(x, y, z, material_dict, laser_power, scan_speed, beam_radius, ambient_temperature)
        return _calculate_rubenchik_temperature_at_point(coords, B, p, material_dict)

    res_peak = minimize_scalar(
        lambda x: - rubenchik_temp_at(x, 0, 0), bounds=(-5*beam_radius, beam_radius), 
        method='bounded', options={'xatol': tol}
    )
    x_peak, temperature_max = res_peak.x, -res_peak.fun
    if temperature_max < melting_temperature: return 0.0, 0.0, 0.0, 0.0, 0.0

    func_x = lambda x: rubenchik_temp_at(x, 0, 0) - melting_temperature
    step = beam_radius
    x_scan_fwd = x_peak + step
    while rubenchik_temp_at(x_scan_fwd, 0, 0) > melting_temperature:
        x_scan_fwd += step
        step *= 1.5
        if x_scan_fwd > x_peak + 0.1: break
    try: x_front = brentq(func_x, x_peak, x_scan_fwd, xtol=tol)
    except ValueError: x_front = x_peak

    step = beam_radius
    x_scan_bwd = x_peak - step
    while rubenchik_temp_at(x_scan_bwd, 0, 0) > melting_temperature:
        x_scan_bwd -= step
        step *= 1.5
        if x_scan_bwd < x_peak - 0.1: break
    try: x_tail = brentq(func_x, x_scan_bwd, x_peak, xtol=tol)
    except ValueError: x_tail = x_peak
    length = x_front - x_tail

    def get_depth_at_x(x_loc):
        if rubenchik_temp_at(x_loc, 0, 0) < melting_temperature: return 0.0
        func_z = lambda z: rubenchik_temp_at(x_loc, 0, z) - melting_temperature
        z_scan, step_z = -beam_radius, beam_radius
        while rubenchik_temp_at(x_loc, 0, z_scan) > melting_temperature:
            z_scan -= step_z
            step_z *= 1.5
            if z_scan < -0.01: break
        try: return abs(brentq(func_z, z_scan, 0, xtol=tol))
        except ValueError: return 0.0

    res_d = minimize_scalar(
        lambda x: -get_depth_at_x(x), bounds=(x_tail, x_front),
        method='bounded', options={'xatol': tol}
    )
    depth = -res_d.fun

    def get_width_at_x(x_loc):
        if rubenchik_temp_at(x_loc, 0, 0) < melting_temperature: return 0.0
        func_y = lambda y: rubenchik_temp_at(x_loc, y, 0) - melting_temperature
        y_scan, step_y = beam_radius, beam_radius
        while rubenchik_temp_at(x_loc, y_scan, 0) > melting_temperature:
            y_scan += step_y
            step_y *= 1.5
            if y_scan > 0.01: break
        try: return brentq(func_y, 0, y_scan, xtol=tol) * 2.0
        except ValueError: return 0.0

    res_w = minimize_scalar(
        lambda x: -get_width_at_x(x), bounds=(x_tail, x_front), 
        method='bounded', options={'xatol': tol} 
    )
    width = -res_w.fun

    return length, width, depth, x_tail, x_front

def _calculate_rubenchik_interpolated_meltpool_dimensions(laser_power, scan_speed, beam_radius, material_dict, ambient_temperature=0):
    coords , B, p = _calculate_rubenchik_dimensionless_variables(0, 0, 0, material_dict, laser_power, scan_speed, beam_radius, ambient_temperature)
    
    dimensionless_depth = (beam_radius / np.sqrt(p)) * (
        0.008 - 0.0048 * B - 0.047 * p - 0.099 * B * p 
        + (0.32 + 0.015 * B) * p * np.log(p) 
        + np.log(B) * (0.0056 - 0.89 * p + 0.29 * p * np.log(p))
    )

    dimensionless_width = (beam_radius / (B * p**3)) * (
        0.0021 - 0.047 * p + 0.34 * p**2 - 1.9 * p**3 - 0.33 * p**4
        + B * (0.00066 - 0.0070 * p - 0.00059 * p**2 + 2.8 * p**3 - 0.12 * p**4)
        + B**2 * (-0.00070 + 0.015 * p - 0.12 * p**2 + 0.59 * p**3 - 0.023 * p**4)
        + B**3 * (0.00001 - 0.00022 * p + 0.0020 * p**2 - 0.0085 * p**3 + 0.0014 * p**4)
    )

    dimensionless_length = (beam_radius / p**2) * (
        0.0053 - 0.21 * p + 1.3 * p**2 + (-0.11 - 0.17 * B) * p**2 * np.log(p)
        + B * (-0.0062 + 0.23 * p + 0.75 * p**2)
    )
    
    thermal_diffusivity = material_dict['thermal_diffusivity']
    depth = dimensionless_depth * np.sqrt(thermal_diffusivity * beam_radius / scan_speed)
    width = dimensionless_width * beam_radius 
    length = dimensionless_length * beam_radius

    return length, width, depth

## ======================= Gladush-Smurov Model ======================= ##
def _calculate_gladush_smurov_depth(laser_power, scan_speed, beam_radius, material_dict):
    absorptivity = material_dict['absorptivity']
    thermal_conductivity = material_dict['thermal_conductivity']
    boiling_temperature = material_dict['boiling_temperature']
    thermal_diffusivity = material_dict['thermal_diffusivity']
    # Gladush-Smurov thermal prefactor
    C1 = absorptivity*laser_power / (2 * np.pi * thermal_conductivity * boiling_temperature)
    return C1 * np.log( (beam_radius + thermal_diffusivity/scan_speed) / beam_radius )

def _calculate_maximum_hybrid_depth_gs_et(laser_power, scan_speed, beam_radius, material_dict, ambient_temperature=0):
    depth_gs = _calculate_gladush_smurov_depth(laser_power, scan_speed, beam_radius, material_dict)
    depth_gs = max(0.0, depth_gs)
    
    _, _, depth_et, _, _ = _calculate_eagar_tsai_meltpool_dimensions(
        laser_power, scan_speed, beam_radius, material_dict, ambient_temperature=ambient_temperature, resolution=250
    )
    
    hybrid_depth = max(depth_gs, depth_et)
    return hybrid_depth, depth_gs, depth_et

@dataclass
class MeltPool:
    """
    Central Physics Hub. 
    Represents the physical manifestation of the laser-material interaction.
    Acts as a multi-dimensional lazy data proxy.
    """
    material: Material
    parameters: ProcessParameters
    
    # Internal cache for lazy properties
    _cached_dimensions: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None
    
    def __post_init__(self):
        """
        Validates inputs but defers any dimension calculation.
        """
        pass

    @property
    def shape(self) -> tuple:
        shapes = [self.parameters.shape]
        for prop in ['density', 'specific_heat', 'thermal_conductivity', 'melting_temperature', 'boiling_temperature', 'absorptivity', 'thermal_diffusivity']:
            val = getattr(self.material, prop, None)
            if val is not None:
                shapes.append(np.asarray(val).shape)
        return np.broadcast_shapes(*shapes)

    @property
    def is_vectorized(self) -> bool:
        return len(self.shape) > 0
        
    def get_property(self, name: str, idx: Optional[tuple] = None):
        """
        Retrieves a scalar physical value (from either parameters or material)
        at a specific grid index, correctly handling multi-dimensional broadcasting.
        Returns a float, or None if the property is not set.
        """
        if hasattr(self.parameters, name):
            val = getattr(self.parameters, name)
        elif hasattr(self.material, name):
            val = getattr(self.material, name)
        else:
            raise ValueError(f"Property '{name}' not found in MeltPool.")
            
        if val is None:
            return None
            
        if idx is None or not self.is_vectorized:
            return float(val)
        return float(np.broadcast_to(val, self.shape)[idx])
        
    def _compute_meltpool_dimensions_at_index(self, idx: Optional[tuple], shape: tuple) -> Tuple[float, float, float]:
        """
        Computes the physical melt pool dimensions (length, width, depth) at a
        specific N-dimensional grid index, or for a scalar parameter set when idx is None.
        Resolves absorptivity from the material object.
        """
        if idx is not None:
            mat_dict = {}
            for prop in ['density', 'specific_heat', 'thermal_conductivity', 'melting_temperature', 'boiling_temperature', 'absorptivity', 'thermal_diffusivity']:
                val = getattr(self.material, prop, None)
                if val is not None:
                    mat_dict[prop] = float(np.broadcast_to(val, shape)[idx])
                else:
                    mat_dict[prop] = None

            laser_power = float(np.broadcast_to(self.parameters.laser_power, shape)[idx])
            scan_speed = float(np.broadcast_to(self.parameters.scan_speed, shape)[idx])
            beam_radius = float(np.broadcast_to(self.parameters.beam_radius, shape)[idx])
            ambient_temperature = float(np.broadcast_to(self.parameters.ambient_temperature, shape)[idx])
        else:
            mat_dict = {
                'density': float(self.material.density),
                'specific_heat': float(self.material.specific_heat),
                'thermal_conductivity': float(self.material.thermal_conductivity),
                'melting_temperature': float(self.material.melting_temperature),
                'boiling_temperature': float(self.material.boiling_temperature),
                'absorptivity': float(self.material.absorptivity),
                'thermal_diffusivity': float(self.material.thermal_diffusivity)
            }
            laser_power = float(self.parameters.laser_power)
            scan_speed = float(self.parameters.scan_speed)
            beam_radius = float(self.parameters.beam_radius)
            ambient_temperature = float(self.parameters.ambient_temperature)

        length, width, _, _, _ = _calculate_rubenchik_meltpool_dimensions(
            laser_power, scan_speed, beam_radius, mat_dict,
            ambient_temperature=ambient_temperature, resolution=100
        )
        depth, _, _ = _calculate_maximum_hybrid_depth_gs_et(
            laser_power, scan_speed, beam_radius, mat_dict,
            ambient_temperature=ambient_temperature
        )

        if width == 0.0 or length == 0.0:
            depth = 0.0

        return float(length), float(width), float(depth)

    @property
    def dimensions(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns (length, width, depth) arrays matching the parameters shape.
        Executes physics solvers only once, caching the results.
        """
        if self._cached_dimensions is not None:
            return self._cached_dimensions

        shape = self.shape

        if not self.is_vectorized:
            length, width, depth = self._compute_meltpool_dimensions_at_index(None, shape)
            self._cached_dimensions = (np.array(length), np.array(width), np.array(depth))
            return self._cached_dimensions

        # Allocate arrays for the multi-dimensional grid
        length_array = np.zeros(shape)
        width_array = np.zeros(shape)
        depth_array = np.zeros(shape)

        # Iterate over all coordinates in the N-dimensional space
        for idx in np.ndindex(shape):
            length, width, depth = self._compute_meltpool_dimensions_at_index(idx, shape)
            length_array[idx] = length
            width_array[idx] = width
            depth_array[idx] = depth

        self._cached_dimensions = (length_array, width_array, depth_array)
        return self._cached_dimensions

    @property
    def length(self) -> np.ndarray:
        return self.dimensions[0]
        
    @property
    def width(self) -> np.ndarray:
        return self.dimensions[1]
        
    @property
    def depth(self) -> np.ndarray:
        return self.dimensions[2]

    @property
    def normalized_enthalpy(self) -> np.ndarray:
        """
        Returns the King's Normalized Enthalpy matrix.
        Formula: (A * P) / (pi * rho * C_p * T_m * sqrt(alpha * v * r^3))
        """
        A = self.material.absorptivity
        P = self.parameters.laser_power
        rho = self.material.density
        C_p = self.material.specific_heat
        T_m = self.material.melting_temperature
        alpha = self.material.thermal_diffusivity
        v = self.parameters.scan_speed
        r = self.parameters.beam_radius
        
        result = (A * P) / (np.pi * rho * C_p * T_m * np.sqrt(alpha * v * (r**3)))
        return np.broadcast_to(result, self.shape)

    def plot_side_view(self, save_path: Optional[str] = None, resolution: int = 100, remove_background: bool = False):
        """
        Plots the thermal field side view (Length vs Depth).
        Automatically handles single cross-section vs grid of cross-sections based on parameter dimensionality.
        """
        from .meltpool_plots import plot_thermal_views
        return plot_thermal_views(self, view_type='side', save_path=save_path, resolution=resolution, remove_background=remove_background)

    def plot_top_view(self, save_path: Optional[str] = None, resolution: int = 100, remove_background: bool = False):
        """
        Plots the thermal field top view (Length vs Width).
        Automatically handles single view vs grid of views based on parameter dimensionality.
        """
        from .meltpool_plots import plot_thermal_views
        return plot_thermal_views(self, view_type='top', save_path=save_path, resolution=resolution, remove_background=remove_background)

    def plot_dimensions(self, sweep_axis: str, save_path: Optional[str] = None):
        """
        Plots the melt pool dimensions (length, width, depth) against a 1D parameter sweep.
        """
        from .meltpool_plots import plot_dimensions
        return plot_dimensions(self, sweep_axis, save_path=save_path)

    def slice_2d_dimensions(self, x_axis: str, y_axis: str, fixed_indices: Optional[dict] = None) -> tuple:
        """
        Slices an N-dimensional grid down to a 2D plane for plotting via strict ijk indexing.
        Returns: (x_grid, y_grid, length_grid, width_grid, depth_grid)
        """
        shape = self.shape
        ndim = len(shape)
        
        if ndim < 2:
            raise ValueError("Parameters must be at least 2D to extract a 2D slice.")
            
        slice_obj = [slice(None)] * ndim
        if fixed_indices:
            for dim, bin_idx in fixed_indices.items():
                slice_obj[dim] = bin_idx
                
        slice_obj = tuple(slice_obj)
        
        def _get_raw(axis):
            if hasattr(self.parameters, axis):
                return getattr(self.parameters, axis)
            if hasattr(self.material, axis):
                return getattr(self.material, axis)
            raise ValueError(f"Property '{axis}' not found.")
            
        x_grid_full = np.broadcast_to(_get_raw(x_axis), shape)
        y_grid_full = np.broadcast_to(_get_raw(y_axis), shape)
        
        l_full = np.broadcast_to(self.length, shape)
        w_full = np.broadcast_to(self.width, shape)
        d_full = np.broadcast_to(self.depth, shape)
        
        return (
            x_grid_full[slice_obj], y_grid_full[slice_obj], 
            l_full[slice_obj], w_full[slice_obj], d_full[slice_obj]
        )

    def plot_dimensions_2d(self, x_axis: str, y_axis: str, fixed_indices: Optional[dict] = None, save_path: Optional[str] = None):
        """
        Plots a 2D contour map of Length, Width, and Depth.
        """
        from .meltpool_plots import plot_dimensions_2d as pd2d
        
        x_grid, y_grid, l_grid, w_grid, d_grid = self.slice_2d_dimensions(x_axis, y_axis, fixed_indices)
        
        x_label = x_axis.replace('_', ' ').title()
        y_label = y_axis.replace('_', ' ').title()
        
        return pd2d(
            x_grid=x_grid, y_grid=y_grid,
            length_grid=l_grid, width_grid=w_grid, depth_grid=d_grid,
            x_label=x_label, y_label=y_label,
            save_path=save_path
        )
