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

        self.bot.timed_commands.append([self.dj_end, 5])

        self.rc_deskcheck = self.bot.Chance({
            565879875647438851: 150,  # pidge (discrimination)
            411365470109958155: 100,  # me
            337793807888285698: 100,  # oken
            431073784724848652: 100,  # baguette
            416630260566851584: 100,  # stas
            325705378769928192: 100,  # maxi
            630930243464462346: 100,  # pika
            361176214188064769: 100,  # mudpip
        })

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
                        end_time = self.bot.time_from_now(hours=time)
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

                # Check if mentioned user is a bot. If so, the role can't be gifted to them.
                is_bot = user.bot
                if is_bot:
                    await ctx.send("The DJ role can't be gifted to bots.")
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
                end_time = self.bot.time_from_now(hours=time)
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

    @commands.command(name="asight")
    async def asight(self, ctx):
        if not await self.bot.has_perm(ctx): return
        """
        Allow a user to assign themselves the "asight" role for a specified amount of time.

        Arguments:
            time: The amount of time to assign the role for, in hours. Defaults to 1 hour.
        Examples:
            c.asight time=4
        """
        message = ctx.message
        content = message.content
        time = float(self.bot.get_variable(content, "time", type="float", default=1))
        asight = ctx.guild.get_role(802630159999828009)
        user = message.author
        if not asight:
            return

        # Check if there's already an entry in the database for this user/role
        self.bot.cursor.execute(
            f"SELECT rowid, * FROM temp_role WHERE"
            f" user_id={user.id} AND server={ctx.guild.id} AND role_ids={asight.id}")
        result = self.bot.cursor.fetchone()

        # Apply the asight role to the user
        try:
            await user.add_roles(asight)
        except discord.errors.Forbidden:
            await ctx.send(
                "I need the manage roles permission for this, and the role must be lower than my highest role.")
            return
        except discord.errors.HTTPException:
            await ctx.send("Adding role failed.")
            return
        except:
            traceback.print_exc()
            return

        if time > 0:
            time = max(min(336, time), 0.0003)  # Limit to 1 month or 1 second.
            end_time = self.bot.time_from_now(hours=time)
            time_string = self.bot.time_to_string(hours=time)

            if result:  # Update existing entry.
                self.bot.cursor.execute(f"UPDATE temp_role SET end_time={end_time} WHERE rowid={result[0]}")
            else:  # Create entry.
                self.bot.cursor.execute(
                    f"INSERT INTO temp_role VALUES({ctx.guild.id}, {user.id}, {end_time}, {asight.id})")
            self.bot.cursor.execute("commit")

            await ctx.send(f"Asight role given to {user.name} for {time_string}!")
        else:
            await ctx.send("Provided time must be above 0.")
            return

    @commands.command(name="deskcheck")
    async def deskcheck(self, ctx):
        if not await self.bot.has_perm(ctx, admin=True): return
        sinner = ctx.guild.get_member(self.rc_deskcheck.get_value())
        punishment = ctx.guild.get_role(815158018324693024)

        await sinner.add_roles(punishment, reason="desk check.")
        await ctx.send(f"{sinner.mention} You've just been DESK CHECKED! Show your TIDY DESK to ABSOLVE YOURSELF OF SIN!")

    # Timed function
    async def dj_end(self, time_now):
        self.bot.cursor.execute("SELECT * FROM dj_temp")
        res = self.bot.cursor.fetchone()  # there should only ever be one in here. i hope.
        if res:
            if time_now > res[1]:
                server = self.bot.get_guild(704361803953733693)
                member = server.get_member(res[0])
                dj = server.get_role(804454276772266034)  # hope this works.

                try:
                    await member.remove_roles(dj, reason="Temporary role end time.")
                except discord.errors.Forbidden:
                    # Don't have the permissions.
                    pass
                except discord.errors.HTTPException:
                    # Failed.
                    pass
                self.bot.cursor.execute(f"DELETE FROM dj_temp")  # clear that dummy thicc list.
                self.bot.cursor.execute("commit")

                cnl = self.bot.get_channel(802620220832481315)
                await cnl.send(f"Removed dj role from {member.name} (Role timeout)")
            else:
                pass
                # TODO: Send message in logging channel about the role being removed.


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

    @commands.command(name="asight.help")
    async def asight_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Allow a user to assign themselves the "asight" role for a specified amount of time.
        HonkBonk will DM you when the role is removed.

        Arguments:
            time: The amount of time to assign the role for, in hours. Defaults to 1 hour.
            
        Examples:
            c.asight time=4```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="deskcheck.help")
    async def deskcheck_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ping a bitch ass desk boy to force them to present their desk for all to see.
        will be slapped with the untidy desk role until proven innocent.
        pool of those who can be desk checked has been decided by your supreme leader.
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
            self.cur.execute("commit")
            cnl = self.bot.get_channel(802620220832481315)
            await cnl.send(f"Removed dj role from {member.name} (User left channel)")
        except:
            traceback.print_exc()
            return

    @commands.Cog.listener()
    async def on_message(self, message):
        if not await self.bot.has_perm(message, ignore_bot=False, message_on_fail=False): return
        msg = message.content
        self_refer = re.search(r"^i['’]?m(.+)", msg, re.I)
        if self_refer:
            try:
                new_name = re.search(r"(.{1,32})(\s|$)", self_refer.group(1)).group(1)  # Breaks it at the last full word.
                await message.author.edit(reason="they said \"I'm\"", nick=new_name)
            except:
                pass

    def init_db(self, cursor):
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS dj_temp ("  # An entry is created for each change that is detected.
            "user_id INTEGER,"  # ID of the user
            "end_time INTEGER"  # The time this role should be removed.
            ")")
        cursor.execute("commit")


def setup(bot):
    bot.core_help_text["General"] += ["asight", "dj"]
    bot.core_help_text["Admins OwOnly"] += ["deskcheck"]
    bot.add_cog(ServerSpecific(bot))


def teardown(bot):
    for l in ["asight", "dj"]:
        bot.core_help_text["General"].remove(l)
    bot.core_help_text["Admins OwOnly"].remove("deskcheck")
    bot.remove_cog(ServerSpecific(bot))