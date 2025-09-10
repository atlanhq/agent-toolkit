"""
Package header middleware for FastMCP to set x-atlan-package-name header.

This middleware captures the tool name being called and updates the Atlan client
headers to include the x-atlan-package-name header with the tool name.
"""

import logging
from typing import Optional
from fastmcp.server.middleware import Middleware, MiddlewareContext
from client import get_atlan_client

logger = logging.getLogger(__name__)


class PackageHeaderMiddleware(Middleware):
    """
    Middleware to set x-atlan-package-name header with the current tool name.
    
    This middleware intercepts tool calls and updates the Atlan client headers
    to include the name of the tool being called in the x-atlan-package-name header.
    """

    def __init__(self):
        """Initialize the Package Header Middleware."""
        logger.info("Package Header Middleware initialized")

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """
        Updates the Atlan client headers to include the x-atlan-package-name header
        with the current tool name before executing the tool.
        """
        tool_name = context.message.name
        
        try:
            logger.debug(f"Setting x-atlan-package-name header to: {tool_name}")
            client = get_atlan_client()
            
            package_headers = {"x-atlan-package-name": tool_name}
            client.update_headers(package_headers)
            
            logger.debug(f"Successfully set x-atlan-package-name header for tool: {tool_name}")
            return await call_next(context)
            
        except Exception as e:
            logger.error(
                f"Error setting package header for tool {tool_name}: {str(e)}",
                exc_info=True,
            )
            return await call_next(context)
