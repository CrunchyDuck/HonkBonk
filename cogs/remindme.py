from discord.ext import commands
import re
from datetime import datetime



class remindme(commands.Cog, name="tatsu_is_bad"):
    r_segment_command = re.compile(r"\s(.*\s)?in (.*)")  # Group 1 is message, group 2 is time.

    def __init__(self, bot):
        self.bot = bot
        self.init_db(self.bot.cursor)
        self.bot.timed_commands.append(self.remind_time)

        self.bot.core_help_text["General"] += ["remind"]

    @commands.command(name="remind", aliases=["remindme", "r"])
    async def remind(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return

        message, time = self.segment_command(ctx.message.content)
        if not message:
            await ctx.send("Provide me with a time to annoy you.")
            return

        time = self.bot.time_from_string(time)  # Convert the time from the command into seconds.
        time = min(86400*30, time)  # Limit to 1 month.
        endtime = self.bot.time_from_now(seconds=time)
        to_remind = self.bot.admin_override(ctx)

        self.bot.cursor.execute("INSERT INTO remindme VALUES(?,?,?)", [message, to_remind.id, endtime])
        self.bot.cursor.execute("commit")

        how_long = self.bot.time_to_string(seconds=time)
        await ctx.send(f"**:alarm_clock:  |  Got it! I'll remind you in {how_long}**")

    @commands.command(name="reminders")
    async def my_reminders(self, ctx):
        if not await self.bot.has_perm(ctx, bot_owner=True, dm=True): return
        user = self.bot.admin_override(ctx).id
        message = ""

        at_time = True # self.bot.get_variable(ctx.message.content, "at", type="keyword", default=False)
        in_time = self.bot.get_variable(ctx.message.content, "in", type="keyword", default=False)

        c = self.bot.cursor
        c.execute("SELECT * FROM remindme WHERE user_id=?", [user])

        for entry in c.fetchall():
            if in_time:
                time = self.bot.time_to_string(seconds=entry[2] - self.bot.time_now())
                time = f" in {time}"
                message += f"{entry[0]} in {time}\n"
            elif at_time:
                time = datetime.fromtimestamp(entry[2]).strftime("%Y-%m-%d %H:%M:%S GMT")
                time = f"{time}"
                message += f"{time}: {entry[0]}\n"

        if not message:
            message = "No reminders!"
        await sleep(3)

        await ctx.send(self.bot.escape_message(message))


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

                self.bot.cursor.execute(f"DELETE FROM remindme WHERE rowid={target[0]}")
                self.bot.cursor.execute("commit")

    @commands.command(name="remind.help")
    async def remind_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Set a reminder for yourself! Stolen from tatsu due to his unreliability.
        Accepted time units:
            second, minute, hour, day, week (and some others~)
        
        Examples:
            c.remind owo in 0.5 minutes
            c.remind in 1 hour
            c.remindme you're cool somewhere in there in 1 day```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="reminders.help")
    async def reminders_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```View your reminders!
        Can be provided with the keyword "in" to change from absolute time to relative time.
        
        Examples:
            c.reminders
            c.reminders in```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    def segment_command(self, command):
        """
        Segments a command up into the reminder, and the timer.
        Returns [reminder, time] or [None, None] if not found.
        """
        match = re.search(self.r_segment_command, command)
        if not match:
            return [None, None]

        m = match.group(1)
        if not m:
            m = "Reminder!"
        return [m, match.group(2)]

    def init_db(self, cursor):
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS remindme ("
            "message STRING,"  # What to remind them of.
            "user_id INTEGER,"  # Who to remind
            "time INTEGER"  # When to remind them
            ")")
        cursor.execute("commit")


def setup(bot):
    bot.add_cog(remindme(bot))
