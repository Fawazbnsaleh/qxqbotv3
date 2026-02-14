import pytest
import aiosqlite
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from al_rased.core import database
from al_rased.services.telethon_monitor.monitor import TelethonMonitor
from telethon.tl.types import Chat, Channel

@pytest.fixture
async def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    with patch("al_rased.core.database.DB_PATH", db_path):
        await database.init_db()
        yield

@pytest.mark.asyncio
async def test_system_flags(test_db):
    """Test setting and retrieving system flags (Action Modes)."""
    # Default is None -> logic usually handles default as 'publish'
    assert await database.get_system_flag("action_mode:test_cat") is None
    
    await database.set_system_flag("action_mode:test_cat", "stop")
    assert await database.get_system_flag("action_mode:test_cat") == "stop"
    
    await database.set_system_flag("action_mode:test_cat", "publish")
    assert await database.get_system_flag("action_mode:test_cat") == "publish"

@pytest.mark.asyncio
async def test_bulk_retrieval(test_db):
    """Test bulk retrieval functions for caching."""
    # 1. Banned Names
    await database.add_banned_name("cat1", "bad1")
    await database.add_banned_name("cat1", "bad2")
    await database.add_banned_name("cat2", "bad3")
    
    mapping = await database.get_all_banned_names_mapping()
    assert "cat1" in mapping
    assert "bad1" in mapping["cat1"]
    assert "bad2" in mapping["cat1"]
    assert "cat2" in mapping
    assert "bad3" in mapping["cat2"]
    
    # 2. System Flags
    await database.set_system_flag("action_mode:cat1", "stop")
    await database.set_system_flag("action_mode:cat2", "publish")
    
    flags = await database.get_all_system_flags_mapping()
    assert flags["action_mode:cat1"] == "stop"
    assert flags["action_mode:cat2"] == "publish"

@pytest.mark.asyncio
async def test_monitor_detection_logic(test_db):
    """Test the core detection loop in TelethonMonitor (isolated)."""
    
    # Setup Data
    await database.add_banned_name("fraud", "scammer")
    await database.set_system_flag("action_mode:fraud", "stop")
    
    # Mock Telethon Client and Event
    mock_client = AsyncMock()
    monitor = TelethonMonitor()
    monitor.client = mock_client
    
    # Mock Event
    event = AsyncMock()
    event.message.text = "Hello from a regular user"
    event.chat_id = 123
    event.message.id = 999
    
    # Sender with forbidden name
    sender = MagicMock()
    sender.first_name = "Mr Scammer"
    sender.last_name = "Smith"
    sender.username = "mrscam"
    sender.id = 456
    sender.bot = False
    
    event.get_sender.return_value = sender
    
    # Needs to pass isinstance(chat, (Channel, Chat))
    chat = MagicMock(spec=Chat)
    chat.title = "Test Group"
    event.get_chat.return_value = chat
    
    # Mock Admin Check (Not admin)
    monitor._is_admin_or_bot = AsyncMock(return_value=(False, False))
    
    # Mock DetectionEngine (to avoid loading real model)
    with patch("al_rased.services.telethon_monitor.monitor.DetectionEngine.predict") as mock_predict:
        mock_predict.return_value = {"label": "Normal", "confidence": 0.0}
        
        # Run processing
        await monitor._process_message(event)
        
        # Verification
        # 1. Should detect "scammer" in "Mr Scammer" -> Fraud
        # 2. Fraud mode is "stop" -> Should delete message
        
        # Verify stats
        assert monitor.stats["violations"] == 1
        
        # Verify delete called
        event.delete.assert_called_once()
        
        # Verify ban called (Permissions edit)
        monitor.client.edit_permissions.assert_called_once()

@pytest.mark.asyncio
async def test_monitor_ml_detection_logic(test_db):
    """Test ML detection logic (Publish mode)."""
    
    # Setup Data
    await database.set_system_flag("action_mode:spam", "publish")
    
    # Mock Telethon Client and Event
    mock_client = AsyncMock()
    monitor = TelethonMonitor()
    monitor.client = mock_client
    
    # Sender with clean name
    sender = MagicMock()
    sender.first_name = "Good User"
    sender.id = 789
    sender.bot = False
    
    event = AsyncMock()
    event.message.text = "Buy cheap meds now!"
    event.message.id = 1001
    event.chat_id = 123
    
    chat = MagicMock(spec=Chat)
    chat.title = "Test Group"
    event.get_chat.return_value = chat
    
    event.get_sender.return_value = sender
    monitor._is_admin_or_bot = AsyncMock(return_value=(False, False))

    with patch("al_rased.services.telethon_monitor.monitor.DetectionEngine.predict") as mock_predict:
        # Mock ML violation
        mock_predict.return_value = {"label": "Spam", "confidence": 0.95}
        
        await monitor._process_message(event)
        
        # Verification
        assert monitor.stats["violations"] == 1
        
        # Publish mode -> Should NOT delete
        event.delete.assert_not_called()
        monitor.client.edit_permissions.assert_not_called()
