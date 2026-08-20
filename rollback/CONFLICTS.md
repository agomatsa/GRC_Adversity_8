# Known Conflict and False-Positive Handling

The brief requires the acceptance suite to distinguish two specific situations:
a scanner item that is a false positive, and a remediation that conflicts
with a service until correctly parameterized. Both are documented here so
they're explainable at defense, not just baked silently into task logic.

## Remediation-vs-service conflict: SSH cipher/MAC restriction (control 01)

**The conflict:** Restricting `Ciphers`/`MACs` to modern algorithms only
(`defaults/main.yml`: `hardening_ssh_ciphers`, `hardening_ssh_macs`) is a
standard CIS-aligned hardening step. On a host where a legacy backup or
monitoring agent connects over SSH using an older cipher (a real, common
situation — e.g. an appliance that only supports `aes128-cbc`), applying
this control as a blanket default **breaks that agent's connectivity**
until the SSH hardening is correctly parameterized for that host: either
(a) the legacy client is upgraded, or (b) `hardening_ssh_ciphers` /
`hardening_ssh_macs` are overridden at the inventory/host_vars level to
include the one additional algorithm the legacy client requires, with that
exception documented and dated.

**How the role handles it:**
- `validate: /usr/sbin/sshd -T -f %s` on every `lineinfile` task in
  `01_ssh_hardening.yml` means a syntactically invalid config is rejected
  by `sshd -T` before the file is ever put in place — this catches
  malformed config, not a working-but-now-incompatible cipher set.
- The actual conflict (a legacy agent losing connectivity) can only be
  caught by the **service acceptance suite** actually attempting that
  connection post-hardening — see `molecule-or-testinfra/test_hardening.py`,
  `test_legacy_agent_connectivity` — which is deliberately written to
  **fail** against the unparameterized defaults on a host with such an
  agent, and pass once the host_vars override is applied. This is the
  acceptance-suite proof the brief asks for; it requires the real assigned
  host to actually run (see README known limitations).

## Scanner false positive

**Expectation:** at least one OpenSCAP/Lynis finding on the real assigned
host is expected to be a false positive — a finding that fires against
this host's actual configuration without describing a real gap (a common
real-world example: a scanner rule checking for a *default* password hash
algorithm string match that also matches this role's already-hardened
`SHA512` setting due to a rule regex bug, or a rule assuming a package
manager path that doesn't exist on the assigned distro).

**How the acceptance suite must distinguish it:** the before/after scan
delta (see `before/` and `after/`) will show this specific finding ID
present in both scans, unchanged, **despite** the relevant control being
verifiably applied (proven by the service/config-state testinfra check for
that control passing). The report must name the specific finding ID once
it's known from the real scan, explain why it's a false positive with
reference to the actual config state (not just assert it), and record that
decision in `evidence-index.csv` with a `disposition` of
`false_positive_documented` rather than silently excluding it from the
delta count.

**Status: pending the real host scan.** This file documents the expected
*shape* of both situations and how the tooling is built to surface them;
the actual finding IDs and confirmation must come from running
`before/` and `after/` scans and the acceptance suite against the real
assigned VM (see README.md known limitations).
