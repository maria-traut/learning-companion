# Project-specific configuration for the workflow hooks.
# Adapt these to your project. Everything else should work unchanged.

TEST_CMD=".venv/bin/pytest -q"
LINT_CMD=".venv/bin/ruff check ."

# File whose presence means the project is runnable, so the test gates apply.
PROJECT_MARKER="src/manage.py"

# Run the test suite after every source/test file write (records red/green
# for the TDD cycle). Set to "false" if your suite is too slow for that;
# tests are then only enforced at commit time.
RUN_TESTS_ON_WRITE="true"

# Branches that may never receive direct commits or force-pushes.
PROTECTED_BRANCHES="main|master"

# Directories that count as production/test code (used by the write guard).
# src = Django project and apps, tests = project-level tests.
SOURCE_DIRS="src|tests"
