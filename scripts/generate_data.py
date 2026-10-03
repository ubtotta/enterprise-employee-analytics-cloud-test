from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.synthesizer import generate_data

parser = argparse.ArgumentParser(description="Generate 100K+ synthetic HR/OLTP data.")
parser.add_argument("--rows", type=int, default=100_000, help="Number of employee rows; minimum 100000")
parser.add_argument("--ibm-path", default=str(ROOT / "data" / "WA_Fn-UseC_-HR-Employee-Attrition.csv"))
args = parser.parse_args()

result = generate_data(str(ROOT / "data" / "generated"), args.rows, args.ibm_path)
print("\nGeneration complete:")
for key, value in result.items():
    print(f"  {key}: {value:,}")
