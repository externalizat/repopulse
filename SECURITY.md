# Security policy

Only the latest released version, or the default branch before the first release,
receives security fixes. There are no claims of a security audit.

For vulnerabilities in RepoPulse, use GitHub's private vulnerability reporting
feature in the repository Security tab when enabled. Otherwise contact a maintainer
through a private channel listed on their profile. Do not open a public issue with
credentials, exploit details, or private repository content. Include affected
versions, expected and actual behavior, and a sanitized minimal reproduction.

Before public launch, repository administrators should enable private vulnerability
reporting under Settings → Code security. This is a hosting setting, not a file that
can be enabled by this source distribution.

RepoPulse does not send repository files anywhere and does not execute scanned code.
Secret matches are fully redacted. A finding is a heuristic: inspect it locally and
rotate confirmed credentials at the provider; deleting a file does not revoke them.
No finding is a guarantee of safety. Scans assume a stable filesystem and do not
provide isolation against an adversary changing paths concurrently.
