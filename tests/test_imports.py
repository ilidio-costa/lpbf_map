import pytest

def test_package_import():
    import lpbf_map
    assert lpbf_map.__version__ == "0.1.0"
