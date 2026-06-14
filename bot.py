import discord
from discord import app_commands
import os
import datetime
import sqlite3
from collections import defaultdict
import time

# =====================
# TOKEN
# =====================
TOKEN = os.getenv("TOKEN")
GUILD_ID = 1431313547014701136

# =====================
# IDS
# =====================
RU_ROLE_ID = 1515772029893218445
EN_ROLE_ID = 1515771862464991413

RU_RULES_CHANNEL_ID = 1431321162721525884
EN_RULES_CHANNEL_ID = 1510594864226500618

# 🔥 ГЛОБАЛ ЛОГ
LOG_CHANNEL_ID = 1515646304166875166

# 🎫 ТИКЕТ ЛОГ ОТДЕЛЬНО
TICKET_LOG_CHANNEL_ID = 1515646304166875166
TICKET_CATEGORY_ID = 1515775223243345971

STAFF_ROLE_ID = 1431682224498933802

# =====================
# INTENTS
# =====================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# LOG FUNCTION
# =====================
async def log(guild, text):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(f"📌 {text}")

async def ticket_log(guild, text):
    ch = guild.get_channel(TICKET_LOG_CHANNEL_ID)
    if ch:
        await ch.send(f"🎫 {text}")

# =====================
# DATABASE (STATS)
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

def ensure(uid):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    conn.commit()

def add_warn(uid):
    ensure(uid)
    cursor.execute("UPDATE users SET warns = warns + 1 WHERE user_id = ?", (uid,))
    conn.commit()

def add_ban(uid):
    ensure(uid)
    cursor.execute("UPDATE users SET bans = bans + 1 WHERE user_id = ?", (uid,))
    conn.commit()

def add_mute(uid):
    ensure(uid)
    cursor.execute("UPDATE users SET mutes = mutes + 1 WHERE user_id = ?", (uid,))
    conn.commit()

def get_stats(uid):
    ensure(uid)
    cursor.execute("SELECT warns, bans, mutes FROM users WHERE user_id = ?", (uid,))
    return cursor.fetchone()

# =====================
# RULES
# =====================
class RulesView(discord.ui.View):

    @discord.ui.button(label="🇷🇺 RU", style=discord.ButtonStyle.primary)
    async def ru(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(RU_ROLE_ID)
        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"RU rules: <#{RU_RULES_CHANNEL_ID}>",
            ephemeral=True
        )

    @discord.ui.button(label="🇬🇧 EN", style=discord.ButtonStyle.success)
    async def en(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(EN_ROLE_ID)
        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"EN rules: <#{EN_RULES_CHANNEL_ID}>",
            ephemeral=True
        )

# =====================
# TICKETS
# =====================
class CloseTicketView(discord.ui.View):

    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        staff = interaction.guild.get_role(STAFF_ROLE_ID)

        if staff not in interaction.user.roles:
            return await interaction.response.send_message("❌ Staff only", ephemeral=True)

        await interaction.response.send_message("Closing...")

        await ticket_log(
            interaction.guild,
            f"CLOSED | {interaction.channel.name} | by {interaction.user}"
        )

        await interaction.channel.delete()

class TicketView(discord.ui.View):

    @discord.ui.button(label="🎫 Create ticket", style=discord.ButtonStyle.green)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):

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

        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            category=category,
            overwrites=overwrites
        )

        staff_ping = staff.mention if staff else "STAFF"

        await channel.send(
            f"🎫 Ticket from {user.mention}\n{staff_ping}",
            view=CloseTicketView()
        )

        await ticket_log(guild, f"CREATED | {user} | {channel.mention}")

        await interaction.response.send_message(
            f"Created {channel.mention}",
            ephemeral=True
        )

# =====================
# MODERATION
# =====================
@tree.command(name="ban", guild=discord.Object(id=GUILD_ID))
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):

    await member.ban(reason=reason)
    add_ban(member.id)

    await log(interaction.guild, f"BAN | {member} | {reason}")
    await interaction.response.send_message("banned", ephemeral=True)


@tree.command(name="warn", guild=discord.Object(id=GUILD_ID))
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):

    add_warn(member.id)
    s = get_stats(member.id)

    await log(interaction.guild, f"WARN | {member} | {reason} | total {s[0]}")
    await interaction.response.send_message(f"warned ({s[0]})", ephemeral=True)


@tree.command(name="stats", guild=discord.Object(id=GUILD_ID))
async def stats(interaction: discord.Interaction, member: discord.Member):

    s = get_stats(member.id)

    await interaction.response.send_message(
        f"Stats:\nWarns: {s[0]}\nBans: {s[1]}\nMutes: {s[2]}",
        ephemeral=True
    )

# =====================
# READY
# =====================
@client.event
async def on_ready():
    print(f"READY: {client.user}")
    await tree.sync(guild=discord.Object(id=GUILD_ID))

# =====================
# JOIN
# =====================
@client.event
async def on_member_join(member):

    ch = member.guild.system_channel
    if ch:
        await ch.send("Choose language:", view=RulesView())

# =====================
# RUN
# =====================
client.run(TOKEN)
