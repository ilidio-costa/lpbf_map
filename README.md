[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![v0.1.0](https://img.shields.io/badge/version-0.1.0-yellow.svg)](https://github.com/ilidio-costa/L-PBF-Processing-Maps-Predictive-Analytical-Modelling/releases)

# Predictive Modeling Of L-PBF Printability Maps


<div align="center">
  <img src="images/Logo_LPBF.png" alt="L-PBF Processing Maps Logo" width="200">
</div align="left">


## Scientific Overview

The optimization of Laser Powder Bed Fusion (L-PBF) processing parameters is frequently constrained by the extensive experimental overhead required to identify stable melting regimes. This framework provides a predictive analytical solution to estimate melt pool morphology and evaluate manufacturing stability. By coupling classical thermal models with established defect criteria, the tool delineates "Safe Zones" from regions prone to balling, lack of fusion (LoF), and keyhole-induced porosity.

## Quick Start

### 1. Installation
Clone the repository and install the core dependencies:
```bash
git clone https://github.com/ilidio-costa/L-PBF-Processing-Maps-Predictive-Analytical-Modelling.git
cd L-PBF-Processing-Maps-Predictive-Analytical-Modelling
pip install -e .
```
## Theoretical Framework

### Thermal Modeling Strategy

To capture the complex heat transfer regimes in L-PBF, the engine employs a hybrid modeling approach:
- **Conduction Mode (Eagar-Tsai Model):** Utilizes a traveling Gaussian-distributed heat source on a semi-infinite substrate to predict surface dimensions ($W$ and $L$) .
- **Deep Penetration Mode (Gladush-Smurov Model):** Accounts for keyhole physics by treating the laser as a cylindrical heat source, providing accurate depth ($D$) predictions in high-intensity regimes .
- **Dimensionless Scaling (Rubenchik Model):** Normalizes spatial coordinates and thermal variables to determine melt pool dimensions via universal functions ($g$) and normalized enthalpy ($B$) .


### Defect Evaluation Criteria

The printability of a specific parameter set is defined by the simultaneous avoidance of multiple competing defect regimes. Each analytical criterion is encapsulated within an isolated Python module in the `src/lpbf_maps/defects/` directory and adheres to a standardized API. This modularity allows the framework to evaluate each physical instability independently while maintaining a unified hierarchical logic for final visualization.

The table below details the current defect modules, their underlying analytical models, and the mathematical conditions they evaluate:

### Algorithmic Implementation of Defect Criteria
| Defect Type | Analytical Model | Python Module | Legacy Name | Defect Condition (Returns `True`) |
| :--- | :--- | :--- | :--- | :--- |
| **Balling** | Plateau-Rayleigh | `balling.py` | `ball01.py` | $length/width \ge 2.3$ |
| **Balling** | Yadroitsev Stability | `balling_yadroitsev.py` | `ball02.py` | $(\pi \cdot width/length) \le \sqrt{2/3}$ |
| **Lack of Fusion** | Geometric Overlap | `lof.py` | `lof02.py`, `lof04.py` | $(hatch\_spacing/width)^2 + layer\_thickness/depth \ge 1.0$  |
| **Lack of Fusion** | Depth-to-Layer Ratio | `lof_depth_ratio.py` | `lof01.py`, `lof03.py` | $depth \le layer\_thickness \cdot threshold$  |
| **Keyholing** | Geometric Ratio | `keyhole_geometric.py` | `key02.py`, `key03.py`, `key04.py` | $width/depth < threshold$  |
| **Keyholing** | King Normalized Enthalpy | `keyhole_king.py` | `key01.py` | $\frac{A \cdot P}{\pi \rho C_p T_m \sqrt{\alpha v a^3}} > \frac{\pi T_b}{T_m}$  |
| **Keyholing** | Gan Universal | `keyhole_gan.py` | `key05.py` | $\frac{A \cdot P}{(T_m - T_{amb}) \pi \rho C_p \sqrt{\alpha v a^3}} > 6.0$  |

### Modular API and Priority Mapping
Each defect module inherits from `DefectCriterion` and uses a standardized class method: `def check(self, melt_pool, idx) -> bool`. This enables the core physics engine to:
* **Perform Isolated Evaluations**: Individual boundaries can be verified independently to confirm specific mathematical thresholds without interference from overlapping regimes.
* **Route Defect Priority**: In regions where multiple conditions are met, a priority-routing algorithm (`DefectSuite`) determines the dominant mechanism for visualization in the printability map.
* **Integrate Uncertainty**: Results can be normalized into model probabilities using a softmax function, identifying regions where predictive uncertainty is high (e.g., when models yield conflicting results).


## Repository Architecture & API Reference

The project follows a modular architecture ensuring a strict separation of concerns between physics, data management, and visualization.

### Physics Engine (`src/lpbf_maps/meltpool.py` & `printability.py`)
* **`PrintabilitySpace`**: Master orchestrator that evaluates a $P-v$ grid using lazy evaluation and applies defect priority mapping.
* **`MeltPool`**: Hybrid wrapper resolving surface dimensions via Rubenchik/Eagar-Tsai and depth via the maximum envelope of Gladush-Smurov and Eagar-Tsai. Dimensions are calculated lazily.

### Visualization Suite (`src/lpbf_maps/printability_plots.py` & `meltpool_plots.py`)
* **`plot_2d_printability_map`**: Renders pre-computed defect matrices using Gaussian-smoothed contours.

<div align="center">
  <img src="images/printability_map.png" alt="printability_map" width="400">
</div align="left">

* **`plot_3d_safe_zone_evolution`**: A multidimensional engine for "Third Axis" evaluation (e.g., sensitivity to $T_{ambient}$, spot size, or layer thickness).

<div align="center">
  <img src="images/printability_map_z_axis.png" alt="printability_map_z_axis" width="400">
</div align="left">

* **`plot_dimensions_2d`**: Generates high-fidelity 2D contour maps of the melt pool dimensions (Length, Width, Depth).

<div align="center">
  <img src="images/eagar_tsai.png" alt="melt pool" width="400">
</div align="left">

### Material Management (`src/lpbf_maps/materials.py`)
* **`Material.from_library()`**: Parses JSON files to calculate derived properties.

### Material JSON Structure
To ensure physical accuracy, thermophysical properties (Density, Specific Heat, and Thermal Conductivity) should be extracted at or near the material's melting point. Material files in the `src/lpbf_maps/database/` directory follow this structure:

```json
{
    "name": "NiTi",
    "density": 6100,
    "specific_heat": 510,
    "thermal_conductivity": 4.4,
    "boiling_temperature": 3033,
    "melting_temperature": 1583,
    "absorptivity": 0.32,
    "electrical_resistivity": 8.2e-7
}
```

| JSON Key | Description | Symbol | Units |
| :--- | :--- | :---: | :--- |
| `density` | Density | $\rho$ | $kg/m^{3}$ |
| `specific_heat` | Specific Heat Capacity | $C_{p}$ | $J/(kg \cdot K)$  |
| `thermal_conductivity` | Thermal Conductivity | $k$ | $W/(m \cdot K)$  |
| `boiling_temperature` | Boiling Temperature | $T_{b}$ | $K$  |
| `melting_temperature` | Melting Temperature | $T_{m}$ | $K$  |
| `absorptivity` | Laser Absorptivity | $A$ | Dimensionless  |
| `electrical_resistivity` | Electrical Resistivity | $\rho_{e}$ | $\Omega \cdot m$  |

## References

- B. Zhang et al., "An efficient framework for printability assessment in laser powder bed fusion metal additive manufacturing," *Additive Manufacturing*, vol. 46, p. 102018, 2021.

- S. Sheikh et al., "High-throughput alloy and process design for metal additive manufacturing," *npj Computational Materials*, vol. 11, no. 1, 2025.

- T. W. Eagar and N.-s. Tsai, "Temperature fields produced by traveling distributed heat sources," *Welding Journal*, vol. 62, no. 12, pp. 346s-355s, 1983.

- J.-N. Zhu et al., "Predictive analytical modelling and experimental validation of processing maps in additive manufacturing of nitinol alloys," *Additive Manufacturing*, vol. 38, p. 101802, 2021.

- S. Sheikh et al., "An automated computational framework to construct printability maps for additively manufactured metal alloys," *npj Computational Materials*, vol. 10, no. 1, 2024.

- Thermo-Calc Software AB, "Thermo-Calc Software Additive Manufacturing Module: Methodology for calculation of phase diagrams (CALPHAD) and steady-state melt pool simulations," Solna, Sweden, 2026.

- L. Johnson et al., "Assessing printability maps in additive manufacturing of metal alloys," *SSRN Electronic Journal*, 2019.

- N. Wu, B. Whalen, J. Ma, and P. V. Balachandran, "Probabilistic printability maps for laser powder bed fusion via functional calibration and uncertainty propagation," *Journal of Computing and Information Science in Engineering*, vol. 24, no. 11, 2024.

- X. Huang et al., "Hybrid microstructure-defect printability map in laser powder bed fusion additive manufacturing," *Computational Materials Science*, vol. 209, p. 111401, 2022.

- I. Yadroitsev, A. Gusarov, I. Yadroitsava, and I. Smurov, "Single track formation in selective laser melting of metal powders," *Journal of Materials Processing Technology*, vol. 210, no. 12, pp. 1624-1631, 2010.

- R. Seede et al., "An ultra-high strength martensitic steel fabricated using selective laser melting additive manufacturing: Densification, microstructure, and mechanical properties," *Acta Materialia*, vol. 186, pp. 199-214, 2020.

- W. E. King et al., "Observation of keyhole-mode laser melting in laser powder-bed fusion additive manufacturing," *Journal of Materials Processing Technology*, vol. 214, no. 12, pp. 2915-2925, 2014.

- Z. Gan et al., "Universal scaling laws of keyhole stability and porosity in 3D printing of metals," *Nature Communications*, vol. 12, no. 1, 2021.

- S. Sinha and T. Mukherjee, "Mitigation of gas porosity in additive manufacturing using experimental data analysis and mechanistic modeling," *Materials*, vol. 17, no. 7, p. 1569, 2024.

- A. M. Rubenchik, W. E. King, and S. S. Wu, "Scaling laws for the additive manufacturing," *Journal of Materials Processing Technology*, vol. 257, pp. 234-243, 2018.

- D. Schuöcker, *Handbook of the Eurolaser Academy*, Springer International Publishing.

## Citation
If you use this simulator in your research, please cite it as:
> [Ilídio Costa] ([2026]). Predictive Modeling Of L-PBF Printability Maps (v1.0.0). Zenodo. https://doi.org/10.5281/zenodo.19118312


## License
Distributed under the **GPLv3 License**. See `LICENSE` for details.

## Author
**Ilídio Costa**
*Personal Project Report: PP-LPBF-PMOLPM-001*

## Contributing
Contributions are what make the research community thrive! Whether you are a materials scientist or a software engineer, your input is welcome. 

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.
