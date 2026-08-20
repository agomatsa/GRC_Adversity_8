"""
GRC Advanced 4 — Builds treatment candidates from the vulnerability
findings' proposed remediations, for input to treatment_selection.py.

Cost methodology (documented, not arbitrary):
  decommission (retire/destroy): $2,000 flat -- deprovisioning labor only,
    no new engineering.
  config/access change (restrict/revoke/rotate/require signing): $6,000 --
    a scoped configuration change plus verification testing.
  patch/upgrade (upgrade firmware/renew certificate/automate alert):
    $9,000 -- includes a maintenance window and regression check.
  engineering change (enforce/deploy/reduce/restrict to management VLAN
    and MFA): $15,000 -- code or architecture change plus testing.

Post-treatment control effectiveness:
  decommission remediations drive control effectiveness to 0.90-0.98
    (residual risk approaches zero because the asset/exposure is gone).
  all other remediations are assumed to raise control effectiveness into
    the "strong" band (0.70-0.90) -- a documented, deliberately
    conservative assumption (not 1.0) because no remediation is modeled
    as perfect.

mean_reduction per treatment = current residual_mean (from the existing
simulation-results.json) minus the residual_mean recomputed with the
treatment's improved control band, using a fresh but deterministic
Generator seeded from the same evidence marker plus the treatment ID (so
re-running produces identical results, and the post-treatment draw does
not silently reuse the pre-treatment stream).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from simulate import derive_seed, simulate_risk_row
import numpy as np

DECOMMISSION_MARKERS = ["retire", "destroy"]

COST_RULES = [
    (["retire", "destroy"], 2000.0, "decommission"),
    (["restrict", "revoke", "rotate", "require signing"], 6000.0, "config/access change"),
    (["upgrade", "renew", "automate"], 9000.0, "patch/upgrade"),
    (["enforce", "deploy", "reduce"], 15000.0, "engineering change"),
]


def classify_remediation(text):
    text = text.lower()
    for markers, cost, label in COST_RULES:
        if any(m in text for m in markers):
            return cost, label
    return 10000.0, "unclassified (default mid-tier cost)"


def build_treatment(risk_row, remediation_text, evidence_marker):
    is_decommission = any(m in remediation_text.lower() for m in DECOMMISSION_MARKERS)
    cost, cost_label = classify_remediation(remediation_text)

    post_control_min, post_control_max = (0.90, 0.98) if is_decommission else (0.70, 0.90)
    post_row = dict(risk_row, control_min=post_control_min, control_max=post_control_max)

    seed = derive_seed(f"{evidence_marker}:{risk_row['risk_id']}", "GRC-A4-TREATMENT")
    rng = np.random.Generator(np.random.PCG64(seed))
    post_result = simulate_risk_row(post_row, rng)

    return {
        "id": f"T-{risk_row['risk_id']}",
        "risk_id": risk_row["risk_id"],
        "remediation": remediation_text,
        "cost": cost,
        "cost_basis": cost_label,
        "dependencies": [],
        "post_treatment_control_band": [post_control_min, post_control_max],
        "post_treatment_residual_mean": post_result["residual_mean"],
    }


def main(risk_rows_path, findings_csv_path, sim_results_path, evidence_marker, out_path):
    import csv
    with open(risk_rows_path) as f:
        rows = {r["risk_id"]: r for r in json.load(f)["rows"]}
    with open(sim_results_path) as f:
        sim = {r["risk_id"]: r for r in json.load(f)["results"]}
    remediation_by_finding = {}
    with open(findings_csv_path, newline="") as f:
        for vf in csv.DictReader(f):
            remediation_by_finding[vf["finding_id"]] = vf["remediation"]

    treatments = []
    for risk_id, row in rows.items():
        finding_id = row["source_finding_ids"][0]
        remediation_text = remediation_by_finding[finding_id]
        t = build_treatment(row, remediation_text, evidence_marker)
        current_residual_mean = sim[risk_id]["residual_mean"]
        t["mean_reduction"] = round(max(0.0, current_residual_mean - t["post_treatment_residual_mean"]), 2)
        treatments.append(t)

    with open(out_path, "w") as f:
        json.dump({"schema_version": "1.0", "treatments": treatments}, f, indent=2)
    print(f"Wrote {len(treatments)} treatment candidates to {out_path}")
    for t in treatments:
        print(f"  {t['id']:10s} cost=${t['cost']:>7,.0f}  mean_reduction=${t['mean_reduction']:>10,.2f}  ({t['cost_basis']})")


if __name__ == "__main__":
    main("schemas/risk-rows.json", "schemas/vulnerability-findings.csv",
         "schemas/simulation-results.json", "UBI-A8-68E05244B5C7",
         "schemas/treatment-candidates.json")
