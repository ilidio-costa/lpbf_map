import numpy as np
from typing import Tuple

from .base import DefectCriterion
from ..meltpool import MeltPool

class KeyholeKingCriterion(DefectCriterion):
    """
    King keyhole criterion based on conduction-to-keyhole transition.
    """
    def check(self, melt_pool: MeltPool, idx: Tuple[int, ...]) -> bool:
        absorptivity = melt_pool.get_property('absorptivity', idx)
        melting_temperature = melt_pool.get_property('melting_temperature', idx)
        ambient_temperature = melt_pool.get_property('ambient_temperature', idx)
        thermal_conductivity = melt_pool.get_property('thermal_conductivity', idx)
        boiling_temperature = melt_pool.get_property('boiling_temperature', idx)
        
        laser_power = melt_pool.get_property('laser_power', idx)
        beam_radius = melt_pool.get_property('beam_radius', idx)

        threshold_power = (
            (melting_temperature - ambient_temperature)
            * np.pi * thermal_conductivity * beam_radius
            / absorptivity
        )
        threshold_power *= (boiling_temperature / melting_temperature)

        return laser_power > threshold_power
