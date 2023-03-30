from ansys.dpf.composites import __version__


def test_pkg_version():
    assert __version__ == "0.2b1"
