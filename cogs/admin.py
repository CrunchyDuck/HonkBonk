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
        await ctx.message.add_reaction("<:caffeine:773749792865779743>")

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

    @commands.command(name="ignore")
    async def ignore_id(self, ctx):
        """
        ```Ignores a channel, category, or user.
        You can mention a category by putting its id into this structure:
        <#id_of_category>

        Arguments:
            (Required) - Requires at least one
            id: The ID to add to the list. Only 1 ID can be provided this way.
            member: A mention of the member to ignore. Can be multiple.
            channel: A mention of the text, voice or category channel to ignore. Can be multiple.

            (Optional)
            stop: Stops ignoring the given IDs.
        Example:
            c.ignore  # Ignores this channel
            c.ignore @Pidge  # Ignores a user
            c.ignore #general #nsfw #announcements # Ignores multiple channels.
            c.ignore id=704361803953733694 stop  # Stops ignoring an ID, such as a category, or a channel.```
        """
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=True): return
        server = ctx.guild.id
        message = ctx.message
        id = int(self.bot.get_variable(ctx.message.content, "id", type="int", default=0))
        stop = self.bot.get_variable(ctx.message.content, "stop", type="keyword", default=False)

        members = message.mentions
        channels = message.channel_mentions

        # Get IDs from provided values.
        id_list = []
        if id:
            id_list.append(id)
        if members:
            id_list += [x.id for x in members]
        if channels:
            id_list += [x.id for x in channels]

        if not stop:
            for id in id_list:
                self.bot.cursor.execute(f"INSERT INTO settings VALUES(?,?,?)", (server, "ignore", id))
            self.bot.cursor.execute("commit")
            await ctx.send("Ignoring IDs.")
        else:
            for id in id_list:
                self.bot.cursor.execute("DELETE FROM settings WHERE rowid IN("
                                        "SELECT rowid FROM settings WHERE value=? AND key='ignore')", (id,))
            await ctx.send("No longer ignoring IDs.")

    @commands.command(name="ignore.list")
    async def ignored_list(self, ctx):
        # TODO: This.
        pass



    @commands.command(name="ignore.help")
    async def ignore_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Ignores a channel, category, or user.
        You can mention a category by putting its id into this structure:
        <#id_of_category>

        Arguments:
            (Required) - Requires at least one
            id: The ID to add to the list. Only 1 ID can be provided this way.
            member: A mention of the member to ignore. Can be multiple.
            channel: A mention of the text, voice or category channel to ignore. Can be multiple.

            (Optional)
            stop: Stops ignoring the given IDs.
        
        Example:
            c.ignore  # Ignores this channel
            c.ignore @Pidge  # Ignores a user
            c.ignore #general #nsfw #announcements # Ignores multiple channels.
            c.ignore id=704361803953733694 stop  # Stops ignoring an ID, such as a category, or a channel.```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="dm.help")
    async def dm_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```DM a user. An excess of spaces should be placed between the user's ID and the content to send to them.
            
            Arguments:
                (Required)
                user: The user to send the ID to.
                content: What to send to them. This should be spaced far from the root command, because it makes my job easier.
            
            Example:
                c.dm user=630930243464462346      you're really cool```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="speak.help")
    async def speak_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Make the bot say something in a channel. Works in the server it was called from.
        Admin command.
        
        Arguments:
            (Required)
            channel_mention: A mention of the channel to send the message in.
            content: What to say.
            
        Example:
            c.speak #bots content="I have gained sapience."```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="timestamp.help")
    async def timestamp_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Get the timestamp of a provided Discord Snowflake. This command works in DMs.

        Example command:
            c.timestamp 411365470109958155
            
        Example response:
            2018-02-09 03:39:30 UTC```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="help")
    async def core_help(self, ctx):
        """The core help command."""
        if not await self.bot.has_perm(ctx, dm=True): return
        help_string = "```Modules:\n" \
        "c.role - Vanity roles and moderation controls.\n" \
        "c.emoji - Adding and moderating emoji.\n" \
        "c.react - Automatic reactions to messages.\n" \
        "c.room - Temporary rooms.\n" \
        "c.vc - underdeveloped VC commands.\n" \
        "\n" \
        "Core commands:\n" \
        "c.timestamp - Provides a date from a Discord ID/Snowflake.\n" \
        "c.ignore - Setting honkbonk to ignore users/channels.\n" \
        "c.speak - Makes HonkBonk say something, somewhere :).\n" \
        "c.dm - Makes HonkBonk DM a user.```"
        await ctx.send(help_string)


def setup(bot):
    bot.add_cog(Admin(bot))
