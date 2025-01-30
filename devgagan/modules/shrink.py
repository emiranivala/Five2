from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random
import string
import aiohttp
from devgagan import app
from devgagan.core.func import *
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB  # Removed WEBSITE_URL and AD_API since they are no longer needed

# MongoDB setup
tclient = AsyncIOMotorClient(MONGO_DB)
tdb = tclient["telegram_bot"]
token = tdb["tokens"]

# Create a TTL index for sessions collection
async def create_ttl_index():
    await token.create_index("expires_at", expireAfterSeconds=0)

# In-memory parameter storage
Param = {}

async def generate_random_param(length=8):
    """Generate a random parameter."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def is_user_verified(user_id):
    """Check if a user has an active session."""
    session = await token.find_one({"user_id": user_id})
    return session is not None

@app.on_message(filters.command("start"))
async def token_handler(client, message):
    """Handle the /token command."""
    join = await subscribe(client, message)
    if join == 1:
        return
    user_id = message.chat.id
    if len(message.command) <= 1:
        image_url = "https://i.postimg.cc/v8q8kGyz/startimg-1.jpg"
        join_button = InlineKeyboardButton("Join Channel", url="https://t.me/+rsngXN2zMJA5NTBl")
        premium = InlineKeyboardButton("Get Premium", url="https://t.me/Doldotby")
        keyboard = InlineKeyboardMarkup([
            [join_button],  
            [premium]   
        ])
        await message.reply_photo(
            photo=image_url,
            caption=(
                "Hi 👋 Welcome, Wanna intro...?\n\n"
                "✳️ I can save posts from channels or groups where forwarding is off. I can download videos/audio from YT, INSTA, ... social platforms\n"
                "✳️ Simply send the post link of a public channel. For private channels, do /login. Send /help to know more. \n\n"
                "> Must check /terms, /plan & /help\n\n"
                "> 👉 **__Note:__** Initiate /set to auto setup bot commands (owner only)"
            ),
            reply_markup=keyboard
        )
        return  
        
    param = message.command[1] if len(message.command) > 1 else None
    freecheck = await chk_user(message, user_id)
    if freecheck != 1:
        await message.reply("You are a premium user no need of token 😉")
        return

    if param:
        if user_id in Param and Param[user_id] == param:
            await token.insert_one({
                "user_id": user_id,
                "param": param,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=3),
            })
            del Param[user_id]  
            await message.reply("✅ You have been verified successfully! Enjoy your session for the next 3 hours.")
            return
        else:
            await message.reply("❌ Invalid or expired verification link. Please generate a new token.")
            return

@app.on_message(filters.command("token"))
async def smart_handler(client, message):
    user_id = message.chat.id
    freecheck = await chk_user(message, user_id)
    if freecheck != 1:
        await message.reply("You are a premium user no need of token 😉")
        return
    if await is_user_verified(user_id):
        await message.reply("✅ Your free session is already active, enjoy!")
    else:
        param = await generate_random_param()
        Param[user_id] = param  

        # Direct deep link (No URL shortener)
        deep_link = f"https://t.me/{client.me.username}?start={param}"

        # Create a button using the direct deep link
        button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Verify the token now...", url=deep_link)]]
        )
        
        await message.reply(
            "Click the button below to verify your free access token: \n\n"
            "> What will you get?\n"
            "1. No time bound up to 3 hours\n"
            "2. Batch command limit will be FreeLimit + 20\n"
            "3. All functions unlocked",
            reply_markup=button
        )
