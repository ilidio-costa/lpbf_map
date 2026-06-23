import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D
from scipy.ndimage import gaussian_filter
import numpy as np
from typing import Dict, Optional, Tuple, List

def plot_2d_printability_map(x_grid: np.ndarray, y_grid: np.ndarray,
                             defect_map: np.ndarray, defect_labels: Dict[int, str],
                             x_label: str = "Scanning Velocity (m/s)",
                             y_label: str = "Laser Power (W)",
                             save_path: Optional[str] = None):
    """
    Renders the Printability Space Map as a 2D plot.
    Uses Gaussian-smoothed masks to avoid interpolation bugs between distinct integer categories.

    Args:
        x_grid:        2D array of values for the horizontal axis.
        y_grid:        2D array of values for the vertical axis.
        defect_map:    Integer defect label array with the same shape as x_grid/y_grid.
        defect_labels: Mapping of integer label → human-readable defect name.
        x_label:       Label for the horizontal axis.
        y_label:       Label for the vertical axis.
        save_path:     Optional file path to save the figure.
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # 0=Safe, 1=Balling, 2=LoF, 3=Keyhole
    colors_dict = {
        0: '#140b34', # Safe Zone
        1: '#f6d746', # Balling
        2: '#e55c30', # Lack of Fusion
        3: '#84206b'  # Keyhole
    }

    unique_ids = sorted(list(defect_labels.keys()))

    for uid in unique_ids:
        color = colors_dict.get(uid, '#333333')

        # 1. Create rigid binary mask
        binary_mask = (defect_map == uid).astype(float)

        # 2. Smooth to create gradient boundaries
        smoothed_mask = gaussian_filter(binary_mask, sigma=1.0)

        # 3. Contour at the 50% threshold
        ax.contourf(x_grid, y_grid, smoothed_mask, levels=[0.5, 2.0], colors=[color], alpha=0.9)

    ax.set_title("L-PBF Printability Map\nDeterministic Defect Boundaries", fontsize=16, fontweight='bold')
    ax.set_xlabel(x_label, fontsize=14)
    ax.set_ylabel(y_label, fontsize=14)

    # Custom Legend
    patches = [mpatches.Patch(color=colors_dict.get(uid, '#333333'), label=defect_labels[uid])
               for uid in unique_ids]
    ax.legend(handles=patches, loc='center left', bbox_to_anchor=(1.05, 0.5), framealpha=0.9)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig, ax

def plot_individual_defects_map(x_grid: np.ndarray, y_grid: np.ndarray,
                                individual_maps: Dict[int, np.ndarray], defect_labels: Dict[int, str],
                                x_label: str = "Scanning Velocity (m/s)",
                                y_label: str = "Laser Power (W)",
                                save_path: Optional[str] = None):
    """
    Renders an array of subplots where each subplot isolates and visualizes a single defect criterion.
    """
    unique_ids = [uid for uid in defect_labels.keys() if uid != 0 and uid in individual_maps]
    unique_ids = sorted(unique_ids)
    n_defects = len(unique_ids)
    
    if n_defects == 0:
        raise ValueError("No defect criteria found.")
        
    cols = min(3, n_defects)
    rows = (n_defects + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 5.5, rows * 4.5))
    if n_defects == 1:
        axes = np.array([axes])
    axes = axes.flatten()
    
    colors_dict = {
        1: '#f6d746', # Balling
        2: '#e55c30', # Lack of Fusion
        3: '#84206b', # Keyhole
        4: '#2d7a5b', # Extra (Green)
        5: '#5e4fa2', # Extra (Purple)
    }
    
    for idx, uid in enumerate(unique_ids):
        ax = axes[idx]
        color = colors_dict.get(uid, '#e55c30')
        label = defect_labels.get(uid, f"Defect {uid}")
        
        defect_slice = individual_maps[uid]
        binary_mask = (defect_slice == uid).astype(float)
        
        if np.sum(binary_mask) > 0:
            smoothed_mask = gaussian_filter(binary_mask, sigma=1.0)
            ax.contourf(x_grid, y_grid, smoothed_mask, levels=[0.5, 2.0], colors=[color], alpha=0.9)
            
        ax.set_title(label, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        
    # Hide any unused subplots
    for idx in range(n_defects, len(axes)):
        axes[idx].set_visible(False)
        
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
    return fig, axes

def plot_3d_safe_zone_evolution(x_grid: np.ndarray, y_grid: np.ndarray, z_grid: np.ndarray, 
                                defect_map_3d: np.ndarray, z_var_name: str, 
                                defect_labels: Dict[int, str],
                                save_path: Optional[str] = None):
    """
    Plots a 3D deterministic map showing the evolution of the Safe Zone.
    Extracts 2D slices along the Z-axis. Base layer shows all defects, higher layers show only the safe zone.
    """
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Formatting
    format_map = {
        'beam_radius': ('Laser Beam Radius (µm)', 1e6),
        'ambient_temperature': ('Ambient Temperature (K)', 1.0),
        'hatch_spacing': ('Hatch Spacing (µm)', 1e6),
        'layer_thickness': ('Layer Thickness (µm)', 1e6),
    }
    z_label, z_scale = format_map.get(z_var_name, (z_var_name, 1.0))

    colors_dict = {
        0: '#140b34', # Safe Zone
        1: '#f6d746', # Balling
        2: '#e55c30', # Lack of Fusion
        3: '#84206b'  # Keyhole
    }
    unique_ids = sorted(list(defect_labels.keys()))
    
    # Determine the unique Z slices (assuming z_grid varies along axis 2)
    z_unique = np.unique(z_grid)
    z_unique = sorted(z_unique)
    
    # Determine which axis z_grid varies along
    z_axis_idx = None
    for i in range(3):
        if z_grid.shape[i] > 1:
            slc = [0, 0, 0]
            slc[i] = slice(None)
            if len(np.unique(z_grid[tuple(slc)])) > 1:
                z_axis_idx = i
                break
                
    if z_axis_idx is None:
        raise ValueError("z_grid does not vary along any axis!")

    for idx, z_val in enumerate(z_unique):
        z_plot_offset = z_val * z_scale
        
        # Find index of z_val along z_axis_idx
        slc = [0, 0, 0]
        slc[z_axis_idx] = slice(None)
        z_array_1d = z_grid[tuple(slc)]
        slice_idx = np.where(z_array_1d == z_val)[0][0]
        
        # Extract 2D slice by taking along the Z axis
        laser_power_slice = np.take(x_grid, slice_idx, axis=z_axis_idx)
        scan_speed_slice = np.take(y_grid, slice_idx, axis=z_axis_idx)
        defect_slice = np.take(defect_map_3d, slice_idx, axis=z_axis_idx)

        if idx == 0:
            # Base layer: plot all defects
            for uid in unique_ids:
                color = colors_dict.get(uid, '#333333')
                binary_mask = (defect_slice == uid).astype(float)
                if np.sum(binary_mask) == 0: continue
                smoothed_mask = gaussian_filter(binary_mask, sigma=1.0)
                ax.contourf(scan_speed_slice, laser_power_slice, smoothed_mask, levels=[0.5, 2.0], 
                            colors=[color], alpha=0.9, zdir='z', offset=z_plot_offset)
        else:
            # Higher layers: plot safe zone only
            binary_mask = (defect_slice == 0).astype(float)
            if np.sum(binary_mask) > 0:
                smoothed_mask = gaussian_filter(binary_mask, sigma=1.0)
                ax.contourf(scan_speed_slice, laser_power_slice, smoothed_mask, levels=[0.5, 2.0], 
                            colors=[colors_dict[0]], alpha=0.35, zdir='z', offset=z_plot_offset)

    ax.set_title(f"Safe Zone Evolution vs {z_label.split('(')[0]}", fontsize=14, pad=20)
    ax.set_xlabel("Scanning Velocity (m/s)", fontsize=12, labelpad=10)
    ax.set_ylabel("Laser Power (W)", fontsize=12, labelpad=10)
    ax.set_zlabel(z_label, fontsize=12, labelpad=10)
    
    ax.set_zlim(z_unique[0] * z_scale, z_unique[-1] * z_scale * 1.05)
    
    patches = [mpatches.Patch(color=colors_dict.get(uid, '#333333'), label=defect_labels[uid]) for uid in unique_ids]
    ax.legend(handles=patches, loc='center left', bbox_to_anchor=(1.1, 0.5), framealpha=0.9)
    ax.view_init(elev=25, azim=-45)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
    return fig, ax
