import os
import discord
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load your Discord and Gemini API tokens
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# Set up the Discord bot
intents = discord.Intents.all()
intents.typing = False
intents.presences = False


class GeminiBot(discord.Client):
    async def on_ready(self):
        print(f"{self.user.name} has connected to Discord!")

    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        # If the message starts with '!grok'
        if not message.content.startswith("!grok"):
            return

        # Extract the text after the command
        input_text = message.content[len("!grok") :].strip()

        # Send an initial message to inform the user that the bot is working on a response
        working_message = await message.channel.send("Thinking ...")

        # Calculate max tokens based on input message length and maximum allowed tokens
        max_reply_tokens = max(1, 1000 - len(input_text))

        try:
            # Call the Gemini API with the user's message
            response = model.generate_content(
                input_text,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_reply_tokens,
                    temperature=1,
                ),
            )

            # Extract the generated response
            gemini_response = response.text.strip()

            # Edit the initial message with the actual response
            await working_message.edit(content=gemini_response)

        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            await working_message.edit(
                content="Sorry, there was an error processing your request."
            )


# Check if tokens are provided
if not DISCORD_TOKEN:
    print("Error: DISCORD_TOKEN not found in environment variables!")
    print("Please create a .env file with your Discord bot token.")
    exit(1)

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables!")
    print("Please create a .env file with your Gemini API key.")
    exit(1)

# Create and run the bot
client = GeminiBot(intents=intents)
client.run(DISCORD_TOKEN)
