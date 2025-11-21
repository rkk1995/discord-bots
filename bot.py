import datetime
import asyncio
import os
from typing import List, Optional
import discord
from openai import AsyncOpenAI
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import logging

from xai_sdk import Client
from xai_sdk.chat import user, system, assistant
from xai_sdk.tools import web_search, x_search
from utils.text_processing import split_for_discord, clean_response, enforce_single_x_link
from utils.discord_helpers import get_server_context
from prompts.system import get_system_prompt

from log.setup import setup_logging
from links.links import handle_links

# Configure logging
logger = setup_logging()

# Load environment variables
load_dotenv()

# Load your Discord and Grok API tokens
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Set up the Discord bot
intents = discord.Intents.all()
intents.message_content = True
intents.messages = True


class GrokBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.openai_client = Client(api_key=XAI_API_KEY)
        self.processed_messages = set()  # Deduplication cache
        self._discord_message_limit = 2000

    async def setup_hook(self):
        # Sync slash commands
        logger.info("Syncing slash commands...")
        await self.tree.sync()
        logger.info("Slash commands synced")

    async def close(self):
        self.openai_client.close()
        await super().close()

    async def on_ready(self):
        logger.info(f"🤖 {self.user} is online and ready!")
    
    async def handle_mention(self, message: discord.Message):
        user_input = message.clean_content.replace(f"@{self.user.name}", "").strip()
        history = []
        try:
            # Fetch last 30 messages for context (increased for better understanding)
            async for msg in message.channel.history(limit=30, before=message):
                item = None
                if msg.author.bot:
                    content = f"[Bot {msg.author.name}]: {msg.clean_content}"
                    item = assistant(content)
                else:
                    content = f"{msg.author.name}: {msg.clean_content}"
                    item = user(content)

                if content:
                    history.append(item)
        except Exception as e:
            logger.warning(f"Could not fetch history: {e}")
        history.reverse()
        server_context = get_server_context(message.guild)
        success, response = await self.call_openai_api(
            user_input,
            history=history,
            server_context=server_context,
        )
        return success, response
    

    async def on_message(self, message: discord.Message):
        # Ignore messages from the bot itself
        if message.author.bot:
            return

        if message.id in self.processed_messages:
            return
        self.processed_messages.add(message.id)

        if len(self.processed_messages) > 1000:
            self.processed_messages.clear()

        mentioned = self.user.id in message.raw_mentions
        if mentioned:
            await message.channel.typing()
            success, response = await self.handle_mention(message)
            if not success:
                await message.channel.send(response, suppress_embeds=True)
                return
            if not response or not response.strip():
                response = (
                    "I'm sorry, I couldn't generate a proper response. Please try again."
                )
            response = clean_response(response)
            for chunk in split_for_discord(response):
                await message.channel.send(chunk, suppress_embeds=True)

        else:
            should_process, response = handle_links(message)
            if not should_process:
                return
            await message.channel.typing()
            await message.delete()
            await message.channel.send(response, allowed_mentions=discord.AllowedMentions.none())
        
    async def call_openai_api(
        self,
        input_text: str,
        image_data: Optional[List[dict]] = None,
        history: Optional[List[dict]] = None,
        server_context: str = "",
    ) -> tuple[bool, str]:
        try:
            # Build messages

            # System prompt
            system_prompt = get_system_prompt(server_context)

            messages = [system(system_prompt)]

            # History
            if history:
                for entry in history:  # History is already limited by on_message
                    messages.append(entry)
            messages.append(user(input_text))

            logger.info(
                f"🔧 Sending request to OpenRouter (Grok 4.1 Fast) with input snippet'"
            )

            chat = self.openai_client.chat.create(
                model="grok-4-1-fast",
                tools=[web_search(), x_search()],
                max_tokens=1000,
                messages=messages,
            )

            response = await asyncio.to_thread(chat.sample)
            if not response:
                logger.warning("No response")
            output_text = response.content
            if not output_text:
                logger.warning("⚠️ OpenRouter returned empty content")
                return False, "I apologize, but I couldn't generate a proper response."

            if output_text.strip() == "[SILENCE]":
                return False, "[SILENCE]"

            if output_text.strip() == "[SILENCE]":
                return False, "[SILENCE]"

            # Enforce single X link limit code-side
            output_text = enforce_single_x_link(output_text)

            return True, output_text
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return False, f"❌ An error occurred: {str(e)}"




# Check if tokens are provided
if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN not found in environment variables!")
    logger.error("Please create a .env file with your Discord bot token.")
    exit(1)

if not XAI_API_KEY:
    logger.error("XAI_API_KEY not found in environment variables!")
    logger.error("Please create a .env file with your X.AI Grok API key.")
    exit(1)

# Create and run the bot
logger.info("Starting Discord bot...")
client = GrokBot()
client.run(DISCORD_TOKEN)
