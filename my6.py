import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from collections import defaultdict
import time
import re

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace 'YOUR_GROUP_CHAT_ID' with your group's chat ID
GROUP_CHAT_ID = '-1002448930264'
CHANNEL_USERNAME = "@MasterMafiaa" 

# Limit for messages sent in quick succession (seconds)
MESSAGE_LIMIT_TIME = 5  # seconds
# Limit for the number of messages allowed in a quick succession
MESSAGE_LIMIT_COUNT = 3

# Create a dictionary to count user messages and their timestamps
user_message_count = defaultdict(lambda: {"count": 0, "first_time": 0})

# تابع برای بررسی عضویت کاربر در کانال
async def check_channel_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member_status = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member_status.status in ["member", "administrator", "creator"]
    except Exception as e:
        # در صورت خطا به عنوان کاربر غیر عضو بازگشت داده می‌شود
        return False
    
# Command to start the bot
# Command to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    is_member = await check_channel_membership(user_id, context)

    if is_member:
        await update.message.reply_text("سلام! آماده دریافت پیام‌های شما هستم.")
    else:
        # اگر کاربر عضو نبود، دکمه شیشه‌ای برای عضویت نشان داده می‌شود
        join_button = InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/MasterMafiaa")
        keyboard = InlineKeyboardMarkup([[join_button]])

        await update.message.reply_text(
            "برای استفاده از این ربات، ابتدا باید عضو کانال شوید.",
            reply_markup=keyboard
        )

# Check for inline keyboard in the message
def has_inline_keyboard(message) -> bool:
    return message.reply_markup is not None and message.reply_markup.inline_keyboard is not None

# Function to handle incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    # Check if the message is a reply to another message
    if update.message.reply_to_message:
        # Check if the replied message is from the bot and has an inline keyboard
        if (update.message.reply_to_message.from_user.id == context.bot.id and
            has_inline_keyboard(update.message.reply_to_message)):
            # Call handle_reply if conditions are met
            await handle_reply(update, context)
            return  # Prevent further handling of this message
    
    if update.message.chat.type != "private":
        return
    
    user_id = update.message.from_user.id
    user_message = update.message

    # Prepare the inline button with user ID
    user_id_button = InlineKeyboardButton(f"User ID: {user_id}", callback_data=str(user_id))
    keyboard = InlineKeyboardMarkup([[user_id_button]])

    # Check for rapid message sending
    current_time = time.time()
    
    if user_message_count[user_id]["count"] == 0:
        user_message_count[user_id]["first_time"] = current_time

    # Update message count and check if the time limit has been exceeded
    if current_time - user_message_count[user_id]["first_time"] < MESSAGE_LIMIT_TIME:
        user_message_count[user_id]["count"] += 1
    else:
        user_message_count[user_id]["count"] = 1
        user_message_count[user_id]["first_time"] = current_time

    # Check if user exceeded message limit
    if user_message_count[user_id]["count"] > MESSAGE_LIMIT_COUNT:
        await update.message.reply_text("لطفا به آرامی پیام ارسال کنید!")
        return  # Ignore the message

    # Notify the user that their message was sent
    await update.message.reply_text("پیام شما ارسال شد.")

    # Send the user's message to the group
    if user_message.text:
        await context.bot.send_message(chat_id=GROUP_CHAT_ID,
                                       text=user_message.text,
                                       reply_markup=keyboard)
    elif user_message.sticker:
        await context.bot.send_sticker(chat_id=GROUP_CHAT_ID,
                                       sticker=user_message.sticker.file_id,
                                       reply_markup=keyboard)
    elif user_message.voice:
        await context.bot.send_voice(chat_id=GROUP_CHAT_ID,
                                     voice=user_message.voice.file_id,
                                     reply_markup=keyboard)
    elif user_message.photo:
        await context.bot.send_photo(chat_id=GROUP_CHAT_ID,
                                     photo=user_message.photo[-1].file_id,
                                     reply_markup=keyboard)
    elif user_message.video:
        await context.bot.send_video(chat_id=GROUP_CHAT_ID,
                                     video=user_message.video.file_id,
                                     reply_markup=keyboard)
    elif user_message.animation:
        await context.bot.send_animation(chat_id=GROUP_CHAT_ID,
                                         animation=user_message.animation.file_id,
                                         reply_markup=keyboard)
        
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.reply_to_message:
        original_message = update.message.reply_to_message

        # Check if the original message has an inline keyboard
        if original_message.reply_markup:
            # Extract user ID from the button's callback data
            button = original_message.reply_markup.inline_keyboard[0][0]  # Get the first button
            original_sender_id = int(button.callback_data)  # Extract the user ID from callback data
            
            # Prepare the reply message
            reply_message_text = update.message.text or update.message.caption or ""

            # Always send the reply message if it exists
            if update.message.text:
                await context.bot.send_message(original_sender_id, reply_message_text)
                
            # Forward any media types from the reply message
            if update.message.sticker:
                await context.bot.send_sticker(original_sender_id, update.message.sticker.file_id)
            if update.message.voice:
                await context.bot.send_voice(original_sender_id, update.message.voice.file_id)
            if update.message.photo:
                await context.bot.send_photo(original_sender_id, update.message.photo[-1].file_id, caption=reply_message_text)
            if update.message.video:
                await context.bot.send_video(original_sender_id, update.message.video.file_id, caption=reply_message_text)
            if update.message.animation:
                await context.bot.send_animation(original_sender_id, update.message.animation.file_id, caption=reply_message_text)
            if update.message.document:
                await context.bot.send_document(original_sender_id, update.message.document.file_id, caption=reply_message_text)

            # Send confirmation message to the group chat
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text="پاسخ شما ارسال شد.")

# Function to handle errors
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def main():
    # Replace 'YOUR_TOKEN' with your bot's API token
    application = ApplicationBuilder().token("7765263412:AAGjqJHrhXPQ12fiU_rSVVVSbDu9NEGJCnk").build()

    # Register command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    application.add_handler(MessageHandler(filters.ALL & filters.REPLY, handle_reply))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
