import numpy as np
from dataclasses import dataclass
from typing import Union, Optional

@dataclass
class ProcessParameters:
    """
    Represents the operational machine configuration for L-PBF.
    Fields support single floats or vectorized NumPy arrays for rapid evaluation grids.
    Internally works exclusively in SI units.

    All fields are cast to NumPy arrays on initialisation so that scalar simulations
    and multi-dimensional grids share a uniform API and always expose `.shape`.
    """
    laser_power: Union[float, np.ndarray]                        # [W]
    scan_speed: Union[float, np.ndarray]                         # [m/s]
    beam_radius: Union[float, np.ndarray]                        # [m]
    hatch_spacing: Union[float, np.ndarray, None] = None         # [m]
    layer_thickness: Union[float, np.ndarray, None] = None       # [m]
    ambient_temperature: Union[float, np.ndarray] = 298.0        # [K]
    wavelength: Optional[Union[float, np.ndarray]] = None        # [m] laser wavelength

    def __post_init__(self):
        """ Validates parameter limits and broadcasts arrays to a common N-dimensional shape. """
        # Convert all to numpy arrays (0-D for scalars)
        self.laser_power = np.asarray(self.laser_power, dtype=float)
        self.scan_speed = np.asarray(self.scan_speed, dtype=float)
        self.beam_radius = np.asarray(self.beam_radius, dtype=float)

        if self.hatch_spacing is not None:
            self.hatch_spacing = np.asarray(self.hatch_spacing, dtype=float)
        if self.layer_thickness is not None:
            self.layer_thickness = np.asarray(self.layer_thickness, dtype=float)

        self.ambient_temperature = np.asarray(self.ambient_temperature, dtype=float)
        if self.wavelength is not None:
            self.wavelength = np.asarray(self.wavelength, dtype=float)

        if np.any(self.laser_power <= 0):
            raise ValueError("Laser power must be strictly positive.")
        if np.any(self.scan_speed <= 0):
            raise ValueError("Scan speed must be strictly positive.")
        if np.any(self.beam_radius <= 0):
            raise ValueError("Beam radius must be strictly positive.")

        # Find the broadcast shape of the active arrays
        arrays_to_broadcast = [self.laser_power, self.scan_speed, self.beam_radius, self.ambient_temperature]
        if self.hatch_spacing is not None:
            arrays_to_broadcast.append(self.hatch_spacing)
        if self.layer_thickness is not None:
            arrays_to_broadcast.append(self.layer_thickness)
        if self.wavelength is not None:
            arrays_to_broadcast.append(self.wavelength)

        try:
            broadcasted = np.broadcast_arrays(*arrays_to_broadcast)
            self.shape = broadcasted[0].shape
        except ValueError as e:
            raise ValueError(f"Parameters cannot be broadcast to a single N-dimensional grid: {e}")

    @property
    def is_vectorized(self) -> bool:
        """ Returns true if parameters are configured as an N-dimensional grid. """
        return len(self.shape) > 0

    def get_point(self, index_tuple: tuple) -> "ProcessParameters":
        """
        Extracts a single ProcessParameters object at the given ijk index tuple.
        """
        def _get(arr):
            if arr is None: return None
            # If the array is scalar (0-D), return it directly
            if arr.ndim == 0: return float(arr)
            # If the array has the broadcast shape, index it
            if arr.shape == self.shape: return float(arr[index_tuple])
            # Broadcast to the full shape first, then index
            return float(np.broadcast_to(arr, self.shape)[index_tuple])

        return ProcessParameters(
            laser_power=_get(self.laser_power),
            scan_speed=_get(self.scan_speed),
            beam_radius=_get(self.beam_radius),
            hatch_spacing=_get(self.hatch_spacing),
            layer_thickness=_get(self.layer_thickness),
            ambient_temperature=_get(self.ambient_temperature),
            wavelength=_get(self.wavelength),
        )
