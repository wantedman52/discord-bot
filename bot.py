import discord
from discord import app_commands
import os
import datetime

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
def parse_time(t: str):
    try:
        t = t.lower()
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
# READY (ONLY SYNC GUILD)
# =====================
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    # ❗ ТОЛЬКО sync, НИЧЕГО НЕ УДАЛЯЕМ
    await tree.sync(guild=guild)

    print(f"Logged in as {client.user}")
    print("Guild commands synced ONLY")

# =====================
# HELP (виден везде где открыт бот, но НЕ глобальный command)
# =====================
@tree.command(name="help", description="Команды", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "/mute /ban /warn /unmute",
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

    await interaction.response.send_message(f"🔇 Мут: {member} на {time}", ephemeral=True)

# =====================
# BAN
# =====================
@tree.command(name="ban", description="Бан", guild=discord.Object(id=GUILD_ID))
async def ban(interaction: discord.Interaction, member: discord.Member):

    if not is_admin(interaction):
        return await interaction.response.send_message("❌ Нет прав", ephemeral=True)

    await member.ban()

    await interaction.response.send_message("🔨 Забанен", ephemeral=True)

client.run(TOKEN)
