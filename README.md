# backee
![Build](https://github.com/pruh/backee/actions/workflows/build.yml/badge.svg)
[![CodeCov](https://codecov.io/gh/pruh/backee/branch/master/graph/badge.svg)](https://codecov.io/gh/pruh/backee)
![Black](https://img.shields.io/badge/code%20style-black-000000.svg)

backee backs up files and directories to SSH servers using rsync, with
incremental snapshots and configurable retention.

## Requirements

- Linux: the single-instance lock uses Linux abstract Unix sockets.
- Python 3: CI tests the latest stable release automatically. Older releases
  are not currently covered by CI.
- `rsync` and the OpenSSH client on the machine running backee.
- An SSH server with `rsync`, `sudo`, and standard Unix utilities on the backup
  destination. Remote commands use `sudo` to create, move, and remove backup
  directories and run rsync, so the configured account needs noninteractive
  sudo access for those operations.
- SSH key authentication, using a configured private key or your SSH agent.
  Paramiko 5 requires modern SSH algorithms; DSA keys and SHA-1-only SSH
  servers are no longer supported. RSA keys with SHA-2 signatures and Ed25519
  keys are supported.

## Installation

From a checkout of this repository:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Debian/Ubuntu, install the system tools with
`sudo apt install python3-venv rsync openssh-client`.

## Configuration and usage

Copy [backee/config_template.yml](backee/config_template.yml) to
`backee/config.yml`, then edit the server, paths, logging, and retention settings
for your environment. `${ENV_VARIABLE}` placeholders are expanded at runtime.

Run from the repository root:

```sh
python backee.py --config backee/config.yml
```

`backee/config.yml` is also the default when `--config` is omitted. Use
`python backee.py --help` for command-line options.

The configuration template includes database and Docker-volume sections, but
the current backup execution only handles file/directory items. Export databases
to files first, or configure volume directories as file items when appropriate.

## Development

Install the development tools into the same virtual environment:

```sh
python -m pip install -r requirements-dev.txt
```

Run the unit tests and generate the coverage report used by CI:

```sh
python -m coverage run --source backee -m unittest discover
python -m coverage report
python -m coverage xml
```

Check formatting and linting:

```sh
python -m black --check .
python -m ruff check .
```

Use `python -m black .` to apply formatting. CI runs these checks and the tests
on the latest stable Python 3, and uploads `coverage.xml` to Codecov using GitHub
OIDC authentication. Dependabot checks Python dependencies and GitHub Actions
weekly and groups updates by ecosystem.
