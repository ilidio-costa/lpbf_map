import matplotlib.pyplot as plt
import numpy as np
from typing import Optional
from scipy.optimize import minimize_scalar

from .meltpool import (
    MeltPool,
    _calculate_rubenchik_dimensionless_variables,
    _calculate_rubenchik_temperature_at_point,
    _calculate_eagar_tsai_temperature_at_point,
    _calculate_rubenchik_meltpool_dimensions
)

def plot_dimensions_2d(x_grid: np.ndarray, y_grid: np.ndarray, 
                       length_grid: np.ndarray, width_grid: np.ndarray, depth_grid: np.ndarray,
                       x_label: str, y_label: str, save_path: Optional[str] = None):
    """
    Plots formatted contour maps for Melt Pool Length, Width, and Depth over a 2D parameter slice.
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    
    titles = ["Length", "Width", "Depth"]
    data_to_plot = [length_grid, width_grid, depth_grid]
    
    for idx, ax in enumerate(axes):
        # Base filled contour using 'inferno'
        cf = ax.contourf(x_grid, y_grid, data_to_plot[idx] * 1e6, levels=20, cmap='inferno')
        
        # Overlay with thin contour lines for readability
        contour_lines = ax.contour(x_grid, y_grid, data_to_plot[idx] * 1e6, levels=10, colors='k', linewidths=0.5, alpha=0.6)
        ax.clabel(contour_lines, inline=True, fontsize=8, fmt='%1.0f') 

        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_title(titles[idx], fontsize=14)
        
        # Add the colorbar with the μm label
        cbar = fig.colorbar(cf, ax=ax)
        cbar.set_label(r'$(\mu m)$', fontsize=12, rotation=270, labelpad=15)

    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
    return fig, axes

def _compute_rubenchik_temperature_field(X, Y, Z, laser_power, scan_speed, beam_radius, mat_dict, ambient_temperature):
    """
    Computes the Rubenchik temperature field over a meshgrid of spatial coordinates.
    Returns a 2D array of temperature values (K) at each (X, Y, Z) mesh point.
    """
    # Local shorthand for formula alignment (see naming_conventions.md §5):
    #   T_field -> temperature_field [K] at each mesh node
    T_field = np.zeros_like(X)
    for i in range(X.shape[0]):
        for j in range(X.shape[1]):
            coords, B, p = _calculate_rubenchik_dimensionless_variables(
                X[i, j], Y[i, j], Z[i, j], mat_dict, laser_power, scan_speed, beam_radius, ambient_temperature
            )
            T_field[i, j] = _calculate_rubenchik_temperature_at_point(coords, B, p, mat_dict)
    return T_field

def plot_thermal_views(melt_pool: MeltPool, view_type: str = 'side', save_path: Optional[str] = None, resolution: int = 100, remove_background: bool = False):
    """
    Plots the thermal field for a melt pool (either 'top' or 'side' view).
    If melt_pool.parameters is vectorized (2D), plots a grid of subplots.
    """
    mat_dict = {
        'density': melt_pool.material.density,
        'specific_heat': melt_pool.material.specific_heat,
        'thermal_conductivity': melt_pool.material.thermal_conductivity,
        'melting_temperature': melt_pool.material.melting_temperature,
        'boiling_temperature': melt_pool.material.boiling_temperature,
        'thermal_diffusivity': melt_pool.material.thermal_diffusivity,
        'absorptivity': melt_pool.material.absorptivity
    }
    # Local shorthand for formula alignment (see naming_conventions.md §5):
    #   Tm -> melting_temperature [K]
    Tm = mat_dict['melting_temperature']
    
    is_grid = melt_pool.is_vectorized
    if is_grid:
        if len(melt_pool.shape) != 2:
            raise ValueError(
                f"Thermal grid plotting requires exactly a 2D parameter grid, "
                f"but received a {len(melt_pool.shape)}D grid "
                f"(shape={melt_pool.shape}). "
                f"Slice higher-dimensional spaces to a 2D cross-section before plotting."
            )
        # Local shorthand for formula alignment (see naming_conventions.md §5):
        #   P_grid -> unique laser_power values [W]
        #   v_grid -> unique scan_speed values [m/s]
        P_grid = np.unique(melt_pool.parameters.laser_power)
        v_grid = np.unique(melt_pool.parameters.scan_speed)

        # Determine exactly the shape
        n_rows, n_cols = melt_pool.shape
    else:
        n_rows, n_cols = 1, 1

    beam_radius_max = float(np.max(melt_pool.parameters.beam_radius))
    global_min_x = -beam_radius_max
    global_max_x = beam_radius_max
    global_max_W = beam_radius_max
    global_max_D = beam_radius_max
    global_peak_T = Tm

    for idx in np.ndindex(melt_pool.shape) if is_grid else [()]:
        p_val = melt_pool.parameters.get_point(idx) if is_grid else melt_pool.parameters

        current_mat_dict = mat_dict.copy()

        # Local shorthand for formula alignment (see naming_conventions.md §5):
        #   lp -> laser_power [W]
        #   ss -> scan_speed [m/s]
        #   br -> beam_radius [m]
        #   at -> ambient_temperature [K]
        lp = float(p_val.laser_power)
        ss = float(p_val.scan_speed)
        br = float(p_val.beam_radius)
        at = float(p_val.ambient_temperature)

        # Calculate Rubenchik dimensions for the global bounding box
        L, W, D, x_tail, x_front = _calculate_rubenchik_meltpool_dimensions(
            lp, ss, br, current_mat_dict, at, resolution=100
        )

        if L > 0:
            global_min_x = min(global_min_x, x_tail)
            global_max_x = max(global_max_x, x_front)
            global_max_W = max(global_max_W, W)
            global_max_D = max(global_max_D, D)

            # Find peak temperature using Rubenchik model along the centreline
            def rubenchik_temp_at_x(x):
                coords, B, p = _calculate_rubenchik_dimensionless_variables(
                    x, 0, 0, current_mat_dict, lp, ss, br, at
                )
                return _calculate_rubenchik_temperature_at_point(coords, B, p, current_mat_dict)

            res_peak = minimize_scalar(lambda x: -rubenchik_temp_at_x(x), bounds=(-5*br, br), method='bounded')
            global_peak_T = max(global_peak_T, -res_peak.fun)

    # Padding
    span_x = global_max_x - global_min_x
    x_min = global_min_x - span_x * 0.1
    x_max = global_max_x + span_x * 0.1
    y_max = (global_max_W / 2) * 1.1
    y_min = -y_max
    z_min = -global_max_D * 1.15
    z_max = 0

    # Lower limit at 300K matches legacy contrast (field values approach 0 far from laser)
    tlims = (300, global_peak_T * 1.05)
    global_levels = np.linspace(tlims[0], tlims[1], 50)

    # Layout sizing
    dx = x_max - x_min
    dy = y_max - y_min
    dz = abs(z_min)
    
    aspect_ratio = dy / dx if view_type == 'top' else dz / dx
    
    subplot_w = 3.5 if is_grid else 6.0
    fig_w = n_cols * subplot_w
    min_row_height = 0.85 
    fig_h = max((n_rows * subplot_w * aspect_ratio), n_rows * min_row_height) + 1.5 

    fig, axes = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=(fig_w, fig_h), 
                             sharex=True, sharey=True, constrained_layout=True)
    
    if n_rows == 1 and n_cols == 1: axes = np.array([[axes]])
    elif n_rows == 1: axes = axes.reshape(1, -1)
    elif n_cols == 1: axes = axes.reshape(-1, 1)

    title_view = "Top" if view_type == 'top' else "Side"
    fig.suptitle(f"{melt_pool.material.name} Melt Pool {title_view} Views", fontsize=16)

    X_grid = np.linspace(x_min, x_max, resolution)
    Y_grid = np.linspace(y_min, y_max, resolution) if view_type == 'top' else np.zeros(resolution)
    Z_grid = np.linspace(z_min, z_max, resolution) if view_type == 'side' else np.zeros(resolution)
    
    if view_type == 'top':
        X_mesh, Y_mesh = np.meshgrid(X_grid, Y_grid)
        Z_mesh = np.zeros_like(X_mesh)
    else:
        X_mesh, Z_mesh = np.meshgrid(X_grid, Z_grid)
        Y_mesh = np.zeros_like(X_mesh)

    for r in range(n_rows):
        for c in range(n_cols):
            ax = axes[r, c]
            idx = (r, c) if is_grid else ()
            p_val = melt_pool.parameters.get_point(idx) if is_grid else melt_pool.parameters

            current_mat_dict = mat_dict.copy()

            T_field = _compute_rubenchik_temperature_field(
                X_mesh, Y_mesh, Z_mesh,
                float(p_val.laser_power), float(p_val.scan_speed), float(p_val.beam_radius),
                current_mat_dict, float(p_val.ambient_temperature)
            )
            
            plot_data = np.ma.masked_less(T_field, Tm) if remove_background else T_field

            if view_type == 'top':
                ax.contourf(X_mesh*1e6, Y_mesh*1e6, plot_data, levels=global_levels, cmap='inferno', vmin=tlims[0], vmax=tlims[1], extend='both')
                ax.contour(X_mesh*1e6, Y_mesh*1e6, T_field, levels=[Tm], colors='cyan', linewidths=1.5, linestyles='--')
            else:
                ax.contourf(X_mesh*1e6, Z_mesh*1e6, plot_data, levels=global_levels, cmap='inferno', vmin=tlims[0], vmax=tlims[1], extend='both')
                ax.contour(X_mesh*1e6, Z_mesh*1e6, T_field, levels=[Tm], colors='cyan', linewidths=1.5, linestyles='--')
            
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.2)
            
            if r == n_rows - 1: ax.set_xlabel("X (µm)")
            if c == 0: 
                ylabel = "Y (µm)" if view_type == 'top' else "Z (µm)"
                ax.set_ylabel(ylabel, labelpad=10)
            if r == 0 or is_grid:
                # Local shorthand for formula alignment (see naming_conventions.md §5):
                #   L_i -> melt pool length at this grid point [m]
                #   W_i -> melt pool width at this grid point [m]
                #   D_i -> melt pool depth at this grid point [m]
                L_i = melt_pool.length[idx] if is_grid else float(melt_pool.length)
                W_i = melt_pool.width[idx] if is_grid else float(melt_pool.width)
                D_i = melt_pool.depth[idx] if is_grid else float(melt_pool.depth)

                dim_lbl = f"L: {L_i*1e6:.1f}µm | "
                if view_type == 'top':
                    dim_lbl += f"W: {W_i*1e6:.1f}µm"
                else:
                    dim_lbl += f"D: {D_i*1e6:.1f}µm"
                if L_i == 0:
                    dim_lbl = "No Melt Pool"
                    
                title = f"P={p_val.laser_power:.0f}W, v={p_val.scan_speed:.2f}m/s\n{dim_lbl}"
                ax.set_title(title, fontsize=10 if is_grid else 12)

    sm = plt.cm.ScalarMappable(cmap='inferno', norm=plt.Normalize(vmin=tlims[0], vmax=tlims[1]))
    cbar = fig.colorbar(sm, ax=axes, location='right', aspect=30)
    cbar.set_label('Temperature (K)', fontsize=12)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig, axes

def plot_dimensions(melt_pool, sweep_axis: str, save_path: Optional[str] = None):
    """
    Plots the melt pool dimensions (length, width, depth) against a 1D parameter sweep.
    """
    if len(melt_pool.shape) != 1:
        raise ValueError("plot_dimensions requires an exactly 1D parameter sweep.")
        
    x_data = getattr(melt_pool.parameters, sweep_axis, None)
    if x_data is None:
        x_data = getattr(melt_pool.material, sweep_axis, None)
        
    if x_data is None:
        raise ValueError(f"Sweep axis '{sweep_axis}' not found on parameters or material.")
        
    fig, ax = plt.subplots(figsize=(8, 6))
    
    L = melt_pool.length * 1e6
    W = melt_pool.width * 1e6
    D = melt_pool.depth * 1e6
    
    ax.plot(x_data, L, 'r-o', label='Length')
    ax.plot(x_data, W, 'g-s', label='Width')
    ax.plot(x_data, D, 'b-^', label='Depth')
    
    ax.set_xlabel(sweep_axis.replace('_', ' ').title(), fontsize=12)
    ax.set_ylabel(r'Dimension ($\mu m$)', fontsize=12)
    ax.set_title(f"Melt Pool Dimensions vs {sweep_axis.replace('_', ' ').title()}", fontsize=14)
    
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
    return fig, ax
