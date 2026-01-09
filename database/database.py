import sqlite3

from dataclasses import dataclass

@dataclass
class Executable:
    id: int
    game_id: int
    path: str

@dataclass
class Game:
    id: int
    name: str
    developer: str
    notes: str
    executables: list[Executable]

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

    def insert_game(self, name: str, developer: str, notes: str, executables: list[Executable]):
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("INSERT INTO games (name, developer, notes) VALUES (?, ?, ?)", (name, developer, notes))
            game_id = cur.lastrowid
            conn.commit()
            print(f"Game successfully inserted, game_id: {game_id}")
        except sqlite3.Error:
            print(f"Something went wrong while inserting a game ({name}, {developer}, {notes})")
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