# Continuity Record — GRC Advanced 4

## Previous-stage component reused

Stage 6 (GRC Advanced 2, PeopleFlow) and Stage 7 (GRC Advanced 3, Northstar
Health) established a typed decision model (status/rule_id/verdict with
locators back to raw evidence). This stage extends that lineage a third
time: `treatment_selection.py`'s output (`selected_treatment_ids`,
`total_cost`, `mean_reduction`, `validation`) is the same typed-decision
shape, now describing a portfolio-selection outcome rather than a single
control verdict, and `simulate.py`'s per-row output
(`inherent_mean/p50/p90`, `residual_mean/p50/p90`) extends the same
evidentiary-locator discipline into quantified probabilistic terms.

## Interface consumed

`schemas/vulnerability-findings.csv` (12 findings, VF-001 through VF-012)
and the Stage 6/7 evidence-graph and control-verdict conventions. The risk
row schema (`schemas/risk-rows.json`) is new to this stage — no prior stage
required triangular/uniform distribution parameters — but retains the
`source_finding_ids` locator field so every risk row traces back to the
exact scan finding(s) that produced it, consistent with every prior
stage's evidence-locator requirement.

## Provenance preserved

Every risk row in `risk-register.csv` carries `source_finding_ids`
pointing back to the exact VF-### finding in
`schemas/vulnerability-findings.csv`. Every treatment candidate in
`schemas/treatment-candidates.json` carries `risk_id`, which traces back to
its risk row, which traces back to its finding. No transformation in this
pipeline drops that chain.

## Migration record

N/A — no incompatible schema changes were made to the supplied
vulnerability findings. The decision-output vocabulary was extended from
prior stages' pass/fail/malformed/insufficient (Stage 6) and
conforms/minor_nc/major_nc/not_tested (Stage 7) to a portfolio-selection
result (`valid`/`infeasible`) because this stage's central decision is
"which three treatments" rather than "does this one thing pass," which
needs a different output shape by nature, not by incompatible drift.

## Handoff to next stage

- Typed treatment-selection result: `schemas/treatment-selection-result.json`.
- Full risk register with residual scores and decisions:
  `risk-register.csv`.
- Deferred (accepted, unfunded) risks with a stated review trigger for
  re-evaluation: see the `decision` column in `risk-register.csv` for every
  row not in the funded set.
- Host-hardening automation (reusable for future hosts once the real VM
  scan/profile-ID gap is closed): `hardening-role/`, `rollback/`,
  `molecule-or-testinfra/`.
- **Known gap to close before next stage:** real Lynis/OpenSCAP
  before/after evidence and a real idempotence run are not yet present
  (see README.md known limitations) — the next stage should not assume
  this host has actually been hardened yet, only that the automation to
  do so is built and unit-verifiable.
