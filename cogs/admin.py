import datetime
import discord
import re
import requests
from discord.ext import commands


class Admin(commands.Cog, name="admin"):
    """Admin commands. Mostly just fun things for me to toy with, sometimes test, rarely useful."""
    def __init__(self, bot):
        self.bot = bot
        self.cur = bot.cursor
        self.r_only_emoji = re.compile(
            r"^((?:<:.*?:)(\d*)(?:>)|[\s])*$")  # This parses over a string and checks if it ONLY contains
        self.r_get_emoji = re.compile(r"(<:.*?:)(\d*)(>)")
        self.r_cdn = re.compile(
            r"(https://cdn.discordapp.com/attachments/.*?\.(gif|png|jpg))|(https://cdn.discordapp.com/emojis/)")  # The domain images and stuff are placed.
        self.r_cdn_filename = re.compile(r"([^/]*?(\.png|\.jpg|\.gif))")

    @commands.command(name=f"timestamp")
    async def timestamp(self, ctx):
        """
        Get the timestamp of a provided Discord Snowflake.
        Example command:
            c.timestamp 411365470109958155
        Example response:
            2018-02-09 03:39:30 UTC
        """
        if not await self.bot.has_perm(ctx, admin=False, message_on_fail=False): return
        snowflake = self.bot.get_variable(ctx.message.content, type="int")
        if not snowflake:
            await ctx.send("No snowflake found.")
            return

        await ctx.send(self.bot.date_from_snowflake(snowflake))

    @commands.command(name="echo")
    async def echo(self, ctx):
        """Repeat what it was given in Discord."""
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False): return
        await ctx.send(ctx.message.content)

    @commands.command(name="test")
    async def test(self, ctx):
        """Misc code I needed to test."""
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False): return
        await ctx.send(self.bot.date_from_snowflake(802295879549452310))

    @commands.command(name="print")
    async def print_message(self, ctx):
        """Similar to c.test, but specifically for printing values to the console."""
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False): return
        print(ctx.message.content)

    @commands.command(name="speak")
    async def speak(self, ctx):
        """
        Make the bot say something in a server. Works in the server it was called from.
        Arguments:
            channel_mention: A mention of the channel to send the message in.
            content: What to say.
        Example:
            c.speak #bots content="I have gained sapience."
        """
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False): return
        content = self.bot.get_variable(ctx.message.content, "content", type="str")

        channel = ctx.message.channel_mentions[0]
        await channel.send(content)

    @commands.command(name="bad")
    async def make_bad(self, ctx):
        """Give someone a "bad" role, which inhibits their interaction with the server."""
        for m in ctx.message.mentions:
            self.bot.banned_from_commands.append(m.id)

    @commands.command(name="dm")
    async def dm_user(self, ctx):
        """
        DM a user. An excess of spaces should be placed between the user's ID and the content to send to them.
        Arguments:
            user: The user to send the ID to.
            content: What to send to them.
        Example:
            c.dm user=630930243464462346      you're really cool
        """
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False, dm=True): return
        target = await self.bot.fetch_user(self.bot.get_variable(ctx.message.content, "user", type="int"))
        # This relies on the fact that the start of the message should ALWAYS be a fixed size.
        # If it isn't, this will go wrong.
        content = ctx.message.content[30:]

        await target.send(content)

def setup(bot):
    bot.add_cog(Admin(bot))
