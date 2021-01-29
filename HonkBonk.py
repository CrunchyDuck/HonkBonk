import asyncio
import discord
import time
import logging
import os
import re
import sqlite3
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv
from random import random
import traceback
import json
from math import trunc

# TODO: Find some way to integrate my variable passing system from discord-powers, as it is way better than discord's methods.

load_dotenv()  # Fetches from .env file.
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # funny bot login number
myID = int(os.getenv("OWNER_ID"))  # The ID of my account :) Certain commands can only be run by admins like me.
bot_prefix = "c."  # Commands in chat should be prefixed with this.


class MyBot(commands.Bot):
    """
    An expanded version of discord.ext.commands.Bot.

    Attributes
    ----------
    admins: List[:class:`int`]
        A list of user IDs who have admin privileges over this bot.
    active_cogs: List[:class:'str']
        A list of the currently loaded cogs.
    crunchyduck: :class:'int'
        My Discord snowflake.
    banned_from_commands: List[:class:'int']
        Discord snowflakes that are disallowed from using most of the bot's commands.
    zws: :class:'str'
        A zero width space, used in embeds.
    db:
        An SQLite3 database
    cursor:
        A cursor to the SQLite3 database
    """
    # A list of "format patterns", essentially the form a variable can take.
    pformats = {
        # "bool": r"(\bTrue\b|\bFalse\b)",
        "str": r"""(?:(?:["”'`]([^"”'`]*)["”'`])|(\w*))""",  # TODO: Update this with capture group backreferencing
        "float": r"(\d+(?:\.\d+)?)",
        "int": r"(\d+)"
    }
    r_newline_whitespace = r"(?<=\n)([ ]+)"  # The whitespace after a new line. Basically, removes indentation.

    def __init__(self, bot_prefix, intents=None):
        super().__init__(bot_prefix, intents=intents)  # This just runs the original commands.Bot __init__ function.
        # The cogs to load on the bot.
        self.active_cogs = ["emoji", "admin", "roles", "message_reactions", "forward_dm", "voice_channels", "temp_channel"]

        self.crunchyduck = myID  # Sometimes it's useful to know who your owner is :)

        # TODO: Switch to storing permissions in a database rather than hardcoding them, so they can be changed on the fly.
        self.admins = [  # Certain commands can only be run by these users.
            self.crunchyduck,
            337793807888285698,  # Oken
            630930243464462346,  # Pika
        ]
        self.banned_from_commands = [  # Any users who have been banned from using these commands. Bad boys.
        ]
        self.zws = "\u200b"  # An empty character, used when a field *requires* a value I don't want to give (normally embeds)

        # Any tabulated data should be stored in this database, under their respective table
        self.db = sqlite3.connect("bot.db")
        self.cursor = self.db.cursor()
        self.db_init()

    def default_embed(self, title):
        """
        An embed that has the bot's signatures.
        returns: :class:discord.Embed
        """
        embed = discord.Embed(
            title=title,
            colour=discord.Colour.dark_purple()
        )
        embed.set_author(name=self.user.name, icon_url=self.user.avatar_url)

        return embed

    def db_init(self):
        """Initializes any important tables in the database if they don't exist."""
        cursor = self.cursor

        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS settings ("
            "server INTEGER,"  # The server this setting is specific to.
            "key STRING,"  # The name of the setting.
            "value STRING"  # The value this setting stores.
            ")")
        cursor.execute("commit")

        # Setting keys:
        # ignore: Ignore a channel, category, user.

    def db_read_setting(self, server_id, key, default=None):
        """Fetches all entries for a key from the settings table in the database. Returns default if no entry exists."""
        self.cursor.execute(f"SELECT value FROM settings WHERE server={server_id} AND key={key}")
        result = self.cursor.fetchall()
        if result:
            return result
        elif default is not None:
            return default
        else:
            # Get default from database
            self.cursor.execute(f"SELECT value FROM settings WHERE server=0 AND key={key}")
            result = self.cursor.fetchall()
            return result

    def db_add_setting(self, server_id, key, value):
        """
        """
        self.cursor.execute(f"INSERT INTO settings VALUES(?, ?, ?)", (server_id, key, value))
        self.cursor.execute("commit")

    def db_remove_setting(self, server_id, key, value=None):
        """Deletes a server setting."""
        #self.cursor.execute(f"DELETE FROM settings ")

    async def has_perm(self, input, admin=False, dm=False, ignore_bot=True, banned_users=False, message_on_fail=True,
                       bot_room=False, ignored_rooms=False):
        """
        Common permissions to be checked to see if this user is allowed to run a command.
        Arguments:
            input: Context or message, should be able to get a User from this.
            admin: Is this an admin only command?
            dm: Should this command be allowed in DMs?
            ignore_bot: If the message comes from a bot, ignore?
            banned_users: Whether to allow even banned users to use this command.
            message_on_fail: Whether to notify the user that the command failed if possible.
            bot_room: Whether this command should only run in bot rooms.
            ignored_rooms: Whether this command can be used in ignored rooms.
        """
        # TODO: Allow for a list of "ignored rooms" to be added to the permissions check.

        # Get information required to check perms.
        b_ctx = isinstance(input, discord.ext.commands.Context)
        b_message = isinstance(input, discord.Message)
        if b_ctx or b_message:
            is_bot = input.author.bot
            u_id = input.author.id
            channel = input.channel
        else:
            raise AttributeError(f"MyBot.has_perm was provided with incorrect type {type(input)} for input.")

        # Checks
        if u_id in self.admins:  # Admins can always run commands.
            return True
        elif admin:  # If the admin check is on, this user cannot run this command.
            if message_on_fail:
                try:
                    await channel.send("You must be an admin to run this command.")
                except:
                    pass
            return False

        if ignore_bot and is_bot:
            return False

        if not banned_users and u_id in self.banned_from_commands:
            if message_on_fail:
                try:
                    await channel.send("Restricted users cannot use this command.")
                except:
                    pass
            return False

        if not dm and channel.type is discord.ChannelType.private:
            return False

        if not ignored_rooms and self.is_room_ignored(input):
            return False

        # If all falsifying checks fail, user has perms.
        return True

    def is_room_ignored(self, ctx):
        server = ctx.guild.id
        room_id = ctx.channel.id
        self.cursor.execute(f"SELECT * FROM settings WHERE server={server} AND key=? AND value={room_id}", ("ignore",))
        if self.cursor.fetchone():
            return True
        else:
            return False

    def admin_override(self, ctx):
        """If an admin calls a command, and has mentioned another user, invoke that command as if the user invoked it."""
        user = ctx.author
        if user.id in self.admins:
            if ctx.message.mentions:
                user = ctx.message.mentions[0]
        return user

    @staticmethod
    def get_variable(string, key=None, type=None, pattern=None, default=None):
        """
        Uses regex to parse through a string, attempting to find a given key:value pair or a keyword.

        List of recognized types:
            "str" - Finds the first key=value_no_spaces or key="value in quotes" pair in the string, E.G say="Hi there!". Returns value.
            "int" - Finds the first key=number pair in the string, E.G repeat=5. Returns value.
            "keyword" - Tries to simply find the given word in the string. Returns True if keyword is found, False otherwise.
            "float" - Find the first key=number.number pair, E.G percent=1.0 or percent=52

        Arguments:
            string: The string to search for the variable in.
            key: Used in key=type. Requires type to be defined. If omitted, will just search the string using "type"
            type: Used in key=type.
            pattern: A regex pattern to search with instead of using key=type
            default: Default return value if nothing is found.

        Returns: String or Boolean
        """
        re_pat = ""  # The regex pattern to parse the string with.

        # Get and compile the regex pattern to use to search.
        if type:
            if key:
                if type == "keyword":
                    re_pat = re.compile(fr"(\b{key}\b)")
                elif type in MyBot.pformats:
                    re_pat = re.compile(fr"(?:\b{key}=){MyBot.pformats[type]}")
                else:  # Unrecognized type.
                    raise AttributeError(f"Unrecognized type for get_variable: {type}")
            else:
                if type in MyBot.pformats:
                    re_pat = re.compile(fr"{MyBot.pformats[type]}")
                else:
                    raise AttributeError()
        elif pattern:  # A pre-compiled re pattern to search with
            re_pat = pattern
        else:
            raise AttributeError(f"get_variable was not provided with a pattern or a type")

        search_result = re.search(re_pat, string)
        if search_result:
            if type == "keyword":
                return True
            else:
                return allgroups(search_result)

        return default

    @staticmethod
    def date_from_snowflake(snowflake, strftime_val="%Y-%m-%d %H:%M:%S UTC"):
        """
        Convert a Discord snowflake into a date string.
        Arguments:
            snowflake: A discord snowflake/ID
            strftime_val: An strf to use on the datetime object.
        Returns:
            A string of the date.
        """
        timestamp = ((int(snowflake) >> 22) + 1420070400000) / 1000
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime(strftime_val)

    @staticmethod
    def hours_from_now(hours):
        """Calculates the Unix Epoch Time in the given amount of hours. UTC time."""
        duration_seconds = hours * 60 * 60  # Convert the duration to seconds.
        return time.mktime(datetime.now().timetuple()) + duration_seconds

    @staticmethod
    def time_to_string(seconds=0, minutes=0, hours=0, days=0):
        """Returns the provided time as a string."""
        # Convert provided values to seconds.
        time = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds  # This is inefficient, but looks nicer in the end.
        days, remainder = divmod(time, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        timestring = ""
        if days:
            timestring += f"{trunc(days)} days, "
        if hours:
            timestring += f"{trunc(hours)} hours, "
        if minutes:
            timestring += f"{trunc(minutes)} minutes, "
        if seconds:
            timestring += f"{trunc(seconds)} seconds, "

        if timestring:
            timestring = timestring[:-2]  # Crop the last two characters

        return timestring

    @staticmethod
    def remove_indentation(string):
        indentation_amount = re.search(MyBot.r_newline_whitespace, string)
        if not indentation_amount:
            return string
        indentation_amount = indentation_amount.group(1)
        return re.sub(indentation_amount, "", string)

    class Chance:
        # TODO: Maybe add in chance "brackets", meaning all things in that bracket add up up to a certain percentage.
        # TODO: Add command to check the chance x amount of weight has in the current index.
        """
        An object that can return a random result from a predefind dictionary of chances and values.
        curtsy of crunchyduck :)

        Arguments:
            chance_index: A dictionary organized as value:chance
                The chance index is a dictionary where every "key" is what to return, and every value is the chance.
                The chance is calculated *relative* to the total value of everything else.
                Something with a value of 100 in a total of 1000 has a 10% chance of being chosen.
                A higher value, of course, means something is more likely.
        """
        def __init__(self, chance_index={}):
            self.chance_index = chance_index
            self.chance_max = 0

            # A dictionary where each value is a float between 0 and 1.
            # The value attached to a key is the maximum that key can go up to.
            self.benchmarks = self.create_benchmarks(chance_index)

        def add_element(self, dict_to_add):
            """
            Adds entries to the dictionary, then updates the benchmarks.
            Arguments:
                dict_to_add: A dictionary of value:chance
            """
            self.chance_index = {**self.chance_index, **dict_to_add}
            self.benchmarks = self.create_benchmarks(self.chance_index)

        def get_value(self, seed=None):
            """
            Fetches a key from the benchmark dictionary.
            Arguments:
                seed: A number between 0 and 1. If None, choose a random number.
            """
            if seed == None:
                seed = random()  # If no seeded value was provided, generate one.

            if seed > 1 or seed < 0:
                raise ValueError("Chance.get_value was provided with a value more than 1 or less than 0.")
            i = 0
            for key, val in self.benchmarks.items():
                if seed > val:
                    continue
                return key

            raise ValueError(f"Chance.get_value could not find a matching key for value {seed}")

        def get_chance(self, value, weight=False):
            """
            Returns the chance of a given value show up.
            Arguments:
                value: The key to search calculate the chance of.
                weight: Whether to return the weight instead of the chance.
            Returns:
                Weight chance | percentage chance
            Raises:
                ValueError: Value is not a valid result.
            """
            if value in self.benchmarks:
                weighted_chance = self.chance_index[value]
                if weight:
                    return weighted_chance
                else:
                    return weighted_chance / self.chance_max
            else:
                raise ValueError("Value is not a valid result.")

        def create_benchmarks(self, chance_index):
            """
            Creates the benchmarks.
            keys will be given a value calculated as chance + previous_chances.
            So, with 2 equal chanced keys, the entries will be 0.5 and 1.
            Therefore, to get a key, check if the seed is more than the current seed. If so, move to next. If not, it is this key.
            The last value in a benchmark will always be 1, within rounding error.

            Arguments:
                chance_index: A dictionary of value:weight, where "value" is what will be returned, and "weight" is the weight to be chosen
            Returns:
                A dictionary
            """
            if not isinstance(chance_index, dict):
                raise TypeError(f"create_benchmarks provided with incorrect chance_index type. Should be dictionary not {type(chance_index)}")

            self.chance_max = 0  # The value for things to be "out of"
            for val in chance_index.values():
                self.chance_max += val

            benchmarks = {}
            chance = 0
            for key, value in chance_index.items():
                chance += value / self.chance_max
                benchmarks[key] = chance

            return benchmarks


async def timed_loop(aBot):
    """
    A loop that polls regularly. Designed to do scheduled functions and run in an async loop with the main bot.
    Arguments:
        aBot: The bot to run the functions on.
    """
    loop_ticks = 5  # How regularly, in seconds, the loop is run.
    while True:
        await asyncio.sleep(loop_ticks)
        time_now = time.mktime(datetime.now().timetuple())  # Current Unix Epoch time.

        # For now I'm manually putting all blocks of code that need to be time in here.
        # I wish to figure out a more automatic process in the future, similar to discord cogs.

        # ======= temp_channel.py =======
        try:
            # Need to find a way to index these dynamically.
            guild_id = 704361803953733693
            archive_category = 774303846478250054

            aBot.cursor.execute("SELECT * FROM temp_room ORDER BY end_time ASC")
            targets = aBot.cursor.fetchall()
            for target in targets:
                if time_now > target[2]:  # If we've passed the time this is supposed to terminate.
                    guild = aBot.get_guild(guild_id)
                    TextChannel = guild.get_channel(target[1])
                    await TextChannel.edit(category=guild.get_channel(archive_category), sync_permissions=True, position=len(guild.channels))
                    try:
                        await TextChannel.send("Archiving channel...")
                    except: pass

                    aBot.cursor.execute("DELETE FROM temp_room WHERE room_id=?", (TextChannel.id,))
                    aBot.cursor.execute("commit")
                else:
                    break
        except:
            traceback.print_exc()

        # ======= Temp role =======
        try:
            aBot.cursor.execute("SELECT rowid, * FROM temp_role ORDER BY end_time ASC")
            targets = aBot.cursor.fetchall()
            for target in targets:
                if time_now > target[3]:
                    rowid = target[0]
                    server = aBot.get_guild(target[1])
                    member = server.get_member(target[2])
                    role = discord.Object(target[4])

                    if member is None:
                        # Member could not be found
                        print("member not found.")
                    try:
                        await member.remove_roles(role, reason="Temporary role end time.")
                    except discord.errors.Forbidden:
                        # Don't have the permissions.
                        pass
                    except discord.errors.HTTPException:
                        # Failed.
                        pass
                    aBot.cursor.execute(f"DELETE FROM temp_role WHERE rowid={rowid}")
                else:
                    break

                    # Send message in logging channel about the role being removed.
        except:
            traceback.print_exc()


def allgroups(matchobject):
    """Returns all of the strings from a regex match object added together."""
    string = ""
    for s in matchobject.groups():
        if s:
            string += s

    return string

# IDEA: Command to make a temporary room for discussion.
# IDEA: A function for the bot that will take an image, and turn it into a Waveform/vectorscope/histogram analysis because they look fucking rad
# IDEA: Add a "collage" function that takes in a bunch of users, and combines them into a x*y collage, like I had to for DTimeLapse
# IDEA: Twitch integration to announce streams.
# IDEA: Add timezone functions.
# IDEA: Allow me to ban reactions on X person's messages.
# IDEA: Quote database.
# IDEA: Github integration

# TODO: Set up Doxygen html documentation.
# TODO: Add server admins as viable "bot admins"
# TODO: Make bot track all roles in color_role.py, so they can be readded if someone loses their roles (E.G Kicking)
# TODO: Change the "bot blocked members" thing to use a specific role to determine blocked members.
# TODO: Add "Bot channel only" check.
# TODO: Command to add "bad" role to people for X time.
# TODO: Shift all commands to take consideration of the server they should be run in.
# TODO: Make temp rooms able to be reopened
# TODO: Make temp rooms modifiable after creation.
# TODO: Make temp rooms announce when created/opened
# TODO: Help command.
# TODO: Make bot automatically update all rooms to have the same permission for the "bad" role.
# TODO: temp_channel Allow channels to be modified after creation.
# TODO: Command for c.react.list to display all reactions in this server.
# TODO: Make admins server based, not bot-wide.
# TODO: Manage reactions on edited messages.

# FIXME: Creating custom roles currently place the role at the top of the list, over the top of admins.
# FIXME: Emoji pushing doesn't properly assign ownership.
# FIXME: Clear attachments after emoji push.

intents = discord.Intents.all()
bot = MyBot(bot_prefix, intents=intents)
bot.remove_command("help")  # the default help command is ugly and I maintain a help in my server. Also lets me control what's shown.

# Set up logger. Modified docs version.
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Runs only the listed cogs
# TODO: Learn how this works so I can use this in other code things I do, hotswitching modules is really cool.
for cog in bot.active_cogs:
    bot.load_extension(f"cogs.{cog}")
bot.load_extension(f"cogs.help")  # This has to be loaded after all of the others, such that all other cogs load before.


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord :) @ {datetime.now()}")

loop = asyncio.get_event_loop()
try:
    asyncio.ensure_future(timed_loop(bot))
    asyncio.ensure_future(bot.start(TOKEN))
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(bot.logout())
finally:
    loop.close()

