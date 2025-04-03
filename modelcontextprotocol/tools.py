import logging

from client import create_atlan_client
from config import Settings

logger = logging.getLogger(__name__)
settings = Settings()
atlan_client = create_atlan_client(settings)
