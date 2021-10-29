from discord.ext import commands
from random import choice
import numpy as np  # Very surprised this isn't a built in module.
import re
from asyncio import sleep
import helpers
from HonkBonk import MyBot
import discord
from typing import Tuple


class BadGames(commands.Cog):
    prefix = "game"

    def __init__(self, bot: MyBot):
        self.bot = bot
        # Storing all of the data for this in memory, as this stuff shouldn't need to be stored long term.
        self.ongoing_games = {}

        self.help_text = {
            "games": ["game.ttt", "game.c4"],
        }

        self.bot.Scheduler.add(self.check_game_alive, 10)

    async def check_game_alive(self, time_now):
        d_copy = self.ongoing_games.copy()  # Python explodes if you remove an entry in a loop.
        for message_id, game in d_copy.items():
            if game.ended:
                self.ongoing_games.pop(message_id)
            elif game.end_time < time_now:
                await game.time_out()
                self.ongoing_games.pop(message_id)

    def get_players(self, ctx) -> Tuple[discord.Member, discord.Member]:
        men = ctx.message.mentions
        if not men:
            raise ValueError

        p2 = men[0]
        p1 = ctx.author
        if ctx.author.id == self.bot.owner_id:
            if len(men) > 1:
                p1 = men[1]
        return p1, p2

    @commands.command(name=f"{prefix}.ttt")
    async def start_ttt(self, ctx: commands.Context):
        if not await self.bot.has_perm(ctx): return
        try:
            p1, p2 = self.get_players(ctx)
        except ValueError:
            await ctx.send("Mention a user to challenge!")
            return

        g = TTT(p1, p2, ctx.message.channel, self.bot)
        await g.start()
        self.ongoing_games[g.message.id] = g

    @commands.command(name=f"{prefix}.c4")
    async def start_c4(self, ctx: commands.Context):
        if not await self.bot.has_perm(ctx): return
        try:
            p1, p2 = self.get_players(ctx)
        except ValueError:
            await ctx.send("Mention a user to challenge!")
            return

        g = C4(p1, p2, ctx.message.channel, self.bot)
        await g.start()
        self.ongoing_games[g.message.id] = g

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.id not in self.ongoing_games:
            return

        game = self.ongoing_games[reaction.message.id]
        if user.id != game.target.id:
            return

        if game.started:
            return

        if str(reaction.emoji) == "❌":
            await game.declined()
            self.ongoing_games.pop(reaction.message.id)
        elif str(reaction.emoji) == "✅":
            await game.accepted()

    @commands.Cog.listener()
    async def on_message(self, message):
        og = self.ongoing_games.copy()
        for _, g in og.items():
            await g.on_message(message)

    @commands.command(name=f"{prefix}.help")
    async def vc_help(self, ctx: commands.Context):
        if not await self.bot.has_perm(ctx, dm=True): return
        desc = "games."
        await ctx.send(embed=self.bot.create_help(self.help_text, help_description=desc))

    @commands.command(aliases=[f"{prefix}.ttt.help"])
    async def start_ttt_help(self, ctx: commands.Context):
        description = """
        TICTACTOE.
        
        **Examples:**
        TICTACTOE.
        `c.game.ttt @HonkBonk`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)

    @commands.command(aliases=[f"{prefix}.c4.help"])
    async def start_c4_help(self, ctx: commands.Context):
        description = """
        conne foure.

        **Examples:**
        chaleng y bonnie mate tah batel foura botleo scrumpy.
        `c.game.c4 @pidge`
        """
        embed = helpers.help_command_embed(self.bot, description)
        await ctx.send(embed=embed)


class TTT:
    def __init__(self, p1: discord.Member, p2: discord.Member, channel: discord.TextChannel, bot: MyBot):
        self.initiator = p1
        self.target = p2

        if p2.id == bot.user.id:
            first_player = p2
            ps = [p1]
        else:
            ps = [p1, p2]
            first_player = choice(ps)
            ps.remove(first_player)

        self.players = {"x": first_player, "o": ps[0]}
        self.current_player = "x"
        self.message = None  # Message the game runs in.
        self.bot = bot
        self.channel = channel

        self.started = False
        self.end_time = helpers.time_from_now(minutes=1)
        self.ended = False

        self.board_state = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        self.turns = 0

    def generate_message(self, win=False, draw=False) -> str:
        message = ""
        message += "Type in the (x y) coordinates of the square to play!\n"
        message += f"x = {self.players['x']} | o = {self.players['o']}\n\n"

        if draw:
            message += f"__**Draw! Who could have seen that coming? :(**__\n"
        elif not win:
            message += f"**{self.players[self.current_player].mention}'s turn**\n"
        else:
            message += f"**__{self.players[self.current_player].display_name} wins!__**\n"

        # Create play board.
        board = "`  1 2 3 `"
        for y in range(3):
            board += "\n`" + str(y+1)
            for x in range(3):
                state = self.board_state[y][x]
                if state == -1:
                    c = "o"
                elif state == -2:
                    c = "O"
                elif state == 1:
                    c = "x"
                elif state == 2:
                    c = "X"
                else:
                    c = "_"

                board += "|" + c
            board += "|`"

        message += board + "\n"
        message += "ᵖʳᵒᵖᵉʳᵗʸ ᵒᶠ ᶜʷᵘⁿʰⁱ ᵈᵘᵏ\n"
        return message

    def check_position(self, _x: int, _y: int) -> bool:
        """Check if the given position is currently a win."""
        position_state = self.board_state[_y][_x]
        if position_state != 0:
            shift_amount = [1-_x, 1-_y]  # How the board needs to be shifted in order to center around this position.
            centered_board = np.roll(self.board_state, shift_amount, axis=(1, 0))  # Move left, then move down.

            for xy in range(4):  # We only need to check 4 of the 8 neighbours to verify a line.
                y, x = divmod(xy, 3)  # Get the x/y of the neighbour.
                cell_state = centered_board[y][x]
                if cell_state == position_state:
                    # Get opposite square.
                    x2 = ((x-1)*-1)+1
                    y2 = ((y-1)*-1)+1
                    if centered_board[y2][x2] == position_state:
                        # Set the winning values to -2 or 2
                        centered_board[1][1] *= 2  # Middle.
                        centered_board[y][x] *= 2
                        centered_board[y2][x2] *= 2
                        reverse_shift = [x * -1 for x in shift_amount]
                        self.board_state = np.roll(centered_board, reverse_shift, axis=(1, 0))
                        return True
        return False

    async def start(self):
        if self.target.id == self.bot.user.id:
            m = await self.channel.send("**__You dare challenge I?__**")
            await sleep(2)
            await m.edit(content=">:)")
            await sleep(1)
            await m.edit(content=self.generate_message())
            await sleep(2)
            self.board_state = [[2, 2, 2], [2, 2, 2], [2, 2, 2]]
            await m.edit(content=self.generate_message(win=True))
            await sleep(0.5)
            end_response = choice(["Close one! GGs!", "learned your lesson", "you now understand.", ":)", "<3"])
            await self.channel.send(end_response)
            self.started = True
            self.ended = True
            self.message = m
            return

        m = await self.channel.send(f"Do you accept the challenge, {self.target.display_name}?")
        self.message = m
        await m.add_reaction("✅")
        await m.add_reaction("❌")

    def refresh(self):
        """Refreshes the timer when something happens, so the game doesn't time out."""
        self.end_time = helpers.time_from_now(minutes=1)

    async def accepted(self):
        self.started = True
        m = self.message
        try:
            await m.clear_reactions()
        except Exception:
            pass
        await m.edit(content=self.generate_message())
        self.refresh()

    async def declined(self):
        await self.message.channel.send(f"Challenge declined by {self.target.display_name}")

    async def time_out(self):
        self.ended = True
        try:
            await self.message.channel.send(f"Game between {self.initiator.display_name} and {self.target.display_name} timed out.")
        except Exception:
            pass

    async def play(self, x, y):
        if self.ended:
            return
        x -= 1
        y -= 1
        cell_val = 1 if self.current_player == "x" else -1

        try:
            board_cell = self.board_state[y][x]
            if board_cell != 0:
                if self.players[self.current_player].id != self.bot.owner_id:
                    return False
        except Exception:
            return False

        self.board_state[y][x] = cell_val
        win = self.check_position(x, y)
        if not win:
            self.current_player = "x" if self.current_player == "o" else "o"
        else:
            self.ended = True

        self.turns += 1
        if self.turns == 9 and not win:
            await self.message.edit(content=self.generate_message(draw=True))
            self.ended = True
        else:
            await self.message.edit(content=self.generate_message(win=win))
        self.refresh()

        return True

    async def on_message(self, message):
        if message.author == self.players[self.current_player]:
            m = message.content
            mat = re.match(r"(\d)[\s,.]?(\d)", m)
            if mat:
                played = await self.play(int(mat.group(1)), int(mat.group(2)))
                if played:
                    try:
                        await message.delete()
                    except Exception:
                        pass


