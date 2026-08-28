"""Tunables. 1 place, no magic numbers in code."""
from pathlib import Path

# Margin audit thresholds
TARGET_TAKE_RATE = 0.15  # >15% intermediary take = flagged
SPO_SCORE_WEIGHTS = {"margin": 0.5, "latency": 0.3, "clarity": 0.2}

# Generator presets
SCENARIOS = {
    "A": "direct",          # Pub -> SSP -> DSP, clean 1-hop
    "B": "margin_leak",     # 3-hop w/ hidden fees
    "C": "duplication",     # 5 parallel paths, 1 imp
}

DATA_DIR = Path(__file__).parent / "data"
MOCK_SELLERS = DATA_DIR / "mock_sellers.json"
