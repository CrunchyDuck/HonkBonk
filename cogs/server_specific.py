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

    @commands.command(name="dj.help")
    async def dj_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Allow a user to gift the DJ role to another user or request it for themselves.
        You must be in VC to gain the role. If gifting, you must own the role already and the mentioned user must be in VC.
        Removed when you leave the VC or after an hour.

        Arguments:
            (Optional)
            user: The user to gift the DJ role to. This can be provided as an argument of their ID, or as a mention.
            
        Examples:
            (Requesting) c.dj
            (Gifting) c.dj @crunc
        ```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="dj")
    async def dj(self, ctx):
        if not await self.bot.has_perm(ctx): return
        """
        Allow a user to gift the DJ role to another user or request it for themselves.
        You must be in VC to gain the role. If gifting, you must own the role already and the mentioned user must be in VC.
        Removed when you leave the VC or after an hour.

        Arguments:
            o_user: A special variable for bypassing some checks. See role_overpower
        Examples:
            (Requesting) c.dj
            (Gifting) c.dj @crunc
        """
        message = ctx.message
        content = message.content
        dj = ctx.guild.get_role(804454276772266034)
        user = message.mentions
        if not dj:
            return

        # Get the current owner of the dj role, if they exist, and store it in the user_id variable.
        self.bot.cursor.execute("SELECT user_id FROM dj_temp")
        res = self.bot.cursor.fetchone()
        if res:
            try:
                user_id = res[0]
            except discord.ext.commands.errors.CommandInvokeError:
                return
        else:
            user_id = 0

        # Make sure the person attempting to gift the DJ role currently owns the role.
        # If they do not, and the role is available, give them the role.
        if user_id != ctx.author.id:
            try:
                await ctx.send(f"{self.bot.get_user(res[0]).mention} currently owns the DJ role, you can't gift or request it.")
                return
            except TypeError:
                if user:
                    await ctx.send("You must own the DJ role before attempting to gift it.")
                    return
                else:
                    vs = ctx.author.voice
                    if not vs:
                        await ctx.send("You must be in a VC to request DJ.")
                        return
                    else:
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
                        self.bot.cursor.execute("commit")

                        await ctx.send(f"Given {ctx.author.mention} {dj.mention} for 1 hour.")
                        return
        else:  # If the user does own the role, then:
            # Find the mentioned user
            if user:
                user = message.mentions[0]
                new_user_id = user.id

                # Check if mentioned user is in a VC.
                vc = user.voice
                if not vc:
                    await ctx.send("The mentioned user must be in a vc to gift them the DJ role.")
                    return

                # Remove DJ role from current owner
                try:
                    await ctx.author.remove_roles(dj, reason="Role remove command")
                except discord.errors.Forbidden:
                    await ctx.send(
                        "I require manage roles, and the role I'm removing must be lower than my highest role.")
                    return
                except discord.errors.HTTPException:
                    await ctx.send("Failed removing role.")
                    return
                except:
                    traceback.print_exc()

                # Apply the DJ role to the user
                try:
                    await user.add_roles(dj)
                except discord.errors.Forbidden:
                    await ctx.send(
                        "I require manage roles, and the role I'm removing must be lower than my highest role.")
                    return
                except discord.errors.HTTPException:
                    await ctx.send("Adding role failed.")
                    return
                except:
                    traceback.print_exc()
                    return

                # Create DB entry
                time = 1  # Hard coded for now.
                end_time = self.bot.hours_from_now(time)
                time_string = self.bot.time_to_string(hours=time)
                self.bot.cursor.execute(
                    f"UPDATE dj_temp SET user_id={new_user_id}, end_time={end_time} WHERE user_id={user_id}")
                self.bot.cursor.execute("commit")

                await ctx.send(f"{ctx.author.mention} has given {user.mention} {dj.mention} for an hour.")

            else:  # If no user is mentioned:
                user_id = int(self.bot.get_variable(content, "user", type="int", default=0))
                if not user_id:
                    await ctx.send("Mention a user or provide their id as user=id")
                    return
                user = ctx.guild.get_member(user_id)
                if not user:
                    await ctx.send(f"Cannot find member with id {user_id}")
                    return


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
