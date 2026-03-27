# Code Development Guidelines

Welcome to the development support document for the **iAlarm Controller** Home Assistant integration.
The purpose of this document is to outline the best practices to follow in order to contribute to the project in a structured, secure, and efficient manner while maintaining a high quality of the source code.

---

## 1. Prerequisites

Before starting, make sure you have the following tools installed on your system:

- **Python 3.14.2** — the project strictly requires this version. Use [`pyenv`](https://github.com/pyenv/pyenv) to manage it:
  ```bash
  pyenv install 3.14.2
  pyenv local 3.14.2
  ```
- **Git** — for version control and branch management.
- **Make** — to run the automated workflow commands.

---

## 2. Development Environment Setup

Before writing any lines of code, make sure you have configured your isolated development environment.

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/bigmoby/ialarm_controller.git
   cd ialarm_controller
   ```

2. **Work on a dedicated branch** (never commit directly to `main`):
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Install all dependencies** — the project automates this via the `Makefile`:
   ```bash
   make install
   ```
   This will execute `./scripts/setup`, which:
   - Creates a Python virtual environment in `venv/` using `python3.14`
   - Installs `uv` as a fast pip replacement if not already present
   - Installs all dependencies from `requirements.txt` and `requirements.test.txt`
   - Installs the `pre-commit` hooks automatically

> **Note:** The `venv/` is activated automatically by all `make` commands (`test`, `lint`, `build`, `dev`). You do not need to activate it manually.

---

## 3. Available Make Commands

Run `make help` to see all available commands:

| Command            | Description                                                 |
|--------------------|-------------------------------------------------------------|
| `make install`     | Create venv and install all dependencies                    |
| `make test`        | Run the full test suite with coverage                       |
| `make lint`        | Run all linting checks (ruff, pylint, mypy)                 |
| `make format`      | Auto-format code with `ruff`                                |
| `make dev`         | Start a local Home Assistant instance for manual testing    |
| `make build`       | Build the distributable package                             |
| `make pre-commit`  | Run all pre-commit hooks on the full codebase               |
| `make update-deps` | Upgrade dependencies and pre-commit hooks                   |
| `make clean`       | Remove build artifacts, htmlcov, and the venv               |

---

## 4. Local Testing with Unit Tests

The project uses `pytest` with a strict **96% code coverage threshold** configured in `pyproject.toml`.

### Run the test suite

```bash
make test
```

This executes `./scripts/test`, which runs `pytest` against the `tests/` directory and generates:
- A terminal coverage summary
- An HTML report at `htmlcov/index.html`
- An XML report at `coverage.xml`

### Test structure

| File                                  | What it tests                                           |
|---------------------------------------|---------------------------------------------------------|
| `tests/test_config_flow.py`           | Configuration UI flow (success, connection errors)      |
| `tests/test_init.py`                  | Component setup, teardown, and `ConfigEntryNotReady`    |
| `tests/test_coordinator.py`           | Data polling, event bus firing, cancel alarm, get log   |
| `tests/test_alarm_control_panel.py`   | Arm away, arm home, disarm (with and without code)      |
| `tests/test_sensor.py`                | Zone status parsing and sensor state transitions        |
| `tests/test_button.py`                | Button press actions (cancel alarm, fetch log)          |

### Writing new tests

- All tests are **async** and use the `pytest-homeassistant-custom-component` framework.
- The `ialarm_api` fixture in `tests/conftest.py` automatically mocks the `IAlarm` class so no physical hardware is required.
- Override individual mock methods in each test as needed:
  ```python
  ialarm_api.return_value.get_mac = AsyncMock(return_value="00:11:22:33:44:55")
  ialarm_api.return_value.get_zone_status = AsyncMock(return_value=[...])
  ```

> **Rule:** Never open a PR if `make test` fails or if coverage drops below 96%.

---

## 5. Manual Testing with a Local Home Assistant Instance

To test the integration end-to-end against a real (or simulated) iAlarm device:

```bash
make dev
```

This executes `./scripts/develop`, which:
1. Activates the `venv` automatically.
2. Creates a `config/` directory in the project root (if it does not exist) and initializes it with `hass --script ensure_config`.
3. Sets `PYTHONPATH` so that Home Assistant finds `custom_components/ialarm_controller` directly, **without symlinks**.
4. Clears any stale `__pycache__` directories.
5. Starts Home Assistant in `--debug` mode pointing to the local `config/` directory.

Then open your browser at **http://localhost:8123** and configure the iAlarm integration through the Home Assistant UI.

> **Note:** The `config/` directory is local only and should be listed in `.gitignore`. It contains your local HA configuration and credentials — never commit it.

---

## 6. Linting and Formatting

Before committing, ensure your code adheres to the project style:

```bash
make format   # auto-fix formatting with ruff
make lint     # run static analysis (ruff, pylint, mypy, bandit)
```

Resolve all warnings before proceeding. The CI pipeline will fail on any linting error.

---

## 7. pre-commit Hooks

Every `git commit` automatically runs the pre-commit hooks, which verify:
- Syntax validity (JSON, TOML, YAML)
- Trailing whitespace / end-of-file consistency
- Code style (ruff)

If a hook fails but auto-fixes the file, simply re-stage and re-commit:

```bash
git add <fixed-file>
git commit -m "your message"
```

You can also run hooks manually on the whole codebase at any time:

```bash
make pre-commit
```

---

## 8. Reviewing and Testing a Pull Request Locally

Before merging any external PR, always test it locally first.

> **Important:** Before checking out a PR branch, commit or stash your current work to avoid losing uncommitted changes.

```bash
# 1. Save your current work first!
git add . && git commit -m "WIP: save before testing PR"

# 2. Fetch the PR branch by number (works for any fork automatically)
git fetch origin pull/<PR_NUMBER>/head:pr-<PR_NUMBER>
git checkout pr-<PR_NUMBER>

# 3. Reinstall in case dependencies changed
make install

# 4. Run the full validation pipeline
make test
make lint

# 5. Start HA locally to test manually
make dev
```

To go back to your branch:

```bash
git checkout feature/your-branch-name

# Optionally delete the PR branch
git branch -D pr-<PR_NUMBER>
```

---

## 9. Recommended Contribution Workflow (PR Lifecycle)

Follow this flow for every feature or bugfix:

1. **Keep `main` up to date:**
   ```bash
   git pull origin main
   ```
2. **Create an isolated branch** with a descriptive name:
   ```bash
   git checkout -b feature/add-climate
   # or
   git checkout -b fix/connection-error
   ```
3. **Write code and tests** — always add or update files inside `tests/`.
4. **Run the full pipeline locally:**
   ```bash
   make format
   make lint
   make test
   ```
5. **Stage only relevant files and commit:**
   ```bash
   git add modified_file.py tests/test_modified_file.py
   git commit -m "feat: short description of what this commit introduces"
   ```
   *Let the pre-commit hooks run and fix any issues automatically.*
6. **Push and open a Pull Request** on GitHub. In the PR body, specify:
   - Which issue it resolves (e.g., `Closes #42`)
   - That it has been tested locally: *"Successfully tested locally with `make test` and `make dev`"*

---

## 10. Dependency Management

| File                    | Purpose                                                             |
|-------------------------|---------------------------------------------------------------------|
| `requirements.txt`      | Runtime dependencies (HA core, pyasyncialarm, ruff, pre-commit)    |
| `requirements.test.txt` | Test-only dependencies (pytest-homeassistant-custom-component, syrupy) |

To upgrade all dependencies and pre-commit hooks:

```bash
make update-deps
```

To do a clean reinstall from scratch:

```bash
make clean
make install
```
