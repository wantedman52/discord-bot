import discord
from discord import app_commands
import os
import datetime

TOKEN = os.getenv("TOKEN")

GUILD_ID = 1431313547014701136
LOG_CHANNEL_ID = 1515646304166875166  # поставь ID канала логов

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# ADMIN CHECK
# =====================
def is_admin(interaction: discord.Interaction):
    return interaction.guild and interaction.user.guild_permissions.administrator

# =====================
# TIME PARSER
# =====================
def parse_time(t: str):
    try:
        t = t.lower().strip()
        num = int(t[:-1])
        unit = t[-1]

        if unit == "s":
            return num
        if unit == "m":
            return num * 60
        if unit == "h":
            return num * 3600
        if unit == "d":
            return num * 86400
    except:
        return None

# =====================
# LOGS
# =====================
async def log(text: str):
    if LOG_CHANNEL_ID == 0:
        return
    channel = client.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(text)

# =====================
# READY (FIX SYNC)
# =====================
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    tree.clear_commands(guild=guild)
    await tree.sync(guild=guild)

    print(f"Logged in as {client.user}")
    print("Guild commands synced clean")

# =====================
# HELP
# =====================
@tree.command(name="help", description="Команды", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "/mute /unmute /ban /unban /warn",
        ephemeral=True
    )

# =====================
# MUTE
# =====================
@tree.command(name="mute", description="Мут", guild=discord.Object(id=GUILD_ID))
async def mute(interaction: discord.Interaction, member: discord.Member, time: str):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Нет прав", ephemeral=True)

    seconds = parse_time(time)
    if not seconds:
        return await interaction.response.send_message("❌ Формат: 10m / 1h / 1d", ephemeral=True)

    until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
    await member.timeout(until)

    await interaction.response.send_message("🔇 Замучен", ephemeral=True)

    await log(f"🔇 MUTE {member} на {time}")

# =====================
# UNMUTE
# =====================
@tree.command(name="unmute", description="Снять мут", guild=discord.Object(id=GUILD_ID))
async def unmute(interaction: discord.Interaction, member: discord.Member):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Нет прав", ephemeral=True)

    await member.timeout(None)

    await interaction.response.send_message("🔊 Размучен", ephemeral=True)

    await log(f"🔊 UNMUTE {member}")

# =====================
# BAN
# =====================
@tree.command(name="ban", description="Бан", guild=discord.Object(id=GUILD_ID))
async def ban(interaction: discord.Interaction, member: discord.Member):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Нет прав", ephemeral=True)

    await member.ban()

    await interaction.response.send_message("🔨 Забанен", ephemeral=True)

    await log(f"🔨 BAN {member}")

# =====================
# UNBAN
# =====================
@tree.command(name="unban", description="Разбан", guild=discord.Object(id=GUILD_ID))
async def unban(interaction: discord.Interaction, user_id: str):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Нет прав", ephemeral=True)

    user = await client.fetch_user(int(user_id))
    await interaction.guild.unban(user)

    await interaction.response.send_message("✅ Разбанен", ephemeral=True)

    await log(f"🔓 UNBAN {user}")

# =====================
# WARN
# =====================
warns = {}

@tree.command(name="warn", description="Варн", guild=discord.Object(id=GUILD_ID))
async def warn(interaction: discord.Interaction, member: discord.Member):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Нет прав", ephemeral=True)

    warns[str(member.id)] = warns.get(str(member.id), 0) + 1

    await interaction.response.send_message(
        f"⚠️ Варн {member} ({warns[str(member.id)]})",
        ephemeral=True
    )

    await log(f"⚠️ WARN {member} ({warns[str(member.id)]})")

# =====================
# RUN
# =====================
client.run(TOKEN)
