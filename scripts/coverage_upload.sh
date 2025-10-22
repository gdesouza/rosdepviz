#!/usr/bin/env bash
set -euo pipefail

# Run tests with coverage and upload to Codecov using the codecov CLI.
# Usage: scripts/coverage_upload.sh
# Requires: pytest, coverage, codecov (python package 'codecov') installed in environment.

# Run pytest with coverage and generate xml report
pytest --cov=rosdepviz --cov-report=xml --cov-report=term

# Upload using codecov CLI (python package)
if command -v codecov >/dev/null 2>&1; then
    codecov -f coverage.xml
else
    echo "codecov CLI not found. Install it with 'pip install codecov' or ensure it's on PATH." >&2
    exit 2
fi
