import discord
import re
from discord.ext import commands


class forward_dm(commands.Cog, name="forward_dm"):
    """Simply forwards any DMs into the console window."""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        msg = message.content
        auth = message.author
        att = message.attachments
        time = message.created_at

        if message.channel.type == discord.ChannelType.private:
            urls = ""
            for x in att:
                urls += f"\n{x.url}"

            m_date = time.strftime("%d/%m/%Y")  # Date as a string in my preferred format.
            m_time = time.strftime("%H:%M:%S")  # Time as a string in my preferred format.
            msg_format = f"{m_date} {m_time} {auth}: {msg}{urls}"

            print(msg_format)


def setup(bot):
    bot.add_cog(forward_dm(bot))
