import discord
import os
import asyncio

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1431313547014701136  # твой сервер

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    guild = discord.Object(id=GUILD_ID)

    # 💥 1. УДАЛЯЕМ GLOBAL (ЛС) команды
    try:
        tree.clear_commands()   # global
        await tree.sync()
        print("Global commands cleared")
    except Exception as e:
        print("Global clear error:", e)

    # 💥 2. УБЕЖДАЕМСЯ ЧТО SERVER НЕ ЛОМАЕМ
    try:
        await tree.sync(guild=guild)
        print("Guild commands synced")
    except Exception as e:
        print("Guild sync error:", e)

    # 💥 выключаем бота после ресета
    await asyncio.sleep(2)
    await client.close()

client.run(TOKEN)
