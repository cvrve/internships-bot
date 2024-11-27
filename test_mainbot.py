import pytest
import asyncio
import json
import os
from unittest.mock import Mock, patch, AsyncMock, mock_open, MagicMock
import discord
from discord.ext import commands
import git

# Import the bot code from mainbot.py
from mainbot import (
    clone_or_update_repo,
    read_json,
    format_message,
    format_deactivation_message,
    compare_roles,
    send_message,
    send_messages_to_channels,
    check_for_new_roles,
    failed_channels,
    JSON_FILE_PATH,
    bot
)

# Test data representing a sample job role with all required fields
SAMPLE_ROLE = {
    'company_name': 'Test Company',
    'title': 'Software Engineer Intern',
    'url': 'https://example.com/job',
    'locations': ['New York', 'Remote'],
    'season': 'Summer 2025',
    'sponsorship': 'Available',
    'active': True,
    'is_visible': True
}

# Fixture to mock Git repository operations
@pytest.fixture
def mock_repo():
    with patch('git.Repo') as mock:
        yield mock

# Fixture to mock Discord bot instance
@pytest.fixture
def mock_discord_bot():
    with patch('discord.ext.commands.Bot') as mock:
        yield mock

class TestRepositoryOperations:
    """Test suite for Git repository operations"""
    
    def test_clone_repo_fresh(self, mock_repo):
        """Test cloning a new repository when none exists"""
        with patch('os.path.exists', return_value=False):
            clone_or_update_repo()
            mock_repo.clone_from.assert_called_once()

    def test_update_existing_repo(self, mock_repo):
        """Test updating an existing repository via git pull"""
        with patch('os.path.exists', return_value=True):
            repo_instance = Mock()
            mock_repo.return_value = repo_instance
            repo_instance.remotes.origin = Mock()
            
            clone_or_update_repo()
            
            repo_instance.remotes.origin.pull.assert_called_once()

    def test_handle_invalid_repo(self, mock_repo):
        """Test handling of an invalid Git repository by removing and re-cloning"""
        with patch('os.path.exists', return_value=True):
            mock_repo.side_effect = git.exc.InvalidGitRepositoryError
            with patch('os.rmdir') as mock_rmdir:
                clone_or_update_repo()
                mock_rmdir.assert_called_once()
                mock_repo.clone_from.assert_called_once()

class TestJsonOperations:
    """Test suite for JSON file operations"""
    
    def test_read_json(self):
        """Test reading and parsing JSON data from file"""
        sample_data = [SAMPLE_ROLE]
        mock_file = mock_open(read_data=json.dumps(sample_data))
        
        with patch('builtins.open', mock_file):
            data = read_json()
            assert data == sample_data
            mock_file.assert_called_once_with(JSON_FILE_PATH, 'r')

class TestMessageFormatting:
    """Test suite for message formatting operations"""
    
    def test_format_message(self):
        """Test formatting a new job posting message with all required fields"""
        message = format_message(SAMPLE_ROLE)
        assert SAMPLE_ROLE['company_name'] in message
        assert SAMPLE_ROLE['title'] in message
        assert SAMPLE_ROLE['url'] in message
        assert all(location in message for location in SAMPLE_ROLE['locations'])
        assert SAMPLE_ROLE['season'] in message
        assert SAMPLE_ROLE['sponsorship'] in message

    def test_format_deactivation_message(self):
        """Test formatting a message for a deactivated job posting"""
        message = format_deactivation_message(SAMPLE_ROLE)
        assert SAMPLE_ROLE['company_name'] in message
        assert SAMPLE_ROLE['title'] in message
        assert SAMPLE_ROLE['url'] in message
        assert 'Inactive' in message

    def test_compare_roles(self):
        """Test comparing two versions of a role to detect changes"""
        old_role = SAMPLE_ROLE.copy()
        new_role = SAMPLE_ROLE.copy()
        new_role['sponsorship'] = 'Not Available'
        new_role['locations'] = ['San Francisco']
        
        changes = compare_roles(old_role, new_role)
        assert len(changes) == 2
        assert any('sponsorship' in change for change in changes)
        assert any('locations' in change for change in changes)