class C4:
    # A list of lines that connections can be made along.
    lines = (
        ((-1, -1), (1, 1)),
        ((-1, 0), (1, 0)),
        ((-1, 1), (1, -1)),
        ((0, -1), (0, 1))
    )

    def __init__(self, p1: discord.Member, p2: discord.Member, channel: discord.TextChannel, bot: MyBot):
        self.initiator = p1
        self.target = p2

        if p2.id == bot.user.id:
            first_player = p2
            ps = [p1]
        else:
            ps = [p1, p2]
            first_player = choice(ps)
            ps.remove(first_player)

        self.players = {"x": first_player, "o": ps[0]}
        self.current_player = "x"
        self.message = None  # Message the game runs in.
        self.bot = bot
        self.channel = channel

        self.started = False
        self.end_time = helpers.time_from_now(minutes=1)
        self.ended = False

        self.board_state = np.zeros((6, 7))
        self.turns = 0

    def check_position(self, _x: int, _y: int) -> bool:
        """Check the given x,y position on the board to see if it results in a victory."""
        position_state = self.board_state[_y][_x]
        if position_state != 0:
            for line in self.lines:
                line_values = [[_x, _y]]  # Cells connected on this line that share this value.
                for direction in line:
                    check_x = _x
                    check_y = _y
                    while True:
                        check_x += direction[0]
                        check_y += direction[1]
                        try:
                            dir_state = self.board_state[check_y][check_x]
                            if dir_state == position_state:
                                line_values.append([check_x, check_y])
                            else:
                                break
                        except IndexError:
                            break

                # win
                if len(line_values) >= 4:
                    for coord in line_values:
                        self.board_state[coord[1]][coord[0]] *= 2
                    return True
        return False

    def generate_message(self, state="") -> str:
        """Creates the board."""
        message = "Type in the column to put your piece in!\n"
        message += f"x = {self.players['x']} | o = {self.players['o']}\n\n"

        if state == "":
            message += f"{self.players[self.current_player].mention}'s turn\n"
        elif state == "win":
            message += f"**__{self.players[self.current_player].display_name} wins!__**\n"

        # Create play board.
        board = "` 1 2 3 4 5 6 7 `"
        for y in range(6):
            board += "\n`"
            for x in range(7):
                state = self.board_state[y][x]
                if state == -1:
                    c = "o"
                elif state == -2:
                    c = "O"
                elif state == 1:
                    c = "x"
                elif state == 2:
                    c = "X"
                else:
                    c = "_"

                board += "|" + c
            board += "|`"

        message += board + "\n"

        return message

    async def start(self):
        m = await self.channel.send(f"Do you accept the challenge, {self.target.display_name}?")
        self.message = m
        await m.add_reaction("✅")
        await m.add_reaction("❌")

    async def accepted(self):
        self.started = True
        m = self.message
        try:
            await m.clear_reactions()
        except Exception:
            pass
        await m.edit(content=self.generate_message())
        self.refresh()

    async def declined(self):
        await self.message.channel.send(f"Challenge declined by {self.target.display_name}")

    async def time_out(self):
        self.ended = True
        try:
            await self.message.channel.send(f"Game between {self.initiator.display_name} and {self.target.display_name} timed out.")
        except Exception:
            pass

    def refresh(self):
        """Refreshes the timer when something happens, so the game doesn't time out."""
        self.end_time = helpers.time_from_now(minutes=1)

    async def play(self, x):
        if self.ended:
            return
        x -= 1
        if x < 0 or x >= len(self.board_state[0]):
            return

        cell_val = 1 if self.current_player == "x" else -1

        y = None
        for i in range(len(self.board_state)-1, 0-1, -1):  # From bottom to top.
            board_cell = self.board_state[i][x]
            if board_cell == 0:  # We've hit a cell that is empty.
                y = i
                break

        if y is None:
            # No empty spaces
            return

        self.board_state[y][x] = cell_val
        win = "win" if self.check_position(x, y) else ""
        if not win:
            self.current_player = "x" if self.current_player == "o" else "o"
        else:
            self.ended = True

        await self.message.edit(content=self.generate_message(state=win))
        self.refresh()

        return True

    async def on_message(self, message):
        if message.author == self.players[self.current_player]:
            m = message.content
            mat = re.match(r"(\d)", m)
            if mat:
                played = await self.play(int(mat.group(1)))
                if played:
                    try:
                        await message.delete()
                    except Exception:
                        pass


def setup(bot):
    bot.core_help_text["modules"] += ["game"]
    bot.add_cog(BadGames(bot))
