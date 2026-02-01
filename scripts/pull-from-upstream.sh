#!/bin/bash
# Pull from upstream using rebase (default) or merge
# Usage: pull-from-upstream.sh [--merge]
#
# Default (rebase): Best for solo workflow - cherry-picked duplicates are skipped
# --merge: Use when others contribute to upstream - creates merge commit

set -e

UPSTREAM_URL="https://github.com/todorkolev/lean-playground.git"
USE_MERGE=false

if [[ "$1" == "--merge" ]]; then
    USE_MERGE=true
fi

# Auto-add upstream remote if not configured
if ! git remote get-url upstream &>/dev/null; then
    echo "Adding upstream remote: $UPSTREAM_URL"
    git remote add upstream "$UPSTREAM_URL"
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

echo ""
echo "Fetching upstream..."
git fetch upstream

echo ""
echo "Commits in upstream not in your branch:"
git log --oneline HEAD..upstream/main || echo "  (none)"

echo ""
echo "Commits in your branch not in upstream:"
git log --oneline upstream/main..HEAD || echo "  (none)"

# Check if already up to date
if [[ -z "$(git log --oneline HEAD..upstream/main)" ]]; then
    echo ""
    echo "Already up to date with upstream/main."
    exit 0
fi

echo ""
if [[ "$USE_MERGE" == "true" ]]; then
    echo "Merging upstream/main (use for external contributions)..."
    git merge upstream/main --no-edit
else
    echo "Rebasing on upstream/main..."
    echo "(Cherry-picked duplicates will be skipped automatically)"
    git pull --rebase upstream main
fi

echo ""
echo "Done! Branch '$CURRENT_BRANCH' is now synced with upstream."
git log --oneline -5
