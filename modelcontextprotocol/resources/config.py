"""
Configuration and connection resources for Atlan MCP server.
"""

import json
from typing import Optional, Dict, Any
from fastmcp import Context
from settings import Settings


async def atlan_config_resource(ctx: Optional[Context] = None) -> Dict[str, Any]:
    """
    Provide Atlan configuration information and server capabilities.
    
    Args:
        ctx: FastMCP context for logging
        
    Returns:
        Dictionary containing configuration text
    """
    
    if ctx:
        await ctx.info("Loading Atlan configuration information")
    
    try:
        settings = Settings()
        base_url = settings.ATLAN_BASE_URL
        environment = "production" if "prod" in base_url.lower() else "development"
    except Exception:
        # Handle case where settings are not configured (e.g., during testing)
        base_url = "https://demo.atlan.com"
        environment = "demo"
    
    config_data = {
        "server_info": {
            "base_url": base_url,
            "environment": environment,
            "user_agent": "Atlan-MCP-Server",
            "note": "Demo configuration - update settings.py for production use"
        },
        "capabilities": {
            "search": {
                "enabled": True,
                "max_results": 1000,
                "supported_operators": [
                    "match", "startswith", "contains", "between", "within"
                ],
                "supported_filters": [
                    "asset_type", "connection_qualified_name", "tags", 
                    "certificate_status", "owner_users", "domain_guids"
                ]
            },
            "lineage": {
                "enabled": True,
                "max_depth": 10,
                "directions": ["UPSTREAM", "DOWNSTREAM"],
                "immediate_neighbors": True
            },
            "metadata_updates": {
                "enabled": True,
                "updatable_attributes": [
                    "user_description", "certificate_status", "readme"
                ],
                "certificate_statuses": ["VERIFIED", "DRAFT", "DEPRECATED"]
            },
            "dsl_queries": {
                "enabled": True,
                "elasticsearch_compatible": True,
                "custom_scoring": True
            }
        },
        "limits": {
            "search_default_limit": 10,
            "search_max_limit": 1000,
            "lineage_default_size": 10,
            "lineage_max_depth": 1000000,
            "batch_update_max_assets": 100
        },
        "default_attributes": {
            "search": [
                "name", "display_name", "description", "qualified_name",
                "certificate_status", "owner_users", "owner_groups", 
                "connector_name", "asset_tags"
            ],
            "lineage": [
                "name", "display_name", "description", "qualified_name",
                "certificate_status", "owner_users", "owner_groups",
                "connector_name", "has_lineage", "source_created_at",
                "source_updated_at", "readme", "asset_tags"
            ]
        },
        "supported_asset_types": [
            "Table", "Column", "View", "Database", "Schema",
            "Connection", "Query", "Collection", "AtlasGlossary",
            "AtlasGlossaryCategory", "AtlasGlossaryTerm", "File",
            "Process", "DataSet", "Report"
        ]
    }
    
    return {
        "text": json.dumps(config_data, indent=2)
    }


async def connection_info_resource(
    connection_name: Optional[str] = None,
    ctx: Optional[Context] = None
) -> Dict[str, Any]:
    """
    Provide information about Atlan connections and their capabilities.
    
    Args:
        connection_name: Specific connection to get info for (optional)
        ctx: FastMCP context for logging
        
    Returns:
        Dictionary containing connection information
    """
    
    if ctx:
        log_msg = f"Loading connection info for {connection_name}" if connection_name else "Loading all connection info"
        await ctx.info(log_msg)
    
    # Common connection types and their characteristics
    connection_types = {
        "snowflake": {
            "type": "Data Warehouse",
            "capabilities": ["SQL queries", "Bulk data operations", "Metadata extraction"],
            "asset_types": ["Database", "Schema", "Table", "View", "Column"],
            "features": {
                "supports_lineage": True,
                "supports_profiling": True,
                "supports_sampling": True,
                "supports_real_time": False
            }
        },
        "bigquery": {
            "type": "Data Warehouse", 
            "capabilities": ["SQL queries", "Machine learning", "Real-time analytics"],
            "asset_types": ["Project", "Dataset", "Table", "View", "Column"],
            "features": {
                "supports_lineage": True,
                "supports_profiling": True,
                "supports_sampling": True,
                "supports_real_time": True
            }
        },
        "databricks": {
            "type": "Lakehouse Platform",
            "capabilities": ["Spark processing", "Delta Lake", "ML workflows"],
            "asset_types": ["Catalog", "Schema", "Table", "Volume", "Column"],
            "features": {
                "supports_lineage": True,
                "supports_profiling": True,
                "supports_sampling": True,
                "supports_real_time": True
            }
        },
        "postgresql": {
            "type": "Relational Database",
            "capabilities": ["ACID transactions", "JSON support", "Extensions"],
            "asset_types": ["Database", "Schema", "Table", "View", "Column"],
            "features": {
                "supports_lineage": True,
                "supports_profiling": True,
                "supports_sampling": True,
                "supports_real_time": False
            }
        },
        "s3": {
            "type": "Object Storage",
            "capabilities": ["File storage", "Data archival", "Static hosting"],
            "asset_types": ["Bucket", "Folder", "File"],
            "features": {
                "supports_lineage": True,
                "supports_profiling": False,
                "supports_sampling": False,
                "supports_real_time": False
            }
        }
    }
    
    if connection_name:
        # Return specific connection info if requested
        conn_type = connection_name.lower()
        for key in connection_types:
            if key in conn_type:
                info = connection_types[key].copy()
                info["connection_name"] = connection_name
                return {"text": json.dumps(info, indent=2)}
        
        # If specific connection not found, return generic info
        return {
            "text": json.dumps({
                "connection_name": connection_name,
                "status": "Connection type not recognized",
                "note": "Generic connection - capabilities may vary"
            }, indent=2)
        }
    
    # Return all connection type information
    return {
        "text": json.dumps({
            "supported_connection_types": connection_types,
            "notes": {
                "lineage_support": "Most connections support lineage tracking",
                "profiling_support": "Database connections typically support profiling",
                "real_time_support": "Cloud data warehouses often support real-time features"
            }
        }, indent=2)
    }