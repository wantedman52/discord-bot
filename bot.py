import discord
from discord import app_commands
import os
import asyncio
import datetime
import json

TOKEN = os.getenv("TOKEN")

GUILD_ID = 1431313547014701136
LOG_CHANNEL_ID = 0  # <-- ВСТАВЬ ID ЛОГ-КАНАЛА

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# WARNS SYSTEM (FILE)
# =====================
WARN_FILE = "warns.json"

def load_warns():
    try:
        with open(WARN_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_warns(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f)

warns = load_warns()

# =====================
# LOGS
# =====================
async def send_log(text: str):
    if LOG_CHANNEL_ID == 0:
        return
    channel = client.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(text)

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
# READY
# =====================
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    try:
        synced = await tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print("Sync error:", e)

    print(f"Logged in as {client.user}")

# =====================
# HELP
# =====================
@tree.command(name="help", description="Команды", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("/help /ban /mute /warn /unban /unmute")

# =====================
# MUTE
# =====================
@tree.command(name="mute", description="Мут с временем", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, time: str, reason: str = "Без причины"):

    seconds = parse_time(time)

    if not seconds:
        await interaction.response.send_message("❌ Формат: 10m / 1h / 1d")
        return

    until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)

    await member.timeout(until, reason=reason)

    await interaction.response.send_message(f"🔇 {member.mention} мут на {time}")

    await send_log(f"🔇 MUTE: {member} | {time} | {reason}")

# =====================
# UNMUTE
# =====================
@tree.command(name="unmute", description="Снять мут", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):

    await member.timeout(None)

    await interaction.response.send_message(f"🔊 Размучен {member}")

    await send_log(f"🔊 UNMUTE: {member}")

# =====================
# BAN
# =====================
@tree.command(name="ban", description="Бан", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):

    await member.ban(reason=reason)

    await interaction.response.send_message(f"🔨 {member} забанен")

    await send_log(f"🔨 BAN: {member} | {reason}")

# =====================
# UNBAN
# =====================
@tree.command(name="unban", description="Разбан", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):

    user = await client.fetch_user(int(user_id))
    await interaction.guild.unban(user)

    await interaction.response.send_message(f"✅ Разбанен {user}")

    await send_log(f"🔓 UNBAN: {user}")

# =====================
# WARN
# =====================
@tree.command(name="warn", description="Варн", guild=discord.Object(id=GUILD_ID))
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):

    warns.setdefault(str(member.id), 0)
    warns[str(member.id)] += 1
    save_warns(warns)

    await interaction.response.send_message(
        f"⚠️ {member.mention} варн ({warns[str(member.id)]})"
    )

    await send_log(f"⚠️ WARN: {member} | {reason}")

# =====================
# RUN
# =====================
client.run(TOKEN)
