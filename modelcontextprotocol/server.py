from fastmcp import FastMCP
from tools import(
    get_user_by_username, 
    get_user_by_email, 
    get_group_by_name, 
    get_users_from_group, 
    get_trait_names, 
)
from typing import Dict, Any, List, Optional

mcp = FastMCP(
    "Altan MCP", 
    dependencies=["pyatlan"]
)

@mcp.tool()
def get_user_by_username_tool(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    return get_user_by_username(username)


@mcp.tool()
def get_user_by_email_tool(email: str) -> Optional[List[Dict[str, Any]]]:
    """Get user by email"""
    return get_user_by_email(email)


@mcp.tool()
def get_group_by_name_tool(group_name: str) -> Optional[List[Dict[str, Any]]]:
    """Get group by name"""
    return get_group_by_name(group_name)


@mcp.tool()
def get_users_from_group_tool(group_name: str):
    """Get users from group"""
    return get_users_from_group(group_name)


@mcp.tool()
def get_trait_names_tool(tag_name: str) -> Optional[List[str]]:
    """Get trait names"""
    return get_trait_names(tag_name)

