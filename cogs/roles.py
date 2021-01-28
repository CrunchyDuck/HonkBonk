import discord
import re
from discord.ext import commands
import traceback


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

    # TODO: Change this to .vanity
    @commands.command(name=f"{prefix}")
    async def colour_role(self, ctx):
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
        u = self.bot.admin_override(ctx)
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
                if vanity_role not in new_roles:
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

    @commands.command(name=f"{prefix}.apply")
    async def apply_role(self, ctx):
        """
        Adds a role to a user, optionally for an amount of time.
        Arguments:
            (Required)
            user: The user to apply the role to. This can be provided as an argument of their ID, or as a mention.
            role: The role to apply to the user. This can be provided as an argument of its ID, or as a mention.

            (Optional)
            time: How long to apply this role for in hours.
        Examples:
            c.role.apply @Oken @bapped time=12  # Apply a role for 12 hours.
            c.role.apply user=411365470109958155 role=772218505306439680  # Apply a role permanently
            c.role.apply @Crunc role=804463840539574302
        """
        if not await self.bot.has_perm(ctx, admin=True): return False
        message = ctx.message
        content = message.content
        time = float(self.bot.get_variable(content, "time", type="float", default=0))
        roles = message.role_mentions
        user = message.mentions

        # Find the member
        if user:
            user = message.mentions[0]
        else:
            user_id = int(self.bot.get_variable(content, "user", type="int", default=0))
            if not user_id:
                await ctx.send("Mention a user or provide their id as user=id")
                return
            user = ctx.guild.get_member(user_id)
            if not user:
                await ctx.send(f"Cannot find member with id {user_id}")
                return

        # Find the role
        if roles:
            roles = roles[0]
        else:
            role_id = int(self.bot.get_variable(content, "role", type="int", default=0))
            if not role_id:
                await ctx.send("Mention a role or provide its id as role=id")
                return
            roles = ctx.guild.get_role(role_id)
            if not roles:
                await ctx.send(f"Cannot find role with id {role_id}")
                return

        # Check if there's already an entry in the database for this user/role
        self.bot.cursor.execute(
            f"SELECT rowid, * FROM temp_role WHERE"
            f" user_id={user.id} AND server={ctx.guild.id} AND role_ids={roles.id}")
        result = self.bot.cursor.fetchone()

        # Apply the role to the user
        try:
            await user.add_roles(roles)
        except discord.errors.Forbidden:
            await ctx.send("I need the manage roles permission for this, and the role must be lower than my highest role.")
            return
        except discord.errors.HTTPException:
            await ctx.send("Adding role failed.")
            return
        except:
            traceback.print_exc()
            return

        if time != 0:
            time = max(min(336, time), 0.0003)  # Limit to 1 month or 1 second.
            end_time = self.bot.hours_from_now(time)
            time_string = self.bot.time_to_string(hours=time)

            if result:  # Update existing entry.
                self.bot.cursor.execute(f"UPDATE temp_role SET end_time={end_time} WHERE rowid={result[0]}")
            else:  # Create entry.
                self.bot.cursor.execute(f"INSERT INTO temp_role VALUES({ctx.guild.id}, {user.id}, {end_time}, {roles.id})")

            await ctx.send(f"{roles.name} added to {user.name} for {time_string}!")
        else:
            if result:  # Remove entries for the temp role so it doesn't get removed later.
                self.bot.cursor.execute(f"DELETE FROM temp_role WHERE rowid={result[0]}")
            await ctx.send(f"Role added!")

        self.bot.cursor.execute("commit")

    @commands.command(name=f"{prefix}.remove")
    async def remove_role(self, ctx):
        """
        Adds a role to a user, optionally for an amount of time.
        Arguments:
            (Required)
            user: The user to apply the role to. This can be provided as an argument of their ID, or as a mention.
            role: The role to apply to the user. This can be provided as an argument of its ID, or as a mention.
        Examples:
              c.role.remove @pidge @straight
              c.role.remove user=565879875647438851 role=771924151950114846
        """
        if not await self.bot.has_perm(ctx, admin=True): return False
        message = ctx.message
        roles = message.role_mentions
        user = message.mentions

        # Find the member
        if user:
            user = message.mentions[0]
        else:
            user_id = int(self.bot.get_variable(content, "user", type="int", default=0))
            if not user_id:
                await ctx.send("Mention a user or provide their id as user=id")
                return
            user = ctx.guild.get_member(user_id)
            if not user:
                await ctx.send(f"Cannot find member with id {user_id}")
                return

        # Find the role
        if roles:
            roles = roles[0]
        else:
            role_id = int(self.bot.get_variable(content, "role", type="int", default=0))
            if not role_id:
                await ctx.send("Mention a role or provide its id as role=id")
                return
            roles = ctx.guild.get_role(role_id)
            if not roles:
                await ctx.send(f"Cannot find role with id {role_id}")
                return

        try:
            await user.remove_roles(roles, reason="Role remove command")
        except discord.errors.Forbidden:
            await ctx.send("I require manage roles, and the role I'm removing must be lower than my highest role.")
            return
        except discord.errors.HTTPException:
            await ctx.send("Failed removing role.")
            return
        except:
            traceback.print_exc()

        await ctx.send(f"{roles.name} removed from {user.name}.")

        # Check if this role and user have an entry in the temp_role database
        self.bot.cursor.execute(
            f"SELECT rowid FROM temp_role WHERE"
            f" user_id={user.id} AND server={ctx.guild.id} AND role_ids={roles.id}")
        results = self.bot.cursor.fetchall()

        self.bot.cursor.executemany("DELETE FROM temp_role WHERE rowid=?", results)

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
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS temp_role ("  # An entry is created for each change that is detected.
            "server INTEGER,"  # ID of the server
            "user_id INTEGER,"  # ID of the user
            "end_time INTEGER,"  # The time this role should be removed.
            "role_ids INTEGER"  # The ID of this user's vanity role.
            ")")
        cursor.execute("commit")


def setup(bot):
    bot.add_cog(RoleControl(bot))
