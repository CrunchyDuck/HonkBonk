from discord.ext import commands
from urllib.request import urlopen, Request
import re


class RandomWord(commands.Cog, name="RandomWord"):
    # TODO: Switch to using BeautifulSoup or some other HTML parser.
    r_word = re.compile(r'<div id="random_word">(.*?)</div>')
    r_definition = re.compile(r'<div id="random_word_definition">(.*?)</div>')

    def __init__(self, bot):
        self.bot = bot
        #self.bot.core_help_text["modules"] += [self.prefix]

    @commands.command(name=f"word")
    async def get_random_word(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return

        try:
            word, definition = self.random_word()
        except:
            await ctx.send("Whoops! Seems to be broken! Tell Duck, because the page probably updated.")
            return

        await ctx.send(f"{word}: {definition}")

    @commands.command(name=f"madlib", aliases=["madlibs"])
    async def madlib(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        copypasta =\
            "Rawr x3 -s how are you -s on you you're so = o3o notices you have a _ o: " \
            "someone's = ;) nuzzles your _ _~ murr~ hehehe rubbies your _ _ you're so = :oooo " \
            # "rubbies more on your bulgy wolgy it doesn't stop growing ·///· kisses you and lickies your necky daddy likies (;" \
            # "nuzzles wuzzles I hope daddy really likes $: wiggles butt and squirms I want to see your big daddy meat~" \
            # "wiggles butt I have a little itch o3o wags tail can you please get my itch~ puts paws on your chest nyea~" \
            # "its a seven inch itch rubs your chest can you help me pwease squirms pwetty pwease sad face I need to be punished" \
            # "runs paws down your chest and bites lip like I need to be punished really good~ paws on your bulge as I lick my lips" \
            # "I'm getting thirsty. I can go for some milk unbuttons your pants as my eyes glow you smell so musky :v" \
            # "licks shaft mmmm~ so musky drools all over your cock your daddy meat I like fondles Mr. Fuzzy Balls hehe puts" \
            # "snout on balls and inhales deeply oh god im so hard~ licks balls punish me daddy~ nyea~ squirms more and wiggles" \
            # "butt I love your musky goodness bites lip please punish me licks lips nyea~ suckles on your tip so good licks" \
            # "pre of your cock salty goodness~ eyes role back and goes balls deep mmmm~ moans and suckles"

        # TODO: improve the speed of this.
        async with ctx.typing():
            pos = 0
            while pos < len(copypasta):
                letter = copypasta[pos]
                if letter == "_":
                    copypasta = copypasta[:pos] + self.random_noun() + copypasta[pos + 1:]
                elif letter == "=":
                    copypasta = copypasta[:pos] + self.random_adjective() + copypasta[pos + 1:]
                elif letter == "-":
                    copypasta = copypasta[:pos] + self.random_verb() + copypasta[pos + 1:]

                pos += 1

        await ctx.send(copypasta)

    def random_word(self):
        req = Request("https://randomword.com/", headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req)
        content = page.read().decode("utf-8")

        word = re.search(self.r_word, content).group(1)
        definition = re.search(self.r_definition, content).group(1)

        return word, definition

    def random_noun(self):
        req = Request("https://randomword.com/noun", headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req)
        content = page.read().decode("utf-8")

        word = re.search(self.r_word, content).group(1)

        return word

    def random_adjective(self):
        req = Request("https://randomword.com/adjective", headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req)
        content = page.read().decode("utf-8")

        word = re.search(self.r_word, content).group(1)

        return word

    def random_verb(self):
        req = Request("https://randomword.com/verb", headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req)
        content = page.read().decode("utf-8")

        word = re.search(self.r_word, content).group(1)

        return word

    @commands.command(name=f"word.help")
    async def get_random_word_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Get a random word! Provided by https://randomword.com/

        Example:
            c.word```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)


def setup(bot):
    bot.core_help_text["General"] += ["word", "madlib"]
    bot.add_cog(RandomWord(bot))


def teardown(bot):
    for l in ["word", "madlib"]:
        bot.core_help_text["General"].remove(l)
    bot.remove_cog(RandomWord(bot))