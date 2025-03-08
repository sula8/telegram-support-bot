import logging
import os
import re
from typing import Optional, Union, Tuple
from dotenv import load_dotenv
from datetime import datetime
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
WELCOME_MESSAGE = (
    "Welcome to support bot! Please send your complete request in a single message, "
    "and we'll forward it to our team. This helps us process your request efficiently."
)
CONFIRMATION_MESSAGE = (
    "Thanks! We've received your request and will respond within a few hours. "
    "There's no need to send multiple messages for the same issue. If you'd like to add "
    "more information, please include everything in one detailed message."
)

# Validate configuration
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env file")
if not ADMIN_CHAT_ID:
    raise ValueError("ADMIN_CHAT_ID must be set in .env file")

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Helper functions
def format_user_info(user) -> str:
    """Format user information into a string."""
    info = f"{user.first_name} {user.last_name or ''}"
    if user.username:
        info += f" (@{user.username})"
    return info.strip()

def extract_ids_from_text(text: str) -> Tuple[Optional[int], Optional[int]]:
    """Extract user ID and message ID from message text."""
    user_id = None
    message_id = None
    
    # Try to find user ID in the message
    id_pattern = r"#ID(\d+)"
    id_matches = re.findall(id_pattern, text)
    if id_matches:
        user_id = int(id_matches[0])
        logger.info(f"Found user ID in message: {user_id}")
    else:
        # Check for user ID in confirmation message format
        confirmation_pattern = r"Message sent to user #ID(\d+)"
        conf_matches = re.findall(confirmation_pattern, text)
        if conf_matches:
            user_id = int(conf_matches[0])
            logger.info(f"Found user ID in confirmation message: {user_id}")
    
    # Try to find message ID in the message
    msg_pattern = r"#MSG(\d+)"
    msg_matches = re.findall(msg_pattern, text)
    if msg_matches:
        message_id = int(msg_matches[0])
        logger.info(f"Found message ID in message: {message_id}")
    else:
        # Check for message ID in confirmation message format
        conf_msg_pattern = r"message #(\d+)"
        conf_msg_matches = re.findall(conf_msg_pattern, text)
        if conf_msg_matches:
            message_id = int(conf_msg_matches[0])
            logger.info(f"Found message ID in confirmation message: {message_id}")
    
    return user_id, message_id

def create_hidden_tag(admin_msg_id: int) -> str:
    """Create a more compact tag with the admin message ID."""
    return f"\n\n#admsg{admin_msg_id}"

def extract_admin_msg_id(text: str) -> Optional[int]:
    """Extract admin message ID from the tag in message text."""
    compact_pattern = r"#admsg(\d+)"
    compact_matches = re.findall(compact_pattern, text)
    
    if compact_matches:
        return int(compact_matches[0])
    
    return None

def get_start_button_keyboard():
    """Create a keyboard with a Start/Restart button."""
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("🔄 Start/Restart")]],
        resize_keyboard=True
    )
    return keyboard

