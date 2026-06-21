from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence
import re
import pandas as pd
import numpy as np

COMMON_COLUMN_ALIASES = {
    "ICE": "ice_percent",
    "ICE (%)": "ice_percent",
    "initial_coulombic_efficiency": "ice_percent",
    "capacity": "reversible_capacity_mah_g",
    "reversible_capacity": "reversible_capacity_mah_g",
    "BET": "bet_m2_g",
    "BET_surface_area": "bet_m2_g",
    "SBET": "bet_m2_g",
    "d002": "d002_nm",
    "ID/IG": "id_ig",
    "IDIG": "id_ig",
    "N_content": "n_at_percent",
    "O_content": "o_at_percent",
    "current_density": "current_density_mag",
    "mass_loading": "mass_loading_mg_cm2",
    "source": "source_location",
}

NUMERIC_CANDIDATES = [
    "year",
    "carbonization_temperature_c",
    "bet_m2_g",
    "total_pore_volume_cm3_g",
    "d002_nm",
    "id_ig",
    "n_at_percent",
    "o_at_percent",
    "current_density_mag",
    "mass_loading_mg_cm2",
    "ice_percent",
    "reversible_capacity_mah_g",
    "specific_capacitance_f_g",
]

REQUIRED_AUDIT_COLUMNS = ["sample_id", "paper_id"]

DEFAULT_FEATURES = [
    "carbonization_temperature_c",
    "bet_m2_g",
    "total_pore_volume_cm3_g",
    "d002_nm",
    "id_ig",
    "n_at_percent",
    "o_at_percent",
    "current_density_mag",
    "mass_loading_mg_cm2",
]


def slugify_column(name: str) -> str:
    name = str(name).strip()
    if name in COMMON_COLUMN_ALIASES:
        return COMMON_COLUMN_ALIASES[name]
    name = re.sub(r"[%()\[\]/]+", "_", name)
    name = re.sub(r"[^0-9a-zA-Z_]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    return COMMON_COLUMN_ALIASES.get(name, name)


def read_table(path: str | Path, sheet: str | int | None = None) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(path, sheet_name=sheet or 0)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported input format: {path.suffix}. Use CSV or XLSX.")
    df = normalize_columns(df)
    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [slugify_column(c) for c in df.columns]
    for col in NUMERIC_CANDIDATES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["quality_tier", "needs_manual_check", "paper_id", "sample_id", "device_system"]:
        if col in df.columns:
            df[col] = df[col].astype("string")
    return df


def ensure_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = pd.NA
    return df


def boolish_yes(series: pd.Series) -> pd.Series:
    return series.astype("string").str.lower().isin(["yes", "y", "true", "1", "是", "需要"])


def numeric_features(df: pd.DataFrame, requested: Sequence[str] | None = None) -> list[str]:
    cols = list(requested or DEFAULT_FEATURES)
    return [c for c in cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]


def target_outlier_flags(df: pd.DataFrame, target: str) -> pd.Series:
    if target not in df.columns:
        return pd.Series(False, index=df.index)
    y = pd.to_numeric(df[target], errors="coerce")
    q1 = y.quantile(0.25)
    q3 = y.quantile(0.75)
    iqr = q3 - q1
    if pd.isna(iqr) or iqr == 0:
        return pd.Series(False, index=df.index)
    return (y > q3 + 1.5 * iqr) | (y < q1 - 1.5 * iqr)


def write_markdown_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "_None._\n"
    preview = df.head(max_rows).copy()
    return preview.to_markdown(index=False) + ("\n" if len(df) <= max_rows else f"\n\n_Showing {max_rows} of {len(df)} rows._\n")
