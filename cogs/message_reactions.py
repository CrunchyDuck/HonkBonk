import discord
import math
import random
import re
from discord.ext import commands
import traceback


# TODO: Document how many times a reaction is called, and what module it was called from.
class Reaction(commands.Cog, name="message_reactions"):
    """Reacts to various chat messages with emotes or messages."""
    prefix = "react"
    
    def __init__(self, bot):
        self.bot = bot
        # This parses over a string and checks if it ONLY contains emoji.
        self.r_only_emoji = re.compile(
            r"^((?:<:.*?:)(\d*)(?:>)|[\s])*$")
        self.r_get_emoji = re.compile(r"(<:.*?:)(\d*)(>)")  # Finds a discord emoji in a string.
        self.r_react_add = re.compile(r"(?:c\.react\.add )(.+?)(?= pattern=| word=)")
        # From https://regexr.com/3ajfi
        self.r_website = re.compile(r"([--:\w?@%&+~#=]*\.[a-z]{2,4}\/{0,2})((?:[?&](?:\w+)=(?:\w+))+|[--:\w?@%&+~#=]+)?")

        self.emote_reactions = []  # Filled in self.refresh_database()
        # There must be at least this many messages since the last time the "good night" wishes triggered.
        self.sleep_counter = 20
        
        self.rc_furry = self.bot.Chance({
            # Very likely
            "🦊": 150,  # Fox
            "🐺": 150,  # Wolf
            
            # Common
            "🐱": 100,  # Cat face
            "🐈": 100,  # Cat
            "🐯": 100,  # Dog?
            "🦦": 75,  # Otter!
            "🐶": 75,  # Dog alt
            "🕊️": 75,  # Bird

            # Unlikely
            "🦝": 50,  # raccoon
            "🐈‍⬛": 50,  # Black cat
            "🦁": 50,  # lion?
            "🐹": 50,  # hamster
            "🐰": 50,  # rabbit
            "🐿": 50,  # Chipmunk
            "🦔": 50,  # Hedgehog
            "🦘": 50,  # Kangaroo
            "🐑": 50,  # Sheep
            "🐦": 50,  # Bird
            
            # Very unlikely
            "🐬": 40,  # Dolphin!
            "🦜": 40,  # Parrot
            "🦚": 30,  # Peacock
            "🐷": 35,  # pig?
            "🐄": 25,  # pig body.
            "🦒": 30,  # giraffe
            
            # Special
            "🐲": 20,  # Dragon face
            "🕷": 10,  # spider
            "🦂": 10,  # mosquito
            "🍌": 10,  # banana
            "🥝": 10,  # kiwi (the fruit)
            "🥥": 10,  # coconut (the fruit)
            "<:furry:772239467544576021>": 10,  # Custom Clyde gay emote
        })
        self.rc_goodnight = self.bot.Chance({
            "Sleep well!": 100,
            "Good night <3": 100,
            "Oyasuminasai!": 100,
            "Sweet dreams~": 100,
            "Gnight!": 100,
            
            "To the land of imagination with you!": 70,
            "bueno dormir :flag_es:": 70,
            "お休み！": 70,
            "nyadios": 70,
            "oidhche mhath": 70,
            "أبام": 70,
            
            "https://www.youtube.com/watch?v=Udj-o2m39NA": 50,  # Go the fuck to sleep story
            "Nya uwu x3 s-sleep w-well~~~ kyaaah!": 50,  # gross gay furry
            "https://youtu.be/46vpxCRCbEs": 50,  # scottish "go the fuck to sleep"
        })
        self.rc_minion = self.bot.Chance({
            "<:eld_eye:644875878177964052>": 1,
            "<:eld_happy:644875878416908336>": 1,
            "<:eld_minion:644875880094498826>": 1,
            "<:eld_sad:644876502957162506>": 1,
            "<:eld_unknown:644876503162552321>": 1,
        })

        self.db_init()
        self.refresh_database()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not await self.bot.has_perm(message, message_on_fail=False): return
        self.sleep_counter -= 1
        server = message.guild.id if message.guild else 0
        msg = message.content.lower()

        # Ignore messages with links.
        if re.search(self.r_website, msg): return

        if server in self.emote_reactions:
            for user in self.emote_reactions[server]:  # Search through each user's custom emotes.
                for entry in self.emote_reactions[server][user]:
                    reaction_to_add = entry["react"]
                    pattern = entry["pattern"]
                    rowid = entry["rowid"]
                    try:
                        if re.search(pattern, msg):
                            await self.react_with_pattern(message, reaction_to_add)
                            self.bot.cursor.execute(f"UPDATE emoji_reactions SET triggered=triggered + 1 WHERE rowid={rowid}")
                            self.bot.cursor.execute("commit")
                    except discord.errors.Forbidden:  # Don't have permission/too many emoji attached to message.
                        pass
                    except discord.errors.HTTPException:  # Seems to trigger only when an emoji is missing.
                        traceback.print_exc()  # TODO: This will spam the console if the emoji doesn't exist.
                    except:
                        traceback.print_exc()

        # React back at emoji
        try:
            if re.search(self.r_only_emoji, message.content):  # Message only contains emoji
                for match in re.findall(self.r_get_emoji, message.content):
                    val = "".join(match)
                    await message.add_reaction(val)
        except:
            pass

        # Goodnight wishes
        try:
            if re.search(r"(gnight|good night|sleep well|\bgn\b)", msg) and self.sleep_counter <= 0:
                react = self.rc_goodnight.get_value()
                await message.channel.send(react)
                self.sleep_counter = 20
        except:
            traceback.print_exc()

        # Furry reaction
        try:
            if re.search(r"(\s|\b|^)(f+u+r+(i+e+s+|y*))(\s|\b|$)",
                         msg):  # Match any f before u before r combination, with an optional y at the end. Essentially, any possibly way to spell "fur" or "furry".
                react = self.rc_furry.get_value()
                await message.add_reaction(react)
        except:
            traceback.print_exc()
        
        # Attempt to react to built-in emoji.
        # What I'm doing here is trying to "react" using the contents of the user's message.
        # It should only succeed if the user's message contains a single built in emoji.
        try:
            await message.add_reaction(message.content)
        except:
            pass

        # hotel.
        try:
            if re.search(r"(hotel\?)", msg):
                await message.channel.send("trivago.")
        except:
            traceback.print_exc()

        # minions.
        try:
            if re.search(r"(minion|banana)", msg):
                await message.add_reaction(self.rc_minion.get_value())
        except:
            traceback.print_exc()

        # quack
        try:
            # TODO: Add more variations of this word.
            if re.search(r"(quack)", msg):
                quack_file = discord.File("./attachments/quak.mp3")
                await message.channel.send(file=quack_file)
        except:
            traceback.print_exc()
    
    @commands.command(name=f"{prefix}.chance")
    async def chance(self, ctx):
        """
        Returns the percentage chance of a given entry in rc_furry to be used as a reaction.
        Arguments:
            val: The emoji to check for.
        Example:
            c.react.chance val=":furry:"
            c.react.chance val=":parrot:"
        """
        if not await self.bot.has_perm(ctx): return
        char = self.bot.get_variable(ctx.message.content, key="val", type="str")
        try:
            chance = self.rc_furry.get_chance(char, weight=False) * 100
            await ctx.send(f"{chance}%")
        except ValueError:
            await ctx.send("Not a valid reaction!")

    @commands.command(name=f"{prefix}.add")
    async def add_reaction(self, ctx):
        """
        Add a word reaction to the database.
        Arguments:
            react: The reaction to add to triggered messages
            word: The word to apply this reaction to.
            pattern: A regex pattern of strings to apply the reaction to.
        """
        if not await self.bot.has_perm(ctx): return
        user = self.bot.admin_override(ctx)
        reaction = re.search(self.r_react_add, ctx.message.content)
        word = self.bot.get_variable(ctx.message.content, key="word", type="str", default=None)

        if not reaction:
            await ctx.send("You need to provide either a word or a RegEx pattern.")
            return
        reaction = reaction.group(1)

        # FIXME: pattern is completely unsecure and anyone can put anything in. Right now i'm running off of trust.
        pattern_search = re.search(r"""pattern=(?:([`])(.+?)(\1))""", ctx.message.content)
        if pattern_search:
            pattern = pattern_search.group(2)
            try:
                re.compile(pattern)
            except re.error:
                await ctx.send("RegEx pattern is invalid.")  # TODO: Give more information about why.
        else:
            pattern = None

        if not word and not pattern:
            await ctx.send("You need to provide either a word or a RegEx pattern.")
            return

        # Can user add a new reaction?
        ENTRIES_LIMIT = 10  # How many entries someone is allowed to make. TODO: Add to settings DB.
        WORD_SIZE_LIMIT = 3  # A word must be this or longer to be valid. TODO: Add to settings DB.
        existing_entries = self.db_get("user", user.id)
        if (len(existing_entries) > ENTRIES_LIMIT) and user.id not in self.bot.admins:
            await ctx.send(f"You cannot have more than {ENTRIES_LIMIT} custom reactions.")
            return

        # Turn "word" param into regex pattern
        if word:
            if len(word) < WORD_SIZE_LIMIT:
                await ctx.send(f"Word must be at least {WORD_SIZE_LIMIT} characters long.")
                return
            pattern = re.escape(f"{word}")  # Make the word safe for regex.

        # Verify reaction can be used by honkbonk
        try:
            await self.react_with_pattern(ctx.message, reaction)
        except:
            await ctx.send("Cannot use reaction/reaction not recognized.")
            return

        # Add reaction data to database
        self.bot.cursor.execute("INSERT into emoji_reactions VALUES (?, ?, ?, ?, ?, ?)",
                                (user.id, ctx.guild.id, pattern, reaction, 0, 0))
        self.bot.cursor.execute("commit")
        self.refresh_database()  # Refresh the database now that it's been changed.

        if word:
            await ctx.send(f"Reaction {reaction} added to \"{word}\"")
        else:
            await ctx.send(f"Reaction {reaction} added to regex pattern `{pattern}`")

    @commands.command(name=f"{prefix}.remove")
    async def remove_reaction(self, ctx):
        """
        Remove a custom reaction. Removal is based on the emote.
        Arguments:
            react: The emote that is tied to reactions to remove.
        """
        if not await self.bot.has_perm(ctx): return
        user = self.bot.admin_override(ctx)
        rowid = re.search(r"(\d+)", ctx.message.content)

        if rowid:
            rowid = rowid.group(0)
        else:
            await ctx.send("Provide the ID of the custom reaction to remove.")
            return

        if not rowid:
            await ctx.send("Provide the ID of the custom reaction you wish to remove.")
            return

        # Check the user actually owns this emote.
        self.bot.cursor.execute(f"SELECT user FROM emoji_reactions WHERE rowid={rowid}")
        result = self.bot.cursor.fetchone()
        if result:
            if user.id not in self.bot.admins and user.id != result[0]:
                await ctx.send("You don't own this reaction.")
                return
        else:
            await ctx.send("No custom reaction with this id!")
            return

        self.bot.cursor.execute(f"DELETE FROM emoji_reactions WHERE rowid={rowid}")
        self.bot.cursor.execute("commit")
        self.refresh_database()  # Refresh the database now that it's been changed.
        await ctx.send("Custom reaction deleted.")

    @commands.command(name=f"{prefix}.list")
    async def display_reactions(self, ctx):
        """Display the user's documented reactions in this server."""
        if not await self.bot.has_perm(ctx): return
        server = ctx.guild.id
        user = ctx.message.author.id
        # If the user is a bot admin, allow them to mention a user to check that person's list.
        if user in self.bot.admins:
            if ctx.message.mentions:
                user = ctx.message.mentions[0].id

        self.refresh_database()  # Refresh the database so the correct data is displayed.

        if server not in self.emote_reactions or user not in self.emote_reactions[server]:
            await ctx.send("You don't have any custom reactions in this server.")
            return

        entries = self.emote_reactions[server][user]

        # Create the embeds for the user to view.
        embed = self.bot.default_embed(None)
        num_of_entries = len(entries)

        ids = ""
        reactions = ""
        patterns = ""

        for entry in entries:
            rowid = entry["rowid"]
            reaction = entry["react"]
            pattern = entry["pattern"]
            trigger = entry["triggered"]

            ids += f"`{rowid}`\n"
            reactions += f"`({trigger})` {reaction}\n"
            patterns += f"`{pattern}"[:40] + "`\n"
            #triggers += f"{trigger}\n"
            #description += f"`{rowid}.` `{pattern}` {reaction}  triggered {triggers} times\n"

        embed.add_field(name="ID", value=ids)
        embed.add_field(name="(trig) reactions", value=reactions)
        embed.add_field(name="patterns", value=patterns)
        embed.set_footer(text=f"{num_of_entries}/10 custom reactions")

        await ctx.send(embed=embed)

    @commands.command(name=f"{prefix}.triggered")
    async def edit_triggered(self, ctx):
        """Allows an admin to change the amount of times a reaction has been triggered."""
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False): return
        values = re.search(r"(\d+) (\d+)", ctx.message.content)
        if not values:
            return

        id = values.group(1)
        value = values.group(2)

        self.bot.cursor.execute(f"UPDATE emoji_reactions SET triggered={value} WHERE server={ctx.guild.id} AND rowid={id}")
        self.bot.cursor.execute("commit")
        self.refresh_database()

        await ctx.send("Changed triggered amount!")


    @commands.command(name=f"{prefix}.chance.help")
    async def chance_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Returns the percentage chance of a given reaction to "furry"
        
        Arguments:
            val: The emoji to check for.
            
        Example:
            c.react.chance val=":furry:"
            c.react.chance val=":parrot:"```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.add.help")
    async def add_reaction_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Add a word reaction to the database. Multiple reactions can be added to one word.
        When adding emoji, they must be separated by one space.
        Admins can mention a user to invoke this command as if they were that user.
        
        Arguments:
            (Required)
            react: The reaction to add to triggered messages
            
            (One or the other)
            word: The word to apply this reaction to.
            pattern: A RegEx pattern of strings to apply the reaction to.
            
        Examples:
            c.react.add :mag_right: :mag: word="investigate"
            c.react.add :hammer: pattern=`hot|gay`
            c.react.add :rainbow_flag: pattern=`pidge` @Pidge  # Admin invoking command on behalf of another.```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.remove.help")
    async def remove_reaction_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Remove a custom reaction. Admins can mention a user to remove their reactions.
        
        Arguments:
            rowid: The ID of the reaction to remove
            
        Examples:
            c.react.remove 10  # Removes reaction with ID of 10.
            c.react.remove 9 @Pidge  # Removes a user's reaction.```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.list.help")
    async def list_reaction_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Display the user's custom reactions in this server.
        Admins can mention a user to check their reactions.
        
        Example:
            c.react.list  # Display your reactions
            c.react.list @Pidge  # Display someone else's.```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.triggered.help")
    async def list_reaction_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Allows an admin to change the amount of times a reaction has been triggered.
        
        Arguments:
            reaction_id: The custom reaction to change the values of
            amount: What to set the triggered amount to.
        
        Example:
            c.react.triggered 12 0```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.help")
    async def reaction_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring="""
        ```This module allows honkbonk to react to messages with emotes.
        Will not react to messages with URLs in them. Will not react in ignored rooms.
        Maximum reactions per person can be seen in c.react.list. Admins bypass this.
        
        c.react.chance - Get chances of specifically the built in "furry" reaction
        c.react.add - Add a custom reaction!
        c.react.remove - Remove a custom reaction!
        c.react.list - Display your custom reactions!
        c.react.triggered - Change how many times a reaction has been triggered. Admin thingy.```
        """
        await ctx.send(docstring)

    # TODO: Command that removes reactions on the last message the user sent. So I can go "gr" at HB going "owo" and he runs away.
    
    def text_to_emoji(self, string):
        # TODO: This.
        # TODO: Display what HB believes it can say, and ask if that's okay.
        # IDEA: Maybe allow people to do this to a word of their choosing.
        # IDEA: Allow people to specify a message to react to with an ID?
        text_to_emoji_dict = {
            "a": ["🅰️"],
            "b": ["🅱️"],
            "c": ["©️,©"],
            "d": [],
            "e": [],
            "f": [],
            "g": [],
            "h": [],
            "i": [],
            "j": [],
            "k": [],
            "l": [],
            "m": [],
            "n": [],
            "o": [],
            "p": [],
            "q": [],
            "r": [],
            "s": [],
            "t": [],
            "u": [],
            "v": [],
            "w": [],
            "x": [],
            "y": [],
            "z": ["💤"],
            
        }
        pass

    async def react_with_pattern(self, message, pattern):
        """Reacts using a pattern of emoji that've been submitted to the database."""
        emojis = pattern.split()  # Split the pattern by spaces.
        for emoji in emojis:
            await message.add_reaction(emoji)

    def pull_database(self):
        """
        {
        server_id: {
            user: [
                {"pattern": val, "react": val, "triggered": val, "rowid": val},
            ],
        },
        }
        """
        emote_reactions = {}
        self.bot.cursor.execute("SELECT rowid, * FROM emoji_reactions ORDER BY server")
        for entry in self.bot.cursor.fetchall():
            if not entry[2] in emote_reactions:  # Create dictionary for this server entry if it doesn't already exist.
                emote_reactions[entry[2]] = {}
            if not entry[1] in emote_reactions[entry[2]]:  # Create dictionary for this user in this server.
                emote_reactions[entry[2]][entry[1]] = []

            emote_reactions[entry[2]][entry[1]].append({"pattern": entry[3], "react": entry[4], "triggered": entry[5], "rowid": entry[0]})

        return emote_reactions

    def refresh_database(self):
        self.emote_reactions = self.pull_database()

    def db_get(self, field, value):
        """
        Searches the emoji_reactions table in the database and returns all matches
        Arguments:
            field: The column to search in the database
            value: What the field should contain to match
        Returns:
            Array of dictionaries. Dictionaries contain the fields:
                user: The ID of the user this entry is attributed to
                pattern: The RegEx pattern to search a string with
                reaction: What reaction to add
        """
        cursor = self.bot.cursor
        result_dict = []  # An array that stores dictionaries containing the results

        cursor.execute(f"SELECT * FROM emoji_reactions WHERE {field}=?", (value,))
        for entry in cursor.fetchall():
            result_dict.append({"user": entry[0], "server": entry[1], "pattern": entry[2], "reaction": entry[3]})

        return result_dict

    def db_init(self):
        cursor = self.bot.cursor
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS emoji_reactions ("  # Emoji reactions to messages
            "user INTEGER,"  # ID of the user who added this.
            "server INTEGER,"  # The server this was added to.
            "pattern STRING,"  # The regex pattern to search with.
            "reaction STRING,"  # The reaction to add.
            "triggered INTEGER,"  # Number of times this has been triggered.
            "snowflake INTEGER"  # Redundant column, but SQLite 3 doesn't let you remove columns???
            ")")
        #cursor.execute(
        #    "CREATE TABLE IF NOT EXISTS pending_reactions ("  # A table that stores the proposed reactions by users.
        #    "user INTEGER,"  # ID of the user who added this.
        #    "server INTEGER,"  # The server this was added to.
        #    "pattern STRING,"  # The regex pattern to search with.
        #    "reaction STRING,"  # The reaction to add.
        #    "triggered INTEGER,"  # Number of times this has been triggered.
        #    "snowflake INTEGER"
        #    ")")
        cursor.execute("commit")


def setup(bot):
    bot.add_cog(Reaction(bot))
