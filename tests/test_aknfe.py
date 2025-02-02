import pytest
from itmlogic.aknfe import aknfe

def test_aknfe():

    assert round(aknfe(-1), 2) == 6.05
    assert round(aknfe(2), 2) == 16.36
    assert round(aknfe(3), 2) == 17.99
    assert round(aknfe(5), 2) == 20.04
    assert round(aknfe(6), 2) == 20.73
