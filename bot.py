import discord
from discord import app_commands
import os
import datetime
import json

TOKEN = os.getenv("TOKEN")

GUILD_ID = 1431313547014701136

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# CHECK ADMIN
# =====================
def is_admin(interaction: discord.Interaction):
    return interaction.guild is not None and interaction.user.guild_permissions.administrator

# =====================
# WARN SYSTEM
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
# TIME PARSER
# =====================
def parse_time(time_str: str):
    try:
        time_str = time_str.lower().strip()
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

# =====================
# READY + GUILD SYNC (IMPORTANT)
# =====================
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    tree.clear_commands(guild=guild)
    await tree.sync(guild=guild)

    print(f"Logged in as {client.user}")
    print("Guild-only commands synced (NO DM COMMANDS)")

# =====================
# HELP (VISIBLE IN DM + SERVER)
# =====================
@tree.command(
    name="help",
    description="Показать команды",
    guild=discord.Object(id=GUILD_ID)
)
async def help_cmd(interaction: discord.Interaction):

    await interaction.response.send_message(
        "📌 Команды:\n/help (везде)\n/mute /ban /warn (только сервер)",
        ephemeral=True
    )

# =====================
# MUTE (SERVER ONLY)
# =====================
@tree.command(
    name="mute",
    description="Мут пользователя",
    guild=discord.Object(id=GUILD_ID)
)
async def mute(interaction: discord.Interaction, member: discord.Member, time: str, reason: str = "Без причины"):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Только админы и только сервер", ephemeral=True)

    seconds = parse_time(time)

    if not seconds:
        return await interaction.response.send_message("❌ Формат: 10m / 1h / 1d", ephemeral=True)

    until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)

    await member.timeout(until, reason=reason)

    await interaction.response.send_message(
        f"🔇 {member} мут на {time}",
        ephemeral=True
    )

# =====================
# BAN
# =====================
@tree.command(
    name="ban",
    description="Бан пользователя",
    guild=discord.Object(id=GUILD_ID)
)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Только админы и только сервер", ephemeral=True)

    await member.ban(reason=reason)

    await interaction.response.send_message(
        f"🔨 {member} забанен",
        ephemeral=True
    )

# =====================
# WARN
# =====================
@tree.command(
    name="warn",
    description="Варн",
    guild=discord.Object(id=GUILD_ID)
)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Только админы и только сервер", ephemeral=True)

    warns.setdefault(str(member.id), 0)
    warns[str(member.id)] += 1
    save_warns(warns)

    await interaction.response.send_message(
        f"⚠️ {member} варн ({warns[str(member.id)]})",
        ephemeral=True
    )

# =====================
# RUN BOT
# =====================
client.run(TOKEN)
