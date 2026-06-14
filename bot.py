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
# ADMIN CHECK
# =====================
def is_admin(interaction: discord.Interaction):
    return interaction.guild is not None and interaction.user.guild_permissions.administrator

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
# CLEAR OLD GLOBAL COMMANDS + SYNC ONLY GUILD
# =====================
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    try:
        # ❗ ВАЖНО: удаляем ВСЕ старые глобальные команды
        tree.clear_commands()

        # синк только на сервер
        await tree.sync(guild=guild)

        print("✅ Old global commands removed")
        print("✅ Guild commands synced")

    except Exception as e:
        print("Sync error:", e)

    print(f"Logged in as {client.user}")

# =====================
# HELP (ONLY GUILD BUT CAN BE SEEN ANYWHERE IF OPENED)
# =====================
@tree.command(name="help", description="Команды", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction: discord.Interaction):

    await interaction.response.send_message(
        "📌 /mute /ban /warn /unmute /unban",
        ephemeral=True
    )

# =====================
# MUTE
# =====================
@tree.command(name="mute", description="Мут", guild=discord.Object(id=GUILD_ID))
async def mute(interaction: discord.Interaction, member: discord.Member, time: str, reason: str = "Без причины"):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Нет прав", ephemeral=True)

    seconds = parse_time(time)

    if not seconds:
        return await interaction.response.send_message("❌ Формат: 10m / 1h / 1d", ephemeral=True)

    until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)

    await member.timeout(until, reason=reason)

    await interaction.response.send_message(f"🔇 {member} мут на {time}", ephemeral=True)

# =====================
# UNMUTE
# =====================
@tree.command(name="unmute", description="Снять мут", guild=discord.Object(id=GUILD_ID))
async def unmute(interaction: discord.Interaction, member: discord.Member):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Нет прав", ephemeral=True)

    await member.timeout(None)

    await interaction.response.send_message("🔊 Размучен", ephemeral=True)

# =====================
# BAN
# =====================
@tree.command(name="ban", description="Бан", guild=discord.Object(id=GUILD_ID))
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Нет прав", ephemeral=True)

    await member.ban(reason=reason)

    await interaction.response.send_message(f"🔨 {member} забанен", ephemeral=True)

# =====================
# RUN
# =====================
client.run(TOKEN)
