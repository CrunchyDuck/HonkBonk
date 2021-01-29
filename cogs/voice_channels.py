import discord
import re
from discord.ext import commands


# TODO: Allow HB to play music from youtube, like bots such as Rythm.
# IDEA: Global volume control option to manually boost/lower a song.
# IDEA: Automatic gain control, based on the peaks of a song.
# IDEA: Give HB a bunch of voice clips he's capable of remotely playing, so I can harass people at range.
class VoiceChannels(commands.Cog, name="voice_channels"):
    prefix = "vc"

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name=f"{prefix}.join")
    async def join_voice_channel(self, ctx):
        """Join the VC channel the user is currently in."""
        if not await self.bot.has_perm(ctx, admin=True): return
        voice = ctx.author.voice
        cnl_variable = self.bot.get_variable(ctx.message.content, "cnl", "int")

        if voice and voice.channel:
            channel = voice.channel
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True, self_mute=True)
            return
        elif cnl_variable:
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True, self_mute=True)
        else:
            await ctx.send("You're not in a voice channel, orokana baaaaaka")
            return

    @commands.command(name=f"{prefix}.leave")
    async def leave_voice_channel(self, ctx):
        """Leave the voice channel the bot is in, within this server."""
        if not await self.bot.has_perm(ctx, admin=True): return
        await ctx.guild.change_voice_state(channel=None, self_deaf=True, self_mute=True)
        return


    @commands.command(name=f"{prefix}.help")
    async def vc_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```c.vc.join - Join your channel
        c.vc.leave - Leave currently joined channel```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.join.help")
    async def join_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Join the VC channel you're in, or the mentioned channel
        
        Arguments:
            cnl: The vc channel ID to join
        
        Examples:
            c.vc.join
            c.vc.join cnl=773744358934446080```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name=f"{prefix}.leave.help")
    async def leave_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```Leave the currently joined vc.

            Example:
                c.vc.leave```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)


def setup(bot):
    bot.add_cog(VoiceChannels(bot))
