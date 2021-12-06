from discord.ext import commands
import discord
import re
import random
import helpers
import requests
from dataclasses import dataclass
from typing import List
from math import ceil


class Words(commands.Cog):
    prefix = "dict"

    def __init__(self, bot):
        self.bot = bot
        self.init_db()
        self.speedrun_nouns = self.bot.Chance({
            # normalish names
            "moat": 100,
            "bus": 100,
            "blimp": 100,
            "bomb": 100,
            "box": 100,
            "dust": 100,
            "sky": 100,
            "menu": 100,
            "death": 100,
            "cannon": 100,
            "clock": 100,
            "juice": 100,
            "tomato sauce": 100,
            "bed": 100,

            "dolphin": 100,
            "fox": 100,
            "pigeon": 100,
            "meerkat": 100,
            "dragon": 100,
            "cat": 100,
            "duck": 100,

            "fire": 100,
            "ice": 100,
            "air": 100,

            # kinda meme ones
            "egg": 100,
            "knot": 100,
            "OOB": 100,
            "cock": 100,
            "dick": 100,
            "macaroni cheese": 70,
        })
        self.speedrun_adjectives = self.bot.Chance({
            "insta": 100,
            "speed": 100,
            "speedy": 100,
            "quick": 100,
            "super": 100,
            "hyper": 100,
            "hyperspeed": 80,
            "turbo": 100,
            "early": 100,
            "crazy": 100,

            "forward": 100,
            "reverse": 100,
            "backwards": 100,
            "sideways": 100,

            "tight": 100,
            "hard": 100,
            "slow": 100,
            "bad": 100,
            "late": 100,
            "tricky": 100,
            "weak": 100,

            "big": 100,
            "small": 100,
            "strong": 100,
            "squeaky": 100,
        })
        self.speedrun_verbs = self.bot.Chance({
            "skip": 100,
            "trick": 100,
            "glitch": 100,
            "clip": 100,
            "exploit": 100,

            "avoid": 100,
            "kill": 100,
            "detonation": 100,
            "boost": 100,
            "one cycle": 100,

            "cancel": 100,
            "drop": 100,
            "pogo": 100,
            "hopping": 100,
            "roll": 100,
            "dupe": 100,
            "clone": 100,
            "swap": 100,
            "walk": 100,
            "dance": 100,
            "block": 100,
            "grab": 100,
            "peek": 100,
            "spin": 100,
            "bonk": 100,
        })
        self.speedrun_patterns = self.bot.Chance({
            "A A N": 100,
            "A A V": 100,
            "N N V": 100,
            "N A V": 100,

            "no N V": 100,

            "A V": 100,
            "A N": 100,
            "N V": 100,
            "N A": 100,

            "Nless": 70,
            "A Nless V": 70,
            "A Nless": 70,
        })

        self.uwu_faces = self.bot.Chance({
            " ": 500,
            " UwU ": 15,
            " OwO ": 15,
            " >.< ": 10,
            " o-owo ": 10,
            " OWOWO ": 10,
            " >//< ": 10,
            " >> ": 10,
            " x3 ": 10,
            " :3 ": 10,
            " :c ": 5,
            " c: ": 5,
            " :J ": 2,
            " :v ": 1
        })

        self.magic_8_ball = self.bot.Chance({
            "It is certain": 100,
            "It is decidedly so.": 100,
            "Without a doubt.": 100,
            "Yes - definitely.": 100,
            "You may rely on it.": 100,
            "As I see it, yes": 100,
            "Most likely.": 100,
            "Outlook good.": 100,
            "Yes.": 100,
            "Signs point to yes.": 100,
            "Reply hazy, try again.": 100,
            "Ask again later.": 100,
            "Better not tell you now.": 100,
            "Cannot predict now.": 100,
            "Concentrate and ask again.": 100,
            "Don't count on it.": 100,
            "My reply is no.": 100,
            "My sources say no.": 100,
            "Outlook not so good.": 100,
            "Very doubtful.": 100,
            "nyes uwu": 100,
            "nyo òwó": 100,
            "m-maybe.... >//<": 100,
            "i don't knowo wight now >>": 100
        })

        self.bot.core_help_text["Words!"] += ["speedrun", "small", "uwu", "big", "8ball"]
        self.bot.core_help_text["modules"] += [self.prefix]
        self.help_dict = {
            "Commands": [f"{self.prefix}." + name for name in ["saved"]]
        }

    def init_db(self):
        cursor = self.bot.cursor
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS saved_definitions ("
            "word STRING," 
            "definition STRING," 
            "example STRING," 
            "part_of_speech STRING," 
            "phonetic STRING," 
            "user_id INTEGER,"  
            "time INTEGER"
            ")")
        cursor.execute("commit")

    @commands.command(f"{prefix}.help")
    async def dict_module_help(self, ctx):
        """The core help command."""
        if not await self.bot.has_perm(ctx, dm=True): return
        desc = "Get the definition of a word!\nType `define {word}`, E.G `define halcyon`\nWorks in DMs."
        await ctx.send(embed=self.bot.create_help(self.help_dict, desc))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not await self.bot.has_perm(message, dm=True): return
        cnl = message.channel
        msg = message.content

        asking_for_define = re.match(r"define (.+)", msg, flags=re.IGNORECASE)
        if asking_for_define:
            api_endpoint = "https://api.dictionaryapi.dev/api/v2/entries/en/"
            word = asking_for_define.group(1).strip()
            response = requests.get(api_endpoint + word)
            if not response:
                # TODO: Implement spellcheck api?
                word = helpers.escape_message(word)
                await cnl.send(f"Could not find `{word}`!")
                return

            definition_pages = self.WordDefinition.from_api(response.json())
            first_page = self.WordDefinition.display_page(definition_pages[0])
            reply = await cnl.send(embed=first_page)
            await self.bot.ReactiveMessageManager.create_reactive_message\
                (reply, self.WordDefinition.display_page, definition_pages,
                 wrap=True, seconds_active=120,
                 users=[message.author.id],
                 custom_reactions={"💾": self.save_word})

    async def save_word(self, reacting_message, user_id):
        """Called on a `define word` by pressing the little save emoji."""
        d = reacting_message.message_pages[reacting_message.page_num]
        data = (d.search_term, d.definition, d.example, d.part_of_speech, d.phonetic, user_id, helpers.time_now())
        self.bot.cursor.execute("INSERT INTO saved_definitions VALUES(?,?,?,?,?,?,?)", data)
        self.bot.cursor.execute("commit")
        await reacting_message.message.channel.send(content=f"💾 Saved! Use `c.dict.saved` to view!")

    @commands.command(f"{prefix}.saved")
    async def show_saved_words(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        uid = ctx.author.id
        self.bot.cursor.execute(f"SELECT rowid,* FROM saved_definitions WHERE user_id={uid}")

        saved_defs = self.SavedDefinitions.from_sql(self.bot.cursor.fetchall())
        if not saved_defs:
            return await ctx.send(content="No saved words!")
        first_page = self.SavedDefinitions.display_page(saved_defs[0])
        reply = await ctx.send(embed=first_page)
        await self.bot.ReactiveMessageManager.create_reactive_message \
            (reply, self.WordDefinition.display_page, saved_defs,
             wrap=True, seconds_active=60,
             on_message_func=self.remove_saved_word,
             users=[ctx.author.id])

    async def remove_saved_word(self, message, reactive_message) -> bool:
        """Called by typing `rm #` after calling c.dict.saved"""
        try:
            entry_id = int(re.match(r"rm (\d+)", message.content).group(1))
        except AttributeError:
            return False

        # Convert entry_id to rowid
        try:
            page_num, page_pos = divmod(entry_id - 1, reactive_message.message_pages[0].per_page)
            rowid = reactive_message.message_pages[page_num].words_on_page[page_pos]["rowid"]
        except IndexError:
            await message.channel.send(f"{entry_id} invalid >:(")
            return False

        self.bot.cursor.execute(f"DELETE FROM saved_definitions WHERE rowid={rowid}")
        self.bot.cursor.execute("commit")
        await self.bot.ReactiveMessageManager.remove_reactive_message(reactive_message)
        c = random.choice(["Removed!", "vanquished...", "destroyed", "✅", "eradicated", "kerblow", "gone bye bye"])
        await message.channel.send(c)
        return True

    @commands.command(f"{prefix}.saved.help")
    async def show_saved_words_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
        Show the words you've saved! Deleting not implemented yet :)

        **Examples:**
        studying for that test
        `c.dict.saved`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @dataclass
    class WordDefinition:
        phonetic: str
        pronunciation: str
        part_of_speech: str
        definition: str
        example: str
        synonyms: List[str]
        antonyms: List[str]
        page_num: int

        search_term: str
        page_total: int

        @staticmethod
        def display_page(page):
            embed = helpers.default_embed()
            embed.title = f"**{page.search_term}**"
            embed.description = ""

            # Add pronunciation
            phonetic = f"/{page.phonetic}/"
            if page.pronunciation != "":
                # Add pronunciation hyperlink
                phonetic = f"[{phonetic}](https:{page.pronunciation})"
            embed.description += f"{phonetic}\n"

            # Add part of speech, definition and example
            embed.description += f"""*{page.part_of_speech}*\n\n**{page.definition}**\n"""
            if page.example:
                embed.description += f'"{page.example}"\n'
            embed.description += "\n"

            # Add synonyms/antonyms
            if page.synonyms:
                embed.description += "**Synonyms**\n```" + ", ".join(page.synonyms) + " ```\n"
            if page.antonyms:
                embed.description += "**Antonyms**\n```" + ", ".join(page.antonyms) + " ```\n"

            footer_text = f"Page {page.page_num}/{page.page_total}"
            embed.set_footer(text=footer_text)
            return embed

        @classmethod
        def from_api(cls, api_response):
            definitions = []

            page_num = 1
            for group in api_response:
                word = group["word"]
                phonetic = group.get("phonetic", "")
                try:
                    pronunciation = group["phonetics"][0]["audio"]
                except Exception as e:
                    pronunciation = ""

                for meaning in group["meanings"]:
                    part_of_speech = meaning["partOfSpeech"]
                    for d in meaning["definitions"]:
                        ex = group.get("example", "")
                        c = cls(phonetic, pronunciation, part_of_speech, d["definition"], ex, d["synonyms"], d["antonyms"],
                                page_num, word, -1)
                        definitions.append(c)
                        page_num += 1

            page_total = page_num - 1
            for definition in definitions:
                definition.page_total = page_total

            return definitions

    @dataclass
    class SavedDefinitions:
        words_on_page: List[List]
        page_num: int

        page_total: int
        per_page: int

        @staticmethod
        def display_page(page):
            embed = helpers.default_embed()
            embed.title = f"**Saved definitions**"
            embed.description = ""
            for i, word_data in enumerate(page.words_on_page):
                word = word_data["word"]
                definition = word_data["definition"]
                position = i + 1 + (page.page_num * page.per_page)
                embed.description += f"`{position}.` **{word}**: {definition}\n"
            footer_text = f"Page {page.page_num + 1}/{page.page_total} | Type \"rm 1\" to remove entry 1."
            embed.set_footer(text=footer_text)
            return embed

        @classmethod
        def from_sql(cls, sql_result, results_per_page=20):
            ret = []

            page_total = ceil(len(sql_result) / results_per_page)
            for page_num in range(page_total):
                from_i = page_num * results_per_page
                to_i = (page_num + 1) * results_per_page
                words_on_page = sql_result[from_i:to_i]

                page = cls(words_on_page, page_num, page_total, results_per_page)
                ret.append(page)
            return ret


    @commands.command(aliases=["speedrun"])
    async def speedrun_terms(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        # A pattern that just ends "less" to the end of a noun.
        pattern = self.speedrun_patterns.get_value()
        message = ""
        for letter in pattern:
            if letter == "N":
                message += self.speedrun_nouns.get_value()
            elif letter == "V":
                message += self.speedrun_verbs.get_value()
            elif letter == "A":
                message += self.speedrun_adjectives.get_value()
            else:
                message += letter
        await ctx.send(message)

    @commands.command(aliases=["small"])
    async def make_superscript(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        msg = helpers.remove_invoke(ctx.message.content).strip()
        if not msg:
            await ctx.send("Can't superscript nothing :(")
            return

        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-=()?"
        alphabet_superscript = "ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖqʳˢᵗᵘᵛʷˣʸᶻᴬᴮCᴰᴱFᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿSᵀᵁⱽᵂᵡᵞᶻ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ˀ"
        superscript = str.maketrans(alphabet, alphabet_superscript)

        await ctx.send(msg.translate(superscript))

    @commands.command(aliases=["uwu", "owo"])
    async def make_uwu(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        msg = helpers.remove_invoke(ctx.message.content).strip()
        if not msg:
            await ctx.send("Youwu have to add a message in owdew to UwU-ify it >.<")
            return

        pos = 0
        while pos < len(msg):
            letter = msg[pos]

            if letter in "rl":
                msg = msg[:pos] + "w" + msg[pos + 1:]
                letter = "w"
            elif letter in "RL":
                msg = msg[:pos] + "W" + msg[pos + 1:]
                letter = "W"
            elif letter == " ":
                emote_to_add = self.uwu_faces.get_value()
                msg = msg[:pos] + emote_to_add + msg[pos + 1:]
                pos += len(emote_to_add) - 1

            if msg[pos - 1] == " ":
                chance = random.random()
                if letter.isalpha() and chance > 0.93:
                    msg = msg[:pos] + f"{letter}-{letter}" + msg[pos + 1:]

            pos += 1

        await ctx.send(msg[:2000])

    @commands.command(name="big")
    async def make_fullwidth(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        msg = helpers.remove_invoke(ctx.message.content).strip()
        if not msg:
            await ctx.send("Can't big nothing :(")
            return

        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-=()? "
        alphabet_big = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９+－＝（）？　"
        superscript = str.maketrans(alphabet, alphabet_big)

        await ctx.send(msg.translate(superscript))

    @commands.command(name="8ball")
    async def magic_8_ball(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return

        reply = self.magic_8_ball.get_value()
        await ctx.send(reply)

    @commands.command(aliases=[f"speedrun.help"])
    async def speedrun_terms_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            gives you a **unique** speedrun trick name

            **Examples:**
            name your new epic fortnite trick
            `c.speedrun`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(name="small.help")
    async def make_superscript_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            ᴹᵃᵏᵉ ᵃ ˢᵉⁿᵗᵉⁿᶜᵉ ˢᵐᵃˡˡ :)

            **Examples:**
            `c.small i am a fairy`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(name="big.help")
    async def make_fullwidth_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            ｍａｋｅ　ｂｉｇ

            **Examples:**
            `c.big deez nuts`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=["owo.help", "uwu.help"])
    async def make_uwu_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            make vewy soft x3c

            **Examples:**
            `c.owo hello`
            `c.uwu how are you doing today`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command("8ball.help")
    async def magic_8_ball_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            GET FACTS.

            **Examples:**
            FACT.
            `c.8ball PIDGE CUTE? (yes)`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    # @commands.command(name="shuffle.help")
    # async def shuffle_word_help(self, ctx):
    #     if not await self.bot.has_perm(ctx, dm=True): return
    #     docstring = """
    #     ```Accept in a sentence, group (pattern) words together, and shuffle the order.
    #     The message to be shuffled should be on a new line after the command.
    #
    #     Arguments:
    #         pattern - A sequence of how many words to be grouped together.
    #         E.G "3,1,1" will group 3 words, then 1, then 1, then loop to group 3, 1, 1, 3...
    #         default = "3,1,1"
    #
    #     Example:
    #         c.shuffle
    #         owo hewwo whats this
    #
    #         c.shuffle pattern="1"
    #         chaotic shuffling```
    #     """
    #     docstring = self.bot.remove_indentation(docstring)
    #     await ctx.send(docstring)
    #
    # @commands.command(name="shuffle")
    # async def shuffle_word(self, ctx):
    #     """```Accept in a sentence, group (pattern) words together, and shuffle the order.
    #     The message to be shuffled should be on a new line after the command.
    #
    #     Arguments:
    #         pattern - A sequence of how many words to be grouped together.
    #         E.G "3,1,1" will group 3 words, then 1, then 1, then loop to group 3, 1, 1, 3...
    #         default = "3,1,1"
    #
    #     Example:
    #         c.shuffle
    #         owo hewwo whats this
    #
    #         c.shuffle pattern="1"
    #         chaotic shuffling```
    #     """
    #     if not await self.bot.has_perm(ctx, dm=True): return
    #     pattern = self.bot.get_variable(ctx.message.content, "pattern", type="str", default="3,1,1")
    #
    #     # Convert pattern into an array of integers.
    #     pattern = pattern.split(",")
    #     for i in range(len(pattern)):
    #         try:
    #             pattern[i] = int(pattern[i])
    #         except:
    #             await ctx.send("Patterns must be numbers separated by commands E.G 3,1,1")
    #             return
    #
    #     # Fetch message to shuffle
    #     sentence = ctx.message.content.split("\n", 1)  # Get text after first new line.
    #     if len(sentence) < 2:
    #         await ctx.send("Place a new line between the command and the text to shuffle.")
    #         return
    #     sentence = sentence[1]
    #
    #     # Group words of the sentence into an list.
    #     words = sentence.split(" ")
    #     word_group = ""
    #     words_grouped = []
    #     i = 0
    #     j = 0
    #     for word in words:
    #         word_group += f"{word} "
    #         i += 1
    #         if i == pattern[j % len(pattern)]:
    #             words_grouped.append(word_group[:-1])
    #             word_group = ""
    #             i = 0
    #             j += 1
    #     if word_group:
    #         words_grouped.append(word_group)
    #
    #     # Shuffle grouped list and send the result
    #     shuffle(words_grouped)
    #     sentence = ""
    #     for word in words_grouped:
    #         sentence += f"{word} "
    #
    #     await ctx.send(sentence)


def setup(bot):
    #bot.core_help_text["modules"] += ["vc"]
    bot.add_cog(Words(bot))
