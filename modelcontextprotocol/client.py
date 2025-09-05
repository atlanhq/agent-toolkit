"""Client factory for Atlan."""

import logging
import threading
from typing import Tuple

from pyatlan.client.atlan import AtlanClient
from settings import Settings

logger = logging.getLogger(__name__)


class AtlanClientManager:
    """
    Minimal thread-safe client manager.
    
    Provides thread-local AtlanClient instances with automatic recreation
    when settings change. Designed for MCP's sequential usage patterns.
    """
    
    _thread_local = threading.local()
    
    @classmethod
    def get_client(cls) -> AtlanClient:
        """
        Get a thread-local AtlanClient instance.
        
        Creates a new client only when:
        - First call in this thread
        - Settings have changed since last creation
        
        Returns:
            AtlanClient: Thread-local client instance.
            
        Raises:
            Exception: Original exception if client creation fails.
        """
        settings = Settings()
        current_key = (settings.ATLAN_BASE_URL, settings.ATLAN_API_KEY, 
                      tuple(sorted(settings.headers.items())))
        
        if (not hasattr(cls._thread_local, 'client') or 
            getattr(cls._thread_local, 'settings_key', None) != current_key):
            
            try:
                logger.info(f"Creating AtlanClient for thread {threading.current_thread().name}")
                
                client = AtlanClient(
                    base_url=settings.ATLAN_BASE_URL,
                    api_key=settings.ATLAN_API_KEY
                )
                client.update_headers(settings.headers)
                
                cls._thread_local.client = client
                cls._thread_local.settings_key = current_key
                
                logger.info("AtlanClient created successfully")
                
            except Exception:
                logger.error("Failed to create Atlan client", exc_info=True)
                raise
        
        return cls._thread_local.client


def get_atlan_client() -> AtlanClient:
    """
    Get a thread-safe AtlanClient instance.
    
    Returns:
        AtlanClient: Thread-local client instance.
        
    Raises:
        Exception: Original exception if client creation fails.
    """
    return AtlanClientManager.get_client()