import pytest

from itmlogic.qlrps import qlrps

def test_qlrps():
    fmhz = 1
    zsys = 1
    en0 = 1
    ipol = 1
    eps = 1
    sgm = 1
    wn, gme, ens, zgnd = qlrps(fmhz, zsys, en0, ipol, eps, sgm)

    # NB - these values obtained from running qlrps as-is, so can only test regressions
    assert wn == pytest.approx(0.02096436)
    assert gme == pytest.approx(1.49634e-7)
    assert ens == pytest.approx(0.99989429)
    assert zgnd == pytest.approx(0.00527592-0.00527533j)
