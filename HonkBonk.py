import asyncio
import discord
import logging
import sqlite3
from datetime import datetime
from discord.ext import commands
from random import random
from collections import defaultdict
from pathlib import Path
from json import loads
from scheduler import Scheduler
from reactive_message import ReactiveMessageManager
import helpers


class MyBot(commands.Bot):
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

    def __init__(self, settings, **kwargs):
        self.settings = settings
        super().__init__(self.settings["PREFIX"], **kwargs)  # This just runs the original commands.Bot __init__ function.

        self.Scheduler = Scheduler()  # Handles commands that run on timers.
        self.ReactiveMessageManager = ReactiveMessageManager(self)

        self.owner_id = self.settings["OWNER_ID"]  # Who owns the bot
        self.uptime_seconds = helpers.time_now()  # Used to check how long the bot has been active for
        self.uptime_datetime = datetime.now()

        # Used for the "core" help command, which is called with c.help. Any non-specific commands are placed here.
        # This relies on dictionaries maintaining their declared order, rather than taking their hash order.
        self.core_help_text = {
            "modules": [],
            "General": [],
        }
        self.core_help_text = defaultdict(list, **self.core_help_text)

        # Assigned in start(), as they run on a different thread.
        self.db = None
        self.cursor = None

    async def honkbonk_start(self, *args, **kwargs):
        """
        Log into discord and begin running commands.
        """
        self.db = sqlite3.connect("bot.db")  # Prepare DB for access from other modules.
        self.db.row_factory = sqlite3.Row  # Allow elements to be returned as dictionaries.
        self.cursor = self.db.cursor()

        # Find and load cogs.
        #cogs = ["cogs.core"]  # Manually loaded for now

        self.load_extension("cogs.core")
        self.load_extension("cogs.vc")
        self.load_extension("cogs.name_history")
        self.load_extension("cogs.message_reactions")
        self.load_extension("cogs.word")
        await self.start(self.settings["BOT_TOKEN"], *args, **kwargs)

    async def has_perm(self, input, *, owner_only=False, dm=True, ignore_bot=True):
        """
        Common permissions to be checked to see if a command should run in the given context.

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
        elif owner_only:
            return False

        # An admin should only be stopped from a command if the room is ignored.
        # if not ignored_rooms and self.is_channel_ignored(input):
        #     return False

        if ignore_bot and is_bot:
            return False

        #if not banned_users and self.is_user_ignored(input):
        #    return False

        if not dm and channel.type is discord.ChannelType.private:
            return False

        # If all falsifying checks fail, user has perms.
        return True

    # def is_channel_ignored(self, ctx=None, server=0, channel_id=0):
    #     """Checks if a channel or category is ignored."""
    #     if ctx:
    #         try:
    #             server = ctx.guild.id
    #             channel = ctx.channel
    #             cat_id = channel.category_id
    #             channel_id = channel.id
    #         except:
    #             return False
    #
    #         # Check category if CTX object
    #         if cat_id:
    #             self.cursor.execute(f"SELECT * FROM settings WHERE server={server} AND key=? AND value={cat_id}", ("ignore",))
    #             if self.cursor.fetchone():
    #                 return True
    #
    #     # Check ID of channel.
    #     self.cursor.execute(f"SELECT * FROM settings WHERE server={server} AND key=? AND value={channel_id}", ("ignore",))
    #     if self.cursor.fetchone():
    #         return True
    #     else:
    #         return False

    # def is_user_ignored(self, ctx):
    #     try:
    #         server = ctx.guild.id
    #         user_id = ctx.author.id
    #     except:
    #         return False
    #     self.cursor.execute(f"SELECT * FROM settings WHERE server={server} AND key=? AND value={user_id}", ("ignore",))
    #     if self.cursor.fetchone():
    #         return True
    #     else:
    #         return False

    # def admin_override(self, ctx):
    #     """If an admin calls a command, and has mentioned another user, invoke that command as if the user invoked it."""
    #     # TODO: Rework this
    #     user = ctx.author
    #     if user.id in self.admins:
    #         user = self._override(ctx)
    #     return user

    # def owner_override(self, ctx):
    #     """Allows only me to invoke a command on behalf of someone else."""
    #     user = ctx.author
    #     if user.id == self.owner_id:
    #         user = self._override(ctx)
    #     return user
    #
    # def _override(self, ctx):
    #     """
    #     Overrides a command invoke, meaning it will return a user different to the person who invoked it.
    #     This should only be called by other functions, such as owner_override or admin_override.
    #     The new user is determined either by the "user" integer variable in the message, or by a mention in the message.
    #
    #     Arguments:
    #         ctx - The context variable provided to discord commands
    #     """
    #     user = ctx.author
    #     if ctx.message.mentions:
    #         user = ctx.message.mentions[0]
    #     else:
    #         target = int(self.get_variable(ctx.message.content, "user", type="int", default=0))
    #         if target:
    #             user = self.get_user(target)
    #
    #     return user

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

    class Chance:
        # TODO: Maybe add in chance "brackets", meaning all things in that bracket add up up to a certain percentage.
        # TODO: Add command to check the chance x amount of weight has in the current index.
        """
        An object that can return a random result from a predefined dictionary of chances and values.
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
# TODO: Madlib for sentences like "X is not a valid Ninjutsu weapon"

# FIXME: Emoji pushing doesn't properly assign ownership.
# FIXME: Clear attachments after emoji push.

def main():
    # Set up logger.
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    loop = asyncio.get_event_loop()
    # Create HonkBonk.
    with open("settings.json", "r") as f:
        json_text = helpers.remove_python_comments(f.read())
        settings = loads(json_text)  # API tokens/bot settings
    intents = discord.Intents.all()  # All intents makes quick testing easier.
    bot = MyBot(settings, intents=intents)
    bot.remove_command("help")  # Default help is ugly.
    asyncio.ensure_future(bot.honkbonk_start())
    asyncio.ensure_future(bot.Scheduler.start())

    # Create archivist bot.
    if "ARCHIVE_BOT_TOKEN" in settings:
        archive_bot = MyBot(settings, intents=intents)
        archive_bot.command_prefix = settings["ARCHIVE_PREFIX"]
        archive_bot.remove_command("help")
        archive_bot.load_extension("cogs.archive_channel")
        asyncio.ensure_future(archive_bot.start(settings["ARCHIVE_BOT_TOKEN"]))

    if "STEAM_BOT_TOKEN" in settings:
        archive_bot = MyBot(settings, intents=intents)
        archive_bot.command_prefix = settings["STEAM_BOT_PREFIX"]
        archive_bot.remove_command("help")
        archive_bot.load_extension("cogs.steam")
        asyncio.ensure_future(archive_bot.start(settings["STEAM_BOT_TOKEN"]))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(bot.logout())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
