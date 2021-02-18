import discord
import re
from discord.ext import commands
from discord.voice_client import opus
import os
from pytube import YouTube
import traceback


# TODO: Allow HB to play music from youtube, like bots such as Rythm. [in progress]
# IDEA: Global volume control option to manually boost/lower a song.
# IDEA: Automatic gain control, based on the peaks of a song.
# IDEA: Give HB a bunch of voice clips he's capable of remotely playing, so I can harass people at range.
class VoiceChannels(commands.Cog, name="voice_channels"):
    prefix = "vc"

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=f"{prefix}.join")
    async def join_voice_channel(self, ctx):
        """Join the VC channel the user is currently in."""
        if not await self.bot.has_perm(ctx, admin=True): return
        voice = ctx.author.voice
        cnl_variable = self.bot.get_variable(ctx.message.content, "cnl", "int")

        if voice and voice.channel:
            channel = voice.channel
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True, self_mute=True)
            return
        elif cnl_variable:
            channel = voice.channel
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True, self_mute=True)
        else:
            await ctx.send("You're not in a voice channel, orokana baaaaaka")
            return

    @commands.command(name=f"{prefix}.leave")
    async def leave_voice_channel(self, ctx):
        """Leave the voice channel the bot is in, within this server."""
        if not await self.bot.has_perm(ctx, admin=True): return
        await ctx.guild.change_voice_state(channel=None, self_deaf=True, self_mute=True)
        return

    @commands.command(name=f"{prefix}.help")
    async def vc_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```c.vc.join - Join your channel
        c.vc.leave - Leave currently joined channel```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.join.help")
    async def join_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Join the VC channel you're in, or the mentioned channel
        
        Arguments:
            cnl: The vc channel ID to join
        
        Examples:
            c.vc.join
            c.vc.join cnl=773744358934446080```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.leave.help")
    async def leave_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```Leave the currently joined vc.

            Example:
                c.vc.leave```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="sleep.help")
    async def sleep_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
                ```Allows the user to specify a time, after which they will be automatically removed from their current VC.
                Admins can mention a user to set a timer for them.

                Arguments:
                    time: The amount of time to wait before removing a user, in minutes. Defaults to 30 minutes.
                Examples:
                    c.sleep 
                    c.sleep time=45 @pip```
                """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"sleep")
    async def sleep_timer(self, ctx):
        if not await self.bot.has_perm(ctx): return False
        """
        Allows the user to specify a time, after which they will be automatically removed from their current VC.
        Admins can mention a user to set a timer for them.

        Arguments:
            time: The amount of time to wait before removing a user, in minutes. Defaults to 30 minutes.
        Examples:
            c.sleep
            c.sleep time=45
        """
        message = ctx.message
        content = message.content
        time = float(self.bot.get_variable(content, "time", type="float", default=30))
        user = self.bot.admin_override(ctx)

        # Checks if user is in a VC.
        voice = user.voice
        if voice:
            channel = voice.channel
        else:
            if user == ctx.author:
                await ctx.send("Join a voice channel before using this command.")
                return
            else:
                await ctx.send("The mentioned user must be in a voice channel.")
                return

        # Check if there's already an entry in the database for this user
        self.bot.cursor.execute(
            f"SELECT rowid, * FROM sleep_timer WHERE"
            f" user_id={user.id} AND server={ctx.guild.id}")
        result = self.bot.cursor.fetchone()

        if time > 0:
            time = (max(min(1440, time), 0.016)) / 60  # Limit to 1 day or 1 second. Also converts from the given minutes to hours.
            end_time = self.bot.hours_from_now(time)
            time_string = self.bot.time_to_string(hours=time)

            if result:  # Update existing entry.
                self.bot.cursor.execute(f"UPDATE sleep_timer SET end_time={end_time} WHERE rowid={result[0]}")
            else:  # Create entry.
                self.bot.cursor.execute(
                    f"INSERT INTO sleep_timer VALUES({ctx.guild.id}, {user.id}, {end_time})")
            self.bot.cursor.execute("commit")

            await ctx.send(f"{user.name} will automatically be removed from VC in {time_string}.")
        else:
            await ctx.send("Provided time must be above 0.")
            return

        try:
            self.bot.cursor.execute("commit")
        except:
            pass

    def init_db(self, cursor):
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS sleep_timer ("  # An entry is created for each change that is detected.
            "server INTEGER,"  # ID of the server
            "user_id INTEGER,"  # ID of the user
            "end_time INTEGER"  # The time the user should be removed from the VC.
            ")")
        cursor.execute("commit")


def setup(bot):
    bot.add_cog(VoiceChannels(bot))