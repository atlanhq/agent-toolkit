# Changelog

All notable changes to the Atlan Claude Code Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-16

### Added
- Initial release of the Atlan Claude Code Plugin
- **MCP Server Integration** via OAuth at `mcp.atlan.com/mcp` (15 tools)
  - Search & Discovery: `semantic_search_tool`
  - Lineage: `traverse_lineage_tool`
  - Asset Management: `update_assets_tool`
  - Glossary: `create_glossaries`, `create_glossary_terms`, `create_glossary_categories`
  - Data Mesh: `create_domains`, `create_data_products`
  - Data Quality: `create_dq_rules_tool`, `update_dq_rules_tool`, `schedule_dq_rules_tool`, `delete_dq_rules_tool`
  - Feature-flagged: `search_assets_tool`, `get_assets_by_dsl_tool`, `query_assets_tool`
- **CLAUDE.md** with tool usage conventions and guidelines
- Marketplace configuration for distribution
