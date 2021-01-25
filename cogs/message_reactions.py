import discord
import math
import random
import re
from discord.ext import commands
import traceback


class Reaction(commands.Cog, name="message_reactions"):
    """Reacts to various chat messages with emotes or messages."""
    prefix = "react"
    
    def __init__(self, bot):
        self.bot = bot
        # This parses over a string and checks if it ONLY contains emoji.
        self.r_only_emoji = re.compile(
            r"^((?:<:.*?:)(\d*)(?:>)|[\s])*$")
        self.r_get_emoji = re.compile(r"(<:.*?:)(\d*)(>)")  # Finds a discord emoji in a string.

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
        self.emote_reactions = self.pull_database()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not await self.bot.has_perm(message, message_on_fail=False): return
        self.sleep_counter -= 1
        server = message.guild.id
        msg = message.content.lower()

        if server in self.emote_reactions:
            for entry in self.emote_reactions[server]:
                reaction_to_add = entry["react"]
                pattern = entry["pattern"]
                try:
                    if re.search(pattern, msg):
                        await message.add_reaction(reaction_to_add)
                except:
                    traceback.print_exc()

        # gay reaction
        try:
            if re.search(r"\bgay\b", msg):
                await message.add_reaction("🅾️")
                await message.add_reaction("🇼")
                await message.add_reaction("🅾")
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
            if re.search(r"(gnight|good night|sleep well|gn)", msg) and self.sleep_counter <= 0:
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
            if re.search(r"(hotel?)", msg):
                await message.channel.send("trivago.")
        except:
            traceback.print_exc()

        # minions.
        try:
            if re.search(r"(minion)", msg):
                await message.add_reaction(self.rc_minion.get_value())
        except:
            traceback.print_exc()

        # quack
        try:
            # TODO: Add more variations of this word.
            if re.search(r"(quack)", msg):
                quack_file = discord.File("./attachments/quak.wav")
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
        user = ctx.author
        reaction = self.bot.get_variable(ctx.message.content, key="react", type="str", default=None)
        word = self.bot.get_variable(ctx.message.content, key="word", type="str", default=None)

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
        elif not reaction:
            await ctx.send("You need to provide a reaction.")
            return

        # Can user add a new reaction?
        ENTRIES_LIMIT = 20  # How many entries someone is allowed to make. TODO: Add to settings DB.
        WORD_SIZE_LIMIT = 3  # A word must be this or longer to be valid. TODO: Add to settings DB.
        existing_entries = self.db_get("user", user.id)
        if (len(existing_entries) > ENTRIES_LIMIT) and user.id not in self.bot.admins:
            await ctx.send(f"You cannot have more than {ENTRIES_LIMIT} custom reactions.")
            return

        # Turn "word" param into regex pattern
        # TODO: Add support for multiple emoji in one react.
        if word:
            if len(word) < WORD_SIZE_LIMIT:
                await ctx.send(f"Word must be at least {WORD_SIZE_LIMIT} characters long.")
                return
            pattern = rf"({word})"  # Not adding word boundaries around this will make it trigger more often. Chaos.

        # Verify reaction can be used by honkbonk
        try:
            await ctx.message.add_reaction(reaction)
        except:
            await ctx.send("Cannot use reaction/reaction not recognized.")
            return

        # Add reaction data to database
        self.bot.cursor.execute("INSERT into emoji_reactions VALUES (?, ?, ?, ?)", (user.id, ctx.guild.id, pattern, reaction))
        self.bot.cursor.execute("commit")
        self.emote_reactions = self.pull_database()  # Refresh the database now that it's been changed.

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

        reaction = self.bot.get_variable(ctx.message.content, key="react", type="str", default=None)

        if not reaction:
            ctx.send("Provide the emote of the reaction you wish to remove.")
            return

        self.bot.cursor.execute("SELECT * FROM emoji_reactions WHERE server=? AND reaction=?", (ctx.guild.id, reaction))
        db_result = self.bot.cursor.fetchone()
        if db_result:
            self.bot.cursor.execute("DELETE FROM emoji_reactions WHERE server=? AND reaction=?", (ctx.guild.id, reaction))
            self.bot.cursor.execute("commit")
            self.emote_reactions = self.pull_database()  # Refresh the database now that it's been changed.
            await ctx.send("Custom reaction deleted.")
        else:
            await ctx.send("Custom reaction not found.")

    @commands.command(name=f"{prefix}")
    async def display_reactions(self, ctx):
        """Display the user's documented reactions in this server."""
        # TODO: This.
        pass

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

    def pull_database(self):
        """
        {
        server_id: [{"user": val, "pattern": val, "react": val},],
        }
        """
        emote_reactions = {}
        self.bot.cursor.execute("SELECT * FROM emoji_reactions ORDER BY server")
        for entry in self.bot.cursor.fetchall():
            if not entry[1] in emote_reactions:  # Create dictionary entry if it doesn't already exist.
                emote_reactions[entry[1]] = []

            emote_reactions[entry[1]].append({"user": entry[0], "pattern": entry[2], "react": entry[3]})

        return emote_reactions

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
            "reaction STRING"  # The reaction to add.
            ")")
        cursor.execute("commit")


def setup(bot):
    bot.add_cog(Reaction(bot))
