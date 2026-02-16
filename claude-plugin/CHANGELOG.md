# Changelog

All notable changes to the Atlan Claude Code Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-16

### Added
- Initial release of the Atlan Claude Code Plugin
- **8 Skills** (agent-invoked):
  - `search-assets` - Natural language asset search via semantic search
  - `explore-lineage` - Upstream and downstream lineage traversal
  - `manage-glossary` - Glossary, term, and category management
  - `manage-domains` - Data domain and product management
  - `data-quality` - DQ rule creation, scheduling, and management
  - `update-assets` - Asset property updates (descriptions, certificates, terms, metadata)
  - `discover-metadata` - Custom metadata discovery via natural language
  - `review-governance` - Governance posture auditing with scorecards
- **MCP Server Integration** via OAuth at `mcp.atlan.com/mcp`
- **CLAUDE.md** with tool usage conventions and guidelines
- Marketplace configuration for distribution
