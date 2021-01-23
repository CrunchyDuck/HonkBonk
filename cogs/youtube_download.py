import discord
import os
import re
import requests
import subprocess
import traceback
from datetime import datetime, timedelta
from discord.ext import commands
from os.path import isfile
from pathlib import Path
from pytube import YouTube, Playlist
from pytube.exceptions import RegexMatchError, VideoPrivate
from urllib.error import HTTPError


class YTDownload(commands.Cog, name="youtube_download"):
    """Downloads a song from YouTube and sends it in the server as audio."""
    prefix = "yt"
    re_yt_link = re.compile(r"(https?://)?(www\.youtube\.com|youtu\.?be)/[^\s]+")

    def __init__(self, bot):
        self.bot = bot
        self.cur = bot.cursor
        self.last_used = datetime.now()
        self.COOLDOWN = timedelta(seconds=30)
        self.EIGHT_MB = 1048576 * 8

    @commands.command(name=f"{prefix}.download")
    async def download_request(self, ctx):
        time_since_last_use = datetime.now() - self.last_used
        # if time_since_last_use < self.COOLDOWN:
        #	await ctx.send(f"Please wait for {time_since_last_use} seconds")

        if not await self.bot.has_perm(ctx): return

        message = ctx.message
        url = re.search(self.re_yt_link, message.content)
        if not url:
            await ctx.send(
                "URL seems to be invalid. But I'm also using a matching pattern I found on StackOverflow, so ping me if this is wrong.")
            return

        file_dir = await self.download(ctx, url.group(0), ".\\attachments")  # , convert_to="mp3")
        if file_dir:
            try:
                await ctx.send(file=discord.File(file_dir))
            except Exception:
                await ctx.send("whoops something went wrong")
            finally:
                os.remove(file_dir)

    async def download(self, ctx, url, dir, recursed=False, convert_to="mp3"):
        """

        :param ctx:
        :param url:
        :param dir:
        :param recursed:
        :param convert_to:
        :return: Directory to file
        """
        # Load youtube object
        try:
            YouTubeObj = YouTube(url)
        except RegexMatchError:
            await ctx.send(f"Video <{url}> is unavailable.")
            return
        except VideoPrivate:
            await ctx.send(f"video's facking private innit m8 <{url}>")
            return
        except Exception as e:
            await ctx.send(f"Unknown error fetching <{url}>")
            traceback.print_exc()
            return

        # Check size of file
        stream = YouTubeObj.streams.filter(only_audio=True, progressive=False).order_by("abr")[1]
        file_size = stream.filesize
        if file_size > self.EIGHT_MB:
            await ctx.send(f"Video too fat for discord :(")

        # Download youtube video/audio
        try:
            created_file = str(Path(stream.download(output_path=dir, skip_existing=False)))
            if convert_to:
                self.convert(created_file, convert_to)
                p = Path(created_file)
                created_file = f"{p.parent}\\{p.stem}.{convert_to}"

            return created_file


        except HTTPError:
            if recursed:
                await ctx.send(f"Could not download <{url}> (HTTPError)")
                return
            await ctx.send("HTTP Error, retrying...")
            download(url, recursed=True)
            return
        except Exception as e:
            await ctx.send(f"Unknown error on: <{url}>")
            traceback.print_exc()
            return

    def convert(self, input_file, convert_to):
        valid_formats = ["mp3", "wav",
                         "ogg"]  # No way to dynamically check what FFmpeg can encode, so I'm limiting the formats myself.
        if convert_to not in valid_formats:
            return

        p = Path(input_file)
        suff = p.suffix
        file = p.stem
        dir = p.parent

        # No point converting if it's the same file format.
        if suff == f".{convert_to}":
            return

        # FFmpeg explodes if you try to output to an existing file, so I will disallow this.
        output_file = f"{dir}/{file}.{convert_to}"
        if isfile(output_file):
            print(f"File \"{file}.{convert_to}\" already exists, skipping conversion...")
            os.remove(input_file)
            return

        print(input_file)
        command = f'ffmpeg -i "{input_file}" "{output_file}"'
        subprocess.run(command, stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)
        os.remove(input_file)


def setup(bot):
    bot.add_cog(YTDownload(bot))
