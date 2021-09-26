from discord.ext import commands
from typing import Callable
from dataclasses import dataclass
import asyncio
from datetime import datetime


class ReactiveMessageManager:
    """
    A reactive message is a message that changes in response to emoji.
    It requires a function to generate a message, and a list of pages that contain the data required to run the function.
    """
    def __init__(self, bot):
        self.reacting_message = {}
        bot.add_listener(self.on_raw_reaction_add)
        bot.add_listener(self.on_raw_reaction_remove)

    # TODO: Implement wrap
    def create_reactive_message(self, message, message_page_function: Callable, message_pages: list,
                                reaction_previous: str, reaction_next: str,
                                *, seconds_active=60, wrap=False):
        """

        Arguments:
            message - The discord message object that should respond to reactions.
            message_page_function - A function that generates the new message, when given a page.
            message_pages - The data to provide to message_page_function.
            reaction_previous - Reaction that calls previous page
            reaction_next - Reaction that calls next page.

            seconds_active - How long the will react for.
        """
        current_time = datetime.now()
        rm = ReactingMessage(message, message_page_function, message_pages, reaction_previous, reaction_next, 0, wrap, current_time, seconds_active)
        self.reacting_message[message] = rm

    async def message_timer_loop(self, current_time):
        rm_copy = self.reacting_message.copy()
        for message, reacting_message in rm_copy.items():
            time_passed = reacting_message.started_time - current_time
            if not time_passed >= reacting_message.seconds_active:
                # Not enough time has passed.
                continue
            await message.remove_reaction(reacting_message.reaction_previous)
            await message.remove_reaction(reacting_message.reaction_next)
            del self.reacting_message[message]

    #@commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        reaction = payload.emoji
        user = payload.member
        await self.message_react(reaction, user)

    #@commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        reaction = payload.emoji
        user = payload.member
        await self.message_react(reaction, user)

    async def message_react(self, emoji, message_id):
        # TODO: User checks?
        if message_id not in self.reacting_message:
            return
        reacting_message = self.reacting_message[message_id]
        # Is the reaction one we care about?
        reaction_str = emoji
        if reaction_str not in [reacting_message.reaction_previous, reacting_message.reaction_next]:
            return

        try:
            if reaction_str == reacting_message.reaction_previous:
                new_message = reacting_message.previous_page()
            else:
                new_message = reacting_message.next_page()
        except IndexError:
            return
        await reacting_message.edit(content=new_message)


@dataclass
class ReactingMessage:
    message: object
    message_page_function: Callable
    message_pages: list
    reaction_previous: str
    reaction_next: str
    page_num: int
    wrap: bool
    started_time: object
    seconds_active: int

    def next_page(self):
        self.page_num += 1
        # Out of bounds
        if self.page_num >= len(self.message_pages):
            if self.wrap:
                self.page_num = self.page_num % len(self.message_pages)
            else:
                self.page_num -= 1
                raise IndexError
        return self.get_page()

    def previous_page(self):
        self.page_num -= 1
        # Out of bounds
        if self.page_num < 0:
            if self.wrap:
                self.page_num = self.page_num + len(self.message_pages)
            else:
                self.page_num += 1
                raise IndexError
        return self.get_page()

    def get_page(self):
        page = self.message_pages[self.page_num]
        self.started_time = datetime.now()
        return self.message_page_function(page)