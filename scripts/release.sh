#!/usr/bin/env bash
# DevMind release script — bumps version, builds, publishes, updates README
set -euo pipefail

if [ -z "${1:-}" ]; then
    echo "Usage: ./scripts/release.sh <version>"
    echo "Example: ./scripts/release.sh 0.16.0"
    exit 1
fi

VERSION="$1"
echo "Releasing DevMind v${VERSION}"

# Validate version format
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "ERROR: Invalid version format. Use X.Y.Z"
    exit 1
fi

# Check working tree is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: Working tree not clean. Commit or stash changes first."
    git status --short
    exit 1
fi

# 1. Bump version in pyproject.toml
echo ">>> Bumping version in pyproject.toml"
sed -i "s/version = \".*\"/version = \"${VERSION}\"/" pyproject.toml

# 2. Bump version strings in commands
for f in src/devmind/commands/forecast.py src/devmind/commands/optimize.py; do
    sed -i "s/0\.[0-9]*\.[0-9]*/${VERSION}/g" "$f"
done

# 3. Bump banner in cli.py
sed -i "s/v[0-9]\+\.[0-9]\+\.[0-9]\+/v${VERSION}/g" src/devmind/cli.py

# 4. Bump README badge
sed -i "s/Version-[0-9]\+\.[0-9]\+\.[0-9]\+/Version-${VERSION}/g" README.md

echo ">>> Building..."
python3 -m build 2>&1 | tail -3

echo ">>> Uploading to PyPI..."
twine upload dist/devmind-${VERSION}* 2>&1 | tail -3

echo ">>> Git commit + tag..."
git add -A
git commit -m "v${VERSION} — Quality & Polish release"
git tag "v${VERSION}"
git push origin main --tags

echo ""
echo "Released v${VERSION} to PyPI: https://pypi.org/project/devmind/${VERSION}/"
