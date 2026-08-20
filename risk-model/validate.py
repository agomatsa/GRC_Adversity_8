"""
GRC Advanced 4 — Risk row validation.

Rejects, per the Quantitative Risk Model Contract:
  - inverted ranges (min > mode, mode > max, or min > max) for frequency
    and loss magnitude triangular parameters
  - control effectiveness values outside 0 <= control <= 1
  - nonpositive dependency multipliers
  - duplicate risk IDs within a register
  - missing asset IDs
"""


class ValidationError(Exception):
    def __init__(self, risk_id, reason):
        self.risk_id = risk_id
        self.reason = reason
        super().__init__(f"{risk_id}: {reason}")


def _check_triangular(risk_id, label, lo, mode, hi):
    if not (lo <= mode <= hi):
        raise ValidationError(risk_id, f"{label} range inverted: expected {label}_min <= {label}_mode <= {label}_max, got {lo}, {mode}, {hi}")


def validate_row(row):
    risk_id = row.get("risk_id")
    if not risk_id:
        raise ValidationError(risk_id or "<missing>", "missing risk_id")
    if not row.get("asset_id"):
        raise ValidationError(risk_id, "missing asset_id")

    _check_triangular(risk_id, "freq", row["freq_min"], row["freq_mode"], row["freq_max"])
    _check_triangular(risk_id, "loss", row["loss_min"], row["loss_mode"], row["loss_max"])

    if row["control_min"] > row["control_max"]:
        raise ValidationError(risk_id, f"control range inverted: control_min {row['control_min']} > control_max {row['control_max']}")
    if not (0 <= row["control_min"] <= 1) or not (0 <= row["control_max"] <= 1):
        raise ValidationError(risk_id, f"control effectiveness out of [0,1]: [{row['control_min']}, {row['control_max']}]")

    if row["dependency_multiplier"] <= 0:
        raise ValidationError(risk_id, f"nonpositive dependency_multiplier: {row['dependency_multiplier']}")

    return True


def validate_register(rows):
    """Validates every row and rejects duplicate risk_ids across the set.
    Returns (valid_rows, errors) — never raises for the whole batch, so a
    single bad row doesn't silently exclude every other row's results."""
    seen_ids = set()
    valid_rows, errors = [], []
    for row in rows:
        rid = row.get("risk_id")
        if rid in seen_ids:
            errors.append({"risk_id": rid, "reason": f"duplicate risk_id: {rid} already seen in this register"})
            continue
        try:
            validate_row(row)
            seen_ids.add(rid)
            valid_rows.append(row)
        except ValidationError as e:
            errors.append({"risk_id": e.risk_id, "reason": e.reason})
    return valid_rows, errors
