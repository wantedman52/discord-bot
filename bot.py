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
# ROLES / CHANNELS
# =====================
RU_ROLE_ID = 1515772029893218445
EN_ROLE_ID = 1515771862464991413

RU_RULES_CHANNEL_ID = 1431321162721525884
EN_RULES_CHANNEL_ID = 1510594864226500618

LOG_CHANNEL_ID = 1515646304166875166

# TICKETS
TICKET_CATEGORY_ID = 1515775223243345971
TICKET_LOG_CHANNEL_ID = 1515775278087934106
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
# ANTIFLOOD
# =====================
spam = defaultdict(list)

# =====================
# SIMPLE LOG
# =====================
async def log(guild, text):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(f"📌 {text}")

# =====================
# DATABASE (можно расширить позже)
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
# RULES VIEW (ТВОЙ КОД + УЛУЧШЕНИЕ)
# =====================
class RulesView(discord.ui.View):

    @discord.ui.button(label="🇷🇺 Русский", style=discord.ButtonStyle.primary)
    async def ru(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(RU_ROLE_ID)
        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"📜 RU правила: <#{RU_RULES_CHANNEL_ID}>",
            ephemeral=True
        )

    @discord.ui.button(label="🇬🇧 English", style=discord.ButtonStyle.success)
    async def en(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(EN_ROLE_ID)
        if role:
            await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"📜 EN rules: <#{EN_RULES_CHANNEL_ID}>",
            ephemeral=True
        )

# =====================
# TICKET SYSTEM
# =====================
class CloseTicketView(discord.ui.View):

    @discord.ui.button(label="🔒 Close ticket", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        staff = interaction.guild.get_role(STAFF_ROLE_ID)

        if staff not in interaction.user.roles:
            return await interaction.response.send_message(
                "❌ Only staff can close tickets",
                ephemeral=True
            )

        await interaction.response.send_message("Closing ticket...")

        ch = interaction.guild.get_channel(TICKET_LOG_CHANNEL_ID)
        if ch:
            await ch.send(f"🔒 Closed: {interaction.channel.name} by {interaction.user}")

        await interaction.channel.delete()

class TicketView(discord.ui.View):

    @discord.ui.button(label="🎫 Create ticket", style=discord.ButtonStyle.green)
    async def create(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        for ch in guild.channels:
            if ch.name == f"ticket-{user.id}":
                return await interaction.response.send_message(
                    "❌ You already have a ticket",
                    ephemeral=True
                )

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

        await channel.send(
            f"🎫 Ticket opened by {user.mention}",
            view=CloseTicketView()
        )

        logch = guild.get_channel(TICKET_LOG_CHANNEL_ID)
        if logch:
            await logch.send(f"🎫 Ticket opened: {channel.mention} by {user}")

        await interaction.response.send_message(
            f"Created: {channel.mention}",
            ephemeral=True
        )

# =====================
@client.event
async def on_ready():
    print(f"Bot ready: {client.user}")
    await tree.sync(guild=discord.Object(id=GUILD_ID))

# =====================
# JOIN MESSAGE + RULES
# =====================
@client.event
async def on_member_join(member):
    ch = member.guild.system_channel

    if ch:
        await ch.send(
            "📜 Choose language / Выберите язык:",
            view=RulesView()
        )

# =====================
# ANTIFLOOD + LOG MSG
# =====================
@client.event
async def on_message(message):
    if message.author.bot:
        return

    now = time.time()
    spam[message.author.id].append(now)
    spam[message.author.id] = [t for t in spam[message.author.id] if now - t < 5]

    if len(spam[message.author.id]) > 5:
        await message.delete()
        await log(message.guild, f"FLOOD | {message.author}")
        return

    await log(message.guild, f"MSG | {message.author}: {message.content}")

# =====================
# RULES COMMAND
# =====================
@tree.command(name="rules", description="RU/EN rules", guild=discord.Object(id=GUILD_ID))
async def rules(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Choose language:",
        view=RulesView()
    )

# =====================
# TICKET COMMAND
# =====================
@tree.command(name="ticket", description="Support tickets", guild=discord.Object(id=GUILD_ID))
async def ticket(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🎫 Support:",
        view=TicketView()
    )

# =====================
client.run(TOKEN)
