import discord
from discord import app_commands
import os
import datetime

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("TOKEN")

GUILD_ID = 1431313547014701136
LOG_CHANNEL_ID = 1515646304166875166
ROLE_ID = 1431319452829618326

RU_RULES_ID = 1431321162721525884  # <- канал RU правил
EN_RULES_ID = 1510594864226500618  # <- канал EN правил

if not TOKEN:
    raise RuntimeError("TOKEN missing")

# =====================
# INTENTS
# =====================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# WARN STORAGE
# =====================
warns = {}

# =====================
# LOG SYSTEM
# =====================
async def log(guild, text):
    if not guild:
        return
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(text)

# =====================
# TIME PARSER
# =====================
def parse_time(t: str):
    try:
        n = int(t[:-1])
        u = t[-1]
        return n * {"s":1,"m":60,"h":3600,"d":86400}.get(u, 0)
    except:
        return None

# =====================
# RULES BUTTONS (RU / EN)
# =====================
class RulesView(discord.ui.View):
    @discord.ui.button(label="🇷🇺 RU Rules", style=discord.ButtonStyle.primary)
    async def ru(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"📜 RU Rules: <#{RU_RULES_ID}>",
            ephemeral=True
        )

    @discord.ui.button(label="🇬🇧 EN Rules", style=discord.ButtonStyle.success)
    async def en(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"📜 EN Rules: <#{EN_RULES_ID}>",
            ephemeral=True
        )

# =====================
# READY
# =====================
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    try:
        await tree.sync(guild=discord.Object(id=GUILD_ID))
        print("Commands synced")
    except Exception as e:
        print("SYNC ERROR:", e)

# =====================
# WELCOME
# =====================
@client.event
async def on_member_join(member):
    try:
        role = member.guild.get_role(ROLE_ID)
        if role:
            await member.add_roles(role)

        channel = member.guild.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(
                f"👋 Welcome {member.mention}!\n"
                "Выбери язык правил 👇",
                view=RulesView()
            )

        await log(member.guild, f"👋 JOIN | {member}")
    except:
        pass

# =====================
# MESSAGE LOG
# =====================
@client.event
async def on_message(message):
    if message.author.bot:
        return

    await log(message.guild,
        f"💬 MSG | {message.author}\n{message.content}"
    )

# =====================
# DELETE LOG
# =====================
@client.event
async def on_message_delete(message):
    await log(message.guild,
        f"🗑 DELETE | {message.author}\n{message.content}"
    )

# =====================
# EDIT LOG
# =====================
@client.event
async def on_message_edit(before, after):
    await log(before.guild,
        f"✏ EDIT | {before.author}\nBEFORE: {before.content}\nAFTER: {after.content}"
    )

# =====================
# HELP
# =====================
@tree.command(name="help", description="Help", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction):
    await interaction.response.send_message(
        "/ban /unban /mute /unmute /warn /clear",
        ephemeral=True
    )

# =====================
# BAN
# =====================
@tree.command(name="ban", description="Ban user", guild=discord.Object(id=GUILD_ID))
async def ban(interaction, member: discord.Member, reason: str = "no reason"):
    await interaction.response.defer(ephemeral=True)

    await member.ban(reason=reason)

    await log(interaction.guild,
        f"🔨 BAN | {member} | {reason}"
    )

    await interaction.followup.send("banned")

# =====================
# UNBAN
# =====================
@tree.command(name="unban", description="Unban user", guild=discord.Object(id=GUILD_ID))
async def unban(interaction, user_id: str):
    await interaction.response.defer(ephemeral=True)

    user = await client.fetch_user(int(user_id))
    await interaction.guild.unban(user)

    await log(interaction.guild,
        f"✅ UNBAN | {user}"
    )

    await interaction.followup.send("unbanned")

# =====================
# MUTE
# =====================
@tree.command(name="mute", description="Mute user", guild=discord.Object(id=GUILD_ID))
async def mute(interaction, member: discord.Member, time: str):
    await interaction.response.defer(ephemeral=True)

    seconds = parse_time(time)
    if not seconds:
        return await interaction.followup.send("10m / 1h / 1d")

    until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
    await member.timeout(until)

    await log(interaction.guild,
        f"🔇 MUTE | {member} | {time}"
    )

    await interaction.followup.send("muted")

# =====================
# UNMUTE
# =====================
@tree.command(name="unmute", description="Unmute user", guild=discord.Object(id=GUILD_ID))
async def unmute(interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)

    await member.timeout(None)

    await log(interaction.guild,
        f"🔊 UNMUTE | {member}"
    )

    await interaction.followup.send("unmuted")

# =====================
# WARN
# =====================
@tree.command(name="warn", description="Warn user", guild=discord.Object(id=GUILD_ID))
async def warn(interaction, member: discord.Member, reason: str = "no reason"):
    await interaction.response.defer(ephemeral=True)

    warns[member.id] = warns.get(member.id, 0) + 1

    await log(interaction.guild,
        f"⚠ WARN | {member} | {reason} | total {warns[member.id]}"
    )

    await interaction.followup.send(f"warned ({warns[member.id]})")

# =====================
# CLEAR
# =====================
@tree.command(name="clear", description="Clear chat", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction, amount: int):
    await interaction.response.defer(ephemeral=True)

    await interaction.channel.purge(limit=amount)

    await interaction.followup.send(f"deleted {amount}")

# =====================
client.run(TOKEN)
