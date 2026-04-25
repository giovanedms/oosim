"""Tests for SGP4 wrapper."""
from datetime import datetime, timezone
import numpy as np
import pytest

from oosim.utils.sgp4_wrapper import HAVE_SGP4, propagate_tle, ISS_SAMPLE_TLE


@pytest.mark.skipif(not HAVE_SGP4, reason="sgp4 library not installed")
def test_propagate_iss_sample_tle_returns_iss_altitude_state():
    """ISS sample TLE should propagate to a position at ~ISS altitude."""
    when = datetime(2024, 1, 18, 12, 0, 0, tzinfo=timezone.utc)
    r, v = propagate_tle(ISS_SAMPLE_TLE[0], ISS_SAMPLE_TLE[1], when)
    altitude = np.linalg.norm(r) - 6378.137
    assert 350.0 < altitude < 500.0  # ISS altitude ~408 km
    speed = np.linalg.norm(v)
    assert 7.5 < speed < 7.9  # ~7.66 km/s for ISS


@pytest.mark.skipif(not HAVE_SGP4, reason="sgp4 library not installed")
def test_propagate_tle_requires_aware_datetime():
    naive = datetime(2024, 1, 18, 12, 0, 0)  # no tzinfo
    with pytest.raises(ValueError):
        propagate_tle(ISS_SAMPLE_TLE[0], ISS_SAMPLE_TLE[1], naive)
