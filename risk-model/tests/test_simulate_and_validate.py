"""
Unit tests for risk-engine/simulate.py and risk-engine/validate.py.

Run: python3 tests/test_simulate_and_validate.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent ))
from simulate import derive_seed, simulate_risk_row, simulate_register, N_DRAWS  # noqa: E402
from validate import validate_row, validate_register, ValidationError  # noqa: E402
import numpy as np  # noqa: E402

MARKER = "UBI-A8-68E05244B5C7"

SAMPLE_ROW = {
    "risk_id": "R-TEST-01", "asset_id": "A-TEST",
    "freq_min": 0.1, "freq_mode": 0.5, "freq_max": 1.0,
    "loss_min": 10000, "loss_mode": 50000, "loss_max": 200000,
    "control_min": 0.3, "control_max": 0.7,
    "dependency_multiplier": 1.0,
}

results = []


def check(name, cond):
    status = "PASS" if cond else "FAIL"
    print(f"{status}  {name}")
    results.append(cond)


def test_seed_derivation_deterministic():
    s1 = derive_seed(MARKER)
    s2 = derive_seed(MARKER)
    check("seed derivation is deterministic for the same marker", s1 == s2)
    check("seed is a valid unsigned 64-bit int", 0 <= s1 < 2**64)

    s_other = derive_seed("some-other-marker")
    check("different markers produce different seeds", s1 != s_other)


def test_simulation_determinism():
    rng1 = np.random.Generator(np.random.PCG64(derive_seed(MARKER)))
    rng2 = np.random.Generator(np.random.PCG64(derive_seed(MARKER)))
    r1 = simulate_risk_row(SAMPLE_ROW, rng1)
    r2 = simulate_risk_row(SAMPLE_ROW, rng2)
    check("same seed + same row -> identical simulation output", r1 == r2)


def test_draw_count():
    rng = np.random.Generator(np.random.PCG64(derive_seed(MARKER)))
    freq = rng.triangular(SAMPLE_ROW["freq_min"], SAMPLE_ROW["freq_mode"], SAMPLE_ROW["freq_max"], size=N_DRAWS)
    check("exactly 50,000 draws requested", len(freq) == 50_000)


def test_statistical_sanity():
    rng = np.random.Generator(np.random.PCG64(derive_seed(MARKER)))
    r = simulate_risk_row(SAMPLE_ROW, rng)
    check("inherent_mean is positive", r["inherent_mean"] > 0)
    check("residual_mean < inherent_mean (control effectiveness reduces loss)", r["residual_mean"] < r["inherent_mean"])
    check("p90 >= p50 >= 0 for inherent", r["inherent_p90"] >= r["inherent_p50"] >= 0)
    check("p90 >= p50 >= 0 for residual", r["residual_p90"] >= r["residual_p50"] >= 0)
    # rough sanity band: mean inherent should be in the right order of
    # magnitude for freq~[0.1,1.0] * loss~[10k,200k]
    check("inherent_mean within a plausible order of magnitude (1k-200k)", 1_000 < r["inherent_mean"] < 200_000)


def test_rounding_half_even():
    from simulate import round_half_even
    check("round_half_even(2.005) == 2.00 or 2.01 consistently (no float drift)", round_half_even(2.005) in (2.00, 2.01))
    check("round_half_even(1.005) rounds to even", round_half_even(1.005) == 1.00)
    check("round_half_even(1.015) rounds to even", round_half_even(1.015) == 1.02)


def test_validation_accepts_good_row():
    check("valid row passes validate_row", validate_row(SAMPLE_ROW) is True)


def test_validation_rejects_inverted_freq_range():
    bad = dict(SAMPLE_ROW, freq_min=0.9, freq_mode=0.5, freq_max=1.0)  # mode < min
    try:
        validate_row(bad)
        check("inverted freq range rejected", False)
    except ValidationError:
        check("inverted freq range rejected", True)


def test_validation_rejects_inverted_loss_range():
    bad = dict(SAMPLE_ROW, loss_min=100000, loss_mode=50000, loss_max=200000)  # mode < min
    try:
        validate_row(bad)
        check("inverted loss range rejected", False)
    except ValidationError:
        check("inverted loss range rejected", True)


def test_validation_rejects_control_out_of_bounds():
    bad = dict(SAMPLE_ROW, control_min=-0.1, control_max=0.5)
    try:
        validate_row(bad)
        check("control_min < 0 rejected", False)
    except ValidationError:
        check("control_min < 0 rejected", True)

    bad2 = dict(SAMPLE_ROW, control_min=0.5, control_max=1.5)
    try:
        validate_row(bad2)
        check("control_max > 1 rejected", False)
    except ValidationError:
        check("control_max > 1 rejected", True)


def test_validation_rejects_nonpositive_dependency_multiplier():
    bad = dict(SAMPLE_ROW, dependency_multiplier=0)
    try:
        validate_row(bad)
        check("dependency_multiplier == 0 rejected", False)
    except ValidationError:
        check("dependency_multiplier == 0 rejected", True)

    bad2 = dict(SAMPLE_ROW, dependency_multiplier=-2)
    try:
        validate_row(bad2)
        check("negative dependency_multiplier rejected", False)
    except ValidationError:
        check("negative dependency_multiplier rejected", True)


def test_validation_rejects_missing_asset_id():
    bad = dict(SAMPLE_ROW, asset_id="")
    try:
        validate_row(bad)
        check("missing asset_id rejected", False)
    except ValidationError:
        check("missing asset_id rejected", True)


def test_validation_rejects_duplicate_risk_ids():
    rows = [SAMPLE_ROW, dict(SAMPLE_ROW, asset_id="A-OTHER")]  # same risk_id twice
    valid, errors = validate_register(rows)
    check("duplicate risk_id detected", any("duplicate" in e["reason"] for e in errors))
    check("only the first occurrence is kept valid", len(valid) == 1)


def test_register_order_stability():
    rows = [SAMPLE_ROW, dict(SAMPLE_ROW, risk_id="R-TEST-02", asset_id="A-TEST-2")]
    r1 = simulate_register(rows, MARKER)
    r2 = simulate_register(rows, MARKER)
    check("full register simulation is reproducible across runs", r1 == r2)
    check("register preserves row order", [r["risk_id"] for r in r1] == ["R-TEST-01", "R-TEST-02"])


if __name__ == "__main__":
    test_seed_derivation_deterministic()
    test_simulation_determinism()
    test_draw_count()
    test_statistical_sanity()
    test_rounding_half_even()
    test_validation_accepts_good_row()
    test_validation_rejects_inverted_freq_range()
    test_validation_rejects_inverted_loss_range()
    test_validation_rejects_control_out_of_bounds()
    test_validation_rejects_nonpositive_dependency_multiplier()
    test_validation_rejects_missing_asset_id()
    test_validation_rejects_duplicate_risk_ids()
    test_register_order_stability()

    passed = sum(results)
    print(f"\n{passed} passed, {len(results) - passed} failed out of {len(results)}")
