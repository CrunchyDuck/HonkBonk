from tkinter import *
from tkinter import ttk
from functools import partial
from sqlite3 import connect
from time import sleep
# TODO: Import PIL

class BotUI:
    def __init__(self, bot):
        self.bot = bot
        self.awaiting = True  # Waiting for the bot to finish initializing.
        self.db = None  # Set in self.start due to threading things.

    def start(self):
        self.db = connect("bot.db")  # Not created in __init__ because of threading.

        while self.awaiting:
            sleep(0.5)

        root = Tk()
        root.title("HonkBonk Control Panel")
        #root.geometry("200x200")
        root.iconbitmap("./icon.ico")

        tab_control = ttk.Notebook(root)
        tab_control.add(self.manage_cogs(), text="cogs")
        tab_control.add(self.manage_database(), text="database")
        tab_control.pack(expand=1, fill="both")

        root.mainloop()

    def manage_cogs(self):
        """The tab for managing cogs"""
        f = Frame()
        tree_columns = ["ID", "Name", "Active", "Start Time"]
        tree = ttk.Treeview(f, columns=tree_columns, show="headings", height=20)
        for col in tree_columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        # Get database stuff
        self.update_cog_tree(tree)

        cmd = partial(self.toggle_cog, tree, tree_columns)
        bToggleCog = ttk.Button(f, text="Toggle on/off", command=cmd)
        cmd = partial(self.reload_cog, tree, tree_columns)
        bReloadCog = ttk.Button(f, text="Reload cog", command=cmd)
        bToggleCog.pack()
        bReloadCog.pack()

        tree.pack()
        return f

    def manage_database(self):
        """The tab for managing the database."""
        f = Frame()
        ttk.Button(f, text="f-fill my base with data aaa").pack()
        return f

    def reload_cog(self, tree, columns):
        columns = self.get_tree_selected(tree, columns)
        if columns:
            for column in columns:
                self.bot.cog_queue.append([column["Name"], self.bot.reload_extension])

    def toggle_cog(self, tree, columns):
        """
        Turns a cog on or off, depending on its current state.

        Arguments:
            tree - The tree to search
            columns - The names of the columns in order. afaik tree has no build in method for viewing them.
        """
        columns = self.get_tree_selected(tree, columns)
        if not columns:  # Nothing selected
            return

        for column in columns:
            # Update database
            entry = self.bot.db_get(self.db, f"SELECT rowid,* FROM cogs WHERE cog=?", column['Name'])[0]
            rowid = entry["rowid"]
            active = entry["active"]
            name = entry["cog"]

            if active:
                self.bot.cog_queue.append([name, self.bot.unload_extension])
                state = 0
            else:
                self.bot.cog_queue.append([name, self.bot.load_extension])
                state = 1

            column["Active"] = state
            self.db.execute(f"UPDATE cogs SET active={state} WHERE rowid={rowid}")
            self.db.execute("commit")
            self.update_cog_tree(tree)
            self.focus_tree(tree, 0, rowid)

    def update_cog_tree(self, tree):
        # Clear tree
        for i in tree.get_children():
            tree.delete(i)

        # Fill tree
        entries = self.bot.db_get(self.db, "SELECT rowid,* FROM cogs")
        for entry in entries:
            id = entry["rowid"]
            values = list(entry.values()) + ["NaN"]
            tree.insert("", id, values=values)

    def focus_tree(self, tree, column, value):
        """
        Sets a tree's focus on the first item with a specific value.

        Arguments:
            tree - tkinter tree object
            column - The POSITION of the column, starting at 0.
            value - What this column should have in it.
        """
        new_selection = []
        for i in tree.get_children():
            row_value = tree.item(i)["values"][column]
            if row_value == value:
                new_selection.append(i)

        tree.selection_set(*new_selection)


    def test(self, a=0, b=1):
        print("owo", a, b)

    @staticmethod
    def get_tree_selected(tree, columns):
        """
        Gets the currently selected rows, and returns a dictionary of their values.
        Returns:
            [{"column":value,(...),"iid":value}, (...)]
        """
        selections = []
        current_focus = tree.selection()
        for i in current_focus:
            column_fields = tree.item(i)["values"]
            column_fields.append(current_focus)
            columns.append("iid")
            selections.append(dict(zip(columns, column_fields)))
        return selections


