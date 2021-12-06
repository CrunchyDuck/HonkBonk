import discord
import re
from discord.ext import commands
import logging
import traceback
import helpers
from HonkBonk import MyBot


class Core(commands.Cog):
    """Admin commands. Mostly just fun things for me to toy with, sometimes test, rarely useful."""
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.init_db(bot.cursor)
        self.bot.Scheduler.add(self.vc_sleep_timer, 5)
        self.bot.event(self.on_command_error)
        self.bot.event(self.on_ready)

        # #self.r_only_emoji = re.compile(
        # #    r"^((?:<:.*?:)(\d*)(?:>)|[\s])*$")  # This parses over a string and checks if it ONLY contains
        # self.r_get_emoji = re.compile(r"(<:.*?:)(\d*)(>)")
        # #self.r_cdn = re.compile(
        # #    r"(https://cdn.discordapp.com/attachments/.*?\.(gif|png|jpg))|(https://cdn.discordapp.com/emojis/)")  # The domain images and stuff are placed.
        # self.r_cdn_filename = re.compile(r"([^/]*?(\.png|\.jpg|\.gif))")
        #
        # self.rc_dunno = self.bot.Chance({
        #     "No encuentro la wea": 100,
        #     "Not a clue": 100,
        #     "Haven't a scooby": 100,
        #     "a dinnae ken": 100,
        #     "dunno": 100
        # })

    async def on_command_error(self, ctx, error):
        """Triggered when a prefix is found, but no command is."""
        if isinstance(error, commands.CommandNotFound):  # Unrecognized command
            if await self.pat_command(ctx):
                return

            # Command not recognized
            await ctx.send("command no no be is.")
        else:
            raise error

    async def on_ready(self):
        print(f"{self.bot.user} has connected to Discord :)")

    def init_db(self, cursor):
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS sleep_timer ("  # An entry is created for each change that is detected.
            "guild INTEGER,"  # ID of the server
            "user INTEGER,"  # ID of the user
            "time INTEGER,"  # The time the user should be removed from the VC.
            "reply_channel INTEGER"  # ID of the channel to announce VC removal in.
            ")")
        cursor.execute("commit")

    # TODO: I'd like to find some way to join up commands and their help functions.
    #  This might be achieved by creating an object rather than simply running functions.
    @commands.command(name=f"timestamp")
    async def timestamp(self, ctx):
        """
        Get the timestamp of a provided Discord Snowflake.

        Example command:
            c.timestamp 411365470109958155
        """
        if not await self.bot.has_perm(ctx, dm=True): return

        timestamps = re.search(r"timestamp ([ \d]+)", ctx.message.content)
        if not timestamps:
            await ctx.send("No snowflake found.")
            return

        message = ""
        for timestamp in timestamps.group(1).split(" "):
            m = int(timestamp.replace(" ", ""))
            message += helpers.date_from_snowflake(m) + "\n"

        await ctx.send(message)

    @commands.command(name="echo")
    async def echo(self, ctx):
        """Repeat what it was given in Discord."""
        if not await self.bot.has_perm(ctx, owner_only=True): return
        await ctx.send(ctx.message.content)

    @commands.command(name="print")
    async def print_message(self, ctx):
        """Similar to c.test, but specifically for printing values to the console."""
        if not await self.bot.has_perm(ctx, owner_only=True): return
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
        if not await self.bot.has_perm(ctx, owner_only=True): return
        content = re.search("content=(.+)", ctx.message.content, flags=re.DOTALL).group(1)

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
        if not await self.bot.has_perm(ctx, owner_only=True): return
        message = helpers.remove_invoke(ctx.message.content)
        message, uid = helpers.get_command_variable(message, "id")
        target = await self.bot.fetch_user(uid)

        await target.send(message)

    @commands.command(name="kick")
    async def selfkick(self, ctx):
        """Allows the user to kick themselves from the server for fun."""
        if not await self.bot.has_perm(ctx): return

        user = ctx.author
        guild = ctx.guild

        # DM the user and then kick them.
        try:
            await user.send(
                "You kicked yourself from the server! Good job. \nHere's the invite link to get back: https://discord.gg/eW4CpfJ")
            await guild.kick(user, reason="self kick c.kick :)")
        except:
            traceback.print_exc()

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        uptime = helpers.time_now() - self.bot.uptime_seconds
        uptime_string = helpers.time_to_string(seconds=uptime)
        uptime_start = self.bot.uptime_datetime.strftime("%Y/%m/%d T %H:%M:%S")

        await ctx.send(f"{uptime_string}; Started at: {uptime_start}")

    @commands.command(name="pfp")
    async def get_pfp(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        men = ctx.message.mentions
        # format = self.bot.get_variable(ctx.message.content, key="format", type="str", default=None)
        # if format not in ["jpg", "png", "gif", "webp", "jpeg", None]:
        #     await ctx.send("hey hey stinker, read the valid formats in c.pfp.")
        #     return

        if men:
            user = men[0]
        else:
            id = re.search(r"\d+", ctx.message.content)
            if not id:
                await ctx.send("Mention a user or provide an ID.")
                return

            id = int(id.group(0))
            if id.bit_length() > 64:  # The exception thrown my discord is generic and so I check it manually.
                await ctx.send("oi you cheeky bugga dis id roite here be too lonk oi oi")
                return

            user = self.bot.get_user(id)
            if not user:
                try:
                    user = await self.bot.fetch_user(id)  # Get users the bot doesn't share a server with.
                except discord.errors.NotFound:
                    await ctx.send("Cannot find user.")
                    return

        img = user.avatar_url_as(format=None, static_format="png", size=4096)
        await ctx.send(f"{img}")

    @commands.command(aliases=["sleep"])
    async def vc_sleep(self, ctx):
        if not await self.bot.has_perm(ctx): return

        time = re.search(r" (\d+)", ctx.message.content)
        if not time:
            await ctx.send("Provide a time to remove you from the VC!")
            return
        time = int(time.group(1))
        target_user = self.bot.admin_override(ctx.message)

        # Check if there's already an entry for this user.
        self.bot.cursor.execute("SELECT rowid, * FROM sleep_timer"
                                f" WHERE user={target_user.id} AND guild={ctx.guild.id}")
        result = self.bot.cursor.fetchone()
        time = max(min(1440.0, time), 0.016)
        end_time = helpers.time_from_now(minutes=time)
        time_string = helpers.time_to_string(minutes=time)

        # Update entry
        if result:
            self.bot.cursor.execute(f"UPDATE sleep_timer SET time={end_time} WHERE rowid={result['rowid']}")
        else:
            self.bot.cursor.execute(f"INSERT INTO sleep_timer VALUES(?,?,?,?)", (ctx.guild.id, target_user.id, end_time, ctx.channel.id))
        self.bot.cursor.execute("commit")
        await ctx.send(f"{target_user.name} will automagically be zapped from any VC in {time_string}.")

    async def vc_sleep_timer(self, time_now):
        self.bot.cursor.execute("SELECT rowid, * FROM sleep_timer ORDER BY time ASC")
        targets = self.bot.cursor.fetchall()
        for target in targets:
            if time_now < target["time"]:
                break

            rowid = target["rowid"]
            try:
                server = self.bot.get_guild(target["guild"])
                if server is None:
                    logging.error(f"Guild {target['guild']} could not be found.")
                    raise ValueError
                member = server.get_member(target["user"])
                channel = None
                if member is None:
                    logging.error(f"User {target['user']} could not be found in guild {server.id} ({server.name})")
                    raise ValueError

                try:
                    await member.move_to(channel, reason="Sleep timer ran out.")
                    cnl = self.bot.get_channel(target["reply_channel"])  # VC text channel.
                    await cnl.send(f"Removed {member.name} from voice chat. Sleep tight :sleeping:")
                except discord.errors.Forbidden as e:
                    # Don't have the permissions.
                    logging.error(f"No permission to remove {member.display_name} from VC in {server.id} ({server.name})")
                    raise e
                except discord.errors.HTTPException as e:
                    # Failed.
                    logging.error(f"HTTPS error trying to remove {member.display_name} from VC in {server.id} ({server.name})")
                    raise e
            except (ValueError, discord.errors.Forbidden, discord.errors.HTTPException):
                pass
            finally:
                self.bot.cursor.execute(f"DELETE FROM sleep_timer WHERE rowid={rowid}")
                self.bot.cursor.execute("commit")

    async def pat_command(self, ctx):
        """Atypical command, used in on_command_error"""
        if not await self.bot.has_perm(ctx, dm=True): return
        pats = re.search(r"c.((?:pat)+)", ctx.message.content)
        if pats:
            num = len(pats.group(1)) // 3
            await ctx.send("U" + ("wU" * num))
            return True
        else:
            return False

    # @commands.command(name="ignore.help")
    # async def ignore_help(self, ctx):
    #     if not await self.bot.has_perm(ctx, dm=True): return
    #     docstring = """
    #     ```Ignores a channel, category, or user.
    #     You can mention a category by putting its id into this structure:
    #     <#id_of_category>
    #
    #     Arguments:
    #         (Required) - Requires at least one
    #         id: The ID to add to the list. Only 1 ID can be provided this way.
    #         member: A mention of the member to ignore. Can be multiple.
    #         channel: A mention of the text, voice or category channel to ignore. Can be multiple.
    #
    #         (Optional)
    #         stop: Stops ignoring the given IDs.
    #
    #     Example:
    #         c.ignore  # Ignores this channel
    #         c.ignore @Pidge  # Ignores a user
    #         c.ignore #general #nsfw #announcements # Ignores multiple channels.
    #         c.ignore id=704361803953733694 stop  # Stops ignoring an ID, such as a category, or a channel.```
    #     """
    #     docstring = self.bot.remove_indentation(docstring)
    #     await ctx.send(docstring)
    #
    # @commands.command(name="ignore.none.help")
    # async def ignore_none_help(self, ctx):
    #     if not await self.bot.has_perm(ctx, dm=True): return
    #     docstring = """```Removes all users and channels from the ignore list.```"""
    #     docstring = self.bot.remove_indentation(docstring)
    #     await ctx.send(docstring)
    #
    # @commands.command(name="ignore.list.help")
    # async def ignore_list_help(self, ctx):
    #     if not await self.bot.has_perm(ctx, dm=True): return
    #     docstring = """```Displays a list of the ignored channels and users.```"""
    #     docstring = self.bot.remove_indentation(docstring)
    #     await ctx.send(docstring)

    @commands.command("pfp.help")
    async def get_pfp_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            Get the highest quality version of anyone's profile picture! Mention a user, or give their ID.
            Works on people not in the server!
    
            **Examples:**
            selfie
            `c.pfp @HonkBonk`
            youfie
            `c.pfp 565879875647438851`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command("timestamp.help")
    async def timestamp_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            Get the time of a Discord Snowflake. Can do multiple at once.

            **Examples:**
            `ctimestamp 565879875647438851`
            `ctimestamp 903211743340273765 903211796658282496`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command("pat.help")
    async def pat_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """```:)```"""
        await ctx.send(docstring)

    @commands.command("kick.help")
    async def self_kick_help(self, ctx):
        # Gives no help so that people try to do it.
        return

    @commands.command(aliases=["sleep.help"])
    async def sleep_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            Automatically remove you (pidge) from a VC after the given time, in minutes.

            **Examples:**
            sleep in one hour
            `c.sleep 60`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command("help")
    async def core_help(self, ctx):
        """The core help command."""
        if not await self.bot.has_perm(ctx, dm=True): return
        # help_string = "```Modules:\n" \
        #               "c.role - Vanity roles and moderation controls.\n" \
        #               "c.emoji - Adding and moderating emoji.\n" \
        #               "c.react - Automatic reactions to messages.\n" \
        #               "c.room - Temporary rooms.\n" \
        #               "c.vc - underdeveloped VC commands.\n" \
        #               "\n" \
        #               "Core commands:\n" \
        #               "c.timestamp - Provides a date from a Discord ID/Snowflake.\n" \
        #               "c.id - Try to figure out what a Discord snowflake/id belongs to.\n" \
        #               "c.dj - Allows control of the DJ role for the Rythm bot.\n" \
        #               "c.asight - Allow a user to assign themselves the \"asight\" role for a specified amount of time.\n" \
        #               "c.sleep - Allows a user to set a time after which they'll be removed from VC.\n" \
        #               "c.shuffle - Shuffles a sentence." \
        #               "c.speak - Makes HonkBonk say something, somewhere :).\n" \
        #               "c.dm - Makes HonkBonk DM a user.\n" \
        #               "c.ignore - Setting honkbonk to ignore users/channels.\n" \
        #               "c.ignore.list - A list of ignored channels and users.\n" \
        #               "c.ignore.none - Stops ignoring all users and channels.```"
        # await ctx.send(help_string)
        desc = "Type c.command.help for more info on that command\nE.G `c.role.help`, `c.pat.help`\n" \
               "Note: Don't DM HonkBonk personal things. I can see that."
        await ctx.send(embed=self.bot.create_help(self.bot.core_help_text, desc))


def setup(bot):
    bot.core_help_text["General"] += [
        "timestamp", "pat", "kick", "uptime", "pfp", "sleep"]
    #bot.core_help_text["Admins OwOnly"] += ["dm", "speak", "ignore", "ignore.none", "ignore.all"]
    bot.add_cog(Core(bot))


# def teardown(bot):
#     for l in ["randcap", "small", "num", "timestamp", "id", "shuffle", "pat", "kick", "uptime", "pfp", "uwu", "8ball"]:
#         bot.core_help_text["General"].remove(l)
#     for l in ["dm", "speak", "ignore", "ignore.none", "ignore.all"]:
#         bot.core_help_text["Admins OwOnly"].remove(l)
#
#     bot.remove_cog(Admin(bot))
