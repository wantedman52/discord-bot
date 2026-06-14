import discord
from discord import app_commands
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    # ❗ удаляем ВСЕ global команды (ЛС)
    tree.clear_commands()
    await tree.sync()

    print("GLOBAL commands deleted")

    await client.close()

client.run(TOKEN)
