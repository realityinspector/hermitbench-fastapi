
#!/bin/bash

echo "Starting git cleanup process..."

# Store paths to clean up
PATHS=(
    "__pycache__"
    "test_outputs/*.*"
    "alembic.ini"
    "attached_assets/*.*"
)

# Create temporary file for tracking operations
OPERATIONS_FILE=$(mktemp)

echo "Finding all matches..."
for path in "${PATHS[@]}"; do
    # Find all matching files/directories and add to operations list
    find . -name "$path" -type f -o -type d >> "$OPERATIONS_FILE"
done

echo "Found matches:"
cat "$OPERATIONS_FILE"

echo "Removing from git history..."
while IFS= read -r file; do
    if [ -n "$file" ]; then
        echo "Processing: $file"
        git filter-branch --force --index-filter \
            "git rm -rf --cached --ignore-unmatch $file" \
            --prune-empty --tag-name-filter cat -- --all
    fi
done < "$OPERATIONS_FILE"

# Clean up refs and force garbage collection
echo "Cleaning up..."
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push changes
echo "Pushing changes..."
git push origin --force

# Clean up operations file
rm "$OPERATIONS_FILE"

echo "Cleanup complete!"

# Self-destruct
rm -- "$0"
