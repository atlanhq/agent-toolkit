import os
import json
import logging
from typing import List, Optional

from dotenv import load_dotenv
from config import Config
from pyatlan.model.group import AtlanGroup
from pyatlan.model.user import AtlanUser, UserResponse
from pyatlan.cache.atlan_tag_cache import AtlanTagCache

load_dotenv()

logger = logging.getLogger(__name__)
config = Config()


def get_user_by_username(username: str) -> Optional[AtlanUser]:
    """Get user by username"""
    logger.info("Getting user by username")
    try:
        user = config.atlan_client.user.get_by_username(username)
        if user:
            return user
        else:
            logger.error(f"User {username} not found")
            return None
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        return None


def get_user_by_email(email: str) -> Optional[List[AtlanUser]]:
    """Get user by email"""
    logger.info("Getting user by email")
    try:
        user = config.atlan_client.user.get_by_email(email)
        return user
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None


def get_group_by_name(group_name: str) -> Optional[List[AtlanGroup]]:
    """Get group by name"""
    logger.info("Getting group by name")
    try:
        group = config.atlan_client.group.get_by_name(group_name)
        if group:
            return group
        else:
            logger.error(f"Group {group_name} not found")
            return None
    except Exception as e:
        logger.error(f"Error getting group by name: {e}")
        return None


def get_users_from_group(group_name: str) -> Optional[UserResponse]:
    """Get users from group"""
    logger.info("Getting users from group")
    try:
        group = config.atlan_client.group.get_by_name(group_name)
        if group:
            members = config.atlan_client.group.get_members(group.id)
            return members
        else:
            logger.error(f"Group {group_name} not found")
            return None
    except Exception as e:
        logger.error(f"Error getting users from group: {e}")
        return None


def get_trait_names(tag_name: str) -> Optional[List[str]]:
    """Get trait names (Hash String) of a tag specific to atlan"""
    logger.info("Getting trait names of a tag")
    try:
        tag_id = AtlanTagCache.get_id_for_name(tag_name)
        if tag_id:
            return tag_id
        else:
            logger.error(f"Tag {tag_name} not found")
            return None
    except Exception as e:
        logger.error(f"Error getting trait names of a tag: {e}")
        return None

