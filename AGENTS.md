# AGENTS.md — agent routing index

Agents: explore the repo directly; this file is a routing index, not a contributor guide.

## Workflow

``Session memory:`` Write plans, notes, and ephemeral files to `.tmp/`
(gitignored) rather than the system temporary directory.

``For non-trivial planning``, inspect deps and tooling:
`pyproject.toml` · `tox.ini` · `.pre-commit-config.yaml` ·
`requirements.txt` · `test-requirements.txt`

``Tests``: Use `tox` or `stestr`; never use `pytest`.
  Invoke them directly, for example `tox -e pep8`.
  Assume project tools are installed and available on `$PATH`.

``Routing:``
- Repo layout: [repo-overview.rst](doc/source/contributor/repo-overview.rst)
- Style, hacking, checks: [HACKING.rst](HACKING.rst)
- Driver development: [driver-development-guide.rst](doc/source/contributor/driver-development-guide.rst)
- API microversions: [microversions.rst](doc/source/contributor/microversions.rst)
- DevStack setup: [devstack_setup.rst](doc/source/contributor/devstack_setup.rst)
- Testing: [tempest-testing.rst](doc/source/contributor/tempest-testing.rst) / [api-sample-testing.rst](doc/source/contributor/api-sample-testing.rst)
- Release notes: [releasenotes.rst](doc/source/contributor/releasenotes.rst)
- Documentation: [contributing.rst](doc/source/contributor/contributing.rst)
- Commit messages: [commit-messages.rst](doc/source/contributor/commit-messages.rst)
- Agentic coding conventions: [agentic-coding.rst](doc/source/contributor/agentic-coding.rst)

## Guardrails

- ``Tools:`` Do not install missing tools with a package manager or `pip`
- ``Review``: Cyborg uses Gerrit, not GitHub PRs. Series are always unsquashed;
  each commit must be independently testable and correct.
- ``Git``: Read-only operations (`git log`, `git diff`, `git status`) are fine.
  Do not run mutating operations (`add`, `commit`, `reset`, `checkout`, `push`,
  `stash`, `merge`, `rebase`, etc.) unless explicitly instructed to do so.
