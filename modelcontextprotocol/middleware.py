"""
Tool restriction middleware for FastMCP to control tool access.

This middleware restricts access to specified tools based on configuration.
Tools can be restricted globally by providing a list during initialization.
"""

from typing import List, Set, Optional
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.exceptions import ToolError
import logging

logger = logging.getLogger(__name__)


class ToolRestrictionMiddleware(Middleware):
    """
    Middleware to restrict tool access based on configuration.

    Allows specifying which tools should be restricted during initialization.
    Restricted tools will be hidden from the tools list and blocked from execution.
    """

    def __init__(self, restricted_tools: Optional[List[str]] = None):
        """
        Initialize the Tool Restriction Middleware.

        Args:
            restricted_tools: List of tool names to restrict. If None, no tools are restricted.
        """
        self.restricted_tools: Set[str] = set(restricted_tools or [])
        self._log_initialization()

    def _log_initialization(self) -> None:
        """Log middleware initialization details."""
        logger.info(
            f"Tool Restriction Middleware initialized with {len(self.restricted_tools)} restricted tools",
            restricted_tools=list(self.restricted_tools),
        )

    def _is_tool_restricted(self, tool_name: str) -> bool:
        """
        Check if a tool is restricted.

        Args:
            tool_name: Name of the tool being called.

        Returns:
            True if the tool is restricted, False otherwise.
        """
        is_restricted = tool_name in self.restricted_tools

        if is_restricted:
            logger.info(f"Tool {tool_name} is restricted", tool=tool_name)

        return is_restricted

    def _get_error_message(self, tool_name: str) -> str:
        """
        Get appropriate error message for a restricted tool.

        Args:
            tool_name: Name of the restricted tool.

        Returns:
            Error message string.
        """
        return f"Tool '{tool_name}' is not available due to access restrictions"

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """
        Hook called when a tool is being executed.

        Checks if the tool is restricted and either allows execution or raises an error.

        Args:
            context: The middleware context containing request information.
            call_next: Function to call the next middleware/handler in the chain.

        Returns:
            The result from the next handler if allowed.

        Raises:
            ToolError: If the tool is restricted.
        """
        tool_name = context.message.name

        try:
            # Check if tool is restricted
            if self._is_tool_restricted(tool_name):
                error_message = self._get_error_message(tool_name)

                logger.warning(
                    f"Tool access denied: {tool_name}",
                    tool=tool_name,
                    reason=error_message,
                )

                raise ToolError(error_message)

            # Tool is allowed, proceed with execution
            logger.debug(f"Tool access granted: {tool_name}", tool=tool_name)

            return await call_next(context)

        except ToolError:
            # Re-raise ToolError as-is
            raise
        except Exception as e:
            # Handle unexpected errors
            logger.error(
                f"Error in tool restriction middleware: {str(e)}",
                tool=tool_name,
                exc_info=True,
            )
            # Re-raise the original exception
            raise

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        """
        Hook called when listing available tools.

        Filters the tool list to hide restricted tools.

        Args:
            context: The middleware context.
            call_next: Function to call the next handler.

        Returns:
            Filtered list of tools.
        """
        # Get the full list of tools
        all_tools = await call_next(context)

        try:
            # If no tools are restricted, return all tools
            if not self.restricted_tools:
                return all_tools

            # Filter out restricted tools
            filtered_tools = [
                tool for tool in all_tools if tool.name not in self.restricted_tools
            ]

            logger.debug(
                "Filtered tool list",
                total_tools=len(all_tools),
                filtered_tools=len(filtered_tools),
                restricted_tools=list(self.restricted_tools),
            )

            return filtered_tools

        except Exception as e:
            logger.error(
                f"Error filtering tool list: {str(e)}",
                exc_info=True,
            )
            # On error, return the original list to avoid breaking functionality
            return all_tools
