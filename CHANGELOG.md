# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.3] - 2025-07-16

### Added
- Expanded docstring attributes for LLM context in `server.py` for improved clarity and developer experience

### Changed
- Major documentation and README refactoring for easier setup and integration with Claude Desktop and Cursor, including clearer configuration examples and troubleshooting guidance

### Fixed
- Made `ATLAN_MCP_USER_AGENT` dynamic in `settings.py` to always reflect the current MCP server version in API requests

## [0.2.2] - 2025-06-23

### Added
- Multi-architecture build support for Docker images (ARM64 and AMD64)
- README support for asset updates - allows updating asset documentation/readme using markdown content
- Enhanced parameter parsing utilities for better Claude Desktop integration

### Fixed
- Search and Update Assets Tool compatibility issues with Claude Desktop
- String input parsing from Claude Desktop for better tool interaction
- Parameter validation and error handling improvements

### Changed
- Upgraded FastMCP dependency version for improved performance and stability
- Enhanced tool parameter processing with better error handling
- Improved asset update functionality with support for README content management

## [0.2.1] - 2025-05-24

### Added
- Advanced search operators support in `search_assets` including `contains`, `between`, and case-insensitive comparisons
- Default attributes for search results via `DEFAULT_SEARCH_ATTRIBUTES` constant with dynamic user-specified attribute support
- Enhanced "some conditions" handling with support for advanced operators and case-insensitive logic
- New search examples demonstrating OR logic for multiple type names and glossary term searches by specific attributes

### Changed
- Integrated `SearchUtils` for centralized and consistent search result processing
- Improved search API flexibility and precision with advanced query capabilities

### Fixed
- Release workflow changelog generation issues that previously caused empty release notes
- Improved commit range calculation and error handling in GitHub Actions workflow

## [0.2.0] - 2025-05-17

### Added
- Support for new transport modes: streamable HTTP and SSE
- MCP server executable script (`atlan-mcp-server`)
- Improved Docker image with non-root user and security enhancements

### Changed
- Made MCP server an installable package
- Updated dependencies and bumped versions
- Improved build process for faster Docker builds
- Restructured release workflow for better isolation and PR-based releases

### Fixed
- Various minor bugs and stability issues

### Documentation
- Updated setup and usage instructions
- Added more comprehensive examples


## [0.1.0] - 2024-05-05

### Added
- Initial release of Atlan MCP Server
- Basic functionality for integrating with Atlan
