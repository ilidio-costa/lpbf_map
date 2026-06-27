import pytest
from lpbf_map.materials import Material

def test_material_initialization():
    mat = Material(
        name="Test",
        density=4430,
        specific_heat=526,
        thermal_conductivity=6.7,
        melting_temperature=1923,
        boiling_temperature=3533,
        absorptivity=0.3
    )
    assert mat.name == "Test"
    assert mat.density == 4430
    assert pytest.approx(mat.thermal_diffusivity, rel=1e-3) == 6.7 / (4430 * 526)

def test_material_invalid_limits():
    with pytest.raises(ValueError, match="Density must be > 0"):
        Material("Test", -10, 500, 10, 1000, 2000, 0.5)

def test_material_from_library():
    # Test that we can load the default Ti64 material securely shipped with the database
    mat = Material.from_library("Ti64")
    assert mat.name == "Ti-6Al-4V"
    assert mat.density == 4250
    assert mat.melting_temperature == 1877

def test_material_from_library_missing():
    with pytest.raises(FileNotFoundError):
        Material.from_library("DoesNotExist")
