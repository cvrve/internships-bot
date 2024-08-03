# Repo feed from Ouckah/Summer-2025-Internships

## Overview

This project is a Discord bot designed to monitor a GitHub repository for new internship postings and send formatted messages to a specified Discord channel. The bot performs the following tasks:

1. Clones or updates the specified GitHub repository.
2. Reads a JSON file containing internship listings.
3. Compares the new listings with previously stored data.
4. Sends formatted messages to a Discord channel for any new visible and active roles.

## Setup

### Prerequisites

- Python 3.6 or higher
- Git
- Discord bot token
- Discord channel ID

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Ouckah/Summer2025-Internships.git
    cd Summer2025-Internships
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Set up your Discord bot:
    - Create a new bot on the [Discord Developer Portal](https://discord.com/developers/applications).
    - Copy the bot token and paste it into the `DISCORD_TOKEN` variable in `mainbot.py`.
    - Get the channel ID where you want the bot to send messages and paste it into the `CHANNEL_ID` variable in `mainbot.py`.

## Usage

1. Run the bot:
    ```sh
    python mainbot.py
    ```

2. The bot will start and perform the following actions:
    - Clone or update the GitHub repository.
    - Read the JSON file containing internship listings.
    - Compare the new listings with previously stored data.
    - Send formatted messages to the specified Discord channel for any new visible and active roles.

## Functions

### `clone_or_update_repo()`

Clones the repository if it doesn't exist locally or updates it if it already exists.

### `read_json()`

Reads a JSON file and returns the loaded data.

### `format_message(role)`

Generates a formatted message for a new internship posting, including details such as company name, role title, location, season, sponsorship, and posting date.

### `check_for_new_roles()`

Checks for new roles, compares them with previous data, and sends messages for new visible and active roles.

### `send_message(message, channel_id)`

Sends a message to a Discord channel identified by the provided channel ID, handling various exceptions that may occur during the process.

### `on_ready()`

Prints a message when the bot is logged in and then continuously runs a schedule while sleeping for 1 second in between.

## Scheduling

The bot uses the `schedule` library to check for new roles every minute. This can be adjusted by modifying the scheduling interval in the `mainbot.py` file.
