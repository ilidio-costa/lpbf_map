# L-PBF Processing Maps Naming Conventions

To ensure the codebase remains maintainable, readable, and perfectly aligned with the physical equations it implements, we strictly adhere to a descriptive naming convention for all public APIs and core data structures.

This file provides a quick reference for developers and contributors.

---

## 1. Process Parameters

These variables capture the operational machine configuration.

| Descriptive Name      |    Legacy Symbol     | Description                                                | SI Unit       |
| :-------------------- | :------------------: | :--------------------------------------------------------- | :------------ |
| `laser_power`         |         `P`          | Power of the laser heat source.                            | $W$           |
| `scan_speed`          |         `v`          | Velocity of the laser along the scan vector.               | $m/s$         |
| `beam_radius`         |         `a`          | $1/e^2$ radius of the laser beam.                          | $m$           |
| `hatch_spacing`       |         `h`          | Distance between adjacent laser scan tracks.               | $m$           |
| `layer_thickness`     |         `t`          | Thickness of the deposited powder layer.                   | $m$           |
| `ambient_temperature` | `T_ambient` or `T_0` | Starting preheat temperature of the powder bed.            | $K$           |
| `wavelength`          | —                    | Laser wavelength used to compute absorptivity via the Hagen-Rubens model. | $m$ |

---

## 2. Material Properties

These variables represent the fixed intrinsic properties of the alloy.

| Descriptive Name | Legacy Symbol | Description | SI Unit |
| :--- | :---: | :--- | :--- |
| `density` | `rho` ($\rho$) | Material density. | $kg/m^3$ |
| `specific_heat` | `C_p` ($C_p$) | Specific heat capacity. | $J/(kg \cdot K)$ |
| `thermal_conductivity` | `k` ($k$) | Thermal conductivity. | $W/(m \cdot K)$ |
| `melting_temperature` | `T_m` ($T_m$) | Solidus/Liquidus point. | $K$ |
| `boiling_temperature` | `T_b` ($T_b$) | Evaporation/boiling point. | $K$ |
| `absorptivity` | `A` ($A$) | Nominal coupling coefficient of the laser. | Dimensionless |
| `thermal_diffusivity` | `alpha` ($\alpha$) | Derived property: $k / (\rho C_p)$. | $m^2/s$ |
| `electrical_resistivity`| `rho_e` ($\rho_e$)| Electrical resistivity (used in Hagen-Rubens). | $\Omega \cdot m$ |

---

## 3. Melt Pool Dimensions

These variables represent the physical size of the predicted molten region.

| Descriptive Name | Legacy Symbol | Description | SI Unit |
| :--- | :---: | :--- | :--- |
| `length` | `L` | Maximum extent of the melt pool along the scan vector. | $m$ |
| `width` | `W` | Maximum transverse width of the melt pool. | $m$ |
| `depth` | `D` | Maximum penetration depth of the melt pool into the substrate. | $m$ |

---

## 4. Dimensionless Parameters

These variables are used in scaling laws (like the Rubenchik model).

| Descriptive Name | Legacy Symbol | Description | Formula |
| :--- | :---: | :--- | :--- |
| `peclet_number` | `pe` or `Pe` | Ratio of advective to diffusive heat transport. | $\alpha / (v \cdot a)$ |
| `normalized_enthalpy` | `B` or `q_star` | Normalized heat input parameter. | $\frac{A \cdot P_{eff}}{\pi \rho C_p T_m \sqrt{\alpha v a^3}}$ |

---

## 5. Mathematical Shorthand in Equations

In deep physics files (e.g., inside `src/lpbf_printability/meltpool.py` or defect criteria), mathematical formulas can become extremely long and hard to align if full descriptive names are used.

**Rule:** You may use single-letter mathematical shorthand _only_ as local variables inside the immediate scope of a mathematical solver or formula. 

**Requirement:** If you do this, you **must** provide a comment block immediately preceding the shorthand mapping the shorthand back to the descriptive names.

**Example:**
```python
# Local shorthand for formula alignment:
#   p_val  -> peclet_number
#   B_val  -> normalized_enthalpy
#   xi, yi, zi -> dimensionless coordinates
p_val = thermal_diffusivity / (scan_speed * beam_radius)
B_val = (absorptivity * P_eff) / denominator
```
