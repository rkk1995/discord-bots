import os
import discord
from openai import OpenAI, max_retries
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),  # Also log to console
    ],
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load your Discord and Grok API tokens
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Configure Grok (OpenAI client for x.ai)
client_grok = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)

# Set up the Discord bot
intents = discord.Intents.all()
intents.typing = False
intents.presences = False


class GrokBot(discord.Client):
    async def on_ready(self):
        if self.user:
            logger.info(f"{self.user.name} has connected to Discord!")
        else:
            logger.info("Bot has connected to Discord!")

    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # If the message starts with '!grok'
        if not message.content.startswith("!grok"):
            return

        # Extract the text after the command
        input_text = message.content[len("!grok") :].strip()

        logger.info(f"Received command from {message.author}: {input_text}")

        # Send an initial message to inform the user that the bot is working on a response
        working_message = await message.channel.send("Thinking ...")
        # Calculate max tokens based on input message length and maximum allowed tokens
        max_reply_tokens = max(1, 2048 - len(input_text))

        try:
            # Call the Grok API with the user's message
            completion = client_grok.chat.completions.create(
                model="grok-4-1-fast-reasoning",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. You answer questions in a discord server with some friends. Try to keep your messages short but always include the most important details and facts unless told not to. ",
                    },
                    {"role": "user", "content": input_text},
                ],
                max_tokens=max_reply_tokens,
                n=1,
                temperature=1,
            )
            grok_response = completion.choices[0].message.content.strip()
            logger.info(f"Generated response: {grok_response}...")
            await working_message.edit(content=grok_response)
        except Exception as e:
            logger.error(f"Grok API Error: {str(e)}")
            await working_message.edit(
                content=f"Sorry, there was an error processing your request. {str(e)}"
            )


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
client = GrokBot(intents=intents)
client.run(DISCORD_TOKEN)
