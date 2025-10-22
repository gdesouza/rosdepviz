#!/usr/bin/env bash
set -euo pipefail

# Run tests with coverage and upload to Codecov using the codecov CLI.
# Usage: scripts/coverage_upload.sh
# Requires: pytest, coverage, codecov (python package 'codecov') installed in environment.

# Run pytest with coverage and generate xml report
pytest --cov=rosdepviz --cov-report=xml --cov-report=term

# Upload using codecov CLI (python package), fall back to bash uploader if it fails
if command -v codecov >/dev/null 2>&1; then
    if ! codecov -f coverage.xml; then
        echo "codecov python CLI failed; falling back to bash uploader" >&2
        # fallthrough to bash uploader
        :
    else
        exit 0
    fi
fi

# Fallback: use Codecov bash uploader
if command -v curl >/dev/null 2>&1; then
    curl -sSfL https://codecov.io/bash | bash -s -- -f coverage.xml || { echo "Codecov bash uploader failed" >&2; exit 3; }
elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://codecov.io/bash | bash -s -- -f coverage.xml || { echo "Codecov bash uploader failed" >&2; exit 3; }
else
    echo "Neither codecov CLI nor curl/wget available to upload coverage" >&2
    exit 4
fi
