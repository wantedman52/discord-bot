import discord
from discord import app_commands
import os
import datetime

TOKEN = os.getenv("TOKEN")

GUILD_ID = 1431313547014701136

# 👉 ВСТАВЬ ID КАНАЛА ДЛЯ ЛОГОВ
LOG_CHANNEL_ID = 1515646304166875166  # <-- поменяешь на свой

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# TIME PARSER
# =====================
def parse_time(time_str: str):
    try:
        time_str = time_str.lower()
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

# =====================
# LOG FUNCTION
# =====================
async def send_log(guild, text):
    if LOG_CHANNEL_ID == 0:
        return

    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(text)

# =====================
# READY
# =====================
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    await tree.sync(guild=guild)

    print(f"Logged in as {client.user}")
    print("Guild commands synced")

# =====================
# HELP
# =====================
@tree.command(name="help", description="Команды", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "/ban /unban /mute /unmute /warn",
        ephemeral=True
    )

# =====================
# BAN
# =====================
@tree.command(name="ban", description="Бан", guild=discord.Object(id=GUILD_ID))
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):
    await member.ban(reason=reason)

    await interaction.response.send_message("🔨 banned", ephemeral=True)

    await send_log(
        interaction.guild,
        f"🔨 BAN\nUser: {member}\nBy: {interaction.user}\nReason: {reason}"
    )

# =====================
# UNBAN
# =====================
@tree.command(name="unban", description="Разбан", guild=discord.Object(id=GUILD_ID))
async def unban(interaction: discord.Interaction, user_id: str):
    user = await client.fetch_user(int(user_id))
    await interaction.guild.unban(user)

    await interaction.response.send_message("✅ unbanned", ephemeral=True)

    await send_log(
        interaction.guild,
        f"✅ UNBAN\nUser ID: {user_id}\nBy: {interaction.user}"
    )

# =====================
# MUTE
# =====================
@tree.command(name="mute", description="Мут", guild=discord.Object(id=GUILD_ID))
async def mute(interaction: discord.Interaction, member: discord.Member, time: str):
    seconds = parse_time(time)

    if not seconds:
        return await interaction.response.send_message("❌ format 10m / 1h / 1d", ephemeral=True)

    until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
    await member.timeout(until)

    await interaction.response.send_message("🔇 muted", ephemeral=True)

    await send_log(
        interaction.guild,
        f"🔇 MUTE\nUser: {member}\nBy: {interaction.user}\nTime: {time}"
    )

# =====================
# UNMUTE
# =====================
@tree.command(name="unmute", description="Снять мут", guild=discord.Object(id=GUILD_ID))
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)

    await interaction.response.send_message("🔊 unmuted", ephemeral=True)

    await send_log(
        interaction.guild,
        f"🔊 UNMUTE\nUser: {member}\nBy: {interaction.user}"
    )

# =====================
# WARN
# =====================
warns = {}

@tree.command(name="warn", description="Варн", guild=discord.Object(id=GUILD_ID))
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):
    warns[member.id] = warns.get(member.id, 0) + 1

    await interaction.response.send_message(
        f"⚠️ {member.mention} варн ({warns[member.id]})",
        ephemeral=True
    )

    await send_log(
        interaction.guild,
        f"⚠️ WARN\nUser: {member}\nBy: {interaction.user}\nReason: {reason}\nTotal warns: {warns[member.id]}"
    )

# =====================
# RUN
# =====================
client.run(TOKEN)
