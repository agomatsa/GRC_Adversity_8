"""
GRC Advanced 4 — Service/config-state acceptance suite (testinfra).

Run against the real assigned host after applying hardening-role:
    py.test --hosts=ssh://<host> molecule-or-testinfra/test_hardening.py \
        --junitxml=service-results.xml

This produces the machine-readable service-results.xml required at the
submission root. Every test below checks END STATE (a file's content, a
service's running/enabled status, a live connection), not "did the task
report changed" — state-based checks are what actually prove a control is
in effect, independent of how it got there.
"""
import re


def test_ssh_root_login_disabled(host):
    sshd_config = host.file("/etc/ssh/sshd_config")
    assert sshd_config.exists
    assert re.search(r"^PermitRootLogin\s+no", sshd_config.content_string, re.MULTILINE)


def test_ssh_ciphers_restricted(host):
    sshd_config = host.file("/etc/ssh/sshd_config")
    content = sshd_config.content_string
    assert "Ciphers" in content
    assert "aes128-cbc" not in re.search(r"^Ciphers\s+(.*)$", content, re.MULTILINE).group(1)


def test_legacy_agent_connectivity(host):
    """
    This is the test documented in rollback/CONFLICTS.md as the one that
    catches the SSH-hardening-vs-legacy-agent conflict. It is EXPECTED TO
    FAIL against a host using the unparameterized cipher/MAC defaults if a
    legacy agent requiring an older algorithm is present, and EXPECTED TO
    PASS once host_vars overrides the cipher/MAC list for that host.

    Marked skip here because it requires knowledge of which real service
    account/agent this applies to on the actual assigned host -- fill in
    the connection check once that's known, per README known limitations.
    """
    import pytest
    pytest.skip("Requires the real assigned host's legacy-agent identity — see rollback/CONFLICTS.md")


def test_filesystem_modules_blacklisted(host):
    blacklist = host.file("/etc/modprobe.d/hardening-role-blacklist.conf")
    assert blacklist.exists
    content = blacklist.content_string
    for module in ["cramfs", "freevxfs", "jffs2", "hfs", "hfsplus", "udf"]:
        assert f"install {module} /bin/false" in content


def test_password_hashing_sha512(host):
    login_defs = host.file("/etc/login.defs")
    assert re.search(r"^ENCRYPT_METHOD\s+SHA512", login_defs.content_string, re.MULTILINE)


def test_auditd_running_and_enabled(host):
    auditd = host.service("auditd")
    assert auditd.is_running
    assert auditd.is_enabled


def test_auditd_baseline_rules_present(host):
    rules = host.file("/etc/audit/rules.d/hardening-role-baseline.rules")
    assert rules.exists
    content = rules.content_string
    assert "/etc/passwd" in content
    assert "/etc/shadow" in content


def test_unattended_upgrades_enabled(host):
    if host.system_info.distribution == "debian":
        conf = host.file("/etc/apt/apt.conf.d/20auto-upgrades-hardening-role.conf")
        assert conf.exists
        assert 'Unattended-Upgrade "1"' in conf.content_string
    else:
        timer = host.service("dnf-automatic.timer")
        assert timer.is_enabled


def test_sensitive_file_permissions(host):
    checks = [
        ("/etc/passwd", "644"),
        ("/etc/shadow", "640"),
        ("/etc/group", "644"),
        ("/etc/gshadow", "640"),
        ("/etc/ssh/sshd_config", "600"),
    ]
    for path, expected_mode in checks:
        f = host.file(path)
        assert f.exists, f"{path} missing"
        assert oct(f.mode)[-3:] == expected_mode, f"{path} has mode {oct(f.mode)}, expected {expected_mode}"


def test_unnecessary_services_disabled(host):
    for svc_name in ["avahi-daemon", "cups", "rpcbind"]:
        svc = host.service(svc_name)
        if svc.exists:
            assert not svc.is_running
            assert not svc.is_enabled


def test_sysctl_hardening_applied(host):
    expected = {
        "net.ipv4.conf.all.accept_redirects": "0",
        "net.ipv4.conf.all.send_redirects": "0",
        "net.ipv4.conf.all.accept_source_route": "0",
        "kernel.randomize_va_space": "2",
        "fs.suid_dumpable": "0",
    }
    for key, value in expected.items():
        result = host.sysctl(key)
        assert str(result) == value, f"{key} = {result}, expected {value}"


def test_essential_service_still_reachable_after_hardening(host):
    """
    Service-safety check: the primary service this host exists to run must
    still be reachable after hardening. Fill in the real service/port for
    the assigned host — left as a template since the assigned host's
    primary role is not yet known here.
    """
    import pytest
    pytest.skip("Fill in with the assigned host's actual primary service/port before running for real")
