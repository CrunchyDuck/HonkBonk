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
        reminder = self.get_reminder_time(ctx.message.content)
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

        remove = int(self.bot.get_variable(ctx.message.content, "remove", type="keyword", default=0))

        # Return a list of reminders
        if not remove:
            hb_response = ""
            entries = self.bot.db_get(self.bot.db, "SELECT rowid, * FROM remindme WHERE user_id=?", user)
            for entry in entries:
                hb_response += f"\n{entry['rowid']}: {entry['message']}"
                if entry["timed"]:
                    time = self.bot.time_to_string(seconds=entry["time"] - self.bot.time_now())
                    hb_response += f" ------ in {time}"
                    if entry["interval"]:
                        reminder_amount = self.bot.time_to_string(seconds=entry["interval"])
                        hb_response += f" (every {reminder_amount})"
            if not hb_response:
                hb_response = "No reminders!"

            await ctx.send(self.bot.escape_message(hb_response))
        # Remove reminder.
        else:
            unowned_ids = []
            unrecognized_ids = []
            deleted_ids = []

            # Run through each ID and try to delete it.
            for remove_id in re.finditer("\d+", ctx.message.content):
                remove_id = remove_id.group(0)
                # Check the user actually owns reminder.
                entry = self.bot.db_get(self.bot.db, f"SELECT user_id FROM remindme WHERE rowid=?", remove_id)
                if entry:
                    if user != entry[0]["user_id"]:
                        unowned_ids.append(remove_id)
                        continue
                else:
                    unrecognized_ids.append(remove_id)
                    continue

                self.bot.db_do(self.bot.db, f"DELETE FROM remindme WHERE rowid=?", remove_id)
                deleted_ids.append(remove_id)

            # Formulate response
            hb_response = "Deleted reminders: " + " ".join(deleted_ids)  # Will always be sent even if nothing was deleted.
            if unowned_ids:
                hb_response += "\nReminders you didn't own (bad person): " + " ".join(unowned_ids)
            if unrecognized_ids:
                hb_response += "\nIds that weren't found: " + " ".join(unrecognized_ids)

            await ctx.send(hb_response)

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
            every - How regularly to remind you of this.
        
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
            remove - Delete reminders from you list. Provide the IDs of the reminders you wish to delete!
        
        Examples:
            c.reminders
            c.reminders remove 1 52 7```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    def get_reminder_time(self, message):
        """
        Gets the message, time to remind, and regularity to remind from a remindme command.
        Returns: Dict["msg": "", "interval": "", "time": ""]
        """
        # Remove the invoking of the command.
        command = command.replace("c.remind ", "")
        command = command.replace("c.remindme ", "")
        command = command[::-1]  # Reverse the string to match backwards.

        # Time
        in_time_start = None
        for in_time_start in re.finditer(" in ", message):
            pass
        if in_time_start:
            pos = in_time_start.start()
            message_from_match = message[pos:]

            # Get the "in amount of time" part of the message and nothing else.
            in_time = re.match("( in \d.+?)(?: every |$)", message_from_match)
            # If there is a valid match, remove it from the original message and store it in the dictionary.
            if in_time:
                match["time"] = in_time.group(1)
                message = message.replace(match["time"], "", 1)

        # Interval
        every_time_start = None
        for every_time_start in re.finditer(" every ", message):
            pass
        if every_time_start:
            pos = every_time_start.start()
            message_from_match = message[pos:]

            # Get the "every amount of time" part of the message and nothing else.
            every_time = re.match("( every \d.+?)(?:$)", message_from_match)
            # If there is a valid match, remove it from the original message and store it in the dictionary.
            if every_time:
                match["interval"] = every_time.group(1)
                message = message.replace(match["interval"], "", 1)

        match["msg"] = message  # Put what is left of the message into the dictionary.
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
