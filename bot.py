import datetime
import os
import re
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


class GrokBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.openai_client = Client(api_key=XAI_API_KEY)
        self.processed_messages = set()  # Deduplication cache
        self._discord_message_limit = 2000

    async def setup_hook(self):
        # Sync slash commands
        await self.tree.sync()
        logger.info("Slash commands synced")

    async def close(self):
        await self.openai_client.close()
        await super().close()

    async def on_ready(self):
        logger.info(f"🤖 {self.user} is online and ready!")

    async def on_message(self, message: discord.Message):
        # Ignore messages from the bot itself
        if not message.content.startswith("!"):
            return
        if message.author.bot:
            return

        if message.id in self.processed_messages:
            return
        self.processed_messages.add(message.id)

        if len(self.processed_messages) > 1000:
            self.processed_messages.clear()

        await message.channel.typing()
        user_input = message.clean_content.replace(f"@{self.user.name}", "").strip()
        history = []
        try:
            # Fetch last 30 messages for context (increased for better understanding)
            async for msg in message.channel.history(limit=30, before=message):
                item = None
                # Label other bots clearly in the history so Grok understands context
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
        if not success:
            # If silence signal returned (success=False, response="[SILENCE]"), just return
            if response == "[SILENCE]":
                return
            await message.channel.send(response, suppress_embeds=True)
            return

        # Check if response is empty or None
        if not response or not response.strip():
            response = (
                "I'm sorry, I couldn't generate a proper response. Please try again."
            )

        # Check for silence token in successful response too (just in case)
        if response.strip() == "[SILENCE]":
            return

        response = clean_response(response)

        # Truncate response if it's too long
        for chunk in split_for_discord(response):
            await message.channel.send(chunk, suppress_embeds=True)


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

            # # Current user message
            # user_content = []
            # final_text = input_text or "Please describe the attached image(s)."
            # user_content.append({"type": "text", "text": final_text})

            # if image_data:
            #     for image in image_data:
            #         # Ensure image_url is in the correct format
            #         if "image_url" in image:
            #             user_content.append(image)

            # messages.append(user(user_content))

            logger.info(
                f"🔧 Sending request to OpenRouter (Grok 4.1 Fast) with input snippet: {messages}'"
            )

            chat = self.openai_client.chat.create(
                model="grok-4-1-fast",
                tools=[web_search(), x_search()],
                max_tokens=1000,
                messages=messages,
            )

            response = chat.sample()
            if not response:
                logger.warning("No response")
            output_text = response.content
            print(output_text)
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
