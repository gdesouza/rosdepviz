#!/usr/bin/env bash
set -euo pipefail

# Run tests with coverage and upload to Codecov using the codecov CLI.
# Usage: scripts/coverage_upload.sh
# Requires: pytest, coverage, codecov (python package 'codecov') installed in environment.

# Run pytest with coverage and generate xml report
pytest --cov=rosdepviz --cov-report=xml --cov-report=term || true

# Ensure coverage.xml exists. If not, try to generate it from the .coverage data file.
if [ -f coverage.xml ]; then
    echo "Found coverage.xml"
else
    if [ -f .coverage ]; then
        echo "coverage.xml not found, generating from .coverage"
        coverage xml -o coverage.xml || echo "coverage xml generation failed" >&2
    else
        echo "No .coverage file found; coverage.xml not present" >&2
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

# Upload using codecov CLI (python package), fall back to bash uploader if it fails
if command -v codecov >/dev/null 2>&1; then
    if ! codecov -f coverage.xml -v; then
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
