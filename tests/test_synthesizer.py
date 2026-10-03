from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.synthesizer import generate_data


def test_generates_minimum_scale(tmp_path):
    result = generate_data(str(tmp_path), rows=100_000, ibm_path=str(tmp_path / "missing.csv"))
    assert result["employees"] == 100_000
    assert result["reviews"] == 100_000
    assert result["historical_employee_versions"] == 10_000
    assert result["total_generated_rows"] > 200_000
