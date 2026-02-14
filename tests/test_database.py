import pytest
import aiosqlite
from pathlib import Path
from unittest.mock import patch
from al_rased.core import database

@pytest.fixture
async def test_db(tmp_path):
    # Use a temporary file instead of :memory: so connections persist data
    db_path = tmp_path / "test.db"
    
    # Patch the DB_PATH in the module
    with patch("al_rased.core.database.DB_PATH", db_path):
        # Initialize schema
        await database.init_db()
        yield

@pytest.mark.asyncio
async def test_group_management(test_db):
    """Test setting and retrieving group IDs."""
    await database.set_group("review", 12345)
    await database.set_group("training", 67890)
    
    review_group = await database.get_group("review")
    training_group = await database.get_group("training")
    
    assert review_group == 12345
    assert training_group == 67890

@pytest.mark.asyncio
async def test_category_settings(test_db):
    """Test enabling/disabling detection categories."""
    category = "medical_fraud"
    
    # Default should be enabled
    assert await database.get_category_status(category) is True
    
    await database.set_category_status(category, False)
    assert await database.get_category_status(category) is False
    
    await database.set_category_status(category, True)
    assert await database.get_category_status(category) is True

@pytest.mark.asyncio
async def test_banned_names(test_db):
    """Test adding and removing banned names."""
    category = "scam"
    name = "bad_bot"
    
    assert await database.get_banned_names_count(category) == 0
    
    await database.add_banned_name(category, name)
    assert await database.get_banned_names_count(category) == 1
    assert name in await database.get_banned_names(category)
    
    await database.remove_banned_name(category, name)
    assert await database.get_banned_names_count(category) == 0

@pytest.mark.asyncio
async def test_bot_settings(test_db):
    """Test key-value bot settings."""
    await database.set_bot_setting("version", "1.0")
    assert await database.get_bot_setting("version") == "1.0"
    
    await database.set_bot_setting("version", "2.0")
    assert await database.get_bot_setting("version") == "2.0"
    
    # Test default
    assert await database.get_bot_setting("unknown", "default") == "default"
