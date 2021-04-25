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
from math import trunc
from collections import defaultdict
from pathlib import Path


class MyBot(commands.Bot):
    # TODO: Document functions.
    """
    An expanded version of discord.ext.commands.Bot.

    Attributes
    ----------
    active_cogs: Dict{:class:`str`: :class:`int`}
        A list of the currently loaded cogs.
    admins: List[:class:`int`]
        A list of user IDs who have admin privileges over this bot.
    all_cogs: Dict{:class:`str`: :class:`int`}
        All cogs that were found upon loading the bot.
    core_help_text: collections.defaultdict{:class:`str`: List[:class:`str`]}
        Dictionary where key is the category, and value is a list of command names.
        Used to construct the response for c.help
    db: :class:`sqlite3.Connection`
        A connection object to the database.
    Scheduler: :class:`Scheduler`
        Handles timed functions.
    uptime_seconds: :class:`int`
        Unix Epoch time of when the bot was turned on.
    uptime_datetime: :class:`datetime.datetime`
        Datetime object of when the bot was turned on.
    owner_id: :class:`int`
        The ID of the person who owns this bot. Used in MyBot.has_perm
    """
    # A list of "format patterns", essentially the form a variable can take.
    pformats = {
        # "bool": r"(\bTrue\b|\bFalse\b)",
        "str": r"""(?:(?:["”'`]([^"”'`]*)["”'`])|(\w*))""",  # TODO: Update this with capture group backreferencing
        "float": r"(-?\d+(?:\.\d+)?)",
        "int": r"(-?\d+)"
    }
    r_newline_whitespace = r"(?<=\n)([ ]+)"  # The whitespace after a new line. Basically, removes indentation.

    def __init__(self, bot_prefix, **kwargs):
        super().__init__(bot_prefix, **kwargs)  # This just runs the original commands.Bot __init__ function.
        # The cogs to load on the bot.
        self.all_cogs = {}  # A list of all cogs found in files.
        self.active_cogs = {}  # A list of all currently loaded cogs

        self.Scheduler = Scheduler(self)  # Handled commands that run on timers.
        self.UI_tabs = []  # A list of functions that are used in user_interface to generate tabs for specific cogs.
        self.BotUI = None

        self.owner_id = int(os.getenv("OWNER_ID"))
        self.uptime_seconds = self.time_now()
        self.uptime_datetime = datetime.now()

        # Used for the "core" help command, which is called with c.help. Any non-specific commands are placed here.
        # This relies on dictionaries maintaining their declared order, rather than taking their hash order.
        self.core_help_text = {
            "modules": [],
            "General": [],
            }
        self.core_help_text = defaultdict(list, **self.core_help_text)

        # TODO: Switch to storing permissions in a database rather than hardcoding them, so they can be changed on the fly.
        self.admins = [  # Certain commands can only be run by these users.
            self.owner_id,
            337793807888285698,  # Oken
            630930243464462346,  # Pika
        ]
        self.zws = "\u200b"  # TODO: Maybe remove this?

        # Assigned in start(), as they run on a different thread.
        self.db = None
        self.cursor = None  # TODO: Remove references to this and switch to using db.execute

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

    async def start(self, *args, **kwargs):
        """Log into discord and begin running commands."""
        self.db = sqlite3.connect("bot.db")
        self.cursor = self.db.cursor()
        self.db_init()

        # Find and load cogs.
        cogs = list(Path("./cogs").glob("**/*.py"))
        db_cogs = self.db_get(self.db, "SELECT rowid, * FROM cogs")
        for cog in cogs:
            cog_name = str(cog)[:-len(cog.suffix)]
            cog_name = cog_name.replace("\\", ".")  # windows.
            cog_name = cog_name.replace("/", ".")  # everything else
            self.all_cogs[cog_name] = self.time_now()

            # Check if this cog exists in the database
            load = None
            for db_cog in db_cogs:
                if cog_name == db_cog["cog"]:
                    load = db_cog["active"]

            # Load cog, or update the database with this new cog.
            if load is None:
                # Cog not found in database, add new entry.
                self.db.execute("INSERT INTO cogs VALUES(?,?)", [cog_name, 1])
                self.db.commit()
                self.load_extension(cog_name)
            elif load:
                self.load_extension(cog_name)
        await super().start(*args, **kwargs)

    def load_extension(self, name):
        self.active_cogs[name] = self.time_now()
        super().load_extension(name)

    def unload_extension(self, name):
        self.active_cogs.pop(name)
        super().unload_extension(name)

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
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS cogs ("
            "cog STRING,"  # The path to the cog.
            "active INTEGER"  # Whether the cog is enabled or not.
            ")")
        cursor.execute("commit")

        # Setting keys:
        # ignore: Ignore a channel, category, user.

    def db_read_setting(self, server_id, key, default=None):
        """Fetches all entries for a key from the settings table in the database. Returns default if no entry exists."""
        self.cursor.execute(f"SELECT value FROM settings WHERE server={server_id} AND key='{key}'")
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

    async def has_perm(self, input, *, admin=False, bot_owner=False, dm=False, ignore_bot=True, banned_users=False, message_on_fail=True,
                       bot_room=False, ignored_rooms=False):
        """
        Common permissions to be checked to see if this user is allowed to run a command.
        Arguments:
            input: Context or message, should be able to get a User from this.
            admin: Is this an admin only command?
            bot_owner: Only the person who owns the bot.
            dm: Should this command be allowed in DMs?
            ignore_bot: If the message comes from a bot, ignore?
            banned_users: Whether to allow even banned users to use this command.
            message_on_fail: Whether to notify the user that the command failed if possible.
            bot_room: Whether this command should only run in bot rooms.
            ignored_rooms: Whether this command can be used in ignored rooms.
        """
        # TODO: Switch to providing a dictionary instead of many bools, to allow one to put the checks in order.
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
        if self.owner_id == input.author.id:
            return True
        elif bot_owner:
            return False

        # An admin should only be stopped from a command if the room is ignored.
        if not ignored_rooms and self.is_channel_ignored(input):
            return False

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

        if not banned_users and self.is_user_ignored(input):
            return False

        if not dm and channel.type is discord.ChannelType.private:
            return False

        # If all falsifying checks fail, user has perms.
        return True

    def is_channel_ignored(self, ctx=None, server=0, channel_id=0):
        """Checks if a channel or category is ignored."""
        if ctx:
            try:
                server = ctx.guild.id
                channel = ctx.channel
                cat_id = channel.category_id
                channel_id = channel.id
            except:
                return False

            # Check category if CTX object
            if cat_id:
                self.cursor.execute(f"SELECT * FROM settings WHERE server={server} AND key=? AND value={cat_id}", ("ignore",))
                if self.cursor.fetchone():
                    return True

        # Check ID of channel.
        self.cursor.execute(f"SELECT * FROM settings WHERE server={server} AND key=? AND value={channel_id}", ("ignore",))
        if self.cursor.fetchone():
            return True
        else:
            return False

    def is_user_ignored(self, ctx):
        try:
            server = ctx.guild.id
            user_id = ctx.author.id
        except:
            return False
        self.cursor.execute(f"SELECT * FROM settings WHERE server={server} AND key=? AND value={user_id}", ("ignore",))
        if self.cursor.fetchone():
            return True
        else:
            return False

    def get_temp_room(self, ctx=None, room_id=0):
        """
        Fetches a temporary room if it exists, None if it does not.
        Requires temp_channel cog.
        Dictionary return formatted as:
        {
            "rowid": val, "user_id": val, "room_id": val, "end_time": val
        }
        """
        # Get entries.
        id = ctx.channel.id if ctx else room_id
        self.cursor.execute(f"SELECT rowid, * FROM temp_room WHERE room_id={id}")

        # Format dictionary return.
        result = self.cursor.fetchone()  # There should only ever be one entry per room.
        if not result:
            return None

        return_dict = {"rowid": result[0], "user_id": result[1], "room_id": result[2], "end_time": result[3]}
        return return_dict

    def admin_override(self, ctx):
        """If an admin calls a command, and has mentioned another user, invoke that command as if the user invoked it."""
        user = ctx.author
        if user.id in self.admins:
            user = self._override(ctx)
        return user

    def owner_override(self, ctx):
        """Allows only me to invoke a command on behalf of someone else."""
        user = ctx.author
        if user.id == self.owner_id:
            user = self._override(ctx)
        return user

    def _override(self, ctx):
        """
        Overrides a command invoke, meaning it will return a user different to the person who invoked it.
        This should only be called by other functions, such as owner_override or admin_override.
        The new user is determined either by the "user" integer variable in the message, or by a mention in the message.

        Arguments:
            ctx - The context variable provided to discord commands
        """
        user = ctx.author
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            target = int(self.get_variable(ctx.message.content, "user", type="int", default=0))
            if target:
                user = self.get_user(target)

        return user

    def create_help(self, help_dict, help_description=""):
        """
        Creates the standard help embed I use for honkbonk.

        Arguments:
            help_dict - Dictionary categorized as {category_name: [commands_in_category]}
            help_description - What to display at the top of the description.
        """
        embed = discord.Embed(color=discord.Colour.dark_purple())
        embed.description = help_description + "\n\n"

        for category in help_dict.items():
            cat_name = category[0]
            cat_commands = sorted(category[1])
            cat_commands = ", ".join(cat_commands)

            embed.description += f"**{cat_name}**\n```{cat_commands} ```\n"

        return embed

    @staticmethod
    def db_get(db, request, *args, master_dict=False):
        """Returns a database request in a nice format.
        Arguments:
            request - The request to run.
            master_dict - If set to false, return a dictionary as {key: [all_values]}. Useful for checking entries.
                Else, return a list as [{key:value,...}, {key:value,...}]. Useful for iteration.

        Returns: See master_dict
        """
        search = db.execute(request, args)  # SQLite3 request.
        columns = [name[0] for name in search.description]

        if master_dict:
            entries = search.fetchall()
            results = dict(zip(columns, zip(*entries)))
        else:
            results = []
            for entry in search.fetchall():
                results.append(dict(zip(columns, entry)))
        return results

    @staticmethod
    def db_do(db, request, *args):
        """Perform an SQLite3 query, then commit the change."""
        db.execute(request, args)
        try:
            db.execute("commit")
        except sqlite3.OperationalError:
            # Piss off giving me an error when there's nothing to commit.
            # That's not an error, that's a functional decision.
            # Sometimes I want to attempt a transaction that might be empty.
            pass

    @staticmethod
    def remove_invoke(message):
        """Removes the invoking call from a message using RegEx."""
        return re.sub("(c\.[^\s]+)", "", message, count=1)

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
    def escape_message(message):
        """Make a message 'safe' to send by removing any pings"""

        m = message
        m = m.replace("\\", "\\\\")  # Stops people undoing my escapes.
        m = m.replace("@", "@\u200b")
        m = m.replace("@everyone", f"@\u200beveryone")
        return m

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
    def time_from_now(*, milliseconds=0, seconds=0, minutes=0, hours=0, days=0, weeks=0):
        """Calculates the time from now with the provided values."""
        seconds_total = MyBot.time_to_seconds(milliseconds=milliseconds, seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks)
        return time.mktime(datetime.utcnow().timetuple()) + seconds_total

    @staticmethod
    def time_to_seconds(*, milliseconds=0, seconds=0, minutes=0, hours=0, days=0, weeks=0):
        """Converts the provided time units into seconds."""
        seconds_total = seconds
        seconds_total += milliseconds*0.000001
        seconds_total += minutes*60
        seconds_total += hours*3600
        seconds_total += days*86400
        seconds_total += weeks*604800
        return seconds_total

    # TODO: Return an object instead of a string, to give the user more control over what they display.
    @staticmethod
    def time_to_string(seconds=0, minutes=0, hours=0, days=0, weeks=0):
        """Returns the provided time as a string."""
        # Convert provided values to seconds.
        time = (weeks * 604800) + (days * 86400) + (hours * 3600) + (minutes * 60) + seconds  # This is inefficient, but looks nicer.
        weeks, remainder = divmod(time, 604800)
        days, remainder = divmod(remainder, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        timestring = ""
        if weeks:
            u = "week" if weeks == 1 else "weeks"
            timestring += f"{trunc(weeks)} {u}, "
        if days:
            u = "day" if days == 1 else "days"
            timestring += f"{trunc(days)} {u}, "
        if hours:
            u = "hour" if hours == 1 else "hours"
            timestring += f"{trunc(hours)} {u}, "
        if minutes:
            u = "minute" if minutes == 1 else "minutes"
            timestring += f"{trunc(minutes)} {u}, "
        if seconds:
            u = "second" if seconds == 1 else "seconds"
            timestring += f"{trunc(seconds)} {u}, "

        if timestring:
            timestring = timestring[:-2]  # Crop the last two characters

        return timestring

    @staticmethod
    def time_from_string(string):
        """
        Creates a time given in seconds out of a string. Accepts:
        picoseconds, nanoseconds, milliseconds, centiseconds, deciseconds seconds, minutes, hours, days, weeks
        """
        seconds = 0
        r_time = r"(\d+(?:\.\d+)?)"  # A number, optionally decimal.

        # Name of unit, followed by how many seconds each is worth.
        time_units = {
            # others
            "jiffy": 0.01,
            "friedman": 86400 * 30 * 6,
            # Metric units
            "picosecond": 0.000000000001,
            "nanosecond": 0.000000001,
            "microsecond": 0.000001,
            "millisecond": 0.001,
            "centisecond": 0.01,
            "decisecond": 0.1,
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400,
            "week": 604800,
            "month": 86400*30,  # 30 days in a month :)
        }

        # Search for the first instance of each of these.
        for unit, worth_seconds in time_units.items():
            re_string = rf"({r_time}) {unit}s?"
            match = re.search(re_string, string)
            if not match:
                continue

            t = float(match.group(1))
            seconds += t*worth_seconds

        return seconds

    @staticmethod
    def remove_indentation(string):
        indentation_amount = re.search(MyBot.r_newline_whitespace, string)
        if not indentation_amount:
            return string
        indentation_amount = indentation_amount.group(1)
        return re.sub(indentation_amount, "", string)

    @staticmethod
    def time_now():
        return time.mktime(datetime.utcnow().timetuple())  # Current Unix Epoch time.

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
        def __init__(self, chance_index=None):
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


class Scheduler:
    """
    Attributes:
        bot: A reference to the discord bot.
        schedule: A list with entries of [function, time]. Time is when the function will be triggered.
    """
    def __init__(self, bot):
        self.bot = bot
        self.timed_functions = []  # Bit of data redundancy never hurt anybody. used in refresh_schedule.
        self.schedule = []
        self.schedule_time = 0.5  # In seconds, how regularly the schedule is checked
        self.l_schedule_time = lambda arr: arr[1]  # get time from a schedule entry

    async def start(self):
        self._refresh_schedule()
        while True:
            await asyncio.sleep(self.schedule_time)
            time_now = self.bot.time_now()  # Current Unix Epoch time.
            while time_now > self.schedule[0][1]:
                function, activate_time, timer = self.schedule[0]
                await function(time_now)

                new_time = self._use_timer(timer)
                self.schedule[0][1] = new_time
                self.schedule = sorted(self.schedule, key=self.l_schedule_time)

    def _refresh_schedule(self):
        """Updates the schedule from self.timed_functions."""
        new_schedule = []
        for function, timer in self.timed_functions:
            try:
                new_time = self._use_timer(timer)
                new_schedule.append([function, new_time, timer])
            except TypeError as e:
                print(e)

        self.schedule = sorted(new_schedule, key=self.l_schedule_time)

    def refresh_timer(self, function):
        """Recalculate the trigger time on the provided function. Normally used for manual calls."""
        # I'm sure there's a simpler way to write this down, but I'm blanking right now.
        for i in range(len(self.schedule)):
            _function, _, timer = self.schedule[i]
            if _function == function:
                new_time = self._use_timer(timer)
                self.schedule[i][1] = new_time
                self.schedule = sorted(self.schedule, key=self.l_schedule_time)
                break

    def add(self, function, timer):
        """
        Adds a timed function to the scheduler.
        Arguments:
            function - The method to run each trigger.
            timer - integer or method
                Integer will cause the function to be run every (integer) seconds.
                A method will be called, and should return a Unix Epoch time in seconds of when the function should run.
        """
        self.timed_functions.append([function, timer])
        # TODO: Maybe support adding while self.start loop is running?

    def _use_timer(self, timer):
        """
        Uses a timer to calculate when a function should next be triggered.
        Returns: (int) Unix Epoch time representing a date.
        """
        time_now = self.bot.time_now()  # Current Unix Epoch time.
        if isinstance(timer, int):
            return time_now + timer
        elif callable(timer):
            return timer(time_now)
        else:
            raise TypeError(f"Scheduler was provided with type {type(timer)} for timer, should be callable or int.\n")


def allgroups(matchobject):
    """Returns all of the strings from a regex match object added together."""
    string = ""
    for s in matchobject.groups():
        if s:
            string += s

    return string


# IDEA: A function for the bot that will take an image, and turn it into a Waveform/vectorscope/histogram analysis because they look fucking rad
# IDEA: Add a "collage" function that takes in a bunch of users, and combines them into a x*y collage, like I had to for DTimeLapse
# IDEA: Twitch integration to announce streams.
# IDEA: Add timezone functions.
# IDEA: Quote database.
# IDEA: Github integration
# IDEA: emoji only channel.

# TODO: I need to update my old message variable fetching code. It's quite messy.
# TODO: Allow .disable to stop a command running in a server.
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

# FIXME: Emoji pushing doesn't properly assign ownership.
# FIXME: Clear attachments after emoji push.


if __name__ == "__main__":
    load_dotenv()  # Fetches from .env file.
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # funny bot login number
    bot_prefix = "c."  # Commands in chat should be prefixed with this.

    intents = discord.Intents.all()
    bot = MyBot(bot_prefix, intents=intents)
    bot.remove_command("help")  # the default help command is ugly and I maintain a help in my server. Also lets me control what's shown.

    # Set up logger. Modified docs version.
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)


    @bot.event
    async def on_ready():
        print(f"{bot.user} has connected to Discord :) @ {datetime.now()}")


    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            # Pat reaction.
            pats = re.search(r"c.((?:pat)+)", ctx.message.content)
            if pats:
                num = len(pats.group(1)) // 3
                await ctx.send("U" + ("wU" * num))
                return

            await ctx.send("command no no be is.")
        else:
            raise error

    loop = asyncio.get_event_loop()  # TODO: Run this loop as a background process, so the UI is the only open process?
    asyncio.ensure_future(bot.start(TOKEN))
    asyncio.ensure_future(bot.Scheduler.start())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(bot.logout())
    finally:
        loop.close()

