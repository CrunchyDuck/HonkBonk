import datetime
import discord
import re
import requests
from discord.ext import commands
import traceback


class ServerSpecific(commands.Cog, name="server_specific"):
    """Commands that will only work in a targeted server."""

    def __init__(self, bot):
        self.bot = bot
        self.cur = bot.cursor
        self.init_db(self.cur)

    @commands.command(name="dj")
    async def request_dj(self, ctx):
        """
        Allow a user to request the dj role.
        You must be in a VC for this to function, and no one else must have the DJ role.
        Removed when you leave the VC or after an hour.

        Example:
            c.dj
        """
        if not await self.bot.has_perm(ctx): return
        dj = ctx.guild.get_role(804454276772266034)
        if not dj:
            return

        # Check if user is in a VC.
        vs = ctx.author.voice
        vc = vs.channel
        if not vc:
            await ctx.send("You must be in a VC to request DJ.")
            return

        # Check if another user owns the DJ role.
        self.bot.cursor.execute("SELECT * FROM dj_temp")
        res = self.bot.cursor.fetchone()
        if res:
            await ctx.send(f"{self.bot.get_user(res[0]).mention} already has the DJ role.")
            return

        # Apply role.
        try:
            await ctx.author.add_roles(dj)
        except:
            traceback.print_exc()
            return

        # Create DB entry.
        time = 1  # Hard coded for now.
        end_time = self.bot.hours_from_now(time)
        time_string = self.bot.time_to_string(hours=time)
        self.bot.cursor.execute("INSERT INTO dj_temp VALUES(?, ?)", [ctx.author.id, end_time])

        await ctx.send(f"Given {ctx.author.mention} {dj.mention} for 1 hour.")

    @commands.command(name="dj.help")
    async def dj_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```Allow a user to request the dj role.
            You must be in a VC for this to function, and no one else must have the DJ role.
            Removed when you leave the VC or after an hour.

            Example:
                c.dj```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Remove the DJ role when a user leaves."""
        # check if left.
        if after.channel is not None:
            return

        # Check if in db
        self.bot.cursor.execute(f"SELECT * FROM dj_temp WHERE user_id={member.id}")
        res = self.bot.cursor.fetchone()
        if not res:
            return

        # Remove role.
        dj = before.channel.guild.get_role(804454276772266034)
        try:
            await member.remove_roles(dj, reason="DJ user left VC")
            self.cur.execute("DELETE FROM dj_temp")
            cnl = self.bot.get_channel(802620220832481315)
            await cnl.send(f"Removed dj role from {member.name} (User left channel)")
        except:
            traceback.print_exc()
            return

    def init_db(self, cursor):
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS dj_temp ("  # An entry is created for each change that is detected.
            "user_id INTEGER,"  # ID of the user
            "end_time INTEGER"  # The time this role should be removed.
            ")")
        cursor.execute("commit")

def setup(bot):
    bot.add_cog(ServerSpecific(bot))
