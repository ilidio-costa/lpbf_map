# Dependencies

The **L-PBF Processing Maps Predictive Analytical Modelling** library relies on the standard scientific Python stack to evaluate equations, solve boundaries numerically, and visualize processing maps.

## Recommended Environment
- **Python Version**: 3.8 to 3.12 (Tested primarily on Python 3.10)

## Core Libraries

| Library          | Typical Usage in Project                                                                                                                                                                                                                     |
| :--------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`numpy`**      | Used throughout the `ProcessParameters`, `Material`, and physics solvers for vectorized mathematical operations, creating multi-dimensional evaluation grids, and matrix slicing.                                                            |
| **`scipy`**      | Used specifically for the numerical boundary solvers (e.g. `scipy.optimize.brentq`, `scipy.optimize.minimize_scalar`) and integration functions (`scipy.integrate.fixed_quad`) to resolve exact meltpool dimensions and thermal field peaks. |
| **`matplotlib`** | Used to generate the 2D Printability Maps, 3D processing windows, and the thermal cross-section side-views (`contour` and `contourf` fields).                                                                                                |

## Standard Library Modules

The project natively relies on standard Python packages without external requirements:
- **`json`**: To load the `.json` material database files.
- **`dataclasses`**: To elegantly structure the `ProcessParameters` and `Material` configurations.
- **`importlib.resources`**: To robustly locate the internal `database/` folder when the package is installed, preventing brittle file-path errors.
- **`typing`**: For robust internal type hints (`Optional`, `Union`, etc).

## Development and Examples
- **`jupyter`** (or `notebook` / `jupyterlab`): Needed to open and run the case studies inside the `examples/` directory.

## Optional Packaging
If you want to package the project, standard `setuptools` is utilized via the `pyproject.toml` file.
