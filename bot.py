import discord
from discord import app_commands
import os

TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# READY
# =====================
@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")

# =====================
# /help
# =====================
@tree.command(name="help", description="Показать команды бота")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "/help, /ban, /mute, /warn"
    )

# =====================
# /ban
# =====================
@tree.command(name="ban", description="Забанить пользователя")
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"{member} забанен. Причина: {reason}")

# =====================
# /mute (простая версия)
# =====================
@tree.command(name="mute", description="Мут пользователя (без роли)")
@app_commands.default_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):
    try:
        await member.timeout(duration=60*10, reason=reason)
        await interaction.response.send_message(f"{member} замучен на 10 минут")
    except:
        await interaction.response.send_message("Не получилось замутить")

# =====================
# /warn (простая версия)
# =====================
warns = {}

@tree.command(name="warn", description="Выдать предупреждение")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):
    if member.id not in warns:
        warns[member.id] = 0

    warns[member.id] += 1

    await interaction.response.send_message(
        f"{member.mention} получил варн ({warns[member.id]}). Причина: {reason}"
    )

# =====================
# RUN
# =====================
client.run(TOKEN)
