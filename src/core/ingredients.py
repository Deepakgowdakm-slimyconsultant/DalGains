"""Lookup helpers over the processed ingredients table."""
from pathlib import Path

import pandas as pd

INGREDIENTS_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "ingredients.parquet"


def load_ingredients(path: Path = INGREDIENTS_PATH) -> pd.DataFrame:
    return pd.read_parquet(path)


def find_ingredient(df: pd.DataFrame, query: str) -> pd.Series | None:
    """Look up an ingredient by exact name or alias match (case-insensitive)."""
    query_lower = query.strip().lower()

    name_match = df[df["name"].str.lower() == query_lower]
    if not name_match.empty:
        return name_match.iloc[0]

    for _, row in df.iterrows():
        if any(alias.lower() == query_lower for alias in row["aliases"]):
            return row

    return None
