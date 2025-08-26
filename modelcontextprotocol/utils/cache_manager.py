"""
Advanced cache management using singleton pattern for persistent caching across MCP tool calls.

This module provides a thread-safe singleton cache manager that can be used as an alternative
to the module-level caching approach. It offers more control and flexibility for cache management.
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SingletonCacheManager(Generic[T]):
    """
    Thread-safe singleton cache manager for persistent data caching across MCP tool calls.
    
    This class ensures that cache data persists across multiple tool calls within the same
    MCP server process.
    """
    
    # Private class variables to store instances and lock
    _instances: Dict[str, 'SingletonCacheManager'] = {}
    _lock = threading.Lock()
    
    # Create or return existing singleton instance for the given cache name
    def __new__(cls, cache_name: str, ttl_seconds: float = 300.0):
        """
        Create or return existing singleton instance for the given cache name.
        
        Args:
            cache_name: Unique identifier for this cache instance
            ttl_seconds: Time-to-live for cached data in seconds
        """
        # Lock to ensure thread-safe access to instances
        with cls._lock:
            if cache_name not in cls._instances:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instances[cache_name] = instance
            return cls._instances[cache_name]
    
    def __init__(self, cache_name: str, ttl_seconds: float = 300.0):
        """
        Initialize the cache manager (only runs once per cache_name).
        
        Args:
            cache_name: Unique identifier for this cache instance
            ttl_seconds: Time-to-live for cached data in seconds
        """
        if self._initialized:
            return
            
        self.cache_name = cache_name
        self.ttl_seconds = ttl_seconds
        self._cache_data: Optional[T] = None
        self._cache_timestamp: Optional[float] = None
        self._data_lock = threading.Lock()
        self._initialized = True
        
        logger.debug(f"Initialized singleton cache manager: {cache_name} (TTL: {ttl_seconds}s)")
    
    def get_or_fetch(self, fetch_function: Callable[[], T]) -> T:
        """
        Get cached data or fetch fresh data if cache is invalid.
        
        Args:
            fetch_function: Function to call to fetch fresh data when cache is invalid
            
        Returns:
            Cached or freshly fetched data
        """
        with self._data_lock:
            current_time = time.time()
            
            # Check if cache is valid
            if self._is_cache_valid(current_time):
                logger.debug(f"Using cached data from {self.cache_name}")
                return self._cache_data
            
            # Fetch fresh data
            logger.debug(f"Fetching fresh data for {self.cache_name}")
            try:
                fresh_data = fetch_function()
                self._cache_data = fresh_data
                self._cache_timestamp = current_time
                logger.info(f"Updated cache {self.cache_name} with fresh data")
                return fresh_data
            except Exception as e:
                logger.error(f"Failed to fetch fresh data for {self.cache_name}: {e}")
                # Return stale cache if available
                if self._cache_data is not None:
                    logger.warning(f"Returning stale cached data for {self.cache_name}")
                    return self._cache_data
                raise
    
    def _is_cache_valid(self, current_time: float) -> bool:
        """Check if the current cache is valid based on TTL."""
        return (self._cache_data is not None and 
                self._cache_timestamp is not None and 
                (current_time - self._cache_timestamp) < self.ttl_seconds)
    
    def invalidate(self) -> None:
        """Clear the cached data, forcing a fresh fetch on next access."""
        with self._data_lock:
            self._cache_data = None
            self._cache_timestamp = None
            logger.info(f"Invalidated cache: {self.cache_name}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the current cache state.
        
        Returns:
            Dict containing cache metadata
        """
        with self._data_lock:
            current_time = time.time()
            cache_size = len(self._cache_data) if isinstance(self._cache_data, (list, dict, str)) else 1 if self._cache_data else 0
            
            return {
                "cache_name": self.cache_name,
                "cache_size": cache_size,
                "cache_timestamp": self._cache_timestamp,
                "current_time": current_time,
                "ttl_seconds": self.ttl_seconds,
                "is_valid": self._is_cache_valid(current_time),
                "age_seconds": current_time - self._cache_timestamp if self._cache_timestamp else None
            }
    
    @classmethod
    def get_all_cache_info(cls) -> Dict[str, Dict[str, Any]]:
        """Get information about all active cache instances."""
        with cls._lock:
            return {name: instance.get_cache_info() for name, instance in cls._instances.items()}
    
    @classmethod
    def invalidate_all(cls) -> None:
        """Invalidate all cache instances."""
        with cls._lock:
            for instance in cls._instances.values():
                instance.invalidate()
            logger.info("Invalidated all cache instances")


# Convenience function for custom metadata caching
def get_custom_metadata_cache_manager() -> SingletonCacheManager[List[Dict[str, Any]]]:
    """
    Get the singleton cache manager for custom metadata context.
    
    Returns:
        Singleton cache manager instance for custom metadata
    """
    return SingletonCacheManager[List[Dict[str, Any]]]("custom_metadata_context", ttl_seconds=900.0)
