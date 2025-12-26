#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/archive_secret.sh [relative/path/to/secret.json] [archive-dir]
SECRET_PATH=${1:-secrets/infinity-x-one-systems-sa.json}
ARCHIVE_DIR=${2:-"$HOME/.secure_secrets/mcp"}

echo "Repository root: $(git rev-parse --show-toplevel 2>/dev/null || echo 'not a git repo')"
echo "Secret to archive: $SECRET_PATH"
echo "Archive directory: $ARCHIVE_DIR"

if [ ! -f "$SECRET_PATH" ]; then
  echo "ERROR: secret file not found: $SECRET_PATH"
  exit 1
fi

# Create archive dir
mkdir -p "$ARCHIVE_DIR"
chmod 700 "$ARCHIVE_DIR"

# Move secret to archive, restrict perms
mv "$SECRET_PATH" "$ARCHIVE_DIR/"
ARCHIVED_PATH="$ARCHIVE_DIR/$(basename "$SECRET_PATH")"
chmod 600 "$ARCHIVED_PATH"
echo "Moved secret to: $ARCHIVED_PATH"

# Unstage and remove from git index if present
if git ls-files --error-unmatch "$SECRET_PATH" >/dev/null 2>&1; then
  git rm --cached --quiet "$SECRET_PATH" || true
  echo "Removed $SECRET_PATH from git index (unstaged)."
fi

# Ensure .gitignore contains 'secrets/'
GITIGNORE=".gitignore"
if [ -f "$GITIGNORE" ]; then
  if ! grep -qxF "secrets/" "$GITIGNORE" 2>/dev/null; then
    echo -e "\n# Ignore secrets directory (added by archive_secret.sh)\nsecrets/" >> "$GITIGNORE"
    git add "$GITIGNORE"
    git commit -m "chore: ignore secrets/ and archive sensitive file" || true
    echo ".gitignore updated and committed."
  else
    echo ".gitignore already contains 'secrets/'."
  fi
else
  echo -e "# Ignore secrets directory\nsecrets/" > "$GITIGNORE"
  git add "$GITIGNORE"
  git commit -m "chore: ignore secrets/ (created .gitignore)" || true
  echo "Created .gitignore and committed."
fi

echo ""
echo "NEXT STEPS (manual):"
echo "1) Rotate the service account keys immediately in GCP and revoke the archived key."
echo "2) If the secret was committed in previous history, purge it using git-filter-repo or BFG:"
echo "   git filter-repo --path secrets/infinity-x-one-systems-sa.json --invert-paths"
echo "3) Coordinate with the team before force-pushing cleaned history:"
echo "   git push --force --all && git push --force --tags"
echo ""
echo "Export env locally to use archived service account:"
echo "  export GOOGLE_APPLICATION_CREDENTIALS=\"$ARCHIVED_PATH\""
echo ""
echo "Done."
