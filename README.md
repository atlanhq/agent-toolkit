# Atlan Agent Toolkit

This repository contains a collection of tools and protocols for interacting with Atlan services for AI agents. Each component is designed to provide specific functionality and can be used independently or together.

## Components

### [Model Context Protocol (MCP)](modelcontextprotocol/README.md)
A protocol server that enables interaction with Atlan services through function calling. Provides tools for asset search and retrieval.


## Contributing Guidelines

We welcome contributions to the Atlan Agent Toolkit! Please follow these guidelines when submitting pull requests:

1. **Create a New Branch:**
   - Create a new branch for your changes.
   - Use a descriptive name for the branch (e.g., `feature/add-new-tool`).

2. **Make Your Changes:**
   - Make your changes in the new branch.
   - Ensure your tools are well-defined and follow the MCP specification.


3. **Submit a Pull Request:**
   - Push your changes to your branch.
   - Create a pull request against the `main` branch.
   - Provide a clear description of the changes and any related issues.
   - Ensure the PR passes all CI checks before requesting a review.

4. **Code Quality:**
   - We use pre-commit hooks to maintain code quality.
   - Install pre-commit in your local environment:
     ```bash
     uv pip install pre-commit
     pre-commit install
     ```
   - Pre-commit will automatically run checks before each commit, including:
     - Code formatting with Ruff
     - Trailing whitespace removal
     - End-of-file fixing
     - YAML and JSON validation
     - Other quality checks

5. **Environment Setup:**
   - This project uses UV for dependency management.
   - Refer to the [Model Context Protocol README](modelcontextprotocol/README.md) for setup instructions.
   - Python 3.11 or higher is required.

6. **Documentation:**
   - Update documentation to reflect your changes.
   - Add comments to your code where necessary.
