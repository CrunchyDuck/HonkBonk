import discord
from discord.ext import commands
from asyncio import TimeoutError
from dotenv import load_dotenv
from os import getenv
from googleapiclient.discovery import build
import pytube as pt
from pytube import exceptions, extract
import json
from traceback import print_exc
import re
from collections import defaultdict
import requests
from datetime import datetime


# TODO: Allow HB to play music from youtube, like bots such as Rythm. [in progress]
# TODO: Navigate song based on YouTube chapters. Can be pulled from description.
# IDEA: Give HB a bunch of voice clips he's capable of remotely playing, so I can harass people at range.
class VoiceChannels(commands.Cog, name="voice_channels"):
    prefix = "vc"

    def __init__(self, bot):
        self.bot = bot
        self.init_db(self.bot.cursor)
        self.bot.Scheduler.add(self.sleep_timer_up, 60)

        self.help_text = {
            "General": ["vc.sleep", "vc.guitar"],
            "AAAAAdmins": [f"{self.prefix}.{command}" for command in ["join", "leave"]],
        }

        self.api_key = getenv("YT_API_KEY")
        #self.yt = build("youtube", "v3", developerKey=self.api_key)

        self.vcs = {}  # serverid: vc object
        self.playlist = defaultdict(list)  # A dictionary of server:list for things to play.

        self.search_settings = {0: {}}  # List of settings for searching within a server. 0=default

    @commands.command(name=f"{prefix}.join")
    async def join_vc_cmd(self, ctx):
        await self.join_voice_channel(ctx, True, True)

    @commands.command(name=f"{prefix}.leave")
    async def leave_voice_channel(self, ctx):
        """Leave the voice channel the bot is in, within this server."""
        if not await self.bot.has_perm(ctx, admin=True): return
        await ctx.guild.change_voice_state(channel=None, self_deaf=True, self_mute=True)
        self.vcs[ctx.guild.id] = None
        return

    @commands.command(name=f"{prefix}.guitar")
    async def play_pretty_guitar(self, ctx):
        if not await self.bot.has_perm(ctx, bot_owner=True): return
        if ctx.guild.id not in self.vcs:
            vc = await self.join_voice_channel(ctx, deaf=False, mute=False)
            if not vc:
                print(":(")
                return
        else:
            vc = self.vcs[ctx.guild.id]

        audiosource = "./attachments/pigid.mp3"
        vc.queue(audiosource, "System")


    @commands.command(name=f"{prefix}.ytest")
    async def yttest(self, ctx):
        if not await self.bot.has_perm(ctx, bot_owner=True): return
        msg = ctx.message.content
        vid = self.ignore_error(msg, extract.video_id)
        playlist = self.ignore_error(msg, extract.playlist_id)
        search_term = ctx.message.content[10:]

        try:
            if vid:
                self.playlist[ctx.guild.id].append(vid)
            elif playlist:
                await ctx.send("Not implemented yet >.<")
                return
            elif search_term:
                await ctx.send("w-wait till it's done~~")
                return
        except:
            print_exc()
            await ctx.send("Whoopsie doopsie! I've done a fucky wucky >//< yell at dukki~~")
            return

        self.vcs[ctx.guild.id] = await self.join_voice_channel(ctx, deaf=False, mute=False)

    @commands.command(name=f"{prefix}.play")
    async def play_audio(self, ctx):
        if not await self.bot.has_perm(ctx, bot_owner=True): return
        if ctx.guild.id not in self.vcs:
            await ctx.send("Not in a VC!")
            return

        audio = self.vcs[ctx.guild.id]
        audio.play()

    @commands.command(name=f"{prefix}.next")
    async def play_next(self, ctx):
        if not await self.bot.has_perm(ctx, bot_owner=True): return
        if ctx.guild.id not in self.vcs:
            await ctx.send("Not in a VC!")
            return

        audio = self.vcs[ctx.guild.id]
        audio.next()

    @commands.command(name=f"{prefix}.list")
    async def show_playlist(self, ctx):
        if not await self.bot.has_perm(ctx, bot_owner=True): return
        if ctx.guild.id not in self.vcs:
            await ctx.send("I'm not in a VC!")
            return

        audio = self.vcs[ctx.guild.id]
        msg = f"{audio.audio_path}\n"
        for s in audio.playlist:
            msg += f"{s.path}\n"
        await ctx.send(msg)

    @commands.command(name=f"{prefix}.chapter")
    async def get_video_chapter(self, ctx):
        if not await self.bot.has_perm(ctx): return
        msg = ctx.message.content
        try:
            vid = extract.video_id(msg)
        except exceptions.RegexMatchError:
            await ctx.send("Provide a video URL to get chapters from!")
            return

        time = re.search(r"time[=\s:]((?:\d+:)?\d{1,2}:\d{2})(?:\s|$)", ctx.message.content)
        if time:
            time = time.group(1)
            if re.match(r"\d+:\d{2}:\d{2}", time):
                time = datetime.strptime(time, "%H:%M:%S")
            elif re.match(r"\d{1,2}:\d{2}", time):
                time = datetime.strptime(time, "%M:%S")
        else:
            time = None

        params = {"part": "snippet", "id": vid, "key": self.api_key}
        description = requests.get("https://www.googleapis.com/youtube/v3/videos", params=params).json()["items"][0]["snippet"]["description"]

        first_timestamp = re.search(r"[^\n]*?00:00", description)
        if not first_timestamp:
            await ctx.send("Cannot find timestamps.")
            return

        description = description[first_timestamp.start(0):]
        return_val = ""
        for m in re.finditer(r"[^\n]*?([^\s]*(?:\d+:)?\d{1,2}:\d{2}[^\s]*)[^\n]*", description):
            if time:
                chapter_name = m.group(0).replace(m.group(1), "")
                chapter_timestamp = re.search(r"((?:\d+:)?\d{1,2}:\d{2})", m.group(1)).group(1)

                if re.match(r"\d+:\d{2}:\d{2}", chapter_timestamp):
                    chapter_time = datetime.strptime(chapter_timestamp, "%H:%M:%S")
                elif re.match(r"\d{1,2}:\d{2}", chapter_timestamp):
                    chapter_time = datetime.strptime(chapter_timestamp, "%M:%S")

                if chapter_time > time:
                    # Current chapter found
                    break
                else:
                    return_val = f"{chapter_name} ({chapter_timestamp})"

            else:
                # Return all chapters
                return_val += m.group(0) + "\n"

        await ctx.send(return_val)

    @commands.command(name=f"{prefix}.chapter.help")
    async def get_video_chapter_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Get a chapter from a timestamp in a video!

        Arguments:
            video: The url of the video.
            (optional) time: The timestamp, provided something like 0:00. Otherwise, display all chapters.

        Examples:
            c.vc.chapter <https://www.youtube.com/watch?v=P196hEuA_Xc> time=11:05
            c.vc.chapter v=2JsYHpiH2xs time 1:05:39```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)


    @staticmethod
    def ignore_error(val, method, default=None):
        """Lets me make my variable assignment one line long."""
        try:
            return method(val)
        except:
            return default

    def youtubetest(self):
        s = self.yt.search().list(
            part="snippet", q="furry"
        ).execute()
        print(json.dumps(s, indent=2))





    @commands.command(name=f"{prefix}.help")
    async def vc_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        # docstring = """
        # ```c.vc.join - Join your channel
        # c.vc.leave - Leave currently joined channel```
        # """
        # docstring = self.bot.remove_indentation(docstring)
        # await ctx.send(docstring)
        await ctx.send(embed=self.bot.create_help(self.help_text))

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

    @commands.command(name="sleep.help")
    async def sleep_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
                ```Allows the user to specify a time, after which they will be automatically removed from their current VC.
                Admins can mention a user to set a timer for them.

                Arguments:
                    time: The amount of time to wait before removing a user, in minutes. Defaults to 30 minutes.
                Examples:
                    c.sleep 
                    c.sleep time=45 @pip```
                """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="sleep")
    async def sleep_timer(self, ctx):
        if not await self.bot.has_perm(ctx): return False
        """
        Allows the user to specify a time, after which they will be automatically removed from their current VC.
        Admins can mention a user to set a timer for them.

        Arguments:
            time: The amount of time to wait before removing a user, in minutes. Defaults to 30 minutes.
        Examples:
            c.sleep
            c.sleep time=45
        """
        message = ctx.message
        content = message.content
        time = float(self.bot.get_variable(content, "time", type="float", default=30))
        user = self.bot.admin_override(ctx)

        # Checks if user is in a VC.
        voice = user.voice
        if voice:
            channel = voice.channel
        else:
            if user == ctx.author:
                await ctx.send("Join a voice channel before using this command.")
                return
            else:
                await ctx.send("The mentioned user must be in a voice channel.")
                return

        # Check if there's already an entry in the database for this user
        self.bot.cursor.execute(
            f"SELECT rowid, * FROM sleep_timer WHERE"
            f" user_id={user.id} AND server={ctx.guild.id}")
        result = self.bot.cursor.fetchone()

        if time > 0:
            time = (max(min(1440, time), 0.016)) / 60  # Limit to 1 day or 1 second. Also converts from the given minutes to hours.
            end_time = self.bot.time_from_now(hours=time)
            time_string = self.bot.time_to_string(hours=time)

            if result:  # Update existing entry.
                self.bot.cursor.execute(f"UPDATE sleep_timer SET end_time={end_time} WHERE rowid={result[0]}")
            else:  # Create entry.
                self.bot.cursor.execute(
                    f"INSERT INTO sleep_timer VALUES({ctx.guild.id}, {user.id}, {end_time})")
            self.bot.cursor.execute("commit")

            await ctx.send(f"{user.name} will automatically be removed from VC in {time_string}.")
        else:
            await ctx.send("Provided time must be above 0.")
            return

        try:
            self.bot.cursor.execute("commit")
        except:
            pass

    # Timed function
    async def sleep_timer_up(self, time_now):
        self.bot.cursor.execute("SELECT rowid, * FROM sleep_timer ORDER BY end_time ASC")
        targets = self.bot.cursor.fetchall()
        for target in targets:
            if time_now > target[3]:
                rowid = target[0]
                server = self.bot.get_guild(target[1])
                member = server.get_member(target[2])
                channel = None

                if member is None:
                    # Member could not be found
                    print("member not found.")
                try:
                    await member.move_to(channel, reason="Sleep timer ran out.")
                    cnl = self.bot.get_channel(709702365896507475) # VC text channel.
                    await cnl.send(f"Removed {member.name} from voice chat. Sleep tight :sleeping:")

                except discord.errors.Forbidden:
                    # Don't have the permissions.
                    pass
                except discord.errors.HTTPException:
                    # Failed.
                    pass
                self.bot.cursor.execute(f"DELETE FROM sleep_timer WHERE rowid={rowid}")
                self.bot.cursor.execute("commit")
            else:
                break

    async def join_voice_channel(self, ctx, deaf=False, mute=False):
        """Join the VC channel the user is currently in, or that they have mentioned."""
        voice = ctx.author.voice
        cnl_variable = self.bot.get_variable(ctx.message.content, "cnl", "int")

        if voice and voice.channel:
            channel = voice.channel
        elif cnl_variable:
            channel = voice.channel
        else:
            await ctx.send("You're not in a voice channel, orokana baaaaaka")
            return None

        vc_conn = None
        try:
            vc_conn = await channel.connect()
        except TimeoutError:
            pass
        except discord.ClientException:
            pass  # I don't know how to handle this yet.
        except discord.opus.OpusNotLoaded:
            print("opus not loaded some how??")

        await ctx.guild.change_voice_state(channel=channel, self_deaf=deaf, self_mute=mute)
        if vc_conn:
            self.vcs[ctx.guild.id] = ServerAudio(vc_conn, ctx.guild.id)
            return self.vcs[ctx.guild.id]

    def init_db(self, cursor):
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS sleep_timer ("  # An entry is created for each change that is detected.
            "server INTEGER,"  # ID of the server
            "user_id INTEGER,"  # ID of the user
            "end_time INTEGER"  # The time the user should be removed from the VC.
            ")")
        cursor.execute("commit")


class ServerAudio():
    def __init__(self, vc, server_id):
        self.server_id = server_id
        self.vc = vc
        self.playlist = []  # A list of DiscordPlaylist items
        self.current_audio = None
        self.audio_path = None

    def next(self, error=None):
        # Remove audio_path from PC

        # Get next item in playlist
        self.current_audio, self.audio_path = self.playlist.pop().get_audio()
        self.play()

    def play(self):
        if self.current_audio:
            self.vc.play(self.current_audio, after=self.next)
        elif self.playlist:
            self.next()

    def pause(self):
        self.vc.pause(self.current_audio)

    def queue(self, path, source):
        self.playlist.append(self.DiscordPlaylist(path, source))

    class DiscordPlaylist():
        def __init__(self, path, source):
            self.path = path
            self.source = source  # "YouTube" or "System"

        def get_audio(self):
            """Returns an audio source for discord to play, and the path on the PC"""
            if self.source == "System":
                return discord.FFmpegPCMAudio(executable="C:\\ffmpeg\\bin\\ffmpeg.exe", source=self.path), self.path


def setup(bot):
    bot.core_help_text["modules"] += ["vc"]
    bot.add_cog(VoiceChannels(bot))


def teardown(bot):
    bot.core_help_text["modules"].remove("vc")
    bot.remove_cog(VoiceChannels(bot))