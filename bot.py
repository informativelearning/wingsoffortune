import discord
import os
from groq import Groq

# 1. Setup Discord Client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 2. Setup Groq (The Brain)
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@client.event
async def on_ready():
    print(f'Bot is logged in as {client.user}')

@client.event
async def on_message(message):
    # Don't let the bot talk to itself
    if message.author == client.user:
        return

    # Optional: Only reply if mentioned (Remove this if you want it to reply to everything)
    if client.user in message.mentions:
        user_message = message.content.replace(f'<@{client.user.id}>', '').strip()
        
        try:
            # Send "Typing..." status so users know it's thinking
            async with message.channel.typing():
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful and intelligent Discord assistant."
                        },
                        {
                            "role": "user",
                            "content": user_message,
                        }
                    ],
                    model="llama3-70b-8192", # High Intelligence Model
                )
                
                response = chat_completion.choices[0].message.content
                
                # Split message if it's too long for Discord (2000 char limit)
                if len(response) > 2000:
                    for i in range(0, len(response), 2000):
                        await message.channel.send(response[i:i+2000])
                else:
                    await message.channel.send(response)
                    
        except Exception as e:
            print(f"Error: {e}")
            await message.channel.send("I ran into an error processing that request.")

# 3. Run the Bot
client.run(os.environ.get("DISCORD_TOKEN"))