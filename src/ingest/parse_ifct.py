"""Normalize the raw IFCT 2017 dataset into data/processed/ingredients.parquet.

Source: IFCT 2017 (Indian Food Composition Tables, ICMR-National Institute
of Nutrition), via the community-maintained CSV export at
https://github.com/nodef/ifct2017 (data/raw/ifct2017/, AGPL-3.0 — see
data/raw/ifct2017/NOTICE.md).
"""
import re
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "ifct2017"
OUT_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "ingredients.parquet"

KJ_PER_KCAL = 4.184

# Atwater general factors (kcal per gram), used only as a fallback below.
ATWATER_PROTEIN = 4
ATWATER_FAT = 9
ATWATER_CARBS = 4

# Starting point only, not a finished list. IFCT's own local-name columns
# (parsed below) cover most regional variants; this fills gaps for common
# household terms that don't appear verbatim in the source data. Expand as
# more variants are identified.
MANUAL_ALIASES = {
    "B021": ["toor dal", "tur dal"],  # red gram dal / arhar dal / tuvar dal
    "B001": ["chana dal", "bengal gram dal"],
    "T013": ["ghee", "clarified butter"],
    "A015": ["chawal", "white rice", "cooked rice"],
}

_LANG_PREFIX_RE = re.compile(r"^(?:[A-Za-z]{1,4}\.,?\s*)+")


def _clean_alias(raw: str) -> str | None:
    text = raw.strip().rstrip(".")
    text = _LANG_PREFIX_RE.sub("", text).strip()
    return text or None


def _split_local_names(desc: str) -> list[str]:
    if not isinstance(desc, str) or not desc.strip():
        return []
    names = []
    for part in desc.split(";"):
        cleaned = _clean_alias(part)
        if cleaned:
            names.append(cleaned)
    return names


def _expand_codes(code_field: str) -> list[str]:
    return [c.strip() for c in str(code_field).split(",") if c.strip()]


def build_alias_map(codes: pd.DataFrame, descriptions: pd.DataFrame) -> dict[str, set[str]]:
    alias_map: dict[str, set[str]] = {}

    for _, row in codes.iterrows():
        for code in _expand_codes(row["code"]):
            alias_map.setdefault(code, set()).add(str(row["name"]).strip())

    for _, row in descriptions.iterrows():
        code = str(row["code"]).strip()
        for name in _split_local_names(row.get("desc")):
            alias_map.setdefault(code, set()).add(name)

    for code, aliases in MANUAL_ALIASES.items():
        alias_map.setdefault(code, set()).update(aliases)

    return alias_map


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    compositions = pd.read_csv(RAW_DIR / "compositions.csv")
    codes = pd.read_csv(RAW_DIR / "codes.csv")
    descriptions = pd.read_csv(RAW_DIR / "descriptions.csv")
    return compositions, codes, descriptions


def parse() -> pd.DataFrame:
    compositions, codes, descriptions = load_raw()
    alias_map = build_alias_map(codes, descriptions)

    records = []
    for _, row in compositions.iterrows():
        code = str(row["code"]).strip()
        name = str(row["name"]).strip()

        aliases = sorted(
            a for a in alias_map.get(code, set()) if a.lower() != name.lower()
        )

        protein_g = float(row["protcnt"])
        fat_g = float(row["fatce"])
        carbs_g = float(row["choavldf"])

        # A handful of source rows (pure edible oils/ghee, e.g. T013) have
        # enerc == 0 despite fatce == 100 -- IFCT's source table leaves
        # energy blank for these rather than measuring it directly. Fall
        # back to Atwater general factors so oil/ghee entries aren't
        # silently recorded as zero-calorie.
        raw_enerc_kj = float(row["enerc"])
        if raw_enerc_kj == 0 and (protein_g or fat_g or carbs_g):
            energy_kcal = (
                protein_g * ATWATER_PROTEIN
                + fat_g * ATWATER_FAT
                + carbs_g * ATWATER_CARBS
            )
        else:
            energy_kcal = raw_enerc_kj / KJ_PER_KCAL

        records.append(
            {
                "ingredient_id": code,
                "name": name,
                "aliases": aliases,
                "energy_kcal_per_100g": round(energy_kcal, 1),
                "protein_g_per_100g": protein_g,
                "fat_g_per_100g": fat_g,
                "carbs_g_per_100g": carbs_g,
                "fiber_g_per_100g": float(row["fibtg"]),
                "source": "IFCT",
            }
        )

    return pd.DataFrame.from_records(records)


def main() -> None:
    df = parse()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PATH, index=False)
    print(f"Wrote {len(df)} ingredients to {OUT_PATH}")


if __name__ == "__main__":
    main()
