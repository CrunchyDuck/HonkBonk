import discord
import re
from discord.ext import commands
import time
import datetime
import asyncio


# TODO: Make an archive room, which honkbonk submits all of the messages from a room into in order to preserve them.
# This should be done in batch

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
        author = message.author.id
        self.bot.cursor.execute("SELECT * FROM temp_room WHERE id=?", (author,))
        if self.bot.cursor.fetchone():  # If someone has a room open, don't allow them to make a new one.
            await ctx.send(f"You already have a room open! Use c.{self.prefix}.close to close it.")
            return
        
        name = self.bot.get_variable(message.content, "name", type="str")
        nsfw = self.bot.get_variable(message.content, "nsfw", type="keyword", default=False)
        duration = float(self.bot.get_variable(message.content, "time", type="float", default=24))  # Provided as hours.
        topic = self.bot.get_variable(message.content, "topic", type="str", default="")

        end_time = self.hours_from_now(duration)
        
        # Input checks.
        if not name:
            await ctx.send("""Please provide a name in the format `name="name-of-room\"""")
            return

        #participants = message.mentions if message.mentions else None  # None allows all members.
        #for member in participants:
        #    pass

        try:
            created_channel = await ctx.guild.create_text_channel(name=name, category=ctx.guild.get_channel(self.create_category),
                sync_permission=True, nsfw=nsfw, topic=topic)
        except:
            await ctx.send("Couldn't create room! Most likely, I've hit the room cap and CrunchyDuck didn't find a solution before this triggered.\ntell he.")
            return

        self.bot.cursor.execute("INSERT INTO temp_room VALUES(?, ?, ?)", (author, created_channel.id, end_time))
        self.bot.cursor.execute("commit")
        
        # Decide what response to give.
        response_message = ""
        response_type = self.rc_room.get_value()
        if response_type == "hours":
            response_message = f"Created {created_channel.name} for {duration} hours."
        elif response_type == "minutes":
            response_message = f"Created {created_channel.name} for {duration * 60} minutes."
        elif response_type == "seconds":
            response_message = f"Created {created_channel.name} for {duration * 60 * 60} seconds."
        elif response_type == "milliseconds":
            response_message = f"Created {created_channel.name} for {duration * 60 * 60 * 1000} milliseconds."
        else:
            response_message = "Crunchydunk broke chances. Room created."
        
        await ctx.send(response_message)

    @commands.command(name=f"{prefix}.close")
    async def room_close(self, ctx):
        """
        Archives a room. Must be called within the room. Only the owner or an admin can close a room.
        Example:
            c.room.close
        """
        if not await self.bot.has_perm(ctx): return

        message = ctx.message
        author = message.author.id
        channel = ctx.channel

        # Check if this channel is a temp channel
        db_entry = self.db_temp_room(channel.id)
        if not db_entry:
            await ctx.send("This channel doesn't seem to be a temporary channel.")
            return

        # Check if this person owns it, or is an admin.
        if author not in self.bot.admins and author != db_entry[0]:
            await ctx.send("You don't own this temp channel. thot.")
            return

        await channel.edit(category=self.bot.get_channel(self.archive_category), sync_permissions=True, position=len(ctx.guild.channels))
        self.bot.cursor.execute("DELETE FROM temp_room WHERE room_id=?", (channel.id,))
        self.bot.cursor.execute("commit")

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
        if not await self.bot.has_perm(ctx): return
        channel = ctx.channel
        user = ctx.author

        # Check if this channel is a temp channel
        db_entry = self.db_temp_room(channel.id)
        if not db_entry:
            await ctx.send("This channel doesn't seem to be a temporary channel.")
            return

        hours = int(self.bot.get_variable(ctx.message.content, type="int", default=0))
        if hours:
            if (db_entry[0] == user.id or user.id in self.bot.admins):
                cur = self.bot.cursor
                end_time = self.hours_from_now(hours)
                cur.execute(f"UPDATE temp_room SET end_time={end_time} WHERE room_id={channel.id}")
                cur.execute("commit")
                await ctx.send(f"The room's lifespan has been changed to {hours} hours!")
            else:
                await ctx.send("you are not **permitted.**")
        else:
            time_diff = db_entry[2] - time.mktime(datetime.datetime.now().timetuple())
            time_diff = round(time_diff / 60 / 60, 3)  # Convert it from seconds to hours.
            destruction_type = self.rc_destroy_type.get_value()
            await ctx.send(f"This room has {time_diff} hours until {destruction_type}.")

    @staticmethod
    def hours_from_now(hours):
        """Calculates the Unix Epoch Time in the given amount of hours. UTC time."""
        duration_seconds = hours * 60 * 60  # Convert the duration to seconds.
        return time.mktime(datetime.datetime.now().timetuple()) + duration_seconds

    def db_temp_room(self, channel_id):
        """Find an entry in the temp_room database from the room_id."""
        # TODO: Reformat the return as a dictionary to make use clearer.
        self.bot.cursor.execute("SELECT * FROM temp_room WHERE room_id=?", (channel_id,))
        db_entry = self.bot.cursor.fetchone()
        return db_entry

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
    
