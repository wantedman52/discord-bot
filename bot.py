import discord
from discord import app_commands
import os
import datetime

TOKEN = os.getenv("TOKEN")

GUILD_ID = 1431313547014701136

# 👉 ВСТАВЬ СЮДА ID ЛОГ КАНАЛА
LOG_CHANNEL_ID = 1515646304166875166

# 👉 ВСТАВЬ СЮДА ID РОЛИ "Игрок"
ROLE_ID = 1431319452829618326

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# TIME PARSER
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

# =====================
# LOGS
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

    try:
        await tree.sync(guild=guild)
        print("Guild commands synced")
    except Exception as e:
        print("Sync error:", e)

    print(f"Logged in as {client.user}")

# =====================
# AUTO ROLE
# =====================
@client.event
async def on_member_join(member: discord.Member):
    role = member.guild.get_role(ROLE_ID)

    if role:
        await member.add_roles(role)

        await send_log(member.guild,
            f"👋 JOIN | {member} получил роль {role.name}"
        )

# =====================
# HELP
# =====================
@tree.command(name="help", description="Команды", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "/ban /unban /mute /unmute /warn /clear",
        ephemeral=True
    )

# =====================
# BAN
# =====================
@tree.command(name="ban", description="Бан", guild=discord.Object(id=GUILD_ID))
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):
    await member.ban(reason=reason)

    await interaction.response.send_message("🔨 banned", ephemeral=True)

    await send_log(interaction.guild,
        f"🔨 BAN | {member} | by {interaction.user} | {reason}"
    )

# =====================
# UNBAN
# =====================
@tree.command(name="unban", description="Разбан", guild=discord.Object(id=GUILD_ID))
async def unban(interaction: discord.Interaction, user_id: str):
    user = await client.fetch_user(int(user_id))
    await interaction.guild.unban(user)

    await interaction.response.send_message("✅ unbanned", ephemeral=True)

    await send_log(interaction.guild,
        f"✅ UNBAN | {user_id} | by {interaction.user}"
    )

# =====================
# MUTE
# =====================
@tree.command(name="mute", description="Мут с временем", guild=discord.Object(id=GUILD_ID))
async def mute(interaction: discord.Interaction, member: discord.Member, time: str):
    seconds = parse_time(time)

    if not seconds:
        return await interaction.response.send_message("❌ 10m / 1h / 1d", ephemeral=True)

    until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
    await member.timeout(until)

    await interaction.response.send_message("🔇 muted", ephemeral=True)

    await send_log(interaction.guild,
        f"🔇 MUTE | {member} | by {interaction.user} | {time}"
    )

# =====================
# UNMUTE
# =====================
@tree.command(name="unmute", description="Снять мут", guild=discord.Object(id=GUILD_ID))
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)

    await interaction.response.send_message("🔊 unmuted", ephemeral=True)

    await send_log(interaction.guild,
        f"🔊 UNMUTE | {member} | by {interaction.user}"
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

    await send_log(interaction.guild,
        f"⚠️ WARN | {member} | by {interaction.user} | {reason} | total {warns[member.id]}"
    )

# =====================
# CLEAR CHAT
# =====================
@tree.command(name="clear", description="Очистка чата", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.channel.purge(limit=amount)

    await interaction.response.send_message(
        f"🧹 Удалено {amount} сообщений",
        ephemeral=True
    )

client.run(TOKEN)
