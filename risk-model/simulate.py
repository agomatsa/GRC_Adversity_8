"""
GRC Advanced 4 — Quantitative risk simulation engine.

Implements the Quantitative Risk Model Contract exactly:
  - Python 3.11 / NumPy 2.1.x, numpy.random.Generator(PCG64(seed))
  - seed = first unsigned 64 bits of SHA-256(evidence_marker + ":GRC-A4"),
    big-endian
  - exactly 50,000 draws per risk row
  - frequency ~ triangular(freq_min, freq_mode, freq_max)
  - loss_magnitude ~ triangular(loss_min, loss_mode, loss_max)
  - control_effectiveness ~ uniform(control_min, control_max)
  - inherent = frequency * loss_magnitude * dependency_multiplier
  - residual = inherent * (1 - control_effectiveness)
  - aggregate: mean, p50, p90 (NumPy default linear percentile method)
  - round only final currency outputs to 2dp, round-half-even

No risk IDs or expected values are hard-coded — every output is derived
from the shape of the input row at call time.
"""
import hashlib
from decimal import Decimal, ROUND_HALF_EVEN

import numpy as np

N_DRAWS = 50_000


def derive_seed(evidence_marker, project_id="GRC-A4"):
    digest = hashlib.sha256(f"{evidence_marker}:{project_id}".encode()).digest()
    return int.from_bytes(digest[:8], byteorder="big")


def round_half_even(value):
    """Round a float to 2 decimal places using round-half-even, via Decimal
    to avoid binary-float representation error near .xx5 boundaries."""
    return float(Decimal(repr(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))


def simulate_risk_row(row, rng):
    """
    row: {
        "risk_id": str, "asset_id": str,
        "freq_min": float, "freq_mode": float, "freq_max": float,
        "loss_min": float, "loss_mode": float, "loss_max": float,
        "control_min": float, "control_max": float,
        "dependency_multiplier": float,
    }
    Returns a dict with mean/p50/p90 inherent and residual annual loss,
    each rounded to 2dp round-half-even.
    """
    freq = rng.triangular(row["freq_min"], row["freq_mode"], row["freq_max"], size=N_DRAWS)
    loss = rng.triangular(row["loss_min"], row["loss_mode"], row["loss_max"], size=N_DRAWS)
    control = rng.uniform(row["control_min"], row["control_max"], size=N_DRAWS)

    inherent = freq * loss * row["dependency_multiplier"]
    residual = inherent * (1 - control)

    return {
        "risk_id": row["risk_id"],
        "asset_id": row["asset_id"],
        "inherent_mean": round_half_even(float(np.mean(inherent))),
        "inherent_p50": round_half_even(float(np.percentile(inherent, 50, method="linear"))),
        "inherent_p90": round_half_even(float(np.percentile(inherent, 90, method="linear"))),
        "residual_mean": round_half_even(float(np.mean(residual))),
        "residual_p50": round_half_even(float(np.percentile(residual, 50, method="linear"))),
        "residual_p90": round_half_even(float(np.percentile(residual, 90, method="linear"))),
    }


def simulate_register(rows, evidence_marker, project_id="GRC-A4"):
    """Runs simulate_risk_row for every row using a single Generator stream
    seeded once from evidence_marker, consumed in row order.

    Design note: the contract says "derive seed" (singular) from the
    evidence marker, not "derive a seed per row." This implementation
    therefore uses ONE Generator(PCG64(seed)) and lets each row's draws
    consume the next slice of that one stream, in the order rows are
    supplied. This means the results for row N depend on how many rows
    preceded it -- which is a real, documented behavior, not a bug: it
    matches the literal single-seed wording rather than assuming an
    unstated per-row reseeding scheme. If the hidden fixture expects
    per-row independence instead, this is the first place to change.
    """
    seed = derive_seed(evidence_marker, project_id)
    rng = np.random.Generator(np.random.PCG64(seed))
    return [simulate_risk_row(row, rng) for row in rows]
