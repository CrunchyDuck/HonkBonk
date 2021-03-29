import discord
from discord.ext import commands


class herbert_live(commands.Cog, name="harass_pidge"):
    def __init__(self, bot):
        self.bot = bot
        self.init_db(self.bot.cursor)
        self.bot.timed_commands.append(self.water_plant_time)

        self.bot.core_help_text["Admins OwOnly"] += ["pidge"]

    @commands.command(name="pidge")
    async def harass_pidge(self, ctx):
        if not await self.bot.has_perm(ctx, admin=True, dm=True): return
        time = float(self.bot.get_variable(ctx.message.content, "time", type="float"))  # Provided as unix epoch

        # Overwrite existing entries.
        self.bot.cursor.execute("DELETE FROM harass_pidge")
        self.bot.cursor.execute("commit")

        self.bot.cursor.execute("INSERT INTO harass_pidge VALUES(?, ?)", [0, time])
        self.bot.cursor.execute("commit")

    @commands.command(name="pidge_from_now")
    async def when_next_trigger(self, ctx):
        one_day_seconds = 86400
        now = self.bot.time_now()
        time_through_day = now % one_day_seconds
        start_of_day = now - time_through_day
        message_time = start_of_day + (15 * 60 * 60) + (72 * 60 * 60)  # 8AM + 3 days
        await ctx.send(message_time)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        cur = self.bot.cursor
        try:
            cur.execute("SELECT * FROM harass_pidge")
            r = cur.fetchone()
            m_id = r[0]
            time = r[1]
        except:
            return

        if payload.message_id != m_id:
            return
        if payload.user_id == self.bot.user.id:
            return

        if str(payload.emoji) == "❌":
            self.bot.cursor.execute("DELETE FROM harass_pidge")
            self.bot.cursor.execute("commit")
            self.bot.cursor.execute("INSERT INTO harass_pidge VALUES(?,?)", [payload.message_id, self.bot.time_from_now(hours=4)])
            self.bot.cursor.execute("commit")

            delay = self.bot.Chance({
                "soon.": 1,
                "i will be watching.": 1,
                "hmmmmm": 1,
                "busy boy": 1,
                "duck will fly over": 1,
            })
            await self.bot.get_user(565879875647438851).send(delay.get_value())
            return

        elif str(payload.emoji) == "✅":
            self.bot.cursor.execute("DELETE FROM harass_pidge")
            self.bot.cursor.execute("commit")

            one_day_seconds = 86400
            now = self.bot.time_now()
            time_through_day = now % one_day_seconds
            start_of_day = now - time_through_day
            message_time = start_of_day + (8 * 60 * 60) + (72 * 60 * 60)  # 8AM + 3 days

            self.bot.cursor.execute("INSERT INTO harass_pidge VALUES(?,?)", [0, message_time])
            self.bot.cursor.execute("commit")

            praise = self.bot.Chance({
                "good boy~": 1,
                "*pats*": 1,
                "herbert is thankful": 1,
                "<3": 1,
                "best boy": 1,
            })
            await self.bot.get_user(565879875647438851).send(praise.get_value())
            return

    # Timed command
    async def water_plant_time(self, time_now):
        self.bot.cursor.execute("SELECT rowid, * FROM harass_pidge")
        target = self.bot.cursor.fetchone()
        if target:
            if time_now > target[2]:
                user = self.bot.get_guild(704361803953733693).get_member(565879875647438851)  # pidge member in my server

                opening = self.bot.Chance({
                    "water your plant.\ndone?": 1,
                    "is herbert wet?": 1,
                    "wetten herbert.": 1,
                    "plant thirsty": 1,
                    "feed your plant~": 1,
                })
                remind = self.bot.Chance({
                    "hello again. feed herbert.": 1,
                    "procrastinator.": 1,
                    "busy, i hope.": 1,
                    "i'll tell duck.": 1,
                    "knock knock. feed plant.": 1,
                    "<https://www.youtube.com/watch?v=DzfxSQRuheY>": 1,
                    "Hi there, this is the Plant Protective Authorities, checking in on your Herbert.": 1,
                    "We've received reports that there's a dry plant in this area.": 1,
                    "feed plant :)": 1,
                    "moisturize": 1,
                })

                if target[1] == 0:
                    message_content = opening.get_value()
                else:
                    message_content = remind.get_value()

                if user.status != discord.Status.offline:  # Don't want to bother him if he's at school/sleeping.
                    message = await user.send(message_content)
                    await message.add_reaction("✅")
                    await message.add_reaction("❌")

                    self.bot.cursor.execute("DELETE FROM harass_pidge")
                    self.bot.cursor.execute("commit")
                    self.bot.cursor.execute("INSERT INTO harass_pidge VALUES(?,?)", [message.id, self.bot.time_from_now(hours=2)])
                    self.bot.cursor.execute("commit")

    def init_db(self, cursor):
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS harass_pidge ("  # An entry is created for each change that is detected.
            "message_id INTEGER,"  # ID of the message to respond to reactions to.
            "next_time INTEGER"  # The unix epoch time that this room should be closed at.
            ")")
        cursor.execute("commit")


def setup(bot):
    bot.add_cog(herbert_live(bot))
