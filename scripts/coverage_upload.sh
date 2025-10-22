#!/usr/bin/env bash
set -euo pipefail

# Run tests with coverage and upload to Codecov using the codecov CLI.
# Usage: scripts/coverage_upload.sh
# Requires: pytest, coverage, codecov (python package 'codecov') installed in environment.

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

# Prepare token argument if CODECOV_TOKEN is present
TOKEN_ARG=""
if [ -n "${CODECOV_TOKEN:-}" ]; then
    echo "Using CODECOV_TOKEN from environment"
    TOKEN_ARG="-t ${CODECOV_TOKEN}"
else
    echo "CODECOV_TOKEN not set. If this repo requires a token for uploads, the upload may fail." >&2
fi

# Upload using codecov CLI (python package), fall back to bash uploader if it fails
if command -v codecov >/dev/null 2>&1; then
    if ! sh -c "codecov ${TOKEN_ARG} -f coverage.xml -v"; then
        echo "codecov python CLI failed; falling back to bash uploader" >&2
        # fallthrough to bash uploader
        :
    else
        exit 0
    fi
fi

# Fallback: use Codecov bash uploader
if command -v curl >/dev/null 2>&1; then
    if ! sh -c "curl -sSfL https://codecov.io/bash | bash -s -- ${TOKEN_ARG} -f coverage.xml"; then
        echo "Codecov bash uploader failed" >&2
        exit 3
    fi
elif command -v wget >/dev/null 2>&1; then
    if ! sh -c "wget -qO- https://codecov.io/bash | bash -s -- ${TOKEN_ARG} -f coverage.xml"; then
        echo "Codecov bash uploader failed" >&2
        exit 3
    fi
else
    echo "Neither codecov CLI nor curl/wget available to upload coverage" >&2
    exit 4
fi
