import discord
from discord import app_commands
import os
import datetime

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise RuntimeError("TOKEN is missing in environment variables")

GUILD_ID = 1431313547014701136
LOG_CHANNEL_ID = 1515646304166875166
ROLE_ID = 1431319452829618326

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)

# ✔ FIX: tree через client.tree (правильный способ)
tree = client.tree


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


async def send_log(guild, text):
    if not guild:
        return

    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(text)


# =====================
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    try:
        guild = discord.Object(id=GUILD_ID)
        await tree.sync(guild=guild)
        print("Commands synced")
    except Exception as e:
        print("SYNC ERROR:", e)


# =====================
@client.event
async def on_member_join(member: discord.Member):
    try:
        role = member.guild.get_role(ROLE_ID)
        if role:
            await member.add_roles(role)

            await send_log(
                member.guild,
                f"👋 JOIN | {member}"
            )
    except Exception as e:
        print("JOIN ERROR:", e)


# =====================
@tree.command(name="help", description="Команды")
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "/ban /unban /mute /unmute /warn /clear",
        ephemeral=True
    )


# =====================
@tree.command(name="ban", description="Бан")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):
    await interaction.response.defer(ephemeral=True)

    await member.ban(reason=reason)

    await send_log(interaction.guild,
        f"🔨 BAN | {member} | {reason}"
    )

    await interaction.followup.send("banned")


# =====================
@tree.command(name="warn", description="Варн")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "no reason"):

    await interaction.response.defer(ephemeral=True)

    await send_log(interaction.guild,
        f"⚠️ WARN | {member} | {reason}"
    )

    await interaction.followup.send("warned")


# =====================
@tree.command(name="clear", description="Очистка")
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):

    await interaction.response.defer(ephemeral=True)

    await interaction.channel.purge(limit=amount)

    await interaction.followup.send(f"deleted {amount}")


# =====================
client.run(TOKEN)
