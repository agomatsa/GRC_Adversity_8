# service-results.xml — TEMPLATE, PENDING REAL HOST RUN

This is the exact JUnit-style schema that running the acceptance suite
for real will produce, once you have SSH access to the assigned VM with
hardening-role already applied:

```
py.test molecule-or-testinfra/test_hardening.py \
    --hosts=ssh://<host> \
    --junitxml=service-results.xml
```

The structure in `service-results.xml` documents the expected shape; the
actual `<testsuite>` attributes and per-test outcomes there are
illustrative placeholders, not fabricated real results — every "skipped"
reason matches a real `pytest.skip()` call in `test_hardening.py` that
names exactly what real-host information is needed to un-skip it.

Regenerate `service-results.xml` for real with the command above once you
have real host access.

(This explanation was moved here, out of an XML comment inside
`service-results.xml` itself, because XML comments cannot contain a
literal double-hyphen `--` anywhere in their content — and the real
pytest command line above legitimately contains `--junitxml` and
`--hosts`, both invalid inside an XML comment. Putting the explanation in
this separate file avoids relying on any comment content ever staying
free of `--`, rather than trying to escape or reword around the
restriction inside the XML file.)
