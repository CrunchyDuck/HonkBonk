import discord
from discord.ext import commands


class look_at_dm(commands.Cog, name="look_dm"):
    def __init__(self, bot):
        self.bot = bot
        #self.init_db(self.bot.cursor)
        #self.bot.timed_commands.append(self.water_plant_time)

        #self.bot.core_help_text["Admins OwOnly"] += ["pidge"]

    @commands.command(name="look.dm")
    async def get_dm(self, ctx):
        if not await self.bot.has_perm(ctx, bot_owner=True): return
        target_user_id = int(self.bot.get_variable(ctx.message.content, "id", type="int"))  # Provided as unix epoch
        if not target_user_id:
            return

        target_user = self.bot.get_user(target_user_id)
        dm_channel = target_user.dm_channel
        if not dm_channel:
            dm_channel = await target_user.create_dm()

        print(dm_channel)
        print(type(dm_channel))
        async for message in dm_channel.history(limit=None, oldest_first=True):
            msg = message.content
            auth = message.author
            att = message.attachments
            time = message.created_at

            urls = ""
            for x in att:
                urls += f"\n{x.url}"

            m_date = time.strftime("%d/%m/%Y")  # Date as a string in my preferred format.
            m_time = time.strftime("%H:%M:%S")  # Time as a string in my preferred format.
            msg_format = f"{m_date} {m_time} {auth}: {msg}{urls}"

            print(msg_format)

def setup(bot):
    bot.add_cog(look_at_dm(bot))
