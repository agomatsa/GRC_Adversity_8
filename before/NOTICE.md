# before/ — PENDING: real host scan required

This directory must contain the pre-hardening baseline scan evidence from
the actual assigned Debian 12 / Rocky Linux 9 VM:

- `lynis-before.txt` (or `.dat`) — full `lynis audit system` output,
  including the hardening index score.
- `openscap-before-results.xml` and `openscap-before-report.html` — from
  `oscap xccdf eval --profile <assigned profile ID> --results ... --report ...`
  against the correct SCAP data-stream path for the assigned distro (see
  README known limitations — the exact profile ID/path was pending at
  drafting time).
- `service-baseline.json` — output of whatever service acceptance check
  confirms the host's primary service is reachable BEFORE hardening, so
  the after/ scan can prove nothing broke.

**Nothing in this repo fabricates this content.** Run the real scans on
your assigned VM and drop the output here, then re-run
`python3 risk-model/build_delta_report.py` (once you've filled it in) to
generate the measurable-delta section of the internal report.
