import discord
import re
from discord.ext import commands


class RoleControl(commands.Cog, name="roles"):
    """
    Various commands related to controlling roles in the server.
    Uniquely controls the concept of "vanity roles", allowing people to create their own role for appearances.
    """
    prefix = "role"
    re_hex = re.compile(r"#([a-fA-F\d]{6})")  # Find a hex code prefixed with #.

    def __init__(self, bot):
        self.bot = bot
        self.init_db(bot.cursor)

    @commands.command(name=f"{prefix}")
    async def fuck_discord(self, ctx):
        """
        Discord doesn't allow me to have more arguments in a function than it likes, even if optional.
        This command acts as a wrapper to allow this. See colour_role
        """
        if not await self.bot.has_perm(ctx): return
        await self.colour_role(ctx)

    async def colour_role(self, ctx, o_user=None):
        """
        Create, or modify, a colour role.
        Arguments:
            o_user: A special variable for bypassing some checks. See role_overpower
            name: What to call the role.
            color: A hex code to assign to the role.
            mention: A keyword that determines if a role is mentionable. If creating, this will set it to true. When modifying, toggle.
        Example:
            (Creation) c.role name="total biscuit" #C070C0 mention
            (Update) c.role name="oops i made a typo"
            (Overpowering) c.role.overpower @Oken name="a real gato"
        """
        # TODO: Maybe split this function into aggregate functions "create role" and "modify role", even if both triggered by c.role
        if not await self.bot.has_perm(ctx): return False
        content = ctx.message.content
        guild = ctx.guild
        u = o_user if o_user else ctx.author  # If this function was called with o_user, allow someone other than the invoker.
        vanity_role = None

        # Fetch any variables the user provided.
        hex_colour = self.get_hex(content)
        can_mention = self.bot.get_variable(content, "mention", type="keyword", default=None)
        name = self.bot.get_variable(content, "name", type="str")

        # Some names should be reserved, as some stupid bots use the name of the role, not the id.
        disallowed_names = ["dj"]
        if u.id not in self.bot.admins and name and name.lower() in disallowed_names:
            await ctx.send("no.")
            return

        # Check if user has a vanity role already
        self.bot.cursor.execute(f"SELECT role_id FROM vanity_role WHERE id={u.id}")
        role_id = self.bot.cursor.fetchone()
        role_id = role_id[0] if role_id else None  # Gets the number stored if it exists, otherwise stores None.

        # If they have an entry, attempt to find this role.
        if role_id:
            vanity_role = guild.get_role(int(role_id))
            if not vanity_role:
                # Delete this entry, as the role doesn't exist anymore.
                self.bot.cursor.execute(f"DELETE FROM vanity_role WHERE id={u.id}")
                self.bot.db.commit()

        # Create new role
        if not vanity_role:
            if not name:
                await ctx.send("""Please provide a role name in the format `name="name of role"`""")
                return
            if not hex_colour:
                await ctx.send("""Please put a hex colour code somewhere in the message :)""")
                return
            else:
                col = discord.Colour(hex_colour)

            can_mention = True if can_mention else False
            vanity_role = await guild.create_role(name=name, colour=col, mentionable=can_mention)

            # TODO: Find a better way to determine the role position.
            role_num = len(guild.roles) - 4
            await vanity_role.edit(position=role_num)

            # Assign role to user and update db
            new_roles = u.roles
            new_roles.append(vanity_role)
            await u.edit(roles=new_roles)
            self.bot.cursor.execute("INSERT INTO vanity_role VALUES(?,?)", (u.id, vanity_role.id))
            self.bot.db.commit()

            await ctx.send("+1 sinful role created")
            return
        # Edit an existing role.
        else:
            # Construct an embed to display what changes have happened.
            embed = self.bot.default_embed("Vanity Role Update")
            zws = self.bot.zws

            if not name and not hex_colour and not can_mention:
                embed.description = "Nothing changed.\nprovide variables."
                msg = await ctx.send(embed=embed)
                await msg.add_reaction("<:bap:771864166294224906>")

                # Assign this role to the person in the event it's somehow off of them.
                new_roles = u.roles
                new_roles.append(vanity_role)
                await u.edit(roles=new_roles)
                return

            if name:
                embed.add_field(name=":new: New name:", value=name, inline=True)
                embed.add_field(name=zws, value=zws,
                                inline=True)  # This last one used to force the next ones to be a new line.
                embed.add_field(name=":older_man: Old name:", value=vanity_role.name, inline=True)
            else:
                name = vanity_role.name

            if hex_colour:
                new_col = f"#{str(hex(hex_colour))[2:]}"
                embed.add_field(name=":new: New colo__u__r:", value=new_col, inline=True)
                embed.add_field(name=zws, value=zws, inline=True)
                embed.add_field(name=":older_woman: Old colo__u__r:", value=vanity_role.colour, inline=True)
                col = discord.Colour(hex_colour)
            else:
                col = vanity_role.colour

            if can_mention != None:
                can_mention = False if vanity_role.mentionable else True
                can_mention_now = "Yes" if can_mention else "No"
                can_mention_before = "Yes" if vanity_role.mentionable else "No"

                embed.add_field(name=":new: Mentionable?", value=can_mention_now, inline=True)
                embed.add_field(name=zws, value=zws,
                                inline=True)  # This last one used to force the next ones to be a new line.
                embed.add_field(name=":older_adult: Used to be?", value=can_mention_before, inline=True)
            else:
                can_mention = vanity_role.mentionable

            embed.set_footer(text="Oken forced me to use emoji. :frowning2:")

            # Assign this role to the person in the event it's somehow off of them.
            new_roles = u.roles
            if vanity_role not in new_roles:
                new_roles.append(vanity_role)
                await u.edit(roles=new_roles)

            await vanity_role.edit(mentionable=can_mention, name=name, colour=col)
            await ctx.send(embed=embed)

    @commands.command(name=f"{prefix}.delete")
    async def delete_vanity_role(self, ctx):
        """
        Deletes a vanity role. Only deletes the role of the person who called it.
        Example:
            c.role.delete
        """
        if not await self.bot.has_perm(ctx, banned_users=True): return False
        u = ctx.author

        # Check if user has a vanity role in the database
        self.bot.cursor.execute(f"SELECT role_id FROM vanity_role WHERE id={u.id}")
        role_id = self.bot.cursor.fetchone()

        role_id = role_id[0] if role_id else None  # Gets the number stored if it exists, otherwise stores None.

        # Find vanity role
        vanity_role = ctx.guild.get_role(role_id)
        if not vanity_role:
            await ctx.send("You don't have a vanity role??")
            return
        await vanity_role.delete()
        self.bot.cursor.execute(f"DELETE FROM vanity_role WHERE id={u.id}")
        self.bot.db.commit()
        await ctx.send("Cast aside your Pride; Vanity has been vanquished.")
        return

    @commands.command(name=f"{prefix}.info")
    async def role_info(self, ctx):
        """
        Gets information about ANY role, not just vanity roles.
        Displays the following information about roles:
            Role name, role snowflake, date created, hex colour, mentionable
        Arguments:
            role_mention: A mention of the role to get info from.
            user_mention: A user to get vanity role information from.
        Example:
            c.role.info @Oken
            c.role.info @newcomers
        """
        if not await self.bot.has_perm(ctx): return False
        message = ctx.message

        if message.role_mentions:
            role = message.role_mentions[0]
        elif message.mentions:
            self.bot.cursor.execute(f"SELECT role_id FROM vanity_role WHERE id={ctx.author.id}")
            role_id = self.bot.cursor.fetchone()[0]
            role = ctx.guild.get_role(role_id)
        else:
            await ctx.send("Please provide a role or a user!")
            return

        if not role:
            await ctx.send("Role not found.")
            return

        col = str(role.colour).upper()  # Hex code of colour.
        id = role.id
        name = role.name
        created = self.bot.date_from_snowflake(id)
        mentionable = role.mentionable

        mentionable = ":white_check_mark:" if mentionable else ":no_entry_sign:"

        embed = self.bot.default_embed("Role Information")
        zws = self.bot.zws

        embed.add_field(name=":name_badge: Name:", value=name, inline=True)
        embed.add_field(name=zws, value=zws, inline=True)  # This last one used to force the next ones to be a new line.
        embed.add_field(name=":id: Snowflake:", value=id, inline=True)

        embed.add_field(name=":clock1030: Created:", value=created, inline=True)
        embed.add_field(name=zws, value=zws, inline=True)  # This last one used to force the next ones to be a new line.
        embed.add_field(name=":paintbrush: Colo__**u**__r:", value=col, inline=True)

        embed.add_field(name=":loudspeaker: Mentionable:", value=mentionable, inline=True)

        await ctx.send(embed=embed)

    @commands.command(name=f"{prefix}.override")
    async def role_overrider(self, ctx):
        """
        Allows an admin to change the vanity role of someone else.
        See colour_role for usage example.
        """
        if not await self.bot.has_perm(ctx, admin=True, message_on_fail=False):
            await ctx.send("nice try.")
            return

        o_user = ctx.message.mentions[0]  # The user to change the role of.
        await self.colour_role(ctx, o_user=o_user)

    def get_hex(self, string):
        """Finds the first instance of a hex value in a string."""
        hex_match = re.search(self.re_hex, string)
        if hex_match:
            return int(hex_match.group(1), 16)
        else:
            return None

    def init_db(self, cursor):
        cursor.execute("begin")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS vanity_role ("  # An entry is created for each change that is detected.
            "id INTEGER,"  # ID of the user
            "role_id INTEGER"  # The ID of this user's vanity role.
            ")")
        cursor.execute("commit")


def setup(bot):
    bot.add_cog(RoleControl(bot))
