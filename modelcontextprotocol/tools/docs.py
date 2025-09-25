"""
Documentation tools for MCP server.
Provides access to Atlan documentation with domain validation for security.
Includes HTML to Markdown conversion to preserve links and reduce tokens.
"""

import re
import httpx
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from dataclasses import dataclass
from markdownify import markdownify as md


@dataclass
class DocSource:
    """Represents a documentation source with name and llms.txt URL."""

    name: str
    llms_txt_url: str
    allowed_domains: List[str]
    description: str


class DocumentationManager:
    """Manages documentation sources and secure fetching."""

    def __init__(self):
        self.sources: Dict[str, DocSource] = {}
        self.timeout = (
            15.0  # Timeout for documentation fetching (reduced to prevent MCP timeouts)
        )
        self.follow_redirects = True  # Allow redirects for documentation URLs
        self._initialize_default_sources()

    def _initialize_default_sources(self):
        """Initialize with default documentation sources."""
        default_sources = [
            DocSource(
                name="Atlan Docs",
                llms_txt_url="https://docs.atlan.com/llms.txt",
                allowed_domains=["docs.atlan.com"],
                description="Official Atlan product documentation",
            )
        ]

        for source in default_sources:
            self.sources[source.name] = source

    def list_sources(self) -> List[Dict[str, Any]]:
        """List all available documentation sources."""
        return [
            {
                "name": source.name,
                "llms_txt_url": source.llms_txt_url,
                "allowed_domains": source.allowed_domains,
                "description": source.description,
            }
            for source in self.sources.values()
        ]

    def _is_domain_allowed(self, url: str, allowed_domains: List[str]) -> bool:
        """Check if URL domain is in allowed domains list."""
        if "*" in allowed_domains:
            return True

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        for allowed in allowed_domains:
            if domain == allowed.lower() or domain.endswith("." + allowed.lower()):
                return True

        return False

    async def _fetch_content(self, url: str) -> Dict[str, Any]:
        """Fetch content and content-type from URL with proper error handling."""
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, read=self.timeout, connect=5.0),
                follow_redirects=self.follow_redirects,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return {
                    "text": response.text,
                    "content_type": response.headers.get("content-type", ""),
                }
        except httpx.TimeoutException:
            raise Exception(f"Timeout fetching {url} after {self.timeout}s")
        except httpx.RequestError as e:
            raise Exception(f"Request error fetching {url}: {e}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code} error fetching {url}: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error fetching {url}: {e}")

    def _html_to_markdown(self, html: str) -> Dict[str, Optional[str]]:
        """Convert HTML to markdown, preserving links and reducing tokens.

        Returns a dict containing:
        - text: cleaned markdown content with links preserved
        - title: page title if found
        """
        # Extract title using simple regex
        title = None
        h1_match = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.IGNORECASE)
        if h1_match:
            title = h1_match.group(1).strip()
        else:
            title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                # Clean up title (remove " | Atlan Documentation" suffix)
                title = re.sub(r"\s*\|\s*Atlan Documentation.*$", "", title)

        # Pre-process HTML to remove JavaScript and other unwanted content
        # Remove script tags with proper case-insensitive matching for both opening and closing tags
        # This pattern is more secure and handles nested content properly
        html = re.sub(
            r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
            "",
            html,
            flags=re.IGNORECASE,
        )

        # Remove inline JavaScript patterns
        html = re.sub(r"window\.dataLayer.*?(?=\n|$)", "", html, flags=re.MULTILINE)
        html = re.sub(r"!function\([^)]*\).*?}\)\([^)]*\);?", "", html, flags=re.DOTALL)
        html = re.sub(
            r"window\.[a-zA-Z_$][a-zA-Z0-9_$]*\s*=.*?(?=\n|$)",
            "",
            html,
            flags=re.MULTILINE,
        )
        html = re.sub(r"\(function\(\).*?}\)\(\);?", "", html, flags=re.DOTALL)

        # Remove JSON-LD structured data
        html = re.sub(
            r'\{"@context".*?"https://schema\.org".*?\}', "", html, flags=re.DOTALL
        )

        # Convert HTML to markdown using markdownify with comprehensive stripping
        markdown_text = md(
            html,
            heading_style="ATX",  # Use # for headings
            bullets="-",  # Use - for bullets
            strip=[
                # Core unwanted elements
                "script",
                "style",
                "noscript",
                "meta",
                "link",
                "title",
                # Navigation and UI elements
                "nav",
                "header",
                "footer",
                "aside",
                "menu",
                # Forms and interactive elements
                "form",
                "button",
                "input",
                "select",
                "textarea",
                # Media and embedded content that doesn't convert well
                "iframe",
                "svg",
                "canvas",
                "audio",
                "video",
                # SEO and tracking elements
                "base",
                "area",
                "map",
                "embed",
                "object",
                "param",
            ],
        )

        # Post-processing cleanup
        # Remove title duplication from content (keep only the H1, remove title text)
        markdown_text = re.sub(
            r"^[^#\n]*\|\s*Atlan Documentation\s*\n+", "", markdown_text
        )

        # Remove empty links and malformed links
        markdown_text = re.sub(r"\[\s*\]\([^)]*\)", "", markdown_text)
        markdown_text = re.sub(
            r"\[!\[.*?\]\([^)]*\)\]\([^)]*\)", "", markdown_text
        )  # Remove logo links

        # Remove navigation artifacts
        markdown_text = re.sub(
            r"^[-•]\s*(Connect data|Data Warehouses|Amazon Redshift)\s*$",
            "",
            markdown_text,
            flags=re.MULTILINE,
        )
        markdown_text = re.sub(r"On this page\s*\n", "", markdown_text)
        markdown_text = re.sub(
            r"Copyright © \d{4} Atlan Pte\. Ltd\.", "", markdown_text
        )

        # Remove skip links and search
        markdown_text = re.sub(r"\[Skip to main content\]\([^)]*\)", "", markdown_text)
        markdown_text = re.sub(r"Search\s*\n", "", markdown_text)

        # Remove navigation menus
        markdown_text = re.sub(
            r"\[What's new\].*?\[Contact support\].*?\n",
            "",
            markdown_text,
            flags=re.DOTALL,
        )
        markdown_text = re.sub(
            r"\[Get started\]\([^)]*\)\s*\n\s*\[Connect data\]\([^)]*\).*?\[Build with Atlan\]\([^)]*\)",
            "",
            markdown_text,
            flags=re.DOTALL,
        )

        # Remove sidebar navigation
        markdown_text = re.sub(
            r"- \[Amazon Redshift\]\([^)]*\)\s*\n\s*- \[Get Started\].*?- \[Troubleshooting\].*?\n",
            "",
            markdown_text,
            flags=re.DOTALL,
        )

        # Remove "Next" navigation and table of contents
        markdown_text = re.sub(
            r"\[Next\s*\n\s*[^\]]+\]\([^)]*\)", "", markdown_text, flags=re.DOTALL
        )
        markdown_text = re.sub(
            r"\n- \[.*?\]\(#.*?\)\s*$", "", markdown_text, flags=re.MULTILINE
        )

        # Clean up whitespace and formatting
        markdown_text = re.sub(
            r"\n\s*\n\s*\n+", "\n\n", markdown_text
        )  # Multiple newlines to double
        markdown_text = re.sub(
            r"[ \t]+", " ", markdown_text
        )  # Multiple spaces to single
        markdown_text = re.sub(
            r"\n\s+\n", "\n\n", markdown_text
        )  # Lines with only whitespace

        # Remove any remaining empty lines at start/end
        markdown_text = markdown_text.strip()

        return {"text": markdown_text, "title": title}

    async def fetch_docs(
        self, url: str, source_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch documentation from a URL with domain security checks.

        Args:
            url: The URL to fetch
            source_names: Optional list of source names to check against their allowed domains.
                         If None, checks against all sources.
        """
        # Determine which sources to check
        sources_to_check = []
        if source_names:
            for name in source_names:
                if name in self.sources:
                    sources_to_check.append(self.sources[name])
        else:
            sources_to_check = list(self.sources.values())

        # Check if URL is allowed by any source
        allowed = False
        matching_sources = []

        for source in sources_to_check:
            if self._is_domain_allowed(url, source.allowed_domains):
                allowed = True
                matching_sources.append(source.name)

        if not allowed:
            return {
                "url": url,
                "error": "Domain not allowed. URL must be from one of the allowed domains from configured sources.",
                "available_sources": [s.name for s in sources_to_check],
                "allowed_domains": [
                    domain for s in sources_to_check for domain in s.allowed_domains
                ],
            }

        try:
            fetched = await self._fetch_content(url)
            content = fetched.get("text", "")
            content_type = fetched.get("content_type", "")

            is_html = "text/html" in content_type.lower() or "<html" in content.lower()

            if is_html:
                parsed = self._html_to_markdown(content)
                cleaned_content = parsed.get("text", "")
                title = parsed.get("title")
            else:
                # Plain text (e.g., llms.txt) – normalize lightly
                cleaned_content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)
                title = None

            return {
                "url": url,
                "title": title,
                "content": cleaned_content,
                "content_type": content_type,
                "matching_sources": matching_sources,
                "success": True,
            }

        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "matching_sources": matching_sources,
                "success": False,
            }


# Global manager instance
documentation_manager = DocumentationManager()


def list_doc_sources() -> List[Dict[str, Any]]:
    """List all available documentation sources with their llms.txt URLs."""
    return documentation_manager.list_sources()


async def fetch_documentation(
    url: str, source_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Fetch documentation from a URL with domain security validation.

    Args:
        url: The documentation URL to fetch
        source_names: Optional list of source names to restrict domain checking

    Returns:
        Dict containing the fetched content or error information
    """
    return await documentation_manager.fetch_docs(url, source_names)
