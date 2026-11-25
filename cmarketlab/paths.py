"""Locations used across the package."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = Path(r"C:\ClaudeSandbox\shared-data")      # read-only: read in place, never write here
PERPS_1H = SHARED / "binance-perps-1h" / "binance_perps_1h.parquet"
CACHE = ROOT / "cache"                                # derived data (git-ignored); safe to delete
RESEARCH = ROOT / "research"


def cache_path(name: str) -> Path:
    CACHE.mkdir(exist_ok=True)
    return CACHE / name
