import requests
from random import randint
from discord.ext import commands
from re import search
from urllib.request import urlopen, Request

class sinner(commands.Cog, name="sinner"):
    prefix = "e"

    def __init__(self, bot):
        self.bot = bot
        self.db_init()
        self.user_agent = {"user-agent": "Random Discord Tag"}
        # self.db_fill(category=0, post_limit=1000)
        # self.db_fill(category=4, post_limit=400)
        # self.db_fill(category=5, post_limit=300)
        self.bot.core_help_text["modules"] += [self.prefix]
        self.help_text = {
            "owo": ["e.idea", "e.sentence", "e.tag_count", "e.search"],
        }

    @commands.command(name=f"{prefix}.idea")
    async def give_drawing_idea(self, ctx):
        if not await self.bot.has_perm(ctx, admin=False, dm=True): return
        species = self.bot.get_variable(ctx.message.content, key="species", type="keyword", default=False)
        char = self.bot.get_variable(ctx.message.content, key="character", type="keyword", default=False)
        tag = self.bot.get_variable(ctx.message.content, key="tag", type="keyword", default=False)

        cat = None
        if species:
            cat = 5
        elif char:
            cat = 4
        elif tag:
            cat = 0

        query = "SELECT * FROM e6_tags"
        if cat:
            query += f" WHERE category_id={cat}"

        self.bot.cursor.execute(query)
        res = self.bot.cursor.fetchall()
        num_tags = len(res)
        pos = randint(0, num_tags-1)

        # Format for discord.
        response = res[pos][0]
        response = response.replace("_", "\\_")
        await ctx.send(response)

    @commands.command(name=f"{prefix}.sentence")
    async def run_on_sentence(self, ctx):
        if not await self.bot.has_perm(ctx, admin=False, dm=True): return
        num_words = int(self.bot.get_variable(ctx.message.content, type="int", default=3))
        num_words = min(num_words, 20)

        self.bot.cursor.execute("SELECT COUNT(*) FROM e6_tags")
        num_tags = self.bot.cursor.fetchone()[0]

        self.bot.cursor.execute("SELECT * FROM e6_tags")
        res = self.bot.cursor.fetchall()
        sentence = ""
        for i in range(num_words):
            pos = randint(0, num_tags-1)
            sentence += f"{res[pos][0]} "

        # Format for discord.
        sentence = sentence.replace("_", "\\_")
        await ctx.send(sentence)

    @commands.command(name=f"{prefix}.tag_count")
    async def how_many_with_tag(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        re_result = search(r"c\.e\.tag_count (.+)", ctx.message.content)
        if not re_result:
            await ctx.send("Please provide a tag!")
            return
        search_tag = re_result.group(1)

        params = {"search[name_matches]": f"{search_tag}"}
        res = requests.get("https://e621.net/tags.json", headers=self.user_agent, params=params).json()
        if "tags" in res:
            await ctx.send(f"No results found for {search_tag}.")
            return
        await ctx.send(f"{res[0]['post_count']} results with the tag `{search_tag}`")

    @commands.command(name=f"{prefix}.search")
    async def search_for_tag(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        valid_tags = []
        valid_aliases = []

        tag_post_limit = int(self.bot.get_variable(ctx.message.content, type="int", default=100))
        re_result = search(r"c\.e\.search ([^ \n]+)", ctx.message.content)
        if not re_result:
            await ctx.send("give. me. a. tag.")
            return
        search_tag = re_result.group(1)

        # Get matching tags.
        params = {"search[name_matches]": f"*{search_tag}*", "limit": 20, "page": 1, "search[order]": "count"}
        res = requests.get("https://e621.net/tags.json", headers=self.user_agent, params=params).json()
        if "tags" not in res:
            for tag_blob in res:
                if tag_blob["post_count"] < tag_post_limit:
                    break
                valid_tags.append(tag_blob["name"])

        # Get matching aliases.
        # params = {"search[name_matches]": f"*{search_tag}*", "limit": 20, "page": 1, "search[order]": "count"}
        # res = requests.get("https://e621.net/tag_aliases.json", headers=self.user_agent, params=params).json()
        # if "tag_aliases" not in res:
        #     for tag_blob in res:
        #         if tag_blob["post_count"] < tag_post_limit:
        #             break
        #         valid_aliases.append(tag_blob["antecedent_name"])

        if not valid_tags and not valid_aliases:
            await ctx.send(f"No tags with `{search_tag}` in them.")
            return
        msg = f"Tags with `{search_tag}`:\n" + ", ".join(valid_tags)
        # msg += f"\nTag aliased with `{search_tag}`:\n" + ", ".join(valid_aliases)
        msg = msg.replace("_", "\\_")
        await ctx.send(msg)

    @commands.command(name=f"{prefix}.search.help")
    async def search_for_tag_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Search for tags! This does not search for aliases of tags.
        Will return up to 20 tags, ordered by number of posts with this tag.
        
        Arguments:
            tag - The name of the tag to search
            limit - The tag must have at least this many posts. Default 100

        Examples:
            c.e.search owo
            c.e.search pidge 50```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.idea.help")
    async def drawing_idea_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```Returns a random drawing idea! Normally SFW!
            Can be provided with one of the following keywords to narrow the search:
            species; character; tag;
            
            Examples:
                c.e.idea
                c.e.idea species
                c.e.idea tag```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.sentence.help")
    async def furry_sentence_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```Construct a furry sentence!
            Type a number afterwards to determine how many words are used!
            
            Examples:
                c.e.sentence
                c.e.sentence 5```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.tag_count.help")
    async def num_with_tag_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```Check how many entries on an unspecified site this tag has!
    
            Examples:
                c.e.tag_count cervid
                c.e.tag_count :d```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.help")
    async def vc_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        desc = "Accesses the API of an unspecified website to get *you* the tags you need."
        await ctx.send(embed=self.bot.create_help(self.help_text, help_description=desc))

    def db_fill(self, category=4, post_limit=400):
        cur = self.bot.cursor
        user_agent = self.user_agent
        params = {"search[category]": f"{category}", "limit": "1000", "page": "1", "search[hide_empty]": "true",
                  "search[order]": "count"}
        tag_data = []

        # Find tags in this category.
        i = 0
        while True:
            i += 1
            params["page"] = str(i)
            res = requests.get('https://e621.net/tags.json', headers=user_agent, params=params).json()
            count_too_low = False
            if "tags" in res:  # No more tags to display.
                break

            for tag_blob in res:
                count = tag_blob["post_count"]
                id = tag_blob["id"]
                name = tag_blob["name"]
                cat = category

                if count < post_limit:
                    count_too_low = True
                    break

                tag_data.append([name, cat, id, count])

            if count_too_low:
                break

        # Index aliases of documented tags.
        alias_data = []
        params = {
            "limit": "1000", "page": 1, "search[status]": "approved", "search[antecedent_tag][category]": f"{category}",
            "search[order]": "tag_count"}
        i = 0
        while True:
            i += 1
            params["page"] = str(i)
            res = requests.get('https://e621.net/tag_aliases.json', headers=user_agent, params=params).json()
            count_too_low = False
            if "tag_aliases" in res:  # No more tags to display.
                break

            for tag_blob in res:
                count = tag_blob["post_count"]
                id = tag_blob["id"]
                name = tag_blob["antecedent_name"]
                cat = category

                if count < post_limit:
                    count_too_low = True
                    break

                alias_data.append([name, cat, id, count])

            if count_too_low:
                break

        # Clear existing DB entries of this category.
        cur.execute(f"DELETE FROM e6_tags WHERE category_id=?", [category])
        cur.execute("commit")

        # Add found tags and their aliases to the database.
        tag_data += alias_data
        cur.executemany("INSERT INTO e6_tags VALUES(?,?,?,?)", tag_data)
        cur.execute("commit")

    def db_init(self):
        cursor = self.bot.cursor
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS e6_tags ("  # An entry is created for each change that is detected.
            "name STRING,"  # name of the tag
            "category_id INTEGER,"  # Category. Check e621 api docs
            "tag_id,"  # Tag's id
            "post_count INTEGER"  # how many posts use this tag.
            # TODO: Add "alias" boolean? Compile aliases into their own field?
            ")")
        cursor.execute("commit")


def setup(bot):
    bot.add_cog(sinner(bot))