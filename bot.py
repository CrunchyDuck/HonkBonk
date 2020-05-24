import os
import discord
from dotenv import load_dotenv
from asyncio import sleep
import random
import re

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = int(os.getenv("DISCORD_GUILD"))

client = discord.Client() # I thought long and hard about whether to use "bot" or "client" (a couple minutes.).
	# I decided to use client because I don't like having my hand held constantly.
#re_p_derg = re.compile(r'(d+e+r+g+)')

@client.event
async def on_ready():
	print(f"{client.user.name} has connected to Discord.")


client.run(TOKEN)
