import subprocess
import sys


def check_git_tag_exists(version_string: str) -> bool:
    """Checks if a git tag exists for the given version string."""
    tag_name = f"v{version_string}"
    print(f"Checking for git tag: {tag_name}")
    try:
        # Use git rev-parse to check if the tag exists. Returns 0 if it exists.
        subprocess.check_output(
            ["git", "rev-parse", tag_name], stderr=subprocess.STDOUT
        )
        print(f"Tag {tag_name} found.")
        return True
    except subprocess.CalledProcessError:
        print(f"Tag {tag_name} not found.")
        return False
    except FileNotFoundError:
        print(
            "Error: git command not found. Is git installed and in PATH?",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_tag.py <version>", file=sys.stderr)
        sys.exit(1)

    version = sys.argv[1]
    exists = check_git_tag_exists(version)

    # Output format for GitHub Actions
    print(f"::set-output name=exists::{str(exists).lower()}")
