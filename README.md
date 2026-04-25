# OOSim — Open On-Orbit Servicing Simulator

End-to-end Python framework for simulating rendezvous and robotic berthing for on-orbit servicing missions, with QP-based berthing-compatible terminal targeting and validation against operational mission data.

**Companion code for:**
- IAC 2026 paper `IAC-26,C2,3,6,x112752` — *Computational Simulation of Rendezvous and Robotic Berthing for On-Orbit Servicing: Validation Against Operational Mission Data*
- RPOD-50 Dataset — see `../dataset/`

## Architecture

```
oosim/
├── phasing/        # Hohmann transfers, J2 secular drift, finite-burn corrections
├── proxops/        # Hill-Clohessy-Wiltshire dynamics, V-bar/R-bar enforcement
├── attitude/       # Quaternion + Euler dynamics, RCS phase-plane control
├── targeting/      # Capture envelope formalization + QP-based terminal targeting
├── validation/     # Mission data loaders, metrics computation
└── utils/          # Coordinate transforms (ECI/LVLH/RTN), time conversions
```

## Quick start

```bash
pip install -e .[dev]
pytest
```

## Authors

Giovane Morais, Ijar Milagre da Fonseca, Emília Villani — Instituto Tecnológico de Aeronáutica (ITA), Brazil.

## License

Code: see `LICENSE-CODE` (MIT). Dataset: see `../dataset/LICENSE-DATA` (CC-BY-4.0).
