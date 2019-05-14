# Pytest customization
from __future__ import division, absolute_import, print_function

import os
import pytest
import warnings

from distutils.version import LooseVersion
from scipy._lib._fpumode import get_fpu_mode
from scipy._lib._testutils import FPUModeChangeWarning


def pytest_configure(config):
    config.addinivalue_line("addopts",
        "-l")

    config.addinivalue_line("markers",
        "slow: Tests that are very slow.")
    config.addinivalue_line("markers",
        "xslow: mark test as extremely slow (not run unless explicitly requested)")

    config.addinivalue_line("filterwarnings",
        "error")
    config.addinivalue_line("filterwarnings",
        "always::scipy._lib._testutils.FPUModeChangeWarning")
    config.addinivalue_line("filterwarnings",
        "once:.*LAPACK bug 0038.*:RuntimeWarning")
    config.addinivalue_line("filterwarnings",
        "ignore:Using or importing the ABCs from 'collections'*:DeprecationWarning")
    config.addinivalue_line("filterwarnings",
        "ignore:can't resolve package from __spec__ or __package__, falling back on __name__ and __path__:ImportWarning")

    config.addinivalue_line("env",
        "PYTHONHASHSEED=0")


def pytest_runtest_setup(item):
    if LooseVersion(pytest.__version__) >= LooseVersion("3.6.0"):
        mark = item.get_closest_marker("xslow")
    else:
        mark = item.get_marker("xslow")
    if mark is not None:
        try:
            v = int(os.environ.get('SCIPY_XSLOW', '0'))
        except ValueError:
            v = False
        if not v:
            pytest.skip("very slow test; set environment variable SCIPY_XSLOW=1 to run it")


@pytest.fixture(scope="function", autouse=True)
def check_fpu_mode(request):
    """
    Check FPU mode was not changed during the test.
    """
    old_mode = get_fpu_mode()
    yield
    new_mode = get_fpu_mode()

    if old_mode != new_mode:
        warnings.warn("FPU mode changed from {0:#x} to {1:#x} during "
                      "the test".format(old_mode, new_mode),
                      category=FPUModeChangeWarning, stacklevel=0)
