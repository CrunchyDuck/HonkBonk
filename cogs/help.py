from discord.ext import commands
import discord
import re


# TODO: This.
# IDEA: Make HonkBonk capable of procedurally creating the description for channels based off of their channel stuff?
class HelpCommands(commands.Cog):
	# This command has no prefix, as it takes the prefix of whatever command it's attached to.

	def __init__(self, bot):
		self.bot = bot
		for active_cog in self.bot.active_cogs:
			cog = self.bot.get_cog(active_cog)
			if cog == None:
				print(f"Could not find cog {active_cog}")
				continue
			#print([c.name for c in cog.get_commands()])


def setup(bot):
	bot.add_cog(HelpCommands(bot))
