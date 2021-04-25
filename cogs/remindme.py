from discord.ext import commands
import re
from datetime import datetime


class remindme(commands.Cog, name="tatsu_is_bad"):
    r_interval = re.compile(r"(?:^)(.+?\d) yreve")  # Gets the interval, if it exists.
    r_in_time = re.compile(r"(?:yreve |^)(.+?\d) ni")

    def __init__(self, bot):
        self.bot = bot
        self.init_db(self.bot.cursor)
        self.bot.Scheduler.add(self.remind_time, 1)

    @commands.command(name="remind", aliases=["remindme", "r"])
    async def remind(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        reminder = self.segment_command(ctx.message.content)
        to_remind = self.bot.admin_override(ctx)

        # No timer reminder
        if not reminder["time"] and not reminder["interval"]:
            reply = "Will keep that safe for you :)"
            self.bot.db_do(self.bot.db, "INSERT INTO remindme VALUES(?,?,?,?,?)",
                           reminder["msg"], to_remind.id, 0, 0, 0)
        # Reminder with timer
        else:
            time = self.bot.time_from_string(reminder["time"])  # Convert the time from the command into seconds.
            time = min(86400 * 30, time)  # Limit to 1 month.
            endtime = self.bot.time_from_now(seconds=time)

            repeat_interval = self.bot.time_from_string(reminder["interval"])
            repeat_interval = min(86400 * 30, repeat_interval)  # 1 month limit.

            self.bot.db_do(self.bot.db, "INSERT INTO remindme VALUES(?,?,?,?,?)",
                           reminder["msg"], to_remind.id, endtime, repeat_interval, 1)

            how_long = self.bot.time_to_string(seconds=time)
            reply = f"**:alarm_clock:  |  Got it! I'll remind you in {how_long}**"
        await ctx.send(reply)

    @commands.command(name="reminders")
    async def my_reminders(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        user = self.bot.owner_override(ctx).id
        message = ""

        remove_id = int(self.bot.get_variable(ctx.message.content, "remove", type="int", default=0))

        # Return a list of reminders
        if not remove_id:
            entries = self.bot.db_get(self.bot.db, "SELECT rowid, * FROM remindme WHERE user_id=?", user)
            for entry in entries:
                message += f"\n{entry['rowid']}: {entry['message']}"
                if entry["timed"]:
                    time = self.bot.time_to_string(seconds=entry["time"] - self.bot.time_now())
                    message += f" ------ in {time}"
                    if entry["interval"]:
                        reminder_amount = self.bot.time_to_string(seconds=entry["interval"])
                        message += f" (every {reminder_amount})"
            if not message:
                message = "No reminders!"

            await ctx.send(self.bot.escape_message(message))
        # Remove reminder.
        else:
            # Check the user actually owns reminder.
            entry = self.bot.db_get(self.bot.db, f"SELECT user_id FROM remindme WHERE rowid=?", remove_id)
            if entry:
                if user != entry[0]["user_id"]:
                    await ctx.send("You don't own this reminder.")
                    return
            else:
                await ctx.send("No reminder with this id!")
                return

            self.bot.db_do(self.bot.db, f"DELETE FROM remindme WHERE rowid=?", remove_id)
            await ctx.send("Reminder deleted.")

    # Timed command
    async def remind_time(self, time_now):
        entries = self.bot.db_get(self.bot.db, "SELECT rowid, * FROM remindme WHERE timed=1 ORDER BY time ASC")
        for target in entries:
            if time_now > target["time"]:
                user = self.bot.get_user(target["user_id"])
                try:
                    await user.send(f"**:alarm_clock: Reminder:** {target['message']}")
                except AttributeError:
                    print(f"Could not message {target['user_id']}")
                    pass

                if not target["interval"]:  # Repeat reminders.
                    self.bot.db_do(self.bot.db, f"DELETE FROM remindme WHERE rowid=?", target["rowid"])
                else:
                    new_time = target["interval"] + self.bot.time_now()
                    self.bot.db_do(self.bot.db, f"UPDATE remindme SET time=? WHERE rowid=?", new_time, target["rowid"])
            else:
                break

    @commands.command(name="remind.help", aliases=["remindme.help", "r.help"])
    async def remind_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Set a reminder for yourself! Stolen from tatsu due to his unreliability.
        Accepted time units:
            second, minute, hour, day, week (and some others~)
            
        Arguments:
            in - How long until the first reminder
            every - How regularly to remind you of this. Should be placed after "in" if it exists.
        
        Examples:
            c.remind owo
            c.remindme you're cool somewhere in there in 1 day
            c.remind wake up time in 2 hours 10 minutes every 24.5 hours
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
        
        Examples:
            c.reminders
            c.reminders remove=21```
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
            "interval INTEGER,"  # For repeated reminders, how regularly to remind.
            "timed INTEGER"  # 0 if this reminder does not use times.
            ")")

        # Update from previous version.
        cursor.execute("PRAGMA table_info(remindme)")
        table_info = cursor.fetchall()
        column_exists = False
        for column in table_info:  # TODO: Standarize this type of column updating in MyBot
            if column[1] == "timed":
                column_exists = True
                break
        if not column_exists:
            cursor.execute("ALTER TABLE remindme ADD COLUMN timed INTEGER")

        cursor.execute("commit")


def setup(bot):
    for help in ["remind", "reminders"]:
        bot.core_help_text["General"] += [help]
    bot.add_cog(remindme(bot))


def teardown(bot):
    for help in ["remind", "reminders"]:
        bot.core_help_text["General"].remove(help)
    bot.remove_cog(remindme(bot))
