"""Soyuz MS-17 ultra-rapid 2-orbit profile reference data (October 2020).

This is the central validation case for the OOSim framework in the IAC paper.
On 14 October 2020, Soyuz MS-17 set the all-time launch-to-dock record for the
ISS at 3 hours 3 minutes 38 seconds, using the new two-orbit ultra-fast profile
developed at RKK Energia by Murtazin and collaborators.

References (validated DOIs):
    Murtazin, R., Sevastiyanov, N., Chudinov, N. (2020). Fast rendezvous profile
        evolution: From ISS to lunar station. Acta Astronautica 173:139-144.
        DOI: 10.1016/j.actaastro.2020.04.032
    Murtazin, R. & Petrov, N. (2012). Short profile for the human spacecraft
        Soyuz-TMA rendezvous mission to the ISS. Acta Astronautica 77:77-82.
        DOI: 10.1016/j.actaastro.2012.03.019

Per-burn delta-v values are from RussianSpaceWeb (Anatoly Zak compilation,
secondary source — flagged 🟡 in RPOD-50 dataset). Recommended action before
publication: confirm against Murtazin 2020 paper text or contact RKK Energia.
URL: https://www.russianspaceweb.com/soyuz-ms-17.html
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Burn:
    """A single rendezvous maneuver."""
    name: str
    t_from_launch_min: float  # minutes after liftoff
    delta_v_ms: float          # m/s
    notes: str = ""


@dataclass(frozen=True)
class MissionRef:
    """Reference data for a single rendezvous mission."""
    mission_id: str
    launch_utc: str
    dock_utc: str
    launch_to_dock_min: float
    profile_orbits: int
    burns: tuple
    total_dv_ms: float
    target_port: str
    gnc_system: str
    capture_mechanism: str
    granularity: str
    primary_doi: str = ""
    primary_url: str = ""
    secondary_url: str = ""
    notes: str = ""


SOYUZ_MS17 = MissionRef(
    mission_id="SOYUZ_MS17",
    launch_utc="2020-10-14T05:45:04Z",
    dock_utc="2020-10-14T08:48:53Z",
    launch_to_dock_min=183.63,  # 3h 03min 38s
    profile_orbits=2,
    burns=(
        Burn("DV1", 41.2, 11.2, "First phasing maneuver after insertion"),
        Burn("DV2", 87.0, 50.9, "Second phasing maneuver"),
        Burn("DV3", 145.0, 48.6, "Terminal initiation / final approach"),
    ),
    total_dv_ms=110.7,
    target_port="ISS Rassvet MIM-1 nadir",
    gnc_system="Kurs-NA digital",
    capture_mechanism="SSVP-G4000 probe-and-drogue",
    granularity="HIGH",
    primary_doi="10.1016/j.actaastro.2020.04.032",
    primary_url="https://www.nasa.gov/image-article/soyuz-ms-17-spacecraft-docked-space-station/",
    secondary_url="https://www.russianspaceweb.com/soyuz-ms-17.html",
    notes=(
        "Per-burn delta-v values from RussianSpaceWeb 🟡. Confirm with "
        "Murtazin 2020 paper body before publication."
    ),
)
