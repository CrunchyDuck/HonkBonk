import sqlite3

"""This is used to quickly grab data from teh database file."""

con = sqlite3.connect("bot.db")
cur = con.cursor()
table = "emoji_reactions"
field = "*"
condition = ""

#cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
cur.execute(f"SELECT {field} FROM {table} {condition}")
#cur.executemany("UPDATE emoji_reactions SET triggered=?", gaf)
#cur.execute("commit")

for e in cur.fetchall():
    print(e)

input("Press enter to continue...")
