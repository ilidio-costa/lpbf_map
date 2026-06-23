import numpy as np
from typing import Tuple

from .base import DefectCriterion
from ..meltpool import MeltPool

class KeyholeGanCriterion(DefectCriterion):
    """
    Gan universal keyhole criterion based on normalized enthalpy.
    Returns True if the normalized enthalpy exceeds the empirical threshold of 6.0.
    """
    def check(self, melt_pool: MeltPool, idx: Tuple[int, ...]) -> bool:
        absorptivity = melt_pool.get_property('absorptivity', idx)
        density = melt_pool.get_property('density', idx)
        specific_heat = melt_pool.get_property('specific_heat', idx)
        melting_temperature = melt_pool.get_property('melting_temperature', idx)
        thermal_diffusivity = melt_pool.get_property('thermal_diffusivity', idx)

        laser_power = melt_pool.get_property('laser_power', idx)
        scan_speed = melt_pool.get_property('scan_speed', idx)
        beam_radius = melt_pool.get_property('beam_radius', idx)
        ambient_temperature = melt_pool.get_property('ambient_temperature', idx)

        normalized_enthalpy = (absorptivity * laser_power) / (
            (melting_temperature - ambient_temperature)
            * np.pi * density * specific_heat
            * np.sqrt(thermal_diffusivity * scan_speed * beam_radius**3)
        )

        return normalized_enthalpy > 6.0
