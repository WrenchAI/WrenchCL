#!/usr/bin/env bash
set -euo pipefail

VERSION_PART="$1"          # patch | minor | major
DRY_RUN="${DRY_RUN:-0}"    # Set DRY_RUN=1 for preview mode
PYPI_REPO="${PYPI_REPO:-pypi}"  # Default repo (use 'testpypi' to publish to Test PyPI)

PYPROJECT_FILE="pyproject.toml"

function log() {
  echo -e "[$(date +'%H:%M:%S')] $*"
}

function get_latest_version() {
  gh release view --json tagName -q '.tagName' 2>/dev/null | sed 's/^v//' || echo "0.0.0"
}

function get_file_version() {
  grep '^version = ' "$PYPROJECT_FILE" | sed -E 's/version = "([^"]+)"/\1/'
}

function bump_version() {
  local version="$1"
  local MAJOR MINOR PATCH

  IFS='.' read -r MAJOR MINOR PATCH <<< "${version}"
  MAJOR="${MAJOR:-0}"
  MINOR="${MINOR:-0}"
  PATCH="${PATCH:-0}"

  case "$VERSION_PART" in
    patch)
      PATCH=$((PATCH + 1))
      ;;
    minor)
      MINOR=$((MINOR + 1))
      PATCH=0
      ;;
    major)
      MAJOR=$((MAJOR + 1))
      MINOR=0
      PATCH=0
      ;;
    *)
      echo "❌ Invalid version part: $VERSION_PART"
      exit 1
      ;;
  esac

  echo "${MAJOR}.${MINOR}.${PATCH}"
}

function update_version_in_file() {
  local new_version="$1"
  sed -i.bak -E "s/^version = \".*\"/version = \"$new_version\"/" "$PYPROJECT_FILE"
  rm "${PYPROJECT_FILE}.bak"
  log "✅ Updated $PYPROJECT_FILE to version $new_version"
}

function do_release() {
  local version="$1"

  log "📦 Cleaning and building package..."
  rm -rf dist build *.egg-info
  python -m build

  log "🚀 Uploading to PyPI repository: $PYPI_REPO"
  if [[ "$DRY_RUN" == "1" ]]; then
    twine upload --repository "$PYPI_REPO" --non-interactive --skip-existing dist/*
  else
    twine upload --repository "$PYPI_REPO" dist/*
  fi

  log "🏷️ Preparing GitHub release..."
  if [[ "$DRY_RUN" == "1" ]]; then
    log "🔍 DRY RUN: gh release create \"v$version\" --repo WrenchAI/WrenchCL --title \"v$version\" ..."
  else
    gh release create "v$version" \
      --repo "WrenchAI/WrenchCL" \
      --title "v$version" \
      --generate-notes \
      dist/*
  fi

  log "✅ Release v$version complete"
}


function main() {
  local latest_version
  latest_version="$(get_latest_version)"
  local file_version
  file_version="$(get_file_version)"
  local new_version
  new_version="$(bump_version "$latest_version")"

  log "📄 Current file version: $file_version"
  log "🏷️ Latest GitHub version: $latest_version"
  log "🔢 Bumping to: \"$new_version\""

  update_version_in_file "$new_version"
  do_release "$new_version"
}

main
