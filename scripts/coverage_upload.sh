#!/usr/bin/env bash
set -euo pipefail

# Run tests with coverage and upload to Codecov using the codecov CLI.
# Usage: scripts/coverage_upload.sh
# Requires: pytest, coverage, codecov-cli (python package 'codecov-cli') installed in environment.

# Run pytest with coverage and generate xml report (prefer pytest-cov plugin when available)
rc_pytest=0
pytest --cov=rosdepviz --cov-report=xml --cov-report=term || rc_pytest=$?

# If pytest didn't produce coverage.xml (e.g., pytest-cov plugin missing), run via coverage run
rc_cov=0
if [ -f coverage.xml ]; then
    echo "Found coverage.xml (produced by pytest with pytest-cov)"
else
    if [ -f .coverage ]; then
        echo "coverage.xml not found, generating from .coverage"
        coverage xml -o coverage.xml || echo "coverage xml generation failed" >&2
    else
        echo "pytest --cov did not produce coverage info (rc=$rc_pytest). Running 'coverage run -m pytest -q' to generate coverage." >&2
        coverage run -m pytest -q || rc_cov=$?
        if [ -f .coverage ]; then
            coverage xml -o coverage.xml || echo "coverage xml generation failed" >&2
        fi
    fi
fi

# Debug: list files and show a snippet of coverage.xml (if present)
echo "Repository files:"
ls -la
if [ -f coverage.xml ]; then
    echo "coverage.xml size: $(stat -c%s coverage.xml) bytes"
    echo "coverage.xml head:" 
    head -n 20 coverage.xml || true
else
    echo "coverage.xml still missing; aborting upload" >&2
    # Continue to attempt upload anyway so CI logs the failure from codecov uploader
fi

# Upload using codecov-cli
if command -v codecov-cli >/dev/null 2>&1; then
    if ! sh -c "codecov-cli upload-process"; then
        echo "codecov-cli failed" >&2
        exit 3
    fi
else
    echo "codecov-cli not found, please install it with 'pip install codecov-cli'" >&2
    exit 4
fi
