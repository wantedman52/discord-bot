import discord
from discord import app_commands
import os
import datetime

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise RuntimeError("TOKEN missing")

GUILD_ID = 1431313547014701136
LOG_CHANNEL_ID = 1515646304166875166
ROLE_ID = 1431319452829618326

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)

# ✔ ВАЖНО: НЕ client.tree!
tree = app_commands.CommandTree(client)


# =====================
def parse_time(time_str: str):
    try:
        time_str = time_str.lower().strip()
        num = int(time_str[:-1])
        unit = time_str[-1]

        if unit == "s":
            return num
        elif unit == "m":
            return num * 60
        elif unit == "h":
            return num * 3600
        elif unit == "d":
            return num * 86400
        return None
    except:
        return None


async def send_log(guild, text):
    if not guild:
        return
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(text)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    try:
        guild = discord.Object(id=GUILD_ID)
        await tree.sync(guild=guild)
        print("Commands synced")
    except Exception as e:
        print("SYNC ERROR:", e)


@tree.command(name="help", description="help", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "/ban /mute /warn /clear",
        ephemeral=True
    )


client.run(TOKEN)
