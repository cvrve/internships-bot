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
REPO_URL = 'https://github.com/Ouckah/Summer2025-Internships'
LOCAL_REPO_PATH = 'Summer2025-Internships'
JSON_FILE_PATH = os.path.join(LOCAL_REPO_PATH, '.github', 'scripts', 'listings.json')
DISCORD_TOKEN = '' #! Your Discord token
CHANNEL_ID = '' #! Your channel ID

# Initialize Discord bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# Function to clone or update the repository
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

# Function to read JSON file
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
    
    :param role: The `format_message` function takes a dictionary `role` as input and generates a
    formatted message containing information about a job role or internship. The function uses the
    values from the `role` dictionary to fill in the template and create the message
    :return: The `format_message` function returns a formatted message containing information about a
    job role. The message includes details such as the company name, job title, job URL, locations,
    season, sponsorship, and the date the job was posted. The message also includes a footer with a
    reference to the team at cvrve.me.
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

# Function to check for new roles
def check_for_new_roles():
    """
    The function `check_for_new_roles` checks for new roles, compares them with previous data, and sends
    messages for new visible and active roles.
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

    new_roles = [role for role in new_data if role not in old_data]
    
    if new_roles:
        print(f"Found {len(new_roles)} new roles.")
        with open('previous_data.json', 'w') as file:
            json.dump(new_data, file)
        print("Updated previous data with new data.")

        for role in new_roles:
            if role['is_visible'] and role['active']:
                message = format_message(role)
                for channel_id in CHANNEL_ID:
                    bot.loop.create_task(send_message(message, channel_id))
                print(f"New role posted: {role['title']}")
    else:
        print("No new roles found.")

# Function to send message to Discord
async def send_message(message, channel_id):
    """
    The function `send_message` sends a message to a Discord channel identified by the provided channel
    ID, handling various exceptions that may occur during the process.
    
    :param message: The `message` parameter in the `send_message` function is the content of the message
    that you want to send to a Discord channel. It should be a string containing the text you want to
    send
    :param channel_id: The `channel_id` parameter is the unique identifier for the channel where you
    want to send the message. It is used to locate the specific channel within the Discord server
    :return: The function `send_message` returns different messages based on the outcome of the message
    sending process. Here are the possible return messages:
    """
    try:
        print(f"Sending message to channel ID {channel_id}...")
        channel = bot.get_channel(int(channel_id))
        if channel is None:
            print(f"Channel with ID {channel_id} not found in cache. Fetching channel...")
            try:
                channel = await bot.fetch_channel(int(channel_id))
            except discord.NotFound:
                print(f"Channel with ID {channel_id} not found.")
                return
            except discord.Forbidden:
                print(f"Bot does not have permission to access channel with ID {channel_id}.")
                return
            except discord.HTTPException as e:
                print(f"HTTP Exception while fetching channel: {e}")
                return

        await channel.send(message)
        print(f"Message sent to channel ID {channel_id}.")
    except Exception as e:
        print(f"Error sending message to channel ID {channel_id}: {e}")

# Schedule the job
schedule.every(1).minutes.do(check_for_new_roles)

@bot.event
async def on_ready():
    """
    The function prints a message when the bot is logged in and then continuously runs a schedule while
    sleeping for 1 second in between.
    """
    print(f'Logged in as {bot.user}')
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

# Run the bot
# This block of code is responsible for starting the Discord bot. It checks the conditions related to
# the Discord token and channel ID to determine how to proceed with running the bot:
print("Starting bot...")
if DISCORD_TOKEN != '' and CHANNEL_ID != '':
    bot.run(DISCORD_TOKEN)
elif DISCORD_TOKEN == '' and CHANNEL_ID == '':
    print("Please provide your Discord token and channel ID.")
elif CHANNEL_ID == '':
    print("Please provide your channel ID.")
elif DISCORD_TOKEN == '':
    print("Please provide your Discord token.")
else:
    print("An unknown error occurred.")