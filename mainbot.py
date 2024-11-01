import json
import os
import time
from datetime import datetime
import git
import schedule
import discord
from discord.ext import tasks, commands
import asyncio

# Constants
REPO_URL = 'https://github.com/cvrve/Summer2025-Internships'
LOCAL_REPO_PATH = 'Summer2025-Internships'
JSON_FILE_PATH = os.path.join(LOCAL_REPO_PATH, '.github', 'scripts', 'listings.json')
DISCORD_TOKEN = '' #! Your Discord token
CHANNEL_IDS = '' #! Your channel IDs
MAX_RETRIES = 3  # Maximum number of retries for failed channels

# Initialize Discord bot and global variables
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
failed_channels = set()  # Keep track of channels that have failed
channel_failure_counts = {}  # Track failure counts for each channel

def clone_or_update_repo():
    """
    The function `clone_or_update_repo` clones a repository if it doesn't exist locally or updates it if
    it already exists.
    """
    print("Cloning or updating repository...")
    if os.path.exists(LOCAL_REPO_PATH):
        try:
            repo = git.Repo(LOCAL_REPO_PATH)
            repo.remotes.origin.pull()
            print("Repository updated.")
        except git.exc.InvalidGitRepositoryError:
            os.rmdir(LOCAL_REPO_PATH)  # Remove invalid directory
            git.Repo.clone_from(REPO_URL, LOCAL_REPO_PATH)
            print("Repository cloned fresh.")
    else:
        git.Repo.clone_from(REPO_URL, LOCAL_REPO_PATH)
        print("Repository cloned fresh.")

def read_json():
    """
    The function `read_json()` reads a JSON file and returns the loaded data.
    :return: The function `read_json` is returning the data loaded from the JSON file.
    """
    print(f"Reading JSON file from {JSON_FILE_PATH}...")
    with open(JSON_FILE_PATH, 'r') as file:
        data = json.load(file)
    print(f"JSON file read successfully, {len(data)} items loaded.")
    return data

# Function to format the message
def format_message(role):
    """
    The `format_message` function generates a formatted message for a new internship posting, including
    details such as company name, role title, location, season, sponsorship, and posting date.
    
    :param role: The role dictionary containing internship information
    :return: A formatted message string for Discord
    """
    cvrve = 'cvrve'
    location_str = ', '.join(role['locations']) if role['locations'] else 'Not specified'
    return f"""
>>> # {role['company_name']} just posted a new internship!

### Role:
[{role['title']}]({role['url']})

### Location:
{location_str}

### Season:
{role['season']}

### Sponsorship: `{role['sponsorship']}`
### Posted on: {datetime.now().strftime('%B, %d')}
made by the team @ [{cvrve}](https://www.cvrve.me/)
"""

def format_deactivation_message(role):
    """
    The function `format_deactivation_message` generates a message indicating that a specific internship
    role is no longer active.
    
    :param role: The role dictionary containing internship information
    :return: A formatted deactivation message string for Discord
    """
    cvrve = 'cvrve'
    return f"""
>>> # {role['company_name']} internship is no longer active

### Role:
[{role['title']}]({role['url']})

### Status: `Inactive`
### Deactivated on: {datetime.now().strftime('%B, %d')}
made by the team @ [{cvrve}](https://www.cvrve.me/)
"""

def compare_roles(old_role, new_role):
    """
    The function `compare_roles` compares two dictionaries representing roles and returns a list of
    changes between them.
    
    :param old_role: The original role dictionary
    :param new_role: The updated role dictionary
    :return: List of changes between the roles
    """
    changes = []
    for key in new_role:
        if old_role.get(key) != new_role.get(key):
            changes.append(f"{key} changed from {old_role.get(key)} to {new_role.get(key)}")
    return changes

