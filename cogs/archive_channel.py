import discord
from discord.ext import commands
import re
import helpers


class ArchiveBotCog(commands.Cog, name="voice_channels"):
    def __init__(self, bot):
        self.bot = bot
        self.bot.event(self.on_command_error)
        self.bot.event(self.on_ready)

    async def on_command_error(self, ctx, error):
        """Triggered when a prefix is found, but no command is."""
        if isinstance(error, commands.CommandNotFound):  # Unrecognized command
            return
        else:
            raise error

    async def on_ready(self):
        print(f"{self.bot.user} has connected to Discord >:)")

    @commands.command(aliases=[f"archive"])
    async def archive_command(self, ctx):
        """Archive a channel
        LIMITATIONS:
          message edited date is not preserved
          embeds not preserved
          threads not preserved
          cdns are only saved as links - if the channel is deleted, these links will stop working.
          message reactions
        """
        if not await self.bot.has_perm(ctx, owner_only=True, dm=False): return
        message = helpers.remove_invoke(ctx.message.content)
        channel = ctx.channel

        category = re.search(r"cat=(\d+)", message)
        target = re.search(r"target=(\d+)", message)
        output = re.search(r"output=(\d+)", message)

        output = await self.bot.fetch_channel(output.group(1)) if output else channel

        if category:
            cat_channel = await self.bot.fetch_channel(category.group(1))
            for target in cat_channel.channels:
                if isinstance(target, discord.TextChannel):
                    await self.archive_channel(target, output)
        else:
            target = await self.bot.fetch_channel(target.group(1)) if target else channel
            await self.archive_channel(target, output)

    async def archive_channel(self, target, output):
        messages_indexed = 0
        embed = embed_indexing(target.name, messages_indexed)
        progress_message = await output.send(embed=embed)

        archive_text = ""
        archive_text += f"Archive for #{target.name}\n"
        curr_date = None  # day month year of messages
        curr_message = None
        while True:
            messages = await target.history(limit=200, oldest_first=True, after=curr_message).flatten()
            if len(messages) == 0:
                break
            for message in messages:
                curr_message = message
                messages_indexed += 1

                date = message.created_at.strftime("%d %b %Y")
                if curr_date != date:
                    curr_date = date
                    archive_text += f"\n{date}\n"

                author = f"{message.author.name}#{message.author.discriminator}"
                content = message.content
                time = message.created_at.strftime("%H:%M:%S")
                # if message.edited_at:
                #    time += message.edited_at.strftime(" (%H:%M:%S)")
                attachments_urls = [x.url for x in message.attachments]
                attachments_txt = "\n".join(attachments_urls)

                message_entry = f"{time} {author}: {content}\n"
                if attachments_txt:
                    message_entry += f"{attachments_txt}\n"
                archive_text += message_entry
            await progress_message.edit(embed=embed_indexing(target.name, messages_indexed, curr_message.jump_url))

        await progress_message.edit(embed=embed_indexing(target.name, messages_indexed, curr_message.jump_url, done=True))

        with open("archive_output.txt", "w", encoding="utf-8") as f:
            f.write(archive_text)

        await output.send(file=discord.File("archive_output.txt", f"archive_{target.id}.txt"))

    @commands.command(aliases=[f"say"])
    async def make_archivist_say(self, ctx):
        if not await self.bot.has_perm(ctx, owner_only=True, dm=False): return
        content = helpers.remove_invoke(ctx.message.content)
        re_target = re.search(r"target=(\d+)", content)
        if re_target:
            target_channel = await self.bot.fetch_channel(re_target.group(1))
            content = content.replace(re_target.group(0), "")
        else:
            target_channel = ctx.channel

        await target_channel.send(content)


def embed_indexing(channel_name: str, messages_indexed: int, last_message_url: str=None, done=False):
    """
    Modifies an embed's description and thumbnail to display the progress through downloading a video.
    Arguments:
        embed - An embed to modify the description of.
        item - The PlaylistItem being downloaded.
        percent - Provided as a decimal from 0 to 1
    """
    embed = helpers.default_embed()
    embed.description = ""
    if done:
        embed.description += f":book: **#{channel_name} archived.**\n"
    else:
        embed.description += f":book: **Archiving #{channel_name}...**\n"

    embed.description += f"Indexed: {messages_indexed}\n"

    if last_message_url and not done:
        embed.description += f"[Last message]({last_message_url})\n"

    return embed


def setup(bot):
    bot.add_cog(ArchiveBotCog(bot))
