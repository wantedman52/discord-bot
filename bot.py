import discord
from discord import app_commands
import os

TOKEN = os.getenv("TOKEN")

GUILD_ID = 1431313547014701136

# =====================
# IDs (ЗАПОЛНИ САМ)
# =====================
RU_ROLE_ID = 1515772029893218445
EN_ROLE_ID = 1515771862464991413

RU_RULES_CHANNEL_ID = 1431321162721525884
EN_RULES_CHANNEL_ID = 1510594864226500618

# =====================
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# =====================
# RULES VIEW
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
@client.event
async def on_ready():
    try:
        await tree.sync(guild=discord.Object(id=GUILD_ID))
        print("Bot ready")
    except Exception as e:
        print(e)

# =====================
# RULES COMMAND
# =====================
@tree.command(name="rules", description="RU / EN rules", guild=discord.Object(id=GUILD_ID))
async def rules(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Выбери язык / Choose language:",
        view=RulesView()
    )

# =====================
# JOIN MESSAGE (OPTIONAL)
# =====================
@client.event
async def on_member_join(member):
    channel = member.guild.system_channel

    if channel:
        await channel.send(
            "📜 Выберите язык правил / Choose rules language:",
            view=RulesView()
        )

# =====================
client.run(TOKEN)
