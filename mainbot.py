#!/usr/bin/env/python3

from dataclasses import dataclass
from datetime import datetime
from typing import (
    Dict,
    List,
    Optional,
    Set,
    # Tuple,
    Any,
)
import asyncio
import json
import os
from pathlib import Path

import discord
from discord.ext import commands, tasks
import git

# import schedule
from discord.abc import Messageable
from discord.channel import TextChannel


@dataclass
class InternshipRole:
    """Data class representing an internship role."""

    title: str
    company_name: str
    locations: List[str]
    url: str
    season: str
    sponsorship: str
    active: bool
    is_visible: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InternshipRole":
        """Create an InternshipRole instance from a dictionary."""
        return cls(
            title=data["title"],
            company_name=data["company_name"],
            locations=data["locations"],
            url=data["url"],
            season=data["season"],
            sponsorship=data["sponsorship"],
            active=data["active"],
            is_visible=data["is_visible"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the InternshipRole instance to a dictionary."""
        return {
            "title": self.title,
            "company_name": self.company_name,
            "locations": self.locations,
            "url": self.url,
            "season": self.season,
            "sponsorship": self.sponsorship,
            "active": self.active,
            "is_visible": self.is_visible,
        }


class GitManager:
    """Manages Git repository operations."""

    def __init__(self, repo_url: str, local_path: str):
        self.repo_url = repo_url
        self.local_path = Path(local_path)

    def clone_or_update(self) -> None:
        """Clone or update the repository."""
        print("Cloning or updating repository...")
        if self.local_path.exists():
            try:
                repo = git.Repo(self.local_path)
                repo.remotes.origin.pull()
                print("Repository updated.")
            except git.exc.InvalidGitRepositoryError:
                self.local_path.rmdir()
                git.Repo.clone_from(self.repo_url, self.local_path)
                print("Repository cloned fresh.")
        else:
            git.Repo.clone_from(self.repo_url, self.local_path)
            print("Repository cloned fresh.")


class MessageFormatter:
    """Handles formatting of Discord messages."""

    @staticmethod
    def format_new_role(role: InternshipRole) -> str:
        """Format a message for a new internship posting."""
        location_str = ", ".join(role.locations) if role.locations else "Not specified"
        return f"""
>>> # {role.company_name} just posted a new internship!

### Role:
[{role.title}]({role.url})

### Location:
{location_str}

### Season:
{role.season}

### Sponsorship: `{role.sponsorship}`
### Posted on: {datetime.now().strftime('%B, %d')}
made by the team @ [cvrve](https://www.cvrve.me/)
"""

    @staticmethod
    def format_deactivation(role: InternshipRole) -> str:
        """Format a message for a deactivated internship role."""
        return f"""
>>> # {role.company_name} internship is no longer active

### Role:
[{role.title}]({role.url})

### Status: `Inactive`
### Deactivated on: {datetime.now().strftime('%B, %d')}
made by the team @ [cvrve](https://www.cvrve.me/)
"""


class InternshipBot(commands.Bot):
    """Main Discord bot class for handling internship notifications."""

    def __init__(
        self,
        repo_url: str,
        local_repo_path: str,
        json_file_path: str,
        channel_ids: List[str],
        command_prefix: str = "!",
        max_retries: int = 3,
    ):
        intents = discord.Intents.default()
        super().__init__(command_prefix=command_prefix, intents=intents)

        self.git_manager = GitManager(repo_url, local_repo_path)
        self.json_file_path = Path(json_file_path)
        self.channel_ids = channel_ids
        self.max_retries = max_retries

        self.failed_channels: Set[str] = set()
        self.channel_failure_counts: Dict[str, int] = {}
        self.formatter = MessageFormatter()

    async def setup_hook(self) -> None:
        """Set up the bot's background tasks."""
        self.check_roles.start()

    def read_json(self) -> List[InternshipRole]:
        """Read and parse the JSON file containing internship data."""
        print(f"Reading JSON file from {self.json_file_path}...")
        with open(self.json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        roles = [InternshipRole.from_dict(role_data) for role_data in data]
        print(f"JSON file read successfully, {len(roles)} items loaded.")
        return roles

    async def send_message(self, message: str, channel_id: str) -> None:
        """Send a message to a specific Discord channel with error handling."""
        if channel_id in self.failed_channels:
            print(f"Skipping previously failed channel ID {channel_id}")
            return

        try:
            channel: Optional[Messageable] = self.get_channel(int(channel_id))

            if channel is None:
                print(f"Channel {channel_id} not in cache, attempting to fetch...")
                try:
                    channel = await self.fetch_channel(int(channel_id))
                except discord.NotFound:
                    self._handle_channel_failure(channel_id, "Channel not found")
                    return
                except discord.Forbidden:
                    self.failed_channels.add(channel_id)
                    print(f"No permission for channel {channel_id}")
                    return

            if isinstance(channel, TextChannel):
                await channel.send(message)
                print(f"Successfully sent message to channel {channel_id}")
                self.channel_failure_counts.pop(channel_id, None)
                await asyncio.sleep(2)  # Rate limiting delay
            else:
                print(f"Channel {channel_id} is not a text channel")
                self.failed_channels.add(channel_id)

        except (
            discord.HTTPException,
            discord.InvalidArgument,
            discord.Forbidden,
            discord.NotFound,
        ) as e:
            self._handle_channel_failure(channel_id, str(e))

    def _handle_channel_failure(self, channel_id: str, error: str) -> None:
        """Handle channel failures and track retry attempts."""
        print(f"Error with channel {channel_id}: {error}")
        self.channel_failure_counts[channel_id] = (
            self.channel_failure_counts.get(channel_id, 0) + 1
        )
        if self.channel_failure_counts[channel_id] >= self.max_retries:
            print(
                f"Channel {channel_id} has failed {self.max_retries} times, blacklisting"
            )
            self.failed_channels.add(channel_id)

    async def send_messages_to_channels(self, message: str) -> None:
        """Send a message to all configured channels concurrently."""
        send_tasks = [
            self.send_message(message, channel_id)
            for channel_id in self.channel_ids
            if channel_id not in self.failed_channels
        ]
        await asyncio.gather(*send_tasks, return_exceptions=True)

    @tasks.loop(minutes=1)
    async def check_roles(self) -> None:
        """Check for new and deactivated roles periodically."""
        print("Checking for new roles...")
        self.git_manager.clone_or_update()

        new_data = self.read_json()
        previous_data_path = Path("previous_data.json")

        if previous_data_path.exists():
            with open(previous_data_path, "r", encoding="utf-8") as file:
                old_data = [
                    InternshipRole.from_dict(role_data) for role_data in json.load(file)
                ]
            print("Previous data loaded.")
        else:
            old_data = []
            print("No previous data found.")

        new_roles: List[InternshipRole] = []
        deactivated_roles: List[InternshipRole] = []

        old_roles_dict = {(role.title, role.company_name): role for role in old_data}

        for new_role in new_data:
            key = (new_role.title, new_role.company_name)
            old_role = old_roles_dict.get(key)

            if old_role:
                if old_role.active and not new_role.active:
                    deactivated_roles.append(new_role)
                    print(
                        f"Role {new_role.title} at {new_role.company_name} is now inactive."
                    )
            elif new_role.is_visible and new_role.active:
                new_roles.append(new_role)
                print(f"New role found: {new_role.title} at {new_role.company_name}")

        # Handle new roles
        for role in new_roles:
            message = self.formatter.format_new_role(role)
            await self.send_messages_to_channels(message)

        # Handle deactivated roles
        for role in deactivated_roles:
            message = self.formatter.format_deactivation(role)
            await self.send_messages_to_channels(message)

        # Update previous data
        with open(previous_data_path, "w", encoding="utf-8") as file:
            json.dump([role.to_dict() for role in new_data], file)
        print("Updated previous data with new data.")

        if not new_roles and not deactivated_roles:
            print("No updates found.")

    @check_roles.before_loop
    async def before_check_roles(self) -> None:
        """Wait for the bot to be ready before starting the check_roles loop."""
        await self.wait_until_ready()


def main() -> None:
    """Main entry point for the bot."""
    # Configuration
    REPO_URL = "https://github.com/cvrve/Summer2025-Internships"
    LOCAL_REPO_PATH = "Summer2025-Internships"
    JSON_FILE_PATH = os.path.join(
        LOCAL_REPO_PATH, ".github", "scripts", "listings.json"
    )
    DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
    CHANNEL_IDS = os.environ.get("CHANNEL_IDS", "").split(",")

    if not DISCORD_TOKEN or not CHANNEL_IDS:
        print("Please provide Discord token and channel IDs via environment variables.")
        return

    bot = InternshipBot(
        repo_url=REPO_URL,
        local_repo_path=LOCAL_REPO_PATH,
        json_file_path=JSON_FILE_PATH,
        channel_ids=CHANNEL_IDS,
    )

    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
