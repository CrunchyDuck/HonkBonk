from dataclasses import dataclass, field
from typing import Callable
import asyncio
import helpers


class Scheduler:
    """
    Allows functions to be scheduled to be run at a later time.

    Attributes:
        bot: A reference to the discord bot.
    """
    def __init__(self):
        self.timed_functions = []  # Bit of data redundancy never hurt anybody. used in refresh_schedule.
        self.schedule = []
        self.schedule_time = 0.5  # In seconds, how regularly the schedule is checked

    def add(self, function, timer):
        """
        Adds a timed function to the scheduler.
        Arguments:
            function - The method to run each trigger.
            timer - integer or method
                Integer will cause the function to be run every (integer) seconds.
                A method will be called, and should return a Unix Epoch time in seconds of when the function should run.
        """
        self.timed_functions.append([function, timer])
        # TODO: Maybe support adding while self.start loop is running?

    def generate_schedule(self):
        """Creates a schedule from self.timed_functions."""
        new_schedule = []
        time = helpers.time_now()  # Current Unix Epoch time.
        for function, timer in self.timed_functions:
            event = ScheduledEvent(function, timer)
            try:
                event.update_time(time)
            except TypeError as e:
                print(e)
            new_schedule.append(event)

        return sorted(new_schedule)

    async def start(self):
        """
        Main loop.
        Will continually check each ScheduledEvent and run if necessary.
        """
        self.schedule = self.generate_schedule()
        if not self.schedule:
            print("No scheduled functions.")
            return
        while True:
            await asyncio.sleep(self.schedule_time)
            time_now = helpers.time_now()  # Current Unix Epoch time.
            while time_now > self.schedule[0].time:
                # FIXME: If an event's time doesn't increase this will cause an infinite loop.
                #  Will never come up through proper use of the Scheduler, but should be prevented still.
                #  Could maybe limit how many times something is allowed to repeat in one tick.
                event = self.schedule[0]
                await event.function(time_now)
                event.update_time(time_now)
                self.schedule = sorted(self.schedule)  # Find the next most recent event


@dataclass(order=True)
class ScheduledEvent:
    """

    Attributes:
        function - The function to run
        timer - A function or integer to calculate a new time
        time - The time this event should trigger
    """
    function: Callable = field(compare=False)
    timer: object = field(compare=False)
    time: int = None

    def run(self, current_time):
        """
        Runs self.function and updates self.time

        Arguments:
            current_time - Current Unix Epoch time in seconds.
        """
        self.function(current_time)
        self.update_time(current_time)

    def update_time(self, current_time):
        """
        Updates self.time using timer.

        Arguments:
            current_time - The current Unix Epoch time in seconds.
        """
        # Timer is an integer, add to current time
        if isinstance(self.timer, int):
            self.time = current_time + self.timer
        # Timer is a function
        elif callable(self.timer):
            self.time = self.timer()
        # Timer is unrecognized
        else:
            raise TypeError(f"Scheduler was provided with type {type(self.timer)} for timer, should be callable or int.\n")
