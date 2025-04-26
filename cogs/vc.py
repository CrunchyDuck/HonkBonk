from discord.ext import commands
import discord.errors
import discord
import asyncio
from random import choice
import helpers
import re
from time import time
import os
from dataclasses import dataclass, field
from math import ceil
from random import shuffle
import aiohttp
import subprocess
import requests
import json
import typing
from typing import List

class VoiceChannels(commands.Cog, name="voice_channels"):
    prefix = "vc"

    def __init__(self, bot):
        self.bot = bot
        self.connections = {}  # A dictionary of guild_id: ServerAudio
        self.session = aiohttp.ClientSession()

        # fun stuff
        self.not_in_vc_replies = [
            "You're not in a VC you big DUMMY!",
            "silly little plonker",
        ]
        self.yt_api_key = self.bot.settings["YT_API_KEY"][0]
        self.help_dict = {
            "Commands": [f"{self.prefix}." + x for x in
                         ["join", "leave", "play", "description", "search", "screenshot", "seek", "fastforward", "rewind",
                          "clear", "repeat", "skip", "queue", "nowplaying", "pause"]]
        }

    # TODO: Screenshot from video function
    # TODO: Add admin override
    @commands.command(aliases=[f"{prefix}.join", f"{prefix}.getin"])
    async def join_vc_command(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        await self.join_voice_channel(ctx)

    @commands.command(aliases=[f"{prefix}.leave", f"{prefix}.go", f"{prefix}.fuckoff", f"{prefix}.pissoff"])
    async def leave_vc_command(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        if await self.leave_voice_channel(ctx):
            replies = ["bye bye :)", "cya :O", "goobye uwu", "boutta head out", "nyeoomm"]
            await ctx.send(choice(replies))

    @commands.command(aliases=[f"{prefix}.play", f"{prefix}.p", f"{prefix}.oi"])
    async def play_song_command(self, ctx):
        await self.play_song(ctx)

    @commands.command(aliases=[f"{prefix}.playtop", f"{prefix}.pt"])
    async def play_song_top(self, ctx):
        await self.play_song(ctx, 0)

    # async def play_song(self, ctx, pos=-1):
    #     if not await self.bot.has_perm(ctx, dm=False): return
    #     content = helpers.remove_invoke(ctx.message.content)
    #     # TODO: Add spotify support. See: https://spotipy.readthedocs.io/en/2.12.0/
    #     # Try to get a link.
    #     url_match = re.match("^<?([^ >]+)", content)
    #     if url_match:
    #         # YouTube URL match
    #         if re.match(
    #                 r"(?:https?://)?(?:(?:(?:www\.?)?youtube\.com(?:/(?:(?:watch\?.*?(v=[^&\s]+).*)|(?:v(/.*))|(channel/.+)|(?:user/(.+))|(?:results\?(search_query=.+))))?)|(?:youtu\.be(/.*)?))",
    #                 url_match.group(1)):
    #             # Try to match a YouTube video.
    #             try:
    #                 video_id = extract.video_id(url_match.group(1))
    #                 vc = await self.get_connected_vc(ctx, join_if_not_in=True)
    #                 item = await PlaylistItem.create_from_video_ids(ctx.author.display_name, self.yt_api_key, [video_id],
    #                                                                 self.session)
    #                 if not item:
    #                     await ctx.send("Video too long!")
    #                     return
    #                 item = item[0]
    #                 if await vc.add_playlist_item(item, pos):
    #                     embed = embed_added_song(item)
    #                     await ctx.send(embed=embed)
    #                 return
    #             except pt_exceptions.RegexMatchError:
    #                 pass
    #
    #             # Try to match a YouTube playlist.
    #             try:
    #                 playlist_id = extract.playlist_id(url_match.group(1))  # FIXME: This keyerrors on fail, use own regex.
    #                 vc = await self.get_connected_vc(ctx, join_if_not_in=True)
    #                 playlist_id = playlist_id.replace(">", "")  # Match picks up the tag for hiding a link's embed.
    #                 playlist_items = await PlaylistItem.create_from_playlist_id(ctx.author.display_name, self.yt_api_key,
    #                                                                             playlist_id, self.session)
    #                 if not playlist_items:
    #                     await ctx.send("Cannot find a playlist with the provided URL D:")
    #                     return
    #                 await vc.add_playlist_list(playlist_items, pos)
    #                 await ctx.send(f"Added {len(playlist_items)} videos!!!")  # TODO: Improve return of "added playlist"
    #                 return
    #             except KeyError:
    #                 pass
    #             except pt_exceptions.RegexMatchError:
    #                 pass
    #         # Try to match a bandcamp page
    #         # else:
    #         #     items = await PlaylistItem.create_from_bandcamp_url(ctx.author.display_name, url_match.group(1))
    #         #     if items:
    #         #         vc = await self.get_connected_vc(ctx, join_if_not_in=True)
    #         #         await vc.add_playlist_list(items, pos)
    #         #         await ctx.send(f"Added {len(items)} videos!!!")
    #         #         return
    #
    #     # Use the message as a YouTube query.
    #     if content:
    #         result_num_match = re.search(r"res=(\d+)", content)
    #         if result_num_match:
    #             content = content.replace(result_num_match.group(0), "")
    #             result_num = int(result_num_match.group(1))
    #             # Range check
    #             if not 1 <= result_num <= 50:
    #                 result_num = max(min(result_num, 50), 1)
    #                 await ctx.send(f"{result_num_match.group(0)} out of range, set to {result_num}.")
    #
    #             result_num -= 1  # 0-index the number.
    #         else:
    #             result_num = 0
    #
    #         r = await youtube_search(self.yt_api_key, content, self.session)
    #         r = r["items"]
    #         number_of_results = len(r)
    #         if not number_of_results:
    #             await ctx.send(f"No results for {content}")
    #             return
    #         result_num = min(result_num, number_of_results - 1)  # Ensure result_num isn't outside of bounds.
    #
    #         video_data = r[result_num]
    #         vc = await self.get_connected_vc(ctx, join_if_not_in=True)
    #         try:
    #             item = await PlaylistItem.create_from_video_ids(ctx.author.display_name, self.yt_api_key,
    #                                                             [video_data["id"]["videoId"]], self.session)
    #             item = item[0]
    #         except IndexError:
    #             await ctx.send("v-v-video too long >//>")
    #             return
    #         if await vc.add_playlist_item(item, pos):
    #             embed = embed_added_song(item)
    #             await ctx.send(embed=embed)
    #         return
    #
    #     # Resume a paused song.
    #     vc = await self.get_connected_vc(ctx, join_if_not_in=True)
    #     if vc:
    #         # TODO: Toggle if already playing.
    #         reply = await vc.play()
    #         await ctx.send(reply)
    #     else:
    #         await ctx.send("Not in a VC!")

    @commands.command(aliases=[f"{prefix}.description"])
    async def return_description(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        vc = await self.get_connected_vc(ctx)
        if not vc:
            await ctx.send("Nothing playing~~")
            return
        try:
            await ctx.send(f"```{vc.get_description()[:1990]}```")
        except PlaylistEmpty:
            await ctx.send("owo no")
            return

    @commands.command(aliases=[f"{prefix}.search"])
    async def yt_query_list(self, ctx):
        """Displays a list things that could be played and allows the user to choose."""
        if not await self.bot.has_perm(ctx, dm=False): return
        # Get query from message.
        content = helpers.remove_invoke(ctx.message.content)
        r = await youtube_search(self.yt_api_key, content, self.session)
        total_results = r["pageInfo"]["totalResults"]
        if not total_results:
            await ctx.send(f"No results for {content}")
            return

        print(r["items"][0])
        ids = [x["id"]["videoId"] for x in r["items"]]  # comma separated IDs.
        results = await PlaylistItem.create_from_video_ids(ctx.author.display_name, self.yt_api_key, ids, self.session, duration=0)

        page_total = ceil(len(results) / 5)

        # Create YouTubeSearchPages
        yt_pages = []
        for page_num in range(page_total):
            from_i = page_num * 5
            to_i = (page_num + 1) * 5
            videos_in_page = results[from_i:to_i]
            page = self.YouTubeSearchPage(videos_in_page, page_num, total_results, content, page_total, 5)
            yt_pages.append(page)

        # Create reactive message
        first_page = self.YouTubeSearchPage.display_page(yt_pages[0])
        msg = await ctx.send(embed=first_page)
        await self.bot.ReactiveMessageManager.create_reactive_message(msg, self.YouTubeSearchPage.display_page, yt_pages,
                                                                on_message_func=self.on_message_youtube_search,
                                                                wrap=True, seconds_active=60, users=[ctx.author.id])

    async def on_message_youtube_search(self, message, reactive_message) -> bool:
        m = re.match(r"\d+", message.content)
        if not m:
            return False

        # Get the video they're requesting
        num = int(m.group(0))
        try:
            page_num, page_pos = divmod(num-1, reactive_message.message_pages[0].per_page)
            result = reactive_message.message_pages[page_num].videos[page_pos]
        except IndexError:
            await message.channel.send(f"{num} invalid >:(")
            return True

        # Get the VC they or the bot are in.
        vc = await self.get_connected_vc(message, join_if_not_in=True)
        if not vc:
            return True

        # Add the song to the VC
        await self.bot.ReactiveMessageManager.remove_reactive_message(reactive_message)
        if await vc.add_playlist_item(result):
            await message.channel.send(embed=embed_added_song(result))
        return True

    @commands.command(aliases=[f"{prefix}.screenshot"])
    async def take_screenshot_now(self, ctx):
        # FIXME: Screenshot function doesn't work. Think it's to do with discord hogging ffmpeg
        if not await self.bot.has_perm(ctx, owner_only=True, dm=False): return
        vc = await self.get_connected_vc(ctx)
        if not vc:
            await ctx.send("b-baka n-nothing to scewwen *shot* ;3")
            return

        try:
            path = vc.screenshot_current_time()
        except NoAudioLoaded:
            await ctx.send("o-owo i-it doesn't look like there's anything to take a picture of~")
            return
        await ctx.send(file=discord.File(path))
        try:
            os.remove(path)
        except:
            pass

    @commands.command(aliases=[f"{prefix}.seek"])
    async def seek_to_position(self, ctx):
        await self.seek(ctx)

    @commands.command(aliases=[f"{prefix}.ff", f"{prefix}.fastforward", f"{prefix}.forward"])
    async def fast_forward(self, ctx):
        await self.seek(ctx, forward=True)

    @commands.command(aliases=[f"{prefix}.rewind", f"{prefix}.back"])
    async def rewind(self, ctx):
        if ctx.message.content == "c.vc.back back":
            await ctx.send("bka")
            return
        await self.seek(ctx, back=True)

    async def seek(self, ctx, *, forward=False, back=False):
        """Handles seeking functions commands"""
        if not await self.bot.has_perm(ctx, dm=False): return
        vc = await self.get_connected_vc(ctx)
        if not vc:
            await ctx.send("what")
            return

        seek_time = re.match(r"^([^ ]+)", helpers.remove_invoke(ctx.message.content))
        if not seek_time:
            return

        try:
            seek_time = helpers.SMPTE_to_seconds(seek_time.group(1))
            if forward:
                seek_pos = vc.seek_forward(seek_time)
                await ctx.send(f"nyeormed to {helpers.seconds_to_SMPTE(seek_pos)}")
            elif back:
                seek_pos = vc.seek_back(seek_time)
                await ctx.send(f"beep beep now at {helpers.seconds_to_SMPTE(seek_pos)}")
            else:
                vc.seek_song(seek_time)
                await ctx.send("s o o k")
            return
        except NoAudioLoaded:
            await ctx.send("No song to seek!")
            return
        except InvalidSeek:
            await ctx.send("Invalid s-seek x3c")
            return

    @commands.command(aliases=[f"{prefix}.clear"])
    async def clear_playlist(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        # Get the appropriate ServerAudio.
        vc = await self.get_connected_vc(ctx)
        if vc is None:
            await ctx.send("not in a vc silly uwu")
            return

        try:
            vc.clear_playlist()
        except PlaylistEmpty:
            await ctx.send("a-alwedy empty owo")
            return
        await ctx.send("wiped clean ;3")

    @commands.command(aliases=[f"{prefix}.skip", f"{prefix}.s", f"{prefix}.next"])
    async def skip_song(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        # TODO: Remove song from position in queue

        # Get the appropriate ServerAudio.
        vc = await self.get_connected_vc(ctx)
        if vc is None:
            ctx.send(":(")
            return

        try:
            vc.skip_song()
            await ctx.send(":fast_forward: Skipped!")
            await vc.play()
        except PlaylistEmpty:
            return

    @commands.command(aliases=[f"{prefix}.repeat", f"{prefix}.r", f"{prefix}.loop"])
    async def repeat_selection(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        # Switch between loop none, loop 1, loop all
        vc = await self.get_connected_vc(ctx)
        if not vc:
            await ctx.send("Not in a VC!")
            return
        vc.loop.next_state()
        if vc.loop.state == "one":
            emoji = ":repeat_one:"
        elif vc.loop.state == "all":
            emoji = ":repeat:"
        else:
            emoji = ":regional_indicator_x:"

        await ctx.send(f"{emoji} **Looping {vc.loop.state}**")

    @commands.command(aliases=[f"{prefix}.shuffle", f"{prefix}.jumble", f"{prefix}.mix", f"{prefix}.shake"])
    async def shuffle_list(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        # Switch between loop none, loop 1, loop all
        vc = await self.get_connected_vc(ctx)
        if not vc:
            await ctx.send("Not in a VC!")
            return
        try:
            vc.shuffle()
        except PlaylistEmpty:
            await ctx.send("Nothing to shuffle!")
            return

    @commands.command(aliases=[f"{prefix}.pause", f"{prefix}.stop", f"{prefix}.shut", f"{prefix}.no"])
    async def pause_song(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        # Make sure their query was valid.

        # Get the appropriate ServerAudio.
        vc = await self.get_connected_vc(ctx)
        if not vc:
            return
        vc.pause()
        await ctx.send("⏸️ pawzed!!")

    @commands.command(aliases=[f"{prefix}.queue", f"{prefix}.q"])
    async def show_queue(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        vc = await self.get_connected_vc(ctx)
        if not vc:
            await ctx.send("Not in a vc silly billy uwu")
            return

        pages = vc.create_pages()
        if not pages:
            await ctx.send("Not playing anything!")
            return

        first_page = vc.display_playlist(pages[0])
        msg = await ctx.send(embed=first_page)
        await self.bot.ReactiveMessageManager.create_reactive_message(msg, vc.display_playlist, pages,
                                                                wrap=True, users=[ctx.message.author.id])

    @commands.command(aliases=[f"{prefix}.np", f"{prefix}.nowplaying", f"{prefix}.whatitdo"])
    async def currently_playing(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        vc = await self.get_connected_vc(ctx)
        if not vc:
            await ctx.send("im not in a VC YOU IDIOTTT AHAAAAAAA (remind me to add more replies to this)")
            return

        try:
            embed = vc.now_playing()
            await ctx.send(embed=embed)
        except PlaylistEmpty:
            await ctx.send("Nothing playing!")

    @commands.command(aliases=[f"{prefix}.playlist"])
    async def user_playlist(self, ctx):
        # User playlists allow users to continue what they were listening to before.
        # TODO: Allow users to save playlists.
        pass

    # === Help functions ===
    # TODO: Document undocumented functions.
    @commands.command(f"{prefix}.help")
    async def vc_module_help(self, ctx):
        """The core help command."""
        if not await self.bot.has_perm(ctx, dm=True): return
        desc = "Play music! Play videos! Upset the ears of your friends!"
        await ctx.send(embed=self.bot.create_help(self.help_dict, desc))

    @commands.command(aliases=[f"{prefix}.join.help"])
    async def join_vc_command_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
        vibe in vc with you

        **Examples:**
        honkbonk vibes with you
        `c.vc.join`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.leave.help"])
    async def leave_vc_command_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
        unvibe from the vc

        **Examples:**
        honkbonk goes out for milk
        `c.vc.leave`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.p.help", f"{prefix}.play.help"])
    async def play_song_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
        Resume a video, or add a new video to the end of the playlist.
        Youtube videos or bandcamp albums supported.
        
        **Examples:**
        Resumes playing the current video.
        `c.vc.play`
        Adds this video to the end of the current playlist.
        `c.vc.p https://youtu.be/J7sU9uB8XtU`
        Add a whole heckin playlist
        `c.vc.p <https://www.youtube.com/playlist?list=PLeSM-rQ-jVpulMI3sas4GE6Xh2XH4pwqD>`
        Add a Bandcamp album
        `c.vc.p <https://music.disasterpeace.com/album/disasters-for-piano>`
        Search YouTube.
        `c.vc.p duck asks for bread`
        Search YouTube, and take the 5th result. Maximum for res is 50.
        `c.vc.p pigeon cooing sounds res=5`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.description.help"])
    async def return_description_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            Get the description of the current video!

            **Examples:**
            get their epic affiliate link for 50% audible dot. com
            `c.vc.description`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.search.help"])
    async def yt_query_list_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            Return a list of results for a YouTube search.

            **Examples:**
            y'know.
            `c.vc.search markiplier fnaf|makiplier happy wheels|pewdiepie roleplay`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.screenshot.help"])
    async def take_screenshot_now_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            Get a screenshot of the video right now!

            **Examples:**
            ;)
            `c.vc.screenshot`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.seek.help"])
    async def seek_to_position_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
        Go to a point in the video.

        **Examples:**
        Go to 5 minutes 30 seconds
        `c.vc.seek 5:30`
        Go to that part that was *really* funny
        `c.vc.seek 20.5`
        look for better days
        `c.vc.seek 2:32:12.05`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.ff.help", f"{prefix}.fastforward.help", f"{prefix}.forward.help"])
    async def fast_forward_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
        Go forward an amount of time.

        **Examples:**
        skip ad for brilliant.organization
        `c.vc.forward 2:00`
        zoom past the part where they talk about their subscribers
        `c.vc.ff 5:00`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.rewind.help", f"{prefix}.back.help"])
    async def rewind_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            go bak

            **Examples:**
            go bak.
            `c.vc.rewind 5`
            gob ak
            `c.vc.back 5:5`
            bak
            `c.vc.back back`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.clear.help"])
    async def clear_playlist_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            Clear the whole playlist!! (current video not included)

            **Examples:**
            remove pidge's gay stuff
            `c.vc.clear`
            remove my gay stuff
            `c.vc.clear`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.r.help", f"{prefix}.repeat.help", f"{prefix}.loop.help"])
    async def repeat_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            loop this, loop all, loop NONE!

            **Examples:**
            toggle loop 1
            `c.vc.repeat`
            toggle loop 2
            `c.vc.loop`
            toggle loop 2
            `c.vc.loop`
            toggle loop 2
            `c.vc.loop`
            toggle loop 2
            `c.vc.loop`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.skip.help", f"{prefix}.s.help"])
    async def skip_song_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
        Mercilessly ends the current song without mercy.

        **Examples:**
        skipping past "all the single furries"
        `c.vc.skip`
        erasing "carrot cake asmr"
        `c.vc.s`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.q.help", f"{prefix}.queue.help"])
    async def show_queue_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            display queue

            **Examples:**
            oh man what's next
            `c.vc.q`
            who summoned this banger
            `c.vc.queue`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.np.help", f"{prefix}.nowplaying.help", f"{prefix}.whatitdo.help"])
    async def currently_playing_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
        Shows the progress through the current song.

        **Examples:**
        seeing how long till the suffering ends
        `c.vc.np`
        tracking the demise of the universe
        `c.vc.nowplaying`
        being casual with the homies
        `c.vc.whatitdo`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.pause.help", f"{prefix}.stop.help", f"{prefix}.shut.help", f"{prefix}.no.help"])
    async def pause_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
            Shows the progress through the current song.

            **Examples:**
            Temporarily suspending your enjoyable experience while you make tea
            `c.vc.pause`
            layin' down the law
            `c.vc.stop`
            rude
            `c.vc.shut`
            expressing discontent with the state of the world
            `c.vc.no`
            """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    # TODO: Lyrics fetch.

    # Functions
    async def join_voice_channel(self, ctx) -> typing.Union['ServerAudio', None]:
        await ctx.guild.change_voice_state(channel=None)
        vc = ctx.author.voice
        if not vc:
            await ctx.send(choice(self.not_in_vc_replies))
            return None
        vc = vc.channel
        message_channel = ctx.channel

        try:
            voice_client = await vc.connect()
        except asyncio.TimeoutError:
            await ctx.send("Failed to connect, for some reason.")
            return None

        await ctx.guild.change_voice_state(channel=vc)
        self.connections[ctx.guild.id] = ServerAudio(voice_client, message_channel, self.bot.loop, self.yt_api_key)
        return self.connections[ctx.guild.id]

    async def leave_voice_channel(self, ctx) -> bool:
        vc = await self.get_connected_vc(ctx)
        if not vc:
            return False

        vc.cleanup()
        await ctx.guild.change_voice_state(channel=None)
        del self.connections[ctx.guild.id]
        return True

    async def get_connected_vc(self, ctx, join_if_not_in=False) -> typing.Union['ServerAudio', None]:
        """Gets the VC that this"""
        try:
            vc = self.connections[ctx.guild.id]
        except KeyError:
            if join_if_not_in:
                vc = await self.join_voice_channel(ctx)
            else:
                return None

        return vc

    @dataclass
    class YouTubeSearchPage:
        videos: List['PlaylistItem']
        page_num: int

        search_total: int
        search_term: str
        page_total: int
        per_page: int

        @staticmethod
        def display_page(page):
            embed = helpers.default_embed()
            embed.title = f"Results for **{page.search_term}**"
            embed.description = ""
            for result_num in range(len(page.videos)):
                video = page.videos[result_num]
                position = result_num + 1 + (page.page_num * 5)
                embed.description += f"`{position}.` [{video.title}]({video.url}) by {video.author} `{helpers.seconds_to_SMPTE(video.duration)}`\n\n"
            footer_text = f"Page {page.page_num + 1}/{page.page_total} | {page.search_total} results"
            embed.set_footer(text=footer_text)
            return embed


class Player(discord.FFmpegPCMAudio):
    def __init__(self, source, duration, *, seek=0):
        if seek == duration:
            seek -= 0.5  # ffmpeg gives a warning if we seek to the end of a song.
        self.current_time = seek  # Time in seconds
        self.length_of_song = duration
        self.source = source
        # pipes = subprocess.Popen(rf"""ffprobe -i {source} -show_entries format=duration -v quiet -of csv="p=0" """, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # self.length_of_song = float(pipes.stdout.read())

        options = f"-ss {seek}"
        super().__init__(source, options=options)

    def read(self):
        ret = super().read()
        if ret != b'':
            self.current_time += 0.02
        return ret


@dataclass
class PlaylistItem:
    """Represents a video to be played by ServerAudio"""
    # TODO: Split this into aggregate items for youtube/bandcamp
    source: str  # "youtube" or "bandcamp"
    url: str = field(repr=False)
    title: str
    author: str
    description: str = field(repr=False)
    duration: int = field(repr=False)
    requested_by: str
    release_date: str
    thumbnail_url: str = field(default="", repr=False)

    @staticmethod
    async def create_from_video_ids(requested_by: str, youtube_api_key: str, video_ids: [str], session: aiohttp.ClientSession,
                                    duration=3600*3) -> List['PlaylistItem']:
        """Creates a PlaylistItem based off of a given YouTube video.

        Arguments:
            requested_by - The name of the user who requested this.
            youtube_api_key - Key to access the YouTube Data API
            video_id - The ID of the video - This is NOT a full URL, only the ID.
            session - Async session to run on.
        Returns: Filled PlaylistItem
        """
        ret_list = []
        data = {"source": "youtube", "requested_by": requested_by}
        for chunk_of_videos in chunk_list(video_ids, 50):
            r = await youtube_video_search(youtube_api_key, ",".join(chunk_of_videos), session)
            r = r["items"]

            for vid in r:
                data["url"] = "https://youtu.be/" + vid["id"]
                data["title"] = vid["snippet"]["title"]
                data["author"] = vid["snippet"]["channelTitle"]
                data["description"] = vid["snippet"]["description"]
                data["thumbnail_url"] = vid["snippet"]["thumbnails"]["high"]["url"]
                data["release_date"] = vid["snippet"]["publishedAt"][:10]

                dur_text = vid["contentDetails"]["duration"]  # Yt provides a weird format.
                match = re.search(r"T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", dur_text)
                if not match:
                    continue
                dur = 0
                if match.group(1):
                    dur += int(match.group(1)) * 3600
                if match.group(2):
                    dur += int(match.group(2)) * 60
                if match.group(3):
                    dur += int(match.group(3))
                data["duration"] = dur

                if duration and dur >= duration:
                    continue
                ret_list.append(PlaylistItem(**data))

            # Potentially useful data.
            #r["statistics"]["viewCount"]
            #r["statistics"]["likeCount"]
            #r["statistics"]["dislikeCount"]
            #r["statistics"]["viewCount"]
            #r["topicDetails"]  # Has wikipedia links related to the videos??
        return ret_list

    @staticmethod
    async def create_from_playlist_id(requested_by: str, youtube_api_key: str, playlist_id: str, session: aiohttp.ClientSession,
                                      duration=3600) -> List['PlaylistItem']:
        """Creates a list of PlaylistItem based off of a given YouTube playlist.

        Arguments:
            requested_by - The name of the user who requested this.
            youtube_api_key - Key to access the YouTube Data API
            playlist_id - The ID of the playlist - This is NOT a full URL, only the ID.
            session - Async session to run on.
        Returns: List of filled PlaylistItem
        """
        # TODO: Implement playlist compilation
        #session = aiohttp.ClientSession()
        api_endpoint = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {"part": "contentDetails", "key": youtube_api_key, "playlistId": playlist_id, "maxResults": 50}
        url = helpers.url_with_params(api_endpoint, params)

        # FIXME: Error handling in the event the API returns bad. See https://developers.google.com/youtube/v3/docs/playlistItems/list#errors
        #total_videos = r["pageInfo"]["totalResults"]
        video_ids = []
        while True:
            r = await session.request(method="GET", url=url)
            r = await r.json()
            for video_data in r["items"]:
                video_ids.append(video_data["contentDetails"]["videoId"])
            if "nextPageToken" not in r:  # last page
                break
            params["pageToken"] = r["nextPageToken"]
            url = helpers.url_with_params(api_endpoint, params)
        item_list = await PlaylistItem.create_from_video_ids(requested_by, youtube_api_key, video_ids, session, duration)

        return item_list

    @staticmethod
    async def create_from_bandcamp_url(requested_by: str, url) -> List['PlaylistItem']:
        r = requests.get(url)
        if r.status_code != 200:
            return []

        m = re.search("""<script type="application/ld\+json">(.+?)</script>""", r.text, flags=re.DOTALL)
        if not m:
            return []

        data = json.loads(m.group(1))

        items = []
        p_data = {"source": "bandcamp", "requested_by": requested_by}
        p_data["author"] = data["publisher"]["name"]
        p_data["description"] = ""
        p_data["release_date"] = data["datePublished"]
        p_data["thumbnail_url"] = data["image"]
        for track in data["track"]["itemListElement"]:
            track = track["item"]
            p_data["title"] = track["name"]
            p_data["url"] = ""
            p_data["duration"] = 0
            for prop in track["additionalProperty"]:
                if prop["name"] == "duration_secs":
                    p_data["duration"] = prop["value"]
                elif prop["name"] == "file_mp3-128":
                    p_data["url"] = prop["value"]
            p = PlaylistItem(**p_data)
            items.append(p)

        return items


# Requires FFMPEG
class ServerAudio:
    def __init__(self, voice_client: discord.VoiceChannel, message_channel, async_loop, yt_api_key):
        self.vc = voice_client
        self.message_channel = message_channel  # The place notifications and messages are sent.
        # FIXME: The first song in the playlist tends to be skipped.
        #  Could be fixed by combining currently_playing and playlist, such that playlist[0] == currently_playing
        self.playlist = []  # List of PlaylistItem.
        self.player = None
        self.download_progress = -1
        self.downloading = False
        self.stop_download = False
        self.stopping = False
        self.video_path = f"./attachments/{self.vc.guild.id}.mp4"
        self.async_loop = async_loop  # Used to run song_end.
        self.yt_api_key = yt_api_key
        self.song_ended = False

        self.loop = helpers.StateObject("off", "one", "all")
        asyncio.run_coroutine_threadsafe(self.check_if_song_ended_loop(), self.async_loop)

    # Handle moving to the next song.
    async def check_if_song_ended_loop(self):
        while True:
            if self.song_ended:
                await self.song_end()
                self.song_ended = False
            await asyncio.sleep(1)

    async def add_playlist_item(self, item: PlaylistItem, pos=-1):
        """Wrapper for add_song to allow for PlaylistItems"""
        #await self.add_song(item.url, item.title, item.author, item.description, item.duration)
        if pos >= 0:
            self.playlist.insert(pos+1, item)
        else:
            self.playlist.append(item)
        if len(self.playlist) == 1:  # Only the song that was just added exists.
            await self.play()
        else:
            return True
            #await self.message_channel.send(f"Added \"{item.title}\" by \"{item.author}\"")

    async def add_playlist_list(self, items: List[PlaylistItem], pos=-1):
        for item in items:
            await self.add_playlist_item(item, pos)
            if pos >= 0:  # Update position with the new size of the playlist.
                pos += 1
        return True

    async def play(self) -> str:
        """
        Play paused or queued audio.
        """
        # Song isn't playing/paused.
        if self.player is None:
            # Prepare the first item on the playlist.
            if self.stopping:
                return "Stopping..."
            if not self.playlist:
                # Playlist empty
                return "Nothing to play!"
            await self.download(self.playlist[0])
            if self.player is None:  # Download failed/stopped
                return "Download failed."
            self.vc.play(self.player, after=self.song_ended_event)
            return f"Playing: {self.playlist[0].title}"
        # Song was paused.
        else:
            self.vc.resume()
            return ":arrow_forward: **Resuming**"

    def get_description(self):
        if not self.playlist:
            raise PlaylistEmpty
        return self.playlist[0].description

    def shuffle(self):
        if not self.playlist:
            raise PlaylistEmpty
        current_song = self.playlist.pop(0)
        shuffle(self.playlist)
        self.playlist.insert(0, current_song)

    def seek_song(self, seek_in_seconds: int):
        """

        Arguments:
            seek_in_seconds - The time to seek to, in seconds.
        Raises:
            NoAudioLoaded - There's no audio to seek
            InvalidSeek - Seek goes out of bounds.
        """
        if not self.player:
            raise NoAudioLoaded
        if not 0 <= seek_in_seconds <= self.player.length_of_song:
            raise InvalidSeek

        self.vc.pause()
        self.player = Player(self.video_path, self.playlist[0].duration, seek=seek_in_seconds)
        self.vc.play(self.player, after=self.song_ended_event)
        return seek_in_seconds

    def seek_back(self, seek_offset: int):
        if not self.player:
            raise NoAudioLoaded
        seek_pos = max(self.player.current_time - seek_offset, 0)
        return self.seek_song(seek_pos)

    def seek_forward(self, seek_offset: int):
        if not self.player:
            raise NoAudioLoaded
        seek_pos = min(self.player.current_time + seek_offset, self.player.length_of_song)
        return self.seek_song(seek_pos)

    def pause(self):
        self.vc.pause()

    def skip_song(self):
        """Gets the next song ready to be played."""
        self.vc.pause()
        if not self.playlist:
            raise PlaylistEmpty
        self.player = None
        self.stop_download = True
        self.playlist.pop(0)  # remove current song.

    def clear_playlist(self):
        if not self.playlist:
            raise PlaylistEmpty
        current_song = self.playlist.pop(0)
        self.playlist = [current_song]

    async def download(self, item: PlaylistItem) -> None:
        if item.source == "youtube":
            await self.download_youtube_item(item)
        # elif item.source == "bandcamp":
        #     await self.download_bandcamp_item(item)

    # async def download_youtube_item(self, item: PlaylistItem) -> None:
    #     if self.downloading or self.stopping:
    #         return
    #     self.downloading = True
    #     try:
    #         YouTubeObj = pytube.YouTube(item.url)
    #     except pt_exceptions.VideoPrivate:
    #         await self.message_channel.send("Video is private!")
    #         self.downloading = False
    #         return
    #
    #     # FIXME: Fix this to not download the highest quality video possible.
    #     stream = YouTubeObj.streams.filter(progressive=True).order_by("abr")[-1]
    #     size = stream.filesize
    #     amount_downloaded = 0
    #
    #     path = f"./attachments/{self.vc.guild.id}.mp4"
    #     start_time = time()
    #     self.stop_download = False  # Removes any previous requests to stop the download.
    #     embed = helpers.default_embed()  # Downloading embed.
    #     embed = embed_downloading(embed, item, 0)
    #     update_message = await self.message_channel.send(embed=embed)
    #     with open(path, "wb") as f:
    #         stream = pytube.request.stream(stream.url)
    #         while amount_downloaded < size:
    #             if self.stop_download:
    #                 break
    #             chunk = next(stream, None)
    #             if chunk:
    #                 f.write(chunk)
    #                 amount_downloaded += len(chunk)
    #             else:
    #                 break
    #             now_time = time()
    #             if now_time - start_time >= 1:
    #                 self.download_progress = amount_downloaded / size
    #                 start_time = now_time
    #                 embed = embed_downloading(embed, item, self.download_progress)
    #                 await update_message.edit(embed=embed)
    #                 await asyncio.sleep(1)  # Let the program send out a heartbeat.
    #     self.download_progress = -1
    #     self.downloading = False
    #     if self.stop_download:
    #         embed.description = "Stopped downloady"
    #         await update_message.edit(embed=embed_stop_download(embed, item))
    #         return
    #
    #     # Create the "Now playing" embed
    #     self.player = Player(self.video_path, self.playlist[0].duration)
    #     embed = self.now_playing()
    #     await update_message.edit(embed=embed)

    async def download_bandcamp_item(self, item: PlaylistItem) -> None:
        if self.downloading or self.stopping:
            return

        self.downloading = True
        r = requests.get(item.url, stream=True)
        length = int(r.headers["Content-Length"])
        start_time = time()
        amount_downloaded = 0

        self.stop_download = False  # Removes any previous requests to stop the download.
        embed = helpers.default_embed()  # Downloading embed.
        embed = embed_downloading(embed, item, 0)
        update_message = await self.message_channel.send(embed=embed)
        with open(self.video_path, "wb") as f:  # FIXME: This sometimes hitches
            print("started")
            for chunk in r.iter_content(chunk_size=1024*1024):  # 1MB chunks
                if self.stop_download:
                    break
                f.write(chunk)
                amount_downloaded += len(chunk)
                now_time = time()
                if now_time - start_time >= 1:
                    self.download_progress = amount_downloaded / length
                    start_time = now_time
                    embed = embed_downloading(embed, item, self.download_progress)
                    print(amount_downloaded)
                    #await update_message.edit(embed=embed)
                    #await asyncio.sleep(1)  # Let the program send out a heartbeat.

        self.download_progress = -1
        self.downloading = False
        if self.stop_download:
            embed.description = "Stopped downloady"
            await update_message.edit(embed=embed_stop_download(embed, item))
            return

        # Create the "Now playing" embed
        self.player = Player(self.video_path, self.playlist[0].duration)
        embed = self.now_playing()
        await update_message.edit(embed=embed)

    def screenshot_current_time(self) -> str:
        if not self.player:
            raise NoAudioLoaded
        output_path = self.video_path[:-3] + "jpg"
        pipes = subprocess.Popen(rf"""ffmpeg -ss {self.player.current_time} -i {self.video_path} -vframes 1 -q:v 4 {output_path}""",
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        #print(pipes.stderr.read())
        #print(pipes.stdout.)
        return output_path

    async def song_end(self):
        if self.loop.state == "all":
            self.player = None
            current_song = self.playlist.pop(0)
            await self.add_playlist_item(current_song)
        elif self.loop.state == "one":
            self.seek_song(0)
        else:
            self.player = None  # Clear old player away.
            self.playlist.pop(0)
        await self.play()  # Play the next song.

    def song_ended_event(self, e):
        self.song_ended = True

    def current_time_string(self):
        # current time
        if not self.player:
            return None
        current_time = helpers.seconds_to_SMPTE(self.player.current_time)
        length_of_song = helpers.seconds_to_SMPTE(self.player.length_of_song)
        return f"`{current_time} / {length_of_song}`"

    def cleanup(self):
        """Cleans up anything ongoing before the bot leaves."""
        self.stop_download = True
        self.stopping = True
        self.vc.pause()
        try:
            os.remove(self.video_path)  # FIXME: for some reason this doesn't work. Need to find a way to free up the file
        except Exception as e:
            print("Error trying to remove file: ", e)

    def create_pages(self):
        """Creates a list of ServerAudio.Page, to pass to ReactiveMessageManager.create_reactive_message"""
        total_time = 0
        song_total = len(self.playlist)
        page_total = ceil(song_total / 10)
        guild_name = self.message_channel.guild
        now_playing = self.playlist[0] if self.playlist else None
        loop_state = self.loop.state
        if loop_state == "one":
            loop_state = ":repeat_one:"
        elif loop_state == "all":
            loop_state = ":repeat:"
        else:
            loop_state = ":regional_indicator_x:"

        # Normal playlist.
        if self.playlist:
            pages = []
            for page_num in range(page_total):
                from_i = page_num * 10
                to_i = (page_num + 1) * 10
                songs_in_page = self.playlist[from_i:to_i]
                # Sum up all songs' duration.
                for s in songs_in_page:
                    total_time += s.duration

                p = self.Page(songs_in_page, page_num, now_playing, guild_name, loop_state, song_total, page_total)
                pages.append(p)

            for page in pages:
                page.total_time = total_time
            return pages
        # Only the song currently playing is on the list.
        elif now_playing:
            total_time += now_playing.duration
            p = self.Page([], 0, now_playing, guild_name, loop_state, 0, 0, total_time)
            return [p]
        else:
            return None

    def now_playing(self):
        """Returns an embed for "now playing" """
        if not self.player:
            raise PlaylistEmpty
        embed = helpers.default_embed()
        if len(self.playlist) > 1:
            next_song = self.playlist[1]
        else:
            next_song = None
        this_song = self.playlist[0]
        embed = embed_now_playing(embed, this_song, next_song, self.player.current_time)
        return embed

    @staticmethod
    def display_playlist(page_data):
        embed = helpers.default_embed()
        embed.title = f"**Queue for {page_data.guild_name}**"
        description = f"""__Now Playing:__
        [{page_data.now_playing.title}]({page_data.now_playing.url}) | `{helpers.seconds_to_SMPTE(page_data.now_playing.duration)}`
        
        __Up Next:__"""
        # Check if we have a queue, or if it's only the song currently playing.
        if page_data.page_total != 0:
            for song_num in range(len(page_data.play_list)):
                song = page_data.play_list[song_num]
                position = song_num + (page_data.page_num * 10)
                if position == 0:
                    continue
                duration = helpers.seconds_to_SMPTE(song.duration)
                description += f"\n`{position}.` [{song.title}]({song.url}) | `{duration}` | `Requested by: {song.requested_by}`\n"
            footer_text = f"Page {page_data.page_num + 1}/{page_data.page_total}"
            description += f"\n**{page_data.song_total} songs in queue | {helpers.seconds_to_SMPTE(page_data.total_time)} total length**\n**Looping: {page_data.loop_state}**"
        else:
            description += f"\nNothing! :)"
            footer_text = f"Page 0/0"

        embed.description = description
        embed.set_footer(text=footer_text)
        return embed

    @dataclass
    class Page:
        play_list: list
        page_num: int

        now_playing: PlaylistItem
        guild_name: str
        loop_state: str
        song_total: int
        page_total: int
        total_time: int = 0


async def youtube_search(youtube_api_key: str, query: str, session: aiohttp.ClientSession) -> dict:
    """Searches the YouTube API with a query.

    Arguments:
        query - What to search
    Returns: The results of the request.
    """
    # TODO: Allow the parsing of multiple pages.
    api_endpoint = "https://www.googleapis.com/youtube/v3/search"
    q = query.replace("|", "%7C")  # Allows for OR searching
    params = {"part": "snippet", "key": youtube_api_key, "q": q, "type": "video", "maxResults": 50}
    url = helpers.url_with_params(api_endpoint, params)

    r = await session.request(method="GET", url=url)
    r = await r.json()
    # NOTE: Because youtube's API is shite, even though I'm filtering for videos only, it will often slip in Topic channels.
    # Therefore, I filter them out manually here, too.
    items = list(r["items"])
    for i in range(len(items)-1, -1, -1):
        item = items[i]
        print(item["id"]["kind"])
        if item["id"]["kind"] != "youtube#video":
            r["items"].pop(i)
            print(i)
    return r


async def youtube_video_search(youtube_api_key: str, video_ids: str, session: aiohttp.ClientSession, get_all=True) -> dict:
    api_endpoint = "https://www.googleapis.com/youtube/v3/videos"
    params = {"part": "snippet,contentDetails", "key": youtube_api_key, "id": video_ids, "maxResults": 50}
    url = helpers.url_with_params(api_endpoint, params)

    r = await session.request(method="GET", url=url)
    r = await r.json()
    ret_dict = r
    if get_all:
        while "nextPageToken" in r:
            params["pageToken"] = r["nextPageToken"]
            url = helpers.url_with_params(api_endpoint, params)

            r = await session.request(method="GET", url=url)
            r = await r.json()
            ret_dict["items"] += r["items"]
    return r


def ascii_seek_position(percent: float, segments: int = 30) -> str:
    unfilled_spot = "▬"
    filled_spot = "🔘"
    blank_seek_line = unfilled_spot*segments

    percent = percent * 100
    segment_percent = 100/(segments-1)
    seek_position = round(percent / segment_percent)
    line_with_seek = blank_seek_line[:seek_position] + filled_spot + blank_seek_line[seek_position+1:]
    return line_with_seek


def embed_downloading(embed, item: PlaylistItem, percent: float):
    """
    Modifies an embed's description and thumbnail to display the progress through downloading a video.
    Arguments:
        embed - An embed to modify the description of.
        item - The PlaylistItem being downloaded.
        percent - Provided as a decimal from 0 to 1
    """
    progress_bar = helpers.ascii_progress_bar(percent)
    percent = percent * 100
    desc = f":inbox_tray: Downloading: [{item.title}]({item.url})"
    embed.description = f"{desc}\n\n`{progress_bar} {percent:.1f}%`"
    embed.set_thumbnail(url=item.thumbnail_url)
    return embed


def embed_stop_download(embed, item: PlaylistItem):
    desc = f":inbox_tray: Downloading: [{item.title}]({item.url})"
    embed.description = f"{desc}\n\nDownload stopped."
    embed.set_thumbnail(url=item.thumbnail_url)
    return embed


def embed_now_playing(embed, item: PlaylistItem, next_item: PlaylistItem = None, song_position=0):
    """Modifies an embed's title, thumbnail and description to display data about the currently playing song."""
    embed.title = "**Now Playing**"
    embed.description = f"[{item.title}]({item.url})\n{item.author}\n\n"

    embed.description += f"`{ascii_seek_position(song_position / item.duration )}`\n\n"

    embed.description += f"`{helpers.seconds_to_SMPTE(song_position)} / {helpers.seconds_to_SMPTE(item.duration)}`\n\n"

    embed.description += f"`Requested by:` {item.requested_by}\n\n"

    next_song = f"[{next_item.title}]({next_item.url})" if next_item else "Nothing"
    embed.description += f"`Up next:` {next_song}\n"
    embed.set_thumbnail(url=item.thumbnail_url)
    return embed


def embed_added_song(item: PlaylistItem):
    embed = helpers.default_embed()
    embed.set_thumbnail(url=item.thumbnail_url)
    embed.title = "Added to queue"
    embed.description = f"[{item.title}]({item.url})"
    embed.add_field(name="Channel", value=item.author)
    embed.add_field(name="Duration", value=helpers.seconds_to_SMPTE(item.duration))
    return embed
    # TODO: Time until playing?


def chunk_list(lst, chunk_size):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

# FIXME: Update on voice state change

# Exceptions
class InvalidVideoId(Exception):
    pass
class VideoTooLong(Exception):
    pass
class PlaylistEmpty(Exception):
    pass
class NoAudioLoaded(Exception):
    pass
class InvalidSeek(Exception):
    pass


async def setup(bot):
    bot.core_help_text["modules"] += ["vc"]
    await bot.add_cog(VoiceChannels(bot))
