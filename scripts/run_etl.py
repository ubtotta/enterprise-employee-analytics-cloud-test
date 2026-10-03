from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.etl import EmployeeWarehouseETL

result = EmployeeWarehouseETL(ROOT / "data" / "generated").run(refresh=True)
print("\nWarehouse ETL completed successfully:")
for key, value in result.items():
    print(f"  {key}: {value:,}")
