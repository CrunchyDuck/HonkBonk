import discord
import re
import requests
from discord.ext import commands
from sys import getsizeof


class Emoji(commands.Cog, name="emoji"):
    """Controls custom emoji in the server. Allows users to add, remove, or modify emoji without the permission to otherwise do so."""
    prefix = "emoji"
    re_emoji_id = re.compile(r"(?:<:.*?:)(\d*)(>)")  # A pattern that finds a custom emoji in a discord message
    r_cdn = re.compile(  # URL for Discord's Content Delivery Network.
        r"(https://cdn.discordapp.com/attachments/.*?\.(gif|png|jpg))|(https://cdn.discordapp.com/emojis/[^\s]*)")
    r_cdn_filename = re.compile(r"([^/]*?(\.png|\.jpg|\.gif))")

    def __init__(self, bot):
        self.bot = bot
        self.init_database(bot.cursor)

        self.bot.core_help_text["modules"] += [self.prefix]
        self.bot.core_help_text["too lazy to categorize"] +=\
            [f"{self.prefix}.{command}" for command in
             sorted(["push", "pop", "owner", "info"])] + ["\n"]

    @commands.command(name=f"{prefix}.push")
    async def emoji_push(self, ctx):
        """
        Adds a custom emoji to the server.
        Arguments:
            name: Name of the emoji.
            image: Can be provided as either a discord cdn image, or as an attached picture.
        Example:
            c.emoji.push name="artwork" https://cdn.discordapp.com/attachments/770741727153750027/802341424087433276/masterpeice.png
        """
        if not await self.bot.has_perm(ctx): return
        message = ctx.message

        emoji_name = self.bot.get_variable(message.content, "name", type="str")
        if not emoji_name:
            await ctx.send("""Please provide a name for the emoji, formatted as `name="name_of_emoji"`""")
            return
        emoji_name.replace(" ", "_")

        if message.attachments:
            img_attachment = message.attachments[0]
            file_ext = img_attachment.filename[-3:]

            img_types = ["jpg", "png", "gif"]
            # file checks
            if file_ext not in img_types:
                await ctx.send("File type is not a png, jpg or gif!")
                return
            if img_attachment.size > 262144:  # 256 kb
                await ctx.send("File is too big! Must be smaller than 256kb")
                return

            dat = None
            await img_attachment.save(f".\\attachments\\{img_attachment.filename}")
            with open(f".\\attachments\\{img_attachment.filename}", "rb") as f:
                dat = f.read()
        else:
            # No image, check for URL
            has_cdn_image = re.search(self.r_cdn, message.content)  # Checks if it has a valid CDN url
            if has_cdn_image:
                url = has_cdn_image.group(0)  # Gets the full url
                filename = re.search(self.r_cdn_filename, url).group(0)  # Gets the file name from the URL

                # Get the bytes data of the image.
                r = requests.get(url)
                dat = r.content  # Saves the bytes data into here to be sent to discord.
                if getsizeof(dat) > 262144:
                    await ctx.send("File is too big! Must be smaller than 256kb")
                    return
            else:
                # No url or image, error.
                await ctx.send("Please provide a URL to a valid image, or attach an image to your message!")
                return

        # TODO: Check if there's enough spots for the emoji.

        # Add emoji, update database
        custom_emoji = await ctx.guild.create_custom_emoji(name=emoji_name, image=dat)
        self.bot.cursor.execute("INSERT INTO custom_emoji VALUES(?, ?)", (message.author.id, custom_emoji.id))
        self.bot.db.commit()

        await ctx.send(f":O here you go:")
        await ctx.send(f"<:{custom_emoji.name}:{custom_emoji.id}>")

    @commands.command(name=f"{prefix}.pop")
    async def emoji_pop(self, ctx):
        """
        Remove an emoji. This can only be done if you are an admin, or originally pushed the emoji
        Arguments:
            emoji: The custom to remove.
        Example:
            c.emoji.pop :artwork:
        """
        admin = await self.bot.has_perm(ctx, admin=True)  # Is this user an admin?
        if not await self.bot.has_perm(ctx): return

        message = ctx.message
        u = message.author
        emoji = await self.get_emoji(ctx, api_call=False)  # The emoji to pop
        if not emoji:
            await ctx.send("Please provide an emoji!")
            return

        # Find emoji entry in database
        self.bot.cursor.execute(f"SELECT * FROM custom_emoji WHERE emoji_id={emoji.id}")
        db_search_result = self.bot.cursor.fetchone()

        # TODO: Make the bot search existing custom emoji to see if it does indeed exist.
        if not db_search_result:
            await ctx.send("Emoji not found in database! (Probably because CrunchyDuck didn't put it in.)")
            emoji_owner_id = 0
        else:
            emoji_owner_id = db_search_result[0]

        # Check if the person running this command is either an admin, or the original owner of the emoji.
        if u == emoji_owner_id or admin:
            await ctx.send("owo o-okay~")
            await emoji.delete()
            self.bot.cursor.execute(f"DELETE FROM custom_emoji WHERE id={u.id}")
            self.bot.db.commit()
            return
        else:
            await ctx.send("you don't have permission for this b-baka >//<")
            return

    @commands.command(name=f"{prefix}.owner")
    async def emoji_ownership(self, ctx):
        """
        Transfers ownership of an emoji to another person.
        Can only be done by admins or the owner.
        Arguments:
            emoji: The owner to transfer ownership from
            target: A mention of who to transfer the emoji to.
        Example:
            c.emoji.db.owner @Oken :artwork:
        """
        if not await self.bot.has_perm(ctx): return
        target_user = ctx.message.mentions[0]
        emoji = await self.get_emoji(ctx, api_call=False)  # The emoji to pop

        if not target_user:
            await ctx.send("Mention a user to transfer ownership to them!")
            return
        elif not emoji:
            await ctx.send("Use the emoji you wish to transfer ownership from!")
            return

        if self.owns_emoji(ctx.author.id, emoji.id) or ctx.author.id in self.bot.admins:
            old_owner = self.bot.cursor.execute(f"SELECT * FROM custom_emoji WHERE emoji_id={emoji.id}").fetchone()[0]
            self.bot.cursor.execute(f"UPDATE custom_emoji SET id={target_user.id} WHERE emoji_id={emoji.id}")
            self.bot.db.commit()

            embed = discord.Embed(
                title="Emoji Owner Transferred",
                colour=discord.Colour.dark_purple()
            )
            embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
            embed.set_thumbnail(url=str(emoji.url))
            zws = "\u200b"

            embed.add_field(name=":new: New owner:", value=f"<@{target_user.id}>", inline=True)
            embed.add_field(name=zws, value=zws, inline=True)
            embed.add_field(name=":japanese_goblin: Old owner:", value=f"<@{old_owner}>", inline=True)
            await ctx.send(embed=embed)
            return
        else:
            await ctx.send("You don't own this emoji >:(")
            return

    @commands.command(name=f"{prefix}.db.update")
    async def db_update(self, ctx):
        """Checks through the server's custom emoji to add any that don't seem to exist."""
        if not await self.bot.has_perm(ctx, admin=True): return
        added_emoji = []
        removed_emoji = []  # TODO: Make the bot cycle through the DB and attempt to find emoji it already has indexed to fill this.

        for emoji in ctx.guild.emojis:
            self.bot.cursor.execute(f"SELECT * FROM custom_emoji WHERE emoji_id={emoji.id}")
            if not self.bot.cursor.fetchone():
                emoji = await ctx.guild.fetch_emoji(
                    emoji.id)  # We need to fetch from the API to fill the Emoji object with the user that added it.
                self.bot.cursor.execute("INSERT INTO custom_emoji VALUES(?, ?)", (emoji.user.id, emoji.id))
                added_emoji.append((emoji.name, emoji.id))
        self.bot.db.commit()

        emoji_list = ""  # The text string containing all of the added emoji
        for e in added_emoji:
            emoji_list += f"<:{e[0]}:{e[1]}> "
        await ctx.send(f"Emoji added to database: {emoji_list}")

    @commands.command(name=f"{prefix}.info")
    async def emoji_info(self, ctx):
        """
        Provides info about a specific emoji, or general info otherwise.
        Information provided:
            (Emoji provided) Name, owner, emoji snowflake, date added.
            (No emoji) Static emoji slots, animated emoji slots
        Arguments:
            emoji: The emoji to get info from. Otherwise, provide info about open emoji slots.
        Example:
            c.emoji.info :artwork:
            c.emoji.info
        """
        if not await self.bot.has_perm(ctx): return

        emoji = await self.get_emoji(ctx, api_call=False)
        # User has provided an emoji that I can get info on.
        if emoji:
            emoji_time_made = emoji.created_at.strftime("%Y/%m/%d %H:%M:%S")

            owner = self.db_get_emoji("emoji_id", emoji.id)["user_id"]
            if not owner:
                await ctx.send(f"Emoji isn't in database :( <@{self.bot.crunchyduck}> fix pls")
                return

            embed = self.bot.default_embed(f"<:{emoji.name}:{emoji.id}> Emoji Info")
            embed.set_thumbnail(url=str(emoji.url))
            embed.add_field(name=":takeout_box: Name:", value=f"{emoji.name}", inline=True)
            embed.add_field(name=f"{self.bot.zws}", value=f"{self.bot.zws}", inline=True)
            embed.add_field(name=":lock: Owner:", value=f"<@{owner}>", inline=True)

            embed.add_field(name=":rainbow: Emoji ID:", value=f"{emoji.id}", inline=True)
            embed.add_field(name=f"{self.bot.zws}", value=f"{self.bot.zws}", inline=True)
            embed.add_field(name=":clock1: Added:", value=f"{emoji_time_made}", inline=True)

            await ctx.send(embed=embed)
        # No emoji provided, give general info.
        else:
            # TODO: Make a list of all emoji and their owners, similar in design to thinks like ayana
            guild = ctx.guild
            limit = guild.emoji_limit
            guild_emojis = guild.emojis
            static_emoji = [x for x in guild_emojis if x.animated == False]
            animated_emoji = [x for x in guild_emojis if x.animated == True]

            embed = self.bot.default_embed(f":information_source: General Emoji Info")
            embed.add_field(name="Static emoji slots:", value=limit - len(static_emoji), inline=True)
            embed.add_field(name="Animated emoji slots:", value=limit - len(animated_emoji), inline=True)

            await ctx.send(embed=embed)


    @commands.command(name=f"{prefix}.help")
    async def emoji_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```This module handles adding and removing emoji from the server
        
        c.emoji.push - Add an emoji.
        c.emoji.pop - Remove an emoji.
        c.emoji.owner - Transfer ownership of an emoji.
        c.emoji.info - Provides information about a given emoji in this server, or slots left.```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.push.help")
    async def emoji_push_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Adds a custom emoji to the server.
        
        Arguments:
            name: Name of the emoji.
            image: Can be provided as either a discord cdn image, or as an attached picture.
            
        Example:
            c.emoji.push name="artwork" https://cdn.discordapp.com/attachments/770741727153750027/802341424087433276/masterpeice.png```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.pop.help")
    async def emoji_pop_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Remove an emoji. This can only be done if you are an admin, or originally pushed the emoji
        
        Arguments:
            emoji: The custom to remove.
            
        Example:
            c.emoji.pop :artwork:```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.owner.help")
    async def emoji_owner_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Transfers ownership of an emoji to another person.
        Can only be done by admins or the owner.
        
        Arguments:
            emoji: The owner to transfer ownership from
            target: A mention of who to transfer the emoji to.
            
        Example:
            c.emoji.db.owner @Oken :artwork:```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.info.help")
    async def emoji_info_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        Provides info about a specific emoji, or general info otherwise.
        Information provided:
            (Emoji provided) Name, owner, emoji snowflake, date added.
            (No emoji) Static emoji slots, animated emoji slots
            
        Arguments:
            emoji: The emoji to get info from. Otherwise, provide info about open emoji slots.
            
        Example:
            c.emoji.info :artwork:
            c.emoji.info
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    async def get_emoji(self, ctx=None, string=None, api_call=True):
        """Finds the first emoji given in a message using RegEx:tm:"""
        # Check if the user actually put an emoji in their message.
        if ctx:
            string = ctx.message.content

        emoji_match = re.search(self.re_emoji_id, string)
        if not emoji_match:
            # await ctx.send("No emoji recognized! Shout at Crunchy?")
            return

        # Fetch the discord emoji object.
        emoji_id = int(emoji_match.group(1))
        if api_call:
            return await ctx.guild.fetch_emoji(emoji_id)
        else:
            for e in ctx.guild.emojis:
                if e.id == emoji_id:
                    return e

        # Found no emoji, therefore the ID was not recognized.
        await ctx.send(f"Could not find emoji with ID {emoji_id}")
        return None

    def owns_emoji(self, user_id, emoji_id):
        """Find who owns an emoji in the database."""
        self.bot.cursor.execute(f"SELECT * FROM custom_emoji WHERE emoji_id={emoji_id}")
        res = self.bot.cursor.fetchone()
        if res:
            return True if res[0] == user_id else False
        else:
            return False

    def db_get_emoji(self, column, value):
        """Fetches an emoji from the database.
        Arguments:
            column: A field to check
            value: What this field must equate to.
        Returns:
            Dictionary
        """
        self.bot.cursor.execute(f"SELECT * FROM custom_emoji WHERE {column}={value}")
        val = self.bot.cursor.fetchone()
        return {"user_id": val[0], "emoji_id": val[1]}

    def init_database(self, cursor):
        """Initiates the database required to store stuff about who made what emoji."""
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS custom_emoji ("  # An entry is created for each change that is detected.
            "id INTEGER,"  # ID of the user
            "emoji_id INTEGER"  # The ID of the emoji they added
            ")")
        cursor.execute("commit")


def setup(bot):
    bot.add_cog(Emoji(bot))
