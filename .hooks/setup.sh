#!/bin/bash
# Per-clone setup. Run once after `git clone`. Idempotent — safe to re-run.

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

echo "[setup] $(basename "$REPO_ROOT") — applying hooks config"

# Enable the shipped hooks in this folder
git config core.hooksPath .hooks
echo "[setup] ✓ core.hooksPath = .hooks"

# Make all hooks executable
chmod +x .hooks/pre-* 2>/dev/null || true
echo "[setup] ✓ hooks executable"

# Install the 'git ship' helper (feature-branch → PR → squash-merge → back on main).
# Global alias, so it applies in every repo on this machine. Re-run to refresh.
git config --global alias.ship '!f() { b=$(git symbolic-ref --short HEAD); if [ "$b" = main ] || [ "$b" = master ]; then echo "✗ on $b — branch first: git checkout -b <name>"; exit 1; fi; if [ -n "$(git status --porcelain --untracked-files=no)" ]; then echo "✗ uncommitted changes on $b — commit or stash first (nothing done)"; exit 1; fi; echo "→ pushing $b"; git push -u origin "$b" || exit 1; gh pr view "$b" >/dev/null 2>&1 || { echo "→ opening PR"; gh pr create --fill --base main --head "$b" || exit 1; }; echo "→ switching to main"; git checkout main || { echo "✗ could not switch to main — nothing merged, still safe on $b"; exit 1; }; echo "→ squash-merging $b"; gh pr merge "$b" --squash --delete-branch || { echo "✗ merge failed — you are on main, $b is intact, nothing lost"; exit 1; }; if git pull --ff-only; then echo "✓ shipped $b → main (now on $(git symbolic-ref --short HEAD))"; else echo "⚠ merged on GitHub, but local main did not fast-forward — run: git pull --ff-only"; exit 1; fi; }; f'
echo "[setup] ✓ git ship alias installed"

echo "[setup] done. See .hooks/README.md for what each hook does."
