# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.10] - 2025-10-13

### Fixed
- Fixed an issue that prevented updates to glossary terms and categories.

## [0.2.9] - 2025-09-22

### Fixed
- Transport configuration not working when installed via PyPI and executed using `uvx atlan-mcp-server` - server would ignore environment variables and command-line arguments, always defaulting to stdio mode

## [0.2.8] - 2025-09-15

### Added
- Term linking functionality for improved glossary term relationships (#138)
- Enhanced search tool with popularity attributes context and examples (#132)
- Comprehensive MCP transport mode documentation (#124)

### Changed
- Implemented client singleton pattern for improved connection pool reuse and performance (#131)
- Enhanced Docker configuration with improved .dockerignore settings (#127)

## [0.2.7] - 2025-09-02

### Added
- Configurable tool access control via `RESTRICTED_TOOLS` environment variable
- Organizations can now restrict any combination of tools for MCP clients


## [0.2.6] - 2025-08-19

### Added
- Glossary management tools to streamline glossary creation and management:
  - `create_glossaries`: Create top-level glossaries with metadata (name, `user_description`, optional `certificate_status`)
  - `create_glossary_terms`: Add individual terms to an existing glossary; supports `user_description`, optional `certificate_status`, and `category_guids`
  - `create_glossary_categories`: Add categories (and nested subcategories) anchored to a glossary or parent category; supports `user_description` and optional `certificate_status`
- Bulk creation support across glossaries, terms, and categories to enable scalable glossary builds
- Foundation for automated, structured glossary generation from unstructured content


## [0.2.5] - 2025-08-05

### Changed
- Enhanced `search_assets_tool` documentation and usage examples for `connection_qualified_name` parameter
- Added `connection_qualified_name` parameter to example function calls for missing descriptions and multiple asset types searches

## [0.2.4] - 2025-07-24

### Added
- Enhanced lineage traversal tool with configurable attribute inclusion support
- `include_attributes` parameter in `traverse_lineage_tool` allowing users to specify additional attributes beyond defaults
- Default attributes are now always included: name, display_name, description, qualified_name, user_description, certificate_status, owner_users, owner_groups, connector_name, has_lineage, source_created_at, source_updated_at, readme, asset_tags

### Changed
- Improved lineage tool return format to standardized dictionary structure with `assets` and `error` keys
- Enhanced lineage processing using Pydantic serialization with `dict(by_alias=True, exclude_unset=True)` for consistent API responses
- Updated `immediate_neighbors` default value from `True` to `False` to align with underlying FluentLineage behavior
- Better error handling and logging throughout lineage traversal operations

### Fixed
- Lineage tool now returns richer attribute information instead of just default minimal attributes
- Resolved issue where lineage results only contained basic metadata without requested additional attributes

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
- Default attributes for search results via `