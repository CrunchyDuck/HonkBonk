from discord.ext import commands
from urllib.request import urlopen, Request
import re


class RandomWord(commands.Cog, name="RandomWord"):
    r_word = re.compile(r'<div id="random_word">(.*?)</div>')  # This is surely not robust, but oh well.
    r_definition = re.compile(r'<div id="random_word_definition">(.*?)</div>')

    def __init__(self, bot):
        self.bot = bot
        #self.bot.core_help_text["modules"] += [self.prefix]
        self.bot.core_help_text["General"] += ["word"]

    @commands.command(name=f"word")
    async def get_random_word(self, ctx):
        if not await self.bot.has_perm(ctx, admin=False, dm=True): return
        req = Request("https://randomword.com/", headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req)
        content = page.read().decode("utf-8")

        try:
            word = re.search(self.r_word, content).group(1)
            definition = re.search(self.r_definition, content).group(1)
        except:
            await ctx.send("Whoops! Seems to be broken! Tell Duck, because the page probably updated.")
            return

        await ctx.send(f"{word}: {definition}")

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
    bot.add_cog(RandomWord(bot))