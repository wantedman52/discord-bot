import discord
from discord import app_commands
import os
import datetime
import sqlite3

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("TOKEN")

GUILD_ID = 1431313547014701136
LOG_CHANNEL_ID = 1515646304166875166
ROLE_ID = 1431319452829618326

RU_RULES_ID = 1431321162721525884
EN_RULES_ID = 1510594864226500618

if not TOKEN:
    raise RuntimeError("TOKEN missing")

# =====================
# SQLITE DB
# =====================
conn = sqlite3.connect("moderation.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    warns INTEGER DEFAULT 0,
    bans INTEGER DEFAULT 0,
    mutes INTEGER DEFAULT 0
)
""")
conn.commit()

def add_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    conn.commit()

def add_warn(uid):
    add_user(uid)
    cursor.execute("UPDATE users SET warns = warns + 1 WHERE user_id = ?", (uid,))
    conn.commit()

def add_ban(uid):
    add_user(uid)
    cursor.execute("UPDATE users SET bans = bans + 1 WHERE user_id = ?", (uid,))
    conn.commit()

def add_mute(uid):
    add_user(uid)
    cursor.execute("UPDATE users SET mutes = mutes + 1 WHERE user_id = ?", (uid,))
    conn.commit()

def get_stats(uid):
    add_user(uid)
    cursor.execute("SELECT warns, bans, mutes FROM users WHERE user_id = ?", (uid,))
    return cursor.fetchone()

# =====================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
def log(guild, text):
    if guild:
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if ch:
            return ch.send(text)

# =====================
def parse_time(t):
    try:
        n = int(t[:-1])
        u = t[-1]
        return n * {"s":1,"m":60,"h":3600,"d":86400}.get(u,0)
    except:
        return None

# =====================
# RULES BUTTONS
# =====================
class RulesView(discord.ui.View):
    @discord.ui.button(label="🇷🇺 RU Rules", style=discord.ButtonStyle.primary)
    async def ru(self, interaction, button):
        await interaction.response.send_message(f"📜 <#{RU_RULES_ID}>", ephemeral=True)

    @discord.ui.button(label="🇬🇧 EN Rules", style=discord.ButtonStyle.success)
    async def en(self, interaction, button):
        await interaction.response.send_message(f"📜 <#{EN_RULES_ID}>", ephemeral=True)

# =====================
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    try:
        await tree.sync(guild=discord.Object(id=GUILD_ID))
        print("Synced")
    except Exception as e:
        print("SYNC ERROR:", e)

# =====================
@client.event
async def on_member_join(member):
    try:
        role = member.guild.get_role(ROLE_ID)
        if role:
            await member.add_roles(role)

        ch = member.guild.get_channel(LOG_CHANNEL_ID)
        if ch:
            await ch.send(f"👋 {member.mention} joined!", view=RulesView())

        await log(member.guild, f"JOIN | {member}")
    except:
        pass

# =====================
@client.event
async def on_message(message):
    if message.author.bot:
        return
    await log(message.guild, f"MSG | {message.author}: {message.content}")

@client.event
async def on_message_delete(message):
    await log(message.guild, f"DELETE | {message.author}: {message.content}")

@client.event
async def on_message_edit(before, after):
    await log(before.guild, f"EDIT | {before.author}\n{before.content} -> {after.content}")

# =====================
# HELP
# =====================
@tree.command(name="help", guild=discord.Object(id=GUILD_ID))
async def help_cmd(interaction):
    await interaction.response.send_message("/ban /mute /warn /stats /clear", ephemeral=True)

# =====================
# BAN
# =====================
@tree.command(name="ban", guild=discord.Object(id=GUILD_ID))
async def ban(interaction, member: discord.Member, reason: str = "no reason"):
    await interaction.response.defer(ephemeral=True)

    await member.ban(reason=reason)
    add_ban(member.id)

    await log(interaction.guild, f"BAN | {member} | {reason}")
    await interaction.followup.send("banned")

# =====================
# MUTE
# =====================
@tree.command(name="mute", guild=discord.Object(id=GUILD_ID))
async def mute(interaction, member: discord.Member, time: str):
    await interaction.response.defer(ephemeral=True)

    seconds = parse_time(time)
    if not seconds:
        return await interaction.followup.send("10m / 1h / 1d")

    until = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
    await member.timeout(until)

    add_mute(member.id)

    await log(interaction.guild, f"MUTE | {member} | {time}")
    await interaction.followup.send("muted")

# =====================
# UNMUTE
# =====================
@tree.command(name="unmute", guild=discord.Object(id=GUILD_ID))
async def unmute(interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)

    await member.timeout(None)
    await log(interaction.guild, f"UNMUTE | {member}")
    await interaction.followup.send("unmuted")

# =====================
# WARN
# =====================
@tree.command(name="warn", guild=discord.Object(id=GUILD_ID))
async def warn(interaction, member: discord.Member, reason: str = "no reason"):
    await interaction.response.defer(ephemeral=True)

    add_warn(member.id)

    warns, bans, mutes = get_stats(member.id)

    await log(interaction.guild, f"WARN | {member} | {reason} | total {warns}")
    await interaction.followup.send(f"warned ({warns})")

# =====================
# STATS
# =====================
@tree.command(name="stats", guild=discord.Object(id=GUILD_ID))
async def stats(interaction, member: discord.Member):
    warns, bans, mutes = get_stats(member.id)

    await interaction.response.send_message(
        f"📊 {member}\n⚠ Warns: {warns}\n🔨 Bans: {bans}\n🔇 Mutes: {mutes}",
        ephemeral=True
    )

# =====================
# CLEAR
# =====================
@tree.command(name="clear", guild=discord.Object(id=GUILD_ID))
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction, amount: int):
    await interaction.response.defer(ephemeral=True)

    await interaction.channel.purge(limit=amount)

    await interaction.followup.send(f"deleted {amount}")

# =====================
client.run(TOKEN)
