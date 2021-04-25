import requests
import xml.etree.ElementTree as ET
from discord.ext import commands
from os import getenv


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rss_code = getenv("BBC_RSS", None)
        # Most likely, people don't want to run this. If no rss is found, don't.
        if not self.rss_code:
            return
        self.website = f"https://weather-broker-cdn.api.bbci.co.uk/en/forecast/rss/3day/{rss_code}"
        self.bot.timed_commands.append([self.tell_weather, self.calculate_next_trigger])
        self.db_init()

    # Timed command
    async def tell_weather(self, time_now, manual=False):
        if self.rss_code is None:
            return
        next_time = self.calculate_next_trigger(time_now)
        if time_now < next_time and not manual:
            return

        me = await self.bot.fetch_user(self.bot.owner_id)
        xml_doc = requests.get(self.website).content.decode("utf-8")
        root = ET.fromstring(xml_doc)
        item = root[0][11]
        msg = f"{item[0].text}\n{item[2].text}"
        await me.send(msg)

        self.bot.db_do(self.bot.db, "DELETE FROM weather_triggered")
        self.bot.db_do(self.bot.db, "INSERT INTO weather_triggered VALUES(?)", time_now)

    @commands.command("w.now")
    async def current_weather(self, ctx):
        if not await self.bot.has_perm(ctx, bot_owner=True, dm=True): return
        await self.tell_weather(self.bot.time_now(), manual=True)

    def calculate_next_trigger(self, time_now):
        """
        Calculates the next time the notification should be sent.
        Returns: (int) Unix timestamp in seconds.
        """
        last_triggered = self.bot.db_get(self.bot.db, "SELECT * FROM weather_triggered")
        if last_triggered:
            next_time = last_triggered[0]["time"] + (60 * 60 * 8)
        else:  # This should only happen during initialization of the database.
            next_time = time_now
        return next_time

    def db_init(self):
        # Not the most efficient method to store this data, but it follows the current standard I've set in place.
        self.bot.db_do(self.bot.db, "CREATE TABLE IF NOT EXISTS weather_triggered(time INTEGER)")


def setup(bot):
    bot.add_cog(Weather(bot))


def teardown(bot):
    bot.remove_cog(Weather(bot))