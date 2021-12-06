import discord
from discord.ext import commands
import helpers
from dataclasses import dataclass
from math import ceil
from datetime import datetime
from typing import List


class NameHistory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.core_help_text["General"] += ["name_history"]
        self.init_db()

    def init_db(self):
        cursor = self.bot.cursor
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS username_history ("
            "before_name STRING,"  # What their old name was.
            "after_name STRING,"  # What their new name is.
            "guild_id INTEGER,"  # ID of the guild. 0 if no guild.
            "user_id INTEGER,"  # Whose name it is.
            "time INTEGER"  # When the name was changed to this
            ")")
        cursor.execute("commit")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        old_name = before.display_name
        new_name = after.display_name
        time = helpers.time_now()
        user_id = after.id
        guild_id = after.guild.id

        if before.nick == after.nick:
            return

        c = self.bot.cursor
        c.execute("""INSERT INTO username_history VALUES(?,?,?,?,?)""", (old_name, new_name, guild_id, user_id, time))
        c.execute("commit")

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        old_name = before.name
        new_name = after.name
        time = helpers.time_now()
        user_id = after.id
        guild_id = 0

        if old_name == new_name:
            return

        c = self.bot.cursor
        c.execute("""INSERT INTO username_history VALUES(?,?,?,?,?)""", (old_name, new_name, guild_id, user_id, time))
        c.execute("commit")

    @commands.command(aliases=[f"name_history"])
    async def username_history(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        if not ctx.message.mentions:
            target_user = ctx.author
        else:
            target_user = ctx.message.mentions[0]
        embed = embed_fetching_data()
        message = await ctx.send(embed=embed)
        pages = self.name_history_member(target_user, ctx.guild.id, ctx.guild.name)
        method = self.ChangedNamePage.display_page_user

        if not pages:
            embed.title = "naem his story"
            embed.description = "w-w-whoops no history x3"
            await message.edit(embed=embed)
            return

        embed = method(pages[0])
        await message.edit(embed=embed)
        await self.bot.ReactiveMessageManager.create_reactive_message(message, method, pages, users=[ctx.author.id])

    def name_history_guild(self, guild_id: int, guild_name: str) -> list:
        self.bot.cursor.execute("SELECT * FROM username_history WHERE guild_id=? ORDER BY time DESC", (guild_id,))
        changed_names = self.bot.cursor.fetchall()
        per_page = 20
        number_of_pages = ceil(len(changed_names) / per_page)
        pages = []
        for page_num in range(number_of_pages):
            from_i = page_num * per_page
            to_i = (page_num + 1) * per_page
            changed_names_in_page = changed_names[from_i:to_i]
            p = self.ChangedNamePage(changed_names_in_page, "", page_num, number_of_pages, guild_name)
            pages.append(p)
        return pages

    def name_history_member(self, member, guild_id: int, guild_name: str) -> list:
        self.bot.cursor.execute("SELECT * FROM username_history WHERE guild_id=? AND user_id=? ORDER BY time DESC", (guild_id, member.id,))
        changed_names = self.bot.cursor.fetchall()
        user_name = member.display_name
        thumbnail_id = member.avatar_url

        per_page = 5
        number_of_pages = ceil(len(changed_names) / per_page)
        pages = []
        for page_num in range(number_of_pages):
            from_i = page_num * per_page
            to_i = (page_num + 1) * per_page
            changed_names_in_page = changed_names[from_i:to_i]
            name = f"{user_name} in {guild_name}"
            p = self.ChangedNamePage(changed_names_in_page, thumbnail_id, page_num, number_of_pages, name)
            pages.append(p)
        return pages

    # === Help functions ===
    @commands.command(aliases=[f"name_history.help"])
    async def name_history_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            Display username changes!
            
            Examples:
            See server changes
            `c.name_changes`
            See my changes
            `c.name_changes @CrunchyDuck`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @dataclass
    class ChangedNamePage:
        row_objs: List[object]  # Search results from an SQLite3 query.
        icon_url: str
        page_num: int

        page_total: int
        target_name: str

        @staticmethod
        def display_page_user(page_data: 'NameHistory.ChangedNamePage') -> discord.Embed:
            embed = helpers.default_embed()
            embed.title = f"Name history for {page_data.target_name}"
            embed.description = ""
            for line in page_data.row_objs:
                before = line["before_name"]
                after = line["after_name"]
                #time = datetime.utcfromtimestamp(line["time"]).strftime("%Y/%m/%d %H:%M")
                embed.description += f"`{after}`\n\n"
            if page_data.page_num == page_data.page_total - 1:
                embed.description += f"`{before}`"
            footer_text = f"Page {page_data.page_num + 1}/{page_data.page_total}"

            embed.set_footer(text=footer_text)
            embed.set_thumbnail(url=page_data.icon_url)
            return embed


def embed_fetching_data():
    """
    Modifies an embed's description and thumbnail to display the progress through downloading a video.
    Arguments:
        embed - An embed to modify the description of.
        item - The PlaylistItem being downloaded.
        percent - Provided as a decimal from 0 to 1
    """
    embed = helpers.default_embed()
    embed.title = "Fetching data..."
    embed.description = "wait a bit :)"
    return embed


def setup(bot):
    #bot.core_help_text["modules"] += ["vc"]
    bot.add_cog(NameHistory(bot))
