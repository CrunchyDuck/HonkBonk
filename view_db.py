import sqlite3

"""This is used to quickly grab data from teh database file."""

con = sqlite3.connect("bot.db")
cur = con.cursor()
table = "temp_room"
field = "*"

cur.execute(f"SELECT field FROM {table}")
for e in cur.fetchall():
    print(e)

input("Press enter to continue...")
