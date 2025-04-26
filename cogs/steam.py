import requests
from discord.ext import commands
from HonkBonk import MyBot
import helpers
from dataclasses import dataclass, field
from math import ceil
import discord
import re
from typing import List


# TODO: Get 64 user id from vanity url
class SteamGames(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.api_key = bot.settings["STEAM_API_KEY"]
        self.default_acc = bot.settings["STEAM_ACC_ID"]
        self.bot.event(self.on_command_error)
        self.bot.event(self.on_ready)

    async def on_command_error(self, ctx, error):
        """Triggered when a prefix is found, but no command is."""
        if isinstance(error, commands.CommandNotFound):  # Unrecognized command
            return
        else:
            raise error

    async def on_ready(self):
        print(f"{self.bot.user} has connected to Discord.")
    
    def owned_games(self, key: str, steamid: int) -> List['SteamGames.SteamGame']:
        """
        Gets a dictionary of all games owned by steamid.
        Parameters
        ----------
        key (str): The API key to access this with.
        steamid (str): steamID64 of the account you wish to check the games of.
        format (Optional(str)): Format to return data in. json, xml or vdf

        Returns
        -------
        game_names (list): A list containing the names of owned games.
        """
        url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
        params = {"key": key, "steamid": steamid, "format": "json", "include_appinfo": True}
        owned_games = requests.get(url, params=params)
        owned_games = owned_games.json()

        games = []
        for game in owned_games["response"]["games"]:
            games.append(SteamGames.SteamGame(game["name"], game["appid"]))
        games.sort(reverse=False, key=lambda g: g.name.lower())  # Sort alphabetically
        
        return games

    @staticmethod
    def steam_user_data(steamid: int) -> List[str]:
        url = f"https://steamcommunity.com/profiles/{steamid}"
        page = requests.get(url).text

        img = re.search(r"""<div class="playerAvatarAutoSizeInner">(.+?)</div>""", page, flags=re.DOTALL)
        img = re.search(r"""src="([^"]+)""", img.group(1)).group(1)

        name = re.search(r"""<span class="actual_persona_name">(.+)</span>""", page).group(1)

        return [name, img]

    @commands.command(name=f"owns")
    async def owns_game(self, ctx):
        matches = []
        content = helpers.remove_invoke(ctx.message.content)
        search_term, target = helpers.get_command_variable(content, "uid", default=self.default_acc)
        
        for game_name in self.owned_games(self.api_key, target):
            if search_term in game_name.name.lower():
                matches.append(game_name)
        if not matches:
            await ctx.send("Sad day. No finds.")
            return

        pages = self.GameListPage.create_from_SteamGame(matches, search_term, target)

        first_page = pages[0].display(pages[0])
        m = await ctx.channel.send(embed=first_page)
        await self.bot.ReactiveMessageManager.create_reactive_message(m, pages[0].display, pages, users=[ctx.author.id])

    @dataclass(order=True)
    class SteamGame:
        name: str
        appid: int = field(compare=False)
        url: str = field(compare=False)

        def __init__(self, name: str, appid: int):
            self.name = name
            self.appid = appid
            self.url = f"https://store.steampowered.com/app/{appid}"

    @dataclass
    class GameListPage:
        games: List['SteamGames.SteamGame']
        page_num: int

        search_term: str
        acc_id: int
        acc_name: str
        acc_img_url: str
        total_pages: int

        @staticmethod
        def create_from_SteamGame(games: List['SteamGames.SteamGame'], search_term, acc_id, page_size=20) -> List['SteamGames.GameListPage']:
            acc_name, acc_img_url = SteamGames.steam_user_data(acc_id)
            num_pages = ceil(len(games)/page_size)
            pages = []
            for i in range(num_pages):
                i_from = i * page_size
                i_to = (i + 1) * page_size
                names = games[i_from:i_to]
                p = SteamGames.GameListPage(names, i, search_term, acc_id, acc_name, acc_img_url, num_pages)
                pages.append(p)
            return pages

        @staticmethod
        def display(page: 'SteamGames.GameListPage') -> discord.Embed:
            e = helpers.default_embed()
            user_page = f"https://steamcommunity.com/profiles/{page.acc_id}"
            e.description = f"**\"{page.search_term}\" for [{page.acc_name}]({user_page})**\n\n"
            for game in page.games:
                e.description += f"[{game.name}]({game.url})\n"
            e.set_footer(text=f"{page.page_num+1}/{page.total_pages}")
            e.set_thumbnail(url=page.acc_img_url)
            return e

    @commands.command(aliases=[f"owns.help"])
    async def owns_game_help(self, ctx):
        pass
    

def setup(bot):
    bot.add_cog(SteamGames(bot))
