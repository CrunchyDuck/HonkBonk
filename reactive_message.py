from typing import Callable, List
from dataclasses import dataclass
from helpers import time_now


class ReactiveMessageManager:
    """
    A reactive message is a message that changes in response to emoji.
    It requires a function to generate a message, and a list of pages that contain the data required to run the function.
    """
    def __init__(self, bot):
        self.reacting_message = {}
        bot.add_listener(self.on_raw_reaction_add)
        bot.add_listener(self.on_raw_reaction_remove)
        bot.add_listener(self.on_message)
        bot.Scheduler.add(self.message_timer_loop, 5)
        self.bot = bot

    # TODO: Rework this to support the concept of books/pages.
    # TODO: Ability to stop reacting before time is up.
    async def create_reactive_message(self, message, message_page_function: Callable, message_pages: list,
                                *, page_back: str = "◀️", page_forward: str = "▶️", cancel: str = "🇽",
                                on_message_func: Callable = None, users: List[int] = None,
                                seconds_active: int = 20, wrap: bool = True,
                                custom_reactions=None):
        """

        Arguments:
            message - The discord message object that should respond to reactions.
            message_page_function - A function that generates the new message, when given a page.
            message_pages - The data to provide to message_page_function.
            reaction_previous - Reaction that calls previous page
            reaction_next - Reaction that calls next page.

            seconds_active - How long the will react for.
            wrap - Whether to wrap to the start page when we reach the end.
            users - A list of user IDs
            custom_reactions - A dictionary of emoji:function
        """
        current_time = time_now()
        await message.add_reaction(page_back)
        await message.add_reaction(page_forward)
        await message.add_reaction(cancel)
        custom_reactions = {} if custom_reactions is None else custom_reactions
        for r in custom_reactions:
            await message.add_reaction(r)

        rm = ReactingMessage(message, on_message_func, message_page_function, message_pages, page_back, page_forward, cancel,
                             0, wrap, current_time, seconds_active, users, custom_reactions)
        self.reacting_message[message.id] = rm

    async def message_timer_loop(self, current_time):
        """Regularly checks whether a message should stop responding to reactions.

        Arguments:
            current_time - Unix epoch seconds.
        """
        rm_copy = self.reacting_message.copy()
        for message_id, reacting_message in rm_copy.items():
            time_passed = current_time - reacting_message.started_time
            if not time_passed >= reacting_message.seconds_active:
                # Not enough time has passed.
                continue
            await self.remove_reactive_message(reacting_message)

    async def remove_reactive_message(self, reacting_message):
        message = reacting_message.message
        del self.reacting_message[message.id]
        try:
            await message.clear_reactions()
        except Exception as e:
            pass

    #@commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        reaction = str(payload.emoji)
        message_id = payload.message_id
        user_id = payload.user_id
        await self.message_react(reaction, message_id, user_id)

    #@commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        reaction = str(payload.emoji)
        message_id = payload.message_id
        user_id = payload.user_id
        await self.message_react(reaction, message_id, user_id)

    async def on_message(self, message):
        rm_copy = self.reacting_message.copy()
        for k, reacting_message in rm_copy.items():
            if not reacting_message.on_message_func:
                continue
            # Is this a user we're expecting a response from?
            if message.author.id in reacting_message.users:
                if await reacting_message.on_message_func(message, reacting_message):
                    return

    async def message_react(self, emoji, message_id, user_id):
        if message_id not in self.reacting_message:
            return
        reacting_message = self.reacting_message[message_id]
        # Is it from a user we're tracking?
        if reacting_message.users and user_id not in reacting_message.users:
            return
        # Is the reaction one we care about?
        if emoji == reacting_message.reaction_cancel:
            await self.remove_reactive_message(reacting_message)
            return
        elif emoji == reacting_message.reaction_previous:
            new_message = reacting_message.previous_page()
        elif emoji == reacting_message.reaction_next:
            new_message = reacting_message.next_page()
        elif emoji in reacting_message.custom_reactions:
            await reacting_message.custom_reactions[emoji](reacting_message, user_id)
            return
        else:
            return
        try:
            await reacting_message.message.edit(embed=new_message)
        except Exception as e:
            # Something went wrong, get rid of it
            await self.remove_reactive_message(reacting_message)
            raise e


@dataclass
class ReactingMessage:
    message: object
    on_message_func: Callable
    message_page_function: Callable
    message_pages: list
    reaction_previous: str
    reaction_next: str
    reaction_cancel: str
    page_num: int
    wrap: bool
    started_time: float
    seconds_active: int
    users: List[int]
    custom_reactions: List[str]

    def next_page(self) -> str:
        self.page_num += 1
        # Out of bounds
        if self.page_num >= len(self.message_pages):
            if self.wrap:
                self.page_num = self.page_num % len(self.message_pages)
            else:
                self.page_num -= 1
                raise IndexError
        return self.get_page()

    def previous_page(self) -> str:
        self.page_num -= 1
        # Out of bounds
        if self.page_num < 0:
            if self.wrap:
                self.page_num = self.page_num + len(self.message_pages)
            else:
                self.page_num += 1
                raise IndexError
        return self.get_page()

    def get_page(self) -> str:
        page = self.message_pages[self.page_num]
        self.started_time = time_now()
        return self.message_page_function(page)