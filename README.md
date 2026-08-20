# GRC Advanced 4 — Hardening as Code and Quantified Risk

Intern code: UBI-2026-0038, Project: GRC-A4, Variant: V8
Evidence marker: UBI-A8-68E05244B5C7

## Tool and OS versions (fill in with your actual environment before submitting)

- OS (control node): [insert]
- Ansible: [insert — `ansible --version`]
- Python: [insert — `python3 --version`]
- NumPy: [insert — `python3 -c "import numpy; print(numpy.__version__)"`]. **The
  contract specifies NumPy 2.1.x; this repo was drafted against 2.4.4
  because PyPI access to pin the exact version was unavailable in the
  drafting sandbox (network blocked pypi.org despite being on the
  documented allowlist — the same issue hit on a prior project). Install
  the real 2.1.x before your real run and re-verify determinism.**
- pytest-testinfra: [insert]
- Assigned VM OS: [insert — Debian 12 or Rocky Linux 9]
- OpenSCAP profile ID: [insert — was not present anywhere in the uploaded
  brief; paste it in here and into `hardening-role/vars/main.yml` once known]

## Reproduction order

1. `python3 risk-model/tests/test_treatment_selection.py` — 8 published fixtures + 4 unit tests (dependency handling, tie-break, infeasibility). Expected: `8 passed, 0 failed` plus 4 `PASS` unit tests.
2. `python3 risk-model/tests/test_simulate_and_validate.py` — 25 checks covering seed determinism, draw count, statistical sanity, rounding, and every validation rejection rule. Expected: `25 passed, 0 failed`.
3. `python3 risk-model/build_risk_rows.py schemas/vulnerability-findings.csv schemas/risk-rows.json` — builds the 12 risk rows from the supplied findings using the documented methodology (see the module docstring for the full rationale, including the $150/record assumption that was tried and rejected as disproportionate).
4. Run the simulation and treatment selection (see the inline script used to generate `schemas/simulation-results.json`, `schemas/treatment-candidates.json`, and `schemas/treatment-selection-result.json` — re-run via `python3 -c "..."` as shown in project history, or wrap into a `run_all.py` if you want a single entry point).
5. Cross-check `risk-register.csv` against `schemas/treatment-selection-result.json` — every row's `decision` column should say "treat" only for the 3 selected treatment IDs' risk rows.
6. `shasum -a 256 -c manifest.sha256` — confirm all files verify.
7. **On your real assigned VM:** run Lynis and OpenSCAP (with the real profile ID) to populate `before/`; apply `hardening-role/` via `ansible-playbook`; run `molecule-or-testinfra/test_hardening.py` to populate `service-results.xml`; run the playbook a second time and capture `idempotence.log`; re-scan to populate `after/`.

## Known limitations — read before defense

- **No real assigned VM was available in the drafting environment.** Every file under `hardening-role/`, `rollback/`, and `molecule-or-testinfra/` is real, reviewable Ansible/testinfra code, but it has not been executed against the actual assigned Debian 12/Rocky 9 host. `before/`, `after/`, `service-results.xml`, and `idempotence.log` are explicitly marked as templates pending that real run — see each file's own NOTICE. **Do not submit these as-is; they must be replaced with real scan/test output before this counts as complete.**
- **The OpenSCAP profile ID was not present anywhere in the uploaded brief.** The private-assignment text referenced it but the actual ID string was not included. Confirm it and fill it into `hardening-role/vars/main.yml` (create this file with `hardening_openscap_profile: <id>` once known) before running any real scan.
- **The 8 hardening controls were chosen by the assistant, not assigned.** The brief requires "at least eight scored remediations" without naming them. The 8 implemented here (SSH hardening, filesystem module blacklist, password policy, auditd, unattended upgrades, file permissions, disable unused services, sysctl hardening) are standard CIS/SSG-aligned controls chosen as broadly-applicable defaults — reconcile these against your actual Lynis/OpenSCAP findings once you have them, and add/replace controls to target whatever your real scan actually flags.
- **NumPy version mismatch** — see Tool Versions above.
- **The risk-magnitude and treatment-cost methodologies are documented assumptions, not measured data** — every formula's rationale is in `risk-model/build_risk_rows.py` and `risk-model/build_treatments.py`'s docstrings, including one methodology (a $150/record loss estimate) that was tried, found disproportionate to this dataset's scale, and explicitly replaced — kept visible in the docstring per the evidence standard's requirement to record what was considered and why it was weakened.
- No risk IDs, finding IDs, or fixture answers are hard-coded in `risk-model/treatment_selection.py` or `simulate.py` — every output is derived from the shape of the input at call time.
- The 12 hidden calculation fixtures and the hidden asset/budget fixture were not available during drafting.

## Declared assistance

I OFORI DZAM Drafted Ansible role design, testinfra suite design, the quantitative risk simulation engine, treatment selection optimizer, risk register construction, and document drafting. All findings, methodology choices, and the treatment decision are owned by the candidate, who is responsible for defending them during the artifact check — including running the real host-hardening evidence this package is currently missing. 