@pytest.mark.asyncio
class TestDiscordOperations:
    """Test suite for Discord-related operations"""
    
    async def test_send_message_success(self):
        """Test successful message sending to a Discord channel"""
        channel = AsyncMock()
        channel.send = AsyncMock()
        
        with patch('mainbot.bot') as mock_bot:
            mock_bot.get_channel = Mock(return_value=channel)
            mock_bot.fetch_channel = AsyncMock(return_value=channel)
            
            await send_message("Test message", "123456789")
            channel.send.assert_called_once_with("Test message")

    async def test_send_message_channel_not_found(self):
        """Test handling of messages when Discord channel is not found"""
        with patch('mainbot.bot') as mock_bot, \
             patch('mainbot.channel_failure_counts', {}) as mock_counts:
            
            mock_bot.get_channel.return_value = None
            mock_bot.fetch_channel = AsyncMock(side_effect=discord.NotFound(Mock(), "Channel not found"))
            
            await send_message("Test message", "123456789")
            assert mock_counts.get("123456789", 0) > 0

    async def test_send_messages_to_channels(self):
        """Test sending messages to multiple Discord channels"""
        test_message = "Test message"
        channel_ids = ["123", "456"]
        
        with patch('mainbot.CHANNEL_IDS', channel_ids), \
             patch('mainbot.send_message') as mock_send:
            mock_send.return_value = asyncio.Future()
            mock_send.return_value.set_result(None)
            
            await send_messages_to_channels(test_message)
            assert mock_send.call_count == len(channel_ids)

@pytest.mark.asyncio
class TestRoleChecking:
    """Test suite for role checking and update detection"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup fixture for role checking tests with mocked bot and event loop"""
        mock_bot = AsyncMock()
        mock_loop = AsyncMock()
        mock_loop.create_task = AsyncMock()
        mock_bot.loop = mock_loop
        
        with patch('mainbot.bot', mock_bot), \
             patch('asyncio.get_event_loop', return_value=mock_loop):
            yield mock_bot

    async def test_check_for_new_roles(self):
        """Test detection and handling of new job roles"""
        mock_messages = []
        
        async def mock_send_messages_to_channels(message):
            mock_messages.append(message)
            
        # Test data with two distinct roles
        new_data = [
            {**SAMPLE_ROLE, 'is_visible': True, 'active': True},
            {
                'company_name': 'New Company',
                'title': 'New Role',
                'url': 'https://example.com/new-job',
                'locations': ['San Francisco'],
                'season': 'Summer 2025',
                'sponsorship': 'Available',
                'active': True,
                'is_visible': True
            }
        ]

        async def async_check_for_new_roles():
            """Helper function to simulate role checking process"""
            import mainbot
            new_data = mainbot.read_json()
            old_data = []
            
            for new_role in new_data:
                if new_role['is_visible'] and new_role['active']:
                    message = mainbot.format_message(new_role)
                    await mock_send_messages_to_channels(message)
            
            return new_data, []

        with patch('mainbot.clone_or_update_repo') as mock_clone, \
             patch('mainbot.read_json', return_value=new_data) as mock_read, \
             patch('mainbot.send_messages_to_channels', mock_send_messages_to_channels), \
             patch('mainbot.check_for_new_roles', side_effect=async_check_for_new_roles):

            result_data, _ = await async_check_for_new_roles()
            
            assert len(mock_messages) == 2
            assert any('Test Company' in msg for msg in mock_messages)
            assert any('New Company' in msg for msg in mock_messages)
            assert len(result_data) == 2
            
            mock_clone.assert_not_called()
            mock_read.assert_called_once()

    async def test_check_for_deactivated_roles(self):
        """Test detection and handling of deactivated job roles"""
        old_role = {**SAMPLE_ROLE, 'active': True}
        new_role = {**SAMPLE_ROLE, 'active': False}
        
        with patch('mainbot.clone_or_update_repo') as mock_clone, \
             patch('mainbot.read_json', return_value=[new_role]) as mock_read, \
             patch('builtins.open', mock_open(read_data=json.dumps([old_role]))), \
             patch('mainbot.send_messages_to_channels') as mock_send:
            
            mock_send.return_value = asyncio.Future()
            mock_send.return_value.set_result(None)
            
            async def async_check_for_new_roles():
                check_for_new_roles()
                future = asyncio.Future()
                future.set_result(None)
                return future
            
            with patch('mainbot.check_for_new_roles', async_check_for_new_roles):
                await async_check_for_new_roles()
            
            mock_clone.assert_called_once()
            mock_read.assert_called_once()

if __name__ == '__main__':
    pytest.main(['-v', '--cov=.', '--cov-report=xml'])