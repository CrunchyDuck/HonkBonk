from discord.ext import commands
import re
from datetime import datetime


class remindme(commands.Cog, name="tatsu_is_bad"):
    r_interval = re.compile(r"(?:^)(.+?) yreve")  # Gets the interval, if it exists.
    r_in_time = re.compile(r"(?:yreve |^)(.+?) ni")

    def __init__(self, bot):
        self.bot = bot
        self.init_db(self.bot.cursor)
        self.bot.timed_commands.append(self.remind_time)

        self.bot.core_help_text["General"] += ["remind", "reminders"]

    @commands.command(name="remind", aliases=["remindme", "r"])
    async def remind(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return

        reminder = self.segment_command(ctx.message.content)
        if not reminder["time"] and not reminder["interval"]:
            await ctx.send("Provide me with a time to annoy you.")
            return

        time = self.bot.time_from_string(reminder["time"])  # Convert the time from the command into seconds.
        time = min(86400 * 30, time)  # Limit to 1 month.
        endtime = self.bot.time_from_now(seconds=time)
        to_remind = self.bot.admin_override(ctx)

        repeat_interval = self.bot.time_from_string(reminder["interval"])
        if repeat_interval and repeat_interval < 300:  # Repeat must be at least 5 minutes if not 0.
            repeat_interval = 300

        self.bot.cursor.execute("INSERT INTO remindme VALUES(?,?,?,?)", [reminder["msg"], to_remind.id, endtime, repeat_interval])
        self.bot.cursor.execute("commit")

        how_long = self.bot.time_to_string(seconds=time)
        await ctx.send(f"**:alarm_clock:  |  Got it! I'll remind you in {how_long}**")

    @commands.command(name="reminders")
    async def my_reminders(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        user = self.bot.admin_override(ctx).id
        message = ""

        at_time = self.bot.get_variable(ctx.message.content, "at", type="keyword", default=False)
        remove_id = int(self.bot.get_variable(ctx.message.content, "remove", type="int", default=0))

        # Return a list of reminders
        if not remove_id:
            c = self.bot.cursor
            c.execute("SELECT rowid, * FROM remindme WHERE user_id=?", [user])

            for entry in c.fetchall():
                if at_time:
                    time = datetime.fromtimestamp(entry[3]).strftime("%Y-%m-%d %H:%M:%S GMT")
                    time = f"{time}"
                    message += f"{entry[0]}: {time}: {entry[1]}\n"
                else:
                    time = self.bot.time_to_string(seconds=entry[3] - self.bot.time_now())
                    time = f" ------ in {time}"
                    if entry[4]:
                        reminder_amount = self.bot.time_to_string(seconds=entry[4])
                        time += f" (every {reminder_amount})"

                    message += f"{entry[0]}: {entry[1]}{time}\n"

            if not message:
                message = "No reminders!"

            await ctx.send(self.bot.escape_message(message))
        # Remove reminder.
        else:
            # Check the user actually owns reminder emote.
            self.bot.cursor.execute(f"SELECT user_id FROM remindme WHERE rowid={remove_id}")
            result = self.bot.cursor.fetchone()
            if result:
                if user != result[0]:
                    await ctx.send("You don't own this reminder.")
                    return
            else:
                await ctx.send("No reminder with this id!")
                return

            self.bot.cursor.execute(f"DELETE FROM remindme WHERE rowid={remove_id}")
            self.bot.cursor.execute("commit")
            await ctx.send("Reminder deleted.")


    # Timed command
    async def remind_time(self, time_now):
        self.bot.cursor.execute("SELECT rowid, * FROM remindme ORDER BY time ASC")
        target = self.bot.cursor.fetchone()
        if target:  # TODO: Switch this to a while loop, so that multiple can be run every tick?
            if time_now > target[3]:
                user = self.bot.get_user(target[2])
                try:
                    await user.send(f"**:alarm_clock: Reminder:** {target[1]}")
                except AttributeError:
                    print(f"Could not message {target[1]}")
                    pass

                if not target[4]:  # Repeat reminders.
                    self.bot.cursor.execute(f"DELETE FROM remindme WHERE rowid={target[0]}")
                else:
                    new_time = target[4] + self.bot.time_now()
                    self.bot.cursor.execute(f"UPDATE remindme SET time={new_time} WHERE rowid={target[0]}")

                self.bot.cursor.execute("commit")

    @commands.command(name="remind.help", aliases=["remindme.help"])
    async def remind_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Set a reminder for yourself! Stolen from tatsu due to his unreliability.
        Accepted time units:
            second, minute, hour, day, week (and some others~)
            
        Arguments:
            in - How long until the first reminder
            every - How regularly to remind you of this. Omit for only once. Has to be after "in" argument.
        
        Examples:
            c.remind owo in 0.5 minutes
            c.remindme you're cool somewhere in there in 1 day
            c.remind wake up time in 2 hours 10 minutes every 24 hours
            c.remindme dummy thicc every 10 hours```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="reminders.help")
    async def reminders_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Manage your reminders!
        
        Arguments:
            remove - Delete the reminder with the provided ID. ID is the leftmost value in the reminders table.
            in - Change display format for reminders.
        
        Examples:
            c.reminders
            c.reminders remove=21
            c.reminders in```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    def segment_command(self, command):
        """
        Segments a command up into the reminder, and the timer.
        Returns [reminder, time] or [None, None] if not found.
        """
        # Remove the invoking of the command.
        command = command.replace("c.remind ", "")
        command = command.replace("c.remindme ", "")
        command = command[::-1]  # Reverse the string to match backwards.

        # TODO: Clean this code, jeez.
        match = {}
        # Get the last matches.
        match["interval"] = re.search(self.r_interval, command)
        if match["interval"]:
            start = match["interval"].start(1)
            end = match["interval"].end(1)
            match["interval"] = match["interval"].group(1)[::-1]
            command = command[:start] + command[end + 6:]  # Remove this from the command.
        else:
            match["interval"] = ""

        match["time"] = re.search(self.r_in_time, command)
        if match["time"]:
            start = match["time"].start(1)
            end = match["time"].end(1)
            match["time"] = match["time"].group(1)[::-1]  # Reverse the match to return it to normal
            command = command[:start] + command[end + 3:]  # remove this from the command.
        else:
            match["time"] = ""

        match["msg"] = command.strip()[::-1]  # Message is whatever remains of the command after all invoking info has been stripped.

        # Default reminder message.
        if not match["msg"]:
            match["msg"] = "Reminder!"

        return match

    def init_db(self, cursor):
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS remindme ("
            "message STRING,"  # What to remind them of.
            "user_id INTEGER,"  # Who to remind
            "time INTEGER,"  # When to remind them
            "interval INTEGER"  # For repeated reminders, how regularly to remind.
            ")")
        cursor.execute("commit")


def setup(bot):
    bot.add_cog(remindme(bot))
