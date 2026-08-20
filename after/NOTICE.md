# after/ — PENDING: real host scan required

This directory must contain the post-hardening scan evidence, collected
by re-running the exact same tools/profile/paths as before/ against the
same assigned VM, after `ansible-playbook hardening-role` has been applied:

- `lynis-after.txt` — same command as before/, same host, after hardening.
- `openscap-after-results.xml` and `openscap-after-report.html` — same
  profile ID and data-stream path as before/ (the brief requires
  "re-scan with the same profile and compare like for like" — using a
  different profile between before/after would make the delta meaningless).
- `service-check-after.json` — the same service acceptance check as the
  before-hardening baseline, run again, to prove services are still green.

**Nothing in this repo fabricates this content.** Once both before/ and
after/ contain real scan output, compute the actual measurable delta
(Lynis hardening-index change, OpenSCAP pass/fail count change per rule ID)
and report it in internal-audit-report / investment-memo.pdf, including
the one expected false-positive finding documented in
rollback/CONFLICTS.md.
