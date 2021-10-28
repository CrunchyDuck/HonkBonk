from discord.ext import commands
import random
import helpers


class Words(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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

        self.bot.core_help_text["Words!"] += ["speedrun", "small", "uwu", "big", "8ball"]

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
