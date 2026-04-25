"""Load mission data from the RPOD-50 dataset CSV."""
from pathlib import Path
import pandas as pd

DATASET_PATH = Path(__file__).resolve().parents[3] / "dataset" / "missions.csv"


def list_missions() -> pd.DataFrame:
    """Return the full RPOD-50 dataset table."""
    return pd.read_csv(DATASET_PATH)


def load_mission(mission_id: str) -> dict:
    """Load a single mission row as dict, by mission_id."""
    df = list_missions()
    row = df[df["mission_id"] == mission_id]
    if row.empty:
        raise KeyError(f"mission_id '{mission_id}' not found in dataset")
    return row.iloc[0].to_dict()
