# Contributing to L-PBF Processing Maps

First off, thank you for considering contributing to this project! It is research-oriented tools like this that help move additive manufacturing forward.

## Development Workflow

All development — whether adding materials, implementing new defect criteria, fixing bugs, or proposing features — is coordinated through **GitHub Issues**.

### The Issue-First Workflow

1. **Open an Issue first.** Before writing any code, open a GitHub Issue describing what you want to add or change. This ensures alignment with the project's goals and avoids duplicate work.
2. **Discuss the proposal.** Use the Issue thread to discuss the approach, share references, and get feedback from maintainers.
3. **Implement the change.** Once the Issue is approved, fork the repo and implement your changes.
4. **Submit a Pull Request.** Reference the Issue number in your PR description (e.g., `Closes #42`).

> **Pull requests without a prior Issue discussion are discouraged** and may be closed without review.

## How Can I Contribute?

### Expanding the Material Database
We aim to support as many alloys as possible. To add a new material:
1. **Open an Issue** with the alloy name, all thermophysical properties, and the scientific reference(s) for the data.
2. Once approved, navigate to the `src/lpbf_map/database/` directory.
3. Create a new `.json` file (e.g., `IN718.json`).
4. Ensure you include all required fields: `density`, `specific_heat`, `thermal_conductivity`, `boiling_temperature`, `melting_temperature`, `absorptivity`, and `electrical_resistivity`.

### Adding New Defect Criteria
If you have a new analytical model for defects (e.g., a specific porosity threshold):
1. **Open an Issue** describing the physical model, the governing equation, and the source publication.
2. Once approved, create a new Python file in `src/lpbf_map/defects/`.
3. Inherit from `DefectCriterion` and implement: `def check(self, melt_pool, idx) -> bool`.
4. Provide references for your model as they will be added to the documentation.

### Reporting Bugs
If you find a bug in the Eagar-Tsai or Rubenchik implementations, please open an Issue. Include:
* The material JSON used.
* The specific P-v parameters that caused the error.
* A description of the expected vs. actual result.

### Requesting Features
Feature requests are welcome! Please open an Issue tagged with `enhancement` and describe:
* The use case for the feature.
* How it fits within the existing architecture.
* Any relevant references or prior art.

## Pull Request Process
1. Fork the repo and create your branch from `main`.
2. Reference the related Issue in your PR description.
3. If you've added code, ensure your changes don't break the existing tests in the `tests/` directory.
4. Update the README.md or documentation if you changed core logic.
5. Submit the PR with a clear description of your changes and the scientific references supporting them.

## Community & Conduct
By participating in this project, you agree to abide by standard academic integrity and open-source cooperation.

Your name will be added to the contributors list in the README.md, and your contributions will be acknowledged in any publications resulting from this project.