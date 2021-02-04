import discord
import re
from discord.ext import commands
import time
import datetime
import asyncio

class TempChannel(commands.Cog, name="temp_channel"):
    """Allows people to set up a temporary channel for discussion. This room is archived after it is closed."""
    prefix = "room"
    
    def __init__(self, bot):
        self.bot = bot
        self.db_init()
        self.server = 704361803953733693
        self.create_category = 802174888344813608
        self.archive_category = 774303846478250054
        
        self.rc_room = self.bot.Chance({
            "hours": 100,
            "minutes": 70,
            "seconds": 50,
            "milliseconds": 30,
        })
        self.rc_destroy_type = self.bot.Chance({
            "annihilation": 50,
            "destruction": 50,
            "incineration": 50,
            "end": 50,
            "die": 50,
            "death": 50,
            "blend": 50,
            "spaghettification": 50,
            "liquidation": 50,
            "eradication": 50,
            "extermination": 50,
            "slaughter": 50,
            "devastation": 50,
            "erasure": 50,
            "demolition": 50,
            "petrification": 50,

            "extinction level event": 30,
            ":gogogo:": 30,

            "america invades": 20,
            "emancipation": 20,
            "freedom": 20,
            "liberation": 20,
            "sweet release": 20,
            "covid-19": 20,
            "": 20,
            "brexit": 20,
            "china takes over": 20,
            "Lyricity schism": 20,
            "Rome falls": 20,
            "dreams fade": 20,
            "obama": 20,
            ":exploding_head:": 20,
            "Dedede invades Equestria": 20,
            "https://youtu.be/mP3bcPvgIG8 ": 10,
            "<https://youtu.be/P8RHDid1th4>\nyeah im putting my mix in here what you gonna do about it xD ": 10,
        })

    @commands.command(name=f"{prefix}.open")
    async def room_open(self, ctx):
        """
        Creates a temporary room.
        Arguments:
            name: Name of the room.
            (Optional) nsfw: If the room should be flagged as nsfw. Default False
            (Optional) time: How long, in hours, the room should be open for. Default 24
            (Optional) topic: The channel's topic.
        Example:
            c.room.open name="big boys only" time=1.12 topic="politics" nsfw
            c.room.open name="how do i cook" time=12
            c.room.open name="what should i make with eggs"
        """
        if not await self.bot.has_perm(ctx): return

        message = ctx.message
        author = self.bot.admin_override(ctx)
        archive_cat = ctx.guild.get_channel(self.create_category)

        # Does user already have a channel open?
        open_rooms = self.user_rooms_open(owner.id)
        if len(open_rooms) > 0 and ctx.author.id not in self.bot.admins:
            await ctx.send(f"You already have a room open! Use c.{self.prefix}.close in the room to close it.")
            return
        
        name = self.bot.get_variable(message.content, "name", type="str")
        nsfw = self.bot.get_variable(message.content, "nsfw", type="keyword", default=False)
        duration = float(self.bot.get_variable(message.content, "time", type="float", default=24))  # Provided as hours.
        topic = self.bot.get_variable(message.content, "topic", type="str", default="")

        end_time = self.bot.hours_from_now(duration)
        
        # Input checks.
        if not name:
            await ctx.send("""Please provide a name in the format `name="name-of-room\"""")
            return

        #participants = message.mentions if message.mentions else None  # None allows all members.
        #for member in participants:
        #    pass

        try:
            cat_perms = archive_cat.overwrites
            overwrites = {**self.create_temp_room_overrides(owner), **cat_perms}  # Merge dictionaries.
            created_channel = await ctx.guild.create_text_channel(name=name, category=ctx.guild.get_channel(self.create_category),
                sync_permission=True, nsfw=nsfw, topic=topic, overwrites=overwrites)
        except:
            await ctx.send("Couldn't create room! Most likely, I've hit the room cap and CrunchyDuck didn't find a solution before this triggered.\ntell he.")
            return

        self.bot.cursor.execute("INSERT INTO temp_room VALUES(?, ?, ?)", (author.id, created_channel.id, end_time))
        self.bot.cursor.execute("commit")
        
        # Decide what response to give.
        response_message = ""
        response_type = self.rc_room.get_value()
        if response_type == "hours":
            response_message = f"Created {created_channel.mention} for {duration} hours."
        elif response_type == "minutes":
            response_message = f"Created {created_channel.mention} for {duration * 60} minutes."
        elif response_type == "seconds":
            response_message = f"Created {created_channel.mention} for {duration * 60 * 60} seconds."
        elif response_type == "milliseconds":
            response_message = f"Created {created_channel.mention} for {duration * 60 * 60 * 1000} milliseconds."
        else:
            response_message = "Crunchydunk broke chances. Room created."
        
        await ctx.send(response_message)
        await created_channel.send("first")

    # TODO: Find a way to deal with rooms getting deleted causing no more room ability.
    @commands.command(name=f"{prefix}.close")
    async def room_close(self, ctx):
        """
        Archives a room. Must be called within the room. Only the owner or an admin can close a room.
        Example:
            c.room.close
        """
        if not await self.bot.has_perm(ctx, ignored_rooms=True): return

        message = ctx.message
        author = message.author.id
        channel = ctx.channel

        # Check if this channel is a temp channel
        db_entry = self.bot.get_temp_room(room_id=channel.id)
        if not db_entry:
            await ctx.send("This channel doesn't seem to be a temporary channel.")
            return

        # Check if this person owns it, or is an admin.
        if author not in self.bot.admins and author != db_entry["user_id"]:
            await ctx.send("You don't own this temp channel. thot.")
            return

        await channel.edit(category=self.bot.get_channel(self.archive_category), sync_permissions=True, position=len(ctx.guild.channels))
        self.bot.cursor.execute("DELETE FROM temp_room WHERE room_id=?", (channel.id,))
        self.bot.cursor.execute("commit")

        await channel.send("Archiving channel...")

    @commands.command(name=f"{prefix}.time")
    async def time_left(self, ctx):
        """Changes how much time the room has left,
        OR returns how much longer until the channel is automatically archived.
        Must be called from within the channel.
        Changing time can only be done by an admin or the owner.
        Arguments:
            time: The new duration of the room.
        Example:
            c.room.time
            c.room.time 1.2
        """
        if not await self.bot.has_perm(ctx, ignored_rooms=True): return
        channel = ctx.channel
        user = ctx.author

        # Check if this channel is a temp channel
        db_entry = self.bot.get_temp_room(room_id=channel.id)
        if not db_entry:
            await ctx.send("This channel doesn't seem to be a temporary channel.")
            return

        hours = float(self.bot.get_variable(ctx.message.content, type="float", default=0))
        if hours:
            if db_entry["user_id"] == user.id or user.id in self.bot.admins:
                cur = self.bot.cursor
                end_time = self.bot.hours_from_now(hours)
                cur.execute(f"UPDATE temp_room SET end_time={end_time} WHERE room_id={channel.id}")
                cur.execute("commit")
                time_string = self.bot.time_to_string(hours=hours)
                await ctx.send(f"The room's lifespan has been changed to {time_string}!")
            else:
                await ctx.send("you are not **permitted.**")
        else:
            time_diff = db_entry["end_time"] - time.mktime(datetime.datetime.now().timetuple())
            time_string = self.bot.time_to_string(seconds=time_diff)
            destruction_type = self.rc_destroy_type.get_value()
            await ctx.send(f"This room has {time_string} until {destruction_type}.")

    @commands.command(name=f"{prefix}.order")
    async def order_archive(self, ctx):
        """
        Order the channels in the archive category for this server.
        Arguments:
            date: Order channels by date
            name: Order channels by name
            descending: Order Z-A or newest-oldest
        Example:
            c.room.order_archive date
            c.room.order_archive name descending
        """
        if not await self.bot.has_perm(ctx, admin=True): return
        message = ctx.message
        name = self.bot.get_variable(message.content, "name", type="keyword", default=False)
        date = self.bot.get_variable(message.content, "date", type="keyword", default=False)
        descending = self.bot.get_variable(message.content, "descending", type="keyword", default=False)

        archive_cat = ctx.guild.get_channel(self.archive_category)

        order = "descending" if descending else "ascending"
        async with ctx.typing():
            if name:
                await self.order_cat_alphabetically(archive_cat, descending)
                await ctx.send(f"Ordered {archive_cat.name} by name in {order} order!")
            elif date:
                await self.order_cat_created(archive_cat, descending)
                await ctx.send(f"Ordered {archive_cat.name} by date in {order} order!")
            else:
                return

    @commands.command(name=f"{prefix}.reopen")
    async def reopen_room(self, ctx):
        """
        ```Reopens a channel in the archive category. Admins may reopen any room.

        Arguments:
            (Optional)
            owner: A mention of the new owner of the channel. Whoever invoked the command if omitted.
            time: How long the channel should be open for. 24 hours if omitted.
            #channel: A mention of the channel to add. Current channel if omitted.

        Example:
            c.room.reopen
            c.room.reopen time=9.12
            c.room.reopen @Oken #images```
        """
        if not await self.bot.has_perm(ctx, ignored_rooms=True): return
        message = ctx.message

        owner = self.bot.admin_override(ctx)  # Allow an admin to define other users.
        channel = message.channel_mentions[0] if message.channel_mentions else ctx.channel
        duration = float(self.bot.get_variable(message.content, "time", type="float", default=24))  # Provided as hours.
        archive_cat = ctx.guild.get_channel(self.create_category)

        end_time = self.bot.hours_from_now(duration)

        # Is channel already temp?
        self.bot.cursor.execute("SELECT * FROM temp_room WHERE room_id=?", (channel.id,))
        if self.bot.cursor.fetchone():
            await ctx.send(f"This room is already a temp room.")
            return

        # Is channel under the archive category?
        if ctx.author not in self.bot.admins and channel.category.id != self.archive_category:
            await ctx.send("Channel must under the archived rooms category.")
            return

        # Does user already have a channel open?
        open_rooms = self.user_rooms_open(owner.id)
        if len(open_rooms) > 0 and ctx.author.id not in self.bot.admins:
            await ctx.send(f"{owner.name} already has a channel open!")
            return

        cat_perms = archive_cat.overwrites
        overwrites = {**self.create_temp_room_overrides(owner), **cat_perms}  # Merge dictionaries.
        await channel.edit(category=archive_cat, sync_permissions=True, overwrites=overwrites)
        self.bot.cursor.execute("INSERT INTO temp_room VALUES(?, ?, ?)", (owner.id, channel.id, end_time))
        self.bot.cursor.execute("commit")

        await ctx.send(f"{channel.mention} changed to temporary room owned by {owner.name}")
        await channel.send(f"Reopened channel under ownership of {owner.name}!")

    @commands.command(name=f"{prefix}.settings")
    async def configure_settings(self, ctx):
        if not await self.bot.has_perm(ctx, admin=True): return
        message = ctx.message
        server = ctx.guild.id

        settings = {}
        fields = [["create category", "int"], ["archive category", "int"], ["default time", "int"],
                  ["ignore channel", "int"], ["ignore category"]]
        for field in fields:
            key = field[0]
            type = field[1]
            val = self.bot.get_variable(message.content, key, type=type, default="0")
            if val != "0":
                settings[key] = val

        for key, value in settings:
            if value == "0":  # default value
                continue
            self.bot.cursor.execute("INSERT INTO settings VALUES(?, ?, ?)", (server, key, value))
        self.bot.cursor.execute("commit")

    @commands.command(name=f"{prefix}.owner")
    async def room_owner(self, ctx):
        """
        Displays the owner of the room.

        Arguments:
            (Optional)
            #room: A mention of the room, assumes current room if not provided.

        Example:
            c.room.owner
            c.room.owner #nyanyacatboys
        """
        if not await self.bot.has_perm(ctx): return
        channel = ctx.message.channel_mentions[0] if ctx.message.channel_mentions else ctx.channel
        result = self.bot.get_temp_room(room_id=channel.id)

        if not result:
            await ctx.send(f"{channel.mention} isn't owned by anyone.")
            return

        user = self.bot.get_user(result["user_id"])
        await ctx.send(f"{channel.mention} is owned by {user.name}")


    @commands.command(name=f"{prefix}.help")
    async def room_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```This module allows users to open rooms temporarily.
            A temporary room is one that will automatically archive or close after its time is up.
            A room is moved to the provided category when it is archived.
            These commands will work even if the temporary room is ignored.
            
            c.room.open - Opens a temporary room
            c.room.close - Closes a temporary room
            c.room.time - Change or check the time on a room.
            c.room.owner - Who owns a temp room?
            
            c.room.order - Orders the archive category.
            c.room.add - Makes a channel a temporary room.
            c.room.settings - nothing lol
            ```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.open.help")
    async def room_open_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Creates a temporary room.
        Room owners get the following permissions:
            Manage Messages, Send TTS Messages, Manage Channel
        Admins can mention a user to open a channel in their name.
        
        Arguments:
            (Required)
            name: Name of the room.
            
            (Optional)
            nsfw: If the room should be flagged as nsfw. Default False
            time: How long, in hours, the room should be open for. Default 24
            topic: The channel's topic.
        
        Example:
            c.room.open name="big boys only" time=1.12 topic="politics" nsfw
            c.room.open name="how do i cook" time=12
            c.room.open name="what should i make with eggs"```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.close.help")
    async def room_close_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Move the room to the archive category. Must be called within the room.
        Only the owner or an admin can close a room.
        
        Example:
            c.room.close```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.owner.help")
    async def room_owner_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Displays the owner of the room.

        Arguments:
            (Optional)
            #room: A mention of the room, assumes current room if not provided.

        Example:
            c.room.owner
            c.room.owner #nyanyacatboys```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.order.help")
    async def room_order_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Order the channels in the archive category for this server.
        
        Arguments:
            date: Order channels by date
            name: Order channels by name
            descending: Order Z-A or newest-oldest
        
        Example:
            c.room.order_archive date  # Order by oldens
            c.room.order_archive name descending  # Order from Z-A```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.time.help")
    async def room_time_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Changes how much time the room has left,
        OR returns how much longer until the channel is automatically archived.
        Must be called from within the channel.
        Changing time can only be done by an admin or the owner.
        
        Arguments:
            (Optional)
            time: The new duration of the room.
            
        Example:
            c.room.time  # Checks time remaining
            c.room.time 1.2  # Sets time remaining.```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.reopen.help")
    async def reopen_room_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Reopens a channel in the archive category. Admins may reopen any room.
        
        Arguments:
            (Optional)
            #channel: A mention of the channel to add. Current channel if omitted.
            time: How long the channel should be open for. 24 hours if omitted.
            @user: Admins can mention a user to invoke on their behalf.
            
        Example:
            c.room.reopen
            c.room.reopen time=9.12
            c.room.reopen @Oken #images```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.settings.help")
    async def room_settings_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```Does nothing right now XD LMAO ROFL PRANKED```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)


    def create_temp_room_overrides(self, member=None, role=None):
        """
        Gives the owner of a room pseudo-admin powers within their own room while it is open.
        This returns a dictionary of the powers they will have.
        """

        perms = {
            "manage_messages": True,
            "send_tts_messages": True,
            "manage_channels": True
        }
        overwrite = discord.PermissionOverwrite(**perms)
        return {member: overwrite}

    def user_rooms_open(self, user_id):
        cur = self.bot.cursor
        cur.execute(f"SELECT room_id FROM temp_room WHERE id={user_id}")
        results = cur.fetchall()
        # I love list comprehension
        ids = [x[0] for x in results]
        return [self.bot.get_channel(x) for x in ids]

    async def order_cat_alphabetically(self, category_channel, descending=False):
        """
        Sorts the channels in a category alphabetically.
        Arguments:
            category_channel: The category containing the channels to order.
            descending: False does A-Z.
        """
        sorted_list = sorted(category_channel.channels, key=lambda channel: channel.name, reverse=descending)
        for i in range(len(sorted_list)):
            channel = sorted_list[i]
            if channel.position == i:
                continue
            await channel.edit(position=i)

    async def order_cat_created(self, category_channel, descending=False):
        """
        Orders channels in a category based on when the channel was created.
        Arguments:
            category_channel: The category containing the channels to order.
            descending: False puts the first entry as the oldest room.
        """
        sorted_list = sorted(category_channel.channels, key=lambda channel: channel.created_at, reverse=descending)
        for i in range(len(sorted_list)):
            channel = sorted_list[i]
            if channel.position == i:
                continue
            await channel.edit(position=i)

    def db_init(self):
        cursor = self.bot.cursor
        
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS temp_room ("  # An entry is created for each change that is detected.
            "id INTEGER,"  # ID of the user
            "room_id INTEGER,"  # The room's ID.
            "end_time INTEGER"  # The unix epoch time that this room should be closed at.
            ")")
        cursor.execute("commit")


def setup(bot):
    bot.add_cog(TempChannel(bot))

