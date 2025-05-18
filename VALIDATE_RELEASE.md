# Validating the Release Process

This guide outlines steps to validate the release process on a feature branch before doing a real release to main.

## Setup

1. Create a feature branch for testing:
   ```
   git checkout -b feature/test-release main
   ```

2. Push the branch to GitHub:
   ```
   git push -u origin feature/test-release
   ```

3. Make sure version.py is updated with the right version:
   ```
   # Check current version
   cat modelcontextprotocol/version.py

   # Update if needed (example for a test version)
   echo '"""Version information."""\n\n__version__ = "0.2.0-test"' > modelcontextprotocol/version.py
   ```

## Manual Validation Steps

### 1. Validate Version Extraction
```
VERSION=$(grep -m 1 "__version__" modelcontextprotocol/version.py | cut -d'"' -f2)
echo "Version: $VERSION"
```

### 2. Validate Changelog Generation
```
# Get the previous tag or first commit
PREV_TAG=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || git rev-list --max-parents=0 HEAD)
RANGE="$PREV_TAG..HEAD"
echo "Changelog range: $RANGE"

# Generate test changelog
RELEASE_DATE=$(date +"%Y-%m-%d")
echo -e "## [$VERSION] - $RELEASE_DATE\n" > TEST_RELEASE_NOTES.md

# Add features
git log $RANGE --format="* %s (%h)" --grep="^feat" --perl-regexp --no-merges | sed -E 's/^\* feat(\(.+\))?:?\s*//' > features.txt
if [ -s features.txt ]; then
  echo -e "### Added\n" >> TEST_RELEASE_NOTES.md
  cat features.txt >> TEST_RELEASE_NOTES.md
  echo -e "\n" >> TEST_RELEASE_NOTES.md
fi

# Add fixes
git log $RANGE --format="* %s (%h)" --grep="^fix" --perl-regexp --no-merges | sed -E 's/^\* fix(\(.+\))?:?\s*//' > fixes.txt
if [ -s fixes.txt ]; then
  echo -e "### Fixed\n" >> TEST_RELEASE_NOTES.md
  cat fixes.txt >> TEST_RELEASE_NOTES.md
  echo -e "\n" >> TEST_RELEASE_NOTES.md
fi

# View output
cat TEST_RELEASE_NOTES.md
```

### 3. Validate PyPI Package Building
```
cd modelcontextprotocol
pip install build wheel
python -m build
# Verify the dist directory has the expected files
ls -la dist/
```

### 4. Validate Docker Build
```
cd modelcontextprotocol
docker build -t atlan-mcp-server:test .
# Verify the image was built
docker images | grep atlan-mcp-server
```

## GitHub Actions Validation

1. Create a test workflow file at `.github/workflows/test-release.yml` (already done)

2. Create a pull request from your feature branch to itself:
   - Go to GitHub > Pull Requests > New pull request
   - Set base: feature/test-release
   - Set compare: feature/test-release (or another branch with changes)
   - Create the pull request with a title like "Test Release Process"

3. Add the "test-release" label to the pull request

4. Monitor the workflow execution in GitHub Actions tab

5. Review the logs to ensure all steps are working as expected:
   - Version extraction
   - Changelog generation
   - PyPI package building
   - Docker image building

## Cleanup

After validation:

1. Delete the test PR if you created one
2. Revert any test-specific changes to version.py
3. Delete the feature/test-release branch when no longer needed

## Moving to Production

When you're ready for a real release:

1. Create a PR from your development branch to main
2. Add the "release" label to that PR
3. Merge the PR to trigger the actual release workflow
