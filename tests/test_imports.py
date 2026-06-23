import pytest

def test_package_import():
    import lpbf_maps
    assert lpbf_maps.__version__ == "0.1.0"
