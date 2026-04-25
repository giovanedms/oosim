"""Additional coordinate-frame transforms beyond the basic ECI <-> LVLH.

Implements:
    RTN (Radial-Tangential-Normal) — equivalent to LVLH but with z = orbit normal
    ECEF (Earth-Centered Earth-Fixed) — rotates with Earth at omega_earth
    Perifocal (PQW) — Keplerian element frame
    Conversion Keplerian elements <-> Cartesian state

Reference: Vallado (2022) Ch. 3.
"""
import numpy as np

MU_EARTH = 398600.4418
OMEGA_EARTH = 7.2921150e-5  # rad/s, sidereal


def eci_to_ecef(r_eci: np.ndarray, gmst_rad: float) -> np.ndarray:
    """Rotate ECI to ECEF using Greenwich Mean Sidereal Time."""
    c, s = np.cos(gmst_rad), np.sin(gmst_rad)
    R = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])
    return R @ r_eci


def perifocal_to_eci(omega: float, inc: float, raan: float) -> np.ndarray:
    """Rotation matrix from perifocal (PQW) to ECI for given angles in radians.

    omega: argument of perigee, inc: inclination, raan: RAAN.
    """
    co, so = np.cos(omega), np.sin(omega)
    ci, si = np.cos(inc), np.sin(inc)
    cR, sR = np.cos(raan), np.sin(raan)
    return np.array([
        [cR*co - sR*so*ci, -cR*so - sR*co*ci, sR*si],
        [sR*co + cR*so*ci, -sR*so + cR*co*ci, -cR*si],
        [so*si,             co*si,            ci],
    ])


def keplerian_to_cartesian(a: float, e: float, inc: float, raan: float,
                            argp: float, true_anom: float,
                            mu: float = MU_EARTH) -> tuple[np.ndarray, np.ndarray]:
    """Convert classical orbital elements to ECI position and velocity.

    Args:
        a: semi-major axis [km].
        e: eccentricity (0..1).
        inc, raan, argp, true_anom: angles [rad].

    Returns:
        (r_eci, v_eci): position [km], velocity [km/s].
    """
    p = a * (1.0 - e * e)
    r_pqw = np.array([
        p * np.cos(true_anom) / (1.0 + e * np.cos(true_anom)),
        p * np.sin(true_anom) / (1.0 + e * np.cos(true_anom)),
        0.0,
    ])
    v_pqw = np.sqrt(mu / p) * np.array([
        -np.sin(true_anom),
        e + np.cos(true_anom),
        0.0,
    ])
    R = perifocal_to_eci(argp, inc, raan)
    return R @ r_pqw, R @ v_pqw


def cartesian_to_keplerian(r: np.ndarray, v: np.ndarray,
                            mu: float = MU_EARTH) -> dict:
    """Convert ECI Cartesian state to classical orbital elements.

    Returns a dict with keys: a, e, inc, raan, argp, true_anom (all in rad
    except a in km).
    """
    r_norm = float(np.linalg.norm(r))
    v_norm = float(np.linalg.norm(v))
    h = np.cross(r, v)
    h_norm = float(np.linalg.norm(h))
    n = np.cross(np.array([0., 0., 1.]), h)
    n_norm = float(np.linalg.norm(n))

    e_vec = ((v_norm ** 2 - mu / r_norm) * r - np.dot(r, v) * v) / mu
    e = float(np.linalg.norm(e_vec))
    energy = v_norm ** 2 / 2.0 - mu / r_norm
    a = -mu / (2.0 * energy)

    inc = float(np.arccos(np.clip(h[2] / h_norm, -1.0, 1.0)))
    raan = float(np.arccos(np.clip(n[0] / n_norm, -1.0, 1.0))) if n_norm > 1e-12 else 0.0
    if n_norm > 1e-12 and n[1] < 0:
        raan = 2 * np.pi - raan
    argp = float(np.arccos(np.clip(np.dot(n, e_vec) / (n_norm * e), -1.0, 1.0))) if n_norm > 1e-12 and e > 1e-12 else 0.0
    if e_vec[2] < 0:
        argp = 2 * np.pi - argp
    nu = float(np.arccos(np.clip(np.dot(e_vec, r) / (e * r_norm), -1.0, 1.0))) if e > 1e-12 else 0.0
    if np.dot(r, v) < 0:
        nu = 2 * np.pi - nu

    return {"a": a, "e": e, "inc": inc, "raan": raan, "argp": argp, "true_anom": nu}
