"""Thin wrapper around the official `sgp4` Python library for TLE propagation.

The SGP4 propagator (Brouwer-Lyddane mean to osculating, with first-order J2/J3/J4
secular and short-period corrections) is the de facto standard for TLE-based
orbit determination of Earth-orbiting satellites with ~1 km accuracy over a
few-day window. We use it to anchor RPOD-50 simulations to real flight epochs.

Reference:
    Vallado, D. A. & Crawford, P. (2008). SGP4 Orbit Determination. AIAA-2008-6770.
    https://celestrak.org/publications/AIAA/2008-6770/
"""
from datetime import datetime, timezone
import numpy as np

try:
    from sgp4.api import Satrec, jday
    HAVE_SGP4 = True
except ImportError:
    HAVE_SGP4 = False


def propagate_tle(line1: str, line2: str, when: datetime
                  ) -> tuple[np.ndarray, np.ndarray]:
    """Propagate a TLE to a given UTC instant.

    Args:
        line1, line2: the two 69-character TLE lines.
        when: target epoch (must be timezone-aware UTC).

    Returns:
        (r_eci, v_eci): 3-vectors in km and km/s, in TEME-of-date.
    """
    if not HAVE_SGP4:
        raise RuntimeError("sgp4 library not installed. pip install sgp4")
    if when.tzinfo is None:
        raise ValueError("'when' must be timezone-aware UTC")
    when_utc = when.astimezone(timezone.utc)
    sat = Satrec.twoline2rv(line1, line2)
    jd, fr = jday(when_utc.year, when_utc.month, when_utc.day,
                  when_utc.hour, when_utc.minute,
                  when_utc.second + when_utc.microsecond * 1e-6)
    e, r, v = sat.sgp4(jd, fr)
    if e != 0:
        raise RuntimeError(f"SGP4 propagation error code {e}")
    return np.array(r), np.array(v)


# Reference TLE for ISS (ZARYA) — for documentation/testing purposes.
# Source: CelesTrak, https://celestrak.org/NORAD/elements/stations.txt
# This is a SAMPLE entry; replace with a fresh TLE from CelesTrak for real use.
ISS_SAMPLE_TLE = (
    "1 25544U 98067A   24018.50000000  .00012345  00000-0  22222-3 0  9990",
    "2 25544  51.6400 123.4567 0001234  56.7890 303.4321 15.50000000123456",
)
