# Telegram Support Bot

A lightweight, efficient Telegram bot for customer support that enables seamless two-way communication between users and support administrators. This bot allows support staff to respond to user inquiries directly through Telegram, with proper message threading and media support.

![Telegram Support Bot](https://img.shields.io/badge/Telegram-Support%20Bot-blue?logo=telegram)
![Python](https://img.shields.io/badge/Python-3.7%2B-green?logo=python)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Two-way Communication**: Users message the bot and administrators reply from a designated admin chat
- **Proper Message Threading**: Maintains conversation context with threaded replies in both directions
- **Media Support**: Handles all types of attachments (photos, videos, documents, voice messages, etc.)
- **Start/Restart Button**: Convenient button for users to restart conversations
- **No Database Required**: Lightweight implementation that doesn't require a database
- **Easy to Deploy**: Simple setup as a systemd service for 24/7 operation

## Requirements

- Python 3.7+
- python-telegram-bot (v20+)
- python-dotenv

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/telegram-support-bot.git
   cd telegram-support-bot
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
   ADMIN_CHAT_ID=your_admin_group_chat_id
   ```

5. Run the bot:
   ```bash
   python main.py
   ```

## Setting up as a Service

1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/support-tg-bot.service
   ```

2. Add the following content (adjust paths as needed):
   ```
   [Unit]
   Description=Telegram Support Bot
   After=network.target
   
   [Service]
   User=root
   WorkingDirectory=/opt/support-tg-bot
   ExecStart=/opt/support-tg-bot/.venv/bin/python /opt/support-tg-bot/main.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable support-tg-bot.service
   sudo systemctl start support-tg-bot.service
   ```

4. Check the status:
   ```bash
   sudo systemctl status support-tg-bot.service
   ```

## Setup Guide

### Bot Setup
1. Create a new bot using [@BotFather](https://t.me/botfather) on Telegram
2. Copy the bot token provided by BotFather
3. Add the token to your `.env` file

### Admin Chat Setup
1. Create a group chat in Telegram
2. Add your bot to the group
3. Send any message to the group
4. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in your browser
5. Find the `chat` object with `"type":"group"` and copy the `id` value
6. Add this ID to your `.env` file as `ADMIN_CHAT_ID`

## How It Works

1. **User Interaction**:
   - Users send messages to the bot
   - The bot forwards these messages to the admin group
   - Each message includes user info and unique IDs for tracking

2. **Admin Responses**:
   - Admins reply to forwarded messages in the group
   - The bot sends these replies back to the corresponding user
   - Replies maintain proper threading and context

3. **Message Threading**:
   - Each message contains hidden tags to maintain the conversation context
   - This allows for proper reply chains without requiring a database

## Customization

You can customize the bot's messages by editing these variables in the `main.py` file:

- `WELCOME_MESSAGE`: Sent when a user first starts the bot
- `CONFIRMATION_MESSAGE`: Sent after a user submits a message

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
