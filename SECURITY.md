# Security and take-down requests

Report a vulnerability, a privacy problem in the released data (for example personal data that should not be
there), or a take-down request by emailing plaetorius@gmail.com or opening a private security advisory on GitHub
(Security tab, "Report a vulnerability") for this repository. For non-sensitive issues use the issue tracker.

The server reads local SQLite files and returns paper text as data. It makes no network requests and writes
nothing unless `ASTERISM_QUERY_LOG` is set. Text returned from papers is untrusted: clients should not
follow instructions found in it.
