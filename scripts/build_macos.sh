#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(uname -s)" != Darwin ]]; then
  echo 'Build this app on macOS; PyInstaller does not cross-compile.' >&2
  exit 1
fi
# Target the build machine's macOS generation, unless explicitly overridden.
MACOS_VERSION="$(sw_vers -productVersion)"
MACOS_MAJOR="${MACOS_VERSION%%.*}"
export BUDGETTRACKER_MIN_MACOS="${BUDGETTRACKER_MIN_MACOS:-${MACOS_MAJOR}.0}"
PYTHON="${PYTHON:-python3}"
"$PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 12), "Use Python 3.12 with Tcl/Tk support"'
"$PYTHON" -m pip install -r requirements-build.txt
"$PYTHON" release_checks.py
"$PYTHON" -m PyInstaller --clean --noconfirm BudgetTracker-macOS.spec
# Test the actual bundled interpreter and bundled dependencies.
dist/BudgetTracker.app/Contents/MacOS/BudgetTracker --smoke-test
codesign --verify --deep --strict dist/BudgetTracker.app
mkdir -p release
ARCH="$(uname -m)"
ARCHIVE="release/BudgetTracker-macOS-${ARCH}.zip"
ditto -c -k --sequesterRsrc --keepParent dist/BudgetTracker.app "$ARCHIVE"
shasum -a 256 "$ARCHIVE" > "${ARCHIVE}.sha256"
echo "Created $ARCHIVE"
