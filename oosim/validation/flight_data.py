"""Load mission data from the RPOD-50 dataset CSV."""
import os
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Candidate locations for the RPOD-50 dataset directory, in search order:
# 1. OOSIM_DATASET_DIR environment variable (explicit override)
# 2. Sibling of the repo checkout (../dataset, the working layout)
# 3. <repo_root>/dataset (dataset copied/vendored into the repo)
def _dataset_candidates() -> list[Path]:
    candidates = []
    env_dir = os.environ.get("OOSIM_DATASET_DIR")
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.append(_REPO_ROOT.parent / "dataset")
    candidates.append(_REPO_ROOT / "dataset")
    return candidates


def resolve_dataset_path() -> Path:
    """Return the path to missions.csv, searching the candidate locations."""
    candidates = _dataset_candidates()
    for directory in candidates:
        csv_path = directory / "missions.csv"
        if csv_path.is_file():
            return csv_path
    searched = "\n".join(f"  - {d / 'missions.csv'}" for d in candidates)
    raise FileNotFoundError(
        "RPOD-50 dataset (missions.csv) not found. Searched, in order:\n"
        f"{searched}\n"
        "Set the OOSIM_DATASET_DIR environment variable to the dataset "
        "directory, place the dataset next to the repo checkout, or copy it "
        "to <repo_root>/dataset. The dataset will also be archived on Zenodo "
        "(RPOD-50, DOI to be assigned at the v1.0 release)."
    )



def list_missions() -> pd.DataFrame:
    """Return the full RPOD-50 dataset table."""
    return pd.read_csv(resolve_dataset_path())


def load_mission(mission_id: str) -> dict:
    """Load a single mission row as dict, by mission_id."""
    df = list_missions()
    row = df[df["mission_id"] == mission_id]
    if row.empty:
        raise KeyError(f"mission_id '{mission_id}' not found in dataset")
    return row.iloc[0].to_dict()
