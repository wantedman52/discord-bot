import discord
from discord import app_commands
import os
import asyncio
import datetime

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1431313547014701136

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# TIME PARSER
# =====================
def parse_time(time_str: str):
    try:
        unit = time_str[-1]
        value = int(time_str[:-1])

        if unit == "s":
            return value
        if unit == "m":
            return value * 60
        if unit == "h":
            return value * 3600
        if unit == "d":
            return value * 86400
    except:
        return None

    return None


# =====================
# READY + SYNC
# =====================
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    try:
        synced = await tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands (guild)")
    except Exception as e:
        print("Sync error:", e)

    print(f"Logged in as {client.user}")


# =====================
# HELP
# =====================
@tree.command(name="help", description="Команды", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("/help /ban /mute /warn")


# =====================
# MUTE (TIME)
# =====================
@tree.command(name="mute", description="Мут с временем", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, time: str, reason: str = "Без причины"):

    seconds = parse_time(time)

    if not seconds:
        await interaction.response.send_message("❌ Используй формат: 10m / 1h / 1d")
        return

    until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)

    await member.timeout(until, reason=reason)

    await interaction.response.send_message(
        f"🔇 {member.mention} замучен на {time}. Причина: {reason}"
    )


# =====================
# BAN
# =====================
@tree.command(name="ban", description="Бан", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):

    await member.ban(reason=reason)

    await interaction.response.send_message(
        f"🔨 {member} забанен. Причина: {reason}"
    )


# =====================
# WARN
# =====================
warns = {}

@tree.command(name="warn", description="Варн", guild=discord.Object(id=GUILD_ID))
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):

    warns.setdefault(member.id, 0)
    warns[member.id] += 1

    await interaction.response.send_message(
        f"⚠️ {member.mention} варн ({warns[member.id]}). Причина: {reason}"
    )


# =====================
# RUN BOT
# =====================
client.run(TOKEN)
