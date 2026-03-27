# Code Development Guidelines

Welcome to the development support document for the **iAlarm Controller** Home Assistant integration.
The purpose of this document is to outline the best practices to follow in order to contribute to the project in a structured, secure, and efficient manner while maintaining a high quality of the source code.

---

## 1. Development Environment Setup

Before writing any lines of code, make sure you have configured your isolated development environment.

1. **Use a Virtual Environment**
   Installing dependencies globally is highly discouraged. Always use a virtual environment (`venv`).
2. **Install Dependencies**
   The project automates this setup phase via the `Makefile`. To prepare everything you need, simply run:
   ```bash
   make install
   ```
   *(This will automatically execute the `./scripts/setup` script to install requirements, testing packages, and pre-commit hooks).*

---

## 2. Using "pre-commit" for Code Quality

One of the fundamental aspects of this repository is the use of **pre-commit hooks**.
These scripts automatically check your modified files every time you attempt to run `git commit`. They verify syntax (JSON, TOML), trim trailing whitespaces, and standardize end-of-file formats.

*   Ensure that you **never bypass** these checks.
*   If a check fails (e.g., `end-of-file-fixer`), the pre-commit hook will automatically modify the files to fix them. All you need to do is stage the fixed files again using `git add <file>` and retry `git commit`.
*   You can manually run checks on the entire codebase with:
    ```bash
    make pre-commit
    ```

---

## 3. Linting and Formatting

The code is formatted and cross-checked using a combination of tools (`ruff`, `pylint`, `mypy`).
Before committing, ensure that your new code adheres to the guidelines:

*   **To automatically format your code:**
    ```bash
    make format
    ```
*   **To run the linting tools (static analysis):**
    ```bash
    make lint
    ```
    Resolve any warnings or errors returned by the linter before proceeding.

---

## 4. Local Testing (The Most Critical Step)

Adding new features or fixing bugs carries the risk of introducing regressions in pre-existing parts of the codebase. **It is absolutely prohibited to open a Pull Request without having tested your changes first.**

In particular, the project relies on `pytest` and requires that the code coverage remains high (above 80%).

1. **Write the Tests**
   Always include corresponding tests for the logic you are modifying or adding under the `tests/` directory.
2. **Run the local test suite**
   Run the tests using the official Makefile command:
   ```bash
   make test
   ```
   *Alternatively, you can run the `./scripts/test` script.*
3. **Check Code Coverage**
   Verify the terminal output. If the command returns errors, you are not ready for a Pull Request. If the code coverage drops below the threshold set in `pyproject.toml`, expand your tests to cover the missing cases.

---

## 5. Recommended Contribution Workflow (PR Lifecycle)

When you decide to implement a new feature (Feature) or a Fix, always follow this methodical flow:

1. **Always keep your local `main` branch updated**:
   Ensure you have the latest code version by pulling the recent commits (`git pull origin main`).
2. **Create an isolated Branch**:
   Use descriptive naming conventions. Example: `feature/add-climate` or `fix/connection-error`.
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Write Code and Tests**:
   Implement the logic and do not forget to add or update files inside the `tests/` directory!
4. **Verify Your Work**:
   Re-run the entire pipeline locally to ensure it will pass CI checks:
   ```bash
   make format
   make lint
   make test
   ```
5. **Stage and Commit**:
   Stage *only* the files that are strictly necessary for the feature (avoid including junk files, generated reports like `bandit-report.json`, or `.DS_Store`).
   ```bash
   git add modified_file.py
   git commit -m "feat: clear explanation of what this commit introduces"
   ```
   *Let the pre-commit hooks do their job.*
6. **Push and Pull Request**:
   Push your isolated branch and open the PR on GitHub, specifying in the PR body which issue it solves and clearly stating: "Successfully tested locally".
