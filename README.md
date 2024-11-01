# Summer 2025 Internships Discord Bot

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Functions](#functions)
- [Scheduling](#scheduling)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

The **Summer 2025 Internships Discord Bot** is a Python-based Discord bot designed to monitor GitHub repositories for new internship postings. It automates the process of notifying a specified Discord channel with updates on available internship positions, ensuring that users stay informed about the latest opportunities.

## Features

- **Repository Monitoring:** Automatically clones or updates a specified GitHub repository to access the latest internship listings.
- **JSON Parsing:** Reads and processes internship data from a JSON file.
- **Change Detection:** Compares new internship listings with previously stored data to identify new opportunities.
- **Discord Integration:** Sends well-formatted messages to a designated Discord channel for each new visible and active internship role.
- **Error Handling:** Manages exceptions during Git operations and Discord interactions to ensure smooth operation.
- **Scheduling:** Utilizes the `schedule` library to periodically check for updates at configurable intervals.

## Prerequisites

Before setting up the bot, ensure you have the following installed:

- **Python:** Version 3.6 or higher. You can download it from [python.org](https://www.python.org/downloads/).
- **Git:** Version control system. Download from [git-scm.com](https://git-scm.com/downloads).
- **Discord Account:** To create and manage the Discord bot.
- **Discord Developer Portal Access:** For creating the bot application and obtaining necessary tokens.

## Installation

1. **Clone the Repository:**

    ```sh
    git clone https://github.com/Ouckah/Summer2025-Internships.git
    cd Summer2025-Internships
    ```

2. **Run the Setup Script:**

    ```sh
    chmod +x setup.sh
    ./setup.sh
    ```

    This script will:
    - Check your operating system and install required system packages
    - Set up a Python virtual environment
    - Install all required Python packages

    Supported platforms:
    - Linux (Ubuntu/Debian with apt, or Fedora/RHEL with dnf)
    - macOS (requires Homebrew)
    - Windows (requires Chocolatey)

3. **Alternative Manual Setup** (if setup script fails):

    Create a virtual environment and install requirements manually:

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # or
    venv\Scripts\activate     # On Windows
    pip install -r requirements.txt
    ```

## Configuration

1. **Discord Bot Setup:**

    - Navigate to the [Discord Developer Portal](https://discord.com/developers/applications) and create a new application.
    - Under the "Bot" section, add a new bot to your application.
    - **Copy the Bot Token:** This token is required for the bot to authenticate with Discord.
    - **Invite the Bot to Your Server:** Generate an OAuth2 URL with the necessary permissions and add the bot to your desired Discord server.

2. **Environment Variables:**

    Create a `.env` file in the root directory of the project and add the following:

    ```env
    DISCORD_TOKEN=your_discord_bot_token
    CHANNEL_ID=your_discord_channel_id
    REPO_URL=https://github.com/Ouckah/Summer2025-Internships.git
    JSON_FILE_PATH=path_to_your_json_file.json
    ```

    Replace `your_discord_bot_token`, `your_discord_channel_id`, and `path_to_your_json_file.json` with your actual Discord bot token, channel ID, and the path to the JSON file containing internship listings, respectively.

## Usage

1. **Run the Bot:**

    ```sh
    python mainbot.py
    ```

2. **Bot Actions:**

    - **Repository Management:** Clones the specified GitHub repository if it doesn't exist locally or pulls the latest changes if it does.
    - **Data Processing:** Reads internship listings from the JSON file and identifies new entries.
    - **Notification:** Sends formatted messages to the designated Discord channel for each new internship role detected.
    - **Continuous Monitoring:** Runs continuously, checking for updates at intervals defined in the scheduling configuration.

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

The bot uses the `schedule` library to check for new roles at regular intervals. By default, it checks every minute. To adjust the scheduling interval, modify the scheduling configuration in the `mainbot.py` file:

```python
import schedule

schedule.every(1).minutes.do(check_for_new_roles)
```

## Troubleshooting

- **Discord Bot Not Responding:**
  - Ensure the bot is online and has the necessary permissions in the Discord server.
  - Check the bot token and channel ID in the `.env` file.
  - Verify that the bot is correctly added to the server using the OAuth2 URL.
- **Git Operations Fail:**
  - Confirm that Git is installed and accessible from the command line.
  - Check the repository URL in the `.env` file and ensure it is correct.
  - Verify that the repository is accessible and public.
- **JSON Parsing Issues:**
  - Ensure the JSON file path in the `.env` file is correct.
  - Validate the JSON file structure and content for any errors.
  - Check the JSON file permissions and accessibility.

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

- Fork the Project
- Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
- Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
- Push to the Branch (`git push origin feature/AmazingFeature`)
- Open a Pull Request