async def send_message(context: ContextTypes.DEFAULT_TYPE, chat_id: Union[str, int], 
                      message: Message, text: Optional[str] = None, 
                      reply_to_message_id: Optional[int] = None,
                      admin_msg_id: Optional[int] = None,
                      with_restart_button: bool = False) -> Message:
    """Send a message to a chat based on the message type."""
    reply_params = {} if reply_to_message_id is None else {"reply_to_message_id": reply_to_message_id}
    
    # Add admin message ID tag if provided - using hidden format
    admin_tag = create_hidden_tag(admin_msg_id) if admin_msg_id is not None else ""
    
    # Add keyboard with restart button if requested
    keyboard = get_start_button_keyboard() if with_restart_button else None
    if keyboard:
        reply_params["reply_markup"] = keyboard
    
    try:
        if message.photo:
            caption = text if text is not None else (message.caption or "")
            if admin_msg_id is not None:
                caption += admin_tag
            
            return await context.bot.send_photo(
                chat_id=chat_id,
                photo=message.photo[-1].file_id,
                caption=caption,
                **reply_params
            )
        elif message.video:
            caption = text if text is not None else (message.caption or "")
            if admin_msg_id is not None:
                caption += admin_tag
                
            return await context.bot.send_video(
                chat_id=chat_id,
                video=message.video.file_id,
                caption=caption,
                **reply_params
            )
        elif message.document:
            caption = text if text is not None else (message.caption or "")
            if admin_msg_id is not None:
                caption += admin_tag
                
            return await context.bot.send_document(
                chat_id=chat_id,
                document=message.document.file_id,
                caption=caption,
                **reply_params
            )
        elif message.voice:
            caption = text if text is not None else (message.caption or "")
            if admin_msg_id is not None:
                caption += admin_tag
                
            return await context.bot.send_voice(
                chat_id=chat_id,
                voice=message.voice.file_id,
                caption=caption,
                **reply_params
            )
        elif message.audio:
            caption = text if text is not None else (message.caption or "")
            if admin_msg_id is not None:
                caption += admin_tag
                
            return await context.bot.send_audio(
                chat_id=chat_id,
                audio=message.audio.file_id,
                caption=caption,
                **reply_params
            )
        else:
            # Plain text message
            message_text = text if text is not None else (message.text or "")
            if admin_msg_id is not None:
                message_text += admin_tag
                
            return await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                **reply_params
            )
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {str(e)}")
        raise

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when the command /start is issued."""
    keyboard = get_start_button_keyboard()
    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=keyboard
    )

# Message handlers
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages from users."""
    if update.message is None:
        return
    
    user = update.effective_user
    if user is None:
        return
    
    # Handle the Start/Restart button
    if update.message.text == "🔄 Start/Restart":
        await start(update, context)
        return
    
    user_id = user.id
    message = update.message
    message_id = message.message_id
    date_time = update.message.date.strftime('%Y-%m-%d %H:%M:%S')
    
    # Log the incoming message
    logger.info(f"Received message from user {user_id}: {message.text or '[attachment]'}")
    
    # Check if this is a reply to an admin message by looking for the admin message tag
    admin_reply_id = None
    if message.reply_to_message:
        reply_text = message.reply_to_message.text or message.reply_to_message.caption or ""
        admin_msg_id = extract_admin_msg_id(reply_text)
        if admin_msg_id is not None:
            logger.info(f"User is replying to admin message ID: {admin_msg_id}")
            admin_reply_id = admin_msg_id
    
    # Format message for admin
    admin_text = f"[{date_time}]\n"
    admin_text += f"From: {format_user_info(user)} #ID{user_id}\n"
    admin_text += f"#MSG{message_id}\n"  # This is the important part for replies
    
    # If this is a reply to an admin's message, note it
    if message.reply_to_message:
        if admin_reply_id:
            admin_text += f"↩️ Reply to admin message #{admin_reply_id}\n"
        else:
            admin_text += f"↩️ Reply to message #{message.reply_to_message.message_id}\n"
    
    # Add message content
    if message.text:
        admin_text += f"Message: {message.text}\n"
    
    # Check if there are attachments
    has_attachment = bool(message.photo or message.video or message.document or message.voice or message.audio)
    if has_attachment:
        admin_text += "Attachments: "
        if message.photo:
            admin_text += "[Photo]"
        elif message.video:
            admin_text += "[Video]"
        elif message.document:
            admin_text += f"[File: {message.document.file_name}]"
        elif message.voice:
            admin_text += "[Voice message]"
        elif message.audio:
            admin_text += f"[Audio: {message.audio.title or 'Unknown title'}]"
        
        if message.caption:
            admin_text += f" with caption: {message.caption}"
    
    try:
        # Forward message to admin - set up reply if we found a admin message ID
        reply_params = {}
        if admin_reply_id:
            reply_params = {"reply_to_message_id": admin_reply_id}
            
        sent_msg = await send_message(context, ADMIN_CHAT_ID, message, admin_text, **reply_params)
        logger.info(f"Sent message to admin, ID: {sent_msg.message_id}")
        
        # Send confirmation message to user with restart button
        await context.bot.send_message(
            chat_id=user_id,
            text=CONFIRMATION_MESSAGE,
            reply_markup=get_start_button_keyboard()
        )
    except Exception as e:
        logger.error(f"Error processing user message: {e}")

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages from the admin."""
    if update.message is None or update.message.reply_to_message is None:
        return
    
    message = update.message
    admin_msg_id = message.message_id  # Store this to include in the message to user
    logger.info(f"Processing admin reply: {message.text or '[attachment]'}")
    
    # Get the text content of the message being replied to
    reply_text = message.reply_to_message.text or message.reply_to_message.caption or ""
    logger.info(f"Admin replying to: {reply_text}")
    
    # Extract user ID and original message ID from the reply text
    user_id, original_message_id = extract_ids_from_text(reply_text)
    logger.info(f"Extracted user_id: {user_id}, original_message_id: {original_message_id}")
    
    if not user_id:
        logger.error("No user ID found in message!")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text="⚠️ Could not find the user ID in the message. Make sure you're replying to a forwarded user message."
        )
        return
    
    try:
        # Let the user know the admin is typing
        await context.bot.send_chat_action(chat_id=user_id, action="typing")
        
        # Send the admin's message to the user as a reply to their original message
        # Include the admin message ID in the message for tracking replies
        sent_message = await send_message(
            context, 
            user_id, 
            message, 
            reply_to_message_id=original_message_id,
            admin_msg_id=admin_msg_id,  # This is the key addition
            with_restart_button=True     # Add the restart button to admin replies
        )
        logger.info(f"Sent admin's reply to user {user_id}, message ID: {sent_message.message_id}")
        
        # Confirm to admin that the message was sent - as a reply to the admin's message
        confirmation_message = f"✅ Message sent to user #ID{user_id} (message #{admin_msg_id})"
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=confirmation_message,
            reply_to_message_id=admin_msg_id  # Send as reply to admin's original message
        )
    except Exception as e:
        error_msg = f"⚠️ Error sending message to user: {str(e)}"
        logger.error(error_msg)
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=error_msg
        )

async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route messages to the appropriate handler based on source and type."""
    if update.message is None:
        return
    
    chat_id = update.effective_chat.id
    message = update.message
    
    # Handle Start/Restart button from anywhere
    if message.text == "🔄 Start/Restart":
        await start(update, context)
        return
    
    # Log basic information about the message
    logger.info(f"Message from chat ID: {chat_id}")
    logger.info(f"Is reply: {bool(message.reply_to_message)}")
    logger.info(f"Text: {message.text or message.caption or '[no text]'}")
    
    if message.reply_to_message:
        logger.info(f"Reply to message ID: {message.reply_to_message.message_id}")
    
    # Route message to appropriate handler
    if str(chat_id) == ADMIN_CHAT_ID and message.reply_to_message:
        await handle_admin_message(update, context)
    elif str(chat_id) != ADMIN_CHAT_ID:
        await handle_user_message(update, context)

def main() -> None:
    """Start the bot."""
    # Create the application and pass it the token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    
    # Add message handler
    application.add_handler(
        MessageHandler(
            (filters.TEXT | filters.ATTACHMENT),
            message_router
        )
    )
    
    # Log startup
    logger.info("Support Bot started!")
    
    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()