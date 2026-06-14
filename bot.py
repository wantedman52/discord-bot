import discord
from discord import app_commands
import os

TOKEN = os.getenv("TOKEN")


# ⚠️ ВСТАВЬ ID СВОЕГО СЕРВЕРА СЮДА
GUILD_ID = 1431313547014701136

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# READY + SYNC
# =====================
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    try:
        await tree.sync(guild=guild)
        print("Slash commands synced (guild)")
    except Exception as e:
        print("Guild sync failed, using global sync:", e)
        await tree.sync()

    print(f"Logged in as {client.user}")

# =====================
# /help
# =====================
@tree.command(name="help", description="Показать команды")
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Команды: /help /ban /mute /warn"
    )

# =====================
# /ban
# =====================
@tree.command(name="ban", description="Забанить пользователя")
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {member} забанен. Причина: {reason}")

# =====================
# /mute (timeout)
# =====================
@tree.command(name="mute", description="Замутить пользователя на 10 минут")
@app_commands.default_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):
    await member.timeout(duration=600, reason=reason)
    await interaction.response.send_message(f"🔇 {member} замучен на 10 минут")

# =====================
# /warn
# =====================
warns = {}

@tree.command(name="warn", description="Выдать предупреждение")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "Без причины"):
    if member.id not in warns:
        warns[member.id] = 0

    warns[member.id] += 1

    await interaction.response.send_message(
        f"⚠️ {member.mention} получил варн ({warns[member.id]}). Причина: {reason}"
    )

# =====================
# RUN BOT
# =====================
client.run(TOKEN)
