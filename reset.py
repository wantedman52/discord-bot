import discord
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    tree.clear_commands()
    await tree.sync()

    print("RESET DONE - global commands cleared")

    await client.close()

client.run(TOKEN)
