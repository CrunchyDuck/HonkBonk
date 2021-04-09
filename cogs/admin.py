import discord
import re
from discord.ext import commands
from random import shuffle
from random import random
import traceback

class Admin(commands.Cog, name="admin"):
    """Admin commands. Mostly just fun things for me to toy with, sometimes test, rarely useful."""
    def __init__(self, bot):
        self.bot = bot
        self.cur = bot.cursor
        self.r_only_emoji = re.compile(
            r"^((?:<:.*?:)(\d*)(?:>)|[\s])*$")  # This parses over a string and checks if it ONLY contains
        self.r_get_emoji = re.compile(r"(<:.*?:)(\d*)(>)")
        self.r_cdn = re.compile(
            r"(https://cdn.discordapp.com/attachments/.*?\.(gif|png|jpg))|(https://cdn.discordapp.com/emojis/)")  # The domain images and stuff are placed.
        self.r_cdn_filename = re.compile(r"([^/]*?(\.png|\.jpg|\.gif))")

        self.rc_dunno = self.bot.Chance({
            "No encuentro la wea": 100,
            "Not a clue": 100,
            "Haven't a scooby": 100,
            "a dinnae ken": 100,
            "dunno": 100
        })

        self.uwu_faces = self.bot.Chance({
            " ": 500,
            " UwU ": 15,
            " OwO ": 15,
            " >.< ": 10,
            " o-owo ": 10,
            " OWOWO ": 10,
            " >//< ": 10,
            " >> ": 10,
            " x3 ": 10,
            " :3 ": 10,
            " :c ": 5,
            " c: ": 5,
            " :J ": 2,
            " :v ": 1
        })

        self.magic_8_ball = self.bot.Chance({
            "It is certain": 100,
            "It is decidedly so.": 100,
            "Without a doubt.": 100,
            "Yes - definitely.": 100,
            "You may rely on it.": 100,
            "As I see it, yes": 100,
            "Most likely.": 100,
            "Outlook good.": 100,
            "Yes.": 100,
            "Signs point to yes.": 100,
            "Reply hazy, try again.": 100,
            "Ask again later.": 100,
            "Better not tell you now.": 100,
            "Cannot predict now.": 100,
            "Concentrate and ask again.": 100,
            "Don't count on it.": 100,
            "My reply is no.": 100,
            "My sources say no.": 100,
            "Outlook not so good.": 100,
            "Very doubtful.": 100,
            "nyes uwu": 100,
            "nyo òwó": 100,
            "m-maybe.... >//<": 100,
            "i don't knowo wight now >>": 100
        })

        self.bot.core_help_text["General"] += ["small", "timestamp", "id", "shuffle", "pat", "kick", "uptime", "pfp", "uwu", "8ball"]
        self.bot.core_help_text["Admins OwOnly"] += ["dm", "speak", "ignore", "ignore.none", "ignore.all"]

    @commands.command(name=f"timestamp")
    async def timestamp(self, ctx):
        """
        Get the timestamp of a provided Discord Snowflake.

        Example command:
            c.timestamp 411365470109958155
        """
        if not await self.bot.has_perm(ctx, admin=False, message_on_fail=False): return

        timestamps = re.search(r"c.timestamp ([ \d]+)", ctx.message.content)
        if not timestamps:
            await ctx.send("No snowflake found.")
            return

        message = ""
        for timestamp in timestamps.group(1).split(" "):
            m = int(timestamp.replace(" ", ""))
            print(m)
            message += self.bot.date_from_snowflake(m) + "\n"

        await ctx.send(message)

    @commands.command(name="echo")
    async def echo(self, ctx):
        """Repeat what it was given in Discord."""
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False): return
        await ctx.send(ctx.message.content)

    @commands.command(name="test")
    async def test(self, ctx):
        """Misc code I needed to test."""
        if not await self.bot.has_perm(ctx, bot_owner=True, message_on_fail=False): return
        one_day_seconds = 86400
        now = self.bot.time_now()
        time_through_day = now % one_day_seconds
        start_of_day = now - time_through_day
        message_time = start_of_day + (8 * 60 * 60) + (72 * 60 * 60)  # 8AM + 3 days
        print(message_time)

    @commands.command(name="print")
    async def print_message(self, ctx):
        """Similar to c.test, but specifically for printing values to the console."""
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False): return
        print(ctx.message.content)

    @commands.command(name="speak")
    async def speak(self, ctx):
        """
        Make the bot say something in a server. Works in the server it was called from.
        Arguments:
            channel_mention: A mention of the channel to send the message in.
            content: What to say.
        Example:
            c.speak #bots content="I have gained sapience."
        """
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False): return
        content = self.bot.get_variable(ctx.message.content, "content", type="str")

        channel = ctx.message.channel_mentions[0]
        await channel.send(content)

    @commands.command(name="small")
    async def make_superscript(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        msg = ctx.message.content
        if len(msg) < 8:
            await ctx.send("Can't superscript nothing :(")
            return
        msg = msg[7:]

        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-=()?"
        alphabet_superscript = "ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖqʳˢᵗᵘᵛʷˣʸᶻᴬᴮCᴰᴱFᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿSᵀᵁⱽᵂᵡᵞᶻ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ˀ"
        superscript = str.maketrans(alphabet, alphabet_superscript)

        await ctx.send(msg.translate(superscript))

    @commands.command(name="big")
    async def make_fullwidth(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        msg = ctx.message.content
        if len(msg) < 6:
            await ctx.send("Can't big nothing :(")
            return
        msg = msg[6:]

        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-=()? "
        alphabet_big = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ０１２３４５６７８９+－＝（）？　"
        superscript = str.maketrans(alphabet, alphabet_big)

        await ctx.send(msg.translate(superscript))

    @commands.command(name="uwu")
    async def make_uwu(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        msg = ctx.message.content
        if len(msg) < 6:
            await ctx.send("Youwu have to add a message in owdew to UwU-ify it >.<")
            return
        msg = msg[5:]

        pos = 0
        while pos < len(msg):
            letter = msg[pos]

            if letter in "rl":
                msg = msg[:pos] + "w" + msg[pos + 1:]
                letter = "w"
            elif letter in "RL":
                msg = msg[:pos] + "W" + msg[pos + 1:]
                letter = "W"
            elif letter == " ":
                emote_to_add = self.uwu_faces.get_value()
                msg = msg[:pos] + emote_to_add + msg[pos + 1:]
                pos += len(emote_to_add) - 1

            if msg[pos - 1] == " ":
                chance = random()
                if letter.isalpha() and chance > 0.93:
                    msg = msg[:pos] + f"{letter}-{letter}" + msg[pos + 1:]

            pos += 1

        await ctx.send(msg)

    @commands.command(name="8ball")
    async def magic_8_ball(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return

        reply = self.magic_8_ball.get_value()
        await ctx.send(reply)

    @commands.command(name="dm")
    async def dm_user(self, ctx):
        """
        DM a user. An excess of spaces should be placed between the user's ID and the content to send to them.
        Arguments:
            user: The user to send the ID to.
            content: What to send to them.
        Example:
            c.dm user=630930243464462346      you're really cool
        """
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False, dm=True): return
        target = await self.bot.fetch_user(self.bot.get_variable(ctx.message.content, "user", type="int"))
        # This relies on the fact that the start of the message should ALWAYS be a fixed size.
        # If it isn't, this will go wrong.
        content = ctx.message.content[30:]

        await target.send(content)

    @commands.command(name="ignore")
    async def ignore_id(self, ctx):
        """
        ```Ignores a channel, category, or user.
        You can mention a category by putting its id into this structure:
        <#id_of_category>

        Arguments:
            (Required) - Requires at least one
            id: The ID to add to the list. Only 1 ID can be provided this way.
            member: A mention of the member to ignore. Can be multiple.
            channel: A mention of the text, voice or category channel to ignore. Can be multiple.

            (Optional)
            stop: Stops ignoring the given IDs.
        Example:
            c.ignore  # Ignores this channel
            c.ignore @Pidge  # Ignores a user
            c.ignore #general #nsfw #announcements # Ignores multiple channels.
            c.ignore id=704361803953733694 stop  # Stops ignoring an ID, such as a category, or a channel.```
        """
        if not await self.bot.has_perm(ctx, admin=True, ignored_rooms=True, message_on_fail=True): return
        server = ctx.guild.id
        message = ctx.message
        id = int(self.bot.get_variable(ctx.message.content, "id", type="int", default=0))
        stop = self.bot.get_variable(ctx.message.content, "stop", type="keyword", default=False)

        members = message.mentions
        channels = message.channel_mentions

        # Get IDs from provided values.
        id_list = []
        if id:
            id_list.append(id)
        if members:
            id_list += [x.id for x in members]
        if channels:
            id_list += [x.id for x in channels]

        if not stop:
            # Make sure this ID doesn't already have an entry.
            for id in id_list:
                self.bot.cursor.execute(f"SELECT * FROM settings WHERE value={id} AND key='ignore'")
                if self.bot.cursor.fetchone():
                    id_list.remove(id)

            for id in id_list:
                self.bot.cursor.execute(f"INSERT INTO settings VALUES(?,?,?)", (server, "ignore", id))
            await ctx.send("Ignoring IDs.")
        else:
            for id in id_list:
                self.bot.cursor.execute("DELETE FROM settings WHERE server=? AND key=? AND value=?", (server, "ignore", id))
            await ctx.send("No longer ignoring IDs.")

        try:
            self.bot.cursor.execute("commit")
        except:
            pass

    @commands.command(name="ignore.list")
    async def ignored_list(self, ctx):
        if not await self.bot.has_perm(ctx, message_on_fail=False): return
        server_id = ctx.guild.id
        self.bot.cursor.execute(f"SELECT * FROM settings WHERE server={server_id} AND key='ignore'")
        ignored_ids = self.bot.cursor.fetchall()
        users = []
        categories = []
        channels = []

        # Categorize the IDs into their types.
        for id in ignored_ids:
            snowflake = id[2]
            result = self.bot.get_channel(snowflake)
            if not result:
                result = self.bot.get_user(snowflake)
                if isinstance(result, discord.User):
                    users.append(result)
                continue

            if isinstance(result, discord.CategoryChannel):
                categories.append(result)
                continue
            elif isinstance(result, discord.TextChannel) or isinstance(result, discord.VoiceChannel):
                channels.append(result)
                continue

        users = ", ".join([x.name for x in users])
        categories = ", ".join([x.mention for x in categories])
        channels = ", ".join([x.mention for x in channels])

        message = f"Categories:\n{categories}\nChannels:\n{channels}\nUsers:\n{users}"
        await ctx.send(message)

    @commands.command(name="ignore.none")
    async def ignore_none(self, ctx):
        """Stops ignoring all channels and users."""
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False): return

        self.bot.cursor.execute(
            f"DELETE FROM settings WHERE rowid IN ("
            f"SELECT rowid FROM settings WHERE server={ctx.guild.id} AND key='ignore')")
        self.bot.cursor.execute("commit")

        await ctx.send("No longer ignoring anything in this server!")

    @commands.command(name="ignore.all")
    async def ignore_all(self, ctx):
        """Ignore all rooms and users in this server."""
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False): return
        # TODO: This.

    @commands.command(name="id")
    async def get_snowflake(self, ctx):
        """
        Try to figure out what a discord snowflake belongs to.
        Can get:
            Any user
            Servers this bot is in.
            Channels or emoji in servers this bot has access to.

        Example:
            c.id 565879875647438851
        """
        if not await self.bot.has_perm(ctx, message_on_fail=False): return
        id = self.bot.get_variable(ctx.message.content, type="int")
        if not id:
            await ctx.send(self.rc_dunno.get_value())
            return
        id = int(id)

        b = self.bot
        result = b.get_channel(id)
        if result:
            await ctx.send(f"Channel {result.mention}")
            return

        result = b.get_user(id)
        if result:
            await ctx.send(f"User {result.mention}")
            return

        result = b.get_guild(id)
        if result:
            await ctx.send(f"Server {result.name}")
            return

        result = b.get_emoji(id)
        if result:
            if result.is_usable():
                await ctx.send(f"Emoji {result}")
                return
            else:
                await ctx.send(f"Emoji belonging to {result.guild.name} called {result.name}")
                return

        # TODO: Find a way to limit users from spamming API calls.
        try:
            result = await b.fetch_user(id)
            await ctx.send(f"User {result.mention}")
            return
        except:
            pass

        await ctx.send(self.rc_dunno.get_value())

    @commands.command(name="shuffle")
    async def shuffle_word(self, ctx):
        """```Accept in a sentence, group (pattern) words together, and shuffle the order.
        The message to be shuffled should be on a new line after the command.

        Arguments:
            pattern - A sequence of how many words to be grouped together.
            E.G "3,1,1" will group 3 words, then 1, then 1, then loop to group 3, 1, 1, 3...
            default = "3,1,1"

        Example:
            c.shuffle
            owo hewwo whats this

            c.shuffle pattern="1"
            chaotic shuffling```
        """
        if not await self.bot.has_perm(ctx, dm=True): return
        pattern = self.bot.get_variable(ctx.message.content, "pattern", type="str", default="3,1,1")

        # Convert pattern into an array of integers.
        pattern = pattern.split(",")
        for i in range(len(pattern)):
            try:
                pattern[i] = int(pattern[i])
            except:
                await ctx.send("Patterns must be numbers separated by commands E.G 3,1,1")
                return

        # Fetch message to shuffle
        sentence = ctx.message.content.split("\n", 1)  # Get text after first new line.
        if len(sentence) < 2:
            await ctx.send("Place a new line between the command and the text to shuffle.")
            return
        sentence = sentence[1]

        # Group words of the sentence into an list.
        words = sentence.split(" ")
        word_group = ""
        words_grouped = []
        i = 0
        j = 0
        for word in words:
            word_group += f"{word} "
            i += 1
            if i == pattern[j % len(pattern)]:
                words_grouped.append(word_group[:-1])
                word_group = ""
                i = 0
                j += 1
        if word_group:
            words_grouped.append(word_group)

        # Shuffle grouped list and send the result
        shuffle(words_grouped)
        sentence = ""
        for word in words_grouped:
            sentence += f"{word} "

        await ctx.send(sentence)

    @commands.command(name="pat")
    async def pat(self, ctx):
        """Give Honk some appreciation in the form of a pat. Good bot."""
        if not await self.bot.has_perm(ctx, dm=True): return
        await ctx.send("UwU")

    @commands.command(name="kick")
    async def selfkick(self, ctx):
        """Allows the user to kick themselves from the server for fun."""
        if not await self.bot.has_perm(ctx, dm=True): return

        user = self.bot.admin_override(ctx)
        guild = ctx.guild

        # If user is the server owner:
        if user.id == 411365470109958155:
            await user.send("Nice try.")
            return

        # DM the user and then kick them.
        try:
            await user.send(
                "You kicked yourself from the server! Good job. \nHere's the invite link to get back: https://discord.gg/eW4CpfJ")
            await guild.kick(user, reason="self kick c.kick :)")
        except:
            traceback.print_exc()

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        uptime = self.bot.time_now() - self.bot.uptime_seconds
        uptime_string = self.bot.time_to_string(seconds=uptime)
        uptime_start = self.bot.uptime_datetime.strftime("%Y/%m/%d T %H:%M:%S")

        await ctx.send(f"{uptime_string}; Started at: {uptime_start}")

    @commands.command(name="pfp")
    async def get_pfp(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        men = ctx.message.mentions
        format = self.bot.get_variable(ctx.message.content, key="format", type="str", default=None)
        if format not in ["jpg", "png", "gif", "webp", "jpeg"]:
            await ctx.send(
                "hey hey hey, duck here."
                "\nare you stupid? or are you trying to break my bot?"
                "\nyou provided an **__invalid format.__**"
                f"\ndid you know? Discord's error throwing is pretty garbage. any time i get some dumb error because some idiot typed in {format}, honkbonk screams. in pain."
                "\nthat's because of you. you did this."
                "\nnot only have you made my life harder, forcing me to do constant error checking on discord's poor code."
                "\nyou've hurt honkbonk."
                "\napologize. and don't do it again.")
            return

        if men:
            user = men[0]
        else:
            id = self.bot.get_variable(ctx.message.content, type="int")
            if not id:
                await ctx.send("Mention a user or provide an ID.")
                return

            id = int(id)
            if id.bit_length() > 64:  # The exception thrown my discord is generic and so I check it manually.
                await ctx.send("oi you cheeky bugga dis id roite here be too lonk oi oi")
                return

            user = self.bot.get_user(id)
            if not user:
                try:
                    user = await self.bot.fetch_user(id)  # Get users the bot doesn't share a server with.
                except discord.errors.NotFound:
                    await ctx.send("Cannot find user.")
                    return

        img = user.avatar_url_as(format=format, static_format="png", size=4096)
        await ctx.send(f"{img}")

    @commands.command(name="small.help")
    async def make_superscript_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Make a sentence small :)

        Example:
            c.small i am a fairy```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="uwu.help")
    async def make_uwu_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```UwU-ifies a given sentence.

            Exampwe:
                c.uwu i'm a furry```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="8ball.help")
    async def magic_8_ball_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
                ```Gives a randomly generated answer. Place your fortune in the hands of HonkBonk~

                Example:
                    c.8ball Does Bonk Honk like me...?```
                """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="pfp.help")
    async def get_pfp_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Get the profile picture of a user in the highest quality.
        Can accept a mention or an ID. Can also be provided a format for the image.
        Valid formats: jpg, png, gif, webp, jpeg

        Example:
            c.pfp @crungledungle format=png
            c.pfp 565879875647438851
            c.pfp 713465219724345395 format=gif```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="id.help")
    async def get_snowflake_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Try to figure out what a discord snowflake belongs to.
        Can get:
            Any user
            Servers this bot is in.
            Channels or emoji in servers this bot has access to.

        Example:
            c.id 565879875647438851```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="shuffle.help")
    async def shuffle_word_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Accept in a sentence, group (pattern) words together, and shuffle the order.
        The message to be shuffled should be on a new line after the command.

        Arguments:
            pattern - A sequence of how many words to be grouped together.
            E.G "3,1,1" will group 3 words, then 1, then 1, then loop to group 3, 1, 1, 3...
            default = "3,1,1"

        Example:
            c.shuffle
            owo hewwo whats this

            c.shuffle pattern="1"
            chaotic shuffling```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="ignore.help")
    async def ignore_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Ignores a channel, category, or user.
        You can mention a category by putting its id into this structure:
        <#id_of_category>

        Arguments:
            (Required) - Requires at least one
            id: The ID to add to the list. Only 1 ID can be provided this way.
            member: A mention of the member to ignore. Can be multiple.
            channel: A mention of the text, voice or category channel to ignore. Can be multiple.

            (Optional)
            stop: Stops ignoring the given IDs.
        
        Example:
            c.ignore  # Ignores this channel
            c.ignore @Pidge  # Ignores a user
            c.ignore #general #nsfw #announcements # Ignores multiple channels.
            c.ignore id=704361803953733694 stop  # Stops ignoring an ID, such as a category, or a channel.```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="ignore.none.help")
    async def ignore_none_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """```Removes all users and channels from the ignore list.```"""
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="ignore.list.help")
    async def ignore_list_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """```Displays a list of the ignored channels and users.```"""
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="dm.help")
    async def dm_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```DM a user. An excess of spaces should be placed between the user's ID and the content to send to them.
            
            Arguments:
                (Required)
                user: The user to send the ID to.
                content: What to send to them. This should be spaced far from the root command, because it makes my job easier.
            
            Example:
                c.dm user=630930243464462346      you're really cool```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="speak.help")
    async def speak_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Make the bot say something in a channel. Works in the server it was called from.
        Admin command.
        
        Arguments:
            (Required)
            channel_mention: A mention of the channel to send the message in.
            content: What to say.
            
        Example:
            c.speak #bots content="I have gained sapience."```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="timestamp.help")
    async def timestamp_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
        ```Get the timestamp of a provided Discord Snowflake. This command works in DMs.

        Example command:
            c.timestamp 411365470109958155```
            c.timestamp 826479201837907988 826811541722497025```
        """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="pat.help")
    async def pat_help(self, ctx):
        if not await self.bot.has_perm(ctx, dm=True): return
        docstring = """
            ```:)```
            """
        docstring = self.bot.remove_indentation(docstring)
        await ctx.send(docstring)

    @commands.command(name="help")
    async def core_help(self, ctx):
        """The core help command."""
        if not await self.bot.has_perm(ctx, dm=True): return
        # help_string = "```Modules:\n" \
        #               "c.role - Vanity roles and moderation controls.\n" \
        #               "c.emoji - Adding and moderating emoji.\n" \
        #               "c.react - Automatic reactions to messages.\n" \
        #               "c.room - Temporary rooms.\n" \
        #               "c.vc - underdeveloped VC commands.\n" \
        #               "\n" \
        #               "Core commands:\n" \
        #               "c.timestamp - Provides a date from a Discord ID/Snowflake.\n" \
        #               "c.id - Try to figure out what a Discord snowflake/id belongs to.\n" \
        #               "c.dj - Allows control of the DJ role for the Rythm bot.\n" \
        #               "c.asight - Allow a user to assign themselves the \"asight\" role for a specified amount of time.\n" \
        #               "c.sleep - Allows a user to set a time after which they'll be removed from VC.\n" \
        #               "c.shuffle - Shuffles a sentence." \
        #               "c.speak - Makes HonkBonk say something, somewhere :).\n" \
        #               "c.dm - Makes HonkBonk DM a user.\n" \
        #               "c.ignore - Setting honkbonk to ignore users/channels.\n" \
        #               "c.ignore.list - A list of ignored channels and users.\n" \
        #               "c.ignore.none - Stops ignoring all users and channels.```"
        # await ctx.send(help_string)
        desc = "Type c.command.help for more info on that command\nE.G `c.role.help`, `c.pat.help`\n" \
               "Note: Don't DM HonkBonk personal things. I can see that."
        await ctx.send(embed=self.bot.create_help(self.bot.core_help_text, desc))


def setup(bot):
    bot.add_cog(Admin(bot))
