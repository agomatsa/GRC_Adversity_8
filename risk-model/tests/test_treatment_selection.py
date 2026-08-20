"""
Runs every published fixture in tests/public-risk-fixtures.json through
risk-engine/treatment_selection.py and asserts an exact match.

Run: python3 tests/test_treatment_selection.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent ))
from treatment_selection import select_treatments  # noqa: E402

FIXTURES_PATH = Path(__file__).parent / "public-risk-fixtures.json"


def load_fixtures():
    with open(FIXTURES_PATH) as f:
        return json.load(f)["fixtures"]


def make_test(fx):
    def test(self):
        result = select_treatments(fx["treatments"], fx["budget"], fx["required_treatment_count"])
        exp = fx["expected"]
        assert result["selected_treatment_ids"] == exp["selected_treatment_ids"], \
            f"{fx['case_id']}: expected {exp['selected_treatment_ids']}, got {result['selected_treatment_ids']}"
        assert result["total_cost"] == exp["total_cost"], f"{fx['case_id']}: cost mismatch"
        assert abs(result["mean_reduction"] - exp["mean_reduction"]) < 0.01, f"{fx['case_id']}: reduction mismatch"
        assert result["validation"] == exp["validation"]
    return test


class TestPublicRiskFixtures:
    pass


for _fx in load_fixtures():
    setattr(TestPublicRiskFixtures, f"test_{_fx['case_id'].lower().replace('-', '_')}", make_test(_fx))


# --- additional unit tests: validation, dependency handling, tie-breaking ---

def test_dependency_not_satisfied_excludes_combo():
    treatments = [
        {"id": "T-X", "cost": 1000, "mean_reduction": 100, "dependencies": ["T-Z"]},
        {"id": "T-Y", "cost": 1000, "mean_reduction": 90, "dependencies": []},
        {"id": "T-W", "cost": 1000, "mean_reduction": 80, "dependencies": []},
        {"id": "T-V", "cost": 1000, "mean_reduction": 70, "dependencies": []},
    ]
    # T-Z is never in the list, so T-X can never be selected (dependency unsatisfiable).
    result = select_treatments(treatments, budget=3000, required_treatment_count=3)
    assert "T-X" not in result["selected_treatment_ids"], "T-X's dependency T-Z is never available; must be excluded"
    assert result["validation"] == "valid"
    print("PASS  dependency exclusion")


def test_dependency_satisfied_when_both_selected():
    treatments = [
        {"id": "T-X", "cost": 1000, "mean_reduction": 500, "dependencies": ["T-Y"]},
        {"id": "T-Y", "cost": 1000, "mean_reduction": 10, "dependencies": []},
        {"id": "T-W", "cost": 1000, "mean_reduction": 20, "dependencies": []},
        {"id": "T-V", "cost": 1000, "mean_reduction": 5, "dependencies": []},
    ]
    result = select_treatments(treatments, budget=3000, required_treatment_count=3)
    assert set(result["selected_treatment_ids"]) == {"T-X", "T-Y", "T-W"}, result["selected_treatment_ids"]
    print("PASS  dependency satisfaction picks the high-value pair plus best remaining")


def test_tie_break_lexicographic():
    treatments = [
        {"id": "T-A", "cost": 1000, "mean_reduction": 100, "dependencies": []},
        {"id": "T-B", "cost": 1000, "mean_reduction": 100, "dependencies": []},
        {"id": "T-C", "cost": 1000, "mean_reduction": 100, "dependencies": []},
        {"id": "T-D", "cost": 1000, "mean_reduction": 100, "dependencies": []},
    ]
    # Every combination of 3 sums to exactly 300 -> tie-break must pick the
    # lexicographically smallest ordered id list: A, B, C.
    result = select_treatments(treatments, budget=5000, required_treatment_count=3)
    assert result["selected_treatment_ids"] == ["T-A", "T-B", "T-C"], result["selected_treatment_ids"]
    print("PASS  lexicographic tie-break")


def test_infeasible_budget():
    treatments = [{"id": "T-A", "cost": 100000, "mean_reduction": 1, "dependencies": []}]
    result = select_treatments(treatments, budget=10, required_treatment_count=1)
    assert result["validation"] == "infeasible"
    print("PASS  infeasible budget correctly flagged")


if __name__ == "__main__":
    fixtures = load_fixtures()
    passed, failed = 0, 0
    for fx in fixtures:
        result = select_treatments(fx["treatments"], fx["budget"], fx["required_treatment_count"])
        exp = fx["expected"]
        ok = (result["selected_treatment_ids"] == exp["selected_treatment_ids"]
              and result["total_cost"] == exp["total_cost"]
              and abs(result["mean_reduction"] - exp["mean_reduction"]) < 0.01
              and result["validation"] == exp["validation"])
        print(f"{'PASS' if ok else 'FAIL'}  {fx['case_id']:12s} expected={exp['selected_treatment_ids']} got={result['selected_treatment_ids']}")
        passed += ok
        failed += not ok
    print(f"\n{passed} passed, {failed} failed out of {len(fixtures)}")

    print("\n--- additional unit tests ---")
    test_dependency_not_satisfied_excludes_combo()
    test_dependency_satisfied_when_both_selected()
    test_tie_break_lexicographic()
    test_infeasible_budget()
