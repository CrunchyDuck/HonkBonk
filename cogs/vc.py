from discord.ext import commands
import discord.errors
import asyncio
from random import choice
import helpers
import pytube
import pytube.exceptions as pt_exceptions
from pytube import extract, request
import re
from time import time
import requests
import os
from dataclasses import dataclass
from math import ceil


class VoiceChannels(commands.Cog, name="voice_channels"):
    prefix = "vc"

    def __init__(self, bot):
        self.bot = bot
        self.connections = {}  # A dictionary of guild_id: ServerAudio

        # fun stuff
        self.not_in_vc_replies = [
            "You're not in a VC you big DUMMY!",
            "AHAHAH YOU'RE AN IDIOT! YOU'RE NOT IN A VC!!!",
            "my god can you believe this dude ain't in a vc",
            "lmao idiot.",
            "god that's - oh man you posted cringe, you're not even in a vc.....",
            "silly little plonker",
        ]
        self.yt_api_key = self.bot.settings["YT_API_KEY"]
        self.help_dict = {
            "Commands": ["vc.join", "vc.leave", "vc.play", "vc.seek", "vc.skip", "vc.pause", "vc.np"]
        }

        #self.init_db(self.bot.cursor)
        #self.bot.Scheduler.add(self.sleep_timer_up, 60)

        # self.help_text = {
        #     "General": ["vc.sleep", "vc.guitar"],
        #     "AAAAAdmins": [f"{self.prefix}.{command}" for command in ["join", "leave"]],
        # }

        #self.api_key = getenv("YT_API_KEY")
        # self.yt = build("youtube", "v3", developerKey=self.api_key)

        #self.vcs = {}  # serverid: vc object
        #self.playlist = defaultdict(list)  # A dictionary of server:list for things to play.

        #self.search_settings = {0: {}}  # List of settings for searching within a server. 0=default

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
    async def play_song(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        content = helpers.remove_invoke(ctx.message.content)
        # Try to get a link.
        url_match = re.match("(^[^ ]+)", content)
        if url_match:
            try:
                video_id = extract.video_id(url_match.group(1))
                song_data = PlaylistItem.get_youtube_playlist_item_data(self.yt_api_key, video_id)
                vc = await self.get_connected_vc(ctx, join_if_not_in=True)
                await vc.add_song(**song_data)
                return
            except InvalidVideoId:
                await ctx.send("Cannot find a video with the provided URL.")
                return
            except pt_exceptions.RegexMatchError:
                pass

        # Use the message as a YouTube query.
        if content:
            result_num_match = re.search("res=(\d+)", content)
            if result_num_match:
                content = content.replace(result_num_match.group(0), "")
                result_num = int(result_num_match.group(1))
                # Range check
                if not 1 <= result_num <= 50:
                    result_num = max(min(result_num, 50), 1)
                    await ctx.send(f"{result_num_match.group(0)} out of range, set to {result_num}.")

                result_num -= 1  # 0-index the number.
            else:
                result_num = 0

            q = content.replace("|", "%7C")  # Allows for OR searching
            params = {"part": "snippet", "key": self.yt_api_key, "q": q, "type": "video", "maxResults": 50}
            r = requests.get("https://www.googleapis.com/youtube/v3/search", params=params).json()["items"]
            number_of_results = len(r)
            if not number_of_results:
                await ctx.send(f"No results for {content}")
                return
            result_num = min(result_num, number_of_results - 1)  # Ensure result_num isn't outside of bounds.

            video_data = r[result_num]
            vc = await self.get_connected_vc(ctx, join_if_not_in=True)
            song_data = PlaylistItem.get_youtube_playlist_item_data(self.yt_api_key, video_data["id"]["videoId"])
            await vc.add_song(**song_data)
            return

        # TODO: Check if playlist link and add.

        # Resume a paused song.
        vc = await self.get_connected_vc(ctx, join_if_not_in=True)
        if vc:
            reply = await vc.play()
            await ctx.send(reply)
        else:
            await ctx.send("Not in a VC!")

    @commands.command(aliases=[f"{prefix}.search"])
    async def yt_query_list(self, ctx):
        """Displays a list things that could be played and allows the user to choose."""
        # TODO: Add "search youtube" command

    @commands.command(aliases=[f"{prefix}.playskip", f"{prefix}.ps"])
    async def play_skip(self, ctx):
        # Like play, but put it to the top of the pile and skips the current song.
        # TODO: Add "play skip" command
        pass

    @commands.command(aliases=[f"{prefix}.seek"])
    async def seek_to_position(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        vc = await self.get_connected_vc(ctx)
        if not vc:
            await ctx.send("what")
            return

        seek_time = re.match(r"^([^ ]+)", helpers.remove_invoke(ctx.message.content))
        if not seek_time:
            return
        await vc.seek_song(seek_time.group(1))

    async def fast_forward(self, ctx):
        # TODO: Add fast forward
        pass

    async def rewind(self, ctx):
        # TODO: Add rewind
        pass

    @commands.command(aliases=[f"{prefix}.skip", f"{prefix}.s", f"{prefix}.next"])
    async def skip_song(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return

        # Get the appropriate ServerAudio.
        vc = await self.get_connected_vc(ctx)
        if vc is None:
            ctx.send(":(")
            return

        await vc.next_song()

    @commands.command(aliases=[f"{prefix}.repeat", f"{prefix}.r", f"{prefix}.loop"])
    async def repeat_selection(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        # Switch between loop none, loop 1, loop all
        vc = await self.get_connected_vc(ctx)
        if not vc:
            return
        vc.loop.next_state()
        await ctx.send(f":repeat: **Looping {vc.loop.state}**")

    @commands.command(aliases=[f"{prefix}.shuffle", f"{prefix}.jumble", f"{prefix}.mix", f"{prefix}.shake"])
    async def shuffle_list(self, ctx):
        # TODO: Add shuffle
        pass

    @commands.command(aliases=[f"{prefix}.pause", f"{prefix}.stop", f"{prefix}.shut", f"{prefix}.no"])
    async def pause_song(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        # Make sure their query was valid.

        # Get the appropriate ServerAudio.
        vc = await self.get_connected_vc(ctx)
        if not vc:
            return
        vc.pause()

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
        page_back = "◀️"
        page_forward = "▶️"
        await msg.add_reaction(page_back)
        await msg.add_reaction(page_forward)
        self.bot.ReactiveMessageManager.create_reactive_message(msg, vc.display_playlist, pages, page_back, page_forward, wrap=True, users=[ctx.message.author.id])

    @commands.command(aliases=[f"{prefix}.np", f"{prefix}.nowplaying", f"{prefix}.whatitdo"])
    async def currently_playing(self, ctx):
        if not await self.bot.has_perm(ctx, dm=False): return
        # TODO: Improve "now playing" appearance
        vc = await self.get_connected_vc(ctx)
        if not vc:
            await ctx.send("im not in a VC YOU IDIOTTT AHAAAAAAA (remind me to add more replies to this)")
            return

        time = vc.current_time()
        if not time:
            await ctx.send("Not playing anything!")
        else:
            await ctx.send(time)

    @commands.command(aliases=[f"{prefix}.playlist"])
    async def user_playlist(self, ctx):
        # User playlists allow users to continue what they were listening to before.
        # TODO: Allow users to save playlists.
        pass

    # === Help functions ===
    @commands.command("vc.help")
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
        
        **Examples:**
        Resumes playing the current video.
        `c.vc.play`
        Adds this video to the end of the current playlist.
        `c.vc.p https://youtu.be/J7sU9uB8XtU`
        Search YouTube.
        `c.vc.p duck asks for bread`
        Search YouTube, and take the 5th result. Maximum for res is 50.
        `c.vc.p pigeon cooing sounds res=5`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.seek.help"])
    async def seek_to_position_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
        Go to a point in the song.

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

    @commands.command(aliases=[f"{prefix}.skip.help", f"{prefix}.s.help"])
    async def skip_song_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        description = """
        Mercilessly ends the current song without mercy.

        **Examples:**
        skipping past "all the single furries"
        `c.vc.skip`
        erasing "carrot cake asmr'
        `c.vc.s`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.q.help", f"{prefix}.queue.help"])
    async def show_queue_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        # TODO: Document queue
        return
        description = """
            Mercilessly ends the current song without mercy.

            **Examples:**
            skipping past "all the single furries"
            `c.vc.skip`
            erasing "carrot cake asmr'
            `c.vc.s`
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

    # Functions
    async def join_voice_channel(self, ctx):
        vc = ctx.author.voice.channel
        message_channel = ctx.message.channel
        if not vc:
            await ctx.send(choice(self.not_in_vc_replies))
            return None

        try:
            voice_client = await vc.connect()
        except (discord.errors.ClientException, asyncio.TimeoutError):
            await ctx.send("Failed to connect, for some reason.")
            return None

        await ctx.guild.change_voice_state(channel=vc)
        self.connections[ctx.guild.id] = ServerAudio(voice_client, message_channel, self.bot.loop, self.yt_api_key)
        return self.connections[ctx.guild.id]

    async def leave_voice_channel(self, ctx):
        vc = await self.get_connected_vc(ctx)
        if not vc:
            return False

        vc.cleanup()
        await ctx.guild.change_voice_state(channel=None)
        del self.connections[ctx.guild.id]
        return True

    async def get_connected_vc(self, ctx, join_if_not_in=False):
        """Gets the VC that this"""
        try:
            vc = self.connections[ctx.guild.id]
        except KeyError:
            if join_if_not_in:
                vc = await self.join_voice_channel(ctx)
            else:
                return None

        return vc


class Player(discord.FFmpegPCMAudio):
    def __init__(self, source, duration, *, seek=0):
        self.current_time = seek  # Time in seconds
        #pipes = subprocess.Popen(rf"""ffprobe -i {source} -show_entries format=duration -v quiet -of csv="p=0" """, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        #self.length_of_song = float(pipes.stdout.read())
        self.length_of_song = duration

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
    url: str
    title: str
    author: str
    description: str
    duration: int
    # TODO: Add who added song

    @staticmethod
    def get_youtube_playlist_item_data(youtube_api_key, video_id):
        """Returns the data required to fill a PlaylistItem."""
        data = {}
        params = {"part": "snippet,contentDetails", "key": youtube_api_key, "id": video_id}
        r = requests.get("https://www.googleapis.com/youtube/v3/videos", params=params).json()["items"]
        if len(r) == 0:
            raise InvalidVideoId
        r = r[0]

        data["url"] = "https://youtu.be/" + r["id"]
        data["title"] = r["snippet"]["title"]
        data["author"] = r["snippet"]["channelTitle"]
        data["description"] = r["snippet"]["description"]

        dur_text = r["contentDetails"]["duration"]  # Yt provides a weird format.
        match = re.search(r"T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", dur_text)
        dur = 0
        if match.group(1):
            dur += int(match.group(1)) * 3600
        if match.group(2):
            dur += int(match.group(2)) * 60
        if match.group(3):
            dur += int(match.group(3))
        data["duration"] = dur

        # Potentially useful data.
        #r["snippet"]["thumbnails"]["default"]
        #r["statistics"]["viewCount"]
        #r["statistics"]["likeCount"]
        #r["statistics"]["dislikeCount"]
        #r["statistics"]["viewCount"]
        #r["topicDetails"]  # Has wikipedia links related to the videos??
        return data


# TODO: Make loop all work
# Requires FFMPEG
class ServerAudio:
    def __init__(self, voice_client, message_channel, async_loop, yt_api_key):
        self.vc = voice_client
        self.message_channel = message_channel  # The place notifications and messages are sent.
        # FIXME: The first song in the playlist tends to be skipped.
        #  Could be fixed by combining currently_playing and playlist, such that playlist[0] == currently_playing
        self.playlist = []  # List of PlaylistItem.
        self.currently_playing = None
        self.player = None
        self.download_progress = -1
        self.stop_download = False
        self.video_path = f"./attachments/{self.vc.guild.id}.mp4"
        self.async_loop = async_loop  # Used to run song_end. TODO: Make it so I don't have to do this.
        self.yt_api_key = yt_api_key
        self.song_ended = False

        self.loop = helpers.StateObject("off", "one", "all")
        asyncio.run_coroutine_threadsafe(self.check_if_song_ended_loop(), self.async_loop)

    async def check_if_song_ended_loop(self):
        while True:
            if self.song_ended:
                await self.song_end()
                self.song_ended = False
            await asyncio.sleep(1)

    async def add_song(self, url, title, author, description, duration):
        item = PlaylistItem(url, title, author, description, duration)
        self.playlist.append(item)
        if self.currently_playing is None:  # Only the song that was just added exists.
            await self.play()
        else:
            await self.message_channel.send(f"Added \"{item.title}\" by \"{item.author}\"")

    async def add_playlist_item(self, item: PlaylistItem):
        """Wrapper for add_song to allow for PlaylistItems"""
        await self.add_song(item.url, item.title, item.author, item.description, item.duration)

    async def play(self):
        """
        Play paused or queued audio.
        """
        # Song isn't queued.
        if self.player is None:
            res = await self.next_song()
            if res is not None:
                return res
            self.player = Player(self.video_path, self.currently_playing.duration)
            self.vc.play(self.player, after=lambda e: self.song_ended_event(e))
            return f"Playing: {self.currently_playing.title}"
        # Song was paused.
        else:
            self.vc.resume()
            return ":arrow_forward: **Resuming**"

    async def seek_song(self, seek):
        if not self.player:
            await self.message_channel("Not playing anything!")

        seek_in_seconds = helpers.SMPTE_to_seconds(seek)
        if not seek_in_seconds:
            await self.message_channel.send("Seek invalid!")
            return
        self.vc.pause()
        self.player = Player(self.video_path, self.currently_playing.duration, seek=seek_in_seconds)
        self.vc.play(self.player, after=lambda e: self.song_ended_event(e))

    def pause(self):
        self.vc.pause()

    async def next_song(self):
        """Gets the next song ready to be played."""
        # FIXME: it fails at going to the next song hehe
        self.vc.stop()
        if not self.playlist:
            return "No next song!"

        next_item = self.playlist.pop(0)
        await self.download_video(next_item)
        self.currently_playing = next_item

    async def download_video(self, item: PlaylistItem):
        # FIXME: If someone requests two songs in quick succession, both will be downloaded, first will be played, other ignored.
        try:
            YouTubeObj = pytube.YouTube(item.url)
        except pt_exceptions.RegexMatchError:
            print("Could not find url!")
            return
        except pt_exceptions.VideoPrivate:
            print("Video is private!")
            return

        # FIXME: Fix this to not download the highest quality video possible.
        stream = YouTubeObj.streams.filter(progressive=True).order_by("abr")[-1]
        size = stream.filesize
        amount_downloaded = 0

        path = f"./attachments/{self.vc.guild.id}.mp4"
        start_time = time()
        self.stop_download = False  # Removes any previous requests to stop the download.
        update_message = await self.message_channel.send(f":inbox_tray: Downloading: \"{item.title}\"...\n0%")
        with open(path, "wb") as f:
            stream = pytube.request.stream(stream.url)
            while amount_downloaded < size:
                if self.stop_download:
                    break
                chunk = next(stream, None)
                if chunk:
                    f.write(chunk)
                    amount_downloaded += len(chunk)
                else:
                    break
                now_time = time()
                if now_time - start_time >= 1:
                    self.download_progress = amount_downloaded / size
                    start_time = now_time
                    await update_message.edit(content=f":inbox_tray: Downloading: \"{item.title}\"...\n{self.download_progress*100:.1f}%")
                    await asyncio.sleep(0.1)  # Let the program send out a heartbeat.
        self.download_progress = -1
        await update_message.edit(content=f"Playing: \"{item.title}\"")
        await self.play()

    async def song_end(self):
        if self.loop.state == "all":  # FIXME: For some reason this shit doesn't work
            await self.add_playlist_item(self.currently_playing)

        if self.loop.state == "one":
            await self.seek_song(0)
        else:
            self.player = None  # Clear old player away.
        await self.play()  # Play the next song.

    def song_ended_event(self, e):
        self.song_ended = True

    def current_time(self):
        # current time
        if not self.player:
            return None
        current_time = helpers.seconds_to_SMPTE(self.player.current_time)
        length_of_song = helpers.seconds_to_SMPTE(self.player.length_of_song)
        return f"`{current_time} / {length_of_song}`"

    def cleanup(self):
        """Cleans up anything ongoing before the bot leaves."""
        self.stop_download = True
        self.vc.stop()
        try:
            os.remove(self.video_path)  # FIXME: for some reason this doesn't work. Need to find a way to free up the file
        except Exception as e:
            print("Error trying to remove file: ", e)

    def create_pages(self):
        """Creates a list of ServerAudio.Page, to pass to ReactiveMessageManager.create_reactive_message"""
        total_time = 0
        song_total = len(self.playlist)
        page_total = ceil(song_total / 10)
        loop_state = self.loop.state
        guild_name = self.message_channel.guild
        now_playing = self.currently_playing

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
        elif self.currently_playing:
            total_time += now_playing.duration
            p = self.Page([], 0, now_playing, guild_name, loop_state, 0, 0, total_time)
            return [p]
        else:
            return None

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
                duration = helpers.seconds_to_SMPTE(song.duration)
                description += f"\n`{position}.` [{song.title}]({song.url}) | `{duration}`\n"
            footer_text = f"Page {page_data.page_num + 1}/{page_data.page_total}"
            description += f"**{page_data.song_total} songs in queue | {helpers.seconds_to_SMPTE(page_data.total_time)} total length**"
        else:
            description += "\nNothing! :)\n"
            footer_text = f"Page 0/0"

        # TODO: Add loop state to footer
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


# Exceptions
class InvalidVideoId(Exception):
    pass


def setup(bot):
    bot.core_help_text["modules"] += ["vc"]
    bot.add_cog(VoiceChannels(bot))
