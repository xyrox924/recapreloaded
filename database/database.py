import sqlite3

from pathlib import Path

from database.models import *

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

        # create db
        try:
            # i'm just closing and opening the connections for everything i do, maybe this isn't right and i should keep one always open
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    developer TEXT,
                    notes TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS executables (
                    id INTEGER PRIMARY KEY,
                    game_id INTEGER NOT NULL,
                    exe_name TEXT NOT NULL,
                    full_path TEXT UNIQUE,
                    FOREIGN KEY (game_id) REFERENCES games(id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY,
                    game_id INTEGER NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    FOREIGN KEY (game_id) REFERENCES games(id)
                )
            """)
            conn.commit()
        except sqlite3.Error:
            print("Something went wrong while creating the database")
            raise # just crash everything because idk at this point
        finally:
            conn.close() # type: ignore

    def insert_game(self, game: Game) -> Game:
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute("INSERT INTO games (name, developer, notes) VALUES (?, ?, ?)", 
                    (game.name, game.developer, game.notes))
            game.id = cur.lastrowid
            
            # Insert executables
            for exe in game.executables:
                cur.execute("INSERT INTO executables (game_id, exe_name, full_path) VALUES (?, ?, ?)",
                        (game.id, Path(exe.path).name, exe.path))
                exe.game_id = game.id
                exe.id = cur.lastrowid
            
            conn.commit()
            return game
        except sqlite3.Error as e:
            print(f"Error inserting game: {e}")
            raise
        finally:
            conn.close() # type: ignore

    def get_game(self, game_id: int):
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("SELECT name, developer, notes FROM games WHERE id = ?", (game_id,))

            game_row = cur.fetchone()
        
            if not game_row:
                return None
            
            return Game(
                id=game_id,
                name=game_row[0],
                developer=game_row[1],
                notes=game_row[2],
                executables=[] # uhh hmm we don't need this in this method so empty list
            )

        except sqlite3.Error:
            print(f"Something went wrong while getting a game. ID is {game_id}")
            return None
        finally:
            conn.close() # type: ignore

    def get_game_full(self, game_id: int):
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("SELECT name, developer, notes FROM games WHERE id = ?", (game_id,))

            game_row = cur.fetchone()
            if not game_row:
                return None
            
            # get executables for said game
            cur.execute(
                "SELECT full_path FROM executables WHERE game_id = ?",
                (game_id,)
            )

            exe_rows = cur.fetchall()
            if not exe_rows:
                print(f"Game {game_row[0]} found but no exes.")
                return Game(
                    id=game_id,
                    name=game_row[0],
                    developer=game_row[1],
                    notes=game_row[2],
                    executables=[] # well there weren't any exes sooo
                )

            executable_list = []
            for exe in exe_rows:
                executable_list.append(exe[0])
            
            return Game(
                id=game_id,
                name=game_row[0],
                developer=game_row[1],
                notes=game_row[2],
                executables=executable_list
            )

        except sqlite3.Error:
            print(f"Something went wrong while getting a game. ID is {game_id}")
            return None
        finally:
            conn.close() # type: ignore