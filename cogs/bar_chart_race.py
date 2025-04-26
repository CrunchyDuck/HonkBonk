import discord
from discord.ext import commands
import datetime  # Used for timestamps
from collections import Counter  # Used to count the users.


class BarChartRace(commands.Cog):
    """Admin commands. Mostly just fun things for me to toy with, sometimes test, rarely useful."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=f"bar_fetch")
    async def bar_fetch(self, ctx):
        your_id_here = 411365470109958155  # Only the person with this account ID can run the function.
        if ctx.message.author.id != your_id_here:
            return

        print("started")

        # ==== Customization variables ==== #
        top_users = 10  # How many users will be displayed in the animation.
        capture_interval = 24*60*60  # How regularly, in seconds, to capture the state of the counter.
        output_path = "top_members.csv"  # Where to save the data to.
        date_format = "%Y-%m-%d"  # Currently set to year-month-day. See datetime.strftime for formatting options.

        keyed_frames = []  # Stores the counter and date at each keyed frame.
        tracked_users = set()  # A non-repeating list of users who broke into the top_users
        message_count = 0  # Total messages done. Used to give updates on progress.
        c = Counter()  # This counts how many messages each user has sent so far.

        # Get the first message to use as a starting point for the animation.
        first_message = await ctx.channel.history(limit=1, oldest_first=True).flatten()
        first_message = first_message[0]
        c[first_message.author.name] += 1  # Add this message to the counter.
        start_snowflake = first_message.id
        start_time = datetime.datetime.now()
        # ==== Tally messages ====
        while True:  # For me, this takes around 7 seconds each loop to search 1000 messages
            end_snowflake = add_to_snowflake(start_snowflake, capture_interval)  # One day later...

            # Count each message for each person on this day...
            async for message in ctx.channel.history(limit=None, after=discord.Object(start_snowflake), before=discord.Object(end_snowflake), oldest_first=True):
                c[message.author.name] += 1
                message_count += 1

            # Record which users are in the top_users
            current_tops = c.most_common(top_users)
            for user in current_tops:
                tracked_users.add(user[0])

            # Record the counter and date
            current_date = discord.utils.snowflake_time(start_snowflake).strftime(date_format)
            keyed_frames.append((current_date, c.copy()))

            # Loop handling
            start_snowflake = end_snowflake
            print(f"Recorded {message_count} messages in {len(keyed_frames)} days")
            if len(keyed_frames) == 0:
                break
            # We've caught up to the current day!
            if discord.utils.snowflake_time(end_snowflake) >= start_time:
                break

        # ==== Create the .csv file ====
        tracked_users = sorted(list(tracked_users))
        with open(output_path, "w", encoding="utf-8") as f:
            name_list = ",".join(tracked_users)
            f.write(f"date,{name_list}\n")
            for keyed_frame in keyed_frames:
                counter = keyed_frame[1]
                user_data = []
                for user in tracked_users:
                    if user in counter:
                        user_data.append(counter[user])
                    else:
                        user_data.append(0)
                user_data_text = ",".join(str(x) for x in user_data)
                f.write(f"{keyed_frame[0]},{user_data_text}\n")

        print("done")


def add_to_snowflake(snowflake, seconds):
    return snowflake + (seconds * 1000 << 22)


def setup(bot):
    bot.add_cog(BarChartRace(bot))
