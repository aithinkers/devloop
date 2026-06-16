#!/usr/bin/env bash
# Regenerate the per-tool packages from core/ + tools/.  `build.sh --check` verifies freshness.
exec python3 "$(dirname "$0")/build/build.py" "$@"
