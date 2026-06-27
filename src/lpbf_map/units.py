"""
Standardized mapping of physical parameters to their SI units.
"""

PARAMETER_UNITS = {
    'laser_power': 'W',
    'scan_speed': 'm/s',
    'beam_radius': 'm',
    'hatch_spacing': 'm',
    'layer_thickness': 'm',
    'ambient_temperature': 'K',
    'wavelength': 'm',
    'density': 'kg/m³',
    'specific_heat': 'J/(kg·K)',
    'thermal_conductivity': 'W/(m·K)',
    'melting_temperature': 'K',
    'boiling_temperature': 'K',
    'absorptivity': '%',
    'thermal_diffusivity': 'm²/s',
    'electrical_resistivity': 'Ω·m'
}

def get_parameter_formatting(param_name: str):
    """
    Returns (human_name, unit, scale_factor) for a given parameter.
    """
    scale = 1.0
    if param_name in ['beam_radius', 'hatch_spacing', 'layer_thickness']:
        scale = 1e6
        unit = 'µm'
    elif param_name == 'absorptivity':
        scale = 100.0
        unit = '%'
    else:
        unit = PARAMETER_UNITS.get(param_name, '')
        
    human_name = param_name.replace('_', ' ').title()
    return human_name, unit, scale

def format_parameter_label(param_name: str, include_unit: bool = True) -> str:
    """
    Returns a human-readable string for a parameter, optionally with its unit.
    For example: 'scan_speed' -> 'Scan Speed (m/s)'
    """
    human_name, unit, _ = get_parameter_formatting(param_name)
    if include_unit and unit:
        return f"{human_name} ({unit})"
    return human_name