async def send_message(message, channel_id):
    """
    The function sends a message to a Discord channel with error handling and retry mechanism.
    
    :param message: The message content to send
    :param channel_id: The Discord channel ID
    :return: None
    """
    if channel_id in failed_channels:
        print(f"Skipping previously failed channel ID {channel_id}")
        return

    try:
        print(f"Sending message to channel ID {channel_id}...")
        channel = bot.get_channel(int(channel_id))
        
        if channel is None:
            print(f"Channel {channel_id} not in cache, attempting to fetch...")
            try:
                channel = await bot.fetch_channel(int(channel_id))
            except discord.NotFound:
                print(f"Channel {channel_id} not found")
                channel_failure_counts[channel_id] = channel_failure_counts.get(channel_id, 0) + 1
                if channel_failure_counts[channel_id] >= MAX_RETRIES:
                    failed_channels.add(channel_id)
                return
            except discord.Forbidden:
                print(f"No permission for channel {channel_id}")
                failed_channels.add(channel_id)  # Immediate blacklist on permission issues
                return
            except Exception as e:
                print(f"Error fetching channel {channel_id}: {e}")
                channel_failure_counts[channel_id] = channel_failure_counts.get(channel_id, 0) + 1
                if channel_failure_counts[channel_id] >= MAX_RETRIES:
                    failed_channels.add(channel_id)
                return

        await channel.send(message)
        print(f"Successfully sent message to channel {channel_id}")
        
        # Reset failure count on success
        if channel_id in channel_failure_counts:
            del channel_failure_counts[channel_id]
        
        await asyncio.sleep(2)  # Rate limiting delay
        
    except Exception as e:
        print(f"Error sending message to channel {channel_id}: {e}")
        channel_failure_counts[channel_id] = channel_failure_counts.get(channel_id, 0) + 1
        if channel_failure_counts[channel_id] >= MAX_RETRIES:
            print(f"Channel {channel_id} has failed {MAX_RETRIES} times, adding to failed channels")
            failed_channels.add(channel_id)

async def send_messages_to_channels(message):
    """
    Sends a message to multiple Discord channels concurrently with error handling.
    
    :param message: The message content to send
    :return: None
    """
    tasks = []
    for channel_id in CHANNEL_IDS:
        if channel_id not in failed_channels:
            tasks.append(send_message(message, channel_id))
    
    # Wait for all messages to be sent
    await asyncio.gather(*tasks, return_exceptions=True)

def check_for_new_roles():
    """
    The function checks for new roles and deactivated roles, sending appropriate messages to Discord channels.
    """
    print("Checking for new roles...")
    clone_or_update_repo()
    
    new_data = read_json()
    
    # Compare with previous data if exists
    if os.path.exists('previous_data.json'):
        with open('previous_data.json', 'r') as file:
            old_data = json.load(file)
        print("Previous data loaded.")
    else:
        old_data = []
        print("No previous data found.")

    new_roles = []
    deactivated_roles = []

    # Create a dictionary for quick lookup of old roles
    old_roles_dict = {(role['title'], role['company_name']): role for role in old_data}

    for new_role in new_data:
        old_role = old_roles_dict.get((new_role['title'], new_role['company_name']))
        
        if old_role:
            # Check if the role was previously active and is now inactive
            if old_role['active'] and not new_role['active']:
                deactivated_roles.append(new_role)
                print(f"Role {new_role['title']} at {new_role['company_name']} is now inactive.")
        elif new_role['is_visible'] and new_role['active']:
            new_roles.append(new_role)
            print(f"New role found: {new_role['title']} at {new_role['company_name']}")

    # Handle new roles
    for role in new_roles:
        message = format_message(role)
        bot.loop.create_task(send_messages_to_channels(message))

    # Handle deactivated roles
    for role in deactivated_roles:
        message = format_deactivation_message(role)
        bot.loop.create_task(send_messages_to_channels(message))

    # Update previous data
    with open('previous_data.json', 'w') as file:
        json.dump(new_data, file)
    print("Updated previous data with new data.")

    if not new_roles and not deactivated_roles:
        print("No updates found.")

@bot.event
async def on_ready():
    """
    Event handler for when the bot is ready and connected to Discord.
    """
    print(f'Logged in as {bot.user}')
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

# Schedule the job
schedule.every(1).minutes.do(check_for_new_roles)

# Run the bot
print("Starting bot...")
if DISCORD_TOKEN != '' and CHANNEL_IDS != '':
    bot.run(DISCORD_TOKEN)
elif DISCORD_TOKEN == '' and CHANNEL_IDS == '':
    print("Please provide your Discord token and channel IDs.")
elif CHANNEL_IDS == '':
    print("Please provide your channel IDs.")
elif DISCORD_TOKEN == '':
    print("Please provide your Discord token.")
else:
    print("An unknown error occurred.")