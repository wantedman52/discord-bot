import discord
from discord import app_commands
import os
import sqlite3
from collections import defaultdict
import datetime

# =====================
TOKEN = os.getenv("TOKEN")
GUILD_ID = 1431313547014701136

# =====================
# IDS
# =====================
RU_ROLE_ID = 1515772029893218445
EN_ROLE_ID = 1515771862464991413

LOG_CHANNEL_ID = 1515646304166875166

TICKET_LOG_CHANNEL_ID = 1515646304166875166
TICKET_CATEGORY_ID = 1515775223243345971

# 👉 КАНАЛ ГДЕ БУДЕТ КНОПКА ТИКЕТОВ
TICKET_PANEL_CHANNEL_ID = 1515775278087934106

STAFF_ROLE_ID = 1431682224498933802

# =====================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# LOG
# =====================
async def log(guild, text):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(f"📌 {text}")

async def tlog(guild, text):
    ch = guild.get_channel(TICKET_LOG_CHANNEL_ID)
    if ch:
        await ch.send(f"🎫 {text}")

# =====================
# DATABASE
# =====================
conn = sqlite3.connect("data.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    warns INTEGER DEFAULT 0,
    bans INTEGER DEFAULT 0,
    mutes INTEGER DEFAULT 0
)
""")
conn.commit()

def ensure(uid):
    cur.execute("INSERT OR IGNORE INTO users VALUES (?,0,0,0)", (uid,))
    conn.commit()

def add_warn(uid):
    ensure(uid)
    cur.execute("UPDATE users SET warns = warns + 1 WHERE user_id = ?", (uid,))
    conn.commit()

def remove_warn(uid):
    ensure(uid)
    cur.execute("UPDATE users SET warns = MAX(warns-1,0) WHERE user_id = ?", (uid,))
    conn.commit()

def add_ban(uid):
    ensure(uid)
    cur.execute("UPDATE users SET bans = bans + 1 WHERE user_id = ?", (uid,))
    conn.commit()

def add_mute(uid):
    ensure(uid)
    cur.execute("UPDATE users SET mutes = mutes + 1 WHERE user_id = ?", (uid,))
    conn.commit()

def get_stats(uid):
    ensure(uid)
    cur.execute("SELECT warns,bans,mutes FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

# =====================
# RULES BUTTONS
# =====================
class Rules(discord.ui.View):

    @discord.ui.button(label="🇷🇺 RU", style=discord.ButtonStyle.primary)
    async def ru(self, interaction, button):

        role = interaction.guild.get_role(RU_ROLE_ID)
        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message("RU rules added", ephemeral=True)

    @discord.ui.button(label="🇬🇧 EN", style=discord.ButtonStyle.success)
    async def en(self, interaction, button):

        role = interaction.guild.get_role(EN_ROLE_ID)
        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message("EN rules added", ephemeral=True)

# =====================
# TICKETS
# =====================
class CloseTicket(discord.ui.View):

    @discord.ui.button(label="🔒 Close ticket", style=discord.ButtonStyle.red)
    async def close(self, interaction, button):

        staff = interaction.guild.get_role(STAFF_ROLE_ID)

        if staff not in interaction.user.roles:
            return await interaction.response.send_message("Only staff", ephemeral=True)

        await tlog(interaction.guild, f"CLOSED | {interaction.channel.name} | {interaction.user}")
        await interaction.channel.delete()


class TicketPanel(discord.ui.View):

    @discord.ui.button(label="🎫 Create ticket", style=discord.ButtonStyle.green)
    async def create(self, interaction, button):

        guild = interaction.guild
        user = interaction.user

        for ch in guild.channels:
            if ch.name == f"ticket-{user.id}":
                return await interaction.response.send_message("Already have ticket", ephemeral=True)

        category = guild.get_channel(TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        staff = guild.get_role(STAFF_ROLE_ID)
        if staff:
            overwrites[staff] = discord.PermissionOverwrite(view_channel=True)

        ch = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            category=category,
            overwrites=overwrites
        )

        await ch.send(
            f"🎫 Ticket created by {user.mention}\n<@&{STAFF_ROLE_ID}>",
            view=CloseTicket()
        )

        await tlog(guild, f"OPENED | {user} | {ch.mention}")

        await interaction.response.send_message(f"Created {ch.mention}", ephemeral=True)

# =====================
# MODERATION
# =====================
@tree.command(name="ban", guild=discord.Object(id=GUILD_ID))
async def ban(interaction, member: discord.Member, reason: str = "no reason"):
    await member.ban(reason=reason)
    add_ban(member.id)
    await log(interaction.guild, f"BAN | {member} | {reason}")
    await interaction.response.send_message("banned", ephemeral=True)


@tree.command(name="mute", guild=discord.Object(id=GUILD_ID))
async def mute(interaction, member: discord.Member, minutes: int):
    until = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
    await member.timeout(until)
    add_mute(member.id)
    await log(interaction.guild, f"MUTE | {member} | {minutes}m")
    await interaction.response.send_message("muted", ephemeral=True)


@tree.command(name="warn", guild=discord.Object(id=GUILD_ID))
async def warn(interaction, member: discord.Member):
    add_warn(member.id)
    s = get_stats(member.id)
    await log(interaction.guild, f"WARN | {member} | total {s[0]}")
    await interaction.response.send_message(f"warned ({s[0]})", ephemeral=True)


@tree.command(name="removewarn", guild=discord.Object(id=GUILD_ID))
async def removewarn(interaction, member: discord.Member):
    remove_warn(member.id)
    s = get_stats(member.id)
    await log(interaction.guild, f"REMOVE WARN | {member}")
    await interaction.response.send_message(f"now {s[0]}", ephemeral=True)

# =====================
# STATS
# =====================
@tree.command(name="stats", guild=discord.Object(id=GUILD_ID))
async def stats(interaction, member: discord.Member):
    s = get_stats(member.id)
    await interaction.response.send_message(f"W:{s[0]} B:{s[1]} M:{s[2]}", ephemeral=True)

# =====================
# READY → AUTO TICKET PANEL
# =====================
@client.event
async def on_ready():
    print("Bot ready")

    await tree.sync(guild=discord.Object(id=GUILD_ID))

    channel = client.get_channel(TICKET_PANEL_CHANNEL_ID)

    if channel:
        await channel.send(
            "🎫 **Support Tickets**\nClick button to create ticket:",
            view=TicketPanel()
        )

# =====================
client.run(TOKEN)
