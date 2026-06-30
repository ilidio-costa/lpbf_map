import json
from dataclasses import dataclass
from typing import Optional, Union
import numpy as np
import importlib.resources

@dataclass
class Material:
    """
    Represents the thermophysical blueprint of an alloy for L-PBF modeling.
    Uses strict SI units (kg, m, s, W, K).

    All numeric properties are internally cast to NumPy arrays on initialisation,
    so that single-value materials and multi-value 'material sweeps' (e.g. a
    thermal_conductivity sweep) share a unified API and always expose `.shape`.
    """
    name: str
    density: Union[float, np.ndarray]                # rho [kg/m^3]
    specific_heat: Union[float, np.ndarray]          # C_p [J/(kg*K)]
    thermal_conductivity: Union[float, np.ndarray]   # k [W/(m*K)]
    melting_temperature: Union[float, np.ndarray]    # T_m [K]
    boiling_temperature: Union[float, np.ndarray]    # T_b [K]
    absorptivity: Union[float, np.ndarray]           # A [dimensionless]
    thermal_diffusivity: Optional[Union[float, np.ndarray]] = None  # alpha [m^2/s]
    electrical_resistivity: Optional[Union[float, np.ndarray]] = None  # rho_e [Ohm*m]

    def __post_init__(self):
        """
        Casts all numeric properties to NumPy arrays and validates physical limits.
        Auto-calculates thermal diffusivity if it was not explicitly provided.
        """
        # --- NumPy casting: ensures every property exposes .shape uniformly ---
        self.density = np.asarray(self.density, dtype=float)
        self.specific_heat = np.asarray(self.specific_heat, dtype=float)
        self.thermal_conductivity = np.asarray(self.thermal_conductivity, dtype=float)
        self.melting_temperature = np.asarray(self.melting_temperature, dtype=float)
        self.boiling_temperature = np.asarray(self.boiling_temperature, dtype=float)
        self.absorptivity = np.asarray(self.absorptivity, dtype=float)
        if self.thermal_diffusivity is not None:
            self.thermal_diffusivity = np.asarray(self.thermal_diffusivity, dtype=float)
        if self.electrical_resistivity is not None:
            self.electrical_resistivity = np.asarray(self.electrical_resistivity, dtype=float)

        # --- Physical validation ---
        if np.any(self.density <= 0):
            raise ValueError(f"Density must be > 0. Got {self.density}")
        if np.any(self.specific_heat <= 0):
            raise ValueError(f"Specific heat must be > 0. Got {self.specific_heat}")
        if np.any(self.thermal_conductivity <= 0):
            raise ValueError(f"Thermal conductivity must be > 0. Got {self.thermal_conductivity}")

        # --- Derived property: alpha = k / (rho * C_p) ---
        if self.thermal_diffusivity is None:
            self.thermal_diffusivity = self.thermal_conductivity / (self.density * self.specific_heat)

    def calculate_absorptivity(self, wavelength: Union[float, np.ndarray], method: str = 'hagen-rubens') -> None:
        """
        Computes and updates `self.absorptivity` from a theoretical model.

        By default uses the Hagen-Rubens approximation, which requires
        `self.electrical_resistivity` to be set on this Material object.

        Args:
            wavelength: Laser wavelength in metres (m). Can be a scalar or array
                        matching the parameter sweep.
            method:     The analytical model to apply. Currently supported:
                        - 'hagen-rubens': Simplified Drude model,
                          A ≈ 0.365 * sqrt(electrical_resistivity / wavelength).

        Raises:
            ValueError: If `electrical_resistivity` is None when using 'hagen-rubens'.
            ValueError: If an unsupported method name is given.
        """
        method = method.lower()
        valid_methods = ['hagen_rubens', 'gusarov_smurov', 'boley_hex', 'boley_gaussian', 'boley_bimodal']
        
        if method not in valid_methods:
            raise ValueError(f"Unknown absorptivity method: '{method}'. Supported: {valid_methods}.")
            
        if self.electrical_resistivity is None:
            raise ValueError(
                f"Method '{method}' requires 'electrical_resistivity' to be set on the Material."
            )
            
        wavelength = np.asarray(wavelength, dtype=float)

        # Base solid absorptivity via Hagen-Rubens
        As = 0.365 * np.sqrt(self.electrical_resistivity / wavelength)
        
        if method == 'hagen_rubens':
            absorptivity_raw = As
        elif method == 'gusarov_smurov':
            absorptivity_raw = (2 * np.sqrt(As)) / (1 + np.sqrt(As))
        elif method == 'boley_hex':
            absorptivity_raw = 0.0889 + 2.73 * As - 5.06 * (As**2) + 4.29 * (As**3)
        elif method == 'boley_gaussian':
            absorptivity_raw = 0.0413 + 2.89 * As - 5.36 * (As**2) + 4.50 * (As**3)
        elif method == 'boley_bimodal':
            absorptivity_raw = 0.104 + 2.39 * As - 3.31 * (As**2) + 2.20 * (As**3)

        # Physical constraint: absorptivity cannot exceed 1.0 (100%)
        self.absorptivity = np.minimum(absorptivity_raw, 1.0)

    @classmethod
    def from_library(cls, material_name: str) -> "Material":
        """
        Factory method that loads a material from the native PyPI packaged JSON library.
        
        Args:
            material_name: Name of the material file (e.g. 'Ti64' for Ti64.json)
        """
        if not material_name.endswith('.json'):
            filename = f"{material_name}.json"
        else:
            filename = material_name
            
        try:
            # Using importlib.resources to guarantee resolution even when pip-installed
            with importlib.resources.open_text('lpbf_map.database', filename) as f:
                data = json.load(f)
                
            return cls(
                name=data.get("name", material_name),
                density=data.get("density", data.get("rho")),
                specific_heat=data.get("specific_heat", data.get("C_p")),
                thermal_conductivity=data.get("thermal_conductivity", data.get("k")),
                melting_temperature=data.get("melting_temperature", data.get("T_m")),
                boiling_temperature=data.get("boiling_temperature", data.get("T_b")), 
                absorptivity=data.get("absorptivity", data.get("A")),
                thermal_diffusivity=data.get("thermal_diffusivity", data.get("alpha")),
                electrical_resistivity=data.get("electrical_resistivity", data.get("rho_e"))
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Material {filename} not found in native database.")
        except KeyError as e:
            raise ValueError(f"Material JSON {filename} is missing required field: {e}")

    @classmethod
    def from_dict(cls, data: dict, name: str = "Custom") -> "Material":
        """
        Helper method to create a material from an existing dictionary of old keys.
        """
        return cls(
            name=name,
            density=data.get("density", data.get("rho")),
            specific_heat=data.get("specific_heat", data.get("C_p")),
            thermal_conductivity=data.get("thermal_conductivity", data.get("k")),
            melting_temperature=data.get("melting_temperature", data.get("T_m")),
            boiling_temperature=data.get("boiling_temperature", data.get("T_b")),
            absorptivity=data.get("absorptivity", data.get("A")),
            thermal_diffusivity=data.get("thermal_diffusivity", data.get("alpha")),
            electrical_resistivity=data.get("electrical_resistivity", data.get("rho_e"))
        )

    def plot_absorptivity_models(self, wavelengths: np.ndarray = None, save_path: str = None):
        """
        Evaluates and plots all 5 mathematical models of absorptivity over a range of wavelengths.
        """
        import matplotlib.pyplot as plt
        if wavelengths is None:
            wavelengths = np.linspace(0.5e-6, 2.0e-6, 50)
            
        models = ['hagen_rubens', 'gusarov_smurov', 'boley_hex', 'boley_gaussian', 'boley_bimodal']
        labels = ['Hagen-Rubens', 'Gusarov-Smurov', 'Boley (Hexagonal)', 'Boley (Gaussian)', 'Boley (Bimodal)']
        
        fig, ax = plt.subplots(figsize=(8, 5))
        cmap = plt.cm.inferno
        colors = [cmap(i) for i in np.linspace(0.15, 0.85, len(models))]
        for m, lbl, color in zip(models, labels, colors):
            self.calculate_absorptivity(wavelengths, method=m)
            ax.plot(wavelengths * 1e9, self.absorptivity * 100, label=lbl, linewidth=2, color=color)
            
        ax.set_title(f"Absorptivity Models for {self.name}", fontsize=14, fontweight='bold')
        ax.set_xlabel("Wavelength (nm)", fontsize=12)
        ax.set_ylabel("Absorptivity (%)", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        return fig, ax
