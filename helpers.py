import time
from datetime import datetime
import re
from math import trunc
"""A bunch of functions that are useful."""


# TODO: All of these time functions would be better served if they returned an object.
def time_now():
    """Get the current Unix Epoch time, in seconds."""
    return time.mktime(datetime.utcnow().timetuple())


def time_from_string(string):
    """
    Creates a time given in seconds out of a string. Accepts:
    picoseconds, nanoseconds, milliseconds, centiseconds, deciseconds seconds, minutes, hours, days, weeks

    Example string:
        "a bunch of text worth 20 seconds, 12 picoseconds, 1 millisecond"
    """
    seconds = 0
    r_time = r"(\d+(?:\.\d+)?)"  # A number, optionally decimal.

    # Name of unit, followed by how many seconds each is worth.
    time_units = {
        # others
        "jiffy": 0.01,
        "friedman": 86400 * 30 * 6,
        # Metric units
        "picosecond": 0.000000000001,
        "nanosecond": 0.000000001,
        "microsecond": 0.000001,
        "millisecond": 0.001,
        "centisecond": 0.01,
        "decisecond": 0.1,
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400,
        "week": 604800,
        "month": 86400*30,  # 30 days in a month :)
    }

    # Search for the first instance of each of these.
    for unit, worth_seconds in time_units.items():
        re_string = rf"({r_time}) {unit}s?"
        match = re.search(re_string, string)
        if not match:
            continue

        t = float(match.group(1))
        seconds += t*worth_seconds

    return seconds


def time_to_string(seconds=0, minutes=0, hours=0, days=0, weeks=0):
    """
    Returns the provided time as a string.
    """
    # Convert provided values to seconds.
    time = (weeks * 604800) + (days * 86400) + (hours * 3600) + (minutes * 60) + seconds  # This is inefficient, but looks nicer.
    weeks, remainder = divmod(time, 604800)
    days, remainder = divmod(remainder, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    timestring = ""
    if weeks:
        u = "week" if weeks == 1 else "weeks"
        timestring += f"{trunc(weeks)} {u}, "
    if days:
        u = "day" if days == 1 else "days"
        timestring += f"{trunc(days)} {u}, "
    if hours:
        u = "hour" if hours == 1 else "hours"
        timestring += f"{trunc(hours)} {u}, "
    if minutes:
        u = "minute" if minutes == 1 else "minutes"
        timestring += f"{trunc(minutes)} {u}, "
    if seconds:
        u = "second" if seconds == 1 else "seconds"
        timestring += f"{trunc(seconds)} {u}, "

    if timestring:
        timestring = timestring[:-2]  # Crop the last two characters

    return timestring


def time_from_now(*, milliseconds=0, seconds=0, minutes=0, hours=0, days=0, weeks=0):
    """Calculates the time from now with the provided values."""
    seconds_total = time_to_seconds(milliseconds=milliseconds, seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks)
    return time.mktime(datetime.utcnow().timetuple()) + seconds_total


def time_to_seconds(*, milliseconds=0, seconds=0, minutes=0, hours=0, days=0, weeks=0):
    """Converts the provided time units into seconds."""
    seconds_total = seconds
    seconds_total += milliseconds*0.000001
    seconds_total += minutes*60
    seconds_total += hours*3600
    seconds_total += days*86400
    seconds_total += weeks*604800
    return seconds_total

# ==== Potentially useful, removed for now ====
#
# def escape_message(message):
#     """Make a message 'safe' to send by removing any pings"""
#
#     m = message
#     m = m.replace("\\", "\\\\")  # Stops people undoing my escapes.
#     m = m.replace("@", "@\u200b")
#     m = m.replace("@everyone", f"@\u200beveryone")
#     return m
#
# def remove_indentation(string):
#     indentation_amount = re.search(MyBot.r_newline_whitespace, string)
#     if not indentation_amount:
#         return string
#     indentation_amount = indentation_amount.group(1)
#     return re.sub(indentation_amount, "", string)
#
# def date_from_snowflake(snowflake, strftime_val="%Y-%m-%d %H:%M:%S UTC"):
#     """
#     Convert a Discord snowflake into a date string.
#     Arguments:
#         snowflake: A discord snowflake/ID
#         strftime_val: An strf to use on the datetime object.
#     Returns:
#         A string of the date.
#     """
#     timestamp = ((int(snowflake) >> 22) + 1420070400000) / 1000
#     dt = datetime.fromtimestamp(timestamp)
#     return dt.strftime(strftime_val)
#
# def remove_invoke(message):
#     """Removes the invoking call from a message using RegEx."""
#     return re.sub("(c\.[^\s]+)", "", message, count=1)
#
# def get_variable(string, key=None, type=None, pattern=None, default=None):
#     """
#     Uses regex to parse through a string, attempting to find a given key:value pair or a keyword.
#
#     List of recognized types:
#         "str" - Finds the first key=value_no_spaces or key="value in quotes" pair in the string, E.G say="Hi there!". Returns value.
#         "int" - Finds the first key=number pair in the string, E.G repeat=5. Returns value.
#         "keyword" - Tries to simply find the given word in the string. Returns True if keyword is found, False otherwise.
#         "float" - Find the first key=number.number pair, E.G percent=1.0 or percent=52
#
#     Arguments:
#         string: The string to search for the variable in.
#         key: Used in key=type. Requires type to be defined. If omitted, will just search the string using "type"
#         type: Used in key=type
#         pattern: A regex pattern to search with instead of using key=type
#         default: Default return value if nothing is found.
#
#     Returns: String or Boolean
#     """
#     re_pat = ""  # The regex pattern to parse the string with.
#
#     # Get and compile the regex pattern to use to search.
#     if type:
#         if key:
#             if type == "keyword":
#                 re_pat = re.compile(fr"(\b{key}\b)")
#             elif type in MyBot.pformats:
#                 re_pat = re.compile(fr"(?:\b{key}=){MyBot.pformats[type]}")
#             else:  # Unrecognized type.
#                 raise AttributeError(f"Unrecognized type for get_variable: {type}")
#         else:
#             if type in MyBot.pformats:
#                 re_pat = re.compile(fr"{MyBot.pformats[type]}")
#             else:
#                 raise AttributeError()
#     elif pattern:  # A pre-compiled re pattern to search with
#         re_pat = pattern
#     else:
#         raise AttributeError(f"get_variable was not provided with a pattern or a type")
#
#     search_result = re.search(re_pat, string)
#     if search_result:
#         if type == "keyword":
#             return True
#         else:
#             return allgroups(search_result)
#
#     return default
