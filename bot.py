import os
from discord.ext import commands
from dotenv import load_dotenv
from asyncio import sleep
import random
import re
import threading
import time
import asyncio
import math

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
myID = int(os.getenv("OWNER_ID")) # The ID of my account. Certain commands can only be run by me.

honkBonk = commands.Bot("owo~") # Commands in chat should be prefixed with this.


helpDict = {
	"save_history": "Creates a .txt file containing Discord-like formatting of messages. Only CrunchyDuck can use this. It takes a while and uses my hard-drive space :)",
	"cls": "Clears all messages that the bot has sent in this channel or DM.",
	"here_info": "Provides information about the location the message was sent.",
	"say_garbage": "Spams garbage [number] of times. Testing command, mostly.",
	"purge_until": "Purges all messages until it reaches the limit, or finds the message that matches the string given.\nSetting either value to 0 will omit this check."
}



@honkBonk.event
async def on_ready():
	print(f"{honkBonk.user.name} has connected to Discord.")



####################
### Bot Commands ###
####################

@honkBonk.command(name="save_history", help=helpDict["save_history"])
async def save_history(ctx, amount:int=50, oldest:bool=True):
	"""TODO:
	Save to a file.
	Find a way to display the messages in a Discord-like format (Maybe HTML stored as XML?)

	"""
	if not isCrunchy(ctx):
		return


	async for message in ctx.history(limit=amount, oldest_first=oldest):
		# Save attached files
		for att in message.attachments:
			try:
				await att.save(f"{att.id}_{att.filename}")
			except (discord.NotFound, discord.HTTPException) as e:
				print(f"==Attachment Error==\nMessage snowflake: {message.id}\nError: {e}")

		# Save message content. Right now just prints it until I decide on a storage format.
		m_t = message.created_at # Datetime object
		m_date = f"{m_t.day}/{m_t.month}/{m_t.year}"
		m_time = f"{m_t.hour}:{m_t.minute}:{m_t.second}"

		print(f"{message.author} {m_time} {m_date}\n{message.content}") # Discord-like formatting.


@honkBonk.command(name="here_info", help=helpDict["here_info"])
async def thisInfo(ctx):
	m = ctx.message
	await m.author.create_dm()
	await m.author.dm_channel.send(
		f"""At `{m.created_at}` user `{m.author}` in `{m.guild}` in `{m.channel}` said:\n`{m.content}`"""
	)


@honkBonk.command(name="cls", help=helpDict["cls"])
async def deleteMessages(ctx):
	"""TODO:
	Provide options for narrowing down the search, E.G X messages, only after X time, etc.
	Allow the deleting of bot command requests, so the message someone sends to issue a command.
	"""
	if ctx.guild == None: # Should always allow someone to delete if in a DM.
		pass
	elif not isCrunchy(ctx): # Only I can delete messages in a server >:)
		await ctx.send("no. Unless CrunchyDuck, will only clear DM messages.")
		return

	await ctx.send("yes sir")
	await sleep(2) # To give them time to read the message.


	msg = await ctx.channel.history().get(author__id=honkBonk.user.id) # Get the most recent message. None if there's no more messages.
	while msg != None:
		await msg.delete()
		msg = await ctx.channel.history().get(author__id=honkBonk.user.id) # Get most recent message.


@honkBonk.command(name="say_garbage", help=helpDict["say_garbage"])
async def sayGarbage(ctx, number:int=2):
	for i in range(number):
		await ctx.send("nya")


# Dev commands
@honkBonk.command(name="read_me")
async def read_message(ctx):
	if not isCrunchy(ctx):
		return

	for att in ctx.message.attachments:
		print(att.id)



def isCrunchy(m):
	"""Checks if the message wa sent by me, CrunchyDuck."""
	return m.author.id == myID

def isMe(m):
	"""Checks if the person who sent this message is this bot, HonkBonk."""
	return m.author == honkBonk.user


# Blocking call.
honkBonk.run(TOKEN)