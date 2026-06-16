#!/usr/bin/env sh
# DevLoop bootstrap installer.
#
#   curl -fsSL https://raw.githubusercontent.com/<owner>/devloop/main/install.sh | sh
#   curl -fsSL .../install.sh | sh -s -- --host claude --scope home
#
# Clones (or updates) DevLoop into ~/.devloop/src and runs `devloop install` with any
# arguments you pass after `--`. If you've already cloned the repo, just run ./devloop.
set -eu

REPO_URL="${DEVLOOP_REPO:-https://github.com/your-org/devloop.git}"
SRC="${DEVLOOP_HOME:-$HOME/.devloop}/src"

if ! command -v git >/dev/null 2>&1; then echo "git is required"; exit 1; fi
if ! command -v python3 >/dev/null 2>&1; then echo "python3 is required"; exit 1; fi

if [ -d "$SRC/.git" ]; then
  echo "Updating DevLoop in $SRC ..."
  git -C "$SRC" pull --ff-only --quiet || true
else
  echo "Fetching DevLoop into $SRC ..."
  mkdir -p "$(dirname "$SRC")"
  git clone --depth 1 "$REPO_URL" "$SRC" --quiet
fi

# If the package lives in a subdir named devloop/, prefer it.
if [ -x "$SRC/devloop" ]; then PKG="$SRC"; else PKG="$SRC/devloop"; fi
chmod +x "$PKG/devloop" 2>/dev/null || true

echo "Running: devloop install $*"
exec "$PKG/devloop" install "$@"
