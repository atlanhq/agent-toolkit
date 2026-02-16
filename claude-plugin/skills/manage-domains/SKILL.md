---
name: manage-domains
description: Create and manage data domains, subdomains, and data products in Atlan. Use when users want to organize their data mesh, define domain ownership, or create data products.
---

# Manage Data Domains & Products

The user wants to work with Atlan's data mesh capabilities - domains, subdomains, and data products.

## Instructions

- Parse the user's intent from: `$ARGUMENTS`
- Search for existing domains before creating new ones to avoid duplicates

### Creating Domains
- Use `create_domains` with name, description, and optional certificate status
- Domain names must be unique at the top level

### Creating Subdomains
- Use `create_domains` with `parent_domain_qualified_name` to nest under a parent domain
- Subdomain names must be unique within the same parent

### Creating Data Products
- Use `create_data_products` - requires:
  - `domain_qualified_name`: search for the domain first to get this
  - `asset_guids`: search for assets to link (at least one required)
- Product names must be unique within the same domain

## Workflow

1. Search for existing domains to avoid duplicates and get qualified names
2. Create domain/subdomain if needed
3. Search for assets to link to data products
4. Create data products with asset links
5. Confirm creation with GUIDs and qualified names